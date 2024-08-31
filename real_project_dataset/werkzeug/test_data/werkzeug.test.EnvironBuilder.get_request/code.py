from __future__ import annotations
import dataclasses
import mimetypes
import sys
import typing as t
from collections import defaultdict
from datetime import datetime
from io import BytesIO
from itertools import chain
from random import random
from tempfile import TemporaryFile
from time import time
from urllib.parse import unquote
from urllib.parse import urlsplit
from urllib.parse import urlunsplit
from ._internal import _get_environ
from ._internal import _wsgi_decoding_dance
from ._internal import _wsgi_encoding_dance
from .datastructures import Authorization
from .datastructures import CallbackDict
from .datastructures import CombinedMultiDict
from .datastructures import EnvironHeaders
from .datastructures import FileMultiDict
from .datastructures import Headers
from .datastructures import MultiDict
from .http import dump_cookie
from .http import dump_options_header
from .http import parse_cookie
from .http import parse_date
from .http import parse_options_header
from .sansio.multipart import Data
from .sansio.multipart import Epilogue
from .sansio.multipart import Field
from .sansio.multipart import File
from .sansio.multipart import MultipartEncoder
from .sansio.multipart import Preamble
from .urls import _urlencode
from .urls import iri_to_uri
from .utils import cached_property
from .utils import get_content_type
from .wrappers.request import Request
from .wrappers.response import Response
from .wsgi import ClosingIterator
from .wsgi import get_current_url

if t.TYPE_CHECKING:
    import typing_extensions as te
    from _typeshed.wsgi import WSGIApplication
    from _typeshed.wsgi import WSGIEnvironment


def stream_encode_multipart(
    data: t.Mapping[str, t.Any],
    use_tempfile: bool = True,
    threshold: int = 1024 * 500,
    boundary: str | None = None,
) -> tuple[t.IO[bytes], int, str]:
    if boundary is None:
        boundary = f"---------------WerkzeugFormPart_{time()}{random()}"
    stream: t.IO[bytes] = BytesIO()
    total_length = 0
    on_disk = False
    write_binary: t.Callable[[bytes], int]
    if use_tempfile:

        def write_binary(s: bytes) -> int:
            nonlocal stream, total_length, on_disk
            if on_disk:
                return stream.write(s)
            else:
                length = len(s)
                if length + total_length <= threshold:
                    stream.write(s)
                else:
                    new_stream = t.cast(t.IO[bytes], TemporaryFile("wb+"))
                    new_stream.write(stream.getvalue())
                    new_stream.write(s)
                    stream = new_stream
                    on_disk = True
                total_length += length
                return length

    else:
        write_binary = stream.write
    encoder = MultipartEncoder(boundary.encode())
    write_binary(encoder.send_event(Preamble(data=b"")))
    for key, value in _iter_data(data):
        reader = getattr(value, "read", None)
        if reader is not None:
            filename = getattr(value, "filename", getattr(value, "name", None))
            content_type = getattr(value, "content_type", None)
            if content_type is None:
                content_type = (
                    filename
                    and mimetypes.guess_type(filename)[0]
                    or "application/octet-stream"
                )
            headers = value.headers
            headers.update([("Content-Type", content_type)])
            if filename is None:
                write_binary(encoder.send_event(Field(name=key, headers=headers)))
            else:
                write_binary(
                    encoder.send_event(
                        File(name=key, filename=filename, headers=headers)
                    )
                )
            while True:
                chunk = reader(16384)
                if not chunk:
                    write_binary(encoder.send_event(Data(data=chunk, more_data=False)))
                    break
                write_binary(encoder.send_event(Data(data=chunk, more_data=True)))
        else:
            if not isinstance(value, str):
                value = str(value)
            write_binary(encoder.send_event(Field(name=key, headers=Headers())))
            write_binary(encoder.send_event(Data(data=value.encode(), more_data=False)))
    write_binary(encoder.send_event(Epilogue(data=b"")))
    length = stream.tell()
    stream.seek(0)
    return stream, length, boundary


def encode_multipart(
    values: t.Mapping[str, t.Any], boundary: str | None = None
) -> tuple[str, bytes]:
    stream, length, boundary = stream_encode_multipart(
        values, use_tempfile=False, boundary=boundary
    )
    return boundary, stream.read()


