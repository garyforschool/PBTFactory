def test_cookie_forging():
    c = Client(cookie_app)
    c.set_cookie("foo", "bar")
    response = c.open()
    assert response.text == "foo=bar"