def test_chunked_encoding_error():

    def incomplete_chunked_response_handler(sock):
        request_content = consume_socket_content(sock, timeout=0.5)
        sock.send(b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n")
        return request_content

    close_server = threading.Event()
    server = Server(incomplete_chunked_response_handler)
    with server as (host, port):
        url = f"http://{host}:{port}/"
        with pytest.raises(requests.exceptions.ChunkedEncodingError):
            requests.get(url)
        close_server.set()

def test_conflicting_content_lengths():

    def multiple_content_length_response_handler(sock):
        request_content = consume_socket_content(sock, timeout=0.5)
        response = b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 16\r\nContent-Length: 32\r\n\r\n-- Bad Actor -- Original Content\r\n"
        sock.send(response)
        return request_content

    close_server = threading.Event()
    server = Server(multiple_content_length_response_handler)
    with server as (host, port):
        url = f"http://{host}:{port}/"
        with pytest.raises(requests.exceptions.InvalidHeader):
            requests.get(url)
        close_server.set()

def test_digestauth_401_count_reset_on_redirect():
    text_401 = b'HTTP/1.1 401 UNAUTHORIZED\r\nContent-Length: 0\r\nWWW-Authenticate: Digest nonce="6bf5d6e4da1ce66918800195d6b9130d", opaque="372825293d1c26955496c80ed6426e9e", realm="me@kennethreitz.com", qop=auth\r\n\r\n'
    text_302 = b"HTTP/1.1 302 FOUND\r\nContent-Length: 0\r\nLocation: /\r\n\r\n"
    text_200 = b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n"
    expected_digest = b'Authorization: Digest username="user", realm="me@kennethreitz.com", nonce="6bf5d6e4da1ce66918800195d6b9130d", uri="/"'
    auth = requests.auth.HTTPDigestAuth("user", "pass")

    def digest_response_handler(sock):
        request_content = consume_socket_content(sock, timeout=0.5)
        assert request_content.startswith(b"GET / HTTP/1.1")
        sock.send(text_401)
        request_content = consume_socket_content(sock, timeout=0.5)
        assert expected_digest in request_content
        sock.send(text_302)
        request_content = consume_socket_content(sock, timeout=0.5)
        assert b"Authorization:" not in request_content
        sock.send(text_401)
        request_content = consume_socket_content(sock, timeout=0.5)
        assert expected_digest in request_content
        sock.send(text_200)
        return request_content

    close_server = threading.Event()
    server = Server(digest_response_handler, wait_to_close_event=close_server)
    with server as (host, port):
        url = f"http://{host}:{port}/"
        r = requests.get(url, auth=auth)
        assert r.status_code == 200
        assert "Authorization" in r.request.headers
        assert r.request.headers["Authorization"].startswith("Digest ")
        assert r.history[0].status_code == 302
        close_server.set()

def test_digestauth_401_only_sent_once():
    text_401 = b'HTTP/1.1 401 UNAUTHORIZED\r\nContent-Length: 0\r\nWWW-Authenticate: Digest nonce="6bf5d6e4da1ce66918800195d6b9130d", opaque="372825293d1c26955496c80ed6426e9e", realm="me@kennethreitz.com", qop=auth\r\n\r\n'
    expected_digest = b'Authorization: Digest username="user", realm="me@kennethreitz.com", nonce="6bf5d6e4da1ce66918800195d6b9130d", uri="/"'
    auth = requests.auth.HTTPDigestAuth("user", "pass")

    def digest_failed_response_handler(sock):
        request_content = consume_socket_content(sock, timeout=0.5)
        assert request_content.startswith(b"GET / HTTP/1.1")
        sock.send(text_401)
        request_content = consume_socket_content(sock, timeout=0.5)
        assert expected_digest in request_content
        sock.send(text_401)
        request_content = consume_socket_content(sock, timeout=0.5)
        assert request_content == b""
        return request_content

    close_server = threading.Event()
    server = Server(digest_failed_response_handler, wait_to_close_event=close_server)
    with server as (host, port):
        url = f"http://{host}:{port}/"
        r = requests.get(url, auth=auth)
        assert r.status_code == 401
        assert r.history[0].status_code == 401
        close_server.set()

def test_digestauth_only_on_4xx():
    text_200_chal = b'HTTP/1.1 200 OK\r\nContent-Length: 0\r\nWWW-Authenticate: Digest nonce="6bf5d6e4da1ce66918800195d6b9130d", opaque="372825293d1c26955496c80ed6426e9e", realm="me@kennethreitz.com", qop=auth\r\n\r\n'
    auth = requests.auth.HTTPDigestAuth("user", "pass")

    def digest_response_handler(sock):
        request_content = consume_socket_content(sock, timeout=0.5)
        assert request_content.startswith(b"GET / HTTP/1.1")
        sock.send(text_200_chal)
        request_content = consume_socket_content(sock, timeout=0.5)
        assert request_content == b""
        return request_content

    close_server = threading.Event()
    server = Server(digest_response_handler, wait_to_close_event=close_server)
    with server as (host, port):
        url = f"http://{host}:{port}/"
        r = requests.get(url, auth=auth)
        assert r.status_code == 200
        assert len(r.history) == 0
        close_server.set()

@pytest.mark.parametrize("var,scheme", _proxy_combos)
def test_use_proxy_from_environment(httpbin, var, scheme):
    url = f"{scheme}://httpbin.org"
    fake_proxy = Server()
    with fake_proxy as (host, port):
        proxy_url = f"socks5://{host}:{port}"
        kwargs = {var: proxy_url}
        with override_environ(**kwargs):
            with pytest.raises(requests.exceptions.ConnectionError):
                requests.get(url)
        assert len(fake_proxy.handler_results) == 1
        assert len(fake_proxy.handler_results[0]) > 0

def test_redirect_rfc1808_to_non_ascii_location():
    path = "š"
    expected_path = b"%C5%A1"
    redirect_request = []

    def redirect_resp_handler(sock):
        consume_socket_content(sock, timeout=0.5)
        location = f"//{host}:{port}/{path}"
        sock.send(
            b"HTTP/1.1 301 Moved Permanently\r\nContent-Length: 0\r\nLocation: %s\r\n\r\n"
            % location.encode("utf8")
        )
        redirect_request.append(consume_socket_content(sock, timeout=0.5))
        sock.send(b"HTTP/1.1 200 OK\r\n\r\n")

    close_server = threading.Event()
    server = Server(redirect_resp_handler, wait_to_close_event=close_server)
    with server as (host, port):
        url = f"http://{host}:{port}"
        r = requests.get(url=url, allow_redirects=True)
        assert r.status_code == 200
        assert len(r.history) == 1
        assert r.history[0].status_code == 301
        assert redirect_request[0].startswith(b"GET /" + expected_path + b" HTTP/1.1")
        assert r.url == "{}/{}".format(url, expected_path.decode("ascii"))
        close_server.set()

def test_fragment_not_sent_with_request():
    close_server = threading.Event()
    server = Server(echo_response_handler, wait_to_close_event=close_server)
    with server as (host, port):
        url = f"http://{host}:{port}/path/to/thing/#view=edit&token=hunter2"
        r = requests.get(url)
        raw_request = r.content
        assert r.status_code == 200
        headers, body = raw_request.split(b"\r\n\r\n", 1)
        status_line, headers = headers.split(b"\r\n", 1)
        assert status_line == b"GET /path/to/thing/ HTTP/1.1"
        for frag in (b"view", b"edit", b"token", b"hunter2"):
            assert frag not in headers
            assert frag not in body
        close_server.set()

def test_fragment_update_on_redirect():

    def response_handler(sock):
        consume_socket_content(sock, timeout=0.5)
        sock.send(
            b"HTTP/1.1 302 FOUND\r\nContent-Length: 0\r\nLocation: /get#relevant-section\r\n\r\n"
        )
        consume_socket_content(sock, timeout=0.5)
        sock.send(
            b"HTTP/1.1 302 FOUND\r\nContent-Length: 0\r\nLocation: /final-url/\r\n\r\n"
        )
        consume_socket_content(sock, timeout=0.5)
        sock.send(b"HTTP/1.1 200 OK\r\n\r\n")

    close_server = threading.Event()
    server = Server(response_handler, wait_to_close_event=close_server)
    with server as (host, port):
        url = f"http://{host}:{port}/path/to/thing/#view=edit&token=hunter2"
        r = requests.get(url)
        assert r.status_code == 200
        assert len(r.history) == 2
        assert r.history[0].request.url == url
        assert r.history[1].request.url == f"http://{host}:{port}/get#relevant-section"
        assert r.url == f"http://{host}:{port}/final-url/#relevant-section"
        close_server.set()

def test_json_decode_compatibility_for_alt_utf_encodings():

    def response_handler(sock):
        consume_socket_content(sock, timeout=0.5)
        sock.send(
            b'HTTP/1.1 200 OK\r\nContent-Length: 18\r\n\r\n\xff\xfe{\x00"\x00K0"\x00=\x00"\x00\xab0"\x00\r\n'
        )

    close_server = threading.Event()
    server = Server(response_handler, wait_to_close_event=close_server)
    with server as (host, port):
        url = f"http://{host}:{port}/"
        r = requests.get(url)
    r.encoding = None
    with pytest.raises(requests.exceptions.JSONDecodeError) as excinfo:
        r.json()
    assert isinstance(excinfo.value, requests.exceptions.RequestException)
    assert isinstance(excinfo.value, JSONDecodeError)
    assert r.text not in str(excinfo.value)

@pytest.mark.parametrize(
        "exception, url",
        (
            (MissingSchema, "hiwpefhipowhefopw"),
            (InvalidSchema, "localhost:3128"),
            (InvalidSchema, "localhost.localdomain:3128/"),
            (InvalidSchema, "10.122.1.1:3128/"),
            (InvalidURL, "http://"),
            (InvalidURL, "http://*example.com"),
            (InvalidURL, "http://.example.com"),
        ),
    )
    def test_invalid_url(self, exception, url):
        with pytest.raises(exception):
            requests.get(url)

def test_HTTP_302_ALLOW_REDIRECT_GET(self, httpbin):
        r = requests.get(httpbin("redirect", "1"))
        assert r.status_code == 200
        assert r.history[0].status_code == 302
        assert r.history[0].is_redirect

def test_HTTP_302_TOO_MANY_REDIRECTS(self, httpbin):
        try:
            requests.get(httpbin("relative-redirect", "50"))
        except TooManyRedirects as e:
            url = httpbin("relative-redirect", "20")
            assert e.request.url == url
            assert e.response.url == url
            assert len(e.response.history) == 30
        else:
            pytest.fail("Expected redirect to raise TooManyRedirects but it did not")

def test_fragment_maintained_on_redirect(self, httpbin):
        fragment = "#view=edit&token=hunter2"
        r = requests.get(httpbin("redirect-to?url=get") + fragment)
        assert len(r.history) > 0
        assert r.history[0].request.url == httpbin("redirect-to?url=get") + fragment
        assert r.url == httpbin("get") + fragment

def test_HTTP_200_OK_GET_WITH_PARAMS(self, httpbin):
        heads = {"User-agent": "Mozilla/5.0"}
        r = requests.get(httpbin("user-agent"), headers=heads)
        assert heads["User-agent"] in r.text
        assert r.status_code == 200

def test_HTTP_200_OK_GET_WITH_MIXED_PARAMS(self, httpbin):
        heads = {"User-agent": "Mozilla/5.0"}
        r = requests.get(
            httpbin("get") + "?test=true", params={"q": "test"}, headers=heads
        )
        assert r.status_code == 200

def test_requests_in_history_are_not_overridden(self, httpbin):
        resp = requests.get(httpbin("redirect/3"))
        urls = [r.url for r in resp.history]
        req_urls = [r.request.url for r in resp.history]
        assert urls == req_urls

def test_history_is_always_a_list(self, httpbin):
        resp = requests.get(httpbin("get"))
        assert isinstance(resp.history, list)
        resp = requests.get(httpbin("redirect/1"))
        assert isinstance(resp.history, list)
        assert not isinstance(resp.history, tuple)

@pytest.mark.parametrize("key", ("User-agent", "user-agent"))
    def test_user_agent_transfers(self, httpbin, key):
        heads = {key: "Mozilla/5.0 (github.com/psf/requests)"}
        r = requests.get(httpbin("user-agent"), headers=heads)
        assert heads[key] in r.text

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

@pytest.mark.parametrize(
        "url, exception",
        (
            ("http://doesnotexist.google.com", ConnectionError),
            ("http://localhost:1", ConnectionError),
            ("http://fe80::5054:ff:fe5a:fc0", InvalidURL),
        ),
    )
    def test_errors(self, url, exception):
        with pytest.raises(exception):
            requests.get(url, timeout=1)

def test_proxy_error(self):
        with pytest.raises(ProxyError):
            requests.get(
                "http://localhost:1", proxies={"http": "non-resolvable-address"}
            )

def test_proxy_error_on_bad_url(self, httpbin, httpbin_secure):
        with pytest.raises(InvalidProxyURL):
            requests.get(httpbin_secure(), proxies={"https": "http:/badproxyurl:3128"})
        with pytest.raises(InvalidProxyURL):
            requests.get(httpbin(), proxies={"http": "http://:8080"})
        with pytest.raises(InvalidProxyURL):
            requests.get(httpbin_secure(), proxies={"https": "https://"})
        with pytest.raises(InvalidProxyURL):
            requests.get(httpbin(), proxies={"http": "http:///example.com:8080"})

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

def test_DIGEST_AUTH_RETURNS_COOKIE(self, httpbin):
        for authtype in self.digest_auth_algo:
            url = httpbin("digest-auth", "auth", "user", "pass", authtype)
            auth = HTTPDigestAuth("user", "pass")
            r = requests.get(url)
            assert r.cookies["fake"] == "fake_value"
            r = requests.get(url, auth=auth)
            assert r.status_code == 200

def test_DIGEST_STREAM(self, httpbin):
        for authtype in self.digest_auth_algo:
            auth = HTTPDigestAuth("user", "pass")
            url = httpbin("digest-auth", "auth", "user", "pass", authtype)
            r = requests.get(url, auth=auth, stream=True)
            assert r.raw.read() != b""
            r = requests.get(url, auth=auth, stream=False)
            assert r.raw.read() == b""

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

def test_DIGESTAUTH_QUOTES_QOP_VALUE(self, httpbin):
        for authtype in self.digest_auth_algo:
            auth = HTTPDigestAuth("user", "pass")
            url = httpbin("digest-auth", "auth", "user", "pass", authtype)
            r = requests.get(url, auth=auth)
            assert '"auth"' in r.request.headers["Authorization"]

def test_request_ok_set(self, httpbin):
        r = requests.get(httpbin("status", "404"))
        assert not r.ok

def test_status_raising(self, httpbin):
        r = requests.get(httpbin("status", "404"))
        with pytest.raises(requests.exceptions.HTTPError):
            r.raise_for_status()
        r = requests.get(httpbin("status", "500"))
        assert not r.ok

def test_decompress_gzip(self, httpbin):
        r = requests.get(httpbin("gzip"))
        r.content.decode("ascii")

@pytest.mark.parametrize(
        "url, params",
        (
            ("/get", {"foo": "føø"}),
            ("/get", {"føø": "føø"}),
            ("/get", {"føø": "føø"}),
            ("/get", {"foo": "foo"}),
            ("ø", {"foo": "foo"}),
        ),
    )
    def test_unicode_get(self, httpbin, url, params):
        requests.get(httpbin(url), params=params)

def test_pyopenssl_redirect(self, httpbin_secure, httpbin_ca_bundle):
        requests.get(httpbin_secure("status", "301"), verify=httpbin_ca_bundle)

def test_invalid_ca_certificate_path(self, httpbin_secure):
        INVALID_PATH = "/garbage"
        with pytest.raises(IOError) as e:
            requests.get(httpbin_secure(), verify=INVALID_PATH)
        assert str(
            e.value
        ) == "Could not find a suitable TLS CA certificate bundle, invalid path: {}".format(
            INVALID_PATH
        )

def test_invalid_ssl_certificate_files(self, httpbin_secure):
        INVALID_PATH = "/garbage"
        with pytest.raises(IOError) as e:
            requests.get(httpbin_secure(), cert=INVALID_PATH)
        assert str(
            e.value
        ) == "Could not find the TLS certificate file, invalid path: {}".format(
            INVALID_PATH
        )
        with pytest.raises(IOError) as e:
            requests.get(httpbin_secure(), cert=(".", INVALID_PATH))
        assert (
            str(e.value)
            == f"Could not find the TLS key file, invalid path: {INVALID_PATH}"
        )

def test_http_with_certificate(self, httpbin):
        r = requests.get(httpbin(), cert=".")
        assert r.status_code == 200

@pytest.mark.skipif(
        SNIMissingWarning is None,
        reason="urllib3 2.0 removed that warning and errors out instead",
    )
    def test_https_warnings(self, nosan_server):
        host, port, ca_bundle = nosan_server
        if HAS_MODERN_SSL or HAS_PYOPENSSL:
            warnings_expected = ("SubjectAltNameWarning",)
        else:
            warnings_expected = (
                "SNIMissingWarning",
                "InsecurePlatformWarning",
                "SubjectAltNameWarning",
            )
        with pytest.warns() as warning_records:
            warnings.simplefilter("always")
            requests.get(f"https://localhost:{port}/", verify=ca_bundle)
        warning_records = [
            item
            for item in warning_records
            if item.category.__name__ != "ResourceWarning"
        ]
        warnings_category = tuple(item.category.__name__ for item in warning_records)
        assert warnings_category == warnings_expected

def test_certificate_failure(self, httpbin_secure):
        with pytest.raises(RequestsSSLError):
            requests.get(httpbin_secure("status", "200"))

def test_urlencoded_get_query_multivalued_param(self, httpbin):
        r = requests.get(httpbin("get"), params={"test": ["foo", "baz"]})
        assert r.status_code == 200
        assert r.url == httpbin("get?test=foo&test=baz")

def test_time_elapsed_blank(self, httpbin):
        r = requests.get(httpbin("get"))
        td = r.elapsed
        total_seconds = (
            td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6
        ) / 10**6
        assert total_seconds > 0.0

def test_request_and_response_are_pickleable(self, httpbin):
        r = requests.get(httpbin("get"))
        assert pickle.loads(pickle.dumps(r.request))
        pr = pickle.loads(pickle.dumps(r))
        assert r.request.url == pr.request.url
        assert r.request.headers == pr.request.headers

def test_uppercase_scheme_redirect(self, httpbin):
        parts = urlparse(httpbin("html"))
        url = "HTTP://" + parts.netloc + parts.path
        r = requests.get(httpbin("redirect-to"), params={"url": url})
        assert r.status_code == 200
        assert r.url.lower() == url.lower()

def test_header_validation(self, httpbin):
        valid_headers = {"foo": "bar baz qux", "bar": b"fbbq", "baz": "", "qux": "1"}
        r = requests.get(httpbin("get"), headers=valid_headers)
        for key in valid_headers.keys():
            assert valid_headers[key] == r.request.headers[key]

@pytest.mark.parametrize(
        "invalid_header, key",
        (
            ({"foo": 3}, "foo"),
            ({"bar": {"foo": "bar"}}, "bar"),
            ({"baz": ["foo", "bar"]}, "baz"),
        ),
    )
    def test_header_value_not_str(self, httpbin, invalid_header, key):
        with pytest.raises(InvalidHeader) as excinfo:
            requests.get(httpbin("get"), headers=invalid_header)
        assert key in str(excinfo.value)

@pytest.mark.parametrize(
        "invalid_header",
        (
            {"foo": "bar\r\nbaz: qux"},
            {"foo": "bar\n\rbaz: qux"},
            {"foo": "bar\nbaz: qux"},
            {"foo": "bar\rbaz: qux"},
            {"fo\ro": "bar"},
            {"fo\r\no": "bar"},
            {"fo\n\ro": "bar"},
            {"fo\no": "bar"},
        ),
    )
    def test_header_no_return_chars(self, httpbin, invalid_header):
        with pytest.raises(InvalidHeader):
            requests.get(httpbin("get"), headers=invalid_header)

@pytest.mark.parametrize(
        "invalid_header",
        (
            {" foo": "bar"},
            {"\tfoo": "bar"},
            {"    foo": "bar"},
            {"foo": " bar"},
            {"foo": "    bar"},
            {"foo": "\tbar"},
            {" ": "bar"},
        ),
    )
    def test_header_no_leading_space(self, httpbin, invalid_header):
        with pytest.raises(InvalidHeader):
            requests.get(httpbin("get"), headers=invalid_header)

def test_header_with_subclass_types(self, httpbin):

        class MyString(str):
            pass

        class MyBytes(bytes):
            pass

        r_str = requests.get(httpbin("get"), headers={MyString("x-custom"): "myheader"})
        assert r_str.request.headers["x-custom"] == "myheader"
        r_bytes = requests.get(
            httpbin("get"), headers={MyBytes(b"x-custom"): b"myheader"}
        )
        assert r_bytes.request.headers["x-custom"] == b"myheader"
        r_mixed = requests.get(
            httpbin("get"), headers={MyString("x-custom"): MyBytes(b"myheader")}
        )
        assert r_mixed.request.headers["x-custom"] == b"myheader"

def test_auth_is_stripped_on_http_downgrade(
        self, httpbin, httpbin_secure, httpbin_ca_bundle
    ):
        r = requests.get(
            httpbin_secure("redirect-to"),
            params={"url": httpbin("get")},
            auth=("user", "pass"),
            verify=httpbin_ca_bundle,
        )
        assert r.history[0].request.headers["Authorization"]
        assert "Authorization" not in r.request.headers

def test_auth_is_retained_for_redirect_on_host(self, httpbin):
        r = requests.get(httpbin("redirect/1"), auth=("user", "pass"))
        h1 = r.history[0].request.headers["Authorization"]
        h2 = r.request.headers["Authorization"]
        assert h1 == h2

def test_requests_history_is_saved(self, httpbin):
        r = requests.get(httpbin("redirect/5"))
        total = r.history[-1].history
        i = 0
        for item in r.history:
            assert item.history == total[0:i]
            i += 1

def test_response_iter_lines(self, httpbin):
        r = requests.get(httpbin("stream/4"), stream=True)
        assert r.status_code == 200
        it = r.iter_lines()
        next(it)
        assert len(list(it)) == 3

def test_response_context_manager(self, httpbin):
        with requests.get(httpbin("stream/4"), stream=True) as response:
            assert isinstance(response, requests.Response)
        assert response.raw.closed

@pytest.mark.xfail
    def test_response_iter_lines_reentrant(self, httpbin):
        r = requests.get(httpbin("stream/4"), stream=True)
        assert r.status_code == 200
        next(r.iter_lines())
        assert len(list(r.iter_lines())) == 3

def test_response_json_when_content_is_None(self, httpbin):
        r = requests.get(httpbin("/status/204"))
        r.status_code = 0
        r._content = False
        r._content_consumed = False
        assert r.content is None
        with pytest.raises(ValueError):
            r.json()

def test_stream_timeout(self, httpbin):
        try:
            requests.get(httpbin("delay/10"), timeout=2.0)
        except requests.exceptions.Timeout as e:
            assert "Read timed out" in e.args[0].args[0]

@pytest.mark.parametrize(
        "timeout, error_text",
        (((3, 4, 5), "(connect, read)"), ("foo", "must be an int, float or None")),
    )
    def test_invalid_timeout(self, httpbin, timeout, error_text):
        with pytest.raises(ValueError) as e:
            requests.get(httpbin("get"), timeout=timeout)
        assert error_text in str(e)

@pytest.mark.parametrize("timeout", (None, Urllib3Timeout(connect=None, read=None)))
    def test_none_timeout(self, httpbin, timeout):
        r = requests.get(httpbin("get"), timeout=timeout)
        assert r.status_code == 200

@pytest.mark.parametrize(
        "timeout", ((None, 0.1), Urllib3Timeout(connect=None, read=0.1))
    )
    def test_read_timeout(self, httpbin, timeout):
        try:
            requests.get(httpbin("delay/10"), timeout=timeout)
            pytest.fail("The recv() request should time out.")
        except ReadTimeout:
            pass

@pytest.mark.parametrize(
        "timeout", ((0.1, None), Urllib3Timeout(connect=0.1, read=None))
    )
    def test_connect_timeout(self, timeout):
        try:
            requests.get(TARPIT, timeout=timeout)
            pytest.fail("The connect() request should time out.")
        except ConnectTimeout as e:
            assert isinstance(e, ConnectionError)
            assert isinstance(e, Timeout)

@pytest.mark.parametrize(
        "timeout", ((0.1, 0.1), Urllib3Timeout(connect=0.1, read=0.1))
    )
    def test_total_timeout_connect(self, timeout):
        try:
            requests.get(TARPIT, timeout=timeout)
            pytest.fail("The connect() request should time out.")
        except ConnectTimeout:
            pass

@pytest.mark.parametrize("url, exception", (("http://:1", InvalidURL),))
    def test_redirecting_to_bad_url(self, httpbin, url, exception):
        with pytest.raises(exception):
            requests.get(httpbin("redirect-to"), params={"url": url})

def test_json_decode_compatibility(self, httpbin):
        r = requests.get(httpbin("bytes/20"))
        with pytest.raises(requests.exceptions.JSONDecodeError) as excinfo:
            r.json()
        assert isinstance(excinfo.value, RequestException)
        assert isinstance(excinfo.value, JSONDecodeError)
        assert r.text not in str(excinfo.value)

def test_json_decode_persists_doc_attr(self, httpbin):
        r = requests.get(httpbin("bytes/20"))
        with pytest.raises(requests.exceptions.JSONDecodeError) as excinfo:
            r.json()
        assert excinfo.value.doc == r.text