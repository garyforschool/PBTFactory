def test_params_original_order_is_preserved_by_default(self):
        param_ordered_dict = collections.OrderedDict(
            (("z", 1), ("a", 1), ("k", 1), ("d", 1))
        )
        session = requests.Session()
        request = requests.Request(
            "GET", "http://example.com/", params=param_ordered_dict
        )
        prep = session.prepare_request(request)
        assert prep.url == "http://example.com/?z=1&a=1&k=1&d=1"

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

def test_headers_on_session_with_None_are_not_sent(self, httpbin):
        ses = requests.Session()
        ses.headers["Accept-Encoding"] = None
        req = requests.Request("GET", httpbin("get"))
        prep = ses.prepare_request(req)
        assert "Accept-Encoding" not in prep.headers

def test_headers_preserve_order(self, httpbin):
        ses = requests.Session()
        ses.headers = collections.OrderedDict()
        ses.headers["Accept-Encoding"] = "identity"
        ses.headers["First"] = "1"
        ses.headers["Second"] = "2"
        headers = collections.OrderedDict([("Third", "3"), ("Fourth", "4")])
        headers["Fifth"] = "5"
        headers["Second"] = "222"
        req = requests.Request("GET", httpbin("get"), headers=headers)
        prep = ses.prepare_request(req)
        items = list(prep.headers.items())
        assert items[0] == ("Accept-Encoding", "identity")
        assert items[1] == ("First", "1")
        assert items[2] == ("Second", "222")
        assert items[3] == ("Third", "3")
        assert items[4] == ("Fourth", "4")
        assert items[5] == ("Fifth", "5")

def test_respect_proxy_env_on_send_session_prepared_request(self, httpbin):
        with override_environ(http_proxy=INVALID_PROXY):
            with pytest.raises(ProxyError):
                session = requests.Session()
                request = requests.Request("GET", httpbin())
                prepared = session.prepare_request(request)
                session.send(prepared)

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

def test_hook_receives_request_arguments(self, httpbin):

        def hook(resp, **kwargs):
            assert resp is not None
            assert kwargs != {}

        s = requests.Session()
        r = requests.Request("GET", httpbin(), hooks={"response": hook})
        prep = s.prepare_request(r)
        s.send(prep)

def test_session_hooks_are_used_with_no_request_hooks(self, httpbin):

        def hook(*args, **kwargs):
            pass

        s = requests.Session()
        s.hooks["response"].append(hook)
        r = requests.Request("GET", httpbin())
        prep = s.prepare_request(r)
        assert prep.hooks["response"] != []
        assert prep.hooks["response"] == [hook]

def test_session_hooks_are_overridden_by_request_hooks(self, httpbin):

        def hook1(*args, **kwargs):
            pass

        def hook2(*args, **kwargs):
            pass

        assert hook1 is not hook2
        s = requests.Session()
        s.hooks["response"].append(hook2)
        r = requests.Request("GET", httpbin(), hooks={"response": [hook1]})
        prep = s.prepare_request(r)
        assert prep.hooks["response"] == [hook1]

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

def test_prepare_request_with_bytestring_url(self):
        req = requests.Request("GET", b"https://httpbin.org/")
        s = requests.Session()
        prep = s.prepare_request(req)
        assert prep.url == "https://httpbin.org/"