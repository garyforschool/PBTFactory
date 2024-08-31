@pytest.mark.parametrize("ranges", ([(0, 1), (-5, None)], [(5, None)]))
def test_range_to_header(ranges):
    header = ds.Range("byes", ranges).to_header()
    r = http.parse_range_header(header)
    assert r.ranges == ranges