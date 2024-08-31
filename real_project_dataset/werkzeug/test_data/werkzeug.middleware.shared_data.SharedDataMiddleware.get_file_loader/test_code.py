def test_get_file_loader():
    app = SharedDataMiddleware(None, {})
    assert callable(app.get_file_loader("foo"))