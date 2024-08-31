def test_request_url_trims_leading_path_separators():
    a = requests.adapters.HTTPAdapter()
    p = requests.Request(method="GET", url="http://127.0.0.1:10000//v:h").prepare()
    assert "/v:h" == a.request_url(p, {})

def test_basic_building(self):
        req = requests.Request()
        req.url = "http://kennethreitz.org/"
        req.data = {"life": "42"}
        pr = req.prepare()
        assert pr.url == req.url
        assert pr.body == "life=42"

@pytest.mark.parametrize("method", ("GET", "HEAD"))
    def test_no_content_length(self, httpbin, method):
        req = requests.Request(method, httpbin(method.lower())).prepare()
        assert "Content-Length" not in req.headers

@pytest.mark.parametrize("method", ("POST", "PUT", "PATCH", "OPTIONS"))
    def test_no_body_content_length(self, httpbin, method):
        req = requests.Request(method, httpbin(method.lower())).prepare()
        assert req.headers["Content-Length"] == "0"

@pytest.mark.parametrize("method", ("POST", "PUT", "PATCH", "OPTIONS"))
    def test_empty_content_length(self, httpbin, method):
        req = requests.Request(method, httpbin(method.lower()), data="").prepare()
        assert req.headers["Content-Length"] == "0"

def test_override_content_length(self, httpbin):
        headers = {"Content-Length": "not zero"}
        r = requests.Request("POST", httpbin("post"), headers=headers).prepare()
        assert "Content-Length" in r.headers
        assert r.headers["Content-Length"] == "not zero"

def test_path_is_not_double_encoded(self):
        request = requests.Request("GET", "http://0.0.0.0/get/test case").prepare()
        assert request.path_url == "/get/test%20case"

@pytest.mark.parametrize(
        "url, expected",
        (
            (
                "http://example.com/path#fragment",
                "http://example.com/path?a=b#fragment",
            ),
            (
                "http://example.com/path?key=value#fragment",
                "http://example.com/path?key=value&a=b#fragment",
            ),
        ),
    )
    def test_params_are_added_before_fragment(self, url, expected):
        request = requests.Request("GET", url, params={"a": "b"}).prepare()
        assert request.url == expected

def test_params_bytes_are_encoded(self):
        request = requests.Request(
            "GET", "http://example.com", params=b"test=foo"
        ).prepare()
        assert request.url == "http://example.com/?test=foo"

def test_binary_put(self):
        request = requests.Request(
            "PUT", "http://example.com", data="ööö".encode()
        ).prepare()
        assert isinstance(request.body, bytes)

def test_whitespaces_are_removed_from_url(self):
        request = requests.Request("GET", " http://example.com").prepare()
        assert request.url == "http://example.com/"

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

@pytest.mark.parametrize(
        "username, password",
        (("user", "pass"), ("имя".encode(), "пароль".encode()), (42, 42), (None, None)),
    )
    def test_set_basicauth(self, httpbin, username, password):
        auth = username, password
        url = httpbin("get")
        r = requests.Request("GET", url, auth=auth)
        p = r.prepare()
        assert p.headers["Authorization"] == _basic_auth_str(username, password)

def test_basicauth_encodes_byte_strings(self):
        auth = b"\xc5\xafsername", b"test\xc6\xb6"
        r = requests.Request("GET", "http://localhost", auth=auth)
        p = r.prepare()
        assert p.headers["Authorization"] == "Basic xa9zZXJuYW1lOnRlc3TGtg=="

def test_respect_proxy_env_on_send_self_prepared_request(self, httpbin):
        with override_environ(http_proxy=INVALID_PROXY):
            with pytest.raises(ProxyError):
                session = requests.Session()
                request = requests.Request("GET", httpbin())
                session.send(request.prepare())

def test_respect_proxy_env_on_send_with_redirects(self, httpbin):
        with override_environ(http_proxy=INVALID_PROXY):
            with pytest.raises(ProxyError):
                session = requests.Session()
                url = httpbin("redirect/1")
                print(url)
                request = requests.Request("GET", url)
                session.send(request.prepare())

