def test_response_without_release_conn(self):
        resp = requests.Response()
        resp.raw = StringIO.StringIO("test")
        assert not resp.raw.closed
        resp.close()
        assert resp.raw.closed