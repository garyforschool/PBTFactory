def test_valid(self):
        assert address_in_network("192.168.1.1", "192.168.1.0/24")

def test_invalid(self):
        assert not address_in_network("172.16.0.1", "192.168.1.0/24")