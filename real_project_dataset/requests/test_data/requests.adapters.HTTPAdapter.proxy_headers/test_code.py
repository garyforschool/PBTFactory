def test_proxy_auth(self):
        adapter = HTTPAdapter()
        headers = adapter.proxy_headers("http://user:pass@httpbin.org")
        assert headers == {"Proxy-Authorization": "Basic dXNlcjpwYXNz"}

def test_proxy_auth_empty_pass(self):
        adapter = HTTPAdapter()
        headers = adapter.proxy_headers("http://user:@httpbin.org")
        assert headers == {"Proxy-Authorization": "Basic dXNlcjo="}