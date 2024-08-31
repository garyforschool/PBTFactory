import json
import logging
import os

from PBTFactory.chat import Chat
from PBTFactory.cut_data import CUT_data
from PBTFactory.eval_code import (
    ERROR_READING_REPORT,
    NO_MUTANTS,
    NO_REPORT,
    NO_TESTS,
    TEST_ERROR,
    TIMEOUT,
    eval_with_mutmut,
)
from PBTFactory.message import MessageManager, count_code
from PBTFactory.request_manager import RequestType


class FileNotFoundError(Exception):
    pass


class IPipeline:
    def run(self) -> float:
        pass

    def have_finished(self) -> bool:
        pass

    def eval_test(self) -> dict:
        pass


class Pipeline(IPipeline):
    def __init__(
        self,
        cut_data: CUT_data,
        max_retry: int,
        max_fix: int,
        max_hypothesis_examples: int,
        system_message: str,
    ):

        self.cut_data = cut_data
        self.max_retry = max_retry
        self.max_fix = max_fix
        self.max_hypothesis_examples = max_hypothesis_examples
        self.failed_count = 0

        if "." in self.cut_data.cut.entry_point:
            self.import_name = self.cut_data.cut.entry_point.split(".")[0]
        else:
            self.import_name = self.cut_data.cut.entry_point

        self.chat = Chat(self.cut_data.logdir, system_message)

        os.makedirs(os.path.join(self.cut_data.logdir, "msg"), exist_ok=True)
        os.makedirs(os.path.join(self.cut_data.logdir, "fail"), exist_ok=True)

    def ask_fix_code(
        self,
        mm: MessageManager,
        err_msg: str,
        extra_msg: str = "",
        step_name="fix_code",
    ):
        err_msg_tmp = []
        for line in err_msg.split("\n"):
            if "-------------- 1 ------------" in line:
                err_msg_tmp = []
            err_msg_tmp.append(line)
        err_msg = "\n".join(err_msg_tmp)
        prompt = f"""Fix the error in the code. Explain what caused the error. Andxplain what you changed and why. Think step by step. Write your thought first. Show me full code after fix, do not omit any code, do not use placeholder.\n{extra_msg}\n{err_msg}"""
        mm.add_user_message(prompt)
        msg = self.chat.ask(mm, step_name)
        mm.add_assistant_message(msg)
        if count_code(msg) != 1:
            return self.ask_for_code_only(mm)
        return msg

    def ask_for_code_only(self, mm: MessageManager):
        mm2 = mm.copy()
        prompt = "You are correct. Base on above, collect the code only. Do not include the explanation. Give me one code block only."
        mm2.add_user_message(prompt)
        msg = self.chat.ask(mm2, "ask_code", RequestType.short_answer)
        mm2.add_assistant_message(msg)
        return msg

    def have_finished(self) -> bool:
        path_to_parsed_report = os.path.join(
            self.cut_data.resultdir, "parsed_report.json"
        )
        if os.path.exists(path_to_parsed_report):
            return True
        return False

    def eval_test(self):
        tests = [
            x
            for x in os.listdir(self.cut_data.testdir)
            if x.endswith(".py") and "test" in x
        ]

        if not tests:
            result = {
                "filename": self.cut_data.cut.id,
                "error": "No tests found",
                "error_code": NO_TESTS,
            }
            with open(
                os.path.join(self.cut_data.resultdir, "parsed_report.json"), "w"
            ) as f:
                json.dump(result, f)
            return result

        try:
            e_code, log, err, _, timeouted = eval_with_mutmut(
                self.cut_data.testdir,
                self.cut_data.project_path,
                self.cut_data.cut.module,
                self.cut_data.resultdir,
                self.cut_data.logdir,
                self.cut_data.cut.start_line,
                self.cut_data.cut.end_line + 1,
                timeout_msg=f"{self.cut_data.cut.id} timeout running mutmut",
            )
        except Exception as e:
            logging.error(f"Error running mutmut:\n{e}")
            raise e

        log_file_path = os.path.join(self.cut_data.logdir, "mutmut.log")
        with open(log_file_path, "w") as f:
            f.write(f"{e_code}\n{log}\n{err}")

        report_file_path = os.path.join(self.cut_data.resultdir, "report.json")
        if not os.path.exists(report_file_path):
            if timeouted:
                result = {"error": "Timeout running mutmut", "error_code": TIMEOUT}
            elif "Tests don't run cleanly without mutations." in log + err:
                result = {
                    "error": "Tests do not run cleanly without mutations",
                    "error_code": TEST_ERROR,
                }
            else:
                result = {"error": "No report.json", "error_code": NO_REPORT}
        else:
            try:
                with open(report_file_path, "r") as report_file:
                    results = json.load(report_file)
                    if len(results) == 0:
                        result = {
                            "error": "No results in report.json",
                            "error_code": NO_MUTANTS,
                        }
                    else:
                        result = results[0]
                        result["untested_ids"] = None  # remove untested_ids
            except Exception as e:
                result = {
                    "error": "Error reading report.json",
                    "error_code": ERROR_READING_REPORT,
                }

        coverage_file_path = os.path.join(
            self.cut_data.resultdir, "cov_report", "coverage.json"
        )
        if os.path.exists(coverage_file_path):
            result["coverage"] = self.parse_coverage(coverage_file_path)

        result["filename"] = self.cut_data.cut.id
        with open(
            os.path.join(self.cut_data.resultdir, "parsed_report.json"), "w"
        ) as f:
            json.dump(result, f)

        return result

    def parse_coverage(self, coverage_file_path):
        with open(coverage_file_path, "r") as f:
            coverage = json.load(f)
        file_names = coverage["files"].keys()
        potential_file_names = []
        for file_name in file_names:
            if "/usr/src/project" not in file_name:
                continue
            if self.cut_data.cut.filepath:
                if self.cut_data.cut.filepath in file_name:
                    potential_file_names.append(file_name)
            else:
                have_all_parts = True
                for part in self.cut_data.cut.module.split("."):
                    if part not in file_name:
                        have_all_parts = False
                        break
                if have_all_parts:
                    potential_file_names.append(file_name)

        if len(potential_file_names) == 1:
            file_name = potential_file_names[0]
            executed_lines = [
                x
                for x in coverage["files"][file_name]["executed_lines"]
                if self.cut_data.cut.start_line <= x <= self.cut_data.cut.end_line
            ]
            missing_lines = [
                x
                for x in coverage["files"][file_name]["missing_lines"]
                if self.cut_data.cut.start_line <= x <= self.cut_data.cut.end_line
            ]
            coverage = {
                "executed_lines": executed_lines,
                "missing_lines": missing_lines,
                "percentage": len(executed_lines)
                / len(executed_lines + missing_lines)
                * 100,
            }
        else:
            raise FileNotFoundError(
                f"Could not find coverage for {self.cut_data.cut.module}, have {potential_file_names}"
            )
        return coverage
