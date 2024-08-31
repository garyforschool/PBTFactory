def test_response_content_length_uses_encode():
    r = wrappers.Response("你好")
    assert r.calculate_content_length() == 6