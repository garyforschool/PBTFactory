from __future__ import annotations
import email.utils
import re
import typing as t
import warnings
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
from datetime import timezone
from enum import Enum
from hashlib import sha1
from time import mktime
from time import struct_time
from urllib.parse import quote
from urllib.parse import unquote
from urllib.request import parse_http_list as _parse_list_header
from ._internal import _dt_as_utc
from ._internal import _plain_int

if t.TYPE_CHECKING:
    from _typeshed.wsgi import WSGIEnvironment
_token_chars = frozenset(
    "!#$%&'*+-.0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ^_`abcdefghijklmnopqrstuvwxyz|~"
)
_etag_re = re.compile('([Ww]/)?(?:"(.*?)"|(.*?))(?:\\s*,\\s*|$)')
_entity_headers = frozenset(
    [
        "allow",
        "content-encoding",
        "content-language",
        "content-length",
        "content-location",
        "content-md5",
        "content-range",
        "content-type",
        "expires",
        "last-modified",
    ]
)
_hop_by_hop_headers = frozenset(
    [
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailer",
        "transfer-encoding",
        "upgrade",
    ]
)
HTTP_STATUS_CODES = {
    (100): "Continue",
    (101): "Switching Protocols",
    (102): "Processing",
    (103): "Early Hints",
    (200): "OK",
    (201): "Created",
    (202): "Accepted",
    (203): "Non Authoritative Information",
    (204): "No Content",
    (205): "Reset Content",
    (206): "Partial Content",
    (207): "Multi Status",
    (208): "Already Reported",
    (226): "IM Used",
    (300): "Multiple Choices",
    (301): "Moved Permanently",
    (302): "Found",
    (303): "See Other",
    (304): "Not Modified",
    (305): "Use Proxy",
    (306): "Switch Proxy",
    (307): "Temporary Redirect",
    (308): "Permanent Redirect",
    (400): "Bad Request",
    (401): "Unauthorized",
    (402): "Payment Required",
    (403): "Forbidden",
    (404): "Not Found",
    (405): "Method Not Allowed",
    (406): "Not Acceptable",
    (407): "Proxy Authentication Required",
    (408): "Request Timeout",
    (409): "Conflict",
    (410): "Gone",
    (411): "Length Required",
    (412): "Precondition Failed",
    (413): "Request Entity Too Large",
    (414): "Request URI Too Long",
    (415): "Unsupported Media Type",
    (416): "Requested Range Not Satisfiable",
    (417): "Expectation Failed",
    (418): "I'm a teapot",
    (421): "Misdirected Request",
    (422): "Unprocessable Entity",
    (423): "Locked",
    (424): "Failed Dependency",
    (425): "Too Early",
    (426): "Upgrade Required",
    (428): "Precondition Required",
    (429): "Too Many Requests",
    (431): "Request Header Fields Too Large",
    (449): "Retry With",
    (451): "Unavailable For Legal Reasons",
    (500): "Internal Server Error",
    (501): "Not Implemented",
    (502): "Bad Gateway",
    (503): "Service Unavailable",
    (504): "Gateway Timeout",
    (505): "HTTP Version Not Supported",
    (506): "Variant Also Negotiates",
    (507): "Insufficient Storage",
    (508): "Loop Detected",
    (510): "Not Extended",
    (511): "Network Authentication Failed",
}


class COEP(Enum):
    UNSAFE_NONE = "unsafe-none"
    REQUIRE_CORP = "require-corp"


class COOP(Enum):
    UNSAFE_NONE = "unsafe-none"
    SAME_ORIGIN_ALLOW_POPUPS = "same-origin-allow-popups"
    SAME_ORIGIN = "same-origin"


def quote_header_value(value: t.Any, allow_token: bool = True) -> str:
    value_str = str(value)
    if not value_str:
        return '""'
    if allow_token:
        token_chars = _token_chars
        if token_chars.issuperset(value_str):
            return value_str
    value_str = value_str.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{value_str}"'


def unquote_header_value(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] == '"':
        value = value[1:-1]
        return value.replace("\\\\", "\\").replace('\\"', '"')
    return value


def dump_options_header(header: str | None, options: t.Mapping[str, t.Any]) -> str:
    segments = []
    if header is not None:
        segments.append(header)
    for key, value in options.items():
        if value is None:
            continue
        if key[-1] == "*":
            segments.append(f"{key}={value}")
        else:
            segments.append(f"{key}={quote_header_value(value)}")
    return "; ".join(segments)


