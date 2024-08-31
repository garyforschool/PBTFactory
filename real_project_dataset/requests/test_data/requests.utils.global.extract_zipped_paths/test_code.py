@pytest.mark.parametrize(
        "path", ("/", __file__, pytest.__file__, "/etc/invalid/location")
    )
    def test_unzipped_paths_unchanged(self, path):
        assert path == extract_zipped_paths(path)

def test_zipped_paths_extracted(self, tmpdir):
        zipped_py = tmpdir.join("test.zip")
        with zipfile.ZipFile(zipped_py.strpath, "w") as f:
            f.write(__file__)
        _, name = os.path.splitdrive(__file__)
        zipped_path = os.path.join(zipped_py.strpath, name.lstrip("\\/"))
        extracted_path = extract_zipped_paths(zipped_path)
        assert extracted_path != zipped_path
        assert os.path.exists(extracted_path)
        assert filecmp.cmp(extracted_path, __file__)

def test_invalid_unc_path(self):
        path = "\\\\localhost\\invalid\\location"
        assert extract_zipped_paths(path) == path