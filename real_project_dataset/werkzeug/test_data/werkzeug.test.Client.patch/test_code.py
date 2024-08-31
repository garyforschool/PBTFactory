def test_base_request():
    client = Client(request_demo_app)
    response = client.get("/?foo=bar&foo=hehe")
    request = response.request
    assert request.args == MultiDict([("foo", "bar"), ("foo", "hehe")])
    assert request.form == MultiDict()
    assert request.data == b""
    assert_environ(request.environ, "GET")
    response = client.post(
        "/?blub=blah",
        data="foo=blub+hehe&blah=42",
        content_type="application/x-www-form-urlencoded",
    )
    request = response.request
    assert request.args == MultiDict([("blub", "blah")])
    assert request.form == MultiDict([("foo", "blub hehe"), ("blah", "42")])
    assert request.data == b""
    assert_environ(request.environ, "POST")
    response = client.patch(
        "/?blub=blah",
        data="foo=blub+hehe&blah=42",
        content_type="application/x-www-form-urlencoded",
    )
    request = response.request
    assert request.args == MultiDict([("blub", "blah")])
    assert request.form == MultiDict([("foo", "blub hehe"), ("blah", "42")])
    assert request.data == b""
    assert_environ(request.environ, "PATCH")
    json = b'{"foo": "bar", "blub": "blah"}'
    response = client.post("/?a=b", data=json, content_type="application/json")
    request = response.request
    assert request.data == json
    assert request.args == MultiDict([("a", "b")])
    assert request.form == MultiDict()