@pytest.mark.parametrize(
        "url,has_proxy_auth",
        (("http://example.com", True), ("https://example.com", False)),
    )
    def test_proxy_authorization_not_appended_to_https_request(
        self, url, has_proxy_auth
    ):
        session = requests.Session()
        proxies = {
            "http": "http://test:pass@localhost:8080",
            "https": "http://test:pass@localhost:8090",
        }
        req = requests.Request("GET", url)
        prep = req.prepare()
        session.rebuild_proxies(prep, proxies)
        assert ("Proxy-Authorization" in prep.headers) is has_proxy_auth

def test_form_encoded_post_query_multivalued_element(self, httpbin):
        r = requests.Request(
            method="POST", url=httpbin("post"), data=dict(test=["foo", "baz"])
        )
        prep = r.prepare()
        assert prep.body == "test=foo&test=baz"

def test_unicode_multipart_post_fieldnames(self, httpbin):
        filename = os.path.splitext(__file__)[0] + ".py"
        with open(filename, "rb") as f:
            r = requests.Request(
                method="POST",
                url=httpbin("post"),
                data={b"stuff": "elixr"},
                files={"file": ("test_requests.py", f)},
            )
            prep = r.prepare()
        assert b'name="stuff"' in prep.body
        assert b"name=\"b'stuff'\"" not in prep.body

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

def test_session_pickling(self, httpbin):
        r = requests.Request("GET", httpbin("get"))
        s = requests.Session()
        s = pickle.loads(pickle.dumps(s))
        s.proxies = getproxies()
        r = s.send(r.prepare())
        assert r.status_code == 200

def test_long_authinfo_in_url(self):
        url = "http://{}:{}@{}:9000/path?query#frag".format(
            "E8A3BE87-9E3F-4620-8858-95478E385B5B",
            "EA770032-DA4D-4D84-8CE9-29C6D910BF1E",
            "exactly-------------sixty-----------three------------characters",
        )
        r = requests.Request("GET", url).prepare()
        assert r.url == url

def test_header_keys_are_native(self, httpbin):
        headers = {"unicode": "blah", b"byte": "blah"}
        r = requests.Request("GET", httpbin("get"), headers=headers)
        p = r.prepare()
        assert "unicode" in p.headers.keys()
        assert "byte" in p.headers.keys()

@pytest.mark.parametrize("files", ("foo", b"foo", bytearray(b"foo")))
    def test_can_send_objects_with_files(self, httpbin, files):
        data = {"a": "this is a string"}
        files = {"b": files}
        r = requests.Request("POST", httpbin("post"), data=data, files=files)
        p = r.prepare()
        assert "multipart/form-data" in p.headers["Content-Type"]

def test_can_send_file_object_with_non_string_filename(self, httpbin):
        f = io.BytesIO()
        f.name = 2
        r = requests.Request("POST", httpbin("post"), files={"f": f})
        p = r.prepare()
        assert "multipart/form-data" in p.headers["Content-Type"]

def test_autoset_header_values_are_native(self, httpbin):
        data = "this is a string"
        length = "16"
        req = requests.Request("POST", httpbin("post"), data=data)
        p = req.prepare()
        assert p.headers["Content-Length"] == length

def test_content_length_for_bytes_data(self, httpbin):
        data = "This is a string containing multi-byte UTF-8 ☃️"
        encoded_data = data.encode("utf-8")
        length = str(len(encoded_data))
        req = requests.Request("POST", httpbin("post"), data=encoded_data)
        p = req.prepare()
        assert p.headers["Content-Length"] == length

def test_content_length_for_string_data_counts_bytes(self, httpbin):
        data = "This is a string containing multi-byte UTF-8 ☃️"
        length = str(len(data.encode("utf-8")))
        req = requests.Request("POST", httpbin("post"), data=data)
        p = req.prepare()
        assert p.headers["Content-Length"] == length

def test_nonhttp_schemes_dont_check_URLs(self):
        test_urls = (
            "data:image/gif;base64,R0lGODlhAQABAHAAACH5BAUAAAAALAAAAAABAAEAAAICRAEAOw==",
            "file:///etc/passwd",
            "magnet:?xt=urn:btih:be08f00302bc2d1d3cfa3af02024fa647a271431",
        )
        for test_url in test_urls:
            req = requests.Request("GET", test_url)
            preq = req.prepare()
            assert test_url == preq.url

