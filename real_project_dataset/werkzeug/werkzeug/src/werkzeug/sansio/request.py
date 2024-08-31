from __future__ import annotations
import typing as t
from datetime import datetime
from urllib.parse import parse_qsl
from ..datastructures import Accept
from ..datastructures import Authorization
from ..datastructures import CharsetAccept
from ..datastructures import ETags
from ..datastructures import Headers
from ..datastructures import HeaderSet
from ..datastructures import IfRange
from ..datastructures import ImmutableList
from ..datastructures import ImmutableMultiDict
from ..datastructures import LanguageAccept
from ..datastructures import MIMEAccept
from ..datastructures import MultiDict
from ..datastructures import Range
from ..datastructures import RequestCacheControl
from ..http import parse_accept_header
from ..http import parse_cache_control_header
from ..http import parse_date
from ..http import parse_etags
from ..http import parse_if_range_header
from ..http import parse_list_header
from ..http import parse_options_header
from ..http import parse_range_header
from ..http import parse_set_header
from ..user_agent import UserAgent
from ..utils import cached_property
from ..utils import header_property
from .http import parse_cookie
from .utils import get_content_length
from .utils import get_current_url
from .utils import get_host


class Request:
    parameter_storage_class: type[MultiDict[str, t.Any]] = ImmutableMultiDict
    dict_storage_class: type[MultiDict[str, t.Any]] = ImmutableMultiDict
    list_storage_class: type[list[t.Any]] = ImmutableList
    user_agent_class: type[UserAgent] = UserAgent
    """The class used and returned by the :attr:`user_agent` property to
    parse the header. Defaults to
    :class:`~werkzeug.user_agent.UserAgent`, which does no parsing. An
    extension can provide a subclass that uses a parser to provide other
    data.

    .. versionadded:: 2.0
    """
    trusted_hosts: list[str] | None = None

    def __init__(
        self,
        method: str,
        scheme: str,
        server: tuple[str, int | None] | None,
        root_path: str,
        path: str,
        query_string: bytes,
        headers: Headers,
        remote_addr: str | None,
    ) -> None:
        self.method = method.upper()
        self.scheme = scheme
        self.server = server
        self.root_path = root_path.rstrip("/")
        self.path = "/" + path.lstrip("/")
        self.query_string = query_string
        self.headers = headers
        self.remote_addr = remote_addr

    def __repr__(self) -> str:
        try:
            url = self.url
        except Exception as e:
            url = f"(invalid URL: {e})"
        return f"<{type(self).__name__} {url!r} [{self.method}]>"

    @cached_property
    def args(self) -> MultiDict[str, str]:
        return self.parameter_storage_class(
            parse_qsl(
                self.query_string.decode(),
                keep_blank_values=True,
                errors="werkzeug.url_quote",
            )
        )

    @cached_property
    def access_route(self) -> list[str]:
        if "X-Forwarded-For" in self.headers:
            return self.list_storage_class(
                parse_list_header(self.headers["X-Forwarded-For"])
            )
        elif self.remote_addr is not None:
            return self.list_storage_class([self.remote_addr])
        return self.list_storage_class()

    @cached_property
    def full_path(self) -> str:
        return f"{self.path}?{self.query_string.decode()}"

    @property
    def is_secure(self) -> bool:
        return self.scheme in {"https", "wss"}

    @cached_property
    def url(self) -> str:
        return get_current_url(
            self.scheme, self.host, self.root_path, self.path, self.query_string
        )

    @cached_property
    def base_url(self) -> str:
        return get_current_url(self.scheme, self.host, self.root_path, self.path)

    @cached_property
    def root_url(self) -> str:
        return get_current_url(self.scheme, self.host, self.root_path)

    @cached_property
    def host_url(self) -> str:
        return get_current_url(self.scheme, self.host)

    @cached_property
    def host(self) -> str:
        return get_host(
            self.scheme, self.headers.get("host"), self.server, self.trusted_hosts
        )

    @cached_property
    def cookies(self) -> ImmutableMultiDict[str, str]:
        wsgi_combined_cookie = ";".join(self.headers.getlist("Cookie"))
        return parse_cookie(wsgi_combined_cookie, cls=self.dict_storage_class)

    content_type = header_property[str](
        "Content-Type",
        doc="""The Content-Type entity-header field indicates the media
        type of the entity-body sent to the recipient or, in the case of
        the HEAD method, the media type that would have been sent had
        the request been a GET.""",
        read_only=True,
    )

    @cached_property
    def content_length(self) -> int | None:
        return get_content_length(
            http_content_length=self.headers.get("Content-Length"),
            http_transfer_encoding=self.headers.get("Transfer-Encoding"),
        )

    content_encoding = header_property[str](
        "Content-Encoding",
        doc="""The Content-Encoding entity-header field is used as a
        modifier to the media-type. When present, its value indicates
        what additional content codings have been applied to the
        entity-body, and thus what decoding mechanisms must be applied
        in order to obtain the media-type referenced by the Content-Type
        header field.

        .. versionadded:: 0.9""",
        read_only=True,
    )
    content_md5 = header_property[str](
        "Content-MD5",
        doc="""The Content-MD5 entity-header field, as defined in
        RFC 1864, is an MD5 digest of the entity-body for the purpose of
        providing an end-to-end message integrity check (MIC) of the
        entity-body. (Note: a MIC is good for detecting accidental
        modification of the entity-body in transit, but is not proof
        against malicious attacks.)

        .. versionadded:: 0.9""",
        read_only=True,
    )
    referrer = header_property[str](
        "Referer",
        doc="""The Referer[sic] request-header field allows the client
        to specify, for the server's benefit, the address (URI) of the
        resource from which the Request-URI was obtained (the
        "referrer", although the header field is misspelled).""",
        read_only=True,
    )
    date = header_property(
        "Date",
        None,
        parse_date,
        doc="""The Date general-header field represents the date and
        time at which the message was originated, having the same
        semantics as orig-date in RFC 822.

        .. versionchanged:: 2.0
            The datetime object is timezone-aware.
        """,
        read_only=True,
    )
    max_forwards = header_property(
        "Max-Forwards",
        None,
        int,
        doc="""The Max-Forwards request-header field provides a
        mechanism with the TRACE and OPTIONS methods to limit the number
        of proxies or gateways that can forward the request to the next
        inbound server.""",
        read_only=True,
    )

    def _parse_content_type(self) -> None:
        if not hasattr(self, "_parsed_content_type"):
            self._parsed_content_type = parse_options_header(
                self.headers.get("Content-Type", "")
            )

    @property
    def mimetype(self) -> str:
        self._parse_content_type()
        return self._parsed_content_type[0].lower()

    @property
    def mimetype_params(self) -> dict[str, str]:
        self._parse_content_type()
        return self._parsed_content_type[1]

    @cached_property
    def pragma(self) -> HeaderSet:
        return parse_set_header(self.headers.get("Pragma", ""))

    @cached_property
    def accept_mimetypes(self) -> MIMEAccept:
        return parse_accept_header(self.headers.get("Accept"), MIMEAccept)

    @cached_property
    def accept_charsets(self) -> CharsetAccept:
        return parse_accept_header(self.headers.get("Accept-Charset"), CharsetAccept)

    @cached_property
    def accept_encodings(self) -> Accept:
        return parse_accept_header(self.headers.get("Accept-Encoding"))

    @cached_property
    def accept_languages(self) -> LanguageAccept:
        return parse_accept_header(self.headers.get("Accept-Language"), LanguageAccept)

    @cached_property
    def cache_control(self) -> RequestCacheControl:
        cache_control = self.headers.get("Cache-Control")
        return parse_cache_control_header(cache_control, None, RequestCacheControl)

    @cached_property
    def if_match(self) -> ETags:
        return parse_etags(self.headers.get("If-Match"))

    @cached_property
    def if_none_match(self) -> ETags:
        return parse_etags(self.headers.get("If-None-Match"))

    @cached_property
    def if_modified_since(self) -> datetime | None:
        return parse_date(self.headers.get("If-Modified-Since"))

    @cached_property
    def if_unmodified_since(self) -> datetime | None:
        return parse_date(self.headers.get("If-Unmodified-Since"))

    @cached_property
    def if_range(self) -> IfRange:
        return parse_if_range_header(self.headers.get("If-Range"))

    @cached_property
    def range(self) -> Range | None:
        return parse_range_header(self.headers.get("Range"))

    @cached_property
    def user_agent(self) -> UserAgent:
        return self.user_agent_class(self.headers.get("User-Agent", ""))

    @cached_property
    def authorization(self) -> Authorization | None:
        return Authorization.from_header(self.headers.get("Authorization"))

    origin = header_property[str](
        "Origin",
        doc="The host that the request originated from. Set :attr:`~CORSResponseMixin.access_control_allow_origin` on the response to indicate which origins are allowed.",
        read_only=True,
    )
    access_control_request_headers = header_property(
        "Access-Control-Request-Headers",
        load_func=parse_set_header,
        doc="Sent with a preflight request to indicate which headers will be sent with the cross origin request. Set :attr:`~CORSResponseMixin.access_control_allow_headers` on the response to indicate which headers are allowed.",
        read_only=True,
    )
    access_control_request_method = header_property[str](
        "Access-Control-Request-Method",
        doc="Sent with a preflight request to indicate which method will be used for the cross origin request. Set :attr:`~CORSResponseMixin.access_control_allow_methods` on the response to indicate which methods are allowed.",
        read_only=True,
    )

    @property
    def is_json(self) -> bool:
        mt = self.mimetype
        return (
            mt == "application/json"
            or mt.startswith("application/")
            and mt.endswith("+json")
        )
