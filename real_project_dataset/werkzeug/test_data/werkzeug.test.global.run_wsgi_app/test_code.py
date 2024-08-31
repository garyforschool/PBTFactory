@pytest.mark.parametrize("buffered", (True, False))
@pytest.mark.parametrize("iterable", (True, False))
def test_run_wsgi_apps(buffered, iterable):
    leaked_data = []

    def simple_app(environ, start_response):
        start_response("200 OK", [("Content-Type", "text/html")])
        return ["Hello World!"]

    def yielding_app(environ, start_response):
        start_response("200 OK", [("Content-Type", "text/html")])
        yield "Hello "
        yield "World!"

    def late_start_response(environ, start_response):
        yield "Hello "
        yield "World"
        start_response("200 OK", [("Content-Type", "text/html")])
        yield "!"

    def depends_on_close(environ, start_response):
        leaked_data.append("harhar")
        start_response("200 OK", [("Content-Type", "text/html")])

        class Rv:

            def __iter__(self):
                yield "Hello "
                yield "World"
                yield "!"

            def close(self):
                assert leaked_data.pop() == "harhar"

        return Rv()

    for app in (simple_app, yielding_app, late_start_response, depends_on_close):
        if iterable:
            app = iterable_middleware(app)
        app_iter, status, headers = run_wsgi_app(app, {}, buffered=buffered)
        assert status == "200 OK"
        assert list(headers) == [("Content-Type", "text/html")]
        assert "".join(app_iter) == "Hello World!"
        if hasattr(app_iter, "close"):
            app_iter.close()
        assert not leaked_data

@pytest.mark.parametrize("buffered", (True, False))
@pytest.mark.parametrize("iterable", (True, False))
def test_lazy_start_response_empty_response_app(buffered, iterable):

    class app:

        def __init__(self, environ, start_response):
            self.start_response = start_response

        def __iter__(self):
            return self

        def __next__(self):
            self.start_response("200 OK", [("Content-Type", "text/html")])
            raise StopIteration

    if iterable:
        app = iterable_middleware(app)
    app_iter, status, headers = run_wsgi_app(app, {}, buffered=buffered)
    assert status == "200 OK"
    assert list(headers) == [("Content-Type", "text/html")]
    assert "".join(app_iter) == ""

def test_run_wsgi_app_closing_iterator():
    got_close = []

    class CloseIter:

        def __init__(self):
            self.iterated = False

        def __iter__(self):
            return self

        def close(self):
            got_close.append(None)

        def __next__(self):
            if self.iterated:
                raise StopIteration()
            self.iterated = True
            return "bar"

    def bar(environ, start_response):
        start_response("200 OK", [("Content-Type", "text/plain")])
        return CloseIter()

    app_iter, status, headers = run_wsgi_app(bar, {})
    assert status == "200 OK"
    assert list(headers) == [("Content-Type", "text/plain")]
    assert next(app_iter) == "bar"
    pytest.raises(StopIteration, partial(next, app_iter))
    app_iter.close()
    assert run_wsgi_app(bar, {}, True)[0] == ["bar"]
    assert len(got_close) == 2

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