def test_prepare_body_position_non_stream(self):
        data = b"the data"
        prep = requests.Request("GET", "http://example.com", data=data).prepare()
        assert prep._body_position is None

def test_rewind_body(self):
        data = io.BytesIO(b"the data")
        prep = requests.Request("GET", "http://example.com", data=data).prepare()
        assert prep._body_position == 0
        assert prep.body.read() == b"the data"
        assert prep.body.read() == b""
        requests.utils.rewind_body(prep)
        assert prep.body.read() == b"the data"

def test_rewind_partially_read_body(self):
        data = io.BytesIO(b"the data")
        data.read(4)
        prep = requests.Request("GET", "http://example.com", data=data).prepare()
        assert prep._body_position == 4
        assert prep.body.read() == b"data"
        assert prep.body.read() == b""
        requests.utils.rewind_body(prep)
        assert prep.body.read() == b"data"

def test_rewind_body_no_seek(self):

        class BadFileObj:

            def __init__(self, data):
                self.data = data

            def tell(self):
                return 0

            def __iter__(self):
                return

        data = BadFileObj("the data")
        prep = requests.Request("GET", "http://example.com", data=data).prepare()
        assert prep._body_position == 0
        with pytest.raises(UnrewindableBodyError) as e:
            requests.utils.rewind_body(prep)
        assert "Unable to rewind request body" in str(e)

def test_rewind_body_failed_seek(self):

        class BadFileObj:

            def __init__(self, data):
                self.data = data

            def tell(self):
                return 0

            def seek(self, pos, whence=0):
                raise OSError()

            def __iter__(self):
                return

        data = BadFileObj("the data")
        prep = requests.Request("GET", "http://example.com", data=data).prepare()
        assert prep._body_position == 0
        with pytest.raises(UnrewindableBodyError) as e:
            requests.utils.rewind_body(prep)
        assert "error occurred when rewinding request body" in str(e)

def test_rewind_body_failed_tell(self):

        class BadFileObj:

            def __init__(self, data):
                self.data = data

            def tell(self):
                raise OSError()

            def __iter__(self):
                return

        data = BadFileObj("the data")
        prep = requests.Request("GET", "http://example.com", data=data).prepare()
        assert prep._body_position is not None
        with pytest.raises(UnrewindableBodyError) as e:
            requests.utils.rewind_body(prep)
        assert "Unable to rewind request body" in str(e)

def test_json_param_post_should_not_override_data_param(self, httpbin):
        r = requests.Request(
            method="POST",
            url=httpbin("post"),
            data={"stuff": "elixr"},
            json={"music": "flute"},
        )
        prep = r.prepare()
        assert "stuff=elixr" == prep.body

def test_empty_stream_with_auth_does_not_set_content_length_header(self, httpbin):
        auth = "user", "pass"
        url = httpbin("post")
        file_obj = io.BytesIO(b"")
        r = requests.Request("POST", url, auth=auth, data=file_obj)
        prepared_request = r.prepare()
        assert "Transfer-Encoding" in prepared_request.headers
        assert "Content-Length" not in prepared_request.headers

def test_stream_with_auth_does_not_set_transfer_encoding_header(self, httpbin):
        auth = "user", "pass"
        url = httpbin("post")
        file_obj = io.BytesIO(b"test data")
        r = requests.Request("POST", url, auth=auth, data=file_obj)
        prepared_request = r.prepare()
        assert "Transfer-Encoding" not in prepared_request.headers
        assert "Content-Length" in prepared_request.headers

def test_chunked_upload_does_not_set_content_length_header(self, httpbin):
        data = (i for i in [b"a", b"b", b"c"])
        url = httpbin("post")
        r = requests.Request("POST", url, data=data)
        prepared_request = r.prepare()
        assert "Transfer-Encoding" in prepared_request.headers
        assert "Content-Length" not in prepared_request.headers

