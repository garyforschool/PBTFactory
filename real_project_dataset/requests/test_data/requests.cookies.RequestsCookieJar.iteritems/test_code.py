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