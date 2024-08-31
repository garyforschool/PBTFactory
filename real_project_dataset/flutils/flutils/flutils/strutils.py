import re

__all__ = [
    "as_escaped_unicode_literal",
    "as_escaped_utf8_literal",
    "camel_to_underscore",
    "convert_escaped_unicode_literal",
    "convert_escaped_utf8_literal",
    "underscore_to_camel",
]


def as_escaped_unicode_literal(text: str) -> str:
    out = ""
    for c in text:
        c_hex = hex(ord(c))[2:]
        c_len = len(c_hex)
        if c_len in (1, 2):
            out += "\\x{:0>2}".format(c_hex)
        elif c_len in (3, 4):
            out += "\\u{:0>4}".format(c_hex)
        else:
            out += "\\U{:0>8}".format(c_hex)
    return out


def as_escaped_utf8_literal(text: str) -> str:
    out = ""
    text_bytes = text.encode("utf8")
    for c in text_bytes:
        out += "\\%s" % hex(c)[1:]
    return out


_CAMEL_TO_UNDERSCORE_RE = re.compile("((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))")


def camel_to_underscore(text: str) -> str:
    return _CAMEL_TO_UNDERSCORE_RE.sub("_\\1", text).lower()


def convert_escaped_unicode_literal(text: str) -> str:
    text_bytes = text.encode()
    return text_bytes.decode("unicode_escape")


def convert_escaped_utf8_literal(text: str) -> str:
    from flutils.codecs import register_codecs

    register_codecs()
    text_bytes = text.encode("utf-8")
    text = text_bytes.decode("raw_utf8_escape")
    return text


def underscore_to_camel(text: str, lower_first: bool = True) -> str:
    out = "".join([(x.capitalize() or "") for x in text.split("_")])
    if lower_first is True:
        return out[:1].lower() + out[1:]
    return out
