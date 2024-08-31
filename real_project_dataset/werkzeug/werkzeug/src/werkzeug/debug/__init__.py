from __future__ import annotations
import getpass
import hashlib
import json
import os
import pkgutil
import re
import sys
import time
import typing as t
import uuid
from contextlib import ExitStack
from io import BytesIO
from itertools import chain
from os.path import basename
from os.path import join
from zlib import adler32
from .._internal import _log
from ..exceptions import NotFound
from ..exceptions import SecurityError
from ..http import parse_cookie
from ..sansio.utils import host_is_trusted
from ..security import gen_salt
from ..utils import send_file
from ..wrappers.request import Request
from ..wrappers.response import Response
from .console import Console
from .tbtools import DebugFrameSummary
from .tbtools import DebugTraceback
from .tbtools import render_console_html

if t.TYPE_CHECKING:
    from _typeshed.wsgi import StartResponse
    from _typeshed.wsgi import WSGIApplication
    from _typeshed.wsgi import WSGIEnvironment
PIN_TIME = 60 * 60 * 24 * 7


def hash_pin(pin: str) -> str:
    return hashlib.sha1(f"{pin} added salt".encode("utf-8", "replace")).hexdigest()[:12]


_machine_id: str | bytes | None = None


def get_machine_id() -> str | bytes | None:
    global _machine_id
    if _machine_id is not None:
        return _machine_id

    def _generate() -> str | bytes | None:
        linux = b""
        for filename in ("/etc/machine-id", "/proc/sys/kernel/random/boot_id"):
            try:
                with open(filename, "rb") as f:
                    value = f.readline().strip()
            except OSError:
                continue
            if value:
                linux += value
                break
        try:
            with open("/proc/self/cgroup", "rb") as f:
                linux += f.readline().strip().rpartition(b"/")[2]
        except OSError:
            pass
        if linux:
            return linux
        try:
            from subprocess import PIPE
            from subprocess import Popen

            dump = Popen(
                ["ioreg", "-c", "IOPlatformExpertDevice", "-d", "2"], stdout=PIPE
            ).communicate()[0]
            match = re.search(b'"serial-number" = <([^>]+)', dump)
            if match is not None:
                return match.group(1)
        except (OSError, ImportError):
            pass
        if sys.platform == "win32":
            import winreg

            try:
                with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    "SOFTWARE\\Microsoft\\Cryptography",
                    0,
                    winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
                ) as rk:
                    guid: str | bytes
                    guid_type: int
                    guid, guid_type = winreg.QueryValueEx(rk, "MachineGuid")
                    if guid_type == winreg.REG_SZ:
                        return guid.encode()
                    return guid
            except OSError:
                pass
        return None

    _machine_id = _generate()
    return _machine_id


class _ConsoleFrame:

    def __init__(self, namespace: dict[str, t.Any]):
        self.console = Console(namespace)
        self.id = 0

    def eval(self, code: str) -> t.Any:
        return self.console.eval(code)


def get_pin_and_cookie_name(
    app: WSGIApplication,
) -> tuple[str, str] | tuple[None, None]:
    pin = os.environ.get("WERKZEUG_DEBUG_PIN")
    rv = None
    num = None
    if pin == "off":
        return None, None
    if pin is not None and pin.replace("-", "").isdecimal():
        if "-" in pin:
            rv = pin
        else:
            num = pin
    modname = getattr(app, "__module__", t.cast(object, app).__class__.__module__)
    username: str | None
    try:
        username = getpass.getuser()
    except (ImportError, KeyError):
        username = None
    mod = sys.modules.get(modname)
    probably_public_bits = [
        username,
        modname,
        getattr(app, "__name__", type(app).__name__),
        getattr(mod, "__file__", None),
    ]
    private_bits = [str(uuid.getnode()), get_machine_id()]
    h = hashlib.sha1()
    for bit in chain(probably_public_bits, private_bits):
        if not bit:
            continue
        if isinstance(bit, str):
            bit = bit.encode()
        h.update(bit)
    h.update(b"cookiesalt")
    cookie_name = f"__wzd{h.hexdigest()[:20]}"
    if num is None:
        h.update(b"pinsalt")
        num = f"{int(h.hexdigest(), 16):09d}"[:9]
    if rv is None:
        for group_size in (5, 4, 3):
            if len(num) % group_size == 0:
                rv = "-".join(
                    num[x : x + group_size].rjust(group_size, "0")
                    for x in range(0, len(num), group_size)
                )
                break
        else:
            rv = num
    return rv, cookie_name


