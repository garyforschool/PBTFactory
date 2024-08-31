import os
import textwrap

from PBTFactory.chat import Chat
from PBTFactory.cut_data import CUT_data
from PBTFactory.eval_code import run_pytest
from PBTFactory.message import MessageManager, find_code
from PBTFactory.pipeline import Pipeline


class pipeline_unit_test_baseline(Pipeline):
    def run(self):
        for i in range(self.max_retry * 2):
            bug_free, logs, err = self.create_pbt(MessageManager())
            if bug_free:
                break
        return self.chat.total_time

    def create_pbt(self, mm: MessageManager):
        test = self.cut_data.cut.test
        if test:
            test = f"Test:\n```python\n{test}\n```\n\n"
        prompt = textwrap.dedent(
            """\
            Create more unit tests for the function {}. Code under test is already imported, do not implement it again.
            Import the function with:
            from {} import {}

            Function:
            ```python
            {}
            ```
            {}
            
            Make sure the new tests are meaningful."""
        ).format(
            self.cut_data.cut.entry_point,
            self.cut_data.cut.module,
            self.import_name,
            self.cut_data.cut.function_body,
            test,
        )
        mm.add_user_message(prompt)
        msg = self.chat.ask(mm, "create_unit")
        mm.add_assistant_message(msg)
        filename = os.path.join(self.cut_data.testdir, "test_unit.py")
        exit_code, logs, logs_err = self.test_pbts(find_code(msg), filename)

        for i in range(self.max_fix):
            if exit_code == 0:
                break
            msg = self.ask_fix_code(mm, logs_err, extra_msg="", step_name="fix_test")
            exit_code, logs, logs_err = self.test_pbts(find_code(msg), filename)
        if exit_code != 0:
            os.remove(filename)
        return exit_code == 0, logs, logs_err

    def test_pbts(self, code, filename):
        with open(filename, "w") as f:
            f.write(
                "import warnings\nfrom hypothesis.errors import NonInteractiveExampleWarning\nwarnings.filterwarnings('ignore', category=NonInteractiveExampleWarning)\nwarnings.filterwarnings('ignore', category=DeprecationWarning)\n\n"
            )
            f.write("import math\n")
            f.write("import pytest\n")
            f.write(f"from {self.cut_data.cut.module} import {self.import_name}\n")

            for line in code.split("\n"):
                if "import" in line and self.import_name in line:
                    line = f"from {self.cut_data.cut.module} import {self.import_name}"
                f.write(line + "\n")

        exit_code, logs, logs_err, time_taken, timeouted = run_pytest(
            filename,
            self.cut_data.project_path,
            self.cut_data.logdir,
            timeout_msg=f"PBTs timeout. {self.cut_data.cut.id}, {filename}",
        )
        return exit_code, logs, logs_err
