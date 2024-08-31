def test_environ_builder_stream_switch():
    d = MultiDict(dict(foo="bar", blub="blah", hu="hum"))
    for use_tempfile in (False, True):
        stream, length, boundary = stream_encode_multipart(
            d, use_tempfile, threshold=150
        )
        assert isinstance(stream, BytesIO) != use_tempfile
        form = parse_form_data(
            {
                "wsgi.input": stream,
                "CONTENT_LENGTH": str(length),
                "CONTENT_TYPE": f'multipart/form-data; boundary="{boundary}"',
            }
        )[1]
        assert form == d
        stream.close()

def test_environ_builder_unicode_file_mix():
    for use_tempfile in (False, True):
        f = FileStorage(BytesIO(b"\\N{SNOWMAN}"), "snowman.txt")
        d = MultiDict(dict(f=f, s="☃"))
        stream, length, boundary = stream_encode_multipart(
            d, use_tempfile, threshold=150
        )
        assert isinstance(stream, BytesIO) != use_tempfile
        _, form, files = parse_form_data(
            {
                "wsgi.input": stream,
                "CONTENT_LENGTH": str(length),
                "CONTENT_TYPE": f'multipart/form-data; boundary="{boundary}"',
            }
        )
        assert form["s"] == "☃"
        assert files["f"].name == "f"
        assert files["f"].filename == "snowman.txt"
        assert files["f"].read() == b"\\N{SNOWMAN}"
        stream.close()
        files["f"].close()

def test_environ_builder_empty_file():
    f = FileStorage(BytesIO(b""), "empty.txt")
    d = MultiDict(dict(f=f, s=""))
    stream, length, boundary = stream_encode_multipart(d)
    _, form, files = parse_form_data(
        {
            "wsgi.input": stream,
            "CONTENT_LENGTH": str(length),
            "CONTENT_TYPE": f'multipart/form-data; boundary="{boundary}"',
        }
    )
    assert form["s"] == ""
    assert files["f"].read() == b""
    stream.close()
    files["f"].close()

def test_parse_form_data_put_without_content(self):
        env = create_environ("/foo", "http://example.org/", method="PUT")
        stream, form, files = formparser.parse_form_data(env)
        assert stream.read() == b""
        assert len(form) == 0
        assert len(files) == 0

def test_parse_form_data_get_without_content(self):
        env = create_environ("/foo", "http://example.org/", method="GET")
        stream, form, files = formparser.parse_form_data(env)
        assert stream.read() == b""
        assert len(form) == 0
        assert len(files) == 0

def test_empty_multipart(self):
        environ = {}
        data = b"--boundary--"
        environ["REQUEST_METHOD"] = "POST"
        environ["CONTENT_TYPE"] = "multipart/form-data; boundary=boundary"
        environ["CONTENT_LENGTH"] = str(len(data))
        environ["wsgi.input"] = io.BytesIO(data)
        stream, form, files = parse_form_data(environ, silent=False)
        rv = stream.read()
        assert rv == b""
        assert form == MultiDict()
        assert files == MultiDict()