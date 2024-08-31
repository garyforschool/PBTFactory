"""
X-Forwarded-For Proxy Fix
=========================

This module provides a middleware that adjusts the WSGI environ based on
``X-Forwarded-`` headers that proxies in front of an application may
set.

When an application is running behind a proxy server, WSGI may see the
request as coming from that server rather than the real client. Proxies
set various headers to track where the request actually came from.

This middleware should only be used if the application is actually
behind such a proxy, and should be configured with the number of proxies
that are chained in front of it. Not all proxies set all the headers.
Since incoming headers can be faked, you must set how many proxies are
setting each header so the middleware knows what to trust.

.. autoclass:: ProxyFix

:copyright: 2007 Pallets
:license: BSD-3-Clause
"""

from __future__ import annotations
import typing as t
from ..http import parse_list_header

if t.TYPE_CHECKING:
    from _typeshed.wsgi import StartResponse
    from _typeshed.wsgi import WSGIApplication
    from _typeshed.wsgi import WSGIEnvironment


class ProxyFix:

    def __init__(
        self,
        app: WSGIApplication,
        x_for: int = 1,
        x_proto: int = 1,
        x_host: int = 0,
        x_port: int = 0,
        x_prefix: int = 0,
    ) -> None:
        self.app = app
        self.x_for = x_for
        self.x_proto = x_proto
        self.x_host = x_host
        self.x_port = x_port
        self.x_prefix = x_prefix

    def _get_real_value(self, trusted: int, value: str | None) -> str | None:
        if not (trusted and value):
            return None
        values = parse_list_header(value)
        if len(values) >= trusted:
            return values[-trusted]
        return None

    def __call__(
        self, environ: WSGIEnvironment, start_response: StartResponse
    ) -> t.Iterable[bytes]:
        environ_get = environ.get
        orig_remote_addr = environ_get("REMOTE_ADDR")
        orig_wsgi_url_scheme = environ_get("wsgi.url_scheme")
        orig_http_host = environ_get("HTTP_HOST")
        environ.update(
            {
                "werkzeug.proxy_fix.orig": {
                    "REMOTE_ADDR": orig_remote_addr,
                    "wsgi.url_scheme": orig_wsgi_url_scheme,
                    "HTTP_HOST": orig_http_host,
                    "SERVER_NAME": environ_get("SERVER_NAME"),
                    "SERVER_PORT": environ_get("SERVER_PORT"),
                    "SCRIPT_NAME": environ_get("SCRIPT_NAME"),
                }
            }
        )
        x_for = self._get_real_value(self.x_for, environ_get("HTTP_X_FORWARDED_FOR"))
        if x_for:
            environ["REMOTE_ADDR"] = x_for
        x_proto = self._get_real_value(
            self.x_proto, environ_get("HTTP_X_FORWARDED_PROTO")
        )
        if x_proto:
            environ["wsgi.url_scheme"] = x_proto
        x_host = self._get_real_value(self.x_host, environ_get("HTTP_X_FORWARDED_HOST"))
        if x_host:
            environ["HTTP_HOST"] = environ["SERVER_NAME"] = x_host
            if ":" in x_host and not x_host.endswith("]"):
                environ["SERVER_NAME"], environ["SERVER_PORT"] = x_host.rsplit(":", 1)
        x_port = self._get_real_value(self.x_port, environ_get("HTTP_X_FORWARDED_PORT"))
        if x_port:
            host = environ.get("HTTP_HOST")
            if host:
                if ":" in host and not host.endswith("]"):
                    host = host.rsplit(":", 1)[0]
                environ["HTTP_HOST"] = f"{host}:{x_port}"
            environ["SERVER_PORT"] = x_port
        x_prefix = self._get_real_value(
            self.x_prefix, environ_get("HTTP_X_FORWARDED_PREFIX")
        )
        if x_prefix:
            environ["SCRIPT_NAME"] = x_prefix
        return self.app(environ, start_response)