@pytest.mark.parametrize(
    "value, expected", (("test", True), ("æíöû", False), ("ジェーピーニック", False))
)
def test_unicode_is_ascii(value, expected):
    assert unicode_is_ascii(value) is expected