def _iter_data(data: t.Mapping[str, t.Any]) -> t.Iterator[tuple[str, t.Any]]:
    if isinstance(data, MultiDict):
        yield from data.items(multi=True)
    else:
        for key, value in data.items():
            if isinstance(value, list):
                for v in value:
                    yield key, v
            else:
                yield key, value


_TAnyMultiDict = t.TypeVar("_TAnyMultiDict", bound="MultiDict[t.Any, t.Any]")


class EnvironBuilder:
    server_protocol = "HTTP/1.1"
    wsgi_version = 1, 0
    request_class = Request
    import json

    json_dumps = staticmethod(json.dumps)
    del json
    _args: MultiDict[str, str] | None
    _query_string: str | None
    _input_stream: t.IO[bytes] | None
    _form: MultiDict[str, str] | None
    _files: FileMultiDict | None

    def __init__(
        self,
        path: str = "/",
        base_url: str | None = None,
        query_string: t.Mapping[str, str] | str | None = None,
        method: str = "GET",
        input_stream: t.IO[bytes] | None = None,
        content_type: str | None = None,
        content_length: int | None = None,
        errors_stream: t.IO[str] | None = None,
        multithread: bool = False,
        multiprocess: bool = False,
        run_once: bool = False,
        headers: Headers | t.Iterable[tuple[str, str]] | None = None,
        data: None | (t.IO[bytes] | str | bytes | t.Mapping[str, t.Any]) = None,
        environ_base: t.Mapping[str, t.Any] | None = None,
        environ_overrides: t.Mapping[str, t.Any] | None = None,
        mimetype: str | None = None,
        json: t.Mapping[str, t.Any] | None = None,
        auth: Authorization | tuple[str, str] | None = None,
    ) -> None:
        if query_string is not None and "?" in path:
            raise ValueError("Query string is defined in the path and as an argument")
        request_uri = urlsplit(path)
        if query_string is None and "?" in path:
            query_string = request_uri.query
        self.path = iri_to_uri(request_uri.path)
        self.request_uri = path
        if base_url is not None:
            base_url = iri_to_uri(base_url)
        self.base_url = base_url
        if isinstance(query_string, str):
            self.query_string = query_string
        else:
            if query_string is None:
                query_string = MultiDict()
            elif not isinstance(query_string, MultiDict):
                query_string = MultiDict(query_string)
            self.args = query_string
        self.method = method
        if headers is None:
            headers = Headers()
        elif not isinstance(headers, Headers):
            headers = Headers(headers)
        self.headers = headers
        if content_type is not None:
            self.content_type = content_type
        if errors_stream is None:
            errors_stream = sys.stderr
        self.errors_stream = errors_stream
        self.multithread = multithread
        self.multiprocess = multiprocess
        self.run_once = run_once
        self.environ_base = environ_base
        self.environ_overrides = environ_overrides
        self.input_stream = input_stream
        self.content_length = content_length
        self.closed = False
        if auth is not None:
            if isinstance(auth, tuple):
                auth = Authorization(
                    "basic", {"username": auth[0], "password": auth[1]}
                )
            self.headers.set("Authorization", auth.to_header())
        if json is not None:
            if data is not None:
                raise TypeError("can't provide both json and data")
            data = self.json_dumps(json)
            if self.content_type is None:
                self.content_type = "application/json"
        if data:
            if input_stream is not None:
                raise TypeError("can't provide input stream and data")
            if hasattr(data, "read"):
                data = data.read()
            if isinstance(data, str):
                data = data.encode()
            if isinstance(data, bytes):
                self.input_stream = BytesIO(data)
                if self.content_length is None:
                    self.content_length = len(data)
            else:
                for key, value in _iter_data(data):
                    if isinstance(value, (tuple, dict)) or hasattr(value, "read"):
                        self._add_file_from_data(key, value)
                    else:
                        self.form.setlistdefault(key).append(value)
        if mimetype is not None:
            self.mimetype = mimetype

    @classmethod
    def from_environ(cls, environ: WSGIEnvironment, **kwargs: t.Any) -> EnvironBuilder:
        headers = Headers(EnvironHeaders(environ))
        out = {
            "path": _wsgi_decoding_dance(environ["PATH_INFO"]),
            "base_url": cls._make_base_url(
                environ["wsgi.url_scheme"],
                headers.pop("Host"),
                _wsgi_decoding_dance(environ["SCRIPT_NAME"]),
            ),
            "query_string": _wsgi_decoding_dance(environ["QUERY_STRING"]),
            "method": environ["REQUEST_METHOD"],
            "input_stream": environ["wsgi.input"],
            "content_type": headers.pop("Content-Type", None),
            "content_length": headers.pop("Content-Length", None),
            "errors_stream": environ["wsgi.errors"],
            "multithread": environ["wsgi.multithread"],
            "multiprocess": environ["wsgi.multiprocess"],
            "run_once": environ["wsgi.run_once"],
            "headers": headers,
        }
        out.update(kwargs)
        return cls(**out)

    def _add_file_from_data(
        self,
        key: str,
        value: t.IO[bytes] | tuple[t.IO[bytes], str] | tuple[t.IO[bytes], str, str],
    ) -> None:
        if isinstance(value, tuple):
            self.files.add_file(key, *value)
        else:
            self.files.add_file(key, value)

    @staticmethod
    def _make_base_url(scheme: str, host: str, script_root: str) -> str:
        return urlunsplit((scheme, host, script_root, "", "")).rstrip("/") + "/"

    @property
    def base_url(self) -> str:
        return self._make_base_url(self.url_scheme, self.host, self.script_root)

    @base_url.setter
    def base_url(self, value: str | None) -> None:
        if value is None:
            scheme = "http"
            netloc = "localhost"
            script_root = ""
        else:
            scheme, netloc, script_root, qs, anchor = urlsplit(value)
            if qs or anchor:
                raise ValueError("base url must not contain a query string or fragment")
        self.script_root = script_root.rstrip("/")
        self.host = netloc
        self.url_scheme = scheme

    @property
    def content_type(self) -> str | None:
        ct = self.headers.get("Content-Type")
        if ct is None and not self._input_stream:
            if self._files:
                return "multipart/form-data"
            if self._form:
                return "application/x-www-form-urlencoded"
            return None
        return ct

    @content_type.setter
    def content_type(self, value: str | None) -> None:
        if value is None:
            self.headers.pop("Content-Type", None)
        else:
            self.headers["Content-Type"] = value

    @property
    def mimetype(self) -> str | None:
        ct = self.content_type
        return ct.split(";")[0].strip() if ct else None

    @mimetype.setter
    def mimetype(self, value: str) -> None:
        self.content_type = get_content_type(value, "utf-8")

    @property
    def mimetype_params(self) -> t.Mapping[str, str]:

        def on_update(d: CallbackDict[str, str]) -> None:
            self.headers["Content-Type"] = dump_options_header(self.mimetype, d)

        d = parse_options_header(self.headers.get("content-type", ""))[1]
        return CallbackDict(d, on_update)

    @property
    def content_length(self) -> int | None:
        return self.headers.get("Content-Length", type=int)

    @content_length.setter
    def content_length(self, value: int | None) -> None:
        if value is None:
            self.headers.pop("Content-Length", None)
        else:
            self.headers["Content-Length"] = str(value)

    def _get_form(self, name: str, storage: type[_TAnyMultiDict]) -> _TAnyMultiDict:
        if self.input_stream is not None:
            raise AttributeError("an input stream is defined")
        rv = getattr(self, name)
        if rv is None:
            rv = storage()
            setattr(self, name, rv)
        return rv

    def _set_form(self, name: str, value: MultiDict[str, t.Any]) -> None:
        self._input_stream = None
        setattr(self, name, value)

    @property
    def form(self) -> MultiDict[str, str]:
        return self._get_form("_form", MultiDict)

    @form.setter
    def form(self, value: MultiDict[str, str]) -> None:
        self._set_form("_form", value)

    @property
    def files(self) -> FileMultiDict:
        return self._get_form("_files", FileMultiDict)

    @files.setter
    def files(self, value: FileMultiDict) -> None:
        self._set_form("_files", value)

    @property
    def input_stream(self) -> t.IO[bytes] | None:
        return self._input_stream

    @input_stream.setter
    def input_stream(self, value: t.IO[bytes] | None) -> None:
        self._input_stream = value
        self._form = None
        self._files = None

    @property
    def query_string(self) -> str:
        if self._query_string is None:
            if self._args is not None:
                return _urlencode(self._args)
            return ""
        return self._query_string

    @query_string.setter
    def query_string(self, value: str | None) -> None:
        self._query_string = value
        self._args = None

    @property
    def args(self) -> MultiDict[str, str]:
        if self._query_string is not None:
            raise AttributeError("a query string is defined")
        if self._args is None:
            self._args = MultiDict()
        return self._args

    @args.setter
    def args(self, value: MultiDict[str, str] | None) -> None:
        self._query_string = None
        self._args = value

    @property
    def server_name(self) -> str:
        return self.host.split(":", 1)[0]

    @property
    def server_port(self) -> int:
        pieces = self.host.split(":", 1)
        if len(pieces) == 2:
            try:
                return int(pieces[1])
            except ValueError:
                pass
        if self.url_scheme == "https":
            return 443
        return 80

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def close(self) -> None:
        if self.closed:
            return
        try:
            files = self.files.values()
        except AttributeError:
            files = ()
        for f in files:
            try:
                f.close()
            except Exception:
                pass
        self.closed = True

    def get_environ(self) -> WSGIEnvironment:
        input_stream = self.input_stream
        content_length = self.content_length
        mimetype = self.mimetype
        content_type = self.content_type
        if input_stream is not None:
            start_pos = input_stream.tell()
            input_stream.seek(0, 2)
            end_pos = input_stream.tell()
            input_stream.seek(start_pos)
            content_length = end_pos - start_pos
        elif mimetype == "multipart/form-data":
            input_stream, content_length, boundary = stream_encode_multipart(
                CombinedMultiDict([self.form, self.files])
            )
            content_type = f'{mimetype}; boundary="{boundary}"'
        elif mimetype == "application/x-www-form-urlencoded":
            form_encoded = _urlencode(self.form).encode("ascii")
            content_length = len(form_encoded)
            input_stream = BytesIO(form_encoded)
        else:
            input_stream = BytesIO()
        result: WSGIEnvironment = {}
        if self.environ_base:
            result.update(self.environ_base)

        def _path_encode(x: str) -> str:
            return _wsgi_encoding_dance(unquote(x))

        raw_uri = _wsgi_encoding_dance(self.request_uri)
        result.update(
            {
                "REQUEST_METHOD": self.method,
                "SCRIPT_NAME": _path_encode(self.script_root),
                "PATH_INFO": _path_encode(self.path),
                "QUERY_STRING": _wsgi_encoding_dance(self.query_string),
                "REQUEST_URI": raw_uri,
                "RAW_URI": raw_uri,
                "SERVER_NAME": self.server_name,
                "SERVER_PORT": str(self.server_port),
                "HTTP_HOST": self.host,
                "SERVER_PROTOCOL": self.server_protocol,
                "wsgi.version": self.wsgi_version,
                "wsgi.url_scheme": self.url_scheme,
                "wsgi.input": input_stream,
                "wsgi.errors": self.errors_stream,
                "wsgi.multithread": self.multithread,
                "wsgi.multiprocess": self.multiprocess,
                "wsgi.run_once": self.run_once,
            }
        )
        headers = self.headers.copy()
        headers.remove("Content-Type")
        headers.remove("Content-Length")
        if content_type is not None:
            result["CONTENT_TYPE"] = content_type
        if content_length is not None:
            result["CONTENT_LENGTH"] = str(content_length)
        combined_headers = defaultdict(list)
        for key, value in headers.to_wsgi_list():
            combined_headers[f"HTTP_{key.upper().replace('-', '_')}"].append(value)
        for key, values in combined_headers.items():
            result[key] = ", ".join(values)
        if self.environ_overrides:
            result.update(self.environ_overrides)
        return result

    def get_request(self, cls: type[Request] | None = None) -> Request:
        if cls is None:
            cls = self.request_class
        return cls(self.get_environ())


