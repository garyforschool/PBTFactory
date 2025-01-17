"""A WSGI and HTTP server for use **during development only**. This
server is convenient to use, but is not designed to be particularly
stable, secure, or efficient. Use a dedicate WSGI server and HTTP
server when deploying to production.

It provides features like interactive debugging and code reloading. Use
``run_simple`` to start the server. Put this in a ``run.py`` script:

.. code-block:: python

    from myapp import create_app
    from werkzeug import run_simple
"""

from __future__ import annotations
import errno
import io
import os
import selectors
import socket
import socketserver
import sys
import typing as t
from datetime import datetime as dt
from datetime import timedelta
from datetime import timezone
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from urllib.parse import unquote
from urllib.parse import urlsplit
from ._internal import _log
from ._internal import _wsgi_encoding_dance
from .exceptions import InternalServerError
from .urls import uri_to_iri

try:
    import ssl
except ImportError:

    class _SslDummy:

        def __getattr__(self, name: str) -> t.Any:
            raise RuntimeError(
                "SSL is unavailable because this Python runtime was not compiled with SSL/TLS support."
            )

    ssl = _SslDummy()
_log_add_style = True
if os.name == "nt":
    try:
        __import__("colorama")
    except ImportError:
        _log_add_style = False
can_fork = hasattr(os, "fork")
if can_fork:
    ForkingMixIn = socketserver.ForkingMixIn
else:

    class ForkingMixIn:
        pass


try:
    af_unix = socket.AF_UNIX
except AttributeError:
    af_unix = None
LISTEN_QUEUE = 128
_TSSLContextArg = t.Optional[
    t.Union["ssl.SSLContext", t.Tuple[str, t.Optional[str]], t.Literal["adhoc"]]
]
if t.TYPE_CHECKING:
    from _typeshed.wsgi import WSGIApplication
    from _typeshed.wsgi import WSGIEnvironment
    from cryptography.hazmat.primitives.asymmetric.rsa import (
        RSAPrivateKeyWithSerialization,
    )
    from cryptography.x509 import Certificate


class DechunkedInput(io.RawIOBase):

    def __init__(self, rfile: t.IO[bytes]) -> None:
        self._rfile = rfile
        self._done = False
        self._len = 0

    def readable(self) -> bool:
        return True

    def read_chunk_len(self) -> int:
        try:
            line = self._rfile.readline().decode("latin1")
            _len = int(line.strip(), 16)
        except ValueError as e:
            raise OSError("Invalid chunk header") from e
        if _len < 0:
            raise OSError("Negative chunk length not allowed")
        return _len

    def readinto(self, buf: bytearray) -> int:
        read = 0
        while not self._done and read < len(buf):
            if self._len == 0:
                self._len = self.read_chunk_len()
            if self._len == 0:
                self._done = True
            if self._len > 0:
                n = min(len(buf), self._len)
                if read + n > len(buf):
                    buf[read:] = self._rfile.read(len(buf) - read)
                    self._len -= len(buf) - read
                    read = len(buf)
                else:
                    buf[read : read + n] = self._rfile.read(n)
                    self._len -= n
                    read += n
            if self._len == 0:
                terminator = self._rfile.readline()
                if terminator not in (b"\n", b"\r\n", b"\r"):
                    raise OSError("Missing chunk terminating newline")
        return read


