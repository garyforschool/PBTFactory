from __future__ import annotations
import io
import mimetypes
import os
import pkgutil
import re
import sys
import typing as t
import unicodedata
from datetime import datetime
from time import time
from urllib.parse import quote
from zlib import adler32
from markupsafe import escape
from ._internal import _DictAccessorProperty
from ._internal import _missing
from ._internal import _TAccessorValue
from .datastructures import Headers
from .exceptions import NotFound
from .exceptions import RequestedRangeNotSatisfiable
from .security import safe_join
from .wsgi import wrap_file

if t.TYPE_CHECKING:
    from _typeshed.wsgi import WSGIEnvironment
    from .wrappers.request import Request
    from .wrappers.response import Response
_T = t.TypeVar("_T")
_entity_re = re.compile("&([^;]+);")
_filename_ascii_strip_re = re.compile("[^A-Za-z0-9_.-]")
_windows_device_files = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(10)),
    *(f"LPT{i}" for i in range(10)),
}


class cached_property(property, t.Generic[_T]):

    def __init__(
        self,
        fget: t.Callable[[t.Any], _T],
        name: str | None = None,
        doc: str | None = None,
    ) -> None:
        super().__init__(fget, doc=doc)
        self.__name__ = name or fget.__name__
        self.slot_name = f"_cache_{self.__name__}"
        self.__module__ = fget.__module__

    def __set__(self, obj: object, value: _T) -> None:
        if hasattr(obj, "__dict__"):
            obj.__dict__[self.__name__] = value
        else:
            setattr(obj, self.slot_name, value)

    def __get__(self, obj: object, type: type = None) -> _T:
        if obj is None:
            return self
        obj_dict = getattr(obj, "__dict__", None)
        if obj_dict is not None:
            value: _T = obj_dict.get(self.__name__, _missing)
        else:
            value = getattr(obj, self.slot_name, _missing)
        if value is _missing:
            value = self.fget(obj)
            if obj_dict is not None:
                obj.__dict__[self.__name__] = value
            else:
                setattr(obj, self.slot_name, value)
        return value

    def __delete__(self, obj: object) -> None:
        if hasattr(obj, "__dict__"):
            del obj.__dict__[self.__name__]
        else:
            setattr(obj, self.slot_name, _missing)


class environ_property(_DictAccessorProperty[_TAccessorValue]):
    read_only = True

    def lookup(self, obj: Request) -> WSGIEnvironment:
        return obj.environ


class header_property(_DictAccessorProperty[_TAccessorValue]):

    def lookup(self, obj: Request | Response) -> Headers:
        return obj.headers


_charset_mimetypes = {
    "application/ecmascript",
    "application/javascript",
    "application/sql",
    "application/xml",
    "application/xml-dtd",
    "application/xml-external-parsed-entity",
}


def get_content_type(mimetype: str, charset: str) -> str:
    if (
        mimetype.startswith("text/")
        or mimetype in _charset_mimetypes
        or mimetype.endswith("+xml")
    ):
        mimetype += f"; charset={charset}"
    return mimetype


def secure_filename(filename: str) -> str:
    filename = unicodedata.normalize("NFKD", filename)
    filename = filename.encode("ascii", "ignore").decode("ascii")
    for sep in (os.sep, os.path.altsep):
        if sep:
            filename = filename.replace(sep, " ")
    filename = str(_filename_ascii_strip_re.sub("", "_".join(filename.split()))).strip(
        "._"
    )
    if (
        os.name == "nt"
        and filename
        and filename.split(".")[0].upper() in _windows_device_files
    ):
        filename = f"_{filename}"
    return filename


def redirect(
    location: str, code: int = 302, Response: type[Response] | None = None
) -> Response:
    if Response is None:
        from .wrappers import Response
    html_location = escape(location)
    response = Response(
        f"""<!doctype html>
<html lang=en>
<title>Redirecting...</title>
<h1>Redirecting...</h1>
<p>You should be redirected automatically to the target URL: <a href="{html_location}">{html_location}</a>. If not, click the link.
""",
        code,
        mimetype="text/html",
    )
    response.headers["Location"] = location
    return response


def append_slash_redirect(environ: WSGIEnvironment, code: int = 308) -> Response:
    tail = environ["PATH_INFO"].rpartition("/")[2]
    if not tail:
        new_path = "./"
    else:
        new_path = f"{tail}/"
    query_string = environ.get("QUERY_STRING")
    if query_string:
        new_path = f"{new_path}?{query_string}"
    return redirect(new_path, code)


