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

def test_auto_content_length():
    resp = wrappers.Response("Hello World!")
    assert resp.content_length == 12
    resp = wrappers.Response(["Hello World!"])
    assert resp.content_length is None
    assert resp.get_wsgi_headers({})["Content-Length"] == "12"

def test_stream_content_length():
    resp = wrappers.Response()
    resp.stream.writelines(["foo", "bar", "baz"])
    assert resp.get_wsgi_headers({})["Content-Length"] == "9"
    resp = wrappers.Response()
    resp.make_conditional({"REQUEST_METHOD": "GET"})
    resp.stream.writelines(["foo", "bar", "baz"])
    assert resp.get_wsgi_headers({})["Content-Length"] == "9"
    resp = wrappers.Response("foo")
    resp.stream.writelines(["bar", "baz"])
    assert resp.get_wsgi_headers({})["Content-Length"] == "9"

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