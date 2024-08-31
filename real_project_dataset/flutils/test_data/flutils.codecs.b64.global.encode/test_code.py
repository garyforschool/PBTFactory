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