def dump_header(iterable: dict[str, t.Any] | t.Iterable[t.Any]) -> str:
    if isinstance(iterable, dict):
        items = []
        for key, value in iterable.items():
            if value is None:
                items.append(key)
            elif key[-1] == "*":
                items.append(f"{key}={value}")
            else:
                items.append(f"{key}={quote_header_value(value)}")
    else:
        items = [quote_header_value(x) for x in iterable]
    return ", ".join(items)


def dump_csp_header(header: ds.ContentSecurityPolicy) -> str:
    return "; ".join(f"{key} {value}" for key, value in header.items())


def parse_list_header(value: str) -> list[str]:
    result = []
    for item in _parse_list_header(value):
        if len(item) >= 2 and item[0] == item[-1] == '"':
            item = item[1:-1]
        result.append(item)
    return result


def parse_dict_header(value: str) -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for item in parse_list_header(value):
        key, has_value, value = item.partition("=")
        key = key.strip()
        if not has_value:
            result[key] = None
            continue
        value = value.strip()
        encoding: str | None = None
        if key[-1] == "*":
            key = key[:-1]
            match = _charset_value_re.match(value)
            if match:
                encoding, value = match.groups()
                encoding = encoding.lower()
            if encoding in {"ascii", "us-ascii", "utf-8", "iso-8859-1"}:
                value = unquote(value, encoding=encoding)
        if len(value) >= 2 and value[0] == value[-1] == '"':
            value = value[1:-1]
        result[key] = value
    return result


_parameter_re = re.compile(
    """
    # don't match multiple empty parts, that causes backtracking
    \\s*;\\s*  # find the part delimiter
    (?:
        ([\\w!#$%&'*+\\-.^`|~]+)  # key, one or more token chars
        =  # equals, with no space on either side
        (  # value, token or quoted string
            [\\w!#$%&'*+\\-.^`|~]+  # one or more token chars
        |
            "(?:\\\\\\\\|\\\\"|.)*?"  # quoted string, consuming slash escapes
        )
    )?  # optionally match key=value, to account for empty parts
    """,
    re.ASCII | re.VERBOSE,
)
_charset_value_re = re.compile(
    """
    ([\\w!#$%&*+\\-.^`|~]*)'  # charset part, could be empty
    [\\w!#$%&*+\\-.^`|~]*'  # don't care about language part, usually empty
    ([\\w!#$%&'*+\\-.^`|~]+)  # one or more token chars with percent encoding
    """,
    re.ASCII | re.VERBOSE,
)
_continuation_re = re.compile("\\*(\\d+)$", re.ASCII)


def parse_options_header(value: str | None) -> tuple[str, dict[str, str]]:
    if value is None:
        return "", {}
    value, _, rest = value.partition(";")
    value = value.strip()
    rest = rest.strip()
    if not value or not rest:
        return value, {}
    rest = f";{rest}"
    options: dict[str, str] = {}
    encoding: str | None = None
    continued_encoding: str | None = None
    for pk, pv in _parameter_re.findall(rest):
        if not pk:
            continue
        pk = pk.lower()
        if pk[-1] == "*":
            pk = pk[:-1]
            match = _charset_value_re.match(pv)
            if match:
                encoding, pv = match.groups()
                encoding = encoding.lower()
            if not encoding:
                encoding = continued_encoding
            if encoding in {"ascii", "us-ascii", "utf-8", "iso-8859-1"}:
                continued_encoding = encoding
                pv = unquote(pv, encoding=encoding)
        if pv[0] == pv[-1] == '"':
            pv = pv[1:-1].replace("\\\\", "\\").replace('\\"', '"').replace("%22", '"')
        match = _continuation_re.search(pk)
        if match:
            pk = pk[: match.start()]
            options[pk] = options.get(pk, "") + pv
        else:
            options[pk] = pv
    return value, options


_q_value_re = re.compile("-?\\d+(\\.\\d+)?", re.ASCII)
_TAnyAccept = t.TypeVar("_TAnyAccept", bound="ds.Accept")


@t.overload
def parse_accept_header(value: str | None) -> ds.Accept: ...


