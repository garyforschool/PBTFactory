def test_remove_hop_by_hop_headers(self):
        headers1 = [("Connection", "closed"), ("Foo", "bar"), ("Keep-Alive", "wtf")]
        headers2 = datastructures.Headers(headers1)
        http.remove_hop_by_hop_headers(headers1)
        assert headers1 == [("Foo", "bar")]
        http.remove_hop_by_hop_headers(headers2)
        assert headers2 == datastructures.Headers([("Foo", "bar")])