from __future__ import annotations
import io
import typing as t
from functools import partial
from functools import update_wrapper
from .exceptions import ClientDisconnected
from .exceptions import RequestEntityTooLarge
from .sansio import utils as _sansio_utils
from .sansio.utils import host_is_trusted

if t.TYPE_CHECKING:
    from _typeshed.wsgi import WSGIApplication
    from _typeshed.wsgi import WSGIEnvironment


def responder(f: t.Callable[..., WSGIApplication]) -> WSGIApplication:
    return update_wrapper(lambda *a: f(*a)(*a[-2:]), f)


def get_current_url(
    environ: WSGIEnvironment,
    root_only: bool = False,
    strip_querystring: bool = False,
    host_only: bool = False,
    trusted_hosts: t.Iterable[str] | None = None,
) -> str:
    parts = {
        "scheme": environ["wsgi.url_scheme"],
        "host": get_host(environ, trusted_hosts),
    }
    if not host_only:
        parts["root_path"] = environ.get("SCRIPT_NAME", "")
        if not root_only:
            parts["path"] = environ.get("PATH_INFO", "")
            if not strip_querystring:
                parts["query_string"] = environ.get("QUERY_STRING", "").encode("latin1")
    return _sansio_utils.get_current_url(**parts)


def _get_server(environ: WSGIEnvironment) -> tuple[str, int | None] | None:
    name = environ.get("SERVER_NAME")
    if name is None:
        return None
    try:
        port: int | None = int(environ.get("SERVER_PORT", None))
    except (TypeError, ValueError):
        port = None
    return name, port


def get_host(
    environ: WSGIEnvironment, trusted_hosts: t.Iterable[str] | None = None
) -> str:
    return _sansio_utils.get_host(
        environ["wsgi.url_scheme"],
        environ.get("HTTP_HOST"),
        _get_server(environ),
        trusted_hosts,
    )


def get_content_length(environ: WSGIEnvironment) -> int | None:
    return _sansio_utils.get_content_length(
        http_content_length=environ.get("CONTENT_LENGTH"),
        http_transfer_encoding=environ.get("HTTP_TRANSFER_ENCODING"),
    )


def get_input_stream(
    environ: WSGIEnvironment,
    safe_fallback: bool = True,
    max_content_length: int | None = None,
) -> t.IO[bytes]:
    stream = t.cast(t.IO[bytes], environ["wsgi.input"])
    content_length = get_content_length(environ)
    if content_length is not None and max_content_length is not None:
        if content_length > max_content_length:
            raise RequestEntityTooLarge()
    if "wsgi.input_terminated" in environ:
        if max_content_length is not None:
            return t.cast(
                t.IO[bytes], LimitedStream(stream, max_content_length, is_max=True)
            )
        return stream
    if content_length is None:
        return io.BytesIO() if safe_fallback else stream
    return t.cast(t.IO[bytes], LimitedStream(stream, content_length))


def get_path_info(environ: WSGIEnvironment) -> str:
    path: bytes = environ.get("PATH_INFO", "").encode("latin1")
    return path.decode(errors="replace")


class ClosingIterator:

    def __init__(
        self,
        iterable: t.Iterable[bytes],
        callbacks: None | (
            t.Callable[[], None] | t.Iterable[t.Callable[[], None]]
        ) = None,
    ) -> None:
        iterator = iter(iterable)
        self._next = t.cast(t.Callable[[], bytes], partial(next, iterator))
        if callbacks is None:
            callbacks = []
        elif callable(callbacks):
            callbacks = [callbacks]
        else:
            callbacks = list(callbacks)
        iterable_close = getattr(iterable, "close", None)
        if iterable_close:
            callbacks.insert(0, iterable_close)
        self._callbacks = callbacks

    def __iter__(self) -> ClosingIterator:
        return self

    def __next__(self) -> bytes:
        return self._next()

    def close(self) -> None:
        for callback in self._callbacks:
            callback()


def wrap_file(
    environ: WSGIEnvironment, file: t.IO[bytes], buffer_size: int = 8192
) -> t.Iterable[bytes]:
    return environ.get("wsgi.file_wrapper", FileWrapper)(file, buffer_size)


