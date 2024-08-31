def test_status_code_425(self):
        r1 = requests.codes.get("TOO_EARLY")
        r2 = requests.codes.get("too_early")
        r3 = requests.codes.get("UNORDERED")
        r4 = requests.codes.get("unordered")
        r5 = requests.codes.get("UNORDERED_COLLECTION")
        r6 = requests.codes.get("unordered_collection")
        assert r1 == 425
        assert r2 == 425
        assert r3 == 425
        assert r4 == 425
        assert r5 == 425
        assert r6 == 425