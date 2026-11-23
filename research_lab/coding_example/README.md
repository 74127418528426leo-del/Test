# Hermes and Qwen coding example

[The project brief](PROJECT.md) asks for a small scheduler that packs VM jobs
into RAM-limited waves while handling dependencies and input errors.

On the example branch, the **Puppy50 Hermes and Qwen** Actions workflow runs
the challenge on a CPU runner. Its manual **Task** input also offers the coding
example. Hermes gives Qwen one read-only tool to retrieve the brief. Qwen
returns the Python module, and a separate grader tests it in a temporary
container with networking disabled. The tool presents only the brief and,
when needed, short failure labels for one revision.

The Actions summary lists the number of checks passed. Each run's artifact
contains the exact model-written Python, tool call counts, and test results.
