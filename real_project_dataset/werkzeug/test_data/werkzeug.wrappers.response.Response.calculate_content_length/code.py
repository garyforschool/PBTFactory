from __future__ import annotations
import json
import typing as t
from http import HTTPStatus
from urllib.parse import urljoin
from .._internal import _get_environ
from ..datastructures import Headers
from ..http import generate_etag
from ..http import http_date
from ..http import is_resource_modified
from ..http import parse_etags
from ..http import parse_range_header
from ..http import remove_entity_headers
from ..sansio.response import Response as _SansIOResponse
from ..urls import iri_to_uri
from ..utils import cached_property
from ..wsgi import _RangeWrapper
from ..wsgi import ClosingIterator
from ..wsgi import get_current_url

if t.TYPE_CHECKING:
    from _typeshed.wsgi import StartResponse
    from _typeshed.wsgi import WSGIApplication
    from _typeshed.wsgi import WSGIEnvironment
    from .request import Request


def _iter_encoded(iterable: t.Iterable[str | bytes]) -> t.Iterator[bytes]:
    for item in iterable:
        if isinstance(item, str):
            yield item.encode()
        else:
            yield item


class Response(_SansIOResponse):
    implicit_sequence_conversion = True
    autocorrect_location_header = False
    automatically_set_content_length = True
    response: t.Iterable[str] | t.Iterable[bytes]

    def __init__(
        self,
        response: t.Iterable[bytes] | bytes | t.Iterable[str] | str | None = None,
        status: int | str | HTTPStatus | None = None,
        headers: (
            t.Mapping[str, str | t.Iterable[str]] | t.Iterable[tuple[str, str]] | None
        ) = None,
        mimetype: str | None = None,
        content_type: str | None = None,
        direct_passthrough: bool = False,
    ) -> None:
        super().__init__(
            status=status, headers=headers, mimetype=mimetype, content_type=content_type
        )
        self.direct_passthrough = direct_passthrough
        self._on_close: list[t.Callable[[], t.Any]] = []
        if response is None:
            self.response = []
        elif isinstance(response, (str, bytes, bytearray)):
            self.set_data(response)
        else:
            self.response = response

    def call_on_close(self, func: t.Callable[[], t.Any]) -> t.Callable[[], t.Any]:
        self._on_close.append(func)
        return func

    def __repr__(self) -> str:
        if self.is_sequence:
            body_info = f"{sum(map(len, self.iter_encoded()))} bytes"
        else:
            body_info = "streamed" if self.is_streamed else "likely-streamed"
        return f"<{type(self).__name__} {body_info} [{self.status}]>"

    @classmethod
    def force_type(
        cls, response: Response, environ: WSGIEnvironment | None = None
    ) -> Response:
        if not isinstance(response, Response):
            if environ is None:
                raise TypeError(
                    "cannot convert WSGI application into response objects without an environ"
                )
            from ..test import run_wsgi_app

            response = Response(*run_wsgi_app(response, environ))
        response.__class__ = cls
        return response

    @classmethod
    def from_app(
        cls, app: WSGIApplication, environ: WSGIEnvironment, buffered: bool = False
    ) -> Response:
        from ..test import run_wsgi_app

        return cls(*run_wsgi_app(app, environ, buffered))

    @t.overload
    def get_data(self, as_text: t.Literal[False] = False) -> bytes: ...

    @t.overload
    def get_data(self, as_text: t.Literal[True]) -> str: ...

    def get_data(self, as_text: bool = False) -> bytes | str:
        self._ensure_sequence()
        rv = b"".join(self.iter_encoded())
        if as_text:
            return rv.decode()
        return rv

    def set_data(self, value: bytes | str) -> None:
        if isinstance(value, str):
            value = value.encode()
        self.response = [value]
        if self.automatically_set_content_length:
            self.headers["Content-Length"] = str(len(value))

    data = property(
        get_data,
        set_data,
        doc="A descriptor that calls :meth:`get_data` and :meth:`set_data`.",
    )

    def calculate_content_length(self) -> int | None:
        try:
            self._ensure_sequence()
        except RuntimeError:
            return None
        return sum(len(x) for x in self.iter_encoded())

    def _ensure_sequence(self, mutable: bool = False) -> None:
        if self.is_sequence:
            if mutable and not isinstance(self.response, list):
                self.response = list(self.response)
            return
        if self.direct_passthrough:
            raise RuntimeError(
                "Attempted implicit sequence conversion but the response object is in direct passthrough mode."
            )
        if not self.implicit_sequence_conversion:
            raise RuntimeError(
                "The response object required the iterable to be a sequence, but the implicit conversion was disabled. Call make_sequence() yourself."
            )
        self.make_sequence()

    def make_sequence(self) -> None:
        if not self.is_sequence:
            close = getattr(self.response, "close", None)
            self.response = list(self.iter_encoded())
            if close is not None:
                self.call_on_close(close)

    def iter_encoded(self) -> t.Iterator[bytes]:
        return _iter_encoded(self.response)

    @property
    def is_streamed(self) -> bool:
        try:
            len(self.response)
        except (TypeError, AttributeError):
            return True
        return False

    @property
    def is_sequence(self) -> bool:
        return isinstance(self.response, (tuple, list))

    def close(self) -> None:
        if hasattr(self.response, "close"):
            self.response.close()
        for func in self._on_close:
            func()

    def __enter__(self) -> Response:
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.close()

    def freeze(self) -> None:
        self.response = list(self.iter_encoded())
        self.headers["Content-Length"] = str(sum(map(len, self.response)))
        self.add_etag()

    def get_wsgi_headers(self, environ: WSGIEnvironment) -> Headers:
        headers = Headers(self.headers)
        location: str | None = None
        content_location: str | None = None
        content_length: str | int | None = None
        status = self.status_code
        for key, value in headers:
            ikey = key.lower()
            if ikey == "location":
                location = value
            elif ikey == "content-location":
                content_location = value
            elif ikey == "content-length":
                content_length = value
        if location is not None:
            location = iri_to_uri(location)
            if self.autocorrect_location_header:
                current_url = get_current_url(environ, strip_querystring=True)
                current_url = iri_to_uri(current_url)
                location = urljoin(current_url, location)
            headers["Location"] = location
        if content_location is not None:
            headers["Content-Location"] = iri_to_uri(content_location)
        if 100 <= status < 200 or status == 204:
            headers.remove("Content-Length")
        elif status == 304:
            remove_entity_headers(headers)
        if (
            self.automatically_set_content_length
            and self.is_sequence
            and content_length is None
            and status not in (204, 304)
            and not 100 <= status < 200
        ):
            content_length = sum(len(x) for x in self.iter_encoded())
            headers["Content-Length"] = str(content_length)
        return headers

    def get_app_iter(self, environ: WSGIEnvironment) -> t.Iterable[bytes]:
        status = self.status_code
        if (
            environ["REQUEST_METHOD"] == "HEAD"
            or 100 <= status < 200
            or status in (204, 304)
        ):
            iterable: t.Iterable[bytes] = ()
        elif self.direct_passthrough:
            return self.response
        else:
            iterable = self.iter_encoded()
        return ClosingIterator(iterable, self.close)

    def get_wsgi_response(
        self, environ: WSGIEnvironment
    ) -> tuple[t.Iterable[bytes], str, list[tuple[str, str]]]:
        headers = self.get_wsgi_headers(environ)
        app_iter = self.get_app_iter(environ)
        return app_iter, self.status, headers.to_wsgi_list()

    def __call__(
        self, environ: WSGIEnvironment, start_response: StartResponse
    ) -> t.Iterable[bytes]:
        app_iter, status, headers = self.get_wsgi_response(environ)
        start_response(status, headers)
        return app_iter

    json_module = json

    @property
    def json(self) -> t.Any | None:
        return self.get_json()

    @t.overload
    def get_json(self, force: bool = ..., silent: t.Literal[False] = ...) -> t.Any: ...

    @t.overload
    def get_json(self, force: bool = ..., silent: bool = ...) -> t.Any | None: ...

    def get_json(self, force: bool = False, silent: bool = False) -> t.Any | None:
        if not (force or self.is_json):
            return None
        data = self.get_data()
        try:
            return self.json_module.loads(data)
        except ValueError:
            if not silent:
                raise
            return None

    @cached_property
    def stream(self) -> ResponseStream:
        return ResponseStream(self)

    def _wrap_range_response(self, start: int, length: int) -> None:
        if self.status_code == 206:
            self.response = _RangeWrapper(self.response, start, length)

    def _is_range_request_processable(self, environ: WSGIEnvironment) -> bool:
        return (
            "HTTP_IF_RANGE" not in environ
            or not is_resource_modified(
                environ,
                self.headers.get("etag"),
                None,
                self.headers.get("last-modified"),
                ignore_if_range=False,
            )
        ) and "HTTP_RANGE" in environ

    def _process_range_request(
        self,
        environ: WSGIEnvironment,
        complete_length: int | None,
        accept_ranges: bool | str,
    ) -> bool:
        from ..exceptions import RequestedRangeNotSatisfiable

        if (
            not accept_ranges
            or complete_length is None
            or complete_length == 0
            or not self._is_range_request_processable(environ)
        ):
            return False
        if accept_ranges is True:
            accept_ranges = "bytes"
        parsed_range = parse_range_header(environ.get("HTTP_RANGE"))
        if parsed_range is None:
            raise RequestedRangeNotSatisfiable(complete_length)
        range_tuple = parsed_range.range_for_length(complete_length)
        content_range_header = parsed_range.to_content_range_header(complete_length)
        if range_tuple is None or content_range_header is None:
            raise RequestedRangeNotSatisfiable(complete_length)
        content_length = range_tuple[1] - range_tuple[0]
        self.headers["Content-Length"] = str(content_length)
        self.headers["Accept-Ranges"] = accept_ranges
        self.content_range = content_range_header
        self.status_code = 206
        self._wrap_range_response(range_tuple[0], content_length)
        return True

    def make_conditional(
        self,
        request_or_environ: WSGIEnvironment | Request,
        accept_ranges: bool | str = False,
        complete_length: int | None = None,
    ) -> Response:
        environ = _get_environ(request_or_environ)
        if environ["REQUEST_METHOD"] in ("GET", "HEAD"):
            if "date" not in self.headers:
                self.headers["Date"] = http_date()
            is206 = self._process_range_request(environ, complete_length, accept_ranges)
            if not is206 and not is_resource_modified(
                environ,
                self.headers.get("etag"),
                None,
                self.headers.get("last-modified"),
            ):
                if parse_etags(environ.get("HTTP_IF_MATCH")):
                    self.status_code = 412
                else:
                    self.status_code = 304
            if (
                self.automatically_set_content_length
                and "content-length" not in self.headers
            ):
                length = self.calculate_content_length()
                if length is not None:
                    self.headers["Content-Length"] = str(length)
        return self

    def add_etag(self, overwrite: bool = False, weak: bool = False) -> None:
        if overwrite or "etag" not in self.headers:
            self.set_etag(generate_etag(self.get_data()), weak)


class ResponseStream:
    mode = "wb+"

    def __init__(self, response: Response):
        self.response = response
        self.closed = False

    def write(self, value: bytes) -> int:
        if self.closed:
            raise ValueError("I/O operation on closed file")
        self.response._ensure_sequence(mutable=True)
        self.response.response.append(value)
        self.response.headers.pop("Content-Length", None)
        return len(value)

    def writelines(self, seq: t.Iterable[bytes]) -> None:
        for item in seq:
            self.write(item)

    def close(self) -> None:
        self.closed = True

    def flush(self) -> None:
        if self.closed:
            raise ValueError("I/O operation on closed file")

    def isatty(self) -> bool:
        if self.closed:
            raise ValueError("I/O operation on closed file")
        return False

    def tell(self) -> int:
        self.response._ensure_sequence()
        return sum(map(len, self.response.response))

    @property
    def encoding(self) -> str:
        return "utf-8"