def test_exists_as_directory(self):
        path_type = exists_as(self.path.as_posix())
        self.normalize_path.assert_called_with(self.path.as_posix())
        self.assertEqual(path_type, "directory")

def test_exists_as_file(self):
        path_type = exists_as(self.path.as_posix())
        self.normalize_path.assert_called_with(self.path.as_posix())
        self.assertEqual(path_type, "file")

def test_exists_as_block_device(self):
        path_type = exists_as(self.path.as_posix())
        self.normalize_path.assert_called_with(self.path.as_posix())
        self.assertEqual(path_type, "block device")

def test_exists_as_char_device(self):
        path_type = exists_as(self.path.as_posix())
        self.normalize_path.assert_called_with(self.path.as_posix())
        self.assertEqual(path_type, "char device")

def test_exists_as_fifo(self):
        path_type = exists_as(self.path.as_posix())
        self.normalize_path.assert_called_with(self.path.as_posix())
        self.assertEqual(path_type, "FIFO")

def test_exists_as_socket(self):
        path_type = exists_as(self.path.as_posix())
        self.normalize_path.assert_called_with(self.path.as_posix())
        self.assertEqual(path_type, "socket")