def test_header_and_body_removal_on_redirect(self, httpbin):
        purged_headers = "Content-Length", "Content-Type"
        ses = requests.Session()
        req = requests.Request("POST", httpbin("post"), data={"test": "data"})
        prep = ses.prepare_request(req)
        resp = ses.send(prep)
        resp.status_code = 302
        resp.headers["location"] = "get"
        next_resp = next(ses.resolve_redirects(resp, prep))
        assert next_resp.request.body is None
        for header in purged_headers:
            assert header not in next_resp.request.headers

def test_transfer_enc_removal_on_redirect(self, httpbin):
        purged_headers = "Transfer-Encoding", "Content-Type"
        ses = requests.Session()
        req = requests.Request("POST", httpbin("post"), data=(b"x" for x in range(1)))
        prep = ses.prepare_request(req)
        assert "Transfer-Encoding" in prep.headers
        resp = requests.Response()
        resp.raw = io.BytesIO(b"the content")
        resp.request = prep
        setattr(resp.raw, "release_conn", lambda *args: args)
        resp.status_code = 302
        resp.headers["location"] = httpbin("get")
        next_resp = next(ses.resolve_redirects(resp, prep))
        assert next_resp.request.body is None
        for header in purged_headers:
            assert header not in next_resp.request.headers

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

def test_manual_redirect_with_partial_body_read(self, httpbin):
        s = requests.Session()
        r1 = s.get(httpbin("redirect/2"), allow_redirects=False, stream=True)
        assert r1.is_redirect
        rg = s.resolve_redirects(r1, r1.request, stream=True)
        r1.iter_content(8)
        r2 = next(rg)
        assert r2.is_redirect
        for _ in r2.iter_content():
            pass
        r3 = next(rg)
        assert not r3.is_redirect