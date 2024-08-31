import os
import shlex
import shutil
import unittest
from locale import getpreferredencoding
from subprocess import PIPE
from sys import getdefaultencoding
from typing import NamedTuple
from flutils.cmdutils import RunCmd, prep_cmd

PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "__init__.py"
)
ENCODING = getpreferredencoding() or getdefaultencoding()
GREP = shutil.which("grep")


class TestPrepCmd(unittest.TestCase):

    def test_bytes(self) -> None:
        arg = b"ls -flap"
        exp = tuple(shlex.split(arg.decode("utf-8")))
        got = prep_cmd(arg)
        msg = f"\n\nflutils.cmdutils.prep_cmd({arg!r})\n\nexp = {exp!r}got = {got!r}"
        self.assertEqual(got, exp, msg=msg)

    def test_str(self) -> None:
        arg = "ls -flap"
        exp = tuple(shlex.split(arg))
        got = prep_cmd(arg)
        msg = f"\n\nflutils.cmdutils.prep_cmd({arg!r})\n\nexp = {exp!r}got = {got!r}"
        self.assertEqual(got, exp, msg=msg)

    def test_list(self) -> None:
        arg = ["ls", "-flap"]
        exp = tuple(arg)
        got = prep_cmd(arg)
        msg = f"\n\nflutils.cmdutils.prep_cmd({arg!r})\n\nexp = {exp!r}got = {got!r}"
        self.assertEqual(got, exp, msg=msg)

    def test_tuple(self) -> None:
        arg = "ls", "-flap"
        exp = tuple(arg)
        got = prep_cmd(arg)
        msg = f"\n\nflutils.cmdutils.prep_cmd({arg!r})\n\nexp = {exp!r}got = {got!r}"
        self.assertEqual(got, exp, msg=msg)

    def test_non_sequence_raises(self) -> None:
        with self.assertRaises(TypeError):
            prep_cmd(1)
        with self.assertRaises(TypeError):
            prep_cmd(None)

    def test_non_str_item(self) -> None:
        with self.assertRaises(TypeError):
            prep_cmd(["ls", 1])


class Kwargs(NamedTuple):
    stderr: int = PIPE
    stdout: int = PIPE


class TestRunCmdClass(unittest.TestCase):

    def test_init_raise_error_value(self) -> None:
        rc = RunCmd(raise_error=False, output_encoding=1)
        msg = f"""

rc = RunCommand(raise_error=False, output_encoding=1)rc.raise_error={rc.raise_error!r}

exp: False"""
        self.assertEqual(rc.raise_error, False, msg=msg)

    def test_init_output_encoding_value(self) -> None:
        rc = RunCmd(raise_error=False, output_encoding=1)
        msg = f"""

rc = RunCommand(raise_error=False, output_encoding=1)

rc._output_encoding={rc._output_encoding!r}

exp: ''

"""
        self.assertEqual(rc._output_encoding, "", msg=msg)

    def test_init_default_kwargs(self) -> None:
        rc = RunCmd(stderr=PIPE, stdout=PIPE)
        exp = Kwargs()
        msg = f"""

rc = RunCommand(
  stderr=PIPE,
  stdout=PIPE,
)

rc.default_kwargs={rc.default_kwargs!r}

exp: {exp!r}"""
        self.assertEqual(rc.default_kwargs, exp, msg=msg)

    def test_output_encoding_no_value(self) -> None:
        rc = RunCmd()
        exp = ENCODING.lower()
        msg = f"""

rc = RunCommand(raise_error=False, output_encoding=1)

rc.output_encoding={rc.output_encoding!r}

exp: {exp!r}

"""
        self.assertEqual(rc.output_encoding, exp, msg=msg)

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
