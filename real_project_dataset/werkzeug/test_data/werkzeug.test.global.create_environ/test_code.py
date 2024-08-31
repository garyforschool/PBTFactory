def test_is_resource_modified(self):
        env = create_environ()
        env["REQUEST_METHOD"] = "POST"
        assert http.is_resource_modified(env, etag="testing")
        env["REQUEST_METHOD"] = "GET"
        pytest.raises(TypeError, http.is_resource_modified, env, data="42", etag="23")
        env["HTTP_IF_NONE_MATCH"] = http.generate_etag(b"awesome")
        assert not http.is_resource_modified(env, data=b"awesome")
        env["HTTP_IF_MODIFIED_SINCE"] = http.http_date(datetime(2008, 1, 1, 12, 30))
        assert not http.is_resource_modified(
            env, last_modified=datetime(2008, 1, 1, 12, 0)
        )
        assert http.is_resource_modified(env, last_modified=datetime(2008, 1, 1, 13, 0))

def test_is_resource_modified_for_range_requests(self):
        env = create_environ()
        env["HTTP_IF_MODIFIED_SINCE"] = http.http_date(datetime(2008, 1, 1, 12, 30))
        env["HTTP_IF_RANGE"] = http.generate_etag(b"awesome_if_range")
        assert not http.is_resource_modified(
            env,
            data=b"not_the_same",
            ignore_if_range=False,
            last_modified=datetime(2008, 1, 1, 12, 30),
        )
        env["HTTP_RANGE"] = ""
        assert not http.is_resource_modified(
            env, data=b"awesome_if_range", ignore_if_range=False
        )
        assert http.is_resource_modified(
            env, data=b"not_the_same", ignore_if_range=False
        )
        env["HTTP_IF_RANGE"] = http.http_date(datetime(2008, 1, 1, 13, 30))
        assert http.is_resource_modified(
            env, last_modified=datetime(2008, 1, 1, 14, 0), ignore_if_range=False
        )
        assert not http.is_resource_modified(
            env, last_modified=datetime(2008, 1, 1, 13, 30), ignore_if_range=False
        )
        assert http.is_resource_modified(
            env, last_modified=datetime(2008, 1, 1, 13, 30), ignore_if_range=True
        )

def test_create_environ():
    env = create_environ("/foo?bar=baz", "http://example.org/")
    expected = {
        "wsgi.multiprocess": False,
        "wsgi.version": (1, 0),
        "wsgi.run_once": False,
        "wsgi.errors": sys.stderr,
        "wsgi.multithread": False,
        "wsgi.url_scheme": "http",
        "SCRIPT_NAME": "",
        "SERVER_NAME": "example.org",
        "REQUEST_METHOD": "GET",
        "HTTP_HOST": "example.org",
        "PATH_INFO": "/foo",
        "SERVER_PORT": "80",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "QUERY_STRING": "bar=baz",
    }
    for key, value in iter(expected.items()):
        assert env[key] == value
    assert env["wsgi.input"].read(0) == b""
    assert create_environ("/foo", "http://example.com/")["SCRIPT_NAME"] == ""

def test_create_environ_query_string_error():
    with pytest.raises(ValueError):
        create_environ("/foo?bar=baz", query_string={"a": "b"})

def test_builder_from_environ():
    environ = create_environ(
        "/ㄱ",
        base_url="https://example.com/base",
        query_string={"name": "Werkzeug"},
        data={"foo": "ㄴ"},
        headers={"X-Foo": "ㄷ"},
    )
    builder = EnvironBuilder.from_environ(environ)
    try:
        new_environ = builder.get_environ()
    finally:
        builder.close()
    assert new_environ == environ

def test_file_closing():
    closed = []

    class SpecialInput:

        def read(self, size):
            return b""

        def close(self):
            closed.append(self)

    create_environ(data={"foo": SpecialInput()})
    assert len(closed) == 1
    builder = EnvironBuilder()
    builder.files.add_file("blah", SpecialInput())
    builder.close()
    assert len(closed) == 2

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

