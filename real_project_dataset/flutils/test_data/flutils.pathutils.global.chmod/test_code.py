def test_chmod_file_default(self):
        chmod("~/tmp/test.txt")
        self.normalize_path.assert_called_with("~/tmp/test.txt")
        self.path.chmod.assert_called_with(384)

def test_chmod_file_mode(self):
        chmod("~/tmp/test.txt", mode_file=511)
        self.normalize_path.assert_called_with("~/tmp/test.txt")
        self.path.chmod.assert_called_with(511)

def test_chmod_directory_default(self):
        chmod("~/tmp/test")
        self.normalize_path.assert_called_with("~/tmp/test")
        self.path.chmod.assert_called_with(448)

def test_chmod_directory_mode(self):
        chmod("~/tmp/test", mode_dir=504)
        self.normalize_path.assert_called_with("~/tmp/test")
        self.path.chmod.assert_called_with(504)

def test_chmod_glob_default(self):
        chmod("~/**")
        self.normalize_path.assert_called_with("~/**")
        self.path.glob.assert_called_with("/home/test_user/**")
        for path in self.path.glob_data:
            if path.kwargs.get("is_file", False) is True:
                path.chmod.assert_called_with(384)
            elif path.kwargs.get("is_dir", False) is True:
                path.chmod.assert_called_with(448)
            elif path.kwargs.get("is_fifo", False) is True:
                path.chmod.assert_not_called()

def test_chmod_glob_modes(self):
        chmod("~/**", mode_file=432, mode_dir=504)
        self.normalize_path.assert_called_with("~/**")
        self.path.glob.assert_called_with("/home/test_user/**")
        for path in self.path.glob_data:
            if path.kwargs.get("is_file", False) is True:
                path.chmod.assert_called_with(432)
            elif path.kwargs.get("is_dir", False) is True:
                path.chmod.assert_called_with(504)
            elif path.kwargs.get("is_fifo", False) is True:
                path.chmod.assert_not_called()

def test_chmod_glob_include_parent(self):
        chmod("~/**", mode_file=432, mode_dir=504, include_parent=True)
        self.normalize_path.assert_called_with("~/**")
        self.path.glob.assert_called_with("/home/test_user/**")
        for path in self.path.glob_data:
            if path.kwargs.get("is_file", False) is True:
                path.chmod.assert_called_with(432)
            elif path.kwargs.get("is_dir", False) is True:
                path.chmod.assert_called_with(504)
            elif path.kwargs.get("is_fifo", False) is True:
                path.chmod.assert_not_called()
        self.path.parent.is_dir.assert_called()
        self.path.parent.chmod.assert_called_with(504)

def test_chmod_empty_glob(self):
        chmod("~/**", mode_file=432, mode_dir=504, include_parent=True)
        self.normalize_path.assert_called_with("~/**")
        self.path.glob.assert_called_with("/home/test_user/**")
        self.path.parent.chmod.assert_not_called()