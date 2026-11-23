# Hermes and Qwen coding example

[The project brief](PROJECT.md) asks for a small scheduler that packs VM jobs
into RAM-limited waves while handling dependencies and input errors.

On the example branch, the **Puppy50 Hermes and Qwen** Actions workflow runs
the challenge on a CPU runner. Its manual **Task** input also offers the coding
example. Hermes gives Qwen one read-only tool to retrieve the brief. Qwen
returns the Python module, and a separate grader tests it in a temporary
container with networking disabled. The tool presents only the brief and,
when needed, short failure labels for one revision.

## Verified example

[Qwen's scheduler](scheduler.py) passed all 59 checks on its first submission
in the [GitHub Actions run](https://github.com/74127418528426leo-del/Test/actions/runs/45105301343).
Hermes Agent v0.23.3 read the brief once, and Qwen3.5-4B completed two inference
calls. The tests covered 19 named cases and 40 generated job graphs.

The checked-in source has normalized trailing whitespace. The Actions artifact
contains the original tested Python, its checksum, and the grading results.
