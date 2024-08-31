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