def test_follow_external_redirect():
    env = create_environ("/", base_url="http://localhost")
    c = Client(external_redirect_demo_app)
    pytest.raises(
        RuntimeError, lambda: c.get(environ_overrides=env, follow_redirects=True)
    )

def test_follow_external_redirect_on_same_subdomain():
    env = create_environ("/", base_url="http://example.com")
    c = Client(external_subdomain_redirect_demo_app, allow_subdomain_redirects=True)
    c.get(environ_overrides=env, follow_redirects=True)
    env = create_environ("/", base_url="http://localhost")
    pytest.raises(
        RuntimeError, lambda: c.get(environ_overrides=env, follow_redirects=True)
    )
    c = Client(external_subdomain_redirect_demo_app)
    pytest.raises(
        RuntimeError, lambda: c.get(environ_overrides=env, follow_redirects=True)
    )

def test_path_info_and_script_name_fetching():
    env = create_environ("/☃", "http://example.com/☄/")
    assert wsgi.get_path_info(env) == "/☃"

def test_get_current_url_unicode():
    env = create_environ(query_string="foo=bar&baz=blah&meh=Ï")
    rv = wsgi.get_current_url(env)
    assert rv == "http://localhost/?foo=bar&baz=blah&meh=Ï"

def test_get_current_url_invalid_utf8():
    env = create_environ()
    env["QUERY_STRING"] = "foo=bar&baz=blah&meh=Ï"
    rv = wsgi.get_current_url(env)
    assert rv == "http://localhost/?foo=bar&baz=blah&meh=%CF"

def test_range_wrapper():
    response = Response(b"Hello World")
    range_wrapper = _RangeWrapper(response.response, 6, 4)
    assert next(range_wrapper) == b"Worl"
    response = Response(b"Hello World")
    range_wrapper = _RangeWrapper(response.response, 1, 0)
    with pytest.raises(StopIteration):
        next(range_wrapper)
    response = Response(b"Hello World")
    range_wrapper = _RangeWrapper(response.response, 6, 100)
    assert next(range_wrapper) == b"World"
    response = Response(x for x in (b"He", b"ll", b"o ", b"Wo", b"rl", b"d"))
    range_wrapper = _RangeWrapper(response.response, 6, 4)
    assert not range_wrapper.seekable
    assert next(range_wrapper) == b"Wo"
    assert next(range_wrapper) == b"rl"
    response = Response(x for x in (b"He", b"ll", b"o W", b"o", b"rld"))
    range_wrapper = _RangeWrapper(response.response, 6, 4)
    assert next(range_wrapper) == b"W"
    assert next(range_wrapper) == b"o"
    assert next(range_wrapper) == b"rl"
    with pytest.raises(StopIteration):
        next(range_wrapper)
    response = Response(x for x in (b"Hello", b" World"))
    range_wrapper = _RangeWrapper(response.response, 1, 1)
    assert next(range_wrapper) == b"e"
    with pytest.raises(StopIteration):
        next(range_wrapper)
    resources = os.path.join(os.path.dirname(__file__), "res")
    env = create_environ()
    with open(os.path.join(resources, "test.txt"), "rb") as f:
        response = Response(wrap_file(env, f))
        range_wrapper = _RangeWrapper(response.response, 1, 2)
        assert range_wrapper.seekable
        assert next(range_wrapper) == b"OU"
        with pytest.raises(StopIteration):
            next(range_wrapper)
    with open(os.path.join(resources, "test.txt"), "rb") as f:
        response = Response(wrap_file(env, f))
        range_wrapper = _RangeWrapper(response.response, 2)
        assert next(range_wrapper) == b"UND\n"
        with pytest.raises(StopIteration):
            next(range_wrapper)

def test_closing_iterator():

    class Namespace:
        got_close = False
        got_additional = False

    class Response:

        def __init__(self, environ, start_response):
            self.start = start_response

        def __iter__(self):
            self.start("200 OK", [("Content-Type", "text/plain")])
            yield "some content"

        def close(self):
            Namespace.got_close = True

    def additional():
        Namespace.got_additional = True

    def app(environ, start_response):
        return ClosingIterator(Response(environ, start_response), additional)

    app_iter, status, headers = run_wsgi_app(app, create_environ(), buffered=True)
    assert "".join(app_iter) == "some content"
    assert Namespace.got_close
    assert Namespace.got_additional

