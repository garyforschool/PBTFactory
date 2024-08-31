@pytest.mark.parametrize("scheme", ("http://", "HTTP://", "hTTp://", "HttP://"))
    def test_mixed_case_scheme_acceptable(self, httpbin, scheme):
        s = requests.Session()
        s.proxies = getproxies()
        parts = urlparse(httpbin("get"))
        url = scheme + parts.netloc + parts.path
        r = requests.Request("GET", url)
        r = s.send(r.prepare())
        assert r.status_code == 200, f"failed for scheme {scheme}"

def test_HTTP_200_OK_GET_ALTERNATIVE(self, httpbin):
        r = requests.Request("GET", httpbin("get"))
        s = requests.Session()
        s.proxies = getproxies()
        r = s.send(r.prepare())
        assert r.status_code == 200

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

def test_respect_proxy_env_on_send_self_prepared_request(self, httpbin):
        with override_environ(http_proxy=INVALID_PROXY):
            with pytest.raises(ProxyError):
                session = requests.Session()
                request = requests.Request("GET", httpbin())
                session.send(request.prepare())

def test_respect_proxy_env_on_send_session_prepared_request(self, httpbin):
        with override_environ(http_proxy=INVALID_PROXY):
            with pytest.raises(ProxyError):
                session = requests.Session()
                request = requests.Request("GET", httpbin())
                prepared = session.prepare_request(request)
                session.send(prepared)

def test_respect_proxy_env_on_send_with_redirects(self, httpbin):
        with override_environ(http_proxy=INVALID_PROXY):
            with pytest.raises(ProxyError):
                session = requests.Session()
                url = httpbin("redirect/1")
                print(url)
                request = requests.Request("GET", url)
                session.send(request.prepare())

def test_unicode_method_name_with_request_object(self, httpbin):
        s = requests.Session()
        with open(__file__, "rb") as f:
            files = {"file": f}
            req = requests.Request("POST", httpbin("post"), files=files)
            prep = s.prepare_request(req)
        assert isinstance(prep.method, builtin_str)
        assert prep.method == "POST"
        resp = s.send(prep)
        assert resp.status_code == 200

def test_non_prepared_request_error(self):
        s = requests.Session()
        req = requests.Request("POST", "/")
        with pytest.raises(ValueError) as e:
            s.send(req)
        assert str(e.value) == "You can only send PreparedRequests."

def test_hook_receives_request_arguments(self, httpbin):

        def hook(resp, **kwargs):
            assert resp is not None
            assert kwargs != {}

        s = requests.Session()
        r = requests.Request("GET", httpbin(), hooks={"response": hook})
        prep = s.prepare_request(r)
        s.send(prep)

def test_prepared_request_hook(self, httpbin):

        def hook(resp, **kwargs):
            resp.hook_working = True
            return resp

        req = requests.Request("GET", httpbin(), hooks={"response": hook})
        prep = req.prepare()
        s = requests.Session()
        s.proxies = getproxies()
        resp = s.send(prep)
        assert hasattr(resp, "hook_working")

def test_prepared_from_session(self, httpbin):

        class DummyAuth(requests.auth.AuthBase):

            def __call__(self, r):
                r.headers["Dummy-Auth-Test"] = "dummy-auth-test-ok"
                return r

        req = requests.Request("GET", httpbin("headers"))
        assert not req.auth
        s = requests.Session()
        s.auth = DummyAuth()
        prep = s.prepare_request(req)
        resp = s.send(prep)
        assert resp.json()["headers"]["Dummy-Auth-Test"] == "dummy-auth-test-ok"

def test_prepared_request_is_pickleable(self, httpbin):
        p = requests.Request("GET", httpbin("get")).prepare()
        r = pickle.loads(pickle.dumps(p))
        assert r.url == p.url
        assert r.headers == p.headers
        assert r.body == p.body
        s = requests.Session()
        resp = s.send(r)
        assert resp.status_code == 200

def test_prepared_request_with_file_is_pickleable(self, httpbin):
        with open(__file__, "rb") as f:
            r = requests.Request("POST", httpbin("post"), files={"file": f})
            p = r.prepare()
        r = pickle.loads(pickle.dumps(p))
        assert r.url == p.url
        assert r.headers == p.headers
        assert r.body == p.body
        s = requests.Session()
        resp = s.send(r)
        assert resp.status_code == 200

def test_prepared_request_with_hook_is_pickleable(self, httpbin):
        r = requests.Request("GET", httpbin("get"), hooks=default_hooks())
        p = r.prepare()
        r = pickle.loads(pickle.dumps(p))
        assert r.url == p.url
        assert r.headers == p.headers
        assert r.body == p.body
        assert r.hooks == p.hooks
        s = requests.Session()
        resp = s.send(r)
        assert resp.status_code == 200

def test_cannot_send_unprepared_requests(self, httpbin):
        r = requests.Request(url=httpbin())
        with pytest.raises(ValueError):
            requests.Session().send(r)

def test_session_pickling(self, httpbin):
        r = requests.Request("GET", httpbin("get"))
        s = requests.Session()
        s = pickle.loads(pickle.dumps(s))
        s.proxies = getproxies()
        r = s.send(r.prepare())
        assert r.status_code == 200