def test_safe_join():
    assert safe_join("foo", "bar/baz") == posixpath.join("foo", "bar/baz")
    assert safe_join("foo", "../bar/baz") is None
    if os.name == "nt":
        assert safe_join("foo", "foo\\bar") is None

def test_safe_join_os_sep():
    import werkzeug.security as sec

    prev_value = sec._os_alt_seps
    sec._os_alt_seps = "*"
    assert safe_join("foo", "bar/baz*") is None
    sec._os_alt_steps = prev_value

def test_safe_join_empty_trusted():
    assert safe_join("", "c:test.txt") == "./c:test.txt"