def test_wrapper_internals():
    req = Request.from_values(data={"foo": "bar"}, method="POST")
    req._load_form_data()
    assert req.form.to_dict() == {"foo": "bar"}
    req._load_form_data()
    assert req.form.to_dict() == {"foo": "bar"}
    assert repr(req) == "<Request 'http://localhost/' [POST]>"
    resp = Response()
    assert repr(resp) == "<Response 0 bytes [200 OK]>"
    resp.set_data("Hello World!")
    assert repr(resp) == "<Response 12 bytes [200 OK]>"
    resp.response = iter(["Test"])
    assert repr(resp) == "<Response streamed [200 OK]>"
    response = Response(["Hällo Wörld"])
    headers = response.get_wsgi_headers(create_environ())
    assert "Content-Length" in headers
    response = Response(["Hällo Wörld".encode()])
    headers = response.get_wsgi_headers(create_environ())
    assert "Content-Length" in headers

def test_request_application():

    @wrappers.Request.application
    def application(request):
        return wrappers.Response("Hello World!")

    @wrappers.Request.application
    def failing_application(request):
        raise BadRequest()

    resp = wrappers.Response.from_app(application, create_environ())
    assert resp.data == b"Hello World!"
    assert resp.status_code == 200
    resp = wrappers.Response.from_app(failing_application, create_environ())
    assert b"Bad Request" in resp.data
    assert resp.status_code == 400

def test_base_response():
    response = wrappers.Response("öäü")
    assert response.get_data() == "öäü".encode()
    response = wrappers.Response("foo")
    response.stream.write("bar")
    assert response.get_data() == b"foobar"
    response = wrappers.Response()
    response.set_cookie(
        "foo",
        value="bar",
        max_age=60,
        expires=0,
        path="/blub",
        domain="example.org",
        samesite="Strict",
    )
    assert response.headers.to_wsgi_list() == [
        ("Content-Type", "text/plain; charset=utf-8"),
        (
            "Set-Cookie",
            "foo=bar; Domain=example.org; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=60; Path=/blub; SameSite=Strict",
        ),
    ]
    response = wrappers.Response()
    response.delete_cookie("foo")
    assert response.headers.to_wsgi_list() == [
        ("Content-Type", "text/plain; charset=utf-8"),
        (
            "Set-Cookie",
            "foo=; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0; Path=/",
        ),
    ]
    closed = []

    class Iterable:

        def __next__(self):
            raise StopIteration()

        def __iter__(self):
            return self

        def close(self):
            closed.append(True)

    response = wrappers.Response(Iterable())
    response.call_on_close(lambda: closed.append(True))
    app_iter, status, headers = run_wsgi_app(response, create_environ(), buffered=True)
    assert status == "200 OK"
    assert "".join(app_iter) == ""
    assert len(closed) == 2
    del closed[:]
    response = wrappers.Response(Iterable())
    with response:
        pass
    assert len(closed) == 1

def test_etag_response():
    response = wrappers.Response("Hello World")
    assert response.get_etag() == (None, None)
    response.add_etag()
    assert response.get_etag() == ("0a4d55a8d778e5022fab701977c5d840bbc486d0", False)
    assert not response.cache_control
    response.cache_control.must_revalidate = True
    response.cache_control.max_age = 60
    response.headers["Content-Length"] = len(response.get_data())
    assert response.headers["Cache-Control"] in (
        "must-revalidate, max-age=60",
        "max-age=60, must-revalidate",
    )
    assert "date" not in response.headers
    env = create_environ()
    env.update({"REQUEST_METHOD": "GET", "HTTP_IF_NONE_MATCH": response.get_etag()[0]})
    response.make_conditional(env)
    assert "date" in response.headers
    resp = wrappers.Response.from_app(response, env)
    assert resp.status_code == 304
    assert "content-length" not in resp.headers
    response = wrappers.Response("Hello World")
    response.date = 1337
    d = response.date
    response.make_conditional(env)
    assert response.date == d
    response = wrappers.Response("Hello World")
    response.content_length = 999
    response.make_conditional(env)
    assert response.content_length == 999

