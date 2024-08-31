@pytest.mark.parametrize(
    "url, expected, proxies",
    (
        ("hTTp://u:p@Some.Host/path", "http://some.host.proxy", http_proxies),
        ("hTTp://u:p@Other.Host/path", "http://http.proxy", http_proxies),
        ("hTTp:///path", "http://http.proxy", http_proxies),
        ("hTTps://Other.Host", None, http_proxies),
        ("file:///etc/motd", None, http_proxies),
        ("hTTp://u:p@Some.Host/path", "socks5://some.host.proxy", all_proxies),
        ("hTTp://u:p@Other.Host/path", "socks5://http.proxy", all_proxies),
        ("hTTp:///path", "socks5://http.proxy", all_proxies),
        ("hTTps://Other.Host", "socks5://http.proxy", all_proxies),
        ("http://u:p@other.host/path", "http://http.proxy", mixed_proxies),
        ("http://u:p@some.host/path", "http://some.host.proxy", mixed_proxies),
        ("https://u:p@other.host/path", "socks5://http.proxy", mixed_proxies),
        ("https://u:p@some.host/path", "socks5://http.proxy", mixed_proxies),
        ("https://", "socks5://http.proxy", mixed_proxies),
        ("file:///etc/motd", "socks5://http.proxy", all_proxies),
    ),
)
def test_select_proxies(url, expected, proxies):
    assert select_proxy(url, proxies) == expected