def test_should_strip_auth_host_change(self):
        s = requests.Session()
        assert s.should_strip_auth(
            "http://example.com/foo", "http://another.example.com/"
        )

def test_should_strip_auth_http_downgrade(self):
        s = requests.Session()
        assert s.should_strip_auth("https://example.com/foo", "http://example.com/bar")

def test_should_strip_auth_https_upgrade(self):
        s = requests.Session()
        assert not s.should_strip_auth(
            "http://example.com/foo", "https://example.com/bar"
        )
        assert not s.should_strip_auth(
            "http://example.com:80/foo", "https://example.com/bar"
        )
        assert not s.should_strip_auth(
            "http://example.com/foo", "https://example.com:443/bar"
        )
        assert s.should_strip_auth(
            "http://example.com:8080/foo", "https://example.com/bar"
        )
        assert s.should_strip_auth(
            "http://example.com/foo", "https://example.com:8443/bar"
        )

def test_should_strip_auth_port_change(self):
        s = requests.Session()
        assert s.should_strip_auth(
            "http://example.com:1234/foo", "https://example.com:4321/bar"
        )

@pytest.mark.parametrize(
        "old_uri, new_uri",
        (
            ("https://example.com:443/foo", "https://example.com/bar"),
            ("http://example.com:80/foo", "http://example.com/bar"),
            ("https://example.com/foo", "https://example.com:443/bar"),
            ("http://example.com/foo", "http://example.com:80/bar"),
        ),
    )
    def test_should_strip_auth_default_port(self, old_uri, new_uri):
        s = requests.Session()
        assert not s.should_strip_auth(old_uri, new_uri)