def test_convert_escaped_utf8_literal(self) -> None:
        values = (("hello\\xe2\\x98\\x85", "hello★"),)
        for arg, exp in values:
            with self.subTest(arg=arg, exp=exp):
                ret = convert_escaped_utf8_literal(arg)
                self.assertEqual(
                    ret,
                    exp,
                    msg=f"""

convert_escaped_utf8_literal({arg})
expected: {exp!r}
     got: {ret!r}
""",
                )