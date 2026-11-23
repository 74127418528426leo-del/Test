# Puppy50 VM test scheduler

Implement one Python 3 function, `plan_runs(jobs, memory_limit)`.
It returns a list of waves. Each wave is a list of job IDs in launch order.
A wave represents jobs that can run together.

Each job is a dict with four keys.

| Key | Value |
|---|---|
| `id` | A nonempty string |
| `ram` | An integer in MiB |
| `priority` | An integer, where higher means earlier |
| `needs` | A list of prerequisite job IDs |

1. Before starting a wave, collect the remaining jobs whose prerequisites finished in **earlier waves**. Sort them by descending priority, then by ascending ID.
2. In that order, add every job that fits in the remaining RAM for the wave. Skip a job that does not fit and keep checking the rest. Every new wave starts with the full memory limit.
3. After the wave, mark its jobs complete. Repeat until every job is scheduled once.

Raise `ValueError` for a nonpositive memory limit, duplicate job IDs, a job with nonpositive RAM or RAM above the limit, an unknown prerequisite, or a dependency cycle (including self-dependency). An empty job list with a positive limit returns `[]`. Job order in the input does not break ties. Preserve all input data.

Inputs otherwise follow the types in the table. Use built-in Python functions and data structures, with no imports or other external dependencies.

## Example

Given a limit of 10 MiB:

```python
jobs = [
    {"id": "bios", "ram": 6, "priority": 10, "needs": []},
    {"id": "uefi", "ram": 5, "priority": 9, "needs": []},
    {"id": "network", "ram": 4, "priority": 5, "needs": []},
    {"id": "report", "ram": 2, "priority": 20, "needs": ["bios"]},
]
plan_runs(jobs, 10)
# [["bios", "network"], ["report", "uefi"]]
```
