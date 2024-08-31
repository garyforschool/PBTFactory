def test_cookie_default_path() -> None:

    @Request.application
    def app(request: Request) -> Response:
        r = Response()
        r.set_cookie("k", "v", path=None)
        return r

    c = Client(app)
    c.get("/nested/leaf")
    assert c.get_cookie("k") is None
    assert c.get_cookie("k", path="/nested") is not None
    c.get("/nested/dir/")
    assert c.get_cookie("k", path="/nested/dir") is not None

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

def test_follow_local_redirect():

    class LocalResponse(Response):
        autocorrect_location_header = False

    def local_redirect_app(environ, start_response):
        req = Request(environ)
        if "/from/location" in req.url:
            response = redirect("/to/location", Response=LocalResponse)
        else:
            response = Response(f"current path: {req.path}")
        return response(environ, start_response)

    c = Client(local_redirect_app)
    resp = c.get("/from/location", follow_redirects=True)
    assert resp.status_code == 200
    assert resp.text == "current path: /to/location"

def test_follow_external_redirect():
    env = create_environ("/", base_url="http://localhost")
    c = Client(external_redirect_demo_app)
    pytest.raises(
        RuntimeError, lambda: c.get(environ_overrides=env, follow_redirects=True)

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

def test_follow_redirect_loop():
    c = Client(redirect_loop_app)
    with pytest.raises(ClientRedirectError):
        c.get("/", follow_redirects=True)

def test_follow_redirect_non_root_base_url():

    @Request.application
    def app(request):
        if request.path == "/redirect":
            return redirect("done")
        return Response(request.path)

    c = Client(app)
    response = c.get(
        "/redirect", base_url="http://localhost/other", follow_redirects=True
    )
    assert response.text == "/done"

def test_follow_redirect_exhaust_intermediate():

    class Middleware:

        def __init__(self, app):
            self.app = app
            self.active = 0

        def __call__(self, environ, start_response):
            assert not self.active
            self.active += 1
            try:
                yield from self.app(environ, start_response)
            finally:
                self.active -= 1

    app = Middleware(redirect_with_get_app)
    client = Client(Middleware(redirect_with_get_app))
    response = client.get("/", follow_redirects=True, buffered=False)
    assert response.text == "current url: http://localhost/some/redirect/"
    assert not app.active

def test_redirects_are_tracked():

    @Request.application
    def app(request):
        if request.path == "/first":
            return redirect("/second")
        if request.path == "/second":
            return redirect("/third")
        return Response("done")

    c = Client(app)
    response = c.get("/first", follow_redirects=True)
    assert response.text == "done"
    assert len(response.history) == 2
    assert response.history[-1].request.path == "/second"
    assert response.history[-1].status_code == 302
    assert response.history[-1].location == "/third"
    assert len(response.history[-1].history) == 1
    assert response.history[-1].history[-1] is response.history[-2]
    assert response.history[-2].request.path == "/first"
    assert response.history[-2].status_code == 302
    assert response.history[-2].location == "/second"
    assert len(response.history[-2].history) == 0

def test_cookie_across_redirect():

    @Request.application
    def app(request):
        if request.path == "/":
            return Response(request.cookies.get("auth", "out"))
        if request.path == "/in":
            rv = redirect("/")
            rv.set_cookie("auth", "in")
            return rv
        if request.path == "/out":
            rv = redirect("/")
            rv.delete_cookie("auth")
            return rv

    c = Client(app)
    assert c.get("/").text == "out"
    assert c.get("/in", follow_redirects=True).text == "in"
    assert c.get("/").text == "in"
    assert c.get("/out", follow_redirects=True).text == "out"
    assert c.get("/").text == "out"

def test_path_info_script_name_unquoting():

    def test_app(environ, start_response):
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [f"{environ['PATH_INFO']}\n{environ['SCRIPT_NAME']}"]

    c = Client(test_app)
    resp = c.get("/foo%40bar")
    assert resp.text == "/foo@bar\n"
    c = Client(test_app)
    resp = c.get("/foo%40bar", "http://localhost/bar%40baz")
    assert resp.text == "/foo@bar\n/bar@baz"

def test_multiple_cookies():

    @Request.application
    def test_app(request):
        response = Response(repr(sorted(request.cookies.items())))
        response.set_cookie("test1", "foo")
        response.set_cookie("test2", "bar")
        return response

    client = Client(test_app)
    resp = client.get("/")
    assert resp.text == "[]"
    resp = client.get("/")
    assert resp.text == repr([("test1", "foo"), ("test2", "bar")])

def test_full_url_requests_with_args():
    base = "http://example.com/"

    @Request.application
    def test_app(request):
        return Response(request.args["x"])

    client = Client(test_app)
    resp = client.get("/?x=42", base)
    assert resp.text == "42"
    resp = client.get("http://www.example.com/?x=23", base)
    assert resp.text == "23"

def test_content_type():

    @Request.application
    def test_app(request):
        return Response(request.content_type)

    client = Client(test_app)
    resp = client.get("/", data=b"testing", mimetype="text/css")
    assert resp.text == "text/css; charset=utf-8"
    resp = client.get("/", data=b"testing", mimetype="application/octet-stream")
    assert resp.text == "application/octet-stream"

def test_raw_request_uri():

    @Request.application
    def app(request):
        path_info = request.path
        request_uri = request.environ["REQUEST_URI"]
        return Response("\n".join((path_info, request_uri)))

    client = Client(app)
    response = client.get("/hello%2fworld")
    data = response.text
    assert data == "/hello/world\n/hello%2fworld"
    response = client.get("/?a=b")
    assert response.text == "/\n/?a=b"
    response = client.get("/%3f?")
    assert response.text == "/?\n/%3f?"

def test_responder():

    def foo(environ, start_response):
        return Response(b"Test")

    client = Client(wsgi.responder(foo))
    response = client.get("/")
    assert response.status_code == 200
    assert response.data == b"Test"

@pytest.mark.parametrize(
    ("path", "base_url", "absolute_location"),
    [
        ("foo", "http://example.org/app", "http://example.org/app/foo/"),
        ("/foo", "http://example.org/app", "http://example.org/app/foo/"),
        ("/foo/bar", "http://example.org/", "http://example.org/foo/bar/"),
        ("/foo/bar", "http://example.org/app", "http://example.org/app/foo/bar/"),
        ("/foo?baz", "http://example.org/", "http://example.org/foo/?baz"),
        ("/foo/", "http://example.org/", "http://example.org/foo/"),
        ("/foo/", "http://example.org/app", "http://example.org/app/foo/"),
        ("/", "http://example.org/", "http://example.org/"),
        ("/", "http://example.org/app", "http://example.org/app/"),
    ],
)
@pytest.mark.parametrize("autocorrect", [False, True])
def test_append_slash_redirect(autocorrect, path, base_url, absolute_location):

    @Request.application
    def app(request):
        rv = utils.append_slash_redirect(request.environ)
        rv.autocorrect_location_header = autocorrect
        return rv

    client = Client(app)
    response = client.get(path, base_url=base_url)
    assert response.status_code == 308
    if not autocorrect:
        assert response.headers["Location"].count("/") == 1
    else:
        assert response.headers["Location"] == absolute_location

def test_base_request():
    client = Client(request_demo_app)
    response = client.get("/?foo=bar&foo=hehe")
    request = response.request
    assert request.args == MultiDict([("foo", "bar"), ("foo", "hehe")])
    assert request.form == MultiDict()
    assert request.data == b""
    assert_environ(request.environ, "GET")
    response = client.post(
        "/?blub=blah",
        data="foo=blub+hehe&blah=42",
        content_type="application/x-www-form-urlencoded",
    )
    request = response.request
    assert request.args == MultiDict([("blub", "blah")])
    assert request.form == MultiDict([("foo", "blub hehe"), ("blah", "42")])
    assert request.data == b""
    assert_environ(request.environ, "POST")
    response = client.patch(
        "/?blub=blah",
        data="foo=blub+hehe&blah=42",
        content_type="application/x-www-form-urlencoded",
    )
    request = response.request
    assert request.args == MultiDict([("blub", "blah")])
    assert request.form == MultiDict([("foo", "blub hehe"), ("blah", "42")])
    assert request.data == b""
    assert_environ(request.environ, "PATCH")
    json = b'{"foo": "bar", "blub": "blah"}'
    response = client.post("/?a=b", data=json, content_type="application/json")
    request = response.request
    assert request.data == json
    assert request.args == MultiDict([("a", "b")])
    assert request.form == MultiDict()

@pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")
@pytest.mark.dev_server
def test_http_proxy(standard_app):
    app = ProxyMiddleware(
        Response("ROOT"),
        {
            "/foo": {
                "target": standard_app.url,
                "host": "faked.invalid",
                "headers": {"X-Special": "foo"},
            },
            "/bar": {
                "target": standard_app.url,
                "host": None,
                "remove_prefix": True,
                "headers": {"X-Special": "bar"},
            },
            "/autohost": {"target": standard_app.url},
        },
    )
    client = Client(app)
    r = client.get("/")
    assert r.data == b"ROOT"
    r = client.get("/foo/bar")
    assert r.json["HTTP_X_SPECIAL"] == "foo"
    assert r.json["HTTP_HOST"] == "faked.invalid"
    assert r.json["PATH_INFO"] == "/foo/bar"
    r = client.get("/bar/baz?a=a&b=b")
    assert r.json["HTTP_X_SPECIAL"] == "bar"
    assert r.json["HTTP_HOST"] == "localhost"
    assert r.json["PATH_INFO"] == "/baz"
    assert r.json["QUERY_STRING"] == "a=a&b=b"
    r = client.get("/autohost/aha")
    assert "HTTP_X_SPECIAL" not in r.json
    assert r.json["HTTP_HOST"] == "127.0.0.1"
    assert r.json["PATH_INFO"] == "/autohost/aha"
    r = client.get("/autohost/$")
    assert r.json["REQUEST_URI"] == "/autohost/$"

def test_filename_format_function():
    mock_capture_name = MagicMock()

    def filename_format(env):
        now = datetime.datetime.fromtimestamp(env["werkzeug.profiler"]["time"])
        timestamp = now.strftime("%Y-%m-%d:%H:%M:%S")
        path = (
            "_".join(token for token in env["PATH_INFO"].split("/") if token) or "ROOT"
        )
        elapsed = env["werkzeug.profiler"]["elapsed"]
        name = f"{timestamp}.{env['REQUEST_METHOD']}.{path}.{elapsed:.0f}ms.prof"
        mock_capture_name(name=name)
        return name

    client = Client(
        ProfilerMiddleware(
            dummy_application,
            stream=None,
            profile_dir="profiles",
            filename_format=filename_format,
        )
    )
    mock_profile = MagicMock(wraps=Profile())
    mock_profile.dump_stats = MagicMock()
    with patch("werkzeug.middleware.profiler.Profile", lambda: mock_profile):
        client.get("/foo/bar")
        mock_capture_name.assert_called_once_with(name=ANY)
        name = mock_capture_name.mock_calls[0].kwargs["name"]
        mock_profile.dump_stats.assert_called_once_with(os.path.join("profiles", name))