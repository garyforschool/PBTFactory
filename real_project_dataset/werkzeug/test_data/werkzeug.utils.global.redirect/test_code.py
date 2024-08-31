def redirect_loop_app(environ, start_response):
    response = redirect("http://localhost/some/redirect/")
    return response(environ, start_response)

def redirect_with_get_app(environ, start_response):
    req = Request(environ)
    if req.url not in (
        "http://localhost/",
        "http://localhost/first/request",
        "http://localhost/some/redirect/",
    ):
        raise AssertionError(f'redirect_demo_app() did not expect URL "{req.url}"')
    if "/some/redirect" not in req.url:
        response = redirect("http://localhost/some/redirect/")
    else:
        response = Response(f"current url: {req.url}")
    return response(environ, start_response)

def external_redirect_demo_app(environ, start_response):
    response = redirect("http://example.com/")
    return response(environ, start_response)

def external_subdomain_redirect_demo_app(environ, start_response):
    if "test.example.com" in environ["HTTP_HOST"]:
        response = Response("redirected successfully to subdomain")
    else:
        response = redirect("http://test.example.com/login")
    return response(environ, start_response)

def local_redirect_app(environ, start_response):
        req = Request(environ)
        if "/from/location" in req.url:
            response = redirect("/to/location", Response=LocalResponse)
        else:
            response = Response(f"current path: {req.path}")
        return response(environ, start_response)

@Request.application
    def app(request):
        if request.url == "http://localhost/some/redirect/":
            assert request.method == "POST" if keep else "GET"
            assert request.headers["X-Foo"] == "bar"
            if keep:
                assert request.form["foo"] == "bar"
            else:
                assert not request.form
            return Response(f"current url: {request.url}")
        return redirect("http://localhost/some/redirect/", code=code)

@pytest.mark.parametrize(
    ("url", "code", "expect"),
    [
        ("http://example.com", None, "http://example.com"),
        ("/füübär", 305, "/f%C3%BC%C3%BCb%C3%A4r"),
        ("http://☃.example.com/", 307, "http://xn--n3h.example.com/"),
        ("itms-services://?url=abc", None, "itms-services://?url=abc"),
    ],
)
def test_redirect(url: str, code: int | None, expect: str) -> None:
    environ = EnvironBuilder().get_environ()
    if code is None:
        resp = utils.redirect(url)
        assert resp.status_code == 302
    else:
        resp = utils.redirect(url, code)
        assert resp.status_code == code
    assert resp.headers["Location"] == url
    assert resp.get_wsgi_headers(environ)["Location"] == expect
    assert resp.get_data(as_text=True).count(url) == 2

def test_redirect_xss():
    location = 'http://example.com/?xss="><script>alert(1)</script>'
    resp = utils.redirect(location)
    assert b"<script>alert(1)</script>" not in resp.get_data()
    location = 'http://example.com/?xss="onmouseover="alert(1)'
    resp = utils.redirect(location)
    assert (
        b'href="http://example.com/?xss="onmouseover="alert(1)"' not in resp.get_data()
    )

def test_redirect_with_custom_response_class():

    class MyResponse(Response):
        pass

    location = "http://example.com/redirect"
    resp = utils.redirect(location, Response=MyResponse)
    assert isinstance(resp, MyResponse)
    assert resp.headers["Location"] == location