def test_etag_response_412():
    response = wrappers.Response("Hello World")
    assert response.get_etag() == (None, None)
    response.add_etag()
    assert response.get_etag() == ("0a4d55a8d778e5022fab701977c5d840bbc486d0", False)
    assert not response.cache_control
    response.cache_control.must_revalidate = True
    response.cache_control.max_age = 60
    response.headers["Content-Length"] = len(response.get_data())
    assert response.headers["Cache-Control"] in (
        "must-revalidate, max-age=60",
        "max-age=60, must-revalidate",
    )
    assert "date" not in response.headers
    env = create_environ()
    env.update(
        {"REQUEST_METHOD": "GET", "HTTP_IF_MATCH": f"{response.get_etag()[0]}xyz"}
    )
    response.make_conditional(env)
    assert "date" in response.headers
    resp = wrappers.Response.from_app(response, env)
    assert resp.status_code == 412
    assert resp.data != b""
    response = wrappers.Response("Hello World")
    response.date = 1337
    d = response.date
    response.make_conditional(env)
    assert response.date == d
    response = wrappers.Response("Hello World")
    response.content_length = 999
    response.make_conditional(env)
    assert response.content_length == 999

def test_range_request_basic():
    env = create_environ()
    response = wrappers.Response("Hello World")
    env["HTTP_RANGE"] = "bytes=0-4"
    response.make_conditional(env, accept_ranges=True, complete_length=11)
    assert response.status_code == 206
    assert response.headers["Accept-Ranges"] == "bytes"
    assert response.headers["Content-Range"] == "bytes 0-4/11"
    assert response.headers["Content-Length"] == "5"
    assert response.data == b"Hello"

def test_range_request_out_of_bound():
    env = create_environ()
    response = wrappers.Response("Hello World")
    env["HTTP_RANGE"] = "bytes=6-666"
    response.make_conditional(env, accept_ranges=True, complete_length=11)
    assert response.status_code == 206
    assert response.headers["Accept-Ranges"] == "bytes"
    assert response.headers["Content-Range"] == "bytes 6-10/11"
    assert response.headers["Content-Length"] == "5"
    assert response.data == b"World"

def test_range_request_with_file():
    env = create_environ()
    resources = os.path.join(os.path.dirname(__file__), "res")
    fname = os.path.join(resources, "test.txt")
    with open(fname, "rb") as f:
        fcontent = f.read()
    with open(fname, "rb") as f:
        response = wrappers.Response(wrap_file(env, f))
        env["HTTP_RANGE"] = "bytes=0-0"
        response.make_conditional(
            env, accept_ranges=True, complete_length=len(fcontent)
        )
        assert response.status_code == 206
        assert response.headers["Accept-Ranges"] == "bytes"
        assert response.headers["Content-Range"] == f"bytes 0-0/{len(fcontent)}"
        assert response.headers["Content-Length"] == "1"
        assert response.data == fcontent[:1]

def test_range_request_with_complete_file():
    env = create_environ()
    resources = os.path.join(os.path.dirname(__file__), "res")
    fname = os.path.join(resources, "test.txt")
    with open(fname, "rb") as f:
        fcontent = f.read()
    with open(fname, "rb") as f:
        fsize = os.path.getsize(fname)
        response = wrappers.Response(wrap_file(env, f))
        env["HTTP_RANGE"] = f"bytes=0-{fsize - 1}"
        response.make_conditional(env, accept_ranges=True, complete_length=fsize)
        assert response.status_code == 206
        assert response.headers["Accept-Ranges"] == "bytes"
        assert response.headers["Content-Range"] == f"bytes 0-{fsize - 1}/{fsize}"
        assert response.headers["Content-Length"] == str(fsize)
        assert response.data == fcontent

