def test_respect_proxy_env_on_request(self, httpbin):
        with override_environ(http_proxy=INVALID_PROXY):
            with pytest.raises(ProxyError):
                session = requests.Session()
                session.request(method="GET", url=httpbin())

def test_proxy_authorization_preserved_on_request(self, httpbin):
        proxy_auth_value = "Bearer XXX"
        session = requests.Session()
        session.headers.update({"Proxy-Authorization": proxy_auth_value})
        resp = session.request(method="GET", url=httpbin("get"))
        sent_headers = resp.json().get("headers", {})
        assert sent_headers.get("Proxy-Authorization") == proxy_auth_value

def test_request_with_bytestring_host(self, httpbin):
        s = requests.Session()
        resp = s.request(
            "GET",
            httpbin("cookies/set?cookie=value"),
            allow_redirects=False,
            headers={"Host": b"httpbin.org"},
        )
        assert resp.cookies.get("cookie") == "value"