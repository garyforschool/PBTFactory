def test_malformed_204_response_has_no_content_length():
    response = wrappers.Response(status=204)
    response.set_data(b"test")
    assert response.content_length == 4
    env = create_environ()
    app_iter, status, headers = response.get_wsgi_response(env)
    assert status == "204 NO CONTENT"
    assert "Content-Length" not in headers
    assert b"".join(app_iter) == b""