@pytest.mark.parametrize("value", [None, 0])
def test_range_request_without_complete_length(value):
    env = create_environ(headers={"Range": "bytes=0-10"})
    response = wrappers.Response("Hello World")
    response.make_conditional(env, accept_ranges=True, complete_length=value)
    assert response.status_code == 200
    assert response.data == b"Hello World"

def test_invalid_range_request():
    env = create_environ()
    response = wrappers.Response("Hello World")
    env["HTTP_RANGE"] = "bytes=-"
    with pytest.raises(RequestedRangeNotSatisfiable):
        response.make_conditional(env, accept_ranges=True, complete_length=11)

def test_urlfication():
    resp = wrappers.Response()
    resp.headers["Location"] = "http://üser:pässword@☃.net/påth"
    resp.headers["Content-Location"] = "http://☃.net/"
    headers = resp.get_wsgi_headers(create_environ())
    assert headers["location"] == "http://%C3%BCser:p%C3%A4ssword@xn--n3h.net/p%C3%A5th"
    assert headers["content-location"] == "http://xn--n3h.net/"

def test_response_304_no_content_length():
    resp = wrappers.Response("Test", status=304)
    env = create_environ()
    assert "content-length" not in resp.get_wsgi_headers(env)

@pytest.mark.parametrize(
    ("auto", "location", "expect"),
    (
        (False, "/test", "/test"),
        (False, "/\\\\test.example?q", "/%5C%5Ctest.example?q"),
        (True, "/test", "http://localhost/test"),
        (True, "test", "http://localhost/a/b/test"),
        (True, "./test", "http://localhost/a/b/test"),
        (True, "../test", "http://localhost/a/test"),
    ),
)
def test_location_header_autocorrect(monkeypatch, auto, location, expect):
    monkeypatch.setattr(wrappers.Response, "autocorrect_location_header", auto)
    env = create_environ("/a/b/c")
    resp = wrappers.Response("Hello World!")
    resp.headers["Location"] = location
    assert resp.get_wsgi_headers(env)["Location"] == expect

def test_204_and_1XX_response_has_no_content_length():
    response = wrappers.Response(status=204)
    assert response.content_length is None
    headers = response.get_wsgi_headers(create_environ())
    assert "Content-Length" not in headers
    response = wrappers.Response(status=100)
    assert response.content_length is None
    headers = response.get_wsgi_headers(create_environ())
    assert "Content-Length" not in headers

def test_malformed_204_response_has_no_content_length():
    response = wrappers.Response(status=204)
    response.set_data(b"test")
    assert response.content_length == 4
    env = create_environ()
    app_iter, status, headers = response.get_wsgi_response(env)
    assert status == "204 NO CONTENT"
    assert "Content-Length" not in headers
    assert b"".join(app_iter) == b""