class FileWrapper:

    def __init__(self, file: t.IO[bytes], buffer_size: int = 8192) -> None:
        self.file = file
        self.buffer_size = buffer_size

    def close(self) -> None:
        if hasattr(self.file, "close"):
            self.file.close()

    def seekable(self) -> bool:
        if hasattr(self.file, "seekable"):
            return self.file.seekable()
        if hasattr(self.file, "seek"):
            return True
        return False

    def seek(self, *args: t.Any) -> None:
        if hasattr(self.file, "seek"):
            self.file.seek(*args)

    def tell(self) -> int | None:
        if hasattr(self.file, "tell"):
            return self.file.tell()
        return None

    def __iter__(self) -> FileWrapper:
        return self

    def __next__(self) -> bytes:
        data = self.file.read(self.buffer_size)
        if data:
            return data
        raise StopIteration()


class _RangeWrapper:

    def __init__(
        self,
        iterable: t.Iterable[bytes] | t.IO[bytes],
        start_byte: int = 0,
        byte_range: int | None = None,
    ):
        self.iterable = iter(iterable)
        self.byte_range = byte_range
        self.start_byte = start_byte
        self.end_byte = None
        if byte_range is not None:
            self.end_byte = start_byte + byte_range
        self.read_length = 0
        self.seekable = hasattr(iterable, "seekable") and iterable.seekable()
        self.end_reached = False

    def __iter__(self) -> _RangeWrapper:
        return self

    def _next_chunk(self) -> bytes:
        try:
            chunk = next(self.iterable)
            self.read_length += len(chunk)
            return chunk
        except StopIteration:
            self.end_reached = True
            raise

    def _first_iteration(self) -> tuple[bytes | None, int]:
        chunk = None
        if self.seekable:
            self.iterable.seek(self.start_byte)
            self.read_length = self.iterable.tell()
            contextual_read_length = self.read_length
        else:
            while self.read_length <= self.start_byte:
                chunk = self._next_chunk()
            if chunk is not None:
                chunk = chunk[self.start_byte - self.read_length :]
            contextual_read_length = self.start_byte
        return chunk, contextual_read_length

    def _next(self) -> bytes:
        if self.end_reached:
            raise StopIteration()
        chunk = None
        contextual_read_length = self.read_length
        if self.read_length == 0:
            chunk, contextual_read_length = self._first_iteration()
        if chunk is None:
            chunk = self._next_chunk()
        if self.end_byte is not None and self.read_length >= self.end_byte:
            self.end_reached = True
            return chunk[: self.end_byte - contextual_read_length]
        return chunk

    def __next__(self) -> bytes:
        chunk = self._next()
        if chunk:
            return chunk
        self.end_reached = True
        raise StopIteration()

    def close(self) -> None:
        if hasattr(self.iterable, "close"):
            self.iterable.close()


class LimitedStream(io.RawIOBase):

    def __init__(self, stream: t.IO[bytes], limit: int, is_max: bool = False) -> None:
        self._stream = stream
        self._pos = 0
        self.limit = limit
        self._limit_is_max = is_max

    @property
    def is_exhausted(self) -> bool:
        return self._pos >= self.limit

    def on_exhausted(self) -> None:
        if self._limit_is_max:
            raise RequestEntityTooLarge()

    def on_disconnect(self, error: Exception | None = None) -> None:
        if not self._limit_is_max or error is not None:
            raise ClientDisconnected()

    def exhaust(self) -> bytes:
        if not self.is_exhausted:
            return self.readall()
        return b""

    def readinto(self, b: bytearray) -> int | None:
        size = len(b)
        remaining = self.limit - self._pos
        if remaining <= 0:
            self.on_exhausted()
            return 0
        if hasattr(self._stream, "readinto"):
            if size <= remaining:
                try:
                    out_size: int | None = self._stream.readinto(b)
                except (OSError, ValueError) as e:
                    self.on_disconnect(error=e)
                    return 0
            else:
                temp_b = bytearray(remaining)
                try:
                    out_size = self._stream.readinto(temp_b)
                except (OSError, ValueError) as e:
                    self.on_disconnect(error=e)
                    return 0
                if out_size:
                    b[:out_size] = temp_b
        else:
            try:
                data = self._stream.read(min(size, remaining))
            except (OSError, ValueError) as e:
                self.on_disconnect(error=e)
                return 0
            out_size = len(data)
            b[:out_size] = data
        if not out_size:
            self.on_disconnect()
            return 0
        self._pos += out_size
        return out_size

    def readall(self) -> bytes:
        if self.is_exhausted:
            self.on_exhausted()
            return b""
        out = bytearray()
        while not self.is_exhausted:
            data = self.read(1024 * 64)
            if not data:
                break
            out.extend(data)
        return bytes(out)

    def tell(self) -> int:
        return self._pos

    def readable(self) -> bool:
        return True