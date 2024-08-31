def test_delete_empty_dir(self) -> None:
        path_absent(DIR_1)
        self.assertFalse(os.path.exists(DIR_1))

def test_delete_file(self) -> None:
        path_absent(FILE_B)
        self.assertFalse(os.path.exists(FILE_B))

def test_non_exists(self) -> None:
        path_absent(DIR_4)
        self.assertFalse(os.path.exists(DIR_4))

def test_delete_dir(self) -> None:
        path_absent(DIR_3)
        self.assertFalse(os.path.exists(DIR_3))
        self.assertFalse(os.path.exists(FILE_B))
        self.assertFalse(os.path.exists(LINK_2))
        self.assertFalse(os.path.exists(LINK_A))
        self.assertTrue(os.path.exists(DIR_2))
        self.assertTrue(os.path.exists(FILE_A))

def test_delete_dir_link(self) -> None:
        path_absent(LINK_2)
        self.assertFalse(os.path.exists(LINK_2))
        self.assertTrue(os.path.exists(DIR_2))
        self.assertTrue(os.path.exists(FILE_B))
        self.assertTrue(os.path.exists(FILE_A))

def test_delete_parent_dir(self) -> None:
        path_absent(DIR_ROOT)
        self.assertFalse(os.path.exists(DIR_1))
        self.assertFalse(os.path.exists(DIR_2))
        self.assertFalse(os.path.exists(DIR_3))
        self.assertFalse(os.path.exists(DIR_4))