class ClientRedirectError(Exception):
    pass


class Client:

    def __init__(
        self,
        application: WSGIApplication,
        response_wrapper: type[Response] | None = None,
        use_cookies: bool = True,
        allow_subdomain_redirects: bool = False,
    ) -> None:
        self.application = application
        if response_wrapper in {None, Response}:
            response_wrapper = TestResponse
        elif response_wrapper is not None and not issubclass(
            response_wrapper, TestResponse
        ):
            response_wrapper = type(
                "WrapperTestResponse", (TestResponse, response_wrapper), {}
            )
        self.response_wrapper = t.cast(t.Type["TestResponse"], response_wrapper)
        if use_cookies:
            self._cookies: dict[tuple[str, str, str], Cookie] | None = {}
        else:
            self._cookies = None
        self.allow_subdomain_redirects = allow_subdomain_redirects

    def get_cookie(
        self, key: str, domain: str = "localhost", path: str = "/"
    ) -> Cookie | None:
        if self._cookies is None:
            raise TypeError(
                "Cookies are disabled. Create a client with 'use_cookies=True'."
            )
        return self._cookies.get((domain, path, key))

    def set_cookie(
        self,
        key: str,
        value: str = "",
        *,
        domain: str = "localhost",
        origin_only: bool = True,
        path: str = "/",
        **kwargs: t.Any,
    ) -> None:
        if self._cookies is None:
            raise TypeError(
                "Cookies are disabled. Create a client with 'use_cookies=True'."
            )
        cookie = Cookie._from_response_header(
            domain, "/", dump_cookie(key, value, domain=domain, path=path, **kwargs)
        )
        cookie.origin_only = origin_only
        if cookie._should_delete:
            self._cookies.pop(cookie._storage_key, None)
        else:
            self._cookies[cookie._storage_key] = cookie

    def delete_cookie(
        self, key: str, *, domain: str = "localhost", path: str = "/"
    ) -> None:
        if self._cookies is None:
            raise TypeError(
                "Cookies are disabled. Create a client with 'use_cookies=True'."
            )
        self._cookies.pop((domain, path, key), None)

    def _add_cookies_to_wsgi(self, environ: WSGIEnvironment) -> None:
        if self._cookies is None:
            return
        url = urlsplit(get_current_url(environ))
        server_name = url.hostname or "localhost"
        value = "; ".join(
            c._to_request_header()
            for c in self._cookies.values()
            if c._matches_request(server_name, url.path)
        )
        if value:
            environ["HTTP_COOKIE"] = value
        else:
            environ.pop("HTTP_COOKIE", None)

    def _update_cookies_from_response(
        self, server_name: str, path: str, headers: list[str]
    ) -> None:
        if self._cookies is None:
            return
        for header in headers:
            cookie = Cookie._from_response_header(server_name, path, header)
            if cookie._should_delete:
                self._cookies.pop(cookie._storage_key, None)
            else:
                self._cookies[cookie._storage_key] = cookie

    def run_wsgi_app(
        self, environ: WSGIEnvironment, buffered: bool = False
    ) -> tuple[t.Iterable[bytes], str, Headers]:
        self._add_cookies_to_wsgi(environ)
        rv = run_wsgi_app(self.application, environ, buffered=buffered)
        url = urlsplit(get_current_url(environ))
        self._update_cookies_from_response(
            url.hostname or "localhost", url.path, rv[2].getlist("Set-Cookie")
        )
        return rv

    def resolve_redirect(
        self, response: TestResponse, buffered: bool = False
    ) -> TestResponse:
        scheme, netloc, path, qs, anchor = urlsplit(response.location)
        builder = EnvironBuilder.from_environ(
            response.request.environ, path=path, query_string=qs
        )
        to_name_parts = netloc.split(":", 1)[0].split(".")
        from_name_parts = builder.server_name.split(".")
        if to_name_parts != [""]:
            builder.url_scheme = scheme
            builder.host = netloc
        else:
            to_name_parts = from_name_parts
        if to_name_parts != from_name_parts:
            if to_name_parts[-len(from_name_parts) :] == from_name_parts:
                if not self.allow_subdomain_redirects:
                    raise RuntimeError("Following subdomain redirects is not enabled.")
            else:
                raise RuntimeError("Following external redirects is not supported.")
        path_parts = path.split("/")
        root_parts = builder.script_root.split("/")
        if path_parts[: len(root_parts)] == root_parts:
            builder.path = path[len(builder.script_root) :]
        else:
            builder.path = path
            builder.script_root = ""
        if response.status_code not in {307, 308}:
            if builder.method != "HEAD":
                builder.method = "GET"
            if builder.input_stream is not None:
                builder.input_stream.close()
                builder.input_stream = None
            builder.content_type = None
            builder.content_length = None
            builder.headers.pop("Transfer-Encoding", None)
        return self.open(builder, buffered=buffered)

    def open(
        self,
        *args: t.Any,
        buffered: bool = False,
        follow_redirects: bool = False,
        **kwargs: t.Any,
    ) -> TestResponse:
        request: Request | None = None
        if not kwargs and len(args) == 1:
            arg = args[0]
            if isinstance(arg, EnvironBuilder):
                request = arg.get_request()
            elif isinstance(arg, dict):
                request = EnvironBuilder.from_environ(arg).get_request()
            elif isinstance(arg, Request):
                request = arg
        if request is None:
            builder = EnvironBuilder(*args, **kwargs)
            try:
                request = builder.get_request()
            finally:
                builder.close()
        response_parts = self.run_wsgi_app(request.environ, buffered=buffered)
        response = self.response_wrapper(*response_parts, request=request)
        redirects = set()
        history: list[TestResponse] = []
        if not follow_redirects:
            return response
        while response.status_code in {301, 302, 303, 305, 307, 308}:
            if not buffered:
                response.make_sequence()
                response.close()
            new_redirect_entry = response.location, response.status_code
            if new_redirect_entry in redirects:
                raise ClientRedirectError(
                    f"Loop detected: A {response.status_code} redirect to {response.location} was already made."
                )
            redirects.add(new_redirect_entry)
            response.history = tuple(history)
            history.append(response)
            response = self.resolve_redirect(response, buffered=buffered)
        else:
            response.history = tuple(history)
            response.call_on_close(request.input_stream.close)
            return response

    def get(self, *args: t.Any, **kw: t.Any) -> TestResponse:
        kw["method"] = "GET"
        return self.open(*args, **kw)

    def post(self, *args: t.Any, **kw: t.Any) -> TestResponse:
        kw["method"] = "POST"
        return self.open(*args, **kw)

    def put(self, *args: t.Any, **kw: t.Any) -> TestResponse:
        kw["method"] = "PUT"
        return self.open(*args, **kw)

    def delete(self, *args: t.Any, **kw: t.Any) -> TestResponse:
        kw["method"] = "DELETE"
        return self.open(*args, **kw)

    def patch(self, *args: t.Any, **kw: t.Any) -> TestResponse:
        kw["method"] = "PATCH"
        return self.open(*args, **kw)

    def options(self, *args: t.Any, **kw: t.Any) -> TestResponse:
        kw["method"] = "OPTIONS"
        return self.open(*args, **kw)

    def head(self, *args: t.Any, **kw: t.Any) -> TestResponse:
        kw["method"] = "HEAD"
        return self.open(*args, **kw)

    def trace(self, *args: t.Any, **kw: t.Any) -> TestResponse:
        kw["method"] = "TRACE"
        return self.open(*args, **kw)

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.application!r}>"


