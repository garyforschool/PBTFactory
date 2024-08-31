from __future__ import annotations
import mimetypes
from io import BytesIO
from os import fsdecode
from os import fspath
from .._internal import _plain_int
from .structures import MultiDict


class FileStorage:

    def __init__(
        self,
        stream=None,
        filename=None,
        name=None,
        content_type=None,
        content_length=None,
        headers=None,
    ):
        self.name = name
        self.stream = stream or BytesIO()
        if filename is None:
            filename = getattr(stream, "name", None)
            if filename is not None:
                filename = fsdecode(filename)
            if filename and filename[0] == "<" and filename[-1] == ">":
                filename = None
        else:
            filename = fsdecode(filename)
        self.filename = filename
        if headers is None:
            from .headers import Headers

            headers = Headers()
        self.headers = headers
        if content_type is not None:
            headers["Content-Type"] = content_type
        if content_length is not None:
            headers["Content-Length"] = str(content_length)

    def _parse_content_type(self):
        if not hasattr(self, "_parsed_content_type"):
            self._parsed_content_type = http.parse_options_header(self.content_type)

    @property
    def content_type(self):
        return self.headers.get("content-type")

    @property
    def content_length(self):
        if "content-length" in self.headers:
            try:
                return _plain_int(self.headers["content-length"])
            except ValueError:
                pass
        return 0

    @property
    def mimetype(self):
        self._parse_content_type()
        return self._parsed_content_type[0].lower()

    @property
    def mimetype_params(self):
        self._parse_content_type()
        return self._parsed_content_type[1]

    def save(self, dst, buffer_size=16384):
        from shutil import copyfileobj

        close_dst = False
        if hasattr(dst, "__fspath__"):
            dst = fspath(dst)
        if isinstance(dst, str):
            dst = open(dst, "wb")
            close_dst = True
        try:
            copyfileobj(self.stream, dst, buffer_size)
        finally:
            if close_dst:
                dst.close()

    def close(self):
        try:
            self.stream.close()
        except Exception:
            pass

    def __bool__(self):
        return bool(self.filename)

    def __getattr__(self, name):
        try:
            return getattr(self.stream, name)
        except AttributeError:
            if hasattr(self.stream, "_file"):
                return getattr(self.stream._file, name)
            raise

    def __iter__(self):
        return iter(self.stream)

    def __repr__(self):
        return f"<{type(self).__name__}: {self.filename!r} ({self.content_type!r})>"


class FileMultiDict(MultiDict):

    def add_file(self, name, file, filename=None, content_type=None):
        if isinstance(file, FileStorage):
            value = file
        else:
            if isinstance(file, str):
                if filename is None:
                    filename = file
                file = open(file, "rb")
            if filename and content_type is None:
                content_type = (
                    mimetypes.guess_type(filename)[0] or "application/octet-stream"
                )
            value = FileStorage(file, filename, name, content_type)
        self.add(name, value)


from .. import http
