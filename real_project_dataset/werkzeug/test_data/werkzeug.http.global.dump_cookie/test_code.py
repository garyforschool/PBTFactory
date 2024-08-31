def test_dump_cookie(self):
        rv = http.dump_cookie(
            "foo", "bar baz blub", 360, httponly=True, sync_expires=False
        )
        assert set(rv.split("; ")) == {
            "HttpOnly",
            "Max-Age=360",
            "Path=/",
            'foo="bar baz blub"',
        }
        assert http.dump_cookie("key", "xxx/") == "key=xxx/; Path=/"
        assert http.dump_cookie("key", "xxx=", path=None) == "key=xxx="

def test_cookie_quoting(self):
        val = http.dump_cookie("foo", "?foo")
        assert val == "foo=?foo; Path=/"
        assert http.parse_cookie(val)["foo"] == "?foo"
        assert http.parse_cookie('foo="foo\\054bar"')["foo"] == "foo,bar"

def test_cookie_domain_resolving(self):
        val = http.dump_cookie("foo", "bar", domain="☃.com")
        assert val == "foo=bar; Domain=xn--n3h.com; Path=/"

def test_cookie_unicode_dumping(self):
        val = http.dump_cookie("foo", "☃")
        h = datastructures.Headers()
        h.add("Set-Cookie", val)
        assert h["Set-Cookie"] == 'foo="\\342\\230\\203"; Path=/'
        cookies = http.parse_cookie(h["Set-Cookie"])
        assert cookies["foo"] == "☃"

def test_cookie_unicode_keys(self):
        val = http.dump_cookie("fö", "fö")
        assert val == _wsgi_encoding_dance('fö="f\\303\\266"; Path=/')
        cookies = http.parse_cookie(val)
        assert cookies["fö"] == "fö"

def test_cookie_domain_encoding(self):
        val = http.dump_cookie("foo", "bar", domain="☃.com")
        assert val == "foo=bar; Domain=xn--n3h.com; Path=/"
        val = http.dump_cookie("foo", "bar", domain="foo.com")
        assert val == "foo=bar; Domain=foo.com; Path=/"

def test_cookie_maxsize(self):
        val = http.dump_cookie("foo", "bar" * 1360 + "b")
        assert len(val) == 4093
        with pytest.warns(UserWarning, match="cookie is too large"):
            http.dump_cookie("foo", "bar" * 1360 + "ba")
        with pytest.warns(UserWarning, match="the limit is 512 bytes"):
            http.dump_cookie("foo", "w" * 501, max_size=512)

@pytest.mark.parametrize(
        ("samesite", "expected"),
        (
            ("strict", "foo=bar; SameSite=Strict"),
            ("lax", "foo=bar; SameSite=Lax"),
            ("none", "foo=bar; SameSite=None"),
            (None, "foo=bar"),
        ),
    )
    def test_cookie_samesite_attribute(self, samesite, expected):
        value = http.dump_cookie("foo", "bar", samesite=samesite, path=None)
        assert value == expected

def test_cookie_samesite_invalid(self):
        with pytest.raises(ValueError):
            http.dump_cookie("foo", "bar", samesite="invalid")

def test_cookie_partitioned(self):
        value = http.dump_cookie("foo", "bar", partitioned=True, secure=True)
        assert value == "foo=bar; Secure; Path=/; Partitioned"

def test_cookie_partitioned_sets_secure(self):
        value = http.dump_cookie("foo", "bar", partitioned=True, secure=False)
        assert value == "foo=bar; Secure; Path=/; Partitioned"