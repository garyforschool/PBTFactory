@pytest.mark.parametrize(
    "uri, expected",
    (
        ("http://example.com/?a=%--", "http://example.com/?a=%--"),
        ("http://example.com/?a=%300", "http://example.com/?a=00"),
    ),
)
def test_unquote_unreserved(uri, expected):
    assert unquote_unreserved(uri) == expected