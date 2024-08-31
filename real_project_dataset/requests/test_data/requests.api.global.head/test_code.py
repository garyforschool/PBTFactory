def test_http_301_doesnt_change_head_to_get(self, httpbin):
        r = requests.head(httpbin("status", "301"), allow_redirects=True)
        print(r.content)
        assert r.status_code == 200
        assert r.request.method == "HEAD"
        assert r.history[0].status_code == 301
        assert r.history[0].is_redirect

def test_http_302_doesnt_change_head_to_get(self, httpbin):
        r = requests.head(httpbin("status", "302"), allow_redirects=True)
        assert r.status_code == 200
        assert r.request.method == "HEAD"
        assert r.history[0].status_code == 302
        assert r.history[0].is_redirect

def test_http_303_doesnt_change_head_to_get(self, httpbin):
        r = requests.head(httpbin("status", "303"), allow_redirects=True)
        assert r.status_code == 200
        assert r.request.method == "HEAD"
        assert r.history[0].status_code == 303
        assert r.history[0].is_redirect

def test_HTTP_200_OK_HEAD(self, httpbin):
        r = requests.head(httpbin("get"))
        assert r.status_code == 200