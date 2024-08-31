@pytest.mark.parametrize(
        "url",
        (
            "http://192.168.0.1:5000/",
            "http://192.168.0.1/",
            "http://172.16.1.1/",
            "http://172.16.1.1:5000/",
            "http://localhost.localdomain:5000/v1.0/",
        ),
    )
    def test_bypass(self, url):
        assert get_environ_proxies(url, no_proxy=None) == {}

@pytest.mark.parametrize(
        "url",
        ("http://192.168.1.1:5000/", "http://192.168.1.1/", "http://www.requests.com/"),
    )
    def test_not_bypass(self, url):
        assert get_environ_proxies(url, no_proxy=None) != {}

@pytest.mark.parametrize(
        "url",
        ("http://192.168.1.1:5000/", "http://192.168.1.1/", "http://www.requests.com/"),
    )
    def test_bypass_no_proxy_keyword(self, url):
        no_proxy = "192.168.1.1,requests.com"
        assert get_environ_proxies(url, no_proxy=no_proxy) == {}

@pytest.mark.parametrize(
        "url",
        (
            "http://192.168.0.1:5000/",
            "http://192.168.0.1/",
            "http://172.16.1.1/",
            "http://172.16.1.1:5000/",
            "http://localhost.localdomain:5000/v1.0/",
        ),
    )
    def test_not_bypass_no_proxy_keyword(self, url, monkeypatch):
        monkeypatch.setenv("http_proxy", "http://proxy.example.com:3128/")
        no_proxy = "192.168.1.1,requests.com"
        assert get_environ_proxies(url, no_proxy=no_proxy) != {}