class WSGIRequestHandler(BaseHTTPRequestHandler):
    server: BaseWSGIServer

    @property
    def server_version(self) -> str:
        return self.server._server_version

    def make_environ(self) -> WSGIEnvironment:
        request_url = urlsplit(self.path)
        url_scheme = "http" if self.server.ssl_context is None else "https"
        if not self.client_address:
            self.client_address = "<local>", 0
        elif isinstance(self.client_address, str):
            self.client_address = self.client_address, 0
        if not request_url.scheme and request_url.netloc:
            path_info = f"/{request_url.netloc}{request_url.path}"
        else:
            path_info = request_url.path
        path_info = unquote(path_info)
        environ: WSGIEnvironment = {
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": url_scheme,
            "wsgi.input": self.rfile,
            "wsgi.errors": sys.stderr,
            "wsgi.multithread": self.server.multithread,
            "wsgi.multiprocess": self.server.multiprocess,
            "wsgi.run_once": False,
            "werkzeug.socket": self.connection,
            "SERVER_SOFTWARE": self.server_version,
            "REQUEST_METHOD": self.command,
            "SCRIPT_NAME": "",
            "PATH_INFO": _wsgi_encoding_dance(path_info),
            "QUERY_STRING": _wsgi_encoding_dance(request_url.query),
            "REQUEST_URI": _wsgi_encoding_dance(self.path),
            "RAW_URI": _wsgi_encoding_dance(self.path),
            "REMOTE_ADDR": self.address_string(),
            "REMOTE_PORT": self.port_integer(),
            "SERVER_NAME": self.server.server_address[0],
            "SERVER_PORT": str(self.server.server_address[1]),
            "SERVER_PROTOCOL": self.request_version,
        }
        for key, value in self.headers.items():
            if "_" in key:
                continue
            key = key.upper().replace("-", "_")
            value = value.replace("\r\n", "")
            if key not in ("CONTENT_TYPE", "CONTENT_LENGTH"):
                key = f"HTTP_{key}"
                if key in environ:
                    value = f"{environ[key]},{value}"
            environ[key] = value
        if environ.get("HTTP_TRANSFER_ENCODING", "").strip().lower() == "chunked":
            environ["wsgi.input_terminated"] = True
            environ["wsgi.input"] = DechunkedInput(environ["wsgi.input"])
        if request_url.scheme and request_url.netloc:
            environ["HTTP_HOST"] = request_url.netloc
        try:
            peer_cert = self.connection.getpeercert(binary_form=True)
            if peer_cert is not None:
                environ["SSL_CLIENT_CERT"] = ssl.DER_cert_to_PEM_cert(peer_cert)
        except ValueError:
            self.server.log("error", "Cannot fetch SSL peer certificate info")
        except AttributeError:
            pass
        return environ

    def run_wsgi(self) -> None:
        if self.headers.get("Expect", "").lower().strip() == "100-continue":
            self.wfile.write(b"HTTP/1.1 100 Continue\r\n\r\n")
        self.environ = environ = self.make_environ()
        status_set: str | None = None
        headers_set: list[tuple[str, str]] | None = None
        status_sent: str | None = None
        headers_sent: list[tuple[str, str]] | None = None
        chunk_response: bool = False

        def write(data: bytes) -> None:
            nonlocal status_sent, headers_sent, chunk_response
            assert status_set is not None, "write() before start_response"
            assert headers_set is not None, "write() before start_response"
            if status_sent is None:
                status_sent = status_set
                headers_sent = headers_set
                try:
                    code_str, msg = status_sent.split(None, 1)
                except ValueError:
                    code_str, msg = status_sent, ""
                code = int(code_str)
                self.send_response(code, msg)
                header_keys = set()
                for key, value in headers_sent:
                    self.send_header(key, value)
                    header_keys.add(key.lower())
                if (
                    not (
                        "content-length" in header_keys
                        or environ["REQUEST_METHOD"] == "HEAD"
                        or 100 <= code < 200
                        or code in {204, 304}
                    )
                    and self.protocol_version >= "HTTP/1.1"
                ):
                    chunk_response = True
                    self.send_header("Transfer-Encoding", "chunked")
                self.send_header("Connection", "close")
                self.end_headers()
            assert isinstance(data, bytes), "applications must write bytes"
            if data:
                if chunk_response:
                    self.wfile.write(hex(len(data))[2:].encode())
                    self.wfile.write(b"\r\n")
                self.wfile.write(data)
                if chunk_response:
                    self.wfile.write(b"\r\n")
            self.wfile.flush()

        def start_response(status, headers, exc_info=None):
            nonlocal status_set, headers_set
            if exc_info:
                try:
                    if headers_sent:
                        raise exc_info[1].with_traceback(exc_info[2])
                finally:
                    exc_info = None
            elif headers_set:
                raise AssertionError("Headers already set")
            status_set = status
            headers_set = headers
            return write

        def execute(app: WSGIApplication) -> None:
            application_iter = app(environ, start_response)
            try:
                for data in application_iter:
                    write(data)
                if not headers_sent:
                    write(b"")
                if chunk_response:
                    self.wfile.write(b"0\r\n\r\n")
            finally:
                selector = selectors.DefaultSelector()
                selector.register(self.connection, selectors.EVENT_READ)
                total_size = 0
                total_reads = 0
                while selector.select(timeout=0.01):
                    data = self.rfile.read(10000000)
                    total_size += len(data)
                    total_reads += 1
                    if not data or total_size >= 10000000000 or total_reads > 1000:
                        break
                selector.close()
                if hasattr(application_iter, "close"):
                    application_iter.close()

        try:
            execute(self.server.app)
        except (ConnectionError, socket.timeout) as e:
            self.connection_dropped(e, environ)
        except Exception as e:
            if self.server.passthrough_errors:
                raise
            if status_sent is not None and chunk_response:
                self.close_connection = True
            try:
                if status_sent is None:
                    status_set = None
                    headers_set = None
                execute(InternalServerError())
            except Exception:
                pass
            from .debug.tbtools import DebugTraceback

            msg = DebugTraceback(e).render_traceback_text()
            self.server.log("error", f"Error on request:\n{msg}")

    def handle(self) -> None:
        try:
            super().handle()
        except (ConnectionError, socket.timeout) as e:
            self.connection_dropped(e)
        except Exception as e:
            if self.server.ssl_context is not None and is_ssl_error(e):
                self.log_error("SSL error occurred: %s", e)
            else:
                raise

    def connection_dropped(
        self, error: BaseException, environ: WSGIEnvironment | None = None
    ) -> None:
        pass

    def __getattr__(self, name: str) -> t.Any:
        if name.startswith("do_"):
            return self.run_wsgi
        return getattr(super(), name)

    def address_string(self) -> str:
        if getattr(self, "environ", None):
            return self.environ["REMOTE_ADDR"]
        if not self.client_address:
            return "<local>"
        return self.client_address[0]

    def port_integer(self) -> int:
        return self.client_address[1]

    _control_char_table = str.maketrans(
        {c: f"\\x{c:02x}" for c in [*range(32), *range(127, 160)]}
    )
    _control_char_table[ord("\\")] = "\\\\"

    def log_request(self, code: int | str = "-", size: int | str = "-") -> None:
        try:
            path = uri_to_iri(self.path)
            msg = f"{self.command} {path} {self.request_version}"
        except AttributeError:
            msg = self.requestline
        msg = msg.translate(self._control_char_table)
        code = str(code)
        if code[0] == "1":
            msg = _ansi_style(msg, "bold")
        elif code == "200":
            pass
        elif code == "304":
            msg = _ansi_style(msg, "cyan")
        elif code[0] == "3":
            msg = _ansi_style(msg, "green")
        elif code == "404":
            msg = _ansi_style(msg, "yellow")
        elif code[0] == "4":
            msg = _ansi_style(msg, "bold", "red")
        else:
            msg = _ansi_style(msg, "bold", "magenta")
        self.log("info", '"%s" %s %s', msg, code, size)

    def log_error(self, format: str, *args: t.Any) -> None:
        self.log("error", format, *args)

    def log_message(self, format: str, *args: t.Any) -> None:
        self.log("info", format, *args)

    def log(self, type: str, message: str, *args: t.Any) -> None:
        _log(
            type,
            f"{self.address_string()} - - [{self.log_date_time_string()}] {message}\n",
            *args,
        )


