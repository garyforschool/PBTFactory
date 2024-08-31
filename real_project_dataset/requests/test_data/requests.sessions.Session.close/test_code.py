def test_session_close_proxy_clear(self):
        proxies = {"one": mock.Mock(), "two": mock.Mock()}
        session = requests.Session()
        with mock.patch.dict(session.adapters["http://"].proxy_manager, proxies):
            session.close()
            proxies["one"].clear.assert_called_once_with()
            proxies["two"].clear.assert_called_once_with()