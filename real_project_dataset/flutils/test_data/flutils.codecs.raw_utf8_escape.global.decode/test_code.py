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