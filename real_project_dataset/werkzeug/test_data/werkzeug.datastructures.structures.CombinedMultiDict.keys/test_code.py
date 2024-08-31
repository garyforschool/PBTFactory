def test_iterables(self):
        a = ds.MultiDict((("key_a", "value_a"),))
        b = ds.MultiDict((("key_b", "value_b"),))
        ab = ds.CombinedMultiDict((a, b))
        assert sorted(ab.lists()) == [("key_a", ["value_a"]), ("key_b", ["value_b"])]
        assert sorted(ab.listvalues()) == [["value_a"], ["value_b"]]
        assert sorted(ab.keys()) == ["key_a", "key_b"]
        assert sorted(ab.lists()) == [("key_a", ["value_a"]), ("key_b", ["value_b"])]
        assert sorted(ab.listvalues()) == [["value_a"], ["value_b"]]
        assert sorted(ab.keys()) == ["key_a", "key_b"]