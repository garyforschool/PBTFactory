def test_convert_escaped_unicode_literal(self) -> None:
        exp = "1.★ 🛑"
        arg = "\\x31\\x2e\\u2605\\x20\\U0001f6d1"
        ret = convert_escaped_unicode_literal(arg)
        self.assertEqual(
            ret,
            exp,
            msg=f"""

convert_escaped_unicode_literal({arg!r})
expected: {exp!r}
     got: {ret!r}
""",
        )