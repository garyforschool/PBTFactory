def test_integration_path(self):
        val = Path("~/tmp")
        expected = os.path.expanduser("~/tmp")
        val = normalize_path(val)
        self.assertEqual(val.as_posix(), expected)

def test_normalize_path(self):
        path = normalize_path("~/tmp/foo/../$TEST")
        self.expanduser.assert_called_with("~/tmp/foo/../$TEST")
        self.expandvars.assert_called_with("/home/test_user/tmp/foo/../$TEST")
        self.isabs.assert_called_once()
        self.getcwd.assert_not_called()
        self.join.assert_not_called()
        self.normpath.assert_called_with("/home/test_user/tmp/foo/../test")
        self.assertEqual(path.as_posix(), "/home/test_user/tmp/test")

def test_normalize_path_bytes(self):
        path = normalize_path("~/tmp/foo/../$TEST".encode(sys.getfilesystemencoding()))
        self.assertEqual(path.as_posix(), "/home/test_user/tmp/test")

def test_normalize_path_posix_path(self):
        path = normalize_path(self.path)
        self.assertEqual(path.as_posix(), "/home/test_user/tmp/test")

def test_normalize_path_cwd(self):
        path = normalize_path("foo/../$TEST")
        self.expanduser.assert_called_with("foo/../$TEST")
        self.expandvars.assert_called_with("foo/../$TEST")
        self.isabs.assert_called_once_with("foo/../test")
        self.getcwd.assert_called_once()
        self.join.assert_called_once_with("/home/test_user/tmp", "foo/../test")
        self.normpath.assert_called_with("/home/test_user/tmp/foo/../test")
        self.assertEqual(path.as_posix(), "/home/test_user/tmp/test")