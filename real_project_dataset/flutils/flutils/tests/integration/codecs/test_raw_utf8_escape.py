import unittest
from collections import UserString
from typing import NamedTuple, Tuple
from flutils.codecs import register_codecs
from flutils.codecs.raw_utf8_escape import NAME, _get_codec_info, decode, encode


class Values(NamedTuple):
    txt_str: str
    txt_bytes: bytes
    txt_str_len: int
    txt_bytes_len: int


TEST_VALUES: Tuple[Values, ...] = (
    Values("Test", b"Test", 4, 4),
    Values(
        "1.★ 2.☆ 3.⭐︎ 4.✩ 5.✪ 6.✫7.✭ 8.✮ 9.🇺🇸 10.🇾🇹 11.🛑",
        b"1.\\xe2\\x98\\x85 2.\\xe2\\x98\\x86 3.\\xe2\\xad\\x90\\xef\\xb8\\x8e 4.\\xe2\\x9c\\xa9 5.\\xe2\\x9c\\xaa 6.\\xe2\\x9c\\xab7.\\xe2\\x9c\\xad 8.\\xe2\\x9c\\xae 9.\\xf0\\x9f\\x87\\xba\\xf0\\x9f\\x87\\xb8 10.\\xf0\\x9f\\x87\\xbe\\xf0\\x9f\\x87\\xb9 11.\\xf0\\x9f\\x9b\\x91",
        47,
        221,
    ),
    Values("Te\\st★", b"Te\\st\\xe2\\x98\\x85", 6, 17),
    Values("☆⭐︎", b"\\xe2\\x98\\x86\\xe2\\xad\\x90\\xef\\xb8\\x8e", 3, 36),
)
register_codecs()


class AString(UserString):
    pass


class AStringPatched(UserString):

    def encode(self, *args, **kwargs) -> bytes:
        return self.data.encode(*args, **kwargs)


class TestRawUtf8Escape(unittest.TestCase):

    def test_encode_value_bytes(self) -> None:
        for v in TEST_VALUES:
            ret = encode(v.txt_str)[0]
            self.assertEqual(
                ret,
                v.txt_bytes,
                msg=f"""

encode({v.txt_str!r})[0]

expected: {v.txt_bytes!r}

     got: {ret!r}

""",
            )

    def test_encode_consumed_value(self) -> None:
        for v in TEST_VALUES:
            ret = encode(v.txt_str)[1]
            self.assertEqual(
                ret,
                v.txt_str_len,
                msg=f"""

encode({v.txt_str!r})[1]

expected: {v.txt_str_len!r}

     got: {ret!r}

""",
            )

    def test_encode_raises_unicode_encode_error(self) -> None:
        with self.assertRaises(UnicodeEncodeError):
            encode("Hello\\x80")

    def test_decode_value_bytes(self) -> None:
        for v in TEST_VALUES:
            ret = decode(v.txt_bytes)[0]
            self.assertEqual(
                ret,
                v.txt_str,
                msg=f"""

decode({v.txt_bytes!r})[0]

expected: {v.txt_str!r}

     got: {ret!r}

""",
            )

    def test_decode_consumed_value(self) -> None:
        for v in TEST_VALUES:
            ret = decode(v.txt_bytes)[1]
            self.assertEqual(
                ret,
                v.txt_bytes_len,
                msg=f"""

decode({v.txt_bytes!r})[1]

expected: {v.txt_bytes_len!r}

     got: {ret!r}

""",
            )

    def test_encode_raises_unicode_decode_error(self) -> None:
        with self.assertRaises(UnicodeDecodeError):
            decode(b"Hello\\x80")

    def test_registered_encode_value(self) -> None:
        for v in TEST_VALUES:
            ret = v.txt_str.encode(NAME)
            self.assertEqual(
                ret,
                v.txt_bytes,
                msg=f"""

{v.txt_str!r}.encode({NAME!r})

expected: {v.txt_bytes!r}

     got: {ret!r}

""",
            )

    def test_registered_decode_value(self) -> None:
        for v in TEST_VALUES:
            ret = v.txt_bytes.decode(NAME)
            self.assertEqual(
                ret,
                v.txt_str,
                msg=f"""

{v.txt_bytes!r}.decode({NAME!r})

expected: {v.txt_str!r}

     got: {ret!r}

""",
            )

    def test_encode_user_string(self) -> None:
        arg = "Testing1"
        obj = AString(arg)
        chk = obj.encode("utf-8")
        if isinstance(chk, bytes) is False:
            obj = AStringPatched(arg)
        exp = b"Testing1"
        ret = obj.encode(NAME)
        ret_type = type(ret).__name__
        self.assertEqual(
            ret,
            exp,
            msg=f"""

{arg!r}.encode({NAME!r})

expected: {exp!r}

     got: {ret!r}

    type: {ret_type}

""",
        )

    def test_get_codec_info(self) -> None:
        val = _get_codec_info("foo")
        self.assertEqual(val, None)
