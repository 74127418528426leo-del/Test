#!/bin/sh
# Read-only diagnostic collection. Use after a VM boot, review logs before sharing.
set -u
out="${1:-/tmp/puppy50-boot-trace}"
mkdir -p "$out" || exit 1
(cat /proc/uptime || true) > "$out/uptime.txt" 2>&1
(cat /proc/cmdline || true) > "$out/cmdline.txt" 2>&1
(cat /proc/meminfo || true) > "$out/meminfo.txt" 2>&1
(ps -eo pid,ppid,comm,etimes,rss,args || ps aux || true) > "$out/processes.txt" 2>&1
(command -v systemd-analyze >/dev/null && systemd-analyze time || true) > "$out/systemd-time.txt" 2>&1
(command -v systemd-analyze >/dev/null && systemd-analyze critical-chain || true) > "$out/systemd-critical-chain.txt" 2>&1
(command -v systemd-analyze >/dev/null && systemd-analyze blame || true) > "$out/systemd-blame.txt" 2>&1
(command -v journalctl >/dev/null && journalctl -b --no-pager -o short-monotonic || true) > "$out/journal.txt" 2>&1
(dmesg || true) > "$out/dmesg.txt" 2>&1
printf 'Collected startup logs under %s. Review and redact before sharing.\n' "$out"
