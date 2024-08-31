@pytest.mark.parametrize(
    ("value", "expect"),
    [
        (
            "Sun, 06 Nov 1994 08:49:37 GMT    ",
            datetime(1994, 11, 6, 8, 49, 37, tzinfo=timezone.utc),
        ),
        (
            "Sunday, 06-Nov-94 08:49:37 GMT",
            datetime(1994, 11, 6, 8, 49, 37, tzinfo=timezone.utc),
        ),
        (
            " Sun Nov  6 08:49:37 1994",
            datetime(1994, 11, 6, 8, 49, 37, tzinfo=timezone.utc),
        ),
        ("foo", None),
        (
            " Sun 02 Feb 1343 08:49:37 GMT",
            datetime(1343, 2, 2, 8, 49, 37, tzinfo=timezone.utc),
        ),
        ("Thu, 01 Jan 1970 00:00:00 GMT", datetime(1970, 1, 1, tzinfo=timezone.utc)),
        ("Thu, 33 Jan 1970 00:00:00 GMT", None),
    ],
)
def test_parse_date(value, expect):
    assert http.parse_date(value) == expect