def test_find_modules():
    assert list(utils.find_modules("werkzeug.debug")) == [
        "werkzeug.debug.console",
        "werkzeug.debug.repr",
        "werkzeug.debug.tbtools",
    ]