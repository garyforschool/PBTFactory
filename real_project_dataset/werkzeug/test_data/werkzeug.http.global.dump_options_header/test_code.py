def test_dump_options_header(self):
        assert http.dump_options_header("foo", {"bar": 42}) == "foo; bar=42"
        assert "fizz" not in http.dump_options_header("foo", {"bar": 42, "fizz": None})