def test_requests_are_updated_each_time(httpbin):
    session = RedirectSession([303, 307])
    prep = requests.Request("POST", httpbin("post")).prepare()
    r0 = session.send(prep)
    assert r0.request.method == "POST"
    assert session.calls[-1] == SendCall((r0.request,), {})
    redirect_generator = session.resolve_redirects(r0, prep)
    default_keyword_args = {
        "stream": False,
        "verify": True,
        "cert": None,
        "timeout": None,
        "allow_redirects": False,
        "proxies": {},
    }
    for response in redirect_generator:
        assert response.request.method == "GET"
        send_call = SendCall((response.request,), default_keyword_args)
        assert session.calls[-1] == send_call

@pytest.mark.parametrize(
        "url,expected",
        (
            ("http://google.com", "http://google.com/"),
            ("http://ジェーピーニック.jp", "http://xn--hckqz9bzb1cyrb.jp/"),
            ("http://xn--n3h.net/", "http://xn--n3h.net/"),
            ("http://ジェーピーニック.jp".encode(), "http://xn--hckqz9bzb1cyrb.jp/"),
            ("http://straße.de/straße", "http://xn--strae-oqa.de/stra%C3%9Fe"),
            ("http://straße.de/straße".encode(), "http://xn--strae-oqa.de/stra%C3%9Fe"),
            (
                "http://Königsgäßchen.de/straße",
                "http://xn--knigsgchen-b4a3dun.de/stra%C3%9Fe",
            ),
            (
                "http://Königsgäßchen.de/straße".encode(),
                "http://xn--knigsgchen-b4a3dun.de/stra%C3%9Fe",
            ),
            (b"http://xn--n3h.net/", "http://xn--n3h.net/"),
            (
                b"http://[1200:0000:ab00:1234:0000:2552:7777:1313]:12345/",
                "http://[1200:0000:ab00:1234:0000:2552:7777:1313]:12345/",
            ),
            (
                "http://[1200:0000:ab00:1234:0000:2552:7777:1313]:12345/",
                "http://[1200:0000:ab00:1234:0000:2552:7777:1313]:12345/",
            ),
        ),
    )
    def test_preparing_url(self, url, expected):

        def normalize_percent_encode(x):
            for c in re.findall("%[a-fA-F0-9]{2}", x):
                x = x.replace(c, c.upper())
            return x

        r = requests.Request("GET", url=url)
        p = r.prepare()
        assert normalize_percent_encode(p.url) == expected

@pytest.mark.parametrize(
        "url",
        (
            b"http://*.google.com",
            b"http://*",
            "http://*.google.com",
            "http://*",
            "http://☃.net/",
        ),
    )
    def test_preparing_bad_url(self, url):
        r = requests.Request("GET", url=url)
        with pytest.raises(requests.exceptions.InvalidURL):
            r.prepare()

@pytest.mark.parametrize(
        "input, expected",
        (
            (
                b"http+unix://%2Fvar%2Frun%2Fsocket/path%7E",
                "http+unix://%2Fvar%2Frun%2Fsocket/path~",
            ),
            (
                "http+unix://%2Fvar%2Frun%2Fsocket/path%7E",
                "http+unix://%2Fvar%2Frun%2Fsocket/path~",
            ),
            (b"mailto:user@example.org", "mailto:user@example.org"),
            ("mailto:user@example.org", "mailto:user@example.org"),
            (b"data:SSDimaUgUHl0aG9uIQ==", "data:SSDimaUgUHl0aG9uIQ=="),
        ),
    )
    def test_url_mutation(self, input, expected):
        r = requests.Request("GET", url=input)
        p = r.prepare()
        assert p.url == expected

@pytest.mark.parametrize(
        "input, params, expected",
        (
            (
                b"http+unix://%2Fvar%2Frun%2Fsocket/path",
                {"key": "value"},
                "http+unix://%2Fvar%2Frun%2Fsocket/path?key=value",
            ),
            (
                "http+unix://%2Fvar%2Frun%2Fsocket/path",
                {"key": "value"},
                "http+unix://%2Fvar%2Frun%2Fsocket/path?key=value",
            ),
            (b"mailto:user@example.org", {"key": "value"}, "mailto:user@example.org"),
            ("mailto:user@example.org", {"key": "value"}, "mailto:user@example.org"),
        ),
    )
    def test_parameters_for_nonstandard_schemes(self, input, params, expected):
        r = requests.Request("GET", url=input, params=params)
        p = r.prepare()
        assert p.url == expected