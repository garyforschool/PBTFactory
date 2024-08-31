import errno
import fcntl
import os
import pty
import shlex
import shutil
import struct
import subprocess
import sys
import termios
from collections import UserString
from copy import copy
from itertools import chain
from select import select
from subprocess import Popen
from typing import Any, IO, List, NamedTuple, Optional, Sequence, TextIO, Tuple, cast
from flutils.codecs import get_encoding
from flutils.namedtupleutils import to_namedtuple

try:
    from functools import cached_property
except ImportError:
    from flutils.decorators import cached_property
__all__ = ["run", "prep_cmd", "CompletedProcess", "RunCmd"]


def _set_size(fd: int, columns: int = 80, lines: int = 20) -> None:
    size = struct.pack("HHHH", lines, columns, 0, 0)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, size)


def run(
    command: Sequence,
    stdout: Optional[IO] = None,
    stderr: Optional[IO] = None,
    columns: int = 80,
    lines: int = 24,
    force_dimensions: bool = False,
    interactive: bool = False,
    **kwargs: Any,
) -> int:
    if hasattr(command, "decode"):
        raise TypeError(
            "The given 'command' must be of type: str, List[str] or Tuple[str]."
        )
    cmd: List[str]
    if hasattr(command, "capitalize"):
        command = cast(str, command)
        cmd = list(shlex.split(command))
    else:
        cmd = list(command)
    if interactive is True:
        bash = shutil.which("bash")
        if not bash:
            raise RuntimeError(
                "Unable to run the command:  %r, in interactive mode because 'bash' could NOT be found on the system."
                % " ".join(command)
            )
        cmd = [bash, "-i", "-c"] + cmd
    if stdout is None:
        stdout = sys.stdout
    stdout = cast(IO, stdout)
    if stderr is None:
        stderr = sys.stderr
    stderr = cast(IO, stderr)
    if force_dimensions is False:
        columns, lines = shutil.get_terminal_size(fallback=(columns, lines))
    masters, slaves = zip(pty.openpty(), pty.openpty())
    try:
        for fd in chain(masters, slaves):
            _set_size(fd, columns=columns, lines=lines)
        kwargs["stdout"] = slaves[0]
        kwargs["stderr"] = slaves[1]
        if "stdin" not in kwargs.keys():
            kwargs["stdin"] = slaves[0]
        with Popen(cmd, **kwargs) as p:
            for fd in slaves:
                os.close(fd)
            readable = {masters[0]: stdout, masters[1]: stderr}
            while readable:
                for fd in select(readable, [], [])[0]:
                    try:
                        data = os.read(fd, 1024)
                    except OSError as e:
                        if e.errno != errno.EIO:
                            raise
                        del readable[fd]
                    else:
                        if not data:
                            del readable[fd]
                        else:
                            if hasattr(readable[fd], "encoding"):
                                obj = readable[fd]
                                obj = cast(TextIO, obj)
                                data_str = data.decode(obj.encoding)
                                readable[fd].write(data_str)
                            else:
                                readable[fd].write(data)
                            readable[fd].flush()
    finally:
        for fd in chain(masters, slaves):
            try:
                os.close(fd)
            except OSError:
                pass
    return p.returncode


def prep_cmd(cmd: Sequence) -> Tuple[str, ...]:
    if not hasattr(cmd, "count") or not hasattr(cmd, "index"):
        raise TypeError(
            "The given 'cmd', %r, must be of type: str, bytes, list or tuple.  Got: %r"
            % (cmd, type(cmd).__name__)
        )
    if hasattr(cmd, "append"):
        out = copy(cmd)
    else:
        out = cmd
    if hasattr(out, "decode"):
        out = cast(bytes, out)
        out = out.decode(get_encoding())
    if hasattr(out, "encode"):
        out = cast(str, out)
        out = shlex.split(out)
    out = tuple(out)
    out = cast(Tuple[str], out)
    item: str
    for x, item in enumerate(out):
        if not isinstance(item, (str, UserString)):
            raise TypeError(
                "Item %r of the given 'cmd' is not of type 'str'.  Got: %r"
                % (x, type(item).__name__)
            )
    return out


class CompletedProcess(NamedTuple):
    return_code: int
    stdout: str
    stderr: str
    cmd: str


class RunCmd:

    def __init__(
        self,
        raise_error: bool = True,
        output_encoding: Optional[str] = None,
        **default_kwargs: Any,
    ) -> None:
        self.raise_error: bool = raise_error
        if not hasattr(output_encoding, "encode"):
            output_encoding = ""
        output_encoding = cast(str, output_encoding)
        self._output_encoding: str = output_encoding
        self.default_kwargs: Any = to_namedtuple(default_kwargs)
        self.default_kwargs = cast(NamedTuple, self.default_kwargs)

    @cached_property
    def output_encoding(self) -> str:
        return get_encoding(self._output_encoding)

    def __call__(self, cmd: Sequence, **kwargs: Any) -> CompletedProcess:
        cmd = prep_cmd(cmd)
        cmd = cast(Tuple[str, ...], cmd)
        keyword_args = self.default_kwargs._asdict()
        keyword_args.update(kwargs)
        result = subprocess.run(cmd, **keyword_args)
        cmd = shlex.join(cmd)
        cmd = cast(str, cmd)
        stdout = result.stdout.decode(self.output_encoding)
        stderr = result.stderr.decode(self.output_encoding)
        if self.raise_error is True:
            if result.returncode != 0:
                raise ChildProcessError(
                    f"""Unable to run the command {cmd!r}:

 {stdout} {stderr} Return code: {result.returncode}"""
                )
        return CompletedProcess(
            return_code=result.returncode, stdout=stdout, stderr=stderr, cmd=cmd
        )
