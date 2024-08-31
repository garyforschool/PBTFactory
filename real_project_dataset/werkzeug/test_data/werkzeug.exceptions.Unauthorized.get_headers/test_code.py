def test_unauthorized_www_authenticate():
    basic = WWWAuthenticate("basic", {"realm": "test"})
    digest = WWWAuthenticate("digest", {"realm": "test", "nonce": "test"})
    exc = exceptions.Unauthorized(www_authenticate=basic)
    h = Headers(exc.get_headers({}))
    assert h["WWW-Authenticate"] == str(basic)
    exc = exceptions.Unauthorized(www_authenticate=[digest, basic])
    h = Headers(exc.get_headers({}))
    assert h.get_all("WWW-Authenticate") == [str(digest), str(basic)]
    exc = exceptions.Unauthorized()
    h = Headers(exc.get_headers({}))
    assert "WWW-Authenticate" not in h