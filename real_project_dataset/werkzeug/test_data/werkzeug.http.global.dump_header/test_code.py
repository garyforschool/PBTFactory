def test_dump_header(self):
        assert http.dump_header([1, 2, 3]) == "1, 2, 3"
        assert http.dump_header({"foo": "bar"}) == "foo=bar"
        assert http.dump_header({"foo*": "UTF-8''bar"}) == "foo*=UTF-8''bar"