def test_cookie_unicode_dumping(self):
        val = http.dump_cookie("foo", "☃")
        h = datastructures.Headers()
        h.add("Set-Cookie", val)
        assert h["Set-Cookie"] == 'foo="\\342\\230\\203"; Path=/'
        cookies = http.parse_cookie(h["Set-Cookie"])
        assert cookies["foo"] == "☃"

def test_envrion_builder_multiple_headers():
    h = Headers()
    h.add("FOO", "bar")
    h.add("FOO", "baz")
    b = EnvironBuilder(headers=h)
    env = b.get_environ()
    assert env["HTTP_FOO"] == "bar, baz"