def test_proxy_local():
    ns = local.Local(_cv_ns)
    ns.foo = []
    p = local.LocalProxy(ns, "foo")
    p.append(42)
    p.append(23)
    p[1:] = [1, 2, 3]
    assert p == [42, 1, 2, 3]
    assert p == ns.foo
    ns.foo += [1]
    assert list(p) == [42, 1, 2, 3, 1]
    p_from_local = ns("foo")
    p_from_local.append(2)
    assert p == p_from_local
    assert p._get_current_object() is ns.foo

def test_proxy_wrapped():

    class SomeClassWithWrapped:
        __wrapped__ = "wrapped"

    proxy = local.LocalProxy(_cv_val)
    assert proxy.__wrapped__ is _cv_val
    _cv_val.set(42)
    with pytest.raises(AttributeError):
        proxy.__wrapped__
    ns = local.Local(_cv_ns)
    ns.foo = SomeClassWithWrapped()
    ns.bar = 42
    assert ns("foo").__wrapped__ == "wrapped"
    with pytest.raises(AttributeError):
        ns("bar").__wrapped__

def test_proxy_unbound():
    ns = local.Local(_cv_ns)
    p = ns("value")
    assert repr(p) == "<LocalProxy unbound>"
    assert not p
    assert dir(p) == []

def _make_proxy(value):
    ns = local.Local(_cv_ns)
    ns.value = value
    p = ns("value")
    return ns, p