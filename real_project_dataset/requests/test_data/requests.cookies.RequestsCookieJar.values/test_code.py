def test_cookie_as_dict_values(self):
        key = "some_cookie"
        value = "some_value"
        key1 = "some_cookie1"
        value1 = "some_value1"
        jar = requests.cookies.RequestsCookieJar()
        jar.set(key, value)
        jar.set(key1, value1)
        values = jar.values()
        assert values == list(values)
        assert list(values) == list(values)