def test_basic_routing():
    map = r.Map(
        [
            r.Rule("/", endpoint="index"),
            r.Rule("/foo", endpoint="foo"),
            r.Rule("/bar/", endpoint="bar"),
            r.Rule("/ws", endpoint="ws", websocket=True),
            r.Rule("/", endpoint="indexws", websocket=True),
        ]
    )
    adapter = map.bind("example.org", "/")
    assert adapter.match("/") == ("index", {})
    assert adapter.match("/foo") == ("foo", {})
    assert adapter.match("/bar/") == ("bar", {})
    pytest.raises(r.RequestRedirect, lambda: adapter.match("/bar"))
    pytest.raises(NotFound, lambda: adapter.match("/blub"))
    adapter = map.bind("example.org", "/", url_scheme="ws")
    assert adapter.match("/") == ("indexws", {})
    adapter = map.bind("example.org", "/test")
    with pytest.raises(r.RequestRedirect) as excinfo:
        adapter.match("/bar")
    assert excinfo.value.new_url == "http://example.org/test/bar/"
    adapter = map.bind("example.org", "/")
    with pytest.raises(r.RequestRedirect) as excinfo:
        adapter.match("/bar")
    assert excinfo.value.new_url == "http://example.org/bar/"
    adapter = map.bind("example.org", "/")
    with pytest.raises(r.RequestRedirect) as excinfo:
        adapter.match("/bar", query_args={"aha": "muhaha"})
    assert excinfo.value.new_url == "http://example.org/bar/?aha=muhaha"
    adapter = map.bind("example.org", "/")
    with pytest.raises(r.RequestRedirect) as excinfo:
        adapter.match("/bar", query_args="aha=muhaha")
    assert excinfo.value.new_url == "http://example.org/bar/?aha=muhaha"
    adapter = map.bind_to_environ(create_environ("/bar?foo=bar", "http://example.org/"))
    with pytest.raises(r.RequestRedirect) as excinfo:
        adapter.match()
    assert excinfo.value.new_url == "http://example.org/bar/?foo=bar"
    adapter = map.bind("example.org", "/ws", url_scheme="wss")
    assert adapter.match("/ws", websocket=True) == ("ws", {})
    with pytest.raises(r.WebsocketMismatch):
        adapter.match("/ws", websocket=False)
    with pytest.raises(r.WebsocketMismatch):
        adapter.match("/foo", websocket=True)
    adapter = map.bind_to_environ(
        create_environ(
            "/ws?foo=bar",
            "http://example.org/",
            headers=[("Connection", "Upgrade"), ("upgrade", "WebSocket")],
        )
    )
    assert adapter.match("/ws") == ("ws", {})
    with pytest.raises(r.WebsocketMismatch):
        adapter.match("/ws", websocket=False)
    adapter = map.bind_to_environ(
        create_environ(
            "/ws?foo=bar",
            "http://example.org/",
            headers=[("Connection", "keep-alive, Upgrade"), ("upgrade", "websocket")],
        )
    )
    assert adapter.match("/ws") == ("ws", {})
    with pytest.raises(r.WebsocketMismatch):
        adapter.match("/ws", websocket=False)

def test_environ_defaults():
    environ = create_environ("/foo")
    assert environ["PATH_INFO"] == "/foo"
    m = r.Map([r.Rule("/foo", endpoint="foo"), r.Rule("/bar", endpoint="bar")])
    a = m.bind_to_environ(environ)
    assert a.match("/foo") == ("foo", {})
    assert a.match() == ("foo", {})
    assert a.match("/bar") == ("bar", {})
    pytest.raises(NotFound, a.match, "/bars")

def test_environ_nonascii_pathinfo():
    environ = create_environ("/лошадь")
    m = r.Map([r.Rule("/", endpoint="index"), r.Rule("/лошадь", endpoint="horse")])
    a = m.bind_to_environ(environ)
    assert a.match("/") == ("index", {})
    assert a.match("/лошадь") == ("horse", {})
    pytest.raises(NotFound, a.match, "/барсук")

def test_dispatch():
    env = create_environ("/")
    map = r.Map([r.Rule("/", endpoint="root"), r.Rule("/foo/", endpoint="foo")])
    adapter = map.bind_to_environ(env)
    raise_this = None

    def view_func(endpoint, values):
        if raise_this is not None:
            raise raise_this
        return Response(repr((endpoint, values)))

    def dispatch(path, quiet=False):
        return Response.force_type(
            adapter.dispatch(view_func, path, catch_http_exceptions=quiet), env
        )

    assert dispatch("/").data == b"('root', {})"
    assert dispatch("/foo").status_code == 308
    raise_this = NotFound()
    pytest.raises(NotFound, lambda: dispatch("/bar"))
    assert dispatch("/bar", True).status_code == 404

def test_invalid_subdomain_warning():
    env = create_environ("/foo")
    env["SERVER_NAME"] = env["HTTP_HOST"] = "foo.example.com"
    m = r.Map([r.Rule("/foo", endpoint="foo")])
    with pytest.warns(UserWarning) as record:
        a = m.bind_to_environ(env, server_name="bar.example.com")
    assert a.subdomain == "<invalid>"
    assert len(record) == 1

@pytest.mark.parametrize(
    ("base", "name"),
    (("http://localhost", "localhost:80"), ("https://localhost", "localhost:443")),
)
def test_server_name_match_default_port(base, name):
    environ = create_environ("/foo", base_url=base)
    map = r.Map([r.Rule("/foo", endpoint="foo")])
    adapter = map.bind_to_environ(environ, server_name=name)
    assert adapter.match() == ("foo", {})

