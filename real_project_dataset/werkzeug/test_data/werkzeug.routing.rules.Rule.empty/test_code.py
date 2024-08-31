def test_rule_emptying():
    rule = r.Rule("/foo", {"meh": "muh"}, "x", ["POST"], False, "x", True, None)
    rule2 = rule.empty()
    assert rule.__dict__ == rule2.__dict__
    rule.methods.add("GET")
    assert rule.__dict__ != rule2.__dict__
    rule.methods.discard("GET")
    rule.defaults["meh"] = "aha"
    assert rule.__dict__ != rule2.__dict__