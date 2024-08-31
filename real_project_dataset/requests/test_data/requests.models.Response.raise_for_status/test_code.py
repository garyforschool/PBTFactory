def test_response_reason_unicode_fallback(self):
        r = requests.Response()
        r.url = "some url"
        reason = "Komponenttia ei löydy"
        r.reason = reason.encode("latin-1")
        r.status_code = 500
        r.encoding = None
        with pytest.raises(requests.exceptions.HTTPError) as e:
            r.raise_for_status()
        assert reason in e.value.args[0]