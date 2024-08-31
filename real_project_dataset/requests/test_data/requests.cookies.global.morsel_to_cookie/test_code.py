def test_expires_valid_str(self):
        morsel = Morsel()
        morsel["expires"] = "Thu, 01-Jan-1970 00:00:01 GMT"
        cookie = morsel_to_cookie(morsel)
        assert cookie.expires == 1

@pytest.mark.parametrize(
        "value, exception", ((100, TypeError), ("woops", ValueError))
    )
    def test_expires_invalid_int(self, value, exception):
        morsel = Morsel()
        morsel["expires"] = value
        with pytest.raises(exception):
            morsel_to_cookie(morsel)

def test_expires_none(self):
        morsel = Morsel()
        morsel["expires"] = None
        cookie = morsel_to_cookie(morsel)
        assert cookie.expires is None

def test_max_age_valid_int(self):
        morsel = Morsel()
        morsel["max-age"] = 60
        cookie = morsel_to_cookie(morsel)
        assert isinstance(cookie.expires, int)

def test_max_age_invalid_str(self):
        morsel = Morsel()
        morsel["max-age"] = "woops"
        with pytest.raises(TypeError):
            morsel_to_cookie(morsel)