def test_underscore_to_camel(self) -> None:
        values: List[Values] = []
        _add_values("foo_bar", "fooBar", values, lower_first=True)
        _add_values("one__two", "OneTwo", values, lower_first=False)
        _add_values("three__four__", "threeFour", values, lower_first=True)
        _add_values("__five_six__", "FiveSix", values, lower_first=False)
        for v in values:
            with self.subTest(v=v):
                ret = underscore_to_camel(v.arg, lower_first=v.lower_first)
                self.assertEqual(
                    ret,
                    v.exp,
                    msg=f"""

underscore_to_camel({v.arg!r}, lower_first={v.lower_first!r})
expected: {v.exp!r}
     got: {ret!r}
""",
                )