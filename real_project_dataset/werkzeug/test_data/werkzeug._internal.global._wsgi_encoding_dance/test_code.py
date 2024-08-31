def test_cookie_unicode_keys(self):
        val = http.dump_cookie("fö", "fö")
        assert val == _wsgi_encoding_dance('fö="f\\303\\266"; Path=/')
        cookies = http.parse_cookie(val)
        assert cookies["fö"] == "fö"