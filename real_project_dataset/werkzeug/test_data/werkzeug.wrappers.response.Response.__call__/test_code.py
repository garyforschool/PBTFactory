def cookie_app(environ, start_response):
    response = Response(environ.get("HTTP_COOKIE", "No Cookie"), mimetype="text/plain")
    response.set_cookie("test", "test")
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

def external_subdomain_redirect_demo_app(environ, start_response):
    if "test.example.com" in environ["HTTP_HOST"]:
        response = Response("redirected successfully to subdomain")
    else:
        response = redirect("http://test.example.com/login")
    return response(environ, start_response)

def multi_value_post_app(environ, start_response):
    req = Request(environ)
    assert req.form["field"] == "val1", req.form["field"]
    assert req.form.getlist("field") == ["val1", "val2"], req.form.getlist("field")
    response = Response("ok")
    return response(environ, start_response)

def local_redirect_app(environ, start_response):
        req = Request(environ)
        if "/from/location" in req.url:
            response = redirect("/to/location", Response=LocalResponse)
        else:
            response = Response(f"current path: {req.path}")
        return response(environ, start_response)

def no_response_headers_app(environ, start_response):
    response = Response("Response")
    response.headers.clear()
    return response(environ, start_response)