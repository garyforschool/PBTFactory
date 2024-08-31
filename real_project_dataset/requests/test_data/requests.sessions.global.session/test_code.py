def test_entry_points(self):
        requests.session
        requests.session().get
        requests.session().head
        requests.get
        requests.head
        requests.put
        requests.patch
        requests.post
        from requests.packages.urllib3.poolmanager import PoolManager

def test_HTTP_302_TOO_MANY_REDIRECTS_WITH_PARAMS(self, httpbin):
        s = requests.session()
        s.max_redirects = 5
        try:
            s.get(httpbin("relative-redirect", "50"))
        except TooManyRedirects as e:
            url = httpbin("relative-redirect", "45")
            assert e.request.url == url
            assert e.response.url == url
            assert len(e.response.history) == 5
        else:
            pytest.fail(
                "Expected custom max number of redirects to be respected but was not"
            )

def test_set_cookie_on_301(self, httpbin):
        s = requests.session()
        url = httpbin("cookies/set?foo=bar")
        s.get(url)
        assert s.cookies["foo"] == "bar"

def test_cookie_sent_on_redirect(self, httpbin):
        s = requests.session()
        s.get(httpbin("cookies/set?foo=bar"))
        r = s.get(httpbin("redirect/1"))
        assert "Cookie" in r.json()["headers"]

def test_cookie_removed_on_expire(self, httpbin):
        s = requests.session()
        s.get(httpbin("cookies/set?foo=bar"))
        assert s.cookies["foo"] == "bar"
        s.get(
            httpbin("response-headers"),
            params={"Set-Cookie": "foo=deleted; expires=Thu, 01-Jan-1970 00:00:01 GMT"},
        )
        assert "foo" not in s.cookies

def test_cookie_quote_wrapped(self, httpbin):
        s = requests.session()
        s.get(httpbin('cookies/set?foo="bar:baz"'))
        assert s.cookies["foo"] == '"bar:baz"'

def test_cookie_persists_via_api(self, httpbin):
        s = requests.session()
        r = s.get(httpbin("redirect/1"), cookies={"foo": "bar"})
        assert "foo" in r.request.headers["Cookie"]
        assert "foo" in r.history[0].request.headers["Cookie"]

def test_request_cookie_overrides_session_cookie(self, httpbin):
        s = requests.session()
        s.cookies["foo"] = "bar"
        r = s.get(httpbin("cookies"), cookies={"foo": "baz"})
        assert r.json()["cookies"]["foo"] == "baz"
        assert s.cookies["foo"] == "bar"

def test_request_cookies_not_persisted(self, httpbin):
        s = requests.session()
        s.get(httpbin("cookies"), cookies={"foo": "baz"})
        assert not s.cookies

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

def test_BASICAUTH_TUPLE_HTTP_200_OK_GET(self, httpbin):
        auth = "user", "pass"
        url = httpbin("basic-auth", "user", "pass")
        r = requests.get(url, auth=auth)
        assert r.status_code == 200
        r = requests.get(url)
        assert r.status_code == 401
        s = requests.session()
        s.auth = auth
        r = s.get(url)
        assert r.status_code == 200

def test_basicauth_with_netrc(self, httpbin):
        auth = "user", "pass"
        wrong_auth = "wronguser", "wrongpass"
        url = httpbin("basic-auth", "user", "pass")
        old_auth = requests.sessions.get_netrc_auth
        try:

            def get_netrc_auth_mock(url):
                return auth

            requests.sessions.get_netrc_auth = get_netrc_auth_mock
            r = requests.get(url)
            assert r.status_code == 200
            r = requests.get(url, auth=wrong_auth)
            assert r.status_code == 401
            s = requests.session()
            r = s.get(url)
            assert r.status_code == 200
            s.auth = wrong_auth
            r = s.get(url)
            assert r.status_code == 401
        finally:
            requests.sessions.get_netrc_auth = old_auth

def test_DIGEST_HTTP_200_OK_GET(self, httpbin):
        for authtype in self.digest_auth_algo:
            auth = HTTPDigestAuth("user", "pass")
            url = httpbin("digest-auth", "auth", "user", "pass", authtype, "never")
            r = requests.get(url, auth=auth)
            assert r.status_code == 200
            r = requests.get(url)
            assert r.status_code == 401
            print(r.headers["WWW-Authenticate"])
            s = requests.session()
            s.auth = HTTPDigestAuth("user", "pass")
            r = s.get(url)
            assert r.status_code == 200

def test_DIGESTAUTH_WRONG_HTTP_401_GET(self, httpbin):
        for authtype in self.digest_auth_algo:
            auth = HTTPDigestAuth("user", "wrongpass")
            url = httpbin("digest-auth", "auth", "user", "pass", authtype)
            r = requests.get(url, auth=auth)
            assert r.status_code == 401
            r = requests.get(url)
            assert r.status_code == 401
            s = requests.session()
            s.auth = auth
            r = s.get(url)
            assert r.status_code == 401

def test_unconsumed_session_response_closes_connection(self, httpbin):
        s = requests.session()
        with contextlib.closing(s.get(httpbin("stream/4"), stream=True)) as response:
            pass
        assert response._content_consumed is False
        assert response.raw.closed