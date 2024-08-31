def test_range_wrapper():
    response = Response(b"Hello World")
    range_wrapper = _RangeWrapper(response.response, 6, 4)
    assert next(range_wrapper) == b"Worl"
    response = Response(b"Hello World")
    range_wrapper = _RangeWrapper(response.response, 1, 0)
    with pytest.raises(StopIteration):
        next(range_wrapper)
    response = Response(b"Hello World")
    range_wrapper = _RangeWrapper(response.response, 6, 100)
    assert next(range_wrapper) == b"World"
    response = Response(x for x in (b"He", b"ll", b"o ", b"Wo", b"rl", b"d"))
    range_wrapper = _RangeWrapper(response.response, 6, 4)
    assert not range_wrapper.seekable
    assert next(range_wrapper) == b"Wo"
    assert next(range_wrapper) == b"rl"
    response = Response(x for x in (b"He", b"ll", b"o W", b"o", b"rld"))
    range_wrapper = _RangeWrapper(response.response, 6, 4)
    assert next(range_wrapper) == b"W"
    assert next(range_wrapper) == b"o"
    assert next(range_wrapper) == b"rl"
    with pytest.raises(StopIteration):
        next(range_wrapper)
    response = Response(x for x in (b"Hello", b" World"))
    range_wrapper = _RangeWrapper(response.response, 1, 1)
    assert next(range_wrapper) == b"e"
    with pytest.raises(StopIteration):
        next(range_wrapper)
    resources = os.path.join(os.path.dirname(__file__), "res")
    env = create_environ()
    with open(os.path.join(resources, "test.txt"), "rb") as f:
        response = Response(wrap_file(env, f))
        range_wrapper = _RangeWrapper(response.response, 1, 2)
        assert range_wrapper.seekable
        assert next(range_wrapper) == b"OU"
        with pytest.raises(StopIteration):
            next(range_wrapper)
    with open(os.path.join(resources, "test.txt"), "rb") as f:
        response = Response(wrap_file(env, f))
        range_wrapper = _RangeWrapper(response.response, 2)
        assert next(range_wrapper) == b"UND\n"
        with pytest.raises(StopIteration):
            next(range_wrapper)

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