@pytest.mark.parametrize(
    ("http_content_length", "http_transfer_encoding", "expected"),
    [
        ("2", None, 2),
        (" 2", None, 2),
        ("2 ", None, 2),
        (None, None, None),
        (None, "chunked", None),
        ("a", None, 0),
        ("-2", None, 0),
    ],
)
def test_get_content_length(
    http_content_length: str | None,
    http_transfer_encoding: str | None,
    expected: int | None,
) -> None:
    assert get_content_length(http_content_length, http_transfer_encoding) == expected