def test_csp_header(self):
        csp = http.parse_csp_header(
            "default-src 'self'; script-src 'unsafe-inline' *; img-src"
        )
        assert csp.default_src == "'self'"
        assert csp.script_src == "'unsafe-inline' *"
        assert csp.img_src is None