def _ansi_style(value: str, *styles: str) -> str:
    if not _log_add_style:
        return value
    codes = {"bold": 1, "red": 31, "green": 32, "yellow": 33, "magenta": 35, "cyan": 36}
    for style in styles:
        value = f"\x1b[{codes[style]}m{value}"
    return f"{value}\x1b[0m"


def generate_adhoc_ssl_pair(
    cn: str | None = None,
) -> tuple[Certificate, RSAPrivateKeyWithSerialization]:
    try:
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID
    except ImportError:
        raise TypeError(
            "Using ad-hoc certificates requires the cryptography library."
        ) from None
    backend = default_backend()
    pkey = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=backend
    )
    if cn is None:
        cn = "*"
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Dummy Certificate"),
            x509.NameAttribute(NameOID.COMMON_NAME, cn),
        ]
    )
    backend = default_backend()
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(pkey.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(dt.now(timezone.utc))
        .not_valid_after(dt.now(timezone.utc) + timedelta(days=365))
        .add_extension(x509.ExtendedKeyUsage([x509.OID_SERVER_AUTH]), critical=False)
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName(cn), x509.DNSName(f"*.{cn}")]),
            critical=False,
        )
        .sign(pkey, hashes.SHA256(), backend)
    )
    return cert, pkey


