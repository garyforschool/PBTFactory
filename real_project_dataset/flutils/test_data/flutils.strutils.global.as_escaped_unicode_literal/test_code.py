def test_as_escaped_unicode_literal(self) -> None:
        arg = "1.★ 🛑"
        arg_lit = "'1.\\u2605 \\U0001f6d1'"
        ret = as_escaped_unicode_literal(arg)
        exp = "\\x31\\x2e\\u2605\\x20\\U0001f6d1"
        self.assertEqual(
            ret,
            exp,
            msg=f"""

as_escaped_unicode_literal({arg_lit})
expected: {exp!r}
     got: {ret!r}
""",
        )