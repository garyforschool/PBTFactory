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

def test_response_stream():
    response = wrappers.Response()
    response.stream.write("Hello ")
    response.stream.write("World!")
    assert response.response == ["Hello ", "World!"]
    assert response.get_data() == b"Hello World!"

def test_new_response_iterator_behavior():
    req = wrappers.Request.from_values()
    resp = wrappers.Response("Hello Wörld!")

    def get_content_length(resp):
        headers = resp.get_wsgi_headers(req.environ)
        return headers.get("content-length", type=int)

    def generate_items():
        yield "Hello "
        yield "Wörld!"

    assert resp.response == ["Hello Wörld!".encode()]
    assert resp.get_data() == "Hello Wörld!".encode()
    assert get_content_length(resp) == 13
    assert not resp.is_streamed
    assert resp.is_sequence
    resp.set_data("Wörd")
    assert resp.response == ["Wörd".encode()]
    assert resp.get_data() == "Wörd".encode()
    assert get_content_length(resp) == 5
    assert not resp.is_streamed
    assert resp.is_sequence
    resp.response = generate_items()
    assert resp.is_streamed
    assert not resp.is_sequence
    assert resp.get_data() == "Hello Wörld!".encode()
    assert resp.response == [b"Hello ", "Wörld!".encode()]
    assert not resp.is_streamed
    assert resp.is_sequence
    resp.response = generate_items()
    resp.implicit_sequence_conversion = False
    assert resp.is_streamed
    assert not resp.is_sequence
    pytest.raises(RuntimeError, lambda: resp.get_data())
    resp.make_sequence()
    assert resp.get_data() == "Hello Wörld!".encode()
    assert resp.response == [b"Hello ", "Wörld!".encode()]
    assert not resp.is_streamed
    assert resp.is_sequence
    for val in (True, False):
        resp.implicit_sequence_conversion = val
        resp.response = "foo", "bar"
        assert resp.is_sequence
        resp.stream.write("baz")
        assert resp.response == ["foo", "bar", "baz"]

assert resp.response == ["Hello Wörld!".encode()]
    assert resp.get_data() == "Hello Wörld!".encode()
    assert get_content_length(resp) == 13
    assert not resp.is_streamed
    assert resp.is_sequence
    resp.set_data("Wörd")
    assert resp.response == ["Wörd".encode()]
    assert resp.get_data() == "Wörd".encode()
    assert get_content_length(resp) == 5
    assert not resp.is_streamed
    assert resp.is_sequence
    resp.response = generate_items()
    assert resp.is_streamed
    assert not resp.is_sequence
    assert resp.get_data() == "Hello Wörld!".encode()
    assert resp.response == [b"Hello ", "Wörld!".encode()]
    assert not resp.is_streamed
    assert resp.is_sequence
    resp.response = generate_items()
    resp.implicit_sequence_conversion = False
    assert resp.is_streamed
    assert not resp.is_sequence
    pytest.raises(RuntimeError, lambda: resp.get_data())

def test_stream_zip():
    import zipfile

    response = wrappers.Response()
    with contextlib.closing(zipfile.ZipFile(response.stream, mode="w")) as z:
        z.writestr("foo", b"bar")
    buffer = BytesIO(response.get_data())
    with contextlib.closing(zipfile.ZipFile(buffer, mode="r")) as z:
        assert z.namelist() == ["foo"]
        assert z.read("foo") == b"bar"