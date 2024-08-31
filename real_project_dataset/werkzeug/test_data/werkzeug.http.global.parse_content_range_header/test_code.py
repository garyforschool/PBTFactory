def test_content_range_parsing(self):
        rv = http.parse_content_range_header("bytes 0-98/*")
        assert rv.units == "bytes"
        assert rv.start == 0
        assert rv.stop == 99
        assert rv.length is None
        assert rv.to_header() == "bytes 0-98/*"
        rv = http.parse_content_range_header("bytes 0-98/*asdfsa")
        assert rv is None
        rv = http.parse_content_range_header("bytes */-1")
        assert rv is None
        rv = http.parse_content_range_header("bytes 0-99/100")
        assert rv.to_header() == "bytes 0-99/100"
        rv.start = None
        rv.stop = None
        assert rv.units == "bytes"
        assert rv.to_header() == "bytes */100"
        rv = http.parse_content_range_header("bytes */100")
        assert rv.start is None
        assert rv.stop is None
        assert rv.length == 100
        assert rv.units == "bytes"

@pytest.mark.parametrize("value", ["*/🯱🯲🯳", "1-+2/3", "1_23-125/*"])
def test_content_range_invalid_int(value):
    assert http.parse_content_range_header(f"bytes {value}") is None