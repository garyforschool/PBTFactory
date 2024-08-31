def test_lower_items(self):
        cid = CaseInsensitiveDict(
            {"Accept": "application/json", "user-Agent": "requests"}
        )
        keyset = frozenset(lowerkey for lowerkey, v in cid.lower_items())