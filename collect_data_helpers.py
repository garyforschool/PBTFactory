import json
import os
import random
import typing as T
from dataclasses import dataclass
from random import choices
from statistics import mean


class IResult:
    filename: str
    error_codes: list

    def error_rate(self) -> float:
        raise NotImplementedError()

    def mutation_score(self) -> float:
        raise NotImplementedError()

    def coverage(self) -> float:
        raise NotImplementedError()

    def __str__(self):
        return f"{self.filename} {self.error_rate()} {self.mutation_score()} {self.coverage()}"


@dataclass(frozen=True)
class SimpleResult(IResult):
    filename: str
    error_codes: list

    mutation_score_: float
    coverage_: float

    def error_rate(self) -> bool:
        return len(self.error_codes)

    def mutation_score(self) -> float:
        return self.mutation_score_

    def coverage(self) -> float:
        return self.coverage_

    def get_number_of_mutants(self) -> int:
        return len(self.killed_ids | self.survived_ids)

    def get_number_lines(self) -> int:
        return len(self.executed_lines | self.missing_lines)


@dataclass(frozen=True)
class EvalResult(IResult):
    filename: str
    error_codes: list

    killed_ids: set
    survived_ids: set

    executed_lines: set
    missing_lines: set

    complexity: int
    retry_count: float = 0
    create_rate: float = 0
    aggregation_count: bool = 0

    def get_number_of_mutants(self) -> int:
        return len(self.killed_ids | self.survived_ids)

    def get_number_lines(self) -> int:
        return len(self.executed_lines | self.missing_lines)

    def mutation_score(self) -> float:
        if self.get_number_of_mutants() == 0:
            return 0
        return len(self.killed_ids) / self.get_number_of_mutants()

    def coverage(self) -> float:
        if self.get_number_lines() == 0:
            return 0
        return len(self.executed_lines) / self.get_number_lines()

    def error_rate(self) -> float:
        if self.get_number_lines() == 0 or self.get_number_of_mutants() == 0:
            return 1
        return 0

    def merge(self, other: "EvalResult") -> "EvalResult":
        """
        Merge two results together, it is same as collect test create from each round, put them together and evaluate.
        """
        assert self.filename == other.filename

        if self.error_rate() + other.error_rate() == 2:
            return EvalResult(
                self.filename,
                list(set(self.error_codes + other.error_codes)),
                set(),
                set(),
                set(),
                set(),
                0,
                0,
                0,
                0,
            )

        if self.error_rate() == 1:
            return other
        elif other.error_rate() == 1:
            return self

        assert self.get_number_lines() == other.get_number_lines()
        assert (
            self.get_number_of_mutants() == other.get_number_of_mutants()
        ), f"{self.filename} {self.get_number_of_mutants()} {other.get_number_of_mutants()}"

        new_result = EvalResult(
            self.filename,
            [],
            self.killed_ids | other.killed_ids,
            self.survived_ids & other.survived_ids,
            self.executed_lines | other.executed_lines,
            self.missing_lines & other.missing_lines,
            max(self.complexity, other.complexity),
            (
                self.retry_count * self.aggregation_count
                + other.retry_count * other.aggregation_count
            )
            / (self.aggregation_count + other.aggregation_count),
            (
                self.create_rate * self.aggregation_count
                + other.create_rate * other.aggregation_count
            )
            / (self.aggregation_count + other.aggregation_count),
            self.aggregation_count + other.aggregation_count,
        )

        assert new_result.get_number_lines() == self.get_number_lines()
        assert (
            new_result.get_number_of_mutants() == self.get_number_of_mutants()
        ), f"{new_result.get_number_of_mutants()} {self.get_number_of_mutants()}"

        return new_result

    @staticmethod
    def from_dict(data):
        if "error_code" not in data:
            return EvalResult(
                data["filename"],
                [],
                set(data["killed_ids"] + data["suspicious_ids"]),
                set(data["survived_ids"] + data["timeout_ids"]),
                set(data["coverage"]["executed_lines"]),
                set(data["coverage"]["missing_lines"]),
                data["complexity"],
                data["retry_count"],
                data["create_rate"],
                1,
            )
        else:
            return EvalResult(
                data["filename"],
                [data["error_code"]],
                set(),
                set(),
                set(),
                set(),
                0,
                0,
                0,
                0,
            )

    @staticmethod
    def merge_results(data: T.List["EvalResult"]) -> "EvalResult":
        assert len(data) > 0
        new_result = data[0]
        for d in data[1:]:
            new_result = new_result.merge(d)
        return new_result


