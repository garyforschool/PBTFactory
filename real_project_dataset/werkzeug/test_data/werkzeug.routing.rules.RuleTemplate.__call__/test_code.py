def test_rule_templates():
    testcase = r.RuleTemplate(
        [
            r.Submount(
                "/test/$app",
                [
                    r.Rule("/foo/", endpoint="handle_foo"),
                    r.Rule("/bar/", endpoint="handle_bar"),
                    r.Rule("/baz/", endpoint="handle_baz"),
                ],
            ),
            r.EndpointPrefix(
                "${app}",
                [
                    r.Rule("/${app}-blah", endpoint="bar"),
                    r.Rule("/${app}-meh", endpoint="baz"),
                ],
            ),
            r.Subdomain(
                "$app",
                [r.Rule("/blah", endpoint="x_bar"), r.Rule("/meh", endpoint="x_baz")],
            ),
        ]
    )
    url_map = r.Map(
        [
            testcase(app="test1"),
            testcase(app="test2"),
            testcase(app="test3"),
            testcase(app="test4"),
        ]
    )
    out = sorted((x.rule, x.subdomain, x.endpoint) for x in url_map.iter_rules())
    assert out == [
        ("/blah", "test1", "x_bar"),
        ("/blah", "test2", "x_bar"),
        ("/blah", "test3", "x_bar"),
        ("/blah", "test4", "x_bar"),
        ("/meh", "test1", "x_baz"),
        ("/meh", "test2", "x_baz"),
        ("/meh", "test3", "x_baz"),
        ("/meh", "test4", "x_baz"),
        ("/test/test1/bar/", "", "handle_bar"),
        ("/test/test1/baz/", "", "handle_baz"),
        ("/test/test1/foo/", "", "handle_foo"),
        ("/test/test2/bar/", "", "handle_bar"),
        ("/test/test2/baz/", "", "handle_baz"),
        ("/test/test2/foo/", "", "handle_foo"),
        ("/test/test3/bar/", "", "handle_bar"),
        ("/test/test3/baz/", "", "handle_baz"),
        ("/test/test3/foo/", "", "handle_foo"),
        ("/test/test4/bar/", "", "handle_bar"),
        ("/test/test4/baz/", "", "handle_baz"),
        ("/test/test4/foo/", "", "handle_foo"),
        ("/test1-blah", "", "test1bar"),
        ("/test1-meh", "", "test1baz"),
        ("/test2-blah", "", "test2bar"),
        ("/test2-meh", "", "test2baz"),
        ("/test3-blah", "", "test3bar"),
        ("/test3-meh", "", "test3baz"),
        ("/test4-blah", "", "test4bar"),
        ("/test4-meh", "", "test4baz"),
    ]