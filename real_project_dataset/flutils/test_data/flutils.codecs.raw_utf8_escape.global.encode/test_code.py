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