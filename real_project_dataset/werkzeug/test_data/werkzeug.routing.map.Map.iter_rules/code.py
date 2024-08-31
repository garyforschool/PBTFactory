from __future__ import annotations
import typing as t
import warnings
from pprint import pformat
from threading import Lock
from urllib.parse import quote
from urllib.parse import urljoin
from urllib.parse import urlunsplit
from .._internal import _get_environ
from .._internal import _wsgi_decoding_dance
from ..datastructures import ImmutableDict
from ..datastructures import MultiDict
from ..exceptions import BadHost
from ..exceptions import HTTPException
from ..exceptions import MethodNotAllowed
from ..exceptions import NotFound
from ..urls import _urlencode
from ..wsgi import get_host
from .converters import DEFAULT_CONVERTERS
from .exceptions import BuildError
from .exceptions import NoMatch
from .exceptions import RequestAliasRedirect
from .exceptions import RequestPath
from .exceptions import RequestRedirect
from .exceptions import WebsocketMismatch
from .matcher import StateMachineMatcher
from .rules import _simple_rule_re
from .rules import Rule

if t.TYPE_CHECKING:
    from _typeshed.wsgi import WSGIApplication
    from _typeshed.wsgi import WSGIEnvironment
    from ..wrappers.request import Request
    from .converters import BaseConverter
    from .rules import RuleFactory


