def test_unicode_method_name(self, httpbin):
        with open(__file__, "rb") as f:
            files = {"file": f}
            r = requests.request(method="POST", url=httpbin("post"), files=files)
        assert r.status_code == 200

def test_encoded_methods(self, httpbin):
        r = requests.request(b"GET", httpbin("get"))
        assert r.ok