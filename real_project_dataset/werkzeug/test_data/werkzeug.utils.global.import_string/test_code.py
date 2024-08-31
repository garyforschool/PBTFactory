def test_import_string():
    from datetime import date
    from werkzeug.debug import DebuggedApplication

    assert utils.import_string("datetime.date") is date
    assert utils.import_string("datetime.date") is date
    assert utils.import_string("datetime:date") is date
    assert utils.import_string("XXXXXXXXXXXX", True) is None
    assert utils.import_string("datetime.XXXXXXXXXXXX", True) is None
    assert (
        utils.import_string("werkzeug.debug.DebuggedApplication") is DebuggedApplication
    )
    pytest.raises(ImportError, utils.import_string, "XXXXXXXXXXXXXXXX")
    pytest.raises(ImportError, utils.import_string, "datetime.XXXXXXXXXX")

def test_import_string_provides_traceback(tmpdir, monkeypatch):
    monkeypatch.syspath_prepend(str(tmpdir))
    dir_a = tmpdir.mkdir("a")
    dir_b = tmpdir.mkdir("b")
    dir_a.join("__init__.py").write("")
    dir_b.join("__init__.py").write("")
    dir_a.join("aa.py").write("from b import bb")
    dir_b.join("bb.py").write("from os import a_typo")
    with pytest.raises(ImportError) as baz_exc:
        utils.import_string("a.aa")
    traceback = "".join(str(line) for line in baz_exc.traceback)
    assert "bb.py':1" in traceback
    assert "from os import a_typo" in traceback

def test_import_string_attribute_error(tmpdir, monkeypatch):
    monkeypatch.syspath_prepend(str(tmpdir))
    tmpdir.join("foo_test.py").write("from bar_test import value")
    tmpdir.join("bar_test.py").write("raise AttributeError('bad')")
    with pytest.raises(AttributeError) as info:
        utils.import_string("foo_test")
    assert "bad" in str(info.value)
    with pytest.raises(AttributeError) as info:
        utils.import_string("bar_test")
    assert "bad" in str(info.value)