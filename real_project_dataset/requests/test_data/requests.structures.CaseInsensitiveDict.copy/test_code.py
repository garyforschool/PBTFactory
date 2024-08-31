def test_copy(self):
        cid = CaseInsensitiveDict(
            {"Accept": "application/json", "user-Agent": "requests"}
        )
        cid_copy = cid.copy()
        assert cid == cid_copy
        cid["changed"] = True
        assert cid != cid_copy