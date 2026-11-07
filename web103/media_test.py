#!/usr/bin/env python3
"""Compare Firefox media support and the real Pexels page in a KVM guest."""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web85.qemu_debian_live_smoke import qmp, ppm_valid
from site_test import send_key, type_text, char_keys
from post_eject import heartbeat_count

TARGETS = {'pexels': 'https://www.pexels.com/video/riverside-27251986/',
           'fixture': 'http://10.0.2.2:8765/fixture.mp4'}
MEDIA_EXPRESSIONS = [
    ('h264_capability', "document.createElement('video').canPlayType('video/mp4;codecs=avc1.42E01E')"),
    ('play', "document.querySelector('video').play()"),
    ('height', "document.querySelector('video').videoHeight"),
    ('time_first', "document.querySelector('video').currentTime"),
    ('time_second', "document.querySelector('video').currentTime"),
]


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--iso', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--ram', type=int, default=4096)
    parser.add_argument('--target', choices=TARGETS, default='pexels')
    args = parser.parse_args()
    target = TARGETS[args.target]
    iso = args.iso.resolve(strict=True)
    if iso.stat().st_size < 700_000_000:
        raise ValueError('Incomplete Firefox Live ISO')
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    monitor, serial = out / 'qmp.sock', out / 'serial.log'
    cmd = ['qemu-system-x86_64', '-machine', 'pc,accel=kvm', '-cpu', 'host',
           '-m', str(args.ram), '-smp', '2',
           '-drive', f'file={iso},if=ide,media=cdrom,id=livecd,readonly=on',
           '-boot', 'order=d', '-display', 'none', '-vga', 'std',
           '-qmp', f'unix:{monitor},server=on,wait=off',
           '-serial', f'file:{serial}', '-nic', 'user,model=e1000,ipv6=off',
           '-no-reboot']
    result = {'target_url': target, 'guest_ram_mib': args.ram,
              'boot_cd_ejected': False, 'qemu_running_at_end': False,
              'heartbeat_at_eject': 0, 'heartbeat_at_end': 0,
              'video_playback_proven': False, 'video_2160p_proven': False,
              'screenshots': [], 'console_queries': [], 'errors': []}
    with (out / 'qemu.log').open('wb') as log:
        vm = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
        start = time.monotonic()

        def shot(name):
            path = out / (name + '.ppm')
            qmp(monitor, 'screendump', {'filename': str(path)})
            if not path.is_file() or not ppm_valid(path):
                raise RuntimeError('Missing valid guest screenshot')
            result['screenshots'].append({'filename': path.name,
                                          'elapsed_seconds': round(time.monotonic() - start, 1)})

        try:
            for mark in (18, 110, 150, 225, 290, 310, 330, 470):
                while time.monotonic() - start < mark and vm.poll() is None:
                    time.sleep(.5)
                if vm.poll() is not None:
                    result['errors'].append('QEMU exited before ' + str(mark))
                    break
                if mark == 18:
                    send_key(monitor, ['ret'], 110)
                elif mark == 150:
                    send_key(monitor, ['ctrl', 'l'], 145)
                    time.sleep(1.4)
                    type_text(monitor, target, .12)
                    send_key(monitor, ['ret'], 110)
                elif mark == 310:
                    qmp(monitor, 'human-monitor-command', {'command-line': 'eject -f livecd'})
                    state = str(qmp(monitor, 'human-monitor-command', {'command-line': 'info block livecd'})).lower()
                    result['boot_cd_ejected'] = 'not inserted' in state or 'no media' in state
                    result['heartbeat_at_eject'] = heartbeat_count(serial)
                elif mark == 330:
                    send_key(monitor, ['ctrl', 'shift', 'k'], 155)
                    time.sleep(5)
                    for name, expression in MEDIA_EXPRESSIONS:
                        type_text(monitor, expression, .105)
                        send_key(monitor, ['ret'], 110)
                        time.sleep(8 if name == 'time_first' else 5)
                        shot('probe_' + name)
                        result['console_queries'].append({'name': name, 'expression': expression,
                                                          'elapsed_seconds': round(time.monotonic() - start, 1),
                                                          'result_visually_verified': False})
                else:
                    shot('frame_' + str(mark))
            result['qemu_running_at_end'] = vm.poll() is None
            result['heartbeat_at_end'] = heartbeat_count(serial)
        except Exception as exc:
            result['errors'].append(repr(exc))
        finally:
            if vm.poll() is None:
                vm.terminate()
                try:
                    vm.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    vm.kill()
                    vm.wait(timeout=5)
    logs = serial.read_text(errors='replace') if serial.exists() else ''
    result['guest_nonroot_firefox_started'] = 'P50_V91_NONROOT_FIREFOX_PROCESS_SEEN' in logs
    result['guest_ca_verified_https_probe'] = (
        'PUPPY50_V85_GUEST_CA_VERIFIED_PUBLIC_HTTPS_DIRECT=PASS' in logs
        or 'PUPPY50_V85_GUEST_CA_VERIFIED_PUBLIC_HTTPS_BRIDGE=PASS' in logs)
    result['guest_heartbeat_continued_after_eject'] = (
        result['heartbeat_at_eject'] > 0 and result['heartbeat_at_end'] > result['heartbeat_at_eject'])
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2), flush=True)
    if not (result['guest_nonroot_firefox_started'] and result['guest_ca_verified_https_probe']
            and result['boot_cd_ejected'] and result['guest_heartbeat_continued_after_eject']):
        raise SystemExit('Guest boot, TLS, ejection, or post-ejection heartbeat not established')
    print('Guest evidence collected; inspect the actual Pexels and console screenshots.')


if __name__ == '__main__':
    run()