@t.overload
def parse_accept_header(value: str | None, cls: type[_TAnyAccept]) -> _TAnyAccept: ...


def parse_accept_header(
    value: str | None, cls: type[_TAnyAccept] | None = None
) -> _TAnyAccept:
    if cls is None:
        cls = t.cast(t.Type[_TAnyAccept], ds.Accept)
    if not value:
        return cls(None)
    result = []
    for item in parse_list_header(value):
        item, options = parse_options_header(item)
        if "q" in options:
            q_str = options.pop("q").strip()
            if _q_value_re.fullmatch(q_str) is None:
                continue
            q = float(q_str)
            if q < 0 or q > 1:
                continue
        else:
            q = 1
        if options:
            item = dump_options_header(item, options)
        result.append((item, q))
    return cls(result)


_TAnyCC = t.TypeVar("_TAnyCC", bound="ds.cache_control._CacheControl")


@t.overload
def parse_cache_control_header(
    value: str | None,
    on_update: t.Callable[[ds.cache_control._CacheControl], None] | None = None,
) -> ds.RequestCacheControl: ...


@t.overload
def parse_cache_control_header(
    value: str | None,
    on_update: t.Callable[[ds.cache_control._CacheControl], None] | None = None,
    cls: type[_TAnyCC] = ...,
) -> _TAnyCC: ...


def parse_cache_control_header(
    value: str | None,
    on_update: t.Callable[[ds.cache_control._CacheControl], None] | None = None,
    cls: type[_TAnyCC] | None = None,
) -> _TAnyCC:
    if cls is None:
        cls = t.cast("type[_TAnyCC]", ds.RequestCacheControl)
    if not value:
        return cls((), on_update)
    return cls(parse_dict_header(value), on_update)


_TAnyCSP = t.TypeVar("_TAnyCSP", bound="ds.ContentSecurityPolicy")


@t.overload
def parse_csp_header(
    value: str | None,
    on_update: t.Callable[[ds.ContentSecurityPolicy], None] | None = None,
) -> ds.ContentSecurityPolicy: ...


@t.overload
def parse_csp_header(
    value: str | None,
    on_update: t.Callable[[ds.ContentSecurityPolicy], None] | None = None,
    cls: type[_TAnyCSP] = ...,
) -> _TAnyCSP: ...


def parse_csp_header(
    value: str | None,
    on_update: t.Callable[[ds.ContentSecurityPolicy], None] | None = None,
    cls: type[_TAnyCSP] | None = None,
) -> _TAnyCSP:
    if cls is None:
        cls = t.cast("type[_TAnyCSP]", ds.ContentSecurityPolicy)
    if value is None:
        return cls((), on_update)
    items = []
    for policy in value.split(";"):
        policy = policy.strip()
        if " " in policy:
            directive, value = policy.strip().split(" ", 1)
            items.append((directive.strip(), value.strip()))
    return cls(items, on_update)


def parse_set_header(
    value: str | None, on_update: t.Callable[[ds.HeaderSet], None] | None = None
) -> ds.HeaderSet:
    if not value:
        return ds.HeaderSet(None, on_update)
    return ds.HeaderSet(parse_list_header(value), on_update)


def parse_if_range_header(value: str | None) -> ds.IfRange:
    if not value:
        return ds.IfRange()
    date = parse_date(value)
    if date is not None:
        return ds.IfRange(date=date)
    return ds.IfRange(unquote_etag(value)[0])


def parse_range_header(
    value: str | None, make_inclusive: bool = True
) -> ds.Range | None:
    if not value or "=" not in value:
        return None
    ranges = []
    last_end = 0
    units, rng = value.split("=", 1)
    units = units.strip().lower()
    for item in rng.split(","):
        item = item.strip()
        if "-" not in item:
            return None
        if item.startswith("-"):
            if last_end < 0:
                return None
            try:
                begin = _plain_int(item)
            except ValueError:
                return None
            end = None
            last_end = -1
        elif "-" in item:
            begin_str, end_str = item.split("-", 1)
            begin_str = begin_str.strip()
            end_str = end_str.strip()
            try:
                begin = _plain_int(begin_str)
            except ValueError:
                return None
            if begin < last_end or last_end < 0:
                return None
            if end_str:
                try:
                    end = _plain_int(end_str) + 1
                except ValueError:
                    return None
                if begin >= end:
                    return None
            else:
                end = None
            last_end = end if end is not None else -1
        ranges.append((begin, end))
    return ds.Range(units, ranges)


