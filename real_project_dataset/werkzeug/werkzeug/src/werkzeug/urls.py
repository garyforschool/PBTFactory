from __future__ import annotations
import codecs
import re
import typing as t
import urllib.parse
from urllib.parse import quote
from urllib.parse import unquote
from urllib.parse import urlencode
from urllib.parse import urlsplit
from urllib.parse import urlunsplit
from .datastructures import iter_multi_items


def _codec_error_url_quote(e: UnicodeError) -> tuple[str, int]:
    out = quote(e.object[e.start : e.end], safe="")
    return out, e.end


codecs.register_error("werkzeug.url_quote", _codec_error_url_quote)


def _make_unquote_part(name: str, chars: str) -> t.Callable[[str], str]:
    choices = "|".join(f"{ord(c):02X}" for c in sorted(chars))
    pattern = re.compile(f"((?:%(?:{choices}))+)", re.I)

    def _unquote_partial(value: str) -> str:
        parts = iter(pattern.split(value))
        out = []
        for part in parts:
            out.append(unquote(part, "utf-8", "werkzeug.url_quote"))
            out.append(next(parts, ""))
        return "".join(out)

    _unquote_partial.__name__ = f"_unquote_{name}"
    return _unquote_partial


_always_unsafe = bytes((*range(33), 37, 127)).decode()
_unquote_fragment = _make_unquote_part("fragment", _always_unsafe)
_unquote_query = _make_unquote_part("query", _always_unsafe + "&=+#")
_unquote_path = _make_unquote_part("path", _always_unsafe + "/?#")
_unquote_user = _make_unquote_part("user", _always_unsafe + ":@/?#")


def uri_to_iri(uri: str) -> str:
    parts = urlsplit(uri)
    path = _unquote_path(parts.path)
    query = _unquote_query(parts.query)
    fragment = _unquote_fragment(parts.fragment)
    if parts.hostname:
        netloc = _decode_idna(parts.hostname)
    else:
        netloc = ""
    if ":" in netloc:
        netloc = f"[{netloc}]"
    if parts.port:
        netloc = f"{netloc}:{parts.port}"
    if parts.username:
        auth = _unquote_user(parts.username)
        if parts.password:
            password = _unquote_user(parts.password)
            auth = f"{auth}:{password}"
        netloc = f"{auth}@{netloc}"
    return urlunsplit((parts.scheme, netloc, path, query, fragment))


def iri_to_uri(iri: str) -> str:
    parts = urlsplit(iri)
    path = quote(parts.path, safe="%!$&'()*+,/:;=@")
    query = quote(parts.query, safe="%!$&'()*+,/:;=?@")
    fragment = quote(parts.fragment, safe="%!#$&'()*+,/:;=?@")
    if parts.hostname:
        netloc = parts.hostname.encode("idna").decode("ascii")
    else:
        netloc = ""
    if ":" in netloc:
        netloc = f"[{netloc}]"
    if parts.port:
        netloc = f"{netloc}:{parts.port}"
    if parts.username:
        auth = quote(parts.username, safe="%!$&'()*+,;=")
        if parts.password:
            password = quote(parts.password, safe="%!$&'()*+,;=")
            auth = f"{auth}:{password}"
        netloc = f"{auth}@{netloc}"
    return urlunsplit((parts.scheme, netloc, path, query, fragment))


if "itms-services" not in urllib.parse.uses_netloc:
    urllib.parse.uses_netloc.append("itms-services")


def _decode_idna(domain: str) -> str:
    try:
        data = domain.encode("ascii")
    except UnicodeEncodeError:
        return domain
    try:
        return data.decode("idna")
    except UnicodeDecodeError:
        pass
    parts = []
    for part in data.split(b"."):
        try:
            parts.append(part.decode("idna"))
        except UnicodeDecodeError:
            parts.append(part.decode("ascii"))
    return ".".join(parts)


def _urlencode(query: t.Mapping[str, str] | t.Iterable[tuple[str, str]]) -> str:
    items = [x for x in iter_multi_items(query) if x[1] is not None]
    return urlencode(items, safe="!$'()*,/:;?@")
