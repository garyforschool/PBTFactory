def test_valid(self):
        assert is_valid_cidr("192.168.1.0/24")

@pytest.mark.parametrize(
        "value",
        (
            "8.8.8.8",
            "192.168.1.0/a",
            "192.168.1.0/128",
            "192.168.1.0/-1",
            "192.168.1.999/24",
        ),
    )
    def test_invalid(self, value):
        assert not is_valid_cidr(value)