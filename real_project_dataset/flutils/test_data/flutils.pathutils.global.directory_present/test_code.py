def setUp(self) -> None:
        if os.path.exists(DIR_ROOT):
            shutil.rmtree(DIR_ROOT)
        directory_present(DIR_1)
        directory_present(DIR_2)
        directory_present(DIR_3)
        with open(FILE_A, "w") as f:
            f.write("")
        with open(FILE_B, "w") as f:
            f.write("")
        os.symlink(DIR_2, LINK_2)
        os.symlink(FILE_A, LINK_A)

def test_directory_present_with_parents_default(self):
        directory_present(self.path.as_posix())
        self.normalize_path.assert_called_with(self.path.as_posix())
        self.path.mkdir.assert_called_with(mode=448)
        self.dir_two.mkdir.assert_called_with(mode=448)
        self.dir_one.mkdir.assert_called_with(mode=448)
        self.tmp.mkdir.assert_not_called()
        self.chown.assert_any_call(self.path, user=None, group=None)
        self.chown.assert_any_call(self.dir_two, user=None, group=None)
        self.chown.assert_any_call(self.dir_one, user=None, group=None)
        self.chmod.assert_not_called()

def test_directory_present_with_parents_mode_user_group(self):
        mode = 504
        user = "test_user"
        group = "test_group"
        directory_present(self.path.as_posix(), mode=mode, user=user, group=group)
        self.normalize_path.assert_called_with(self.path.as_posix())
        self.path.mkdir.assert_called_with(mode=mode)
        self.dir_two.mkdir.assert_called_with(mode=mode)
        self.dir_one.mkdir.assert_called_with(mode=mode)
        self.tmp.mkdir.assert_not_called()
        self.chown.assert_any_call(self.path, user=user, group=group)
        self.chown.assert_any_call(self.dir_two, user=user, group=group)
        self.chown.assert_any_call(self.dir_one, user=user, group=group)
        self.chmod.assert_not_called()

def test_directory_present_exists(self):
        directory_present(self.path.as_posix())
        self.normalize_path.assert_called_with(self.path.as_posix())
        self.path.mkdir.assert_not_called()
        self.dir_two.mkdir.assert_not_called()
        self.dir_one.mkdir.assert_not_called()
        self.tmp.mkdir.assert_not_called()
        self.chmod.assert_called_once_with(self.path, mode_dir=448)
        self.chown.assert_called_once_with(self.path, user=None, group=None)