def test_server_name_interpolation():
    server_name = "example.invalid"
    map = r.Map(
        [r.Rule("/", endpoint="index"), r.Rule("/", endpoint="alt", subdomain="alt")]
    )
    env = create_environ("/", f"http://{server_name}/")
    adapter = map.bind_to_environ(env, server_name=server_name)
    assert adapter.match() == ("index", {})
    env = create_environ("/", f"http://alt.{server_name}/")
    adapter = map.bind_to_environ(env, server_name=server_name)
    assert adapter.match() == ("alt", {})
    env = create_environ("/", f"http://{server_name}/")
    with pytest.warns(UserWarning):
        adapter = map.bind_to_environ(env, server_name="foo")
    assert adapter.subdomain == "<invalid>"

def test_external_building_with_port_bind_to_environ():
    map = r.Map([r.Rule("/", endpoint="index")])
    adapter = map.bind_to_environ(
        create_environ("/", "http://example.org:5000/"), server_name="example.org:5000"
    )
    built_url = adapter.build("index", {}, force_external=True)
    assert built_url == "http://example.org:5000/", built_url

def test_external_building_with_port_bind_to_environ_wrong_servername():
    map = r.Map([r.Rule("/", endpoint="index")])
    environ = create_environ("/", "http://example.org:5000/")
    with pytest.warns(UserWarning):
        adapter = map.bind_to_environ(environ, server_name="example.org")
    assert adapter.subdomain == "<invalid>"

def test_server_name_casing():
    m = r.Map([r.Rule("/", endpoint="index", subdomain="foo")])
    env = create_environ()
    env["SERVER_NAME"] = env["HTTP_HOST"] = "FOO.EXAMPLE.COM"
    a = m.bind_to_environ(env, server_name="example.com")
    assert a.match("/") == ("index", {})
    env = create_environ()
    env["SERVER_NAME"] = "127.0.0.1"
    env["SERVER_PORT"] = "5000"
    del env["HTTP_HOST"]
    with pytest.warns(UserWarning):
        a = m.bind_to_environ(env, server_name="example.com")
    with pytest.raises(NotFound):
        a.match()

def test_redirect_request_exception_code():
    exc = r.RequestRedirect("http://www.google.com/")
    exc.code = 307
    env = create_environ()
    assert exc.get_response(env).status_code == exc.code

def test_parse_form_data_put_without_content(self):
        env = create_environ("/foo", "http://example.org/", method="PUT")
        stream, form, files = formparser.parse_form_data(env)
        assert stream.read() == b""
        assert len(form) == 0
        assert len(files) == 0

def test_parse_form_data_get_without_content(self):
        env = create_environ("/foo", "http://example.org/", method="GET")
        stream, form, files = formparser.parse_form_data(env)
        assert stream.read() == b""
        assert len(form) == 0
        assert len(files) == 0

def test_dispatcher():

    def null_application(environ, start_response):
        start_response("404 NOT FOUND", [("Content-Type", "text/plain")])
        yield b"NOT FOUND"

    def dummy_application(environ, start_response):
        start_response("200 OK", [("Content-Type", "text/plain")])
        yield environ["SCRIPT_NAME"].encode()

    app = DispatcherMiddleware(
        null_application,
        {"/test1": dummy_application, "/test2/very": dummy_application},
    )
    tests = {
        "/test1": ("/test1", "/test1/asfd", "/test1/very"),
        "/test2/very": ("/test2/very", "/test2/very/long/path/after/script/name"),
    }
    for name, urls in tests.items():
        for p in urls:
            environ = create_environ(p)
            app_iter, status, headers = run_wsgi_app(app, environ)
            assert status == "200 OK"
            assert b"".join(app_iter).strip() == name.encode()
    app_iter, status, headers = run_wsgi_app(app, create_environ("/missing"))
    assert status == "404 NOT FOUND"
    assert b"".join(app_iter).strip() == b"NOT FOUND"