def parse_content_range_header(
    value: str | None, on_update: t.Callable[[ds.ContentRange], None] | None = None
) -> ds.ContentRange | None:
    if value is None:
        return None
    try:
        units, rangedef = (value or "").strip().split(None, 1)
    except ValueError:
        return None
    if "/" not in rangedef:
        return None
    rng, length_str = rangedef.split("/", 1)
    if length_str == "*":
        length = None
    else:
        try:
            length = _plain_int(length_str)
        except ValueError:
            return None
    if rng == "*":
        if not is_byte_range_valid(None, None, length):
            return None
        return ds.ContentRange(units, None, None, length, on_update=on_update)
    elif "-" not in rng:
        return None
    start_str, stop_str = rng.split("-", 1)
    try:
        start = _plain_int(start_str)
        stop = _plain_int(stop_str) + 1
    except ValueError:
        return None
    if is_byte_range_valid(start, stop, length):
        return ds.ContentRange(units, start, stop, length, on_update=on_update)
    return None


def quote_etag(etag: str, weak: bool = False) -> str:
    if '"' in etag:
        raise ValueError("invalid etag")
    etag = f'"{etag}"'
    if weak:
        etag = f"W/{etag}"
    return etag


def unquote_etag(etag: str | None) -> tuple[str, bool] | tuple[None, None]:
    if not etag:
        return None, None
    etag = etag.strip()
    weak = False
    if etag.startswith(("W/", "w/")):
        weak = True
        etag = etag[2:]
    if etag[:1] == etag[-1:] == '"':
        etag = etag[1:-1]
    return etag, weak


def parse_etags(value: str | None) -> ds.ETags:
    if not value:
        return ds.ETags()
    strong = []
    weak = []
    end = len(value)
    pos = 0
    while pos < end:
        match = _etag_re.match(value, pos)
        if match is None:
            break
        is_weak, quoted, raw = match.groups()
        if raw == "*":
            return ds.ETags(star_tag=True)
        elif quoted:
            raw = quoted
        if is_weak:
            weak.append(raw)
        else:
            strong.append(raw)
        pos = match.end()
    return ds.ETags(strong, weak)


def generate_etag(data: bytes) -> str:
    return sha1(data).hexdigest()


