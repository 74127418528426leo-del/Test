"""Compare fresh Puppy50 boots while preserving the real browser checks."""

import argparse
import hashlib
import json
from pathlib import Path
import re
from statistics import mean
import subprocess

from repack import replace_once

BASELINE_HASH = 'aa074377b00832818bcb1cd45c0166cb1975b6c1b3ad778279fef6132941aaf6'
MARKERS = (
    'P50_LAB_INITRAMFS_START', 'P50_FIVE_OPTICAL_DEVICE_READY', 'P50_FIVE_INIT_TOP',
    'P50_FIVE_RNG_READY', 'P50_V123_XORG_START', 'P50_V127_FIREFOX_DIRECT_EXEC',
    'P50_FIVE_ROOT_MOUNT_RETURN', 'P50_FIVE_PREFETCH_OK', 'P50_STAGE_START',
    'P50_STAGE_COPY_VERIFIED', 'P50_STAGE_READY',
)
AHCI = "cmd += ['-device', 'ich9-ahci,id=ahci', '-device', 'ide-cd,drive=livecd,bus=ahci.0,id=bootusb,bootindex=1']"
VIRTIO = "cmd += ['-device', 'virtio-scsi-pci,id=p50scsi', '-device', 'scsi-cd,drive=livecd,bus=p50scsi.0,id=bootusb,bootindex=1']"


def prepare_harness(source, boot_files):
    text = source.read_text()
    home_time = "result['first_home_seen_seconds'] = "
    for old, new in (
        ("else .2)", "else .08)"),
        ("time.sleep(25)", "time.sleep(9)"),
        ("fixture_log = out.parent / 'reports' / 'fixture-after.log'", "fixture_log = out / 'http-receipts.log'"),
        (home_time + "round(time.monotonic() - started, 2)", home_time + "time.monotonic() - started"),
        ("    with (out / 'qemu.log').open", f"    markers.extend({MARKERS!r})\n    with (out / 'qemu.log').open"),
    ):
        text = replace_once(text, old, new)
    config = (boot_files / 'live.cfg').read_text()
    stanza = re.search(r'^label live-vm\n(?P<body>(?:[ \t].*\n)+)', config, re.M)
    if not stanza:
        raise ValueError('Could not find the exact compact boot command line')
    lines = [s.strip() for s in stanza['body'].splitlines()]
    if 'linux /live/vmlinuz' not in lines or 'initrd /live/initrd-vm.img' not in lines:
        raise ValueError('Unexpected kernel or initial ramdisk in the ISO')
    arguments = [s.removeprefix('append ') for s in lines if s.startswith('append ')]
    if len(arguments) != 1 or 'p50-vm-entry' not in arguments[0].split():
        raise ValueError('Unexpected compact boot parameters')
    direct = [
        '-kernel', str((boot_files / 'vmlinuz').resolve(strict=True)),
        '-initrd', str((boot_files / 'initrd-vm.img').resolve(strict=True)),
        '-append', arguments[0],
    ]
    variants = {
        'bios': text,
        'direct': replace_once(text, AHCI, AHCI + f'\n        cmd += {direct!r}'),
        'virtio': replace_once(text, AHCI, VIRTIO),
    }
    for key, value in variants.items():
        target = source.with_name(f'boot_bench_lab_{key}.py')
        compile(value, str(target), 'exec')
        target.write_text(value)


def prepare_initrd(root):
    init = root / 'init'
    text = init.read_text()
    text = replace_once(
        text, 'p50_ahci=0\np50_display=0',
        'p50_ahci=0\np50_virtio_scsi=0\np50_display=0',
    )
    text = replace_once(
        text, '0x8086:0x2922) p50_ahci=1 ;;',
        '0x8086:0x2922) p50_ahci=1 ;;\n            0x1af4:0x1004|0x1af4:0x1048) p50_virtio_scsi=1 ;;',
    )
    text = replace_once(
        text, 'if [ "$p50_ahci" = 1 ] && [ "$p50_display" = 1 ]; then P50_OPTICAL_PATH=1; fi',
        'if [ "$p50_display" = 1 ] && { [ "$p50_ahci" = 1 ] || [ "$p50_virtio_scsi" = 1 ]; }; then\n'
        '    P50_OPTICAL_PATH=1\nfi',
    )
    text = replace_once(
        text, 'mkdir -m 0700 /run/initramfs\n',
        "mkdir -m 0700 /run/initramfs\n"
        "printf 'P50_LAB_INITRAMFS_START %s\\n' \"$(cat /proc/uptime)\" >/dev/ttyS0\n",
    )
    init.write_text(text)


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def repack_iso(reference, output, boot_files, image):
    if output.exists():
        raise FileExistsError(output)
    manifest = (boot_files / 'sha256sum.txt').read_text()
    previous_hash = sha256(boot_files / 'initrd-vm.img')
    new_hash = sha256(image)
    manifest = replace_once(
        manifest, f'{previous_hash}  ./live/initrd-vm.img',
        f'{new_hash}  ./live/initrd-vm.img',
    )
    manifest_path = boot_files / 'lab-sha256sum.txt'
    manifest_path.write_text(manifest)
    subprocess.run([
        'xorriso', '-indev', str(reference), '-outdev', str(output),
        '-map', str(manifest_path), '/sha256sum.txt', '-map', str(image), '/live/initrd-vm.img',
        '-boot_image', 'any', 'replay', '-commit', '-end',
    ], check=True)


