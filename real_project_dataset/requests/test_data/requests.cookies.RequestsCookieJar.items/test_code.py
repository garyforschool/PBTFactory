def test_cookie_as_dict_keeps_len(self):
        key = "some_cookie"
        value = "some_value"
        key1 = "some_cookie1"
        value1 = "some_value1"
        jar = requests.cookies.RequestsCookieJar()
        jar.set(key, value)
        jar.set(key1, value1)
        d1 = dict(jar)
        d2 = dict(jar.iteritems())
        d3 = dict(jar.items())
        assert len(jar) == 2
        assert len(d1) == 2
        assert len(d2) == 2
        assert len(d3) == 2

def test_cookie_as_dict_keeps_items(self):
        key = "some_cookie"
        value = "some_value"
        key1 = "some_cookie1"
        value1 = "some_value1"
        jar = requests.cookies.RequestsCookieJar()
        jar.set(key, value)
        jar.set(key1, value1)
        d1 = dict(jar)
        d2 = dict(jar.iteritems())
        d3 = dict(jar.items())
        assert d1["some_cookie"] == "some_value"
        assert d2["some_cookie"] == "some_value"
        assert d3["some_cookie1"] == "some_value1"

def test_cookie_as_dict_items(self):
        key = "some_cookie"
        value = "some_value"
        key1 = "some_cookie1"
        value1 = "some_value1"
        jar = requests.cookies.RequestsCookieJar()
        jar.set(key, value)
        jar.set(key1, value1)
        items = jar.items()
        assert items == list(items)
        assert list(items) == list(items)

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