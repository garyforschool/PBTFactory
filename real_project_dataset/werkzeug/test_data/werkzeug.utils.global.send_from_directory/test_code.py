@pytest.mark.parametrize(
    ("directory", "path"),
    [(str(res_path), "test.txt"), (res_path, pathlib.Path("test.txt"))],
)
def test_from_directory(directory, path):
    rv = send_from_directory(directory, path, environ)
    rv.direct_passthrough = False
    assert rv.data.strip() == b"FOUND"
    rv.close()

@pytest.mark.parametrize("path", ["../res/test.txt", "nothing.txt", "null\x00.txt"])
def test_from_directory_not_found(path):
    with pytest.raises(NotFound):
        send_from_directory(res_path, path, environ)

def test_root_path(tmp_path):
    d = tmp_path / "d"
    d.mkdir()
    (d / "test.txt").write_bytes(b"test")
    rv = send_file("d/test.txt", environ, _root_path=tmp_path)
    rv.direct_passthrough = False
    assert rv.data == b"test"
    rv.close()
    rv = send_from_directory("d", "test.txt", environ, _root_path=tmp_path)
    rv.direct_passthrough = False
    assert rv.data == b"test"
    rv.close()