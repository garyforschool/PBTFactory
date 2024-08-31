@pytest.mark.skipif(sys.version_info >= (3, 10), reason="not needed on >= 3.10")
def test_windows_get_args_for_reloading(monkeypatch, tmp_path):
    argv = [str(tmp_path / "test.exe"), "run"]
    monkeypatch.setattr("sys.executable", str(tmp_path / "python.exe"))
    monkeypatch.setattr("sys.argv", argv)
    monkeypatch.setattr("__main__.__package__", None)
    monkeypatch.setattr("os.name", "nt")
    rv = _get_args_for_reloading()
    assert rv == argv