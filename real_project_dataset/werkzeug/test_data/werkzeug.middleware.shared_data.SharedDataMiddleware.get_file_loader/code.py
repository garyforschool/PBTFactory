"""
Serve Shared Static Files
=========================

.. autoclass:: SharedDataMiddleware
    :members: is_allowed

:copyright: 2007 Pallets
:license: BSD-3-Clause
"""

from __future__ import annotations
import importlib.util
import mimetypes
import os
import posixpath
import typing as t
from datetime import datetime
from datetime import timezone
from io import BytesIO
from time import time
from zlib import adler32
from ..http import http_date
from ..http import is_resource_modified
from ..security import safe_join
from ..utils import get_content_type
from ..wsgi import get_path_info
from ..wsgi import wrap_file

_TOpener = t.Callable[[], t.Tuple[t.IO[bytes], datetime, int]]
_TLoader = t.Callable[[t.Optional[str]], t.Tuple[t.Optional[str], t.Optional[_TOpener]]]
if t.TYPE_CHECKING:
    from _typeshed.wsgi import StartResponse
    from _typeshed.wsgi import WSGIApplication
    from _typeshed.wsgi import WSGIEnvironment


class SharedDataMiddleware:

    def __init__(
        self,
        app: WSGIApplication,
        exports: (
            dict[str, str | tuple[str, str]]
            | t.Iterable[tuple[str, str | tuple[str, str]]]
        ),
        disallow: None = None,
        cache: bool = True,
        cache_timeout: int = 60 * 60 * 12,
        fallback_mimetype: str = "application/octet-stream",
    ) -> None:
        self.app = app
        self.exports: list[tuple[str, _TLoader]] = []
        self.cache = cache
        self.cache_timeout = cache_timeout
        if isinstance(exports, dict):
            exports = exports.items()
        for key, value in exports:
            if isinstance(value, tuple):
                loader = self.get_package_loader(*value)
            elif isinstance(value, str):
                if os.path.isfile(value):
                    loader = self.get_file_loader(value)
                else:
                    loader = self.get_directory_loader(value)
            else:
                raise TypeError(f"unknown def {value!r}")
            self.exports.append((key, loader))
        if disallow is not None:
            from fnmatch import fnmatch

            self.is_allowed = lambda x: not fnmatch(x, disallow)
        self.fallback_mimetype = fallback_mimetype

    def is_allowed(self, filename: str) -> bool:
        return True

    def _opener(self, filename: str) -> _TOpener:
        return lambda: (
            open(filename, "rb"),
            datetime.fromtimestamp(os.path.getmtime(filename), tz=timezone.utc),
            int(os.path.getsize(filename)),
        )

    def get_file_loader(self, filename: str) -> _TLoader:
        return lambda x: (os.path.basename(filename), self._opener(filename))

    def get_package_loader(self, package: str, package_path: str) -> _TLoader:
        load_time = datetime.now(timezone.utc)
        spec = importlib.util.find_spec(package)
        reader = spec.loader.get_resource_reader(package)

        def loader(path: str | None) -> tuple[str | None, _TOpener | None]:
            if path is None:
                return None, None
            path = safe_join(package_path, path)
            if path is None:
                return None, None
            basename = posixpath.basename(path)
            try:
                resource = reader.open_resource(path)
            except OSError:
                return None, None
            if isinstance(resource, BytesIO):
                return basename, lambda: (resource, load_time, len(resource.getvalue()))
            return basename, lambda: (
                resource,
                datetime.fromtimestamp(
                    os.path.getmtime(resource.name), tz=timezone.utc
                ),
                os.path.getsize(resource.name),
            )

        return loader

    def get_directory_loader(self, directory: str) -> _TLoader:

        def loader(path: str | None) -> tuple[str | None, _TOpener | None]:
            if path is not None:
                path = safe_join(directory, path)
                if path is None:
                    return None, None
            else:
                path = directory
            if os.path.isfile(path):
                return os.path.basename(path), self._opener(path)
            return None, None

        return loader

    def generate_etag(self, mtime: datetime, file_size: int, real_filename: str) -> str:
        fn_str = os.fsencode(real_filename)
        timestamp = mtime.timestamp()
        checksum = adler32(fn_str) & 4294967295
        return f"wzsdm-{timestamp}-{file_size}-{checksum}"

    def __call__(
        self, environ: WSGIEnvironment, start_response: StartResponse
    ) -> t.Iterable[bytes]:
        path = get_path_info(environ)
        file_loader = None
        for search_path, loader in self.exports:
            if search_path == path:
                real_filename, file_loader = loader(None)
                if file_loader is not None:
                    break
            if not search_path.endswith("/"):
                search_path += "/"
            if path.startswith(search_path):
                real_filename, file_loader = loader(path[len(search_path) :])
                if file_loader is not None:
                    break
        if file_loader is None or not self.is_allowed(real_filename):
            return self.app(environ, start_response)
        guessed_type = mimetypes.guess_type(real_filename)
        mime_type = get_content_type(guessed_type[0] or self.fallback_mimetype, "utf-8")
        f, mtime, file_size = file_loader()
        headers = [("Date", http_date())]
        if self.cache:
            timeout = self.cache_timeout
            etag = self.generate_etag(mtime, file_size, real_filename)
            headers += [
                ("Etag", f'"{etag}"'),
                ("Cache-Control", f"max-age={timeout}, public"),
            ]
            if not is_resource_modified(environ, etag, last_modified=mtime):
                f.close()
                start_response("304 Not Modified", headers)
                return []
            headers.append(("Expires", http_date(time() + timeout)))
        else:
            headers.append(("Cache-Control", "public"))
        headers.extend(
            (
                ("Content-Type", mime_type),
                ("Content-Length", str(file_size)),
                ("Last-Modified", http_date(mtime)),
            )
        )
        start_response("200 OK", headers)
        return wrap_file(environ, f)