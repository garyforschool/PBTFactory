def test_set_size__1(self) -> None:
        ret = _set_size(22, 100, 50)
        self.assertEqual(ret, None)

def test_set_size__2(self) -> None:
        _set_size(22, 100, 50)
        self.struct_pack.assert_called_once_with("HHHH", 50, 100, 0, 0)

def test_set_size__3(self) -> None:
        _set_size(22, 100, 50)
        self.fcntl_ioctl.assert_called_once_with(22, termios.TIOCSWINSZ, 555)