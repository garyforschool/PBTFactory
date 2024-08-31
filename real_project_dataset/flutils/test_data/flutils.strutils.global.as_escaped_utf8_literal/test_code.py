def test_as_escaped_utf8_literal(self) -> None:
        arg = "1.★ 🛑"
        arg_lit = "'1.\\u2605 \\U0001f6d1'"
        ret = as_escaped_utf8_literal(arg)
        exp = "\\x31\\x2e\\xe2\\x98\\x85\\x20\\xf0\\x9f\\x9b\\x91"
        self.assertEqual(
            ret,
            exp,
            msg=f"""

as_escaped_utf8_literal({arg_lit})
expected: {exp!r}
     got: {ret!r}
""",
        )