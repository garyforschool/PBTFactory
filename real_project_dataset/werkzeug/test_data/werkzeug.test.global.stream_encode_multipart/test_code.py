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

@pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")
@pytest.mark.parametrize("send_length", [False, True])
@pytest.mark.dev_server
def test_chunked_request(monkeypatch, dev_server, send_length):
    stream, length, boundary = stream_encode_multipart(
        {
            "value": "this is text",
            "file": FileStorage(
                BytesIO(b"this is a file"),
                filename="test.txt",
                content_type="text/plain",
            ),
        }
    )
    client = dev_server("data")
    conn = client.connect(blocksize=128)
    conn.putrequest("POST", "/")
    conn.putheader("Transfer-Encoding", "chunked")
    conn.putheader("Content-Type", f"multipart/form-data; boundary={boundary}")
    if send_length:
        conn.putheader("Content-Length", "invalid")
        expect_content_len = "invalid"
    else:
        expect_content_len = None
    conn.endheaders(stream, encode_chunked=True)
    r = conn.getresponse()
    data = json.load(r)
    r.close()
    assert data["form"]["value"] == "this is text"
    assert data["files"]["file"] == "this is a file"
    environ = data["environ"]
    assert environ["HTTP_TRANSFER_ENCODING"] == "chunked"
    assert environ.get("CONTENT_LENGTH") == expect_content_len
    assert environ["wsgi.input_terminated"]