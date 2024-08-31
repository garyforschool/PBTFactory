def test_environ_builder_basics():
    b = EnvironBuilder()
    assert b.content_type is None
    b.method = "POST"
    assert b.content_type is None
    b.form["test"] = "normal value"
    assert b.content_type == "application/x-www-form-urlencoded"
    b.files.add_file("test", BytesIO(b"test contents"), "test.txt")
    assert b.files["test"].content_type == "text/plain"
    b.form["test_int"] = 1
    assert b.content_type == "multipart/form-data"
    req = b.get_request()
    b.close()
    assert req.url == "http://localhost/"
    assert req.method == "POST"
    assert req.form["test"] == "normal value"
    assert req.files["test"].content_type == "text/plain"
    assert req.files["test"].filename == "test.txt"
    assert req.files["test"].read() == b"test contents"
    req.close()

def test_environ_builder_content_type():
    builder = EnvironBuilder()
    assert builder.content_type is None
    builder.method = "POST"
    assert builder.content_type is None
    builder.method = "PUT"
    assert builder.content_type is None
    builder.method = "PATCH"
    assert builder.content_type is None
    builder.method = "DELETE"
    assert builder.content_type is None
    builder.method = "GET"
    assert builder.content_type is None
    builder.form["foo"] = "bar"
    assert builder.content_type == "application/x-www-form-urlencoded"
    builder.files.add_file("data", BytesIO(b"foo"), "test.txt")
    assert builder.content_type == "multipart/form-data"
    req = builder.get_request()
    builder.close()
    assert req.form["foo"] == "bar"
    assert req.files["data"].read() == b"foo"
    req.close()

def test_file_closing():
    closed = []

    class SpecialInput:

        def read(self, size):
            return b""

        def close(self):
            closed.append(self)

    create_environ(data={"foo": SpecialInput()})
    assert len(closed) == 1
    builder = EnvironBuilder()
    builder.files.add_file("blah", SpecialInput())
    builder.close()
    assert len(closed) == 2