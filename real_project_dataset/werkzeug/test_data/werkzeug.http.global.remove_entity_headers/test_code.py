def test_remove_entity_headers(self):
        now = http.http_date()
        headers1 = [
            ("Date", now),
            ("Content-Type", "text/html"),
            ("Content-Length", "0"),
        ]
        headers2 = datastructures.Headers(headers1)
        http.remove_entity_headers(headers1)
        assert headers1 == [("Date", now)]
        http.remove_entity_headers(headers2)
        assert headers2 == datastructures.Headers([("Date", now)])