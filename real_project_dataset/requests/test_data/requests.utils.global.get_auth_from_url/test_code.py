@pytest.mark.parametrize(
    "url, auth",
    (
        (
            f"http://{ENCODED_USER}:{ENCODED_PASSWORD}@request.com/url.html#test",
            (USER, PASSWORD),
        ),
        ("http://user:pass@complex.url.com/path?query=yes", ("user", "pass")),
        (
            "http://user:pass%20pass@complex.url.com/path?query=yes",
            ("user", "pass pass"),
        ),
        ("http://user:pass pass@complex.url.com/path?query=yes", ("user", "pass pass")),
        (
            "http://user%25user:pass@complex.url.com/path?query=yes",
            ("user%user", "pass"),
        ),
        (
            "http://user:pass%23pass@complex.url.com/path?query=yes",
            ("user", "pass#pass"),
        ),
        ("http://complex.url.com/path?query=yes", ("", "")),
    ),
)
def test_get_auth_from_url(url, auth):
    assert get_auth_from_url(url) == auth