def test_construct(self):
        csp = ds.ContentSecurityPolicy([("font-src", "'self'"), ("media-src", "*")])
        assert csp.font_src == "'self'"
        assert csp.media_src == "*"
        policies = [policy.strip() for policy in csp.to_header().split(";")]