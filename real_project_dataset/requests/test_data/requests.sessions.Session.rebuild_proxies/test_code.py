@pytest.mark.parametrize(
        "url,has_proxy_auth",
        (("http://example.com", True), ("https://example.com", False)),
    )
    def test_proxy_authorization_not_appended_to_https_request(
        self, url, has_proxy_auth
    ):
        session = requests.Session()
        proxies = {
            "http": "http://test:pass@localhost:8080",
            "https": "http://test:pass@localhost:8090",
        }
        req = requests.Request("GET", url)
        prep = req.prepare()
        session.rebuild_proxies(prep, proxies)
        assert ("Proxy-Authorization" in prep.headers) is has_proxy_auth

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