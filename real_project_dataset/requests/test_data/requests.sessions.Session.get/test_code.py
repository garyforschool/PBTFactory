def test_respect_proxy_env_on_get(self, httpbin):
        with override_environ(http_proxy=INVALID_PROXY):
            with pytest.raises(ProxyError):
                session = requests.Session()
                session.get(httpbin())

def test_DIGEST_AUTH_SETS_SESSION_COOKIES(self, httpbin):
        for authtype in self.digest_auth_algo:
            url = httpbin("digest-auth", "auth", "user", "pass", authtype)
            auth = HTTPDigestAuth("user", "pass")
            s = requests.Session()
            s.get(url, auth=auth)
            assert s.cookies["fake"] == "fake_value"

def test_fixes_1329(self, httpbin):
        s = requests.Session()
        s.headers.update({"ACCEPT": "BOGUS"})
        s.headers.update({"accept": "application/json"})
        r = s.get(httpbin("get"))
        headers = r.request.headers
        assert headers["accept"] == "application/json"
        assert headers["Accept"] == "application/json"
        assert headers["ACCEPT"] == "application/json"

def test_header_remove_is_case_insensitive(self, httpbin):
        s = requests.Session()
        s.headers["foo"] = "bar"
        r = s.get(httpbin("get"), headers={"FOO": None})
        assert "foo" not in r.request.headers

def test_params_are_merged_case_sensitive(self, httpbin):
        s = requests.Session()
        s.params["foo"] = "bar"
        r = s.get(httpbin("get"), params={"FOO": "bar"})
        assert r.json()["args"] == {"foo": "bar", "FOO": "bar"}

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

def test_redirect_with_wrong_gzipped_header(self, httpbin):
        s = requests.Session()
        url = httpbin("redirect/1")
        self._patch_adapter_gzipped_redirect(s, url)
        s.get(url)

def test_urllib3_retries(httpbin):
    from urllib3.util import Retry

    s = requests.Session()
    s.mount("http://", HTTPAdapter(max_retries=Retry(total=2, status_forcelist=[500])))
    with pytest.raises(RetryError):
        s.get(httpbin("status/500"))

def test_urllib3_pool_connection_closed(httpbin):
    s = requests.Session()
    s.mount("http://", HTTPAdapter(pool_connections=0, pool_maxsize=0))
    try:
        s.get(httpbin("status/200"))
    except ConnectionError as e:
        assert "Pool is closed." in str(e)

def test_different_connection_pool_for_tls_settings_verify_True(self):

        def response_handler(sock):
            consume_socket_content(sock, timeout=0.5)
            sock.send(
                b'HTTP/1.1 200 OK\r\nContent-Length: 18\r\n\r\n\xff\xfe{\x00"\x00K0"\x00=\x00"\x00\xab0"\x00\r\n'
            )

        s = requests.Session()
        close_server = threading.Event()
        server = TLSServer(
            handler=response_handler,
            wait_to_close_event=close_server,
            requests_to_handle=3,
            cert_chain="tests/certs/expired/server/server.pem",
            keyfile="tests/certs/expired/server/server.key",
        )
        with server as (host, port):
            url = f"https://{host}:{port}"
            r1 = s.get(url, verify=False)
            assert r1.status_code == 200
            with pytest.raises(requests.exceptions.SSLError):
                s.get(url)
            close_server.set()
        assert 2 == len(s.adapters["https://"].poolmanager.pools)

def test_different_connection_pool_for_tls_settings_verify_bundle_expired_cert(
        self,
    ):

        def response_handler(sock):
            consume_socket_content(sock, timeout=0.5)
            sock.send(
                b'HTTP/1.1 200 OK\r\nContent-Length: 18\r\n\r\n\xff\xfe{\x00"\x00K0"\x00=\x00"\x00\xab0"\x00\r\n'
            )

        s = requests.Session()
        close_server = threading.Event()
        server = TLSServer(
            handler=response_handler,
            wait_to_close_event=close_server,
            requests_to_handle=3,
            cert_chain="tests/certs/expired/server/server.pem",
            keyfile="tests/certs/expired/server/server.key",
        )
        with server as (host, port):
            url = f"https://{host}:{port}"
            r1 = s.get(url, verify=False)
            assert r1.status_code == 200
            with pytest.raises(requests.exceptions.SSLError):
                s.get(url, verify="tests/certs/expired/ca/ca.crt")
            close_server.set()
        assert 2 == len(s.adapters["https://"].poolmanager.pools)