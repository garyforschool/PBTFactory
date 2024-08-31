def test_set_header(self):
        hs = http.parse_set_header('foo, Bar, "Blah baz", Hehe')
        assert "blah baz" in hs
        assert "foobar" not in hs
        assert "foo" in hs
        assert list(hs) == ["foo", "Bar", "Blah baz", "Hehe"]
        hs.add("Foo")
        assert hs.to_header() == 'foo, Bar, "Blah baz", Hehe'