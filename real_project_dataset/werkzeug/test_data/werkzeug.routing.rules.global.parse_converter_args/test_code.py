def test_converter_parser():
    args, kwargs = r.parse_converter_args("test, a=1, b=3.0")
    assert args == ("test",)
    assert kwargs == {"a": 1, "b": 3.0}
    args, kwargs = r.parse_converter_args("")
    assert not args and not kwargs
    args, kwargs = r.parse_converter_args("a, b, c,")
    assert args == ("a", "b", "c")
    assert not kwargs
    args, kwargs = r.parse_converter_args("True, False, None")
    assert args == (True, False, None)
    args, kwargs = r.parse_converter_args('"foo", "bar"')
    assert args == ("foo", "bar")
    with pytest.raises(ValueError):
        r.parse_converter_args("min=0;max=500")