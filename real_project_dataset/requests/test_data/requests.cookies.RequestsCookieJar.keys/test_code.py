def test_cookie_as_dict_keys(self):
        key = "some_cookie"
        value = "some_value"
        key1 = "some_cookie1"
        value1 = "some_value1"
        jar = requests.cookies.RequestsCookieJar()
        jar.set(key, value)
        jar.set(key1, value1)
        keys = jar.keys()
        assert keys == list(keys)
        assert list(keys) == list(keys)