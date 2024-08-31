import importlib
import inspect
import json
import os
import shutil

from mutmut import mutmut


def main(html_report="mutmut_report", json_report="mutmut_report/report.json"):
    shutil.copytree("/workdir/tests", "/workdir/tests_copy", dirs_exist_ok=True)

    mutmut_config = mutmut.MutmutConfig()
    mutmut_config.paths_to_mutate = [
        inspect.getfile(importlib.import_module(os.environ["module_name"]))
    ]
    mutmut_config.tests_dir = "/workdir/tests_copy"

    if os.environ.get("line_start") and os.environ.get("line_end"):
        mutmut_config.line_start = int(os.environ["line_start"])
        mutmut_config.line_end = int(os.environ["line_end"])

    print(
        mutmut_config.paths_to_mutate,
        mutmut_config.tests_dir,
        mutmut_config.line_start,
        mutmut_config.line_end,
    )

    mutmut.run(mutmut_config)
    mutmut.html(["Struct", "NamedStruct"], html_report)
    json.dump(mutmut.create_report(), open(json_report, "w", encoding="utf-8"))


if __name__ == "__main__":
    main()
