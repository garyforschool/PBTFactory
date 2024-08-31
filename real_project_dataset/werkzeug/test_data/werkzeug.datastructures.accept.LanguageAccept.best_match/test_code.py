@pytest.mark.parametrize(
        ("values", "matches", "default", "expect"),
        (
            ([("en-us", 1)], ["en"], None, "en"),
            ([("en", 1)], ["en_US"], None, "en_US"),
            ([("en-GB", 1)], ["en-US"], None, None),
            ([("de_AT", 1), ("de", 0.9)], ["en"], None, None),
            ([("de_AT", 1), ("de", 0.9), ("en-US", 0.8)], ["de", "en"], None, "de"),
            ([("de_AT", 0.9), ("en-US", 1)], ["en"], None, "en"),
            ([("en-us", 1)], ["en-us"], None, "en-us"),
            ([("en-us", 1)], ["en-us", "en"], None, "en-us"),
            ([("en-GB", 1)], ["en-US", "en"], "en-US", "en"),
            ([("de_AT", 1)], ["en-US", "en"], "en-US", "en-US"),
            ([("aus-EN", 1)], ["aus"], None, "aus"),
            ([("aus", 1)], ["aus-EN"], None, "aus-EN"),
        ),
    )
    def test_best_match_fallback(self, values, matches, default, expect):
        accept = ds.LanguageAccept(values)
        best = accept.best_match(matches, default=default)
        assert best == expect