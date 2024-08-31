def test_basic_local():
    ns = local.Local(_cv_ns)
    ns.foo = 0
    values = []

    def value_setter(idx):
        time.sleep(0.01 * idx)
        ns.foo = idx
        time.sleep(0.02)
        values.append(ns.foo)

    threads = [Thread(target=value_setter, args=(x,)) for x in [1, 2, 3]]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(values) == [1, 2, 3]

    def delfoo():
        del ns.foo

    delfoo()
    pytest.raises(AttributeError, lambda: ns.foo)
    pytest.raises(AttributeError, delfoo)
    local.release_local(ns)

def test_basic_local_asyncio():
    ns = local.Local(_cv_ns)
    ns.foo = 0
    values = []

    async def value_setter(idx):
        await asyncio.sleep(0.01 * idx)
        ns.foo = idx
        await asyncio.sleep(0.02)
        values.append(ns.foo)

    async def main():
        futures = [asyncio.ensure_future(value_setter(i)) for i in [1, 2, 3]]
        await asyncio.gather(*futures)

    asyncio.run(main())
    assert sorted(values) == [1, 2, 3]

    def delfoo():
        del ns.foo

    delfoo()
    pytest.raises(AttributeError, lambda: ns.foo)
    pytest.raises(AttributeError, delfoo)
    local.release_local(ns)

def test_local_release():
    ns = local.Local(_cv_ns)
    ns.foo = 42
    local.release_local(ns)
    assert not hasattr(ns, "foo")
    ls = local.LocalStack(_cv_stack)
    ls.push(42)
    local.release_local(ls)
    assert ls.top is None