def test_dict_header(self):
        d = http.parse_dict_header('foo="bar baz", blah=42')
        assert d == {"foo": "bar baz", "blah": "42"}