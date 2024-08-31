def test_transport_adapter_ordering(self):
        s = requests.Session()
        order = ["https://", "http://"]
        assert order == list(s.adapters)
        s.mount("http://git", HTTPAdapter())
        s.mount("http://github", HTTPAdapter())
        s.mount("http://github.com", HTTPAdapter())
        s.mount("http://github.com/about/", HTTPAdapter())
        order = [
            "http://github.com/about/",
            "http://github.com",
            "http://github",
            "http://git",
            "https://",
            "http://",
        ]
        assert order == list(s.adapters)
        s.mount("http://gittip", HTTPAdapter())
        s.mount("http://gittip.com", HTTPAdapter())
        s.mount("http://gittip.com/about/", HTTPAdapter())
        order = [
            "http://github.com/about/",
            "http://gittip.com/about/",
            "http://github.com",
            "http://gittip.com",
            "http://github",
            "http://gittip",
            "http://git",
            "https://",
            "http://",
        ]
        assert order == list(s.adapters)
        s2 = requests.Session()
        s2.adapters = {"http://": HTTPAdapter()}
        s2.mount("https://", HTTPAdapter())
        assert "http://" in s2.adapters
        assert "https://" in s2.adapters

def test_session_get_adapter_prefix_matching(self):
        prefix = "https://example.com"
        more_specific_prefix = prefix + "/some/path"
        url_matching_only_prefix = prefix + "/another/path"
        url_matching_more_specific_prefix = more_specific_prefix + "/longer/path"
        url_not_matching_prefix = "https://another.example.com/"
        s = requests.Session()
        prefix_adapter = HTTPAdapter()
        more_specific_prefix_adapter = HTTPAdapter()
        s.mount(prefix, prefix_adapter)
        s.mount(more_specific_prefix, more_specific_prefix_adapter)
        assert s.get_adapter(url_matching_only_prefix) is prefix_adapter
        assert (
            s.get_adapter(url_matching_more_specific_prefix)
            is more_specific_prefix_adapter
        )
        assert s.get_adapter(url_not_matching_prefix) not in (
            prefix_adapter,
            more_specific_prefix_adapter,
        )

def test_session_get_adapter_prefix_matching_mixed_case(self):
        mixed_case_prefix = "hTtPs://eXamPle.CoM/MixEd_CAse_PREfix"
        url_matching_prefix = mixed_case_prefix + "/full_url"
        s = requests.Session()
        my_adapter = HTTPAdapter()
        s.mount(mixed_case_prefix, my_adapter)
        assert s.get_adapter(url_matching_prefix) is my_adapter

def test_session_get_adapter_prefix_matching_is_case_insensitive(self):
        mixed_case_prefix = "hTtPs://eXamPle.CoM/MixEd_CAse_PREfix"
        url_matching_prefix_with_different_case = (
            "HtTpS://exaMPLe.cOm/MiXeD_caSE_preFIX/another_url"
        )
        s = requests.Session()
        my_adapter = HTTPAdapter()
        s.mount(mixed_case_prefix, my_adapter)
        assert s.get_adapter(url_matching_prefix_with_different_case) is my_adapter

def test_urllib3_retries(httpbin):
    from urllib3.util import Retry

    s = requests.Session()
    s.mount("http://", HTTPAdapter(max_retries=Retry(total=2, status_forcelist=[500])))
    with pytest.raises(RetryError):
        s.get(httpbin("status/500"))

def test_urllib3_pool_connection_closed(httpbin):
    s = requests.Session()
    s.mount("http://", HTTPAdapter(pool_connections=0, pool_maxsize=0))
    try:
        s.get(httpbin("status/200"))
    except ConnectionError as e:
        assert "Pool is closed." in str(e)