import ast

# import mccabe


def get_mccabe_complexity(filename: str) -> int:
    return -1
    code = mccabe._read(filename)
    tree = compile(code, filename, "exec", ast.PyCF_ONLY_AST)
    visitor = mccabe.PathGraphingAstVisitor()
    visitor.preorder(tree, visitor)
    complexity = []
    for graph in visitor.graphs.values():
        # if "test" in graph.name:
        complexity.append(graph.complexity())
    return sum(complexity)


def get_create_error_rate(path_to_data):
    fix_names = []
    for i in sorted(
        [
            x
            for x in os.listdir(os.path.join(path_to_data, "log/msg"))
            if "fix_code_pbt" in x and x.endswith(".json")
        ]
    ):
        parts = i.replace(" ", "_").split("_")[4:]  # remove the num and 'fix_code_pbt'
        fix_names.append("_".join(parts)[:-9])  # remove the .txt.json
    prop_names = []
    for i in sorted(
        [
            x
            for x in os.listdir(os.path.join(path_to_data, "log/msg"))
            if "create_test" in x and x.endswith(".json")
        ]
    ):
        parts = i.replace(" ", "_").split("_")[3:]  # remove the num and 'create_test'
        prop_names.append("_".join(parts)[:-9])  # remove the .txt.json
    for i in sorted(
        [
            x
            for x in os.listdir(os.path.join(path_to_data, "log/msg"))
            if x.endswith("create_pbt.txt.json")
        ]
    ):
        prop_names.append("pbt")
    for i in sorted(
        [
            x
            for x in os.listdir(os.path.join(path_to_data, "log/msg"))
            if x.endswith("create_unit.txt.json")
        ]
    ):
        prop_names.append("unit")
    test_names = []
    for i in sorted(
        [
            x
            for x in os.listdir(os.path.join(path_to_data, "tests"))
            if "test" in x and x.endswith(".py")
        ]
    ):
        parts = i.replace(" ", "_").split("_")[1:]  # remove 'tests'
        test_names.append("_".join(parts)[:-3])  # remove the .py
    if len(test_names) == 0 or len(prop_names) == 0:
        return -1, -1
    return mean([prop_names.count(k) for k in test_names]) - 1, len(test_names) / len(
        set(prop_names)
    )

result_cache = {}

def get_all_results(data_dir) -> T.List[EvalResult]:
    data = []
    for path in sorted(os.listdir(data_dir)):
        report = os.path.join(data_dir, path, "result/parsed_report.json")
        if report in result_cache:
            data.append(result_cache[report])
            continue
        if not os.path.exists(report):
            continue
        tests = [
            os.path.join(data_dir, path, "tests", x)
            for x in sorted(os.listdir(os.path.join(data_dir, path, "tests")))
            if "test" in x
        ]
        if tests:
            tests_complexity = mean([get_mccabe_complexity(x) for x in tests])
        else:
            tests_complexity = 0
        retry_count, create_rate = get_create_error_rate(os.path.join(data_dir, path))
        with open(report) as f:
            json_data = json.load(f)
            json_data["complexity"] = tests_complexity
            json_data["retry_count"] = retry_count
            json_data["create_rate"] = create_rate
            eval_result = EvalResult.from_dict(json_data)
            data.append(eval_result)
            result_cache[report] = eval_result
    return data


def filter_keep_correct(data: T.List[T.List[EvalResult]]) -> T.List[str]:
    filename_all_correct = {}
    for row in data:
        for cell in row:
            if cell.error_rate() == 0:
                if cell.filename not in filename_all_correct:
                    filename_all_correct[cell.filename] = 1
            else:
                filename_all_correct[cell.filename] = 0
    all_correct = []
    for k, v in filename_all_correct.items():
        if v == 1:
            all_correct.append(k)
    return all_correct


