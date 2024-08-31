def test_response_iter_wrapping():

    def uppercasing(iterator):
        for item in iterator:
            yield item.upper()

    def generator():
        yield "foo"
        yield "bar"

    req = wrappers.Request.from_values()
    resp = wrappers.Response(generator())
    del resp.headers["Content-Length"]
    resp.response = uppercasing(resp.iter_encoded())
    actual_resp = wrappers.Response.from_app(resp, req.environ, buffered=True)
    assert actual_resp.get_data() == b"FOOBAR"