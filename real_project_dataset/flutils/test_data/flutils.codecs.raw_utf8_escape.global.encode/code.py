import codecs
from collections import UserString
from functools import reduce
from typing import ByteString as _ByteString
from typing import Generator, Optional, Tuple, Union, cast

_Str = Union[str, UserString]


def _each_utf8_hex(text: _Str) -> Generator[str, None, None]:
    for char in text:
        if ord(char) < 128 and char.isprintable():
            yield char
            continue
        utf8_bytes = char.encode("utf8")
        for utf8_byte in utf8_bytes:
            str_hex = "\\%s" % hex(utf8_byte)[1:]
            yield str_hex


def encode(text: _Str, errors: _Str = "strict") -> Tuple[bytes, int]:
    text_input = str(text)
    errors_input = str(errors)
    text_bytes_utf8 = text_input.encode("utf-8")
    text_bytes_utf8 = cast(bytes, text_bytes_utf8)
    text_str_latin1 = text_bytes_utf8.decode("unicode_escape")
    text_bytes_utf8 = text_str_latin1.encode("latin1")
    try:
        text_str = text_bytes_utf8.decode("utf-8", errors=errors_input)
    except UnicodeDecodeError as e:
        raise UnicodeEncodeError("eutf8h", str(text_input), e.start, e.end, e.reason)
    out_str: str = reduce(lambda a, b: f"{a}{b}", _each_utf8_hex(text_str))
    out_bytes = out_str.encode("utf-8")
    return out_bytes, len(text)


def decode(data: _ByteString, errors: _Str = "strict") -> Tuple[str, int]:
    data_bytes = bytes(data)
    errors_input = str(errors)
    text_str_latin1 = data_bytes.decode("unicode_escape")
    text_bytes_utf8 = text_str_latin1.encode("latin1")
    try:
        out = text_bytes_utf8.decode("utf-8", errors=errors_input)
    except UnicodeDecodeError as e:
        raise UnicodeDecodeError("eutf8h", data_bytes, e.start, e.end, e.reason)
    return out, len(data)


NAME = __name__.split(".")[-1]


def _get_codec_info(name: str) -> Optional[codecs.CodecInfo]:
    if name == NAME:
        obj = codecs.CodecInfo(name=NAME, encode=encode, decode=decode)
        return obj
    return None


def register() -> None:
    try:
        codecs.getdecoder(NAME)
    except LookupError:
        codecs.register(_get_codec_info)