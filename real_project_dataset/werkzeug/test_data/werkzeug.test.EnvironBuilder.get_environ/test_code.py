def test_no_cache_conditional_default():
    rv = send_file(
        txt_path,
        EnvironBuilder(
            headers={"If-Modified-Since": http_date(datetime.datetime(2020, 7, 12))}
        ).get_environ(),
        last_modified=datetime.datetime(2020, 7, 11),
    )
    rv.close()
    assert "no-cache" in rv.headers["Cache-Control"]
    assert not rv.cache_control.public
    assert not rv.cache_control.max_age
    assert not rv.expires
    assert rv.status_code == 304

def test_environ_builder_headers():
    b = EnvironBuilder(
        environ_base={"HTTP_USER_AGENT": "Foo/0.1"},
        environ_overrides={"wsgi.version": (1, 1)},
    )
    b.headers["X-Beat-My-Horse"] = "very well sir"
    env = b.get_environ()
    assert env["HTTP_USER_AGENT"] == "Foo/0.1"
    assert env["HTTP_X_BEAT_MY_HORSE"] == "very well sir"
    assert env["wsgi.version"] == (1, 1)
    b.headers["User-Agent"] = "Bar/1.0"
    env = b.get_environ()
    assert env["HTTP_USER_AGENT"] == "Bar/1.0"

def test_environ_builder_headers_content_type():
    b = EnvironBuilder(headers={"Content-Type": "text/plain"})
    env = b.get_environ()
    assert env["CONTENT_TYPE"] == "text/plain"
    assert "HTTP_CONTENT_TYPE" not in env
    b = EnvironBuilder(content_type="text/html", headers={"Content-Type": "text/plain"})
    env = b.get_environ()
    assert env["CONTENT_TYPE"] == "text/html"
    assert "HTTP_CONTENT_TYPE" not in env
    b = EnvironBuilder()
    env = b.get_environ()
    assert "CONTENT_TYPE" not in env
    assert "HTTP_CONTENT_TYPE" not in env

def test_envrion_builder_multiple_headers():
    h = Headers()
    h.add("FOO", "bar")
    h.add("FOO", "baz")
    b = EnvironBuilder(headers=h)
    env = b.get_environ()
    assert env["HTTP_FOO"] == "bar, baz"

def test_environ_builder_paths():
    b = EnvironBuilder(path="/foo", base_url="http://example.com/")
    assert b.base_url == "http://example.com/"
    assert b.path == "/foo"
    assert b.script_root == ""
    assert b.host == "example.com"
    b = EnvironBuilder(path="/foo", base_url="http://example.com/bar")
    assert b.base_url == "http://example.com/bar/"
    assert b.path == "/foo"
    assert b.script_root == "/bar"
    assert b.host == "example.com"
    b.host = "localhost"
    assert b.base_url == "http://localhost/bar/"
    b.base_url = "http://localhost:8080/"
    assert b.host == "localhost:8080"
    assert b.server_name == "localhost"
    assert b.server_port == 8080
    b.host = "foo.invalid"
    b.url_scheme = "https"
    b.script_root = "/test"
    env = b.get_environ()
    assert env["SERVER_NAME"] == "foo.invalid"
    assert env["SERVER_PORT"] == "443"
    assert env["SCRIPT_NAME"] == "/test"
    assert env["PATH_INFO"] == "/foo"
    assert env["HTTP_HOST"] == "foo.invalid"
    assert env["wsgi.url_scheme"] == "https"
    assert b.base_url == "https://foo.invalid/test/"

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