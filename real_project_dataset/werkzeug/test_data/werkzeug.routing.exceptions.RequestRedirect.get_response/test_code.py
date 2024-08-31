def test_redirect_request_exception_code():
    exc = r.RequestRedirect("http://www.google.com/")
    exc.code = 307
    env = create_environ()
    assert exc.get_response(env).status_code == exc.code