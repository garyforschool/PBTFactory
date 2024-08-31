def test_camel_to_underscore(self) -> None:
        values: List[Values] = []
        _add_values("FooBar", "foo_bar", values)
        _add_values("oneTwo", "one_two", values)
        _add_values("THREEFourFive", "three_four_five", values)
        _add_values("sixSEVENEight", "six_seven_eight", values)
        for v in values:
            with self.subTest(v=v):
                ret = camel_to_underscore(v.arg)
                self.assertEqual(
                    ret,
                    v.exp,
                    msg=f"""

camel_to_underscore({v.arg!r})
expected: {v.exp!r}
     got: {ret!r}
""",
                )