def parse_date(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        dt = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def http_date(
    timestamp: datetime | date | int | float | struct_time | None = None,
) -> str:
    if isinstance(timestamp, date):
        if not isinstance(timestamp, datetime):
            timestamp = datetime.combine(timestamp, time(), tzinfo=timezone.utc)
        else:
            timestamp = _dt_as_utc(timestamp)
        return email.utils.format_datetime(timestamp, usegmt=True)
    if isinstance(timestamp, struct_time):
        timestamp = mktime(timestamp)
    return email.utils.formatdate(timestamp, usegmt=True)


def parse_age(value: str | None = None) -> timedelta | None:
    if not value:
        return None
    try:
        seconds = int(value)
    except ValueError:
        return None
    if seconds < 0:
        return None
    try:
        return timedelta(seconds=seconds)
    except OverflowError:
        return None


def dump_age(age: timedelta | int | None = None) -> str | None:
    if age is None:
        return None
    if isinstance(age, timedelta):
        age = int(age.total_seconds())
    else:
        age = int(age)
    if age < 0:
        raise ValueError("age cannot be negative")
    return str(age)


def is_resource_modified(
    environ: WSGIEnvironment,
    etag: str | None = None,
    data: bytes | None = None,
    last_modified: datetime | str | None = None,
    ignore_if_range: bool = True,
) -> bool:
    return _sansio_http.is_resource_modified(
        http_range=environ.get("HTTP_RANGE"),
        http_if_range=environ.get("HTTP_IF_RANGE"),
        http_if_modified_since=environ.get("HTTP_IF_MODIFIED_SINCE"),
        http_if_none_match=environ.get("HTTP_IF_NONE_MATCH"),
        http_if_match=environ.get("HTTP_IF_MATCH"),
        etag=etag,
        data=data,
        last_modified=last_modified,
        ignore_if_range=ignore_if_range,
    )


def remove_entity_headers(
    headers: ds.Headers | list[tuple[str, str]],
    allowed: t.Iterable[str] = ("expires", "content-location"),
) -> None:
    allowed = {x.lower() for x in allowed}
    headers[:] = [
        (key, value)
        for key, value in headers
        if not is_entity_header(key) or key.lower() in allowed
    ]


def remove_hop_by_hop_headers(headers: ds.Headers | list[tuple[str, str]]) -> None:
    headers[:] = [
        (key, value) for key, value in headers if not is_hop_by_hop_header(key)
    ]


def is_entity_header(header: str) -> bool:
    return header.lower() in _entity_headers


def is_hop_by_hop_header(header: str) -> bool:
    return header.lower() in _hop_by_hop_headers


def parse_cookie(
    header: WSGIEnvironment | str | None,
    cls: type[ds.MultiDict[str, str]] | None = None,
) -> ds.MultiDict[str, str]:
    if isinstance(header, dict):
        cookie = header.get("HTTP_COOKIE")
    else:
        cookie = header
    if cookie:
        cookie = cookie.encode("latin1").decode()
    return _sansio_http.parse_cookie(cookie=cookie, cls=cls)


_cookie_no_quote_re = re.compile("[\\w!#$%&'()*+\\-./:<=>?@\\[\\]^`{|}~]*", re.A)
_cookie_slash_re = re.compile(b'[\\x00-\\x19\\",;\\\\\\x7f-\\xff]', re.A)
_cookie_slash_map = {b'"': b'\\"', b"\\": b"\\\\"}
_cookie_slash_map.update(
    (v.to_bytes(1, "big"), b"\\%03o" % v)
    for v in [*range(32), *b",;", *range(127, 256)]
)


def dump_cookie(
    key: str,
    value: str = "",
    max_age: timedelta | int | None = None,
    expires: str | datetime | int | float | None = None,
    path: str | None = "/",
    domain: str | None = None,
    secure: bool = False,
    httponly: bool = False,
    sync_expires: bool = True,
    max_size: int = 4093,
    samesite: str | None = None,
    partitioned: bool = False,
) -> str:
    if path is not None:
        path = quote(path, safe="%!$&'()*+,/:=@")
    if domain:
        domain = domain.partition(":")[0].lstrip(".").encode("idna").decode("ascii")
    if isinstance(max_age, timedelta):
        max_age = int(max_age.total_seconds())
    if expires is not None:
        if not isinstance(expires, str):
            expires = http_date(expires)
    elif max_age is not None and sync_expires:
        expires = http_date(datetime.now(tz=timezone.utc).timestamp() + max_age)
    if samesite is not None:
        samesite = samesite.title()
        if samesite not in {"Strict", "Lax", "None"}:
            raise ValueError("SameSite must be 'Strict', 'Lax', or 'None'.")
    if partitioned:
        secure = True
    if not _cookie_no_quote_re.fullmatch(value):
        value = _cookie_slash_re.sub(
            lambda m: _cookie_slash_map[m.group()], value.encode()
        ).decode("ascii")
        value = f'"{value}"'
    buf = [f"{key.encode().decode('latin1')}={value}"]
    for k, v in (
        ("Domain", domain),
        ("Expires", expires),
        ("Max-Age", max_age),
        ("Secure", secure),
        ("HttpOnly", httponly),
        ("Path", path),
        ("SameSite", samesite),
        ("Partitioned", partitioned),
    ):
        if v is None or v is False:
            continue
        if v is True:
            buf.append(k)
            continue
        buf.append(f"{k}={v}")
    rv = "; ".join(buf)
    cookie_size = len(rv)
    if max_size and cookie_size > max_size:
        value_size = len(value)
        warnings.warn(
            f"The '{key}' cookie is too large: the value was {value_size} bytes but the header required {cookie_size - value_size} extra bytes. The final size was {cookie_size} bytes but the limit is {max_size} bytes. Browsers may silently ignore cookies larger than this.",
            stacklevel=2,
        )
    return rv


def is_byte_range_valid(
    start: int | None, stop: int | None, length: int | None
) -> bool:
    if (start is None) != (stop is None):
        return False
    elif start is None:
        return length is None or length >= 0
    elif length is None:
        return 0 <= start < stop
    elif start >= stop:
        return False
    return 0 <= start < length


from . import datastructures as ds
from .sansio import http as _sansio_http
