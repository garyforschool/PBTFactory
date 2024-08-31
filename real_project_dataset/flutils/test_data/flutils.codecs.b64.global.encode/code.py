import base64
import codecs
from binascii import Error
from collections import UserString
from typing import ByteString as _ByteString
from typing import Optional, Tuple, Union

_STR = Union[str, UserString]


def encode(text: _STR, errors: _STR = "strict") -> Tuple[bytes, int]:
    text_input = str(text)
    text_str = text_input.strip()
    text_str = "\n".join(
        filter(
            lambda x: len(x) > 0,
            map(lambda x: x.strip(), text_str.strip().splitlines()),
        )
    )
    text_bytes = text_str.encode("utf-8")
    try:
        out = base64.decodebytes(text_bytes)
    except Error as e:
        raise UnicodeEncodeError(
            "b64",
            text_input,
            0,
            len(text),
            f"{text_str!r} is not a proper bas64 character string: {e}",
        )
    return out, len(text)


def decode(data: _ByteString, errors: _STR = "strict") -> Tuple[str, int]:
    data_bytes = bytes(data)
    encoded_bytes = base64.b64encode(data_bytes)
    encoded_str = encoded_bytes.decode("utf-8")
    return encoded_str, len(data)


NAME = __name__.split(".")[-1]


def _get_codec_info(name: str) -> Optional[codecs.CodecInfo]:
    if name == NAME:
        obj = codecs.CodecInfo(name=NAME, decode=decode, encode=encode)
        return obj
    return None


def register() -> None:
    try:
        codecs.getdecoder(NAME)
    except LookupError:
        codecs.register(_get_codec_info)