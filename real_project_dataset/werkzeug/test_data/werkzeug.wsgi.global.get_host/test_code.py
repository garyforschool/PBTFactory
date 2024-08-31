@pytest.mark.parametrize(
    ("environ", "expect"),
    (
        pytest.param({"HTTP_HOST": "spam"}, "spam", id="host"),
        pytest.param({"HTTP_HOST": "spam:80"}, "spam", id="host, strip http port"),
        pytest.param(
            {"wsgi.url_scheme": "https", "HTTP_HOST": "spam:443"},
            "spam",
            id="host, strip https port",
        ),
        pytest.param({"HTTP_HOST": "spam:8080"}, "spam:8080", id="host, custom port"),
        pytest.param(
            {"HTTP_HOST": "spam", "SERVER_NAME": "eggs", "SERVER_PORT": "80"},
            "spam",
            id="prefer host",
        ),
        pytest.param(
            {"SERVER_NAME": "eggs", "SERVER_PORT": "80"},
            "eggs",
            id="name, ignore http port",
        ),
        pytest.param(
            {"wsgi.url_scheme": "https", "SERVER_NAME": "eggs", "SERVER_PORT": "443"},
            "eggs",
            id="name, ignore https port",
        ),
        pytest.param(
            {"SERVER_NAME": "eggs", "SERVER_PORT": "8080"},
            "eggs:8080",
            id="name, custom port",
        ),
        pytest.param(
            {"HTTP_HOST": "ham", "HTTP_X_FORWARDED_HOST": "eggs"},
            "ham",
            id="ignore x-forwarded-host",
        ),
    ),
)
def test_get_host(environ, expect):
    environ.setdefault("wsgi.url_scheme", "http")
    assert wsgi.get_host(environ) == expect

def test_get_host_validate_trusted_hosts():
    env = {"SERVER_NAME": "example.org", "SERVER_PORT": "80", "wsgi.url_scheme": "http"}
    assert wsgi.get_host(env, trusted_hosts=[".example.org"]) == "example.org"
    pytest.raises(BadRequest, wsgi.get_host, env, trusted_hosts=["example.com"])
    env["SERVER_PORT"] = "8080"
    assert wsgi.get_host(env, trusted_hosts=[".example.org:8080"]) == "example.org:8080"
    pytest.raises(BadRequest, wsgi.get_host, env, trusted_hosts=[".example.com"])
    env = {"HTTP_HOST": "example.org", "wsgi.url_scheme": "http"}
    assert wsgi.get_host(env, trusted_hosts=[".example.org"]) == "example.org"
    pytest.raises(BadRequest, wsgi.get_host, env, trusted_hosts=["example.com"])

def test_get_host_fallback():
    assert (
        wsgi.get_host(
            {
                "SERVER_NAME": "foobar.example.com",
                "wsgi.url_scheme": "http",
                "SERVER_PORT": "80",
            }
        )
        == "foobar.example.com"
    )
    assert (
        wsgi.get_host(
            {
                "SERVER_NAME": "foobar.example.com",
                "wsgi.url_scheme": "http",
                "SERVER_PORT": "81",
            }
        )
        == "foobar.example.com:81"
    )