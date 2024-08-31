def test_method_not_allowed_methods():
    exc = exceptions.MethodNotAllowed(["GET", "HEAD", "POST"])
    h = dict(exc.get_headers({}))
    assert h["Allow"] == "GET, HEAD, POST"
    assert "The method is not allowed" in exc.get_description()