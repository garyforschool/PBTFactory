@pytest.mark.parametrize(
        "username, password",
        (("user", "pass"), ("имя".encode(), "пароль".encode()), (42, 42), (None, None)),
    )
    def test_set_basicauth(self, httpbin, username, password):
        auth = username, password
        url = httpbin("get")
        r = requests.Request("GET", url, auth=auth)
        p = r.prepare()
        assert p.headers["Authorization"] == _basic_auth_str(username, password)

@pytest.mark.parametrize(
        "username, password, auth_str",
        (
            ("test", "test", "Basic dGVzdDp0ZXN0"),
            ("имя".encode(), "пароль".encode(), "Basic 0LjQvNGPOtC/0LDRgNC+0LvRjA=="),
        ),
    )
    def test_basic_auth_str_is_always_native(self, username, password, auth_str):
        s = _basic_auth_str(username, password)
        assert isinstance(s, builtin_str)
        assert s == auth_str