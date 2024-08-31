def test_cookie_duplicate_names_different_domains(self):
        key = "some_cookie"
        value = "some_value"
        domain1 = "test1.com"
        domain2 = "test2.com"
        jar = requests.cookies.RequestsCookieJar()
        jar.set(key, value, domain=domain1)
        jar.set(key, value, domain=domain2)
        assert key in jar
        items = jar.items()
        assert len(items) == 2
        with pytest.raises(requests.cookies.CookieConflictError):
            jar.get(key)
        cookie = jar.get(key, domain=domain1)
        assert cookie == value

def test_cookie_duplicate_names_raises_cookie_conflict_error(self):
        key = "some_cookie"
        value = "some_value"
        path = "some_path"
        jar = requests.cookies.RequestsCookieJar()
        jar.set(key, value, path=path)
        jar.set(key, value)
        with pytest.raises(requests.cookies.CookieConflictError):
            jar.get(key)