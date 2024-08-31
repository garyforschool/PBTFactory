"""
Application Profiler
====================

This module provides a middleware that profiles each request with the
:mod:`cProfile` module. This can help identify bottlenecks in your code
that may be slowing down your application.

.. autoclass:: ProfilerMiddleware

:copyright: 2007 Pallets
:license: BSD-3-Clause
"""

from __future__ import annotations
import os.path
import sys
import time
import typing as t
from pstats import Stats

try:
    from cProfile import Profile
except ImportError:
    from profile import Profile
if t.TYPE_CHECKING:
    from _typeshed.wsgi import StartResponse
    from _typeshed.wsgi import WSGIApplication
    from _typeshed.wsgi import WSGIEnvironment


class ProfilerMiddleware:

    def __init__(
        self,
        app: WSGIApplication,
        stream: t.IO[str] | None = sys.stdout,
        sort_by: t.Iterable[str] = ("time", "calls"),
        restrictions: t.Iterable[str | int | float] = (),
        profile_dir: str | None = None,
        filename_format: str = "{method}.{path}.{elapsed:.0f}ms.{time:.0f}.prof",
    ) -> None:
        self._app = app
        self._stream = stream
        self._sort_by = sort_by
        self._restrictions = restrictions
        self._profile_dir = profile_dir
        self._filename_format = filename_format

    def __call__(
        self, environ: WSGIEnvironment, start_response: StartResponse
    ) -> t.Iterable[bytes]:
        response_body: list[bytes] = []

        def catching_start_response(status, headers, exc_info=None):
            start_response(status, headers, exc_info)
            return response_body.append

        def runapp() -> None:
            app_iter = self._app(
                environ, t.cast("StartResponse", catching_start_response)
            )
            response_body.extend(app_iter)
            if hasattr(app_iter, "close"):
                app_iter.close()

        profile = Profile()
        start = time.time()
        profile.runcall(runapp)
        body = b"".join(response_body)
        elapsed = time.time() - start
        if self._profile_dir is not None:
            if callable(self._filename_format):
                environ["werkzeug.profiler"] = {
                    "elapsed": elapsed * 1000.0,
                    "time": time.time(),
                }
                filename = self._filename_format(environ)
            else:
                filename = self._filename_format.format(
                    method=environ["REQUEST_METHOD"],
                    path=environ["PATH_INFO"].strip("/").replace("/", ".") or "root",
                    elapsed=elapsed * 1000.0,
                    time=time.time(),
                )
            filename = os.path.join(self._profile_dir, filename)
            profile.dump_stats(filename)
        if self._stream is not None:
            stats = Stats(profile, stream=self._stream)
            stats.sort_stats(*self._sort_by)
            print("-" * 80, file=self._stream)
            path_info = environ.get("PATH_INFO", "")
            print(f"PATH: {path_info!r}", file=self._stream)
            stats.print_stats(*self._restrictions)
            print(f"{'-' * 80}\n", file=self._stream)
        return [body]
