def test_etags(self):
        assert http.quote_etag("foo") == '"foo"'
        assert http.quote_etag("foo", True) == 'W/"foo"'
        assert http.unquote_etag('"foo"') == ("foo", False)
        assert http.unquote_etag('W/"foo"') == ("foo", True)
        es = http.parse_etags('"foo", "bar", W/"baz", blar')
        assert sorted(es) == ["bar", "blar", "foo"]
        assert "foo" in es
        assert "baz" not in es
        assert es.contains_weak("baz")
        assert "blar" in es
        assert es.contains_raw('W/"baz"')
        assert es.contains_raw('"foo"')
        assert sorted(es.to_header().split(", ")) == [
            '"bar"',
            '"blar"',
            '"foo"',
            'W/"baz"',
        ]

def test_etags_nonzero(self):
        etags = http.parse_etags('W/"foo"')
        assert bool(etags)
        assert etags.contains_raw('W/"foo"')