def test_etag_response():
    response = wrappers.Response("Hello World")
    assert response.get_etag() == (None, None)
    response.add_etag()
    assert response.get_etag() == ("0a4d55a8d778e5022fab701977c5d840bbc486d0", False)
    assert not response.cache_control
    response.cache_control.must_revalidate = True
    response.cache_control.max_age = 60
    response.headers["Content-Length"] = len(response.get_data())
    assert response.headers["Cache-Control"] in (
        "must-revalidate, max-age=60",
        "max-age=60, must-revalidate",
    )
    assert "date" not in response.headers
    env = create_environ()
    env.update({"REQUEST_METHOD": "GET", "HTTP_IF_NONE_MATCH": response.get_etag()[0]})
    response.make_conditional(env)
    assert "date" in response.headers
    resp = wrappers.Response.from_app(response, env)
    assert resp.status_code == 304
    assert "content-length" not in resp.headers
    response = wrappers.Response("Hello World")
    response.date = 1337
    d = response.date
    response.make_conditional(env)
    assert response.date == d
    response = wrappers.Response("Hello World")
    response.content_length = 999
    response.make_conditional(env)
    assert response.content_length == 999

def test_etag_response_412():
    response = wrappers.Response("Hello World")
    assert response.get_etag() == (None, None)
    response.add_etag()
    assert response.get_etag() == ("0a4d55a8d778e5022fab701977c5d840bbc486d0", False)
    assert not response.cache_control
    response.cache_control.must_revalidate = True
    response.cache_control.max_age = 60
    response.headers["Content-Length"] = len(response.get_data())
    assert response.headers["Cache-Control"] in (
        "must-revalidate, max-age=60",
        "max-age=60, must-revalidate",
    )
    assert "date" not in response.headers
    env = create_environ()
    env.update(
        {"REQUEST_METHOD": "GET", "HTTP_IF_MATCH": f"{response.get_etag()[0]}xyz"}
    )
    response.make_conditional(env)
    assert "date" in response.headers
    resp = wrappers.Response.from_app(response, env)
    assert resp.status_code == 412
    assert resp.data != b""
    response = wrappers.Response("Hello World")
    response.date = 1337
    d = response.date
    response.make_conditional(env)
    assert response.date == d
    response = wrappers.Response("Hello World")
    response.content_length = 999
    response.make_conditional(env)
    assert response.content_length == 999

def test_etag_response_freezing():
    response = Response("Hello World")
    response.freeze()
    assert response.get_etag() == (str(generate_etag(b"Hello World")), False)