def send_file(
    path_or_file: os.PathLike[str] | str | t.IO[bytes],
    environ: WSGIEnvironment,
    mimetype: str | None = None,
    as_attachment: bool = False,
    download_name: str | None = None,
    conditional: bool = True,
    etag: bool | str = True,
    last_modified: datetime | int | float | None = None,
    max_age: None | (int | t.Callable[[str | None], int | None]) = None,
    use_x_sendfile: bool = False,
    response_class: type[Response] | None = None,
    _root_path: os.PathLike[str] | str | None = None,
) -> Response:
    if response_class is None:
        from .wrappers import Response

        response_class = Response
    path: str | None = None
    file: t.IO[bytes] | None = None
    size: int | None = None
    mtime: float | None = None
    headers = Headers()
    if isinstance(path_or_file, (os.PathLike, str)) or hasattr(
        path_or_file, "__fspath__"
    ):
        path_or_file = t.cast("t.Union[os.PathLike[str], str]", path_or_file)
        if _root_path is not None:
            path = os.path.join(_root_path, path_or_file)
        else:
            path = os.path.abspath(path_or_file)
        stat = os.stat(path)
        size = stat.st_size
        mtime = stat.st_mtime
    else:
        file = path_or_file
    if download_name is None and path is not None:
        download_name = os.path.basename(path)
    if mimetype is None:
        if download_name is None:
            raise TypeError(
                "Unable to detect the MIME type because a file name is not available. Either set 'download_name', pass a path instead of a file, or set 'mimetype'."
            )
        mimetype, encoding = mimetypes.guess_type(download_name)
        if mimetype is None:
            mimetype = "application/octet-stream"
        if encoding is not None and not as_attachment:
            headers.set("Content-Encoding", encoding)
    if download_name is not None:
        try:
            download_name.encode("ascii")
        except UnicodeEncodeError:
            simple = unicodedata.normalize("NFKD", download_name)
            simple = simple.encode("ascii", "ignore").decode("ascii")
            quoted = quote(download_name, safe="!#$&+-.^_`|~")
            names = {"filename": simple, "filename*": f"UTF-8''{quoted}"}
        else:
            names = {"filename": download_name}
        value = "attachment" if as_attachment else "inline"
        headers.set("Content-Disposition", value, **names)
    elif as_attachment:
        raise TypeError(
            "No name provided for attachment. Either set 'download_name' or pass a path instead of a file."
        )
    if use_x_sendfile and path is not None:
        headers["X-Sendfile"] = path
        data = None
    else:
        if file is None:
            file = open(path, "rb")
        elif isinstance(file, io.BytesIO):
            size = file.getbuffer().nbytes
        elif isinstance(file, io.TextIOBase):
            raise ValueError("Files must be opened in binary mode or use BytesIO.")
        data = wrap_file(environ, file)
    rv = response_class(
        data, mimetype=mimetype, headers=headers, direct_passthrough=True
    )
    if size is not None:
        rv.content_length = size
    if last_modified is not None:
        rv.last_modified = last_modified
    elif mtime is not None:
        rv.last_modified = mtime
    rv.cache_control.no_cache = True
    if callable(max_age):
        max_age = max_age(path)
    if max_age is not None:
        if max_age > 0:
            rv.cache_control.no_cache = None
            rv.cache_control.public = True
        rv.cache_control.max_age = max_age
        rv.expires = int(time() + max_age)
    if isinstance(etag, str):
        rv.set_etag(etag)
    elif etag and path is not None:
        check = adler32(path.encode()) & 4294967295
        rv.set_etag(f"{mtime}-{size}-{check}")
    if conditional:
        try:
            rv = rv.make_conditional(environ, accept_ranges=True, complete_length=size)
        except RequestedRangeNotSatisfiable:
            if file is not None:
                file.close()
            raise
        if rv.status_code == 304:
            rv.headers.pop("x-sendfile", None)
    return rv


def send_from_directory(
    directory: os.PathLike[str] | str,
    path: os.PathLike[str] | str,
    environ: WSGIEnvironment,
    **kwargs: t.Any,
) -> Response:
    path_str = safe_join(os.fspath(directory), os.fspath(path))
    if path_str is None:
        raise NotFound()
    if "_root_path" in kwargs:
        path_str = os.path.join(kwargs["_root_path"], path_str)
    if not os.path.isfile(path_str):
        raise NotFound()
    return send_file(path_str, environ, **kwargs)


def import_string(import_name: str, silent: bool = False) -> t.Any:
    import_name = import_name.replace(":", ".")
    try:
        try:
            __import__(import_name)
        except ImportError:
            if "." not in import_name:
                raise
        else:
            return sys.modules[import_name]
        module_name, obj_name = import_name.rsplit(".", 1)
        module = __import__(module_name, globals(), locals(), [obj_name])
        try:
            return getattr(module, obj_name)
        except AttributeError as e:
            raise ImportError(e) from None
    except ImportError as e:
        if not silent:
            raise ImportStringError(import_name, e).with_traceback(
                sys.exc_info()[2]
            ) from None
    return None


def find_modules(
    import_path: str, include_packages: bool = False, recursive: bool = False
) -> t.Iterator[str]:
    module = import_string(import_path)
    path = getattr(module, "__path__", None)
    if path is None:
        raise ValueError(f"{import_path!r} is not a package")
    basename = f"{module.__name__}."
    for _importer, modname, ispkg in pkgutil.iter_modules(path):
        modname = basename + modname
        if ispkg:
            if include_packages:
                yield modname
            if recursive:
                yield from find_modules(modname, include_packages, True)
        else:
            yield modname


class ImportStringError(ImportError):
    import_name: str
    exception: BaseException

    def __init__(self, import_name: str, exception: BaseException) -> None:
        self.import_name = import_name
        self.exception = exception
        msg = import_name
        name = ""
        tracked = []
        for part in import_name.replace(":", ".").split("."):
            name = f"{name}.{part}" if name else part
            imported = import_string(name, silent=True)
            if imported:
                tracked.append((name, getattr(imported, "__file__", None)))
            else:
                track = [f"- {n!r} found in {i!r}." for n, i in tracked]
                track.append(f"- {name!r} not found.")
                track_str = "\n".join(track)
                msg = f"""import_string() failed for {import_name!r}. Possible reasons are:

- missing __init__.py in a package;
- package or module path not included in sys.path;
- duplicated package or module name taking precedence in sys.path;
- missing module, class, function or variable;

Debugged import:

{track_str}

Original exception:

{type(exception).__name__}: {exception}"""
                break
        super().__init__(msg)

    def __repr__(self) -> str:
        return f"<{type(self).__name__}({self.import_name!r}, {self.exception!r})>"