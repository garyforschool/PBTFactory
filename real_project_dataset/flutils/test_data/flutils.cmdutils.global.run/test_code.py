def test_static_types(self) -> None:
        cmd = "mypy -p flutils"
        with BytesIO() as stdout:
            return_code = run(cmd, stdout=stdout, stderr=stdout)
            text: bytes = stdout.getvalue()
        if return_code != 0:
            txt = text.decode(sys.getdefaultencoding())
            msg = """
mypy command: %s
return code:  %r
The following problems were found with mypy:

%s
""" % (
                cmd,
                return_code,
                txt,
            )
            self.fail(msg=msg)

def test_return_code(self) -> None:
        ret = run(["ls", "-Flap"], force_dimensions=True)
        self.popen.assert_called()
        self.assertEqual(ret, 0)

def test_bytes_command(self) -> None:
        with self.assertRaises(TypeError):
            run(b"ls -Flap")

def test_stdout(self) -> None:
        stdout = BytesIO()
        run("ls -Flap", stdout=stdout)
        self.shlex_split.assert_called_once_with("ls -Flap")
        self.assertEqual(stdout.getvalue(), b"foo\n")

def test_stderr(self) -> None:
        stderr = BytesIO()
        run("ls -Flap", stderr=stderr)
        self.shlex_split.assert_called_once_with("ls -Flap")
        self.assertEqual(stderr.getvalue(), b"bar\n")

def test_interactive(self) -> None:
        run("ls -Flap", interactive=True)
        self.popen.assert_called_with(
            ["/bin/bash", "-i", "-c", "ls", "-Flap"], stdout=20, stderr=40, stdin=20
        )

def test_encoding(self) -> None:
        run("ls -Flap", encoding="utf-8", stdout=sys.stdout)
        self.popen.assert_called_with(
            ["ls", "-Flap"], stdout=20, stderr=40, stdin=20, encoding="utf-8"
        )

def test_write_error(self) -> None:
        run("ls -Flap", encoding="utf-8")
        self.popen.assert_called_with(
            ["ls", "-Flap"], stdout=20, stderr=40, stdin=20, encoding="utf-8"
        )

def test_errno_eio(self) -> None:
        self.os_read.side_effect = [
            b"foo\n",
            b"bar\n",
            OSError(errno.EIO, "end of file"),
            OSError(errno.EIO, "end of file"),
        ]
        ret = run("ls -Flap")
        self.assertEqual(ret, 0)

def test_different_errno_eio(self) -> None:
        self.os_read.side_effect = [OSError(_get_different_eio(), "an error")]
        with self.assertRaises(OSError):
            run("ls -Flap")

def test_missing_bash(self) -> None:
        self.shutil_which.return_value = ""
        with self.assertRaises(RuntimeError):
            run("ls -Flap", interactive=True)