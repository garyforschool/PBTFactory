@pytest.mark.parametrize("value, expected", (("T", "T"), (b"T", "T"), ("T", "T")))
def test_to_native_string(value, expected):
    assert to_native_string(value) == expected