class DebuggedApplication:
    _pin: str
    _pin_cookie: str

    def __init__(
        self,
        app: WSGIApplication,
        evalex: bool = False,
        request_key: str = "werkzeug.request",
        console_path: str = "/console",
        console_init_func: t.Callable[[], dict[str, t.Any]] | None = None,
        show_hidden_frames: bool = False,
        pin_security: bool = True,
        pin_logging: bool = True,
    ) -> None:
        if not console_init_func:
            console_init_func = None
        self.app = app
        self.evalex = evalex
        self.frames: dict[int, DebugFrameSummary | _ConsoleFrame] = {}
        self.frame_contexts: dict[int, list[t.ContextManager[None]]] = {}
        self.request_key = request_key
        self.console_path = console_path
        self.console_init_func = console_init_func
        self.show_hidden_frames = show_hidden_frames
        self.secret = gen_salt(20)
        self._failed_pin_auth = 0
        self.pin_logging = pin_logging
        if pin_security:
            if os.environ.get("WERKZEUG_RUN_MAIN") == "true" and pin_logging:
                _log("warning", " * Debugger is active!")
                if self.pin is None:
                    _log("warning", " * Debugger PIN disabled. DEBUGGER UNSECURED!")
                else:
                    _log("info", " * Debugger PIN: %s", self.pin)
        else:
            self.pin = None
        self.trusted_hosts: list[str] = [".localhost", "127.0.0.1"]
        """List of domains to allow requests to the debugger from. A leading dot
        allows all subdomains. This only allows ``".localhost"`` domains by
        default.

        .. versionadded:: 3.0.3
        """

    @property
    def pin(self) -> str | None:
        if not hasattr(self, "_pin"):
            pin_cookie = get_pin_and_cookie_name(self.app)
            self._pin, self._pin_cookie = pin_cookie
        return self._pin

    @pin.setter
    def pin(self, value: str) -> None:
        self._pin = value

    @property
    def pin_cookie_name(self) -> str:
        if not hasattr(self, "_pin_cookie"):
            pin_cookie = get_pin_and_cookie_name(self.app)
            self._pin, self._pin_cookie = pin_cookie
        return self._pin_cookie

    def debug_application(
        self, environ: WSGIEnvironment, start_response: StartResponse
    ) -> t.Iterator[bytes]:
        contexts: list[t.ContextManager[t.Any]] = []
        if self.evalex:
            environ["werkzeug.debug.preserve_context"] = contexts.append
        app_iter = None
        try:
            app_iter = self.app(environ, start_response)
            yield from app_iter
            if hasattr(app_iter, "close"):
                app_iter.close()
        except Exception as e:
            if hasattr(app_iter, "close"):
                app_iter.close()
            tb = DebugTraceback(e, skip=1, hide=not self.show_hidden_frames)
            for frame in tb.all_frames:
                self.frames[id(frame)] = frame
                self.frame_contexts[id(frame)] = contexts
            is_trusted = bool(self.check_pin_trust(environ))
            html = tb.render_debugger_html(
                evalex=self.evalex and self.check_host_trust(environ),
                secret=self.secret,
                evalex_trusted=is_trusted,
            )
            response = Response(html, status=500, mimetype="text/html")
            try:
                yield from response(environ, start_response)
            except Exception:
                environ["wsgi.errors"].write(
                    """Debugging middleware caught exception in streamed response at a point where response headers were already sent.
"""
                )
            environ["wsgi.errors"].write("".join(tb.render_traceback_text()))

    def execute_command(
        self, request: Request, command: str, frame: DebugFrameSummary | _ConsoleFrame
    ) -> Response:
        if not self.check_host_trust(request.environ):
            return SecurityError()
        contexts = self.frame_contexts.get(id(frame), [])
        with ExitStack() as exit_stack:
            for cm in contexts:
                exit_stack.enter_context(cm)
            return Response(frame.eval(command), mimetype="text/html")

    def display_console(self, request: Request) -> Response:
        if not self.check_host_trust(request.environ):
            return SecurityError()
        if 0 not in self.frames:
            if self.console_init_func is None:
                ns = {}
            else:
                ns = dict(self.console_init_func())
            ns.setdefault("app", self.app)
            self.frames[0] = _ConsoleFrame(ns)
        is_trusted = bool(self.check_pin_trust(request.environ))
        return Response(
            render_console_html(secret=self.secret, evalex_trusted=is_trusted),
            mimetype="text/html",
        )

    def get_resource(self, request: Request, filename: str) -> Response:
        path = join("shared", basename(filename))
        try:
            data = pkgutil.get_data(__package__, path)
        except OSError:
            return NotFound()
        else:
            if data is None:
                return NotFound()
            etag = str(adler32(data) & 4294967295)
            return send_file(
                BytesIO(data), request.environ, download_name=filename, etag=etag
            )

    def check_pin_trust(self, environ: WSGIEnvironment) -> bool | None:
        if self.pin is None:
            return True
        val = parse_cookie(environ).get(self.pin_cookie_name)
        if not val or "|" not in val:
            return False
        ts_str, pin_hash = val.split("|", 1)
        try:
            ts = int(ts_str)
        except ValueError:
            return False
        if pin_hash != hash_pin(self.pin):
            return None
        return time.time() - PIN_TIME < ts

    def check_host_trust(self, environ: WSGIEnvironment) -> bool:
        return host_is_trusted(environ.get("HTTP_HOST"), self.trusted_hosts)

    def _fail_pin_auth(self) -> None:
        time.sleep(5.0 if self._failed_pin_auth > 5 else 0.5)
        self._failed_pin_auth += 1

    def pin_auth(self, request: Request) -> Response:
        if not self.check_host_trust(request.environ):
            return SecurityError()
        exhausted = False
        auth = False
        trust = self.check_pin_trust(request.environ)
        pin = t.cast(str, self.pin)
        bad_cookie = False
        if trust is None:
            self._fail_pin_auth()
            bad_cookie = True
        elif trust:
            auth = True
        elif self._failed_pin_auth > 10:
            exhausted = True
        else:
            entered_pin = request.args["pin"]
            if entered_pin.strip().replace("-", "") == pin.replace("-", ""):
                self._failed_pin_auth = 0
                auth = True
            else:
                self._fail_pin_auth()
        rv = Response(
            json.dumps({"auth": auth, "exhausted": exhausted}),
            mimetype="application/json",
        )
        if auth:
            rv.set_cookie(
                self.pin_cookie_name,
                f"{int(time.time())}|{hash_pin(pin)}",
                httponly=True,
                samesite="Strict",
                secure=request.is_secure,
            )
        elif bad_cookie:
            rv.delete_cookie(self.pin_cookie_name)
        return rv

    def log_pin_request(self, request: Request) -> Response:
        if not self.check_host_trust(request.environ):
            return SecurityError()
        if self.pin_logging and self.pin is not None:
            _log(
                "info", " * To enable the debugger you need to enter the security pin:"
            )
            _log("info", " * Debugger pin code: %s", self.pin)
        return Response("")

    def __call__(
        self, environ: WSGIEnvironment, start_response: StartResponse
    ) -> t.Iterable[bytes]:
        request = Request(environ)
        response = self.debug_application
        if request.args.get("__debugger__") == "yes":
            cmd = request.args.get("cmd")
            arg = request.args.get("f")
            secret = request.args.get("s")
            frame = self.frames.get(request.args.get("frm", type=int))
            if cmd == "resource" and arg:
                response = self.get_resource(request, arg)
            elif cmd == "pinauth" and secret == self.secret:
                response = self.pin_auth(request)
            elif cmd == "printpin" and secret == self.secret:
                response = self.log_pin_request(request)
            elif (
                self.evalex
                and cmd is not None
                and frame is not None
                and self.secret == secret
                and self.check_pin_trust(environ)
            ):
                response = self.execute_command(request, cmd, frame)
        elif (
            self.evalex
            and self.console_path is not None
            and request.path == self.console_path
        ):
            response = self.display_console(request)
        return response(environ, start_response)
