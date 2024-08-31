import unittest
from unittest.mock import patch
from flutils.pathutils import chmod
from ..mocks.pathlib import PosixPathMock


class TestChmodFile(unittest.TestCase):

    def setUp(self):
        self.path = PosixPathMock("/home/test_user/tmp/test.txt", is_file=True)
        patcher = patch("flutils.pathutils.normalize_path", return_value=self.path)
        self.normalize_path = patcher.start()
        self.addCleanup(patcher.stop)

    def test_chmod_file_default(self):
        chmod("~/tmp/test.txt")
        self.normalize_path.assert_called_with("~/tmp/test.txt")
        self.path.chmod.assert_called_with(384)

    def test_chmod_file_mode(self):
        chmod("~/tmp/test.txt", mode_file=511)
        self.normalize_path.assert_called_with("~/tmp/test.txt")
        self.path.chmod.assert_called_with(511)


class TestChmodDirectory(unittest.TestCase):

    def setUp(self):
        self.path = PosixPathMock("/home/test_user/tmp/test", is_dir=True)
        patcher = patch("flutils.pathutils.normalize_path", return_value=self.path)
        self.normalize_path = patcher.start()
        self.addCleanup(patcher.stop)

    def test_chmod_directory_default(self):
        chmod("~/tmp/test")
        self.normalize_path.assert_called_with("~/tmp/test")
        self.path.chmod.assert_called_with(448)

    def test_chmod_directory_mode(self):
        chmod("~/tmp/test", mode_dir=504)
        self.normalize_path.assert_called_with("~/tmp/test")
        self.path.chmod.assert_called_with(504)


class TestChmodGlob(unittest.TestCase):

    def setUp(self):
        self.file_four = PosixPathMock(
            "/home/test_user/dir_tmp/dir_sub/file_four", is_file=True
        )
        self.dir_sub = PosixPathMock("/home/test_user/dir_tmp/dir_sub", is_dir=True)
        self.file_three = PosixPathMock(
            "/home/test_user/dir_tmp/file_three", is_file=True
        )
        self.fifo_two = PosixPathMock("/home/test_user/dir_tmp/fifo_two", is_fifo=True)
        self.file_one = PosixPathMock("/home/test_user/dir_tmp/file_one", is_file=True)
        self.dir_tmp = PosixPathMock("/home/test_user/dir_tmp", is_dir=True)
        self.path = PosixPathMock(
            "/home/test_user/**",
            glob=[
                self.file_four,
                self.dir_sub,
                self.file_three,
                self.fifo_two,
                self.file_one,
                self.dir_tmp,
            ],
        )
        patcher = patch("flutils.pathutils.normalize_path", return_value=self.path)
        self.normalize_path = patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch("flutils.pathutils.Path", return_value=self.path)
        self.path_func = patcher.start()
        self.addCleanup(patcher.stop)

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


class TestChmodEmptyGlob(unittest.TestCase):

    def setUp(self):
        self.path = PosixPathMock("/home/test_user/**")
        patcher = patch("flutils.pathutils.normalize_path", return_value=self.path)
        self.normalize_path = patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch("flutils.pathutils.Path", return_value=self.path)
        self.path_func = patcher.start()
        self.addCleanup(patcher.stop)

    def test_chmod_empty_glob(self):
        chmod("~/**", mode_file=432, mode_dir=504, include_parent=True)
        self.normalize_path.assert_called_with("~/**")
        self.path.glob.assert_called_with("/home/test_user/**")
        self.path.parent.chmod.assert_not_called()
