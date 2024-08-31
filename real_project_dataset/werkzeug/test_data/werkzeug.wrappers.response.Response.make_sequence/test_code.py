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