class Map:
    default_converters = ImmutableDict(DEFAULT_CONVERTERS)
    lock_class = Lock

    def __init__(
        self,
        rules: t.Iterable[RuleFactory] | None = None,
        default_subdomain: str = "",
        strict_slashes: bool = True,
        merge_slashes: bool = True,
        redirect_defaults: bool = True,
        converters: t.Mapping[str, type[BaseConverter]] | None = None,
        sort_parameters: bool = False,
        sort_key: t.Callable[[t.Any], t.Any] | None = None,
        host_matching: bool = False,
    ) -> None:
        self._matcher = StateMachineMatcher(merge_slashes)
        self._rules_by_endpoint: dict[t.Any, list[Rule]] = {}
        self._remap = True
        self._remap_lock = self.lock_class()
        self.default_subdomain = default_subdomain
        self.strict_slashes = strict_slashes
        self.redirect_defaults = redirect_defaults
        self.host_matching = host_matching
        self.converters = self.default_converters.copy()
        if converters:
            self.converters.update(converters)
        self.sort_parameters = sort_parameters
        self.sort_key = sort_key
        for rulefactory in rules or ():
            self.add(rulefactory)

    @property
    def merge_slashes(self) -> bool:
        return self._matcher.merge_slashes

    @merge_slashes.setter
    def merge_slashes(self, value: bool) -> None:
        self._matcher.merge_slashes = value

    def is_endpoint_expecting(self, endpoint: t.Any, *arguments: str) -> bool:
        self.update()
        arguments_set = set(arguments)
        for rule in self._rules_by_endpoint[endpoint]:
            if arguments_set.issubset(rule.arguments):
                return True
        return False

    @property
    def _rules(self) -> list[Rule]:
        return [rule for rules in self._rules_by_endpoint.values() for rule in rules]

    def iter_rules(self, endpoint: t.Any | None = None) -> t.Iterator[Rule]:
        self.update()
        if endpoint is not None:
            return iter(self._rules_by_endpoint[endpoint])
        return iter(self._rules)

    def add(self, rulefactory: RuleFactory) -> None:
        for rule in rulefactory.get_rules(self):
            rule.bind(self)
            if not rule.build_only:
                self._matcher.add(rule)
            self._rules_by_endpoint.setdefault(rule.endpoint, []).append(rule)
        self._remap = True

    def bind(
        self,
        server_name: str,
        script_name: str | None = None,
        subdomain: str | None = None,
        url_scheme: str = "http",
        default_method: str = "GET",
        path_info: str | None = None,
        query_args: t.Mapping[str, t.Any] | str | None = None,
    ) -> MapAdapter:
        server_name = server_name.lower()
        if self.host_matching:
            if subdomain is not None:
                raise RuntimeError("host matching enabled and a subdomain was provided")
        elif subdomain is None:
            subdomain = self.default_subdomain
        if script_name is None:
            script_name = "/"
        if path_info is None:
            path_info = "/"
        server_name, port_sep, port = server_name.partition(":")
        try:
            server_name = server_name.encode("idna").decode("ascii")
        except UnicodeError as e:
            raise BadHost() from e
        return MapAdapter(
            self,
            f"{server_name}{port_sep}{port}",
            script_name,
            subdomain,
            url_scheme,
            path_info,
            default_method,
            query_args,
        )

    def bind_to_environ(
        self,
        environ: WSGIEnvironment | Request,
        server_name: str | None = None,
        subdomain: str | None = None,
    ) -> MapAdapter:
        env = _get_environ(environ)
        wsgi_server_name = get_host(env).lower()
        scheme = env["wsgi.url_scheme"]
        upgrade = any(
            v.strip() == "upgrade"
            for v in env.get("HTTP_CONNECTION", "").lower().split(",")
        )
        if upgrade and env.get("HTTP_UPGRADE", "").lower() == "websocket":
            scheme = "wss" if scheme == "https" else "ws"
        if server_name is None:
            server_name = wsgi_server_name
        else:
            server_name = server_name.lower()
            if scheme in {"http", "ws"} and server_name.endswith(":80"):
                server_name = server_name[:-3]
            elif scheme in {"https", "wss"} and server_name.endswith(":443"):
                server_name = server_name[:-4]
        if subdomain is None and not self.host_matching:
            cur_server_name = wsgi_server_name.split(".")
            real_server_name = server_name.split(".")
            offset = -len(real_server_name)
            if cur_server_name[offset:] != real_server_name:
                warnings.warn(
                    f"Current server name {wsgi_server_name!r} doesn't match configured server name {server_name!r}",
                    stacklevel=2,
                )
                subdomain = "<invalid>"
            else:
                subdomain = ".".join(filter(None, cur_server_name[:offset]))

        def _get_wsgi_string(name: str) -> str | None:
            val = env.get(name)
            if val is not None:
                return _wsgi_decoding_dance(val)
            return None

        script_name = _get_wsgi_string("SCRIPT_NAME")
        path_info = _get_wsgi_string("PATH_INFO")
        query_args = _get_wsgi_string("QUERY_STRING")
        return Map.bind(
            self,
            server_name,
            script_name,
            subdomain,
            scheme,
            env["REQUEST_METHOD"],
            path_info,
            query_args=query_args,
        )

    def update(self) -> None:
        if not self._remap:
            return
        with self._remap_lock:
            if not self._remap:
                return
            self._matcher.update()
            for rules in self._rules_by_endpoint.values():
                rules.sort(key=lambda x: x.build_compare_key())
            self._remap = False

    def __repr__(self) -> str:
        rules = self.iter_rules()
        return f"{type(self).__name__}({pformat(list(rules))})"


