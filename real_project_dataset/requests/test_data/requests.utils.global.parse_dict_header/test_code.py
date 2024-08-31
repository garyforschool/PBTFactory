@pytest.mark.parametrize(
    "value, expected",
    (
        ('foo="is a fish", bar="as well"', {"foo": "is a fish", "bar": "as well"}),
        ("key_without_value", {"key_without_value": None}),
    ),
)
def test_parse_dict_header(value, expected):
    assert parse_dict_header(value) == expected