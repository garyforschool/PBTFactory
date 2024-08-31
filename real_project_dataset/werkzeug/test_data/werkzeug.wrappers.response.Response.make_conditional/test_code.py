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

def test_range_request_basic():
    env = create_environ()
    response = wrappers.Response("Hello World")
    env["HTTP_RANGE"] = "bytes=0-4"
    response.make_conditional(env, accept_ranges=True, complete_length=11)
    assert response.status_code == 206
    assert response.headers["Accept-Ranges"] == "bytes"
    assert response.headers["Content-Range"] == "bytes 0-4/11"
    assert response.headers["Content-Length"] == "5"
    assert response.data == b"Hello"

def test_range_request_out_of_bound():
    env = create_environ()
    response = wrappers.Response("Hello World")
    env["HTTP_RANGE"] = "bytes=6-666"
    response.make_conditional(env, accept_ranges=True, complete_length=11)
    assert response.status_code == 206
    assert response.headers["Accept-Ranges"] == "bytes"
    assert response.headers["Content-Range"] == "bytes 6-10/11"
    assert response.headers["Content-Length"] == "5"
    assert response.data == b"World"

def test_range_request_with_file():
    env = create_environ()
    resources = os.path.join(os.path.dirname(__file__), "res")
    fname = os.path.join(resources, "test.txt")
    with open(fname, "rb") as f:
        fcontent = f.read()
    with open(fname, "rb") as f:
        response = wrappers.Response(wrap_file(env, f))
        env["HTTP_RANGE"] = "bytes=0-0"
        response.make_conditional(
            env, accept_ranges=True, complete_length=len(fcontent)
        )
        assert response.status_code == 206
        assert response.headers["Accept-Ranges"] == "bytes"
        assert response.headers["Content-Range"] == f"bytes 0-0/{len(fcontent)}"
        assert response.headers["Content-Length"] == "1"
        assert response.data == fcontent[:1]

def test_range_request_with_complete_file():
    env = create_environ()
    resources = os.path.join(os.path.dirname(__file__), "res")
    fname = os.path.join(resources, "test.txt")
    with open(fname, "rb") as f:
        fcontent = f.read()
    with open(fname, "rb") as f:
        fsize = os.path.getsize(fname)
        response = wrappers.Response(wrap_file(env, f))
        env["HTTP_RANGE"] = f"bytes=0-{fsize - 1}"
        response.make_conditional(env, accept_ranges=True, complete_length=fsize)
        assert response.status_code == 206
        assert response.headers["Accept-Ranges"] == "bytes"
        assert response.headers["Content-Range"] == f"bytes 0-{fsize - 1}/{fsize}"
        assert response.headers["Content-Length"] == str(fsize)
        assert response.data == fcontent

@pytest.mark.parametrize("value", [None, 0])
def test_range_request_without_complete_length(value):
    env = create_environ(headers={"Range": "bytes=0-10"})
    response = wrappers.Response("Hello World")
    response.make_conditional(env, accept_ranges=True, complete_length=value)
    assert response.status_code == 200
    assert response.data == b"Hello World"

def test_invalid_range_request():
    env = create_environ()
    response = wrappers.Response("Hello World")
    env["HTTP_RANGE"] = "bytes=-"
    with pytest.raises(RequestedRangeNotSatisfiable):
        response.make_conditional(env, accept_ranges=True, complete_length=11)

def test_stream_content_length():
    resp = wrappers.Response()
    resp.stream.writelines(["foo", "bar", "baz"])
    assert resp.get_wsgi_headers({})["Content-Length"] == "9"
    resp = wrappers.Response()
    resp.make_conditional({"REQUEST_METHOD": "GET"})
    resp.stream.writelines(["foo", "bar", "baz"])
    assert resp.get_wsgi_headers({})["Content-Length"] == "9"
    resp = wrappers.Response("foo")
    resp.stream.writelines(["bar", "baz"])
    assert resp.get_wsgi_headers({})["Content-Length"] == "9"