def make_ssl_devcert(
    base_path: str, host: str | None = None, cn: str | None = None
) -> tuple[str, str]:
    if host is not None:
        cn = host
    cert, pkey = generate_adhoc_ssl_pair(cn=cn)
    from cryptography.hazmat.primitives import serialization

    cert_file = f"{base_path}.crt"
    pkey_file = f"{base_path}.key"
    with open(cert_file, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    with open(pkey_file, "wb") as f:
        f.write(
            pkey.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
    return cert_file, pkey_file


def generate_adhoc_ssl_context() -> ssl.SSLContext:
    import atexit
    import tempfile

    cert, pkey = generate_adhoc_ssl_pair()
    from cryptography.hazmat.primitives import serialization

    cert_handle, cert_file = tempfile.mkstemp()
    pkey_handle, pkey_file = tempfile.mkstemp()
    atexit.register(os.remove, pkey_file)
    atexit.register(os.remove, cert_file)
    os.write(cert_handle, cert.public_bytes(serialization.Encoding.PEM))
    os.write(
        pkey_handle,
        pkey.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ),
    )
    os.close(cert_handle)
    os.close(pkey_handle)
    ctx = load_ssl_context(cert_file, pkey_file)
    return ctx


def load_ssl_context(
    cert_file: str, pkey_file: str | None = None, protocol: int | None = None
) -> ssl.SSLContext:
    if protocol is None:
        protocol = ssl.PROTOCOL_TLS_SERVER
    ctx = ssl.SSLContext(protocol)
    ctx.load_cert_chain(cert_file, pkey_file)
    return ctx


def is_ssl_error(error: Exception | None = None) -> bool:
    if error is None:
        error = t.cast(Exception, sys.exc_info()[1])
    return isinstance(error, ssl.SSLError)


def select_address_family(host: str, port: int) -> socket.AddressFamily:
    if host.startswith("unix://"):
        return socket.AF_UNIX
    elif ":" in host and hasattr(socket, "AF_INET6"):
        return socket.AF_INET6
    return socket.AF_INET


def get_sockaddr(
    host: str, port: int, family: socket.AddressFamily
) -> tuple[str, int] | str:
    if family == af_unix:
        return os.path.abspath(host.partition("://")[2])
    try:
        res = socket.getaddrinfo(
            host, port, family, socket.SOCK_STREAM, socket.IPPROTO_TCP
        )
    except socket.gaierror:
        return host, port
    return res[0][4]


def get_interface_ip(family: socket.AddressFamily) -> str:
    host = "fd31:f903:5ab5:1::1" if family == socket.AF_INET6 else "10.253.155.219"
    with socket.socket(family, socket.SOCK_DGRAM) as s:
        try:
            s.connect((host, 58162))
        except OSError:
            return "::1" if family == socket.AF_INET6 else "127.0.0.1"
        return s.getsockname()[0]


class BaseWSGIServer(HTTPServer):
    multithread = False
    multiprocess = False
    request_queue_size = LISTEN_QUEUE
    allow_reuse_address = True

    def __init__(
        self,
        host: str,
        port: int,
        app: WSGIApplication,
        handler: type[WSGIRequestHandler] | None = None,
        passthrough_errors: bool = False,
        ssl_context: _TSSLContextArg | None = None,
        fd: int | None = None,
    ) -> None:
        if handler is None:
            handler = WSGIRequestHandler
        if "protocol_version" not in vars(handler) and (
            self.multithread or self.multiprocess
        ):
            handler.protocol_version = "HTTP/1.1"
        self.host = host
        self.port = port
        self.app = app
        self.passthrough_errors = passthrough_errors
        self.address_family = address_family = select_address_family(host, port)
        server_address = get_sockaddr(host, int(port), address_family)
        if address_family == af_unix and fd is None:
            server_address = t.cast(str, server_address)
            if os.path.exists(server_address):
                os.unlink(server_address)
        super().__init__(server_address, handler, bind_and_activate=False)
        if fd is None:
            try:
                self.server_bind()
                self.server_activate()
            except OSError as e:
                self.server_close()
                print(e.strerror, file=sys.stderr)
                if e.errno == errno.EADDRINUSE:
                    print(
                        f"Port {port} is in use by another program. Either identify and stop that program, or start the server with a different port.",
                        file=sys.stderr,
                    )
                    if sys.platform == "darwin" and port == 5000:
                        print(
                            "On macOS, try disabling the 'AirPlay Receiver' service from System Preferences -> General -> AirDrop & Handoff.",
                            file=sys.stderr,
                        )
                sys.exit(1)
            except BaseException:
                self.server_close()
                raise
        else:
            self.server_close()
            self.socket = socket.fromfd(fd, address_family, socket.SOCK_STREAM)
            self.server_address = self.socket.getsockname()
        if address_family != af_unix:
            self.port = self.server_address[1]
        if ssl_context is not None:
            if isinstance(ssl_context, tuple):
                ssl_context = load_ssl_context(*ssl_context)
            elif ssl_context == "adhoc":
                ssl_context = generate_adhoc_ssl_context()
            self.socket = ssl_context.wrap_socket(self.socket, server_side=True)
            self.ssl_context: ssl.SSLContext | None = ssl_context
        else:
            self.ssl_context = None
        import importlib.metadata

        self._server_version = f"Werkzeug/{importlib.metadata.version('werkzeug')}"

    def log(self, type: str, message: str, *args: t.Any) -> None:
        _log(type, message, *args)

    def serve_forever(self, poll_interval: float = 0.5) -> None:
        try:
            super().serve_forever(poll_interval=poll_interval)
        except KeyboardInterrupt:
            pass
        finally:
            self.server_close()

    def handle_error(
        self, request: t.Any, client_address: tuple[str, int] | str
    ) -> None:
        if self.passthrough_errors:
            raise
        return super().handle_error(request, client_address)

    def log_startup(self) -> None:
        dev_warning = "WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead."
        dev_warning = _ansi_style(dev_warning, "bold", "red")
        messages = [dev_warning]
        if self.address_family == af_unix:
            messages.append(f" * Running on {self.host}")
        else:
            scheme = "http" if self.ssl_context is None else "https"
            display_hostname = self.host
            if self.host in {"0.0.0.0", "::"}:
                messages.append(f" * Running on all addresses ({self.host})")
                if self.host == "0.0.0.0":
                    localhost = "127.0.0.1"
                    display_hostname = get_interface_ip(socket.AF_INET)
                else:
                    localhost = "[::1]"
                    display_hostname = get_interface_ip(socket.AF_INET6)
                messages.append(f" * Running on {scheme}://{localhost}:{self.port}")
            if ":" in display_hostname:
                display_hostname = f"[{display_hostname}]"
            messages.append(f" * Running on {scheme}://{display_hostname}:{self.port}")
        _log("info", "\n".join(messages))


class ThreadedWSGIServer(socketserver.ThreadingMixIn, BaseWSGIServer):
    multithread = True
    daemon_threads = True


class ForkingWSGIServer(ForkingMixIn, BaseWSGIServer):
    multiprocess = True

    def __init__(
        self,
        host: str,
        port: int,
        app: WSGIApplication,
        processes: int = 40,
        handler: type[WSGIRequestHandler] | None = None,
        passthrough_errors: bool = False,
        ssl_context: _TSSLContextArg | None = None,
        fd: int | None = None,
    ) -> None:
        if not can_fork:
            raise ValueError("Your platform does not support forking.")
        super().__init__(host, port, app, handler, passthrough_errors, ssl_context, fd)
        self.max_children = processes


def make_server(
    host: str,
    port: int,
    app: WSGIApplication,
    threaded: bool = False,
    processes: int = 1,
    request_handler: type[WSGIRequestHandler] | None = None,
    passthrough_errors: bool = False,
    ssl_context: _TSSLContextArg | None = None,
    fd: int | None = None,
) -> BaseWSGIServer:
    if threaded and processes > 1:
        raise ValueError("Cannot have a multi-thread and multi-process server.")
    if threaded:
        return ThreadedWSGIServer(
            host, port, app, request_handler, passthrough_errors, ssl_context, fd=fd
        )
    if processes > 1:
        return ForkingWSGIServer(
            host,
            port,
            app,
            processes,
            request_handler,
            passthrough_errors,
            ssl_context,
            fd=fd,
        )
    return BaseWSGIServer(
        host, port, app, request_handler, passthrough_errors, ssl_context, fd=fd
    )


def is_running_from_reloader() -> bool:
    return os.environ.get("WERKZEUG_RUN_MAIN") == "true"


def run_simple(
    hostname: str,
    port: int,
    application: WSGIApplication,
    use_reloader: bool = False,
    use_debugger: bool = False,
    use_evalex: bool = True,
    extra_files: t.Iterable[str] | None = None,
    exclude_patterns: t.Iterable[str] | None = None,
    reloader_interval: int = 1,
    reloader_type: str = "auto",
    threaded: bool = False,
    processes: int = 1,
    request_handler: type[WSGIRequestHandler] | None = None,
    static_files: dict[str, str | tuple[str, str]] | None = None,
    passthrough_errors: bool = False,
    ssl_context: _TSSLContextArg | None = None,
) -> None:
    if not isinstance(port, int):
        raise TypeError("port must be an integer")
    if static_files:
        from .middleware.shared_data import SharedDataMiddleware

        application = SharedDataMiddleware(application, static_files)
    if use_debugger:
        from .debug import DebuggedApplication

        application = DebuggedApplication(application, evalex=use_evalex)
        application.trusted_hosts.append(hostname)
    if not is_running_from_reloader():
        fd = None
    else:
        fd = int(os.environ["WERKZEUG_SERVER_FD"])
    srv = make_server(
        hostname,
        port,
        application,
        threaded,
        processes,
        request_handler,
        passthrough_errors,
        ssl_context,
        fd=fd,
    )
    srv.socket.set_inheritable(True)
    os.environ["WERKZEUG_SERVER_FD"] = str(srv.fileno())
    if not is_running_from_reloader():
        srv.log_startup()
        _log("info", _ansi_style("Press CTRL+C to quit", "yellow"))
    if use_reloader:
        from ._reloader import run_with_reloader

        try:
            run_with_reloader(
                srv.serve_forever,
                extra_files=extra_files,
                exclude_patterns=exclude_patterns,
                interval=reloader_interval,
                reloader_type=reloader_type,
            )
        finally:
            srv.server_close()
    else:
        srv.serve_forever()