def get_summary_for_one_round(data: T.List[IResult]) -> T.Dict[str, T.Any]:
    total_rounds = 0
    total_rounds_success = 0
    total_error = 0
    error_codes = {}
    mutation_score_total = 0
    cov_total = 0
    total_retry_count = 0
    total_create_rate = 0

    for result in data:
        total_rounds += 1
        if not result.error_codes:
            total_rounds_success += 1
            mutation_score_total += result.mutation_score()
            cov_total += result.coverage()
            total_retry_count += result.retry_count
            total_create_rate += result.create_rate
        else:
            total_error += 1
            error_codes[result.filename] = result.error_codes

    summary = {}

    if total_rounds_success > 0:
        summary["mutation_score_avg"] = mutation_score_total / total_rounds_success
        summary["coverage_avg"] = cov_total / total_rounds_success
        summary["retry_count_avg"] = total_retry_count / total_rounds_success
        summary["create_rate_avg"] = total_create_rate / total_rounds_success

    summary["total"] = total_rounds
    summary["error_percent"] = total_error / total_rounds
    summary["error_codes"] = error_codes
    return summary


def cumulate_results(data: T.List[T.List[EvalResult]]) -> T.List[EvalResult]:
    data = [x for y in data for x in y]
    file_names = set([x.filename for x in data])
    results = []
    for f in file_names:
        results.append(EvalResult.merge_results([x for x in data if x.filename == f]))
    return results


def get_summary_average_for_all_round(
    data: T.List[T.List[IResult]],
) -> T.Dict[str, T.Any]:
    summary = [get_summary_for_one_round(x) for x in data]
    assert (
        len(set([x["total"] for x in summary])) == 1
    ), "All rounds should have the same number of functions"
    mutation_score_avg = mean([x["mutation_score_avg"] for x in summary])
    coverage_avg = mean([x["coverage_avg"] for x in summary])
    error_percent = mean([x["error_percent"] for x in summary])
    retry_count_avg = mean([x["retry_count_avg"] for x in summary])
    create_rate_avg = mean([x["create_rate_avg"] for x in summary])
    errors = [x["error_codes"] for x in summary if x["error_percent"] > 0]
    total = summary[0]["total"]
    return {
        "mutation_score_avg": mutation_score_avg,
        "coverage_avg": coverage_avg,
        "error_percent": error_percent,
        "total": total,
        "errors": errors,
        "retry_count_avg": retry_count_avg,
        "create_rate_avg": create_rate_avg,
    }


def compare(data1: T.List[IResult], data2: T.List[IResult]) -> T.Tuple[
    T.List[T.Tuple[IResult, IResult]],
    T.List[T.Tuple[IResult, IResult]],
    T.List[T.Tuple[IResult, IResult]],
]:
    data1_is_better = []
    data2_is_better = []
    same = []

    keys1 = set([x.filename for x in data1])
    keys2 = set([x.filename for x in data2])
    assert keys1 == keys2, "The two data sets should have the same keys"
    for key in sorted(list(keys1)):
        a = [x for x in data1 if x.filename == key]
        b = [x for x in data2 if x.filename == key]
        assert len(a) == len(b) == 1, "Each key should have only one result"

        a = a[0]
        b = b[0]

        if a.error_rate() == 1 and b.error_rate() == 1:
            same.append((a, b))
        elif a.error_rate() == 1:
            data2_is_better.append((a, b))
        elif b.error_rate() == 1:
            data1_is_better.append((a, b))
        else:
            if a.mutation_score() > b.mutation_score():
                data1_is_better.append((a, b))
            elif a.mutation_score() < b.mutation_score():
                data2_is_better.append((a, b))
            else:
                if a.coverage() > b.coverage():
                    data1_is_better.append((a, b))
                elif a.coverage() < b.coverage():
                    data2_is_better.append((a, b))
                else:
                    same.append((a, b))
    return (data1_is_better, same, data2_is_better)


