def test_basic_routing():
    map = r.Map(
        [
            r.Rule("/", endpoint="index"),
            r.Rule("/foo", endpoint="foo"),
            r.Rule("/bar/", endpoint="bar"),
            r.Rule("/ws", endpoint="ws", websocket=True),
            r.Rule("/", endpoint="indexws", websocket=True),
        ]
    )
    adapter = map.bind("example.org", "/")
    assert adapter.match("/") == ("index", {})
    assert adapter.match("/foo") == ("foo", {})
    assert adapter.match("/bar/") == ("bar", {})
    pytest.raises(r.RequestRedirect, lambda: adapter.match("/bar"))
    pytest.raises(NotFound, lambda: adapter.match("/blub"))
    adapter = map.bind("example.org", "/", url_scheme="ws")
    assert adapter.match("/") == ("indexws", {})
    adapter = map.bind("example.org", "/test")
    with pytest.raises(r.RequestRedirect) as excinfo:
        adapter.match("/bar")
    assert excinfo.value.new_url == "http://example.org/test/bar/"
    adapter = map.bind("example.org", "/")
    with pytest.raises(r.RequestRedirect) as excinfo:
        adapter.match("/bar")
    assert excinfo.value.new_url == "http://example.org/bar/"
    adapter = map.bind("example.org", "/")
    with pytest.raises(r.RequestRedirect) as excinfo:
        adapter.match("/bar", query_args={"aha": "muhaha"})
    assert excinfo.value.new_url == "http://example.org/bar/?aha=muhaha"
    adapter = map.bind("example.org", "/")
    with pytest.raises(r.RequestRedirect) as excinfo:
        adapter.match("/bar", query_args="aha=muhaha")
    assert excinfo.value.new_url == "http://example.org/bar/?aha=muhaha"
    adapter = map.bind_to_environ(create_environ("/bar?foo=bar", "http://example.org/"))
    with pytest.raises(r.RequestRedirect) as excinfo:
        adapter.match()
    assert excinfo.value.new_url == "http://example.org/bar/?foo=bar"
    adapter = map.bind("example.org", "/ws", url_scheme="wss")
    assert adapter.match("/ws", websocket=True) == ("ws", {})
    with pytest.raises(r.WebsocketMismatch):
        adapter.match("/ws", websocket=False)
    with pytest.raises(r.WebsocketMismatch):
        adapter.match("/foo", websocket=True)
    adapter = map.bind_to_environ(
        create_environ(
            "/ws?foo=bar",
            "http://example.org/",
            headers=[("Connection", "Upgrade"), ("upgrade", "WebSocket")],
        )
    )
    assert adapter.match("/ws") == ("ws", {})
    with pytest.raises(r.WebsocketMismatch):
        adapter.match("/ws", websocket=False)
    adapter = map.bind_to_environ(
        create_environ(
            "/ws?foo=bar",
            "http://example.org/",
            headers=[("Connection", "keep-alive, Upgrade"), ("upgrade", "websocket")],
        )
    )
    assert adapter.match("/ws") == ("ws", {})
    with pytest.raises(r.WebsocketMismatch):
        adapter.match("/ws", websocket=False)

def test_environ_defaults():
    environ = create_environ("/foo")
    assert environ["PATH_INFO"] == "/foo"
    m = r.Map([r.Rule("/foo", endpoint="foo"), r.Rule("/bar", endpoint="bar")])
    a = m.bind_to_environ(environ)
    assert a.match("/foo") == ("foo", {})
    assert a.match() == ("foo", {})
    assert a.match("/bar") == ("bar", {})
    pytest.raises(NotFound, a.match, "/bars")

def test_environ_nonascii_pathinfo():
    environ = create_environ("/лошадь")
    m = r.Map([r.Rule("/", endpoint="index"), r.Rule("/лошадь", endpoint="horse")])
    a = m.bind_to_environ(environ)
    assert a.match("/") == ("index", {})
    assert a.match("/лошадь") == ("horse", {})
    pytest.raises(NotFound, a.match, "/барсук")

