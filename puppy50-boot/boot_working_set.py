"""Learn the released root-image pages read before a genuine Firefox frame."""

import argparse
from pathlib import Path
import json
import re
import shutil
import subprocess
import time

from repack import replace_once

ROOT_SHA256 = '8c1bed5bcd3089f203e8afe1fcedae129af2c87408a57252be24f42adacac913'
CHUNK = 32 * 1024
BUDGET = 128 * 1024 * 1024
TRACE_READ = re.compile(r'\bblk_co_preadv\b.*?\boffset (\d+) bytes (\d+)\b')
LBA = re.compile(r"File data lba:\s*0\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*'/live/filesystem[.]squashfs'")
BROAD_START = '        # P50_V131_LIBXUL_READAHEAD:'
BROAD_END = '        # P50_V125_DRM_PREREQ:'
SOURCE_CASE = '        /run/live/medium/live/filesystem.squashfs)\n'


def patch(root, reader=None, plan=None):
    main = root / 'usr/lib/live/boot/9990-main.sh'
    text = main.read_text()
    begin = text.index(BROAD_START)
    end = text.index(BROAD_END, begin)
    original = text[begin:end]
    if original.count('if=/usr/lib/firefox-esr/libxul.so') != 1:
        raise ValueError('Unexpected Firefox prefetch in the input')
    main.write_text(text[:begin] + '        if [ "${P50_OPTICAL_PATH:-0}" != 1 ]; then\n'
                    + original + '        fi\n' + text[end:])
    if reader is None:
        return
    if plan is None:
        raise ValueError('The reader requires a measured plan')
    target = root / 'usr/lib/p50-workset'
    target.mkdir()
    shutil.copyfile(reader, target / 'warm-root')
    (target / 'warm-root').chmod(0o755)
    shutil.copyfile(plan, target / 'ranges')
    helper = root / 'usr/lib/live/boot/9990-misc-helpers.sh'
    # This callback is called in a command substitution. Detach all child FDs.
    hook = r'''
            if [ "${P50_OPTICAL_PATH:-0}" = 1 ] && grep -Fqx 'ROOT_HASH  ./live/filesystem.squashfs' /run/live/medium/sha256sum.txt; then
                (
                    read -r stamp idle </proc/uptime
                    printf 'P50_WORKSET_STARTED %s\n' "$stamp" >/dev/ttyS0
                    if /usr/lib/p50-workset/warm-root "$1" /usr/lib/p50-workset/ranges; then
                        read -r stamp idle </proc/uptime
                        printf 'P50_WORKSET_COMPLETE %s\n' "$stamp" >/dev/ttyS0
                    else
                        printf 'P50_WORKSET_READ_FAILED\n' >/dev/ttyS0
                    fi
                ) </dev/null >/dev/null 2>&1 &
            fi
'''.replace('ROOT_HASH', ROOT_SHA256)
    helper.write_text(replace_once(helper.read_text(), SOURCE_CASE, SOURCE_CASE + hook))


def prepare_training_harness(bios, driver):
    plain, delimiter, _ = bios.read_text().partition("    result = {'guest_ram_mib':")
    if not delimiter:
        raise ValueError('Unexpected benchmark entry')
    call = "\n    run_trace(cmd, monitor, out, capture)\n\nif __name__ == '__main__':\n    main()\n"
    prefix = f"import sys\nsys.path.insert(0, {str(Path(__file__).resolve().parent)!r})\nfrom boot_working_set import run_trace\n"
    source = prefix + plain + call
    compile(source, str(driver), 'exec')
    driver.write_text(source)


def run_trace(cmd, monitor, out, capture):
    from web85.qemu_debian_live_smoke import qmp
    with (out / 'reads.log').open('wb') as trace:
        vm = subprocess.Popen(cmd + ['-trace', 'enable=blk_co_preadv'], stdout=trace, stderr=trace)
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline and vm.poll() is None:
                if monitor.exists() and capture(monitor, out, None):
                    qmp(monitor, 'stop')
                    capture(monitor, out, 'first-home.png')
                    break
                time.sleep(.08)
            else:
                raise RuntimeError('The training VM did not display the real home page')
        finally:
            if vm.poll() is None:
                vm.terminate()
                try:
                    vm.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    vm.kill()
                    vm.wait()


def file_extent(layout):
    extents = LBA.findall(layout.read_text())
    if len(extents) != 1:
        raise ValueError(f'Expected one contiguous SquashFS extent, found {extents!r}')
    lba, sectors, size = map(int, extents[0])
    if (size + 2047) // 2048 != sectors or size % 4096:
        raise ValueError('Unexpected SquashFS extent size')
    return lba * 2048, size


def sampled_chunks(path, base, size):
    seen = {}
    for line in path.read_text(errors='replace').splitlines():
        match = TRACE_READ.search(line)
        if match is None:
            continue
        start, length = map(int, match.groups())
        lo = max(0, start - base)
        hi = min(size, start + length - base)
        if hi > lo:
            for chunk in range(lo // CHUNK, (hi - 1) // CHUNK + 1):
                if chunk not in seen:
                    seen[chunk] = len(seen)
    if len(seen) < 32:
        raise ValueError(f'Trace contains too few SquashFS data reads: {path}, {len(seen)} chunks')
    return seen


def make_plan(layout, traces, target):
    base, size = file_extent(layout)
    samples = [sampled_chunks(path, base, size) for path in traces]
    if len(samples) < 2:
        raise ValueError('At least two independent fresh training boots are required')
    shared = set.intersection(*(set(items) for items in samples))
    if not shared:
        raise ValueError('Boots have no common root reads')
    # Prefer consistently early reads when the common set exceeds the RAM budget.
    priority = sorted(shared, key=lambda x: (max(s[x] / len(s) for s in samples), x))
    selected = sorted(priority[:BUDGET // CHUNK])
    spans = []
    for chunk in selected:
        lo = chunk * CHUNK
        hi = min(size, lo + CHUNK)
        if spans and spans[-1][1] == lo:
            spans[-1][1] = hi
        else:
            spans.append([lo, hi])
    total = sum(hi - lo for lo, hi in spans)
    target.write_text(f'P50_READS_V1 {size}\n' + ''.join(f'{lo} {hi-lo}\n' for lo, hi in spans))
    stats = {
        'squashfs_sha256': ROOT_SHA256, 'root_bytes': size, 'start_byte_in_training_iso': base,
        'granularity_bytes': CHUNK, 'budget_bytes': BUDGET,
        'training_chunks_per_boot': [len(s) for s in samples], 'common_chunks': len(shared),
        'selected_bytes': total, 'extents': len(spans),
    }
    target.with_suffix('.json').write_text(json.dumps(stats, indent=2) + '\n')
    print(json.dumps(stats, indent=2))


def main():
    args = argparse.ArgumentParser(description=__doc__)
    modes = args.add_subparsers(dest='mode', required=True)
    image = modes.add_parser('patch')
    image.add_argument('root', type=Path)
    image.add_argument('--reader', type=Path)
    image.add_argument('--plan', type=Path)
    harness = modes.add_parser('training-harness')
    harness.add_argument('bios', type=Path)
    harness.add_argument('driver', type=Path)
    plan = modes.add_parser('plan')
    plan.add_argument('layout', type=Path)
    plan.add_argument('target', type=Path)
    plan.add_argument('traces', nargs='+', type=Path)
    values = vars(args.parse_args())
    mode = values.pop('mode')
    {'patch': patch, 'training-harness': prepare_training_harness, 'plan': make_plan}[mode](**values)


if __name__ == '__main__':
    main()
