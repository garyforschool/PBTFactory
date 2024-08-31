def test_cookie_forging():
    c = Client(cookie_app)
    c.set_cookie("foo", "bar")
    response = c.open()
    assert response.text == "foo=bar"

def test_set_cookie_app():
    c = Client(cookie_app)
    response = c.open()
    assert "Set-Cookie" in response.headers

def test_cookiejar_stores_cookie():
    c = Client(cookie_app)
    c.open()
    assert c.get_cookie("test") is not None

def test_no_initial_cookie():
    c = Client(cookie_app)
    response = c.open()
    assert response.text == "No Cookie"

def test_resent_cookie():
    c = Client(cookie_app)
    c.open()
    response = c.open()
    assert response.text == "test=test"

def test_disable_cookies():
    c = Client(cookie_app, use_cookies=False)
    c.open()
    response = c.open()
    assert response.text == "No Cookie"

def test_cookie_for_different_path():
    c = Client(cookie_app)
    c.open("/path1")
    response = c.open("/path2")
    assert response.text == "test=test"

def test_follow_redirect():
    env = create_environ("/", base_url="http://localhost")
    c = Client(redirect_with_get_app)
    response = c.open(environ_overrides=env, follow_redirects=True)
    assert response.status == "200 OK"
    assert response.text == "current url: http://localhost/some/redirect/"
    c = Client(redirect_with_get_app)
    resp = c.get("/", follow_redirects=True)
    assert resp.status_code == 200
    assert resp.text == "current url: http://localhost/some/redirect/"
    c = Client(redirect_with_get_app)
    resp = c.get("/first/request", follow_redirects=True)
    assert resp.status_code == 200
    assert resp.text == "current url: http://localhost/some/redirect/"

def open(self, *args, **kwargs):
            self.counter += 1
            env = kwargs.setdefault("environ_overrides", {})
            env["werkzeug._foo"] = self.counter
            return Client.open(self, *args, **kwargs)

def test_no_content_type_header_addition():
    c = Client(no_response_headers_app)
    response = c.open()
    assert response.headers == Headers([("Content-Length", "8")])

def test_client_response_wrapper():

    class CustomResponse(Response):
        pass

    class CustomTestResponse(TestResponse, Response):
        pass

    c1 = Client(Response(), CustomResponse)
    r1 = c1.open()
    assert isinstance(r1, CustomResponse)
    assert type(r1) is not CustomResponse
    assert issubclass(type(r1), CustomResponse)
    c2 = Client(Response(), CustomTestResponse)
    r2 = c2.open()
    assert isinstance(r2, CustomTestResponse)
    assert type(r2) is CustomTestResponse