def test_dispatch():
    env = create_environ("/")
    map = r.Map([r.Rule("/", endpoint="root"), r.Rule("/foo/", endpoint="foo")])
    adapter = map.bind_to_environ(env)
    raise_this = None

    def view_func(endpoint, values):
        if raise_this is not None:
            raise raise_this
        return Response(repr((endpoint, values)))

    def dispatch(path, quiet=False):
        return Response.force_type(
            adapter.dispatch(view_func, path, catch_http_exceptions=quiet), env
        )

    assert dispatch("/").data == b"('root', {})"
    assert dispatch("/foo").status_code == 308
    raise_this = NotFound()
    pytest.raises(NotFound, lambda: dispatch("/bar"))
    assert dispatch("/bar", True).status_code == 404

def test_http_host_before_server_name():
    env = {
        "HTTP_HOST": "wiki.example.com",
        "SERVER_NAME": "web0.example.com",
        "SERVER_PORT": "80",
        "SCRIPT_NAME": "",
        "PATH_INFO": "",
        "REQUEST_METHOD": "GET",
        "wsgi.url_scheme": "http",
    }
    map = r.Map([r.Rule("/", endpoint="index", subdomain="wiki")])
    adapter = map.bind_to_environ(env, server_name="example.com")
    assert adapter.match("/") == ("index", {})
    assert adapter.build("index", force_external=True) == "http://wiki.example.com/"
    assert adapter.build("index") == "/"
    env["HTTP_HOST"] = "admin.example.com"
    adapter = map.bind_to_environ(env, server_name="example.com")
    assert adapter.build("index") == "http://wiki.example.com/"

def test_invalid_subdomain_warning():
    env = create_environ("/foo")
    env["SERVER_NAME"] = env["HTTP_HOST"] = "foo.example.com"
    m = r.Map([r.Rule("/foo", endpoint="foo")])
    with pytest.warns(UserWarning) as record:
        a = m.bind_to_environ(env, server_name="bar.example.com")
    assert a.subdomain == "<invalid>"
    assert len(record) == 1

@pytest.mark.parametrize(
    ("base", "name"),
    (("http://localhost", "localhost:80"), ("https://localhost", "localhost:443")),
)
def test_server_name_match_default_port(base, name):
    environ = create_environ("/foo", base_url=base)
    map = r.Map([r.Rule("/foo", endpoint="foo")])
    adapter = map.bind_to_environ(environ, server_name=name)
    assert adapter.match() == ("foo", {})

def test_server_name_interpolation():
    server_name = "example.invalid"
    map = r.Map(
        [r.Rule("/", endpoint="index"), r.Rule("/", endpoint="alt", subdomain="alt")]
    )
    env = create_environ("/", f"http://{server_name}/")
    adapter = map.bind_to_environ(env, server_name=server_name)
    assert adapter.match() == ("index", {})
    env = create_environ("/", f"http://alt.{server_name}/")
    adapter = map.bind_to_environ(env, server_name=server_name)
    assert adapter.match() == ("alt", {})
    env = create_environ("/", f"http://{server_name}/")
    with pytest.warns(UserWarning):
        adapter = map.bind_to_environ(env, server_name="foo")
    assert adapter.subdomain == "<invalid>"

def test_external_building_with_port_bind_to_environ():
    map = r.Map([r.Rule("/", endpoint="index")])
    adapter = map.bind_to_environ(
        create_environ("/", "http://example.org:5000/"), server_name="example.org:5000"
    )
    built_url = adapter.build("index", {}, force_external=True)
    assert built_url == "http://example.org:5000/", built_url

def test_external_building_with_port_bind_to_environ_wrong_servername():
    map = r.Map([r.Rule("/", endpoint="index")])
    environ = create_environ("/", "http://example.org:5000/")
    with pytest.warns(UserWarning):
        adapter = map.bind_to_environ(environ, server_name="example.org")
    assert adapter.subdomain == "<invalid>"

def test_server_name_casing():
    m = r.Map([r.Rule("/", endpoint="index", subdomain="foo")])
    env = create_environ()
    env["SERVER_NAME"] = env["HTTP_HOST"] = "FOO.EXAMPLE.COM"
    a = m.bind_to_environ(env, server_name="example.com")
    assert a.match("/") == ("index", {})
    env = create_environ()
    env["SERVER_NAME"] = "127.0.0.1"
    env["SERVER_PORT"] = "5000"
    del env["HTTP_HOST"]
    with pytest.warns(UserWarning):
        a = m.bind_to_environ(env, server_name="example.com")
    with pytest.raises(NotFound):
        a.match()