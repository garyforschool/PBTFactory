import sys
import unittest
from io import BytesIO
from flutils.cmdutils import run


class TestStaticTypes(unittest.TestCase):

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
