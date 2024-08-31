def test_call_return_code(self) -> None:
        rc = RunCmd(stderr=PIPE, stdout=PIPE)
        cwd = shlex.quote(os.path.abspath(os.getcwd()))
        cmd = f"ls {cwd}"
        res = rc(cmd)
        exp = 0
        msg = f"""

rc = RunCommand(stderr=PIPE, stdout=PIPE)

res = rc({cmd!r})

res.return_code={res.return_code!r}

exp: {exp!r}

"""
        self.assertEqual(res.return_code, exp, msg=msg)

def test_call_stdout(self) -> None:
        rc = RunCmd(stderr=PIPE, stdout=PIPE)
        cwd = shlex.quote(os.path.abspath(os.getcwd()))
        cmd = f"ls {cwd}"
        res = rc(cmd)
        exp = 0
        msg = f"""

rc = RunCommand(stderr=PIPE, stdout=PIPE)

res = rc({cmd!r})

res.stdout={res.return_code!r}

exp: len(res.stdout) > 0

"""
        self.assertTrue(len(res.stdout) > 0, msg=msg)

@unittest.skipUnless(GREP, "unable to find the grep command.")
    def test_call_raises_child_process_error(self):
        rc = RunCmd(raise_error=True, stderr=PIPE, stdout=PIPE)
        path = shlex.quote(PATH)
        cmd = f"{GREP} -q 'foobarfoobar' {path}"
        with self.assertRaises(ChildProcessError):
            rc(cmd)

def test_call_raises_file_not_found_error(self):
        rc = RunCmd(raise_error=True, stderr=PIPE, stdout=PIPE)
        cmd = f"foobarfoobar"
        with self.assertRaises(FileNotFoundError):
            rc(cmd)