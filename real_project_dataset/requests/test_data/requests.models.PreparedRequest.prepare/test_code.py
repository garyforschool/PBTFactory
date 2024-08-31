def test_json_encodes_as_bytes():
    body = {"key": "value"}
    p = PreparedRequest()
    p.prepare(method="GET", url="https://www.example.com/", json=body)
    assert isinstance(p.body, bytes)

@pytest.mark.parametrize(
    "var,url,proxy",
    [
        ("http_proxy", "http://example.com", "socks5://proxy.com:9876"),
        ("https_proxy", "https://example.com", "socks5://proxy.com:9876"),
        ("all_proxy", "http://example.com", "socks5://proxy.com:9876"),
        ("all_proxy", "https://example.com", "socks5://proxy.com:9876"),
    ],
)
def test_proxy_env_vars_override_default(var, url, proxy):
    session = requests.Session()
    prep = PreparedRequest()
    prep.prepare(method="GET", url=url)
    kwargs = {var: proxy}
    scheme = urlparse(url).scheme
    with override_environ(**kwargs):
        proxies = session.rebuild_proxies(prep, {})
        assert scheme in proxies
        assert proxies[scheme] == proxy

@pytest.mark.parametrize(
    "data",
    (
        (("a", "b"), ("c", "d")),
        (("c", "d"), ("a", "b")),
        (("a", "b"), ("c", "d"), ("e", "f")),
    ),
)
def test_data_argument_accepts_tuples(data):
    p = PreparedRequest()
    p.prepare(
        method="GET", url="http://www.example.com", data=data, hooks=default_hooks()
    )
    assert p.body == urlencode(data)

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