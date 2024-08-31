import ast
import json
import os
import shutil

import astor

from PBTFactory.code_under_test import code_under_test
from PBTFactory.get_code_helper import get_class_structure


def get_code_stdlib(path_to_data):
    with open(os.path.join(path_to_data, "setup_data.json")) as f:
        data = json.load(f)
    name = f"{data['package']}.{data['classname']}.{data['name']}"

    with open(os.path.join(path_to_data, "code.py")) as f:
        full_code = f.read()

    function_body = "\n".join(
        full_code.split("\n")[data["startline"] - 1 : data["endline"]]
    )

    max_line = 300
    hard_limit = 600
    test_lines = []
    with open(os.path.join(path_to_data, "test_code.py")) as f:
        test_lines_raw = f.read().split("\n")
    for line in test_lines_raw:
        if len(test_lines) > max_line and "def " in line:
            break
        if len(test_lines) > hard_limit:
            break
        if line.strip():
            test_lines.append(line)

    entry_point = (
        f"{data['classname']}.{data['name']}"
        if data["classname"] != "global"
        else data["name"]
    )

    class_structure = astor.to_source(get_class_structure(full_code, data["classname"]))

    cut = code_under_test(
        name,
        data["signature"],
        entry_point,
        function_body,
        "\n".join(test_lines),
        class_structure,
    )
    cut.module = data["package"]
    cut.start_line = data["startline"]
    cut.end_line = data["endline"]
    cut.path_to_data = path_to_data
    return cut


def setup_for_stdlib(cut: code_under_test, working_dir: str):
    project_path = os.path.join(working_dir, cut.id, "project")
    testdir = os.path.join(working_dir, cut.id, "tests")
    resultdir = os.path.join(working_dir, cut.id, "result")
    logdir = os.path.join(working_dir, cut.id, "log")

    os.makedirs(project_path, exist_ok=True)
    os.makedirs(testdir, exist_ok=True)
    os.makedirs(resultdir, exist_ok=True)
    os.makedirs(logdir, exist_ok=True)
    shutil.copyfile(
        os.path.join(cut.path_to_data, "code.py"),
        os.path.join(project_path, f"{cut.module}.py"),
    )

    return project_path, testdir, resultdir, logdir
