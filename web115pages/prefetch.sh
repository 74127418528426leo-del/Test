#!/bin/sh
# Test-only, best-effort, read-only speculative cache warmup.
printf 'P50_TARGET_PREFETCH_BEGIN %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
/run/p50-stage/tools/p50-prefetch /run/p50-stage/tools/hotpages-plan.tsv >/run/p50-stage/prefetch.log 2>&1
rc=$?
cat /run/p50-stage/prefetch.log >/dev/ttyS0
printf 'P50_TARGET_PREFETCH_END rc=%s uptime=%s\n' "$rc" "$(cat /proc/uptime)" >/dev/ttyS0
exit "$rc"
