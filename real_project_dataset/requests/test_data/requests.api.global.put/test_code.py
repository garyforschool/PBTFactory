def test_HTTP_200_OK_PUT(self, httpbin):
        r = requests.put(httpbin("put"))
        assert r.status_code == 200

def test_unicode_header_name(self, httpbin):
        requests.put(
            httpbin("put"),
            headers={"Content-Type": "application/octet-stream"},
            data="ÿ",
        )