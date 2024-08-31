def test_valid(self):
        assert is_ipv4_address("8.8.8.8")

@pytest.mark.parametrize("value", ("8.8.8.8.8", "localhost.localdomain"))
    def test_invalid(self, value):
        assert not is_ipv4_address(value)