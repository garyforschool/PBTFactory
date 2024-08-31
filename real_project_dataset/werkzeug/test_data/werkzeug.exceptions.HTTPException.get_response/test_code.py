def test_response_header_content_type_should_contain_charset():
    exc = exceptions.HTTPException("An error message")
    h = exc.get_response({})
    assert h.headers["Content-Type"] == "text/html; charset=utf-8"

def test_description_none():
    HTTPException().get_response()