@pytest.mark.parametrize(
    "value, expected",
    (
        ("example.com/path", "http://example.com/path"),
        ("//example.com/path", "http://example.com/path"),
        ("example.com:80", "http://example.com:80"),
        (
            "http://user:pass@example.com/path?query",
            "http://user:pass@example.com/path?query",
        ),
        ("http://user@example.com/path?query", "http://user@example.com/path?query"),
    ),
)
def test_prepend_scheme_if_needed(value, expected):
    assert prepend_scheme_if_needed(value, "http") == expected