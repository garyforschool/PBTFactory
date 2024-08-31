def test_parse_cookie(self):
        cookies = http.parse_cookie(
            'dismiss-top=6; CP=null*; PHPSESSID=0a539d42abc001cdc762809248d4beed;a=42; b="\\";"; ; fo234{=bar;blub=Blah; "__Secure-c"=d;==__Host-eq=bad;__Host-eq=good;'
        )
        assert cookies.to_dict() == {
            "CP": "null*",
            "PHPSESSID": "0a539d42abc001cdc762809248d4beed",
            "a": "42",
            "dismiss-top": "6",
            "b": '";',
            "fo234{": "bar",
            "blub": "Blah",
            '"__Secure-c"': "d",
            "__Host-eq": "good",
        }

def test_bad_cookies(self):
        cookies = http.parse_cookie(
            "first=IamTheFirst ; a=1; oops ; a=2 ;second = andMeTwo;"
        )
        expect = {
            "first": ["IamTheFirst"],
            "a": ["1", "2"],
            "oops": [""],
            "second": ["andMeTwo"],
        }
        assert cookies.to_dict(flat=False) == expect
        assert cookies["a"] == "1"
        assert cookies.getlist("a") == ["1", "2"]

def test_empty_keys_are_ignored(self):
        cookies = http.parse_cookie("spam=ham; duck=mallard; ; ")
        expect = {"spam": "ham", "duck": "mallard"}
        assert cookies.to_dict() == expect

def test_cookie_quoting(self):
        val = http.dump_cookie("foo", "?foo")
        assert val == "foo=?foo; Path=/"
        assert http.parse_cookie(val)["foo"] == "?foo"
        assert http.parse_cookie('foo="foo\\054bar"')["foo"] == "foo,bar"

def test_parse_set_cookie_directive(self):
        val = 'foo="?foo"; version="0.1";'
        assert http.parse_cookie(val).to_dict() == {"foo": "?foo", "version": "0.1"}

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

def test_cookie_unicode_parsing(self):
        cookies = http.parse_cookie("fÃ¶=fÃ¶")
        assert cookies["fö"] == "fö"