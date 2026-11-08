#!/usr/bin/env python3
"""Validate pinned v110 USB-test evidence and visually reviewed screenshots."""
import hashlib
import json
from pathlib import Path

review = json.loads(Path('web110/V110_USB_MANUAL_REVIEW.json').read_text())
assert review['iso_sha256'] == 'b2f6ce26c4a794d87fd2e29d1d22b7e49a1ee175d58d89f7b72215dd54bc8a9e'
assert review['benchmark']['run_id'] == 42457412894
assert review['validation_run_id'] == 42458605379


def load(path):
    return json.loads(Path(path).read_text())


def verify_frames(folder, entries):
    for rel, expected in entries.items():
        path = folder / rel
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, str(path)


def verify_result(r):
    assert r['first_home_seen_seconds'] is not None
    assert r['media_ejected'] and r['input_sent_after_eject'] and r['qemu_running_at_end']
    assert not r['errors'], r['errors']


bench = Path('evidence/benchmark')
verify_frames(bench, review['benchmark']['screenshots_sha256'])
comparison = load(bench / 'reports/comparison.json')
assert abs(comparison['baseline_home_mean'] - 19.535) < 1e-7
assert abs(comparison['candidate_home_mean'] - 18.3) < 1e-7
assert not comparison['physical_acer_tested']
assert (bench / 'reports/fixture.log').read_text().count('GET /after.html?nonce=P50-42457412894 HTTP/1.1" 200') == 4
for trial in ('base1', 'cand1', 'cand2', 'base2'):
    verify_result(load(bench / trial / 'result.json'))
checks = (bench / 'reports/media-checksums.txt').read_text().splitlines()
assert len(checks) == 292 and all(line.endswith(': OK') for line in checks)

assert len(review['validation']) == 5
for name, case in review['validation'].items():
    folder = Path('evidence/validation') / ('Puppy50-v110-usb-validation-' + name)
    verify_frames(folder, case['screenshots_sha256'])
    r = load(folder / 'qemu/result.json')
    verify_result(r)
    serial = (folder / 'qemu/serial.log').read_text(errors='replace')
    if name == 'bios-fullram-fallback':
        assert r['fullram_fallback_selected'] and 'P50_STAGE_READY' not in serial
    else:
        assert r['staged_ram_ready_seconds'] is not None
        for marker in ('P50_STAGE_COPY_VERIFIED', 'P50_STAGE_RAM_BACKING=', 'P50_STAGE_READY'):
            assert marker in serial, (name, marker)
    if r['network_mode'] == 'online':
        assert 'GET /after.html?nonce=P50-42458605379 HTTP/1.1" 200' in (folder / 'reports/fixture.log').read_text()
    if name == 'bios-usb-2048':
        assert r['guest_ram_mib'] == 2048
    if name == 'connectivity-restored':
        assert r['outbound_https_intentionally_blocked'] and r['network_restored_signal_observed']

notes = Path('web110/V110_USB_RELEASE_NOTES.md').read_text()
for phrase in ('does **not** meet the eight-second goal', 'physical Acer', 'keep the USB connected', '384 MiB'):
    assert phrase in notes, phrase
print('Pinned benchmark, validation results, and visually reviewed frames verified.')