def print_table(table1, keys=None, table2=None):
    if keys is None:
        keys = [
            "Pipeline",
            "Mutation Score",
            "Coverage",
            "Success Rate",
            "Create Rate",
            "Retry Count",
            "Total",
        ]
    print("|" + "|".join([f" {key} " for key in keys]) + "|")
    print("|" + "|".join([" --- " for key in keys]) + "|")
    if table2 is None:
        for obj in table1:
            s = []
            for k in keys:
                if k == "Pipeline":
                    s.append(f"{obj['pipeline']}")
                elif k == "Mutation Score":
                    s.append(f"{obj['mutation_score_avg']*100:.0f}%")
                elif k == "Coverage":
                    s.append(f"{obj['coverage_avg']*100:.0f}%")
                elif k == "Success Rate":
                    s.append(f"{100-obj['error_percent']*100:.0f}%")
                elif k == "Create Rate":
                    s.append(f"{obj['create_rate_avg']*100:.0f}%")
                elif k == "Retry Count":
                    s.append(f"{obj['retry_count_avg']:.1f}")
                elif k == "Total":
                    s.append(f"{obj['total']:.1f}")
                else:
                    raise Exception(f"Invalid key {key}")
            print("| " + " | ".join(s) + " |")
    else:
        for obj, obj2 in zip(table1, table2):
            assert obj["pipeline"] == obj2["pipeline"]
            s = []
            for k in keys:
                if k == "Pipeline":
                    s.append(f"{obj['pipeline']}")
                elif k == "Mutation Score":
                    s.append(
                        f"{obj['mutation_score_avg']*100:.0f}% / {obj2['mutation_score_avg']*100:.0f}%"
                    )
                elif k == "Coverage":
                    s.append(
                        f"{obj['coverage_avg']*100:.0f}% / {obj2['coverage_avg']*100:.0f}%"
                    )
                elif k == "Success Rate":
                    s.append(
                        f"{100-obj['error_percent']*100:.0f}% / {100-obj2['error_percent']*100:.0f}%"
                    )
                elif k == "Create Rate":
                    s.append(
                        f"{obj['create_rate_avg']*100:.0f}% / {obj2['create_rate_avg']*100:.0f}%"
                    )
                elif k == "Retry Count":
                    s.append(
                        f"{obj['retry_count_avg']:.1f} / {obj2['retry_count_avg']:.1f}"
                    )
                elif k == "Total":
                    s.append(f"{obj['total']:.1f} / {obj2['total']:.1f}")
                else:
                    raise Exception(f"Invalid key {key}")
            print("| " + " | ".join(s) + " |")


def load_from_folder(data_folder, num_of_runs):
    data = []
    run_data = sorted(
        [
            x
            for x in os.listdir(data_folder)
            if os.path.isdir(os.path.join(data_folder, x))
        ]
    )
    # if len(run_data) < num_of_runs:
    #     raise Exception(f"Not enough runs in folder: {data_folder}. Expected {num_of_runs}, got {len(run_data)}")
    if len(run_data) == 0:
        raise Exception(f"No runs in folder: {data_folder}")
    # run_data = run_data[:num_of_runs]
    run_data = random.sample(run_data, num_of_runs)
    # run_data = choices(run_data, k=num_of_runs)
    for x in run_data:
        data.append(get_all_results(os.path.join(data_folder, x)))
    return data


def average_tables(tables):
    if len(tables) == 0:
        return None
    pipeline_names = []
    t1 = tables[0]
    for obj in t1:
        pipeline_names.append(obj["pipeline"])
    for t in tables[1:]:
        for obj in t:
            if obj["pipeline"] not in pipeline_names:
                raise Exception(f"Pipeline {obj['pipeline']} not found in first table")
    new_table = []
    for pipeline in pipeline_names:
        objs = [x for x in t1 if x["pipeline"] == pipeline]
        for t in tables[1:]:
            objs += [x for x in t if x["pipeline"] == pipeline]
        new_obj = {}
        for key in objs[0].keys():
            if key == "pipeline":
                new_obj[key] = pipeline
            else:
                try:
                    new_obj[key] = sum([x[key] for x in objs]) / float(len(objs))
                except:
                    pass
        new_table.append(new_obj)
    return new_table



def get_summary(load_data, num_of_runs, all_correct=False):
    summary_datas = []
    for i in range(500):
        data = load_data(num_of_runs)
        if all_correct:
            data_all_correct_names = filter_keep_correct([cumulate_results(v) for k, v in data.items()])
            data_tmp = data
            data = {}
            for k, v in data_tmp.items():
                new_run_data = []
                for result in v:
                    tmp_result = []
                    for r in result:
                        if r.filename in data_all_correct_names:
                            tmp_result.append(r)
                    new_run_data.append(tmp_result)
                data[k] = new_run_data

        summary_data = []
        for key, value in data.items():
            summary = get_summary_for_one_round(cumulate_results(value))
            summary['pipeline'] = key
            summary_data.append(summary)

        summary_datas.append(summary_data)
    return average_tables(summary_datas)