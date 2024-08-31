@pytest.mark.parametrize(
        "value, expected",
        (
            (None, None),
            ("Test", "Test"),
            ('"Test"', "Test"),
            ('"Test\\\\"', "Test\\"),
            ('"\\\\Comp\\Res"', "\\Comp\\Res"),
        ),
    )
    def test_valid(self, value, expected):
        assert unquote_header_value(value) == expected

def test_is_filename(self):
        assert unquote_header_value('"\\\\Comp\\Res"', True) == "\\\\Comp\\Res"