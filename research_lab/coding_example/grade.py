"""Grade a submitted scheduler inside the disposable coding-example container."""

import ast
import builtins
import json
import random
import sys
from collections import namedtuple
from copy import deepcopy
from pathlib import Path

SAFE_BUILTINS = {
    name: getattr(builtins, name)
    for name in (
        "ValueError", "all", "any", "bool", "dict", "enumerate", "int", "isinstance",
        "len", "list", "max", "min", "range", "reversed", "set", "sorted", "str",
        "sum", "tuple", "zip",
    )
}
SAFE_METHODS = {
    "add", "append", "clear", "copy", "difference", "discard", "extend", "get",
    "intersection", "issubset", "items", "keys", "pop", "remove", "sort", "update", "values",
}
Case = namedtuple("Case", "label jobs limit expected")


def load_scheduler(source):
    tree = ast.parse(source, filename="submission.py")
    if not tree.body or any(not isinstance(node, ast.FunctionDef) for node in tree.body):
        raise ValueError("submit Python function definitions at module scope")
    names = {node.name for node in tree.body}
    if "plan_runs" not in names:
        raise ValueError("missing plan_runs(jobs, memory_limit)")
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.ClassDef, ast.Delete, ast.Global, ast.Nonlocal)):
            raise ValueError("use only functions and Python built-in data structures")
        if isinstance(node, ast.Attribute) and node.attr not in SAFE_METHODS:
            raise ValueError("use only ordinary list, dict, and set methods")
        if isinstance(node, ast.Name) and node.id.startswith("__"):
            raise ValueError("do not access Python internals")
        if isinstance(node, ast.FunctionDef) and (node.decorator_list or node.name.startswith("__")):
            raise ValueError("use ordinary function definitions")
    namespace = {"__builtins__": SAFE_BUILTINS}
    exec(compile(tree, "submission.py", "exec"), namespace)
    return namespace["plan_runs"]


def job(label, ram, priority=0, needs=()):
    return {"id": label, "ram": ram, "priority": priority, "needs": list(needs)}


def named_cases():
    return (
        Case("empty input", [], 5, []),
        Case("exact fit", [job("a", 10)], 10, [["a"]]),
        Case("skip nonfitting job", [job("a", 6, 5), job("b", 5, 4), job("c", 4, 3)], 10, [["a", "c"], ["b"]]),
        Case("dependent waits for next wave", [job("parent", 2), job("child", 2, 8, ["parent"])], 10,
             [["parent"], ["child"]]),
        Case("tie uses ascending ID", [job("z", 4), job("b", 4), job("a", 4)], 8, [["a", "b"], ["z"]]),
        Case("higher priority, including negative values", [job("a", 5, -6), job("z", 5, -1)], 5, [["z"], ["a"]]),
        Case("wait for every dependency", [job("compile", 6), job("media", 5), job("boot", 1, 9, ["compile", "media"])],
             10, [["compile"], ["media"], ["boot"]]),
        Case("release a new high-priority job", [job("a", 6, 8), job("b", 6, 7), job("c", 4, 20, ["a"])],
             10, [["a"], ["c", "b"]]),
        Case("diamond dependency", [job("a", 1), job("b", 1, 3, ["a"]), job("c", 1, 4, ["a"]),
                                    job("d", 1, 8, ["b", "c"])], 10, [["a"], ["c", "b"], ["d"]]),
        Case("duplicate prerequisite has one meaning", [job("start", 1), job("end", 2, 8, ["start", "start"])],
             5, [["start"], ["end"]]),
        Case("zero memory limit", [], 0, None),
        Case("negative memory limit", [job("a", 1)], -1, None),
        Case("zero RAM job", [job("a", 0)], 4, None),
        Case("negative RAM job", [job("a", -2)], 5, None),
        Case("oversize job", [job("a", 6)], 5, None),
        Case("duplicate IDs", [job("a", 1), job("a", 2)], 5, None),
        Case("unknown dependency", [job("a", 2, needs=["missing"])], 5, None),
        Case("self dependency", [job("a", 2, needs=["a"])], 5, None),
        Case("cycle after a valid wave", [job("start", 1), job("a", 1, needs=["b"]), job("b", 1, needs=["a"])],
             5, None),
    )


def generated_cases():
    rng = random.Random(374)
    for _ in range(40):
        limit = rng.randint(3, 16)
        jobs = []
        for index in range(rng.randint(2, 11)):
            prerequisites = [old["id"] for old in jobs if rng.randrange(4) == 0]
            jobs.append(job(f"vm-{index:02}", rng.randint(1, limit), rng.randint(-3, 3), prerequisites))

        # Independent oracle: freeze eligibility as a wave number per job.
        ordered = sorted(jobs, key=lambda item: (-item["priority"], item["id"]))
        assigned = {}
        while len(assigned) != len(ordered):
            wave = max(assigned.values(), default=0) + 1
            used = 0
            for item in ordered:
                if item["id"] in assigned:
                    continue
                if any(assigned.get(need, wave) >= wave for need in item["needs"]):
                    continue
                if used + item["ram"] <= limit:
                    used += item["ram"]
                    assigned[item["id"]] = wave
        expected = [
            [label for label in assigned if assigned[label] == wave]
            for wave in range(1, max(assigned.values()) + 1)
        ]
        rng.shuffle(jobs)
        yield Case("generated job graph", jobs, limit, expected)


def failures_for(plan, cases):
    failures = []
    for case in cases:
        jobs = deepcopy(case.jobs)
        try:
            result = plan(jobs, case.limit)
        except ValueError:
            correct = case.expected is None
        except BaseException:
            correct = False
        else:
            correct = type(result) is list and result == case.expected
        if not correct:
            failures.append(case.label)
        elif jobs != case.jobs:
            failures.append("input mutation")
    return failures


def main():
    cases = [*named_cases(), *generated_cases()]
    try:
        plan = load_scheduler(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except SyntaxError as error:
        failures = [f"Python syntax error on line {error.lineno}"]
        passed = 0
    except ValueError as error:
        failures = [str(error)]
        passed = 0
    except BaseException:
        failures = ["submission failed while loading its function definitions"]
        passed = 0
    else:
        failures = failures_for(plan, cases)
        passed = len(cases) - len(failures)
    print(json.dumps({"passed": passed, "total": len(cases), "failures": sorted(set(failures))}))


if __name__ == "__main__":
    main()
