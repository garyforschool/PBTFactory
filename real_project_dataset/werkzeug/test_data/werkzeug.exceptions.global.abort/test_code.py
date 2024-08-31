def test_proxy_exception():
    orig_resp = Response("Hello World")
    with pytest.raises(exceptions.HTTPException) as excinfo:
        exceptions.abort(orig_resp)
    resp = excinfo.value.get_response({})
    assert resp is orig_resp
    assert resp.get_data() == b"Hello World"

@pytest.mark.parametrize(
    "test",
    [
        (exceptions.BadRequest, 400),
        (exceptions.Unauthorized, 401, 'Basic "test realm"'),
        (exceptions.Forbidden, 403),
        (exceptions.NotFound, 404),
        (exceptions.MethodNotAllowed, 405, ["GET", "HEAD"]),
        (exceptions.NotAcceptable, 406),
        (exceptions.RequestTimeout, 408),
        (exceptions.Gone, 410),
        (exceptions.LengthRequired, 411),
        (exceptions.PreconditionFailed, 412),
        (exceptions.RequestEntityTooLarge, 413),
        (exceptions.RequestURITooLarge, 414),
        (exceptions.UnsupportedMediaType, 415),
        (exceptions.UnprocessableEntity, 422),
        (exceptions.Locked, 423),
        (exceptions.InternalServerError, 500),
        (exceptions.NotImplemented, 501),
        (exceptions.BadGateway, 502),
        (exceptions.ServiceUnavailable, 503),
    ],
)
def test_aborter_general(test):
    exc_type = test[0]
    args = test[1:]
    with pytest.raises(exc_type) as exc_info:
        exceptions.abort(*args)
    assert type(exc_info.value) is exc_type

def test_abort_description_markup():
    with pytest.raises(HTTPException) as exc_info:
        exceptions.abort(400, Markup("<b>&lt;</b>"))
    assert "<b>&lt;</b>" in str(exc_info.value)