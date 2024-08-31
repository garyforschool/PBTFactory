import ast
import os
import random
import typing as T

import astor
from evalplus.data import get_human_eval_plus

from PBTFactory.code_under_test import code_under_test


def remove_comments(source):
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.ClassDef):
            if ast.get_docstring(node):
                node.body = node.body[1:]
    return astor.to_source(tree)


def get_problem(id: T.Optional[str] = None) -> T.Tuple[str, dict]:
    problems = get_human_eval_plus()
    if id and id in problems:
        return id, problems[id]

    problem = random.choice(list(problems.values()))
    return problem["task_id"], problem


def get_problem_function(problem: dict) -> str:
    return remove_comments(problem["prompt"] + "\n" + problem["canonical_solution"])


def get_problem_test(problem: dict) -> str:
    test = []
    test_start = False
    for line in problem["test"].split("\n"):
        if line.startswith("def"):
            test.append(line.replace("candidate", ""))
            test_start = True
        elif test_start:
            if line:
                test.append(line.replace("candidate", problem["entry_point"]))
    return "\n".join(test)


def get_code_evalplus(id: str = None) -> code_under_test:
    task_id, problem = get_problem(id)
    function_body = get_problem_function(problem)
    test = get_problem_test(problem)
    entry_point = problem["entry_point"]
    signature = ""
    for line in function_body.split("\n"):
        if line.startswith("def") and entry_point in line:
            signature = line
            break
    module = f"{task_id.replace('/', '_')}_{entry_point}"
    cut = code_under_test(module, signature, entry_point, function_body, test)
    cut.module = module
    return cut


def setup_for_evalplus(code: code_under_test, working_dir: str):
    project_path = os.path.join(working_dir, code.module, "project")
    testdir = os.path.join(working_dir, code.module, "tests")
    resultdir = os.path.join(working_dir, code.module, "result")
    logdir = os.path.join(working_dir, code.module, "log")

    os.makedirs(project_path, exist_ok=True)
    os.makedirs(testdir, exist_ok=True)
    os.makedirs(resultdir, exist_ok=True)
    os.makedirs(logdir, exist_ok=True)

    with open(os.path.join(project_path, f"{code.module}.py"), "w") as f:
        f.write(code.function_body)

    return project_path, testdir, resultdir, logdir