def create_environ(*args: t.Any, **kwargs: t.Any) -> WSGIEnvironment:
    builder = EnvironBuilder(*args, **kwargs)
    try:
        return builder.get_environ()
    finally:
        builder.close()


def run_wsgi_app(
    app: WSGIApplication, environ: WSGIEnvironment, buffered: bool = False
) -> tuple[t.Iterable[bytes], str, Headers]:
    environ = _get_environ(environ).copy()
    status: str
    response: tuple[str, list[tuple[str, str]]] | None = None
    buffer: list[bytes] = []

    def start_response(status, headers, exc_info=None):
        nonlocal response
        if exc_info:
            try:
                raise exc_info[1].with_traceback(exc_info[2])
            finally:
                exc_info = None
        response = status, headers
        return buffer.append

    app_rv = app(environ, start_response)
    close_func = getattr(app_rv, "close", None)
    app_iter: t.Iterable[bytes] = iter(app_rv)
    if buffered:
        try:
            app_iter = list(app_iter)
        finally:
            if close_func is not None:
                close_func()
    else:
        for item in app_iter:
            buffer.append(item)
            if response is not None:
                break
        if buffer:
            app_iter = chain(buffer, app_iter)
        if close_func is not None and app_iter is not app_rv:
            app_iter = ClosingIterator(app_iter, close_func)
    status, headers = response
    return app_iter, status, Headers(headers)