class MapAdapter:

    def __init__(
        self,
        map: Map,
        server_name: str,
        script_name: str,
        subdomain: str | None,
        url_scheme: str,
        path_info: str,
        default_method: str,
        query_args: t.Mapping[str, t.Any] | str | None = None,
    ):
        self.map = map
        self.server_name = server_name
        if not script_name.endswith("/"):
            script_name += "/"
        self.script_name = script_name
        self.subdomain = subdomain
        self.url_scheme = url_scheme
        self.path_info = path_info
        self.default_method = default_method
        self.query_args = query_args
        self.websocket = self.url_scheme in {"ws", "wss"}

    def dispatch(
        self,
        view_func: t.Callable[[str, t.Mapping[str, t.Any]], WSGIApplication],
        path_info: str | None = None,
        method: str | None = None,
        catch_http_exceptions: bool = False,
    ) -> WSGIApplication:
        try:
            try:
                endpoint, args = self.match(path_info, method)
            except RequestRedirect as e:
                return e
            return view_func(endpoint, args)
        except HTTPException as e:
            if catch_http_exceptions:
                return e
            raise

    @t.overload
    def match(
        self,
        path_info: str | None = None,
        method: str | None = None,
        return_rule: t.Literal[False] = False,
        query_args: t.Mapping[str, t.Any] | str | None = None,
        websocket: bool | None = None,
    ) -> tuple[t.Any, t.Mapping[str, t.Any]]: ...

    @t.overload
    def match(
        self,
        path_info: str | None = None,
        method: str | None = None,
        return_rule: t.Literal[True] = True,
        query_args: t.Mapping[str, t.Any] | str | None = None,
        websocket: bool | None = None,
    ) -> tuple[Rule, t.Mapping[str, t.Any]]: ...

    def match(
        self,
        path_info: str | None = None,
        method: str | None = None,
        return_rule: bool = False,
        query_args: t.Mapping[str, t.Any] | str | None = None,
        websocket: bool | None = None,
    ) -> tuple[t.Any | Rule, t.Mapping[str, t.Any]]:
        self.map.update()
        if path_info is None:
            path_info = self.path_info
        if query_args is None:
            query_args = self.query_args or {}
        method = (method or self.default_method).upper()
        if websocket is None:
            websocket = self.websocket
        domain_part = self.server_name
        if not self.map.host_matching and self.subdomain is not None:
            domain_part = self.subdomain
        path_part = f"/{path_info.lstrip('/')}" if path_info else ""
        try:
            result = self.map._matcher.match(domain_part, path_part, method, websocket)
        except RequestPath as e:
            new_path = quote(e.path_info, safe="!$&'()*+,/:;=@")
            raise RequestRedirect(
                self.make_redirect_url(new_path, query_args)
            ) from None
        except RequestAliasRedirect as e:
            raise RequestRedirect(
                self.make_alias_redirect_url(
                    f"{domain_part}|{path_part}",
                    e.endpoint,
                    e.matched_values,
                    method,
                    query_args,
                )
            ) from None
        except NoMatch as e:
            if e.have_match_for:
                raise MethodNotAllowed(valid_methods=list(e.have_match_for)) from None
            if e.websocket_mismatch:
                raise WebsocketMismatch() from None
            raise NotFound() from None
        else:
            rule, rv = result
            if self.map.redirect_defaults:
                redirect_url = self.get_default_redirect(rule, method, rv, query_args)
                if redirect_url is not None:
                    raise RequestRedirect(redirect_url)
            if rule.redirect_to is not None:
                if isinstance(rule.redirect_to, str):

                    def _handle_match(match: t.Match[str]) -> str:
                        value = rv[match.group(1)]
                        return rule._converters[match.group(1)].to_url(value)

                    redirect_url = _simple_rule_re.sub(_handle_match, rule.redirect_to)
                else:
                    redirect_url = rule.redirect_to(self, **rv)
                if self.subdomain:
                    netloc = f"{self.subdomain}.{self.server_name}"
                else:
                    netloc = self.server_name
                raise RequestRedirect(
                    urljoin(
                        f"{self.url_scheme or 'http'}://{netloc}{self.script_name}",
                        redirect_url,
                    )
                )
            if return_rule:
                return rule, rv
            else:
                return rule.endpoint, rv

    def test(self, path_info: str | None = None, method: str | None = None) -> bool:
        try:
            self.match(path_info, method)
        except RequestRedirect:
            pass
        except HTTPException:
            return False
        return True

    def allowed_methods(self, path_info: str | None = None) -> t.Iterable[str]:
        try:
            self.match(path_info, method="--")
        except MethodNotAllowed as e:
            return e.valid_methods
        except HTTPException:
            pass
        return []

    def get_host(self, domain_part: str | None) -> str:
        if self.map.host_matching:
            if domain_part is None:
                return self.server_name
            return domain_part
        if domain_part is None:
            subdomain = self.subdomain
        else:
            subdomain = domain_part
        if subdomain:
            return f"{subdomain}.{self.server_name}"
        else:
            return self.server_name

    def get_default_redirect(
        self,
        rule: Rule,
        method: str,
        values: t.MutableMapping[str, t.Any],
        query_args: t.Mapping[str, t.Any] | str,
    ) -> str | None:
        assert self.map.redirect_defaults
        for r in self.map._rules_by_endpoint[rule.endpoint]:
            if r is rule:
                break
            if r.provides_defaults_for(rule) and r.suitable_for(values, method):
                values.update(r.defaults)
                domain_part, path = r.build(values)
                return self.make_redirect_url(path, query_args, domain_part=domain_part)
        return None

    def encode_query_args(self, query_args: t.Mapping[str, t.Any] | str) -> str:
        if not isinstance(query_args, str):
            return _urlencode(query_args)
        return query_args

    def make_redirect_url(
        self,
        path_info: str,
        query_args: t.Mapping[str, t.Any] | str | None = None,
        domain_part: str | None = None,
    ) -> str:
        if query_args is None:
            query_args = self.query_args
        if query_args:
            query_str = self.encode_query_args(query_args)
        else:
            query_str = None
        scheme = self.url_scheme or "http"
        host = self.get_host(domain_part)
        path = "/".join((self.script_name.strip("/"), path_info.lstrip("/")))
        return urlunsplit((scheme, host, path, query_str, None))

    def make_alias_redirect_url(
        self,
        path: str,
        endpoint: t.Any,
        values: t.Mapping[str, t.Any],
        method: str,
        query_args: t.Mapping[str, t.Any] | str,
    ) -> str:
        url = self.build(
            endpoint, values, method, append_unknown=False, force_external=True
        )
        if query_args:
            url += f"?{self.encode_query_args(query_args)}"
        assert url != path, "detected invalid alias setting. No canonical URL found"
        return url

    def _partial_build(
        self,
        endpoint: t.Any,
        values: t.Mapping[str, t.Any],
        method: str | None,
        append_unknown: bool,
    ) -> tuple[str, str, bool] | None:
        if method is None:
            rv = self._partial_build(
                endpoint, values, self.default_method, append_unknown
            )
            if rv is not None:
                return rv
        first_match = None
        for rule in self.map._rules_by_endpoint.get(endpoint, ()):
            if rule.suitable_for(values, method):
                build_rv = rule.build(values, append_unknown)
                if build_rv is not None:
                    rv = build_rv[0], build_rv[1], rule.websocket
                    if self.map.host_matching:
                        if rv[0] == self.server_name:
                            return rv
                        elif first_match is None:
                            first_match = rv
                    else:
                        return rv
        return first_match

    def build(
        self,
        endpoint: t.Any,
        values: t.Mapping[str, t.Any] | None = None,
        method: str | None = None,
        force_external: bool = False,
        append_unknown: bool = True,
        url_scheme: str | None = None,
    ) -> str:
        self.map.update()
        if values:
            if isinstance(values, MultiDict):
                values = {
                    k: (v[0] if len(v) == 1 else v)
                    for k, v in dict.items(values)
                    if len(v) != 0
                }
            else:
                values = {k: v for k, v in values.items() if v is not None}
        else:
            values = {}
        rv = self._partial_build(endpoint, values, method, append_unknown)
        if rv is None:
            raise BuildError(endpoint, values, method, self)
        domain_part, path, websocket = rv
        host = self.get_host(domain_part)
        if url_scheme is None:
            url_scheme = self.url_scheme
        secure = url_scheme in {"https", "wss"}
        if websocket:
            force_external = True
            url_scheme = "wss" if secure else "ws"
        elif url_scheme:
            url_scheme = "https" if secure else "http"
        if not force_external and (
            self.map.host_matching
            and host == self.server_name
            or not self.map.host_matching
            and domain_part == self.subdomain
        ):
            return f"{self.script_name.rstrip('/')}/{path.lstrip('/')}"
        scheme = f"{url_scheme}:" if url_scheme else ""
        return f"{scheme}//{host}{self.script_name[:-1]}/{path.lstrip('/')}"