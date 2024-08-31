@pytest.mark.parametrize(
    "url, expected",
    (
        ("http://u:p@example.com/path?a=1#test", "http://example.com/path?a=1"),
        ("http://example.com/path", "http://example.com/path"),
        ("//u:p@example.com/path", "//example.com/path"),
        ("//example.com/path", "//example.com/path"),
        ("example.com/path", "//example.com/path"),
        ("scheme:u:p@example.com/path", "scheme://example.com/path"),
    ),
)
def test_urldefragauth(url, expected):
    assert urldefragauth(url) == expected