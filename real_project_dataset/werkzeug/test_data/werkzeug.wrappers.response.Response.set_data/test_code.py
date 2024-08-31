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

def test_malformed_204_response_has_no_content_length():
    response = wrappers.Response(status=204)
    response.set_data(b"test")
    assert response.content_length == 4
    env = create_environ()
    app_iter, status, headers = response.get_wsgi_response(env)
    assert status == "204 NO CONTENT"
    assert "Content-Length" not in headers
    assert b"".join(app_iter) == b""