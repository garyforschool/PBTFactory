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