def test_cache_control_header(self):
        cc = http.parse_cache_control_header("max-age=0, no-cache")
        assert cc.max_age == 0
        assert cc.no_cache
        cc = http.parse_cache_control_header(
            'private, community="UCI"', None, datastructures.ResponseCacheControl
        )
        assert cc.private
        assert cc["community"] == "UCI"
        c = datastructures.ResponseCacheControl()
        assert c.no_cache is None
        assert c.private is None
        c.no_cache = True
        assert c.no_cache == "*"
        c.private = True
        assert c.private == "*"
        del c.private
        assert c.private is None
        c.max_age = 3.1
        assert c.max_age == 3
        del c.max_age
        c.s_maxage = 3.1
        assert c.s_maxage == 3
        del c.s_maxage
        assert c.to_header() == "no-cache"