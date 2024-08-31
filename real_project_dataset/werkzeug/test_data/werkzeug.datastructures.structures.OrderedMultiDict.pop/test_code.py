def test_get_description(self):
        data = ds.OrderedMultiDict()
        with pytest.raises(BadRequestKeyError) as exc_info:
            data["baz"]
        assert "baz" not in exc_info.value.get_description()
        exc_info.value.show_exception = True
        assert "baz" in exc_info.value.get_description()
        with pytest.raises(BadRequestKeyError) as exc_info:
            data.pop("baz")
        exc_info.value.show_exception = True
        assert "baz" in exc_info.value.get_description()
        exc_info.value.args = ()
        assert "baz" not in exc_info.value.get_description()