def read_sample(folder, name, run_id):
    item = folder / name
    status = (item / 'exit-status').read_text().strip()
    try:
        result = json.loads((item / 'result.json').read_text())
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return {'functional_ok': False, 'harness_exit': status, 'error': str(exc)}
    serial = (item / 'serial.log').read_text(errors='replace') if (item / 'serial.log').is_file() else ''
    receipts = (item / 'http-receipts.log').read_text(errors='replace')
    token = f'P50-{run_id}-TRIAL-{name.upper()}'
    first = result.get('first_home_seen_seconds')
    required = (
        'P50_STAGE_COPY_VERIFIED',
        'P50_STAGE_RAM_BACKING=/run/p50-stage/store/root.squashfs',
        'P50_FIVE_LOCAL_COOKIE_OK', 'P50_FIVE_RNG_READY',
        'P50_FIVE_OPTICAL_DEVICE_READY', 'P50_FIVE_CACHE_SEEDED',
    )
    result['functional_ok'] = bool(
        status == '0' and first is not None and first > 0
        and result.get('early_js_response_seconds') is not None
        and result.get('early_media_attached_before_navigation')
        and result.get('early_media_attached_after_js_response')
        and result.get('staged_ram_ready_seconds') is not None
        and result.get('media_ejected')
        and result.get('post_eject_browser_http200_confirmed')
        and f'nonce={token} HTTP/1.1" 200' in receipts
        and all(mark in serial for mark in required)
        and re.search(r'^\s*\d+\s+\d+\s+1000\s+\S+\s+firefox-esr\s+', serial, re.M)
        and re.search(r'^\s*\d+\s+\d+\s+1000\s+\S+\s+openbox\s+', serial, re.M)
        and 'Authorization required' not in serial and not result.get('errors')
    )
    result['harness_exit'] = status
    result['kernel_uptime_at_events_seconds'] = {}
    for marker in MARKERS:
        found = re.search(r'^' + re.escape(marker) + r' (\d+\.\d+)(?: |\r?$)', serial, re.M)
        if found:
            result['kernel_uptime_at_events_seconds'][marker] = float(found[1])
    return result


def summarize(folder, route, run_id, names):
    samples = {name: read_sample(folder, name, run_id) for name in names}
    groups = {
        group: [r for name, r in samples.items() if name.rstrip('0123456789') == group]
        for group in dict.fromkeys(name.rstrip('0123456789') for name in names)
    }
    series = {}
    for group, items in groups.items():
        times = [r.get('first_home_seen_seconds') for r in items]
        passed = all(r['functional_ok'] for r in items)
        series[group] = {
            'frames_seconds': times,
            'mean_seconds': mean(times) if all(t is not None for t in times) else None,
            'all_functional_ok': passed,
            'all_at_or_below_one_second': passed and all(0 < t <= 1.0 for t in times),
        }
    report = {
        'reference_sha256': BASELINE_HASH, 'route': route, 'series': series,
        'measurement': 'Host monotonic clock, immediately before each new KVM process through detection of the first genuine Firefox home frame.',
        'samples': samples,
    }
    (folder / 'reports/comparison.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(series, indent=2))
    for name, result in samples.items():
        print(
            name, result.get('first_home_seen_seconds'), result['functional_ok'],
            result.get('early_js_response_seconds'), result.get('staged_ram_ready_seconds'),
            result.get('serial_marker_first_seen_seconds'),
        )
    if not all(r['functional_ok'] for r in samples.values()):
        raise SystemExit('At least one boot failed functional validation; evidence was retained.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest='mode', required=True)
    harness = modes.add_parser('harness')
    harness.add_argument('source', type=Path)
    harness.add_argument('boot_files', type=Path)
    initrd = modes.add_parser('initrd')
    initrd.add_argument('root', type=Path)
    iso = modes.add_parser('iso')
    iso.add_argument('reference', type=Path)
    iso.add_argument('output', type=Path)
    iso.add_argument('boot_files', type=Path)
    iso.add_argument('image', type=Path)
    report = modes.add_parser('report')
    report.add_argument('folder', type=Path)
    report.add_argument('route')
    report.add_argument('run_id')
    report.add_argument('names', nargs='+')
    args = vars(parser.parse_args())
    mode = args.pop('mode')
    {'harness': prepare_harness, 'initrd': prepare_initrd,
     'iso': repack_iso, 'report': summarize}[mode](**args)


if __name__ == '__main__':
    main()
