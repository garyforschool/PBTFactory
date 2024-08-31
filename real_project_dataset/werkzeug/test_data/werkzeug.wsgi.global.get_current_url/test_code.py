def test_get_current_url_unicode():
    env = create_environ(query_string="foo=bar&baz=blah&meh=Ï")
    rv = wsgi.get_current_url(env)
    assert rv == "http://localhost/?foo=bar&baz=blah&meh=Ï"

def test_get_current_url_invalid_utf8():
    env = create_environ()
    env["QUERY_STRING"] = "foo=bar&baz=blah&meh=Ï"
    rv = wsgi.get_current_url(env)
    assert rv == "http://localhost/?foo=bar&baz=blah&meh=%CF"