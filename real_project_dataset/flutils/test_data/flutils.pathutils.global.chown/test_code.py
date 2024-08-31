def test_chown_default(self):
        chown("~/tmp/test.txt")
        self.normalize_path.assert_called_with("~/tmp/test.txt")
        self.get_os_user.assert_called_with(None)
        self.get_os_group.assert_called_with(None)
        self.os_chown.assert_called_with(self.path.as_posix(), 9753, 1357)

def test_chown_current_owner(self):
        chown("~/tmp/test.txt", user="-1", group="-1")
        self.normalize_path.assert_called_with("~/tmp/test.txt")
        self.get_os_user.assert_not_called()
        self.get_os_group.assert_not_called()
        self.os_chown.assert_called_with(self.path.as_posix(), -1, -1)

def test_chown_user_group(self):
        chown("~/tmp/test.txt", user="test_user", group="test_group")
        self.normalize_path.assert_called_with("~/tmp/test.txt")
        self.get_os_user.assert_called_with("test_user")
        self.get_os_group.assert_called_with("test_group")
        self.os_chown.assert_called_with(self.path.as_posix(), 9753, 1357)

def test_chown_glob(self):
        chown("~/**")
        self.normalize_path.assert_called_with("~/**")
        self.get_os_user.assert_called_with(None)
        self.get_os_group.assert_called_with(None)
        for path in self.path.glob_data:
            if path.kwargs.get("is_dir", False) is True:
                self.os_chown.assert_any_call(path.as_posix(), 9753, 1357)
                path.is_dir.assert_called()
                path.is_file.assert_not_called()
            elif path.kwargs.get("is_file", False) is True:
                self.os_chown.assert_any_call(path.as_posix(), 9753, 1357)
                path.is_dir.assert_called()
                path.is_file.assert_called()
            else:
                path.is_dir.assert_called()
                path.is_file.assert_called()

def test_chown_include_parent(self):
        chown("~/tmp/*", include_parent=True)
        self.normalize_path.assert_called_with("~/tmp/*")
        self.get_os_user.assert_called_with(None)
        self.get_os_group.assert_called_with(None)
        for path in self.path.glob_data:
            if path.kwargs.get("is_dir", False) is True:
                self.os_chown.assert_any_call(path.as_posix(), 9753, 1357)
                path.is_dir.assert_called()
                path.is_file.assert_not_called()
            elif path.kwargs.get("is_file", False) is True:
                self.os_chown.assert_any_call(path.as_posix(), 9753, 1357)
                path.is_dir.assert_called()
                path.is_file.assert_called()
            else:
                path.is_dir.assert_called()
                path.is_file.assert_called()
        self.os_chown.assert_any_call(self.path.parent.as_posix(), 9753, 1357)

def test_chown_empty_glob(self):
        chown("~/**")
        self.normalize_path.assert_called_with("~/**")
        self.get_os_user.assert_called_with(None)
        self.get_os_group.assert_called_with(None)
        self.os_chown.assert_not_called()