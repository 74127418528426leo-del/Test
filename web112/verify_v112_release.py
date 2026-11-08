#!/usr/bin/env python3
"""Verify the pinned v112 candidate evidence and reviewed browser frames."""
import hashlib
import json
import os
from pathlib import Path

root = Path(os.environ.get('P50_EVIDENCE_DIR', 'evidence'))
review_path = Path(os.environ.get('P50_REVIEW_FILE', 'web112/V112_MANUAL_REVIEW.json'))
review = json.loads(review_path.read_text())
assert review['iso_sha256'] == '317999f51e47698d90889b129e9f74bbbefaa382b4d481f4da32016861d8ddc7'
assert (review['benchmark_run_id'], review['validation_run_id'], review['audit_run_id'], review['interaction_run_id']) == (42479601193, 42480523148, 42480757160, 42480553607)


def load(path):
    return json.loads(path.read_text())


def frames(folder, expected):
    for relative, digest in expected.items():
        path = folder / relative
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, str(path)


def result_ok(r):
    assert r['first_home_seen_seconds'] is not None
    assert r['media_ejected'] and r['input_sent_after_eject'] and r['qemu_running_at_end']
    assert not r['errors'], r['errors']


benchmark = root / 'benchmark'
frames(benchmark, review['benchmark_screenshots'])
b = load(benchmark / 'reports/comparison.json')
assert abs(b['baseline_home_mean'] - 17.155) < 1e-6
assert abs(b['candidate_home_mean'] - 15.47) < 1e-6
assert b['home_difference_seconds'] > b['sample_interval_seconds']
assert not b['physical_acer_tested']
assert 'Block size 262144' in (benchmark / 'reports/candidate-format.txt').read_text()
assert not (benchmark / 'reports/rsync-forward.txt').read_bytes()
assert not (benchmark / 'reports/rsync-reverse.txt').read_bytes()
for case in ('base1', 'cand1', 'cand2', 'base2'):
    result_ok(load(benchmark / case / 'result.json'))
checks = (benchmark / 'reports/media-checksums.txt').read_text().splitlines()
assert len(checks) == 293 and all(line.endswith(': OK') for line in checks)

interaction = root / 'interaction'
frames(interaction, review['interaction_screenshots'])
i = load(interaction / 'reports/interaction-summary.json')
assert not i['physical_acer_tested']
assert abs(i['baseline_mean_early_js_response_seconds'] - 20.875) < 1e-6
assert abs(i['candidate_mean_early_js_response_seconds'] - 19.655) < 1e-6
assert i['candidate_mean_early_js_response_seconds'] < i['baseline_mean_early_js_response_seconds']
assert (interaction / 'reports/early-fixture.log').read_text().count('"GET /e HTTP/1.1" 200') == 4
assert (interaction / 'reports/after-fixture.log').read_text().count('GET /after.html?nonce=P50-42480553607 HTTP/1.1" 200') == 4
for case in ('base1', 'cand1', 'cand2', 'base2'):
    r = load(interaction / case / 'result.json')
    result_ok(r)
    assert r['early_media_attached_before_navigation'] and r['early_media_attached_after_js_response']
    assert not r['ram_ready_before_early_navigation'] and not r['ram_ready_before_early_js_response']
    assert r['early_js_response_seconds'] >= r['early_page_seen_seconds'] >= r['early_navigation_start_seconds'] >= r['first_home_seen_seconds']

assert len(review['validation']) == 5
for name, expected in review['validation'].items():
    folder = root / 'validation' / ('Puppy50-v112-block256-validation-' + name)
    frames(folder, expected)
    r = load(folder / 'qemu/result.json')
    result_ok(r)
    serial = (folder / 'qemu/serial.log').read_text(errors='replace')
    if name == 'bios-fullram-fallback':
        assert r['fullram_fallback_selected'] and 'P50_STAGE_READY' not in serial
    else:
        assert r['staged_ram_ready_seconds'] is not None
        for marker in ('P50_STAGE_COPY_VERIFIED', 'P50_STAGE_RAM_BACKING=', 'P50_STAGE_READY'):
            assert marker in serial, (name, marker)
    if r['network_mode'] == 'online':
        assert 'GET /after.html?nonce=P50-42480523148 HTTP/1.1" 200' in (folder / 'reports/fixture.log').read_text()
    if name == 'bios-usb-2048':
        assert r['guest_ram_mib'] == 2048
    if name == 'connectivity-restored':
        assert r['outbound_https_intentionally_blocked'] and r['network_restored_signal_observed']

audit = root / 'audit'
assert not (audit / 'rsync-forward.txt').read_bytes()
assert not (audit / 'rsync-reverse.txt').read_bytes()
assert 'Block size 262144' in (audit / 'new-format.txt').read_text()
assert '293 candidate image checksums pass' in (audit / 'audit-result.txt').read_text()
checks = (audit / 'media-checksums.txt').read_text().splitlines()
assert len(checks) == 293 and all(line.endswith(': OK') for line in checks)
print('Pinned layout, interaction, five validations, independent audit and reviewed screenshots verified.')
