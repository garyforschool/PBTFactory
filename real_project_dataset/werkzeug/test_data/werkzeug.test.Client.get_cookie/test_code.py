def test_cookiejar_stores_cookie():
    c = Client(cookie_app)
    c.open()
    assert c.get_cookie("test") is not None

def test_cookie_default_path() -> None:

    @Request.application
    def app(request: Request) -> Response:
        r = Response()
        r.set_cookie("k", "v", path=None)
        return r

    c = Client(app)
    c.get("/nested/leaf")
    assert c.get_cookie("k") is None
    assert c.get_cookie("k", path="/nested") is not None
    c.get("/nested/dir/")
    assert c.get_cookie("k", path="/nested/dir") is not None