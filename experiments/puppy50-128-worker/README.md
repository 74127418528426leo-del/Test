# Puppy50 128-worker CPU Micro-Laboratory

This is an actual **128-task** benchmark: 4 local Linux data sets × 32 compressor configurations. It does **not** instantiate 128 LLM agents, GPU servers, or real Puppy50 virtual-machine boots.

## Architecture

Planner → bounded executor (4 slots) → 128 subprocess codec tests → three SHA256 decompression verifications per task → task ledger → sequential replay of promising configurations → report/artifact.

Run on Linux with Python 3, gzip, xz, zstd:

```bash
python3 experiments/puppy50-128-worker/experiment.py --output results --slots 4 --mib 1
```

Outputs: `all_128_tasks.csv`, `summary.json`, `REPORT.md`.

The workflow `.github/workflows/puppy50-128-worker-microlab.yml` is scoped to this experimental branch and checks all 128 jobs for success. It runs CPU testing on GitHub-hosted Ubuntu, not 128 individual GitHub runners.

**Limitation:** Samples come from local Linux files, not Puppy50's actual initramfs. These results cannot establish boot-time or Firefox-speed improvements. Next: run experiments on actual Puppy50 initramfs, then perform matched QEMU BIOS/UEFI boot tests and Firefox first-frame benchmarks.
