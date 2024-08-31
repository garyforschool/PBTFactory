def cookie_app(environ, start_response):
    response = Response(environ.get("HTTP_COOKIE", "No Cookie"), mimetype="text/plain")
    response.set_cookie("test", "test")
    return response(environ, start_response)

@Request.application
    def app(request: Request) -> Response:
        r = Response()
        r.set_cookie("k", "v", path=None)
        return r

@Request.application
    def test_app(request):
        response = Response(repr(sorted(request.cookies.items())))
        response.set_cookie("test1", "foo")
        response.set_cookie("test2", "bar")
        return response

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

def test_secure(self):
        response = wrappers.Response()
        response.set_cookie(
            "foo",
            value="bar",
            max_age=60,
            expires=0,
            path="/blub",
            domain="example.org",
            secure=True,
            samesite=None,
        )
        assert response.headers.to_wsgi_list() == [
            ("Content-Type", "text/plain; charset=utf-8"),
            (
                "Set-Cookie",
                "foo=bar; Domain=example.org; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=60; Secure; Path=/blub",
            ),
        ]

def test_httponly(self):
        response = wrappers.Response()
        response.set_cookie(
            "foo",
            value="bar",
            max_age=60,
            expires=0,
            path="/blub",
            domain="example.org",
            secure=False,
            httponly=True,
            samesite=None,
        )
        assert response.headers.to_wsgi_list() == [
            ("Content-Type", "text/plain; charset=utf-8"),
            (
                "Set-Cookie",
                "foo=bar; Domain=example.org; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=60; HttpOnly; Path=/blub",
            ),
        ]

def test_secure_and_httponly(self):
        response = wrappers.Response()
        response.set_cookie(
            "foo",
            value="bar",
            max_age=60,
            expires=0,
            path="/blub",
            domain="example.org",
            secure=True,
            httponly=True,
            samesite=None,
        )
        assert response.headers.to_wsgi_list() == [
            ("Content-Type", "text/plain; charset=utf-8"),
            (
                "Set-Cookie",
                "foo=bar; Domain=example.org; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=60; Secure; HttpOnly; Path=/blub",
            ),
        ]

def test_samesite(self):
        response = wrappers.Response()
        response.set_cookie(
            "foo",
            value="bar",
            max_age=60,
            expires=0,
            path="/blub",
            domain="example.org",
            secure=False,
            samesite="strict",
        )
        assert response.headers.to_wsgi_list() == [
            ("Content-Type", "text/plain; charset=utf-8"),
            (
                "Set-Cookie",
                "foo=bar; Domain=example.org; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=60; Path=/blub; SameSite=Strict",
            ),
        ]