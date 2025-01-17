import base64
import pickle
import unittest
from collections import UserString
from typing import Any, Dict, List, NamedTuple
from flutils.codecs.b64 import decode, encode, register

register()
NAME = "b64"


class AString(UserString):
    pass


class AStringPatched(UserString):

    def encode(self, *args, **kwargs) -> bytes:
        return self.data.encode(*args, **kwargs)


class Values(NamedTuple):
    obj: Any
    obj_bytes: bytes
    obj_bytes_len: int
    b64_bytes: bytes
    b64_str: str
    b64_str_wrapped: str
    b64_str_len: int


TEST_VALUES: List[Values] = []


def _wrap(data: str) -> str:
    combined_length = len(data) + 4
    if combined_length > 60:
        out = ""
        tmp_data = data
        while tmp_data:
            if len(tmp_data) > 56:
                out += "    %s\n" % tmp_data[0:56]
                tmp_data = tmp_data[56:]
            else:
                out += "    %s\n" % tmp_data
                tmp_data = ""
        return out
    return data


def _build_value(obj: Any) -> Values:
    kwargs: Dict[str, Any] = dict(obj=obj)
    kwargs["obj_bytes"] = pickle.dumps(obj)
    kwargs["obj_bytes_len"] = len(kwargs["obj_bytes"])
    kwargs["b64_bytes"] = base64.b64encode(kwargs["obj_bytes"])
    kwargs["b64_str"] = kwargs["b64_bytes"].decode("utf-8")
    kwargs["b64_str_wrapped"] = _wrap(kwargs["b64_str"])
    kwargs["b64_str_len"] = len(kwargs["b64_str"])
    out = Values(**kwargs)
    return out


def _add_value(obj: Any) -> None:
    vals = _build_value(obj)
    TEST_VALUES.append(vals)


_add_value("Test")
_add_value(
    "Testing One Two Three Four Five Six Seven Eight Nine Ten Eleven TwelveThirteen Fourteen Fifteen Sixteen Seventeen Eighteen Nineteen Twenty"
)
_add_value(1)
_add_value(True)
_add_value(None)
_add_value(dict(a=1, b=2))


class TestB64(unittest.TestCase):

    def test_encode_value_bytes(self) -> None:
        for v in TEST_VALUES:
            with self.subTest(v=v):
                ret = encode(v.b64_str_wrapped)[0]
                self.assertEqual(
                    ret,
                    v.obj_bytes,
                    msg=f"""

encode({v.b64_str!r})[0]

expected: {v.obj_bytes!r}

     got: {ret!r}

""",
                )

    def test_encode_consumed_value(self) -> None:
        for v in TEST_VALUES:
            with self.subTest(v=v):
                ret = encode(v.b64_str)[1]
                self.assertEqual(
                    ret,
                    v.b64_str_len,
                    msg=f"""

encode({v.b64_str!r})[1]

expected: {v.b64_str_len!r}

     got: {ret!r}

""",
                )

    def test_decode_value_bytes(self) -> None:
        for v in TEST_VALUES:
            with self.subTest(v=v):
                ret = decode(v.obj_bytes)[0]
                self.assertEqual(
                    ret,
                    v.b64_str,
                    msg=f"""

decode({v.obj_bytes!r})[0]

expected: {v.b64_str!r}

     got: {ret!r}

""",
                )

    def test_decode_consumed_value(self) -> None:
        for v in TEST_VALUES:
            with self.subTest(v=v):
                ret = decode(v.obj_bytes)[1]
                self.assertEqual(
                    ret,
                    v.obj_bytes_len,
                    msg=f"""

decode({v.obj_bytes!r})[1]

expected: {v.obj_bytes_len!r}

     got: {ret!r}

""",
                )

    def test_registered_encode_value(self) -> None:
        for v in TEST_VALUES:
            with self.subTest(v=v):
                ret = v.b64_str_wrapped.encode(NAME)
                self.assertEqual(
                    ret,
                    v.obj_bytes,
                    msg=f"""

{v.b64_str_wrapped!r}).encode({NAME!r})

expected: {v.obj_bytes!r}

     got: {ret!r}

""",
                )

    def test_registered_decode_value(self) -> None:
        for v in TEST_VALUES:
            with self.subTest(v=v):
                ret = v.obj_bytes.decode(NAME)
                self.assertEqual(
                    ret,
                    v.b64_str,
                    msg=f"""

{v.obj_bytes!r}).encode({NAME!r})

expected: {v.b64_str!r}

     got: {ret!r}

""",
                )

    def test_encode_user_string(self) -> None:
        arg = "Testing1"
        cls = AString
        obj = AString(arg)
        chk = obj.encode("utf-8")
        if isinstance(chk, bytes) is False:
            cls = AStringPatched
            obj = AStringPatched(arg)
        for v in TEST_VALUES:
            with self.subTest(v=v):
                obj = cls(v.b64_str_wrapped)
                ret = obj.encode(NAME)
                self.assertEqual(
                    ret,
                    v.obj_bytes,
                    msg=f"""

{obj!r}).encode({NAME!r})

expected: {v.obj_bytes!r}

     got: {ret!r}

""",
                )

    def test_end_to_end(self) -> None:
        for v in TEST_VALUES:
            with self.subTest(v=v):
                b64_str = v.obj_bytes.decode(NAME)
                obj_bytes = b64_str.encode(NAME)
                ret = pickle.loads(obj_bytes)
                self.assertEqual(
                    ret, v.obj, msg=f"\n\nexpected: {v.obj!r}\n\n     got: {ret!r}\n\n"
                )

    def test_raises_unicode_encode_error(self) -> None:
        val = "{foo}"
        with self.assertRaises(UnicodeEncodeError):
            val.encode("b64")
