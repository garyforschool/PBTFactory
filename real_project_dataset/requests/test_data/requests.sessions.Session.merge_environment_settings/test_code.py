@pytest.mark.parametrize(
        "env, expected",
        (
            ({}, True),
            ({"REQUESTS_CA_BUNDLE": "/some/path"}, "/some/path"),
            ({"REQUESTS_CA_BUNDLE": ""}, True),
            ({"CURL_CA_BUNDLE": "/some/path"}, "/some/path"),
            ({"CURL_CA_BUNDLE": ""}, True),
            ({"REQUESTS_CA_BUNDLE": "", "CURL_CA_BUNDLE": ""}, True),
            (
                {"REQUESTS_CA_BUNDLE": "/some/path", "CURL_CA_BUNDLE": "/curl/path"},
                "/some/path",
            ),
            ({"REQUESTS_CA_BUNDLE": "", "CURL_CA_BUNDLE": "/curl/path"}, "/curl/path"),
        ),
    )
    def test_env_cert_bundles(self, httpbin, env, expected):
        s = requests.Session()
        with mock.patch("os.environ", env):
            settings = s.merge_environment_settings(
                url=httpbin("get"), proxies={}, stream=False, verify=True, cert=None
            )
        assert settings["verify"] == expected