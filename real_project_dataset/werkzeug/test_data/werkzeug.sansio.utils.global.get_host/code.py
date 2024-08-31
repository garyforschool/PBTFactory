from __future__ import annotations
import typing as t
from urllib.parse import quote
from .._internal import _plain_int
from ..exceptions import SecurityError
from ..urls import uri_to_iri


def host_is_trusted(hostname: str | None, trusted_list: t.Iterable[str]) -> bool:
    if not hostname:
        return False
    try:
        hostname = hostname.partition(":")[0].encode("idna").decode("ascii")
    except UnicodeEncodeError:
        return False
    if isinstance(trusted_list, str):
        trusted_list = [trusted_list]
    for ref in trusted_list:
        if ref.startswith("."):
            ref = ref[1:]
            suffix_match = True
        else:
            suffix_match = False
        try:
            ref = ref.partition(":")[0].encode("idna").decode("ascii")
        except UnicodeEncodeError:
            return False
        if ref == hostname or suffix_match and hostname.endswith(f".{ref}"):
            return True
    return False


def get_host(
    scheme: str,
    host_header: str | None,
    server: tuple[str, int | None] | None = None,
    trusted_hosts: t.Iterable[str] | None = None,
) -> str:
    host = ""
    if host_header is not None:
        host = host_header
    elif server is not None:
        host = server[0]
        if server[1] is not None:
            host = f"{host}:{server[1]}"
    if scheme in {"http", "ws"} and host.endswith(":80"):
        host = host[:-3]
    elif scheme in {"https", "wss"} and host.endswith(":443"):
        host = host[:-4]
    if trusted_hosts is not None:
        if not host_is_trusted(host, trusted_hosts):
            raise SecurityError(f"Host {host!r} is not trusted.")
    return host


def get_current_url(
    scheme: str,
    host: str,
    root_path: str | None = None,
    path: str | None = None,
    query_string: bytes | None = None,
) -> str:
    url = [scheme, "://", host]
    if root_path is None:
        url.append("/")
        return uri_to_iri("".join(url))
    url.append(quote(root_path.rstrip("/"), safe="!$&'()*+,/:;=@%"))
    url.append("/")
    if path is None:
        return uri_to_iri("".join(url))
    url.append(quote(path.lstrip("/"), safe="!$&'()*+,/:;=@%"))
    if query_string:
        url.append("?")
        url.append(quote(query_string, safe="!$&'()*+,/:;=?@%"))
    return uri_to_iri("".join(url))


def get_content_length(
    http_content_length: str | None = None, http_transfer_encoding: str | None = None
) -> int | None:
    if http_transfer_encoding == "chunked" or http_content_length is None:
        return None
    try:
        return max(0, _plain_int(http_content_length))
    except ValueError:
        return 0