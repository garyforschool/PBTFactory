from dataclasses import dataclass

from PBTFactory.code_under_test import code_under_test


@dataclass
class CUT_data:
    cut: code_under_test
    project_path: str
    testdir: str
    resultdir: str
    logdir: str