def test_lint_middleware():
    app = LintMiddleware(dummy_application)
    environ = create_environ("/test")
    app_iter, status, headers = run_wsgi_app(app, environ, buffered=True)
    assert status == "200 OK"

@pytest.mark.parametrize(
    "key, value, message",
    [
        ("wsgi.version", (0, 7), "Environ is not a WSGI 1.0 environ."),
        ("SCRIPT_NAME", "test", "'SCRIPT_NAME' does not start with a slash:"),
        ("PATH_INFO", "test", "'PATH_INFO' does not start with a slash:"),
    ],
)
def test_lint_middleware_check_environ(key, value, message):
    app = LintMiddleware(dummy_application)
    environ = create_environ("/test")
    environ[key] = value
    with pytest.warns(WSGIWarning, match=message):
        app_iter, status, headers = run_wsgi_app(app, environ, buffered=True)
    assert status == "200 OK"

def test_lint_middleware_invalid_status():

    def my_dummy_application(environ, start_response):
        start_response("20 OK", [("Content-Type", "text/plain")])
        return [b"Foo"]

    app = LintMiddleware(my_dummy_application)
    environ = create_environ("/test")
    with pytest.warns(WSGIWarning) as record:
        run_wsgi_app(app, environ, buffered=True)
    assert len(record) == 3

@pytest.mark.parametrize(
    "headers, message",
    [
        (tuple([("Content-Type", "text/plain")]), "Header list is not a list."),
        (["fo"], "Header items must be 2-item tuples."),
        ([("status", "foo")], "The status header is not supported."),
    ],
)
def test_lint_middleware_http_headers(headers, message):

    def my_dummy_application(environ, start_response):
        start_response("200 OK", headers)
        return [b"Foo"]

    app = LintMiddleware(my_dummy_application)
    environ = create_environ("/test")
    with pytest.warns(WSGIWarning, match=message):
        run_wsgi_app(app, environ, buffered=True)

def test_lint_middleware_invalid_location():

    def my_dummy_application(environ, start_response):
        start_response("200 OK", [("location", "foo")])
        return [b"Foo"]

    app = LintMiddleware(my_dummy_application)
    environ = create_environ("/test")
    with pytest.warns(HTTPWarning, match="Absolute URLs required for location header."):
        run_wsgi_app(app, environ, buffered=True)

def test_shared_data_middleware(tmpdir):

    def null_application(environ, start_response):
        start_response("404 NOT FOUND", [("Content-Type", "text/plain")])
        yield b"NOT FOUND"

    test_dir = str(tmpdir)
    with open(os.path.join(test_dir, "äöü"), "w") as test_file:
        test_file.write("FOUND")
    for t in [list, dict]:
        app = SharedDataMiddleware(
            null_application,
            t(
                [
                    ("/", os.path.join(os.path.dirname(__file__), "..", "res")),
                    ("/sources", os.path.join(os.path.dirname(__file__), "..", "res")),
                    ("/pkg", ("werkzeug.debug", "shared")),
                    ("/foo", test_dir),
                ]
            ),
        )
        for p in ("/test.txt", "/sources/test.txt", "/foo/äöü"):
            app_iter, status, headers = run_wsgi_app(app, create_environ(p))
            assert status == "200 OK"
            if p.endswith(".txt"):
                content_type = next(v for k, v in headers if k == "Content-Type")
                assert content_type == "text/plain; charset=utf-8"
            with closing(app_iter) as app_iter:
                data = b"".join(app_iter).strip()
            assert data == b"FOUND"
        app_iter, status, headers = run_wsgi_app(
            app, create_environ("/pkg/debugger.js")
        )
        with closing(app_iter) as app_iter:
            contents = b"".join(app_iter)
        assert b"docReady(() =>" in contents
        for path in ("/missing", "/pkg", "/pkg/", "/pkg/missing.txt"):
            app_iter, status, headers = run_wsgi_app(app, create_environ(path))
            assert status == "404 NOT FOUND"
            assert b"".join(app_iter).strip() == b"NOT FOUND"