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