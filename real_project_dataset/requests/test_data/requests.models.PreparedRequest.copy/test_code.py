@pytest.mark.parametrize(
    "kwargs",
    (
        None,
        {
            "method": "GET",
            "url": "http://www.example.com",
            "data": "foo=bar",
            "hooks": default_hooks(),
        },
        {
            "method": "GET",
            "url": "http://www.example.com",
            "data": "foo=bar",
            "hooks": default_hooks(),
            "cookies": {"foo": "bar"},
        },
        {"method": "GET", "url": "http://www.example.com/üniçø∂é"},
    ),
)
def test_prepared_copy(kwargs):
    p = PreparedRequest()
    if kwargs:
        p.prepare(**kwargs)
    copy = p.copy()
    for attr in ("method", "url", "headers", "_cookies", "body", "hooks"):
        assert getattr(p, attr) == getattr(copy, attr)