class TestResponse(Response):
    default_mimetype = None
    request: Request
    """A request object with the environ used to make the request that
    resulted in this response.
    """
    history: tuple[TestResponse, ...]
    """A list of intermediate responses. Populated when the test request
    is made with ``follow_redirects`` enabled.
    """
    __test__ = False

    def __init__(
        self,
        response: t.Iterable[bytes],
        status: str,
        headers: Headers,
        request: Request,
        history: tuple[TestResponse] = (),
        **kwargs: t.Any,
    ) -> None:
        super().__init__(response, status, headers, **kwargs)
        self.request = request
        self.history = history
        self._compat_tuple = response, status, headers

    @cached_property
    def text(self) -> str:
        return self.get_data(as_text=True)


@dataclasses.dataclass
class Cookie:
    key: str
    """The cookie key, encoded as a client would see it."""
    value: str
    """The cookie key, encoded as a client would see it."""
    decoded_key: str
    """The cookie key, decoded as the application would set and see it."""
    decoded_value: str
    """The cookie value, decoded as the application would set and see it."""
    expires: datetime | None
    """The time at which the cookie is no longer valid."""
    max_age: int | None
    """The number of seconds from when the cookie was set at which it is
    no longer valid.
    """
    domain: str
    """The domain that the cookie was set for, or the request domain if not set."""
    origin_only: bool
    """Whether the cookie will be sent for exact domain matches only. This is ``True``
    if the ``Domain`` parameter was not present.
    """
    path: str
    """The path that the cookie was set for."""
    secure: bool | None
    """The ``Secure`` parameter."""
    http_only: bool | None
    """The ``HttpOnly`` parameter."""
    same_site: str | None
    """The ``SameSite`` parameter."""

    def _matches_request(self, server_name: str, path: str) -> bool:
        return (
            server_name == self.domain
            or not self.origin_only
            and server_name.endswith(self.domain)
            and server_name[: -len(self.domain)].endswith(".")
        ) and (
            path == self.path
            or path.startswith(self.path)
            and path[len(self.path) - self.path.endswith("/") :].startswith("/")
        )

    def _to_request_header(self) -> str:
        return f"{self.key}={self.value}"

    @classmethod
    def _from_response_header(cls, server_name: str, path: str, header: str) -> te.Self:
        header, _, parameters_str = header.partition(";")
        key, _, value = header.partition("=")
        decoded_key, decoded_value = next(parse_cookie(header).items())
        params = {}
        for item in parameters_str.split(";"):
            k, sep, v = item.partition("=")
            params[k.strip().lower()] = v.strip() if sep else None
        return cls(
            key=key.strip(),
            value=value.strip(),
            decoded_key=decoded_key,
            decoded_value=decoded_value,
            expires=parse_date(params.get("expires")),
            max_age=int(params["max-age"] or 0) if "max-age" in params else None,
            domain=params.get("domain") or server_name,
            origin_only="domain" not in params,
            path=params.get("path") or path.rpartition("/")[0] or "/",
            secure="secure" in params,
            http_only="httponly" in params,
            same_site=params.get("samesite"),
        )

    @property
    def _storage_key(self) -> tuple[str, str, str]:
        return self.domain, self.path, self.decoded_key

    @property
    def _should_delete(self) -> bool:
        return (
            self.max_age == 0
            or self.expires is not None
            and self.expires.timestamp() == 0
        )