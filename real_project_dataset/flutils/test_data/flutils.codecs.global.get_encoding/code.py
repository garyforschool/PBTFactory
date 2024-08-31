import codecs
from locale import getpreferredencoding
from sys import getdefaultencoding
from typing import Optional, cast
from . import b64, raw_utf8_escape

__all__ = ["register_codecs", "get_encoding", "SYSTEM_ENCODING"]


def register_codecs() -> None:
    raw_utf8_escape.register()
    b64.register()


SYSTEM_ENCODING: str = getpreferredencoding() or getdefaultencoding()
"""str: The default encoding as indicated by the system."""


def get_encoding(
    name: Optional[str] = None, default: Optional[str] = SYSTEM_ENCODING
) -> str:
    if name is None:
        name = ""
    if hasattr(name, "encode") is False:
        name = ""
    name = cast(str, name)
    name = name.strip()
    if default is None:
        default = ""
    if hasattr(default, "encode") is False:
        default = ""
    default = cast(str, default)
    default = default.strip()
    if default:
        try:
            codec = codecs.lookup(default)
        except LookupError:
            raise LookupError(
                f"The given 'default' of {default!r} is an invalid encoding codec name."
            )
        else:
            default = codec.name
    try:
        codec = codecs.lookup(name)
    except LookupError:
        if default:
            return default
        raise LookupError(
            f"The given 'name' of {name!r} is an invalid encoding codec name."
        )
    else:
        return codec.name