def test_range_parsing(self):
        rv = http.parse_range_header("bytes=52")
        assert rv is None
        rv = http.parse_range_header("bytes=52-")
        assert rv.units == "bytes"
        assert rv.ranges == [(52, None)]
        assert rv.to_header() == "bytes=52-"
        rv = http.parse_range_header("bytes=52-99")
        assert rv.units == "bytes"
        assert rv.ranges == [(52, 100)]
        assert rv.to_header() == "bytes=52-99"
        rv = http.parse_range_header("bytes=52-99,-1000")
        assert rv.units == "bytes"
        assert rv.ranges == [(52, 100), (-1000, None)]
        assert rv.to_header() == "bytes=52-99,-1000"
        rv = http.parse_range_header("bytes = 1 - 100")
        assert rv.units == "bytes"
        assert rv.ranges == [(1, 101)]
        assert rv.to_header() == "bytes=1-100"
        rv = http.parse_range_header("AWesomes=0-999")
        assert rv.units == "awesomes"
        assert rv.ranges == [(0, 1000)]
        assert rv.to_header() == "awesomes=0-999"
        rv = http.parse_range_header("bytes=-")
        assert rv is None
        rv = http.parse_range_header("bytes=bad")
        assert rv is None
        rv = http.parse_range_header("bytes=bad-1")
        assert rv is None
        rv = http.parse_range_header("bytes=-bad")
        assert rv is None
        rv = http.parse_range_header("bytes=52-99, bad")
        assert rv is None

@pytest.mark.parametrize("value", ["🯱🯲🯳", "+1-", "1-1_23"])
def test_range_invalid_int(value):
    assert http.parse_range_header(value) is None

@pytest.mark.parametrize("ranges", ([(0, 1), (-5, None)], [(5, None)]))
def test_range_to_header(ranges):
    header = ds.Range("byes", ranges).to_header()
    r = http.parse_range_header(header)
    assert r.ranges == ranges