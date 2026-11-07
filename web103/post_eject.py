#!/usr/bin/env python3
"""Collect guest heartbeat and browser input after removing the Live CD."""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web85.qemu_debian_live_smoke import qmp, ppm_valid
from site_test import send_key, type_text

TARGET = 'https://example.com/?aftereject=1'
HEARTBEAT = 'P50_V99_RAM_SAMPLE '


def captured_guest_progress(result):
    before = result.get('heartbeat_at_eject', 0)
    after = result.get('heartbeat_at_end', 0)
    return bool(result.get('boot_cd_ejected') and result.get('qemu_running_at_end')
                and result.get('post_eject_input_sent') and before > 0
                and after > before and 'frame_360.ppm' in result.get('screenshots', []))


def heartbeat_count(path):
    if not path.exists():
        return 0
    return path.read_text(errors='replace').count(HEARTBEAT)


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--iso', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--ram', type=int, required=True)
    args = parser.parse_args()
    iso = args.iso.resolve(strict=True)
    if iso.stat().st_size < 700_000_000:
        raise ValueError('Incomplete Firefox Live ISO')
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    monitor, serial = out / 'qmp.sock', out / 'serial.log'
    command = ['qemu-system-x86_64', '-machine', 'pc,accel=kvm', '-cpu', 'host',
               '-m', str(args.ram), '-smp', '2',
               '-drive', f'file={iso},if=ide,media=cdrom,id=livecd,readonly=on',
               '-boot', 'order=d', '-display', 'none', '-vga', 'std',
               '-qmp', f'unix:{monitor},server=on,wait=off',
               '-serial', f'file:{serial}', '-nic', 'user,model=e1000,ipv6=off',
               '-no-reboot']
    result = {'guest_ram_mib': args.ram, 'target_url_after_eject': TARGET,
              'boot_cd_ejected': False, 'qemu_running_at_end': False,
              'post_eject_input_sent': False, 'heartbeat_at_eject': 0,
              'heartbeat_at_end': 0, 'guest_heartbeat_continued': False,
              'post_eject_webpage_visually_verified': False,
              'screenshots': [], 'errors': []}
    with (out / 'qemu.log').open('wb') as log:
        vm = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        start = time.monotonic()
        try:
            for mark in (18, 145, 245, 260, 270, 320, 360):
                while time.monotonic() - start < mark and vm.poll() is None:
                    time.sleep(.5)
                if vm.poll() is not None:
                    result['errors'].append('QEMU exited before ' + str(mark))
                    break
                if mark == 18:
                    send_key(monitor, ['ret'], 110)
                elif mark == 145:
                    send_key(monitor, ['ctrl', 'l'], 145)
                    time.sleep(1.4)
                    type_text(monitor, 'https://example.com/', .3)
                    send_key(monitor, ['ret'], 110)
                elif mark == 260:
                    qmp(monitor, 'human-monitor-command', {'command-line': 'eject -f livecd'})
                    block = str(qmp(monitor, 'human-monitor-command', {'command-line': 'info block livecd'})).lower()
                    result['boot_cd_ejected'] = 'not inserted' in block or 'no media' in block
                    result['heartbeat_at_eject'] = heartbeat_count(serial)
                elif mark == 270:
                    if result['boot_cd_ejected']:
                        send_key(monitor, ['ctrl', 'l'], 145)
                        time.sleep(1.4)
                        type_text(monitor, TARGET, .3)
                        send_key(monitor, ['ret'], 110)
                        result['post_eject_input_sent'] = True
                elif mark in (245, 320, 360):
                    image = out / f'frame_{mark:03d}.ppm'
                    qmp(monitor, 'screendump', {'filename': str(image)})
                    if not image.is_file() or not ppm_valid(image):
                        raise RuntimeError('Missing valid QEMU framebuffer')
                    result['screenshots'].append(image.name)
            result['qemu_running_at_end'] = vm.poll() is None
            result['heartbeat_at_end'] = heartbeat_count(serial)
            result['guest_heartbeat_continued'] = (
                result['heartbeat_at_eject'] > 0
                and result['heartbeat_at_end'] > result['heartbeat_at_eject'])
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
    result['guest_ca_verified_https_probe'] = (
        'PUPPY50_V85_GUEST_CA_VERIFIED_PUBLIC_HTTPS_DIRECT=PASS' in logs
        or 'PUPPY50_V85_GUEST_CA_VERIFIED_PUBLIC_HTTPS_BRIDGE=PASS' in logs)
    result['guest_nonroot_firefox_started'] = 'P50_V91_NONROOT_FIREFOX_PROCESS_SEEN' in logs
    result['guest_progress_evidence'] = captured_guest_progress(result)
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2), flush=True)
    if (not result['guest_progress_evidence'] or not result['guest_ca_verified_https_probe']
            or not result['guest_nonroot_firefox_started']):
        raise SystemExit('Post-ejection guest heartbeat/input evidence not established')
    print('Guest heartbeat continued; screenshot requires visual review of the new URL.')


if __name__ == '__main__':
    run()
