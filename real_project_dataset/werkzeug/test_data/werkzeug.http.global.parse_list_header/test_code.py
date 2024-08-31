@pytest.mark.parametrize(
        ("value", "expect"),
        [
            ("a b", ["a b"]),
            ("a b, c", ["a b", "c"]),
            ('a b, "c, d"', ["a b", "c, d"]),
            ('"a\\"b", c', ['a"b', "c"]),
        ],
    )
    def test_list_header(self, value, expect):
        assert http.parse_list_header(value) == expect