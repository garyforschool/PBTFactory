from __future__ import annotations
import collections.abc as cabc
import functools
import json
import typing as t
from io import BytesIO
from .._internal import _wsgi_decoding_dance
from ..datastructures import CombinedMultiDict
from ..datastructures import EnvironHeaders
from ..datastructures import FileStorage
from ..datastructures import ImmutableMultiDict
from ..datastructures import iter_multi_items
from ..datastructures import MultiDict
from ..exceptions import BadRequest
from ..exceptions import UnsupportedMediaType
from ..formparser import default_stream_factory
from ..formparser import FormDataParser
from ..sansio.request import Request as _SansIORequest
from ..utils import cached_property
from ..utils import environ_property
from ..wsgi import _get_server
from ..wsgi import get_input_stream

if t.TYPE_CHECKING:
    from _typeshed.wsgi import WSGIApplication
    from _typeshed.wsgi import WSGIEnvironment


class Request(_SansIORequest):
    max_content_length: int | None = None
    max_form_memory_size: int | None = None
    max_form_parts = 1000
    form_data_parser_class: type[FormDataParser] = FormDataParser
    environ: WSGIEnvironment
    shallow: bool

    def __init__(
        self,
        environ: WSGIEnvironment,
        populate_request: bool = True,
        shallow: bool = False,
    ) -> None:
        super().__init__(
            method=environ.get("REQUEST_METHOD", "GET"),
            scheme=environ.get("wsgi.url_scheme", "http"),
            server=_get_server(environ),
            root_path=_wsgi_decoding_dance(environ.get("SCRIPT_NAME") or ""),
            path=_wsgi_decoding_dance(environ.get("PATH_INFO") or ""),
            query_string=environ.get("QUERY_STRING", "").encode("latin1"),
            headers=EnvironHeaders(environ),
            remote_addr=environ.get("REMOTE_ADDR"),
        )
        self.environ = environ
        self.shallow = shallow
        if populate_request and not shallow:
            self.environ["werkzeug.request"] = self

    @classmethod
    def from_values(cls, *args: t.Any, **kwargs: t.Any) -> Request:
        from ..test import EnvironBuilder

        builder = EnvironBuilder(*args, **kwargs)
        try:
            return builder.get_request(cls)
        finally:
            builder.close()

    @classmethod
    def application(cls, f: t.Callable[[Request], WSGIApplication]) -> WSGIApplication:
        from ..exceptions import HTTPException

        @functools.wraps(f)
        def application(*args: t.Any) -> cabc.Iterable[bytes]:
            request = cls(args[-2])
            with request:
                try:
                    resp = f(*(args[:-2] + (request,)))
                except HTTPException as e:
                    resp = t.cast("WSGIApplication", e.get_response(args[-2]))
                return resp(*args[-2:])

        return t.cast("WSGIApplication", application)

    def _get_file_stream(
        self,
        total_content_length: int | None,
        content_type: str | None,
        filename: str | None = None,
        content_length: int | None = None,
    ) -> t.IO[bytes]:
        return default_stream_factory(
            total_content_length=total_content_length,
            filename=filename,
            content_type=content_type,
            content_length=content_length,
        )

    @property
    def want_form_data_parsed(self) -> bool:
        return bool(self.environ.get("CONTENT_TYPE"))

    def make_form_data_parser(self) -> FormDataParser:
        return self.form_data_parser_class(
            stream_factory=self._get_file_stream,
            max_form_memory_size=self.max_form_memory_size,
            max_content_length=self.max_content_length,
            max_form_parts=self.max_form_parts,
            cls=self.parameter_storage_class,
        )

    def _load_form_data(self) -> None:
        if "form" in self.__dict__:
            return
        if self.want_form_data_parsed:
            parser = self.make_form_data_parser()
            data = parser.parse(
                self._get_stream_for_parsing(),
                self.mimetype,
                self.content_length,
                self.mimetype_params,
            )
        else:
            data = (
                self.stream,
                self.parameter_storage_class(),
                self.parameter_storage_class(),
            )
        d = self.__dict__
        d["stream"], d["form"], d["files"] = data

    def _get_stream_for_parsing(self) -> t.IO[bytes]:
        cached_data = getattr(self, "_cached_data", None)
        if cached_data is not None:
            return BytesIO(cached_data)
        return self.stream

    def close(self) -> None:
        files = self.__dict__.get("files")
        for _key, value in iter_multi_items(files or ()):
            value.close()

    def __enter__(self) -> Request:
        return self

    def __exit__(self, exc_type, exc_value, tb) -> None:
        self.close()

    @cached_property
    def stream(self) -> t.IO[bytes]:
        if self.shallow:
            raise RuntimeError(
                "This request was created with 'shallow=True', reading from the input stream is disabled."
            )
        return get_input_stream(
            self.environ, max_content_length=self.max_content_length
        )

    input_stream = environ_property[t.IO[bytes]](
        "wsgi.input",
        doc="""The raw WSGI input stream, without any safety checks.

        This is dangerous to use. It does not guard against infinite streams or reading
        past :attr:`content_length` or :attr:`max_content_length`.

        Use :attr:`stream` instead.
        """,
    )

    @cached_property
    def data(self) -> bytes:
        return self.get_data(parse_form_data=True)

    @t.overload
    def get_data(
        self,
        cache: bool = True,
        as_text: t.Literal[False] = False,
        parse_form_data: bool = False,
    ) -> bytes: ...

    @t.overload
    def get_data(
        self,
        cache: bool = True,
        as_text: t.Literal[True] = ...,
        parse_form_data: bool = False,
    ) -> str: ...

    def get_data(
        self, cache: bool = True, as_text: bool = False, parse_form_data: bool = False
    ) -> bytes | str:
        rv = getattr(self, "_cached_data", None)
        if rv is None:
            if parse_form_data:
                self._load_form_data()
            rv = self.stream.read()
            if cache:
                self._cached_data = rv
        if as_text:
            rv = rv.decode(errors="replace")
        return rv

    @cached_property
    def form(self) -> ImmutableMultiDict[str, str]:
        self._load_form_data()
        return self.form

    @cached_property
    def values(self) -> CombinedMultiDict[str, str]:
        sources = [self.args]
        if self.method != "GET":
            sources.append(self.form)
        args = []
        for d in sources:
            if not isinstance(d, MultiDict):
                d = MultiDict(d)
            args.append(d)
        return CombinedMultiDict(args)

    @cached_property
    def files(self) -> ImmutableMultiDict[str, FileStorage]:
        self._load_form_data()
        return self.files

    @property
    def script_root(self) -> str:
        return self.root_path

    @cached_property
    def url_root(self) -> str:
        return self.root_url

    remote_user = environ_property[str](
        "REMOTE_USER",
        doc="""If the server supports user authentication, and the
        script is protected, this attribute contains the username the
        user has authenticated as.""",
    )
    is_multithread = environ_property[bool](
        "wsgi.multithread",
        doc="""boolean that is `True` if the application is served by a
        multithreaded WSGI server.""",
    )
    is_multiprocess = environ_property[bool](
        "wsgi.multiprocess",
        doc="""boolean that is `True` if the application is served by a
        WSGI server that spawns multiple processes.""",
    )
    is_run_once = environ_property[bool](
        "wsgi.run_once",
        doc="""boolean that is `True` if the application will be
        executed only once in a process lifetime.  This is the case for
        CGI for example, but it's not guaranteed that the execution only
        happens one time.""",
    )
    json_module = json

    @property
    def json(self) -> t.Any | None:
        return self.get_json()

    _cached_json: tuple[t.Any, t.Any] = (Ellipsis, Ellipsis)

    @t.overload
    def get_json(
        self, force: bool = ..., silent: t.Literal[False] = ..., cache: bool = ...
    ) -> t.Any: ...

    @t.overload
    def get_json(
        self, force: bool = ..., silent: bool = ..., cache: bool = ...
    ) -> t.Any | None: ...

    def get_json(
        self, force: bool = False, silent: bool = False, cache: bool = True
    ) -> t.Any | None:
        if cache and self._cached_json[silent] is not Ellipsis:
            return self._cached_json[silent]
        if not (force or self.is_json):
            if not silent:
                return self.on_json_loading_failed(None)
            else:
                return None
        data = self.get_data(cache=cache)
        try:
            rv = self.json_module.loads(data)
        except ValueError as e:
            if silent:
                rv = None
                if cache:
                    normal_rv, _ = self._cached_json
                    self._cached_json = normal_rv, rv
            else:
                rv = self.on_json_loading_failed(e)
                if cache:
                    _, silent_rv = self._cached_json
                    self._cached_json = rv, silent_rv
        else:
            if cache:
                self._cached_json = rv, rv
        return rv

    def on_json_loading_failed(self, e: ValueError | None) -> t.Any:
        if e is not None:
            raise BadRequest(f"Failed to decode JSON object: {e}")
        raise UnsupportedMediaType(
            "Did not attempt to load JSON data because the request Content-Type was not 'application/json'."
        )
