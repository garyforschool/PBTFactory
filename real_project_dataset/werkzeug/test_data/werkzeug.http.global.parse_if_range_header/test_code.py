def test_if_range_parsing(self):
        rv = http.parse_if_range_header('"Test"')
        assert rv.etag == "Test"
        assert rv.date is None
        assert rv.to_header() == '"Test"'
        rv = http.parse_if_range_header('W/"Test"')
        assert rv.etag == "Test"
        assert rv.date is None
        assert rv.to_header() == '"Test"'
        rv = http.parse_if_range_header("bullshit")
        assert rv.etag == "bullshit"
        assert rv.date is None
        assert rv.to_header() == '"bullshit"'
        rv = http.parse_if_range_header("Thu, 01 Jan 1970 00:00:00 GMT")
        assert rv.etag is None
        assert rv.date == datetime(1970, 1, 1, tzinfo=timezone.utc)
        assert rv.to_header() == "Thu, 01 Jan 1970 00:00:00 GMT"
        for x in ("", None):
            rv = http.parse_if_range_header(x)
            assert rv.etag is None
            assert rv.date is None
            assert rv.to_header() == ""