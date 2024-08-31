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