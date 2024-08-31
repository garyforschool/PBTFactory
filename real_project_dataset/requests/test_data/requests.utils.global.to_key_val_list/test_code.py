@pytest.mark.parametrize(
        "value, expected",
        (
            ([("key", "val")], [("key", "val")]),
            ((("key", "val"),), [("key", "val")]),
            ({"key": "val"}, [("key", "val")]),
            (None, None),
        ),
    )
    def test_valid(self, value, expected):
        assert to_key_val_list(value) == expected

def test_invalid(self):
        with pytest.raises(ValueError):
            to_key_val_list("string")