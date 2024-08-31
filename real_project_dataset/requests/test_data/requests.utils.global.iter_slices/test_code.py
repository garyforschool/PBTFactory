@pytest.mark.parametrize(
    "value, length",
    (("", 0), ("T", 1), ("Test", 4), ("Cont", 0), ("Other", -5), ("Content", None)),
)
def test_iter_slices(value, length):
    if length is None or length <= 0 and len(value) > 0:
        assert len(list(iter_slices(value, length))) == 1
    else:
        assert len(list(iter_slices(value, 1))) == length