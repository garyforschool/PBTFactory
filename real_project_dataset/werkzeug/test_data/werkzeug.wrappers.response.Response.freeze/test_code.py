def test_etag_response_freezing():
    response = Response("Hello World")
    response.freeze()
    assert response.get_etag() == (str(generate_etag(b"Hello World")), False)

def test_response_freeze():

    def generate():
        yield "foo"
        yield "bar"

    resp = wrappers.Response(generate())
    resp.freeze()
    assert resp.response == [b"foo", b"bar"]
    assert resp.headers["content-length"] == "6"