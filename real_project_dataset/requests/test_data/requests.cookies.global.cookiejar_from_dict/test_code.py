def test_generic_cookiejar_works(self, httpbin):
        cj = cookielib.CookieJar()
        cookiejar_from_dict({"foo": "bar"}, cj)
        s = requests.session()
        s.cookies = cj
        r = s.get(httpbin("cookies"))
        assert r.json()["cookies"]["foo"] == "bar"
        assert s.cookies is cj

def test_param_cookiejar_works(self, httpbin):
        cj = cookielib.CookieJar()
        cookiejar_from_dict({"foo": "bar"}, cj)
        s = requests.session()
        r = s.get(httpbin("cookies"), cookies=cj)
        assert r.json()["cookies"]["foo"] == "bar"

def test_cookielib_cookiejar_on_redirect(self, httpbin):
        cj = cookiejar_from_dict({"foo": "bar"}, cookielib.CookieJar())
        s = requests.Session()
        s.cookies = cookiejar_from_dict({"cookie": "tasty"})
        req = requests.Request("GET", httpbin("headers"), cookies=cj)
        prep_req = req.prepare()
        resp = s.send(prep_req)
        resp.status_code = 302
        resp.headers["location"] = httpbin("get")
        redirects = s.resolve_redirects(resp, prep_req)
        resp = next(redirects)
        assert isinstance(prep_req._cookies, cookielib.CookieJar)
        assert isinstance(resp.request._cookies, cookielib.CookieJar)
        assert not isinstance(resp.request._cookies, requests.cookies.RequestsCookieJar)
        cookies = {}
        for c in resp.request._cookies:
            cookies[c.name] = c.value
        assert cookies["foo"] == "bar"
        assert cookies["cookie"] == "tasty"