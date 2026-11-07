#!/usr/bin/env python3
"""Measure a QEMU/KVM boot, optionally retaining media for a demand-boot experiment.

The reported time starts immediately before QEMU is spawned and includes its
virtual firmware and boot menu. It is not the timing of a physical computer.
The home-page image is an objective coarse detector; retain frames for review.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def missing_required_probe(mode, expect_no_https, allow_no_probe, has_probe):
    return mode == 'online' and not expect_no_https and not allow_no_probe and not has_probe


def media_condition_passed(keep_media, media_ejected, input_sent):
    """Avoid claiming media removal for the separate demand-boot experiment."""
    return input_sent and (not media_ejected if keep_media else media_ejected)


def home_visible(image):
    image = image.convert('RGB')
    if image.size != (1280, 800):
        return False
    # Independent page regions plus a browser toolbar, not a single pixel.
    header = [(50, 110), (300, 120), (30, 155), (500, 160)]
    body = [(120, 180), (900, 180), (1000, 250), (20, 400), (1000, 400), (100, 700)]
    return (sum(image.getpixel(p) == (18, 54, 88) for p in header) >= 3
            and sum(image.getpixel(p) == (7, 19, 34) for p in body) >= 5
            and image.getpixel((900, 600)) == (20, 41, 65)
            and image.getpixel((350, 500)) == (23, 52, 80))


def capture(monitor, out, name):
    from web85.qemu_debian_live_smoke import qmp
    ppm = out / 'current.ppm'
    qmp(monitor, 'screendump', {'filename': str(ppm)})
    with Image.open(ppm) as img:
        img.load()
        visible = home_visible(img)
        if name:
            img.save(out / name, 'PNG', optimize=True)
    return visible


def navigate(monitor, address):
    from web103.site_test import send_key, type_text
    send_key(monitor, ['ctrl', 'l'], 145)
    time.sleep(1.4)
    type_text(monitor, address, .15)
    send_key(monitor, ['ret'], 110)


def request_network_restore(out, timeout=60, interval=.2):
    out = Path(out)
    (out / 'network_restore_requested').touch()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if (out / 'network_restored').exists():
            return True
        time.sleep(interval)
    return False


def main():
    from web85.qemu_debian_live_smoke import qmp
    p = argparse.ArgumentParser()
    p.add_argument('--iso', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--mode', choices=['online', 'offline'], required=True)
    p.add_argument('--ram', type=int, default=2560)
    p.add_argument('--cpu-model', choices=['host', 'Westmere', 'i3-540-conservative'], default='host',
                   help='Models restrict exposed features; host speed and devices remain virtual')
    p.add_argument('--seconds', type=int, default=210)
    p.add_argument('--bandwidth', type=int, default=0)
    p.add_argument('--boot-enter-at', type=float, default=None,
                   help='For baseline only: press Enter at this elapsed time')
    p.add_argument('--firmware', choices=['bios', 'uefi'], default='bios')
    p.add_argument('--media', choices=['optical', 'usb'], default='optical')
    p.add_argument('--expect-no-https', action='store_true',
                   help='Only for controlled tests where outbound HTTPS is intentionally blocked')
    p.add_argument('--allow-no-startup-probe', action='store_true',
                   help='For images that intentionally do not perform automatic startup probes; inspect browser HTTPS screenshots')
    p.add_argument('--test-network-restore', action='store_true',
                   help='Request host to restore HTTPS, then try browsing in the same session')
    p.add_argument('--keep-media', action='store_true',
                   help='EXPERIMENT ONLY: leave boot media attached; this is not RAM-only')
    p.add_argument('--emulate-acer-id', action='store_true',
                   help='Use Acer as virtual SMBIOS vendor to exercise the physical startup path')
    args = p.parse_args()
    if args.expect_no_https and args.mode != 'online':
        raise ValueError('This controlled condition requires a virtual NIC')
    if args.test_network_restore and not args.expect_no_https:
        raise ValueError('Restoration test requires intentionally blocked initial HTTPS')
    iso = args.iso.resolve(strict=True)
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    monitor, serial = out / 'qmp.sock', out / 'serial.log'
    cd = (f'file={iso},if=ide,media=cdrom,id=livecd,readonly=on' if args.media == 'optical'
          else f'file={iso},if=none,id=livecd,format=raw,readonly=on')
    if args.bandwidth:
        cd += f',bps_rd={args.bandwidth}'
    cpu = ('Westmere,-aes,-pclmulqdq,-x2apic,-3dnowprefetch'
           if args.cpu_model == 'i3-540-conservative' else args.cpu_model)
    cmd = ['qemu-system-x86_64', '-machine', 'pc,accel=kvm', '-cpu', cpu,
           '-m', str(args.ram), '-smp', '2', '-drive', cd,
           '-boot', 'order=d' if args.media == 'optical' else 'order=c',
           '-display', 'none', '-vga', 'std', '-qmp', f'unix:{monitor},server=on,wait=off',
           '-serial', f'file:{serial}', '-no-reboot',
           '-nic', 'user,model=e1000,ipv6=off' if args.mode == 'online' else 'none']
    if args.emulate_acer_id:
        cmd += ['-smbios', 'type=1,manufacturer=Acer,product=Aspire-X3950-EMULATED']
    if args.media == 'usb':
        cmd += ['-device', 'qemu-xhci,id=xhci', '-device', 'usb-storage,drive=livecd,id=bootusb,bootindex=1']
    if args.firmware == 'uefi':
        pairs = [('/usr/share/OVMF/OVMF_CODE_4M.fd', '/usr/share/OVMF/OVMF_VARS_4M.fd'),
                 ('/usr/share/OVMF/OVMF_CODE.fd', '/usr/share/OVMF/OVMF_VARS.fd')]
        firmware = next(((code, var) for code, var in pairs
                         if Path(code).is_file() and Path(var).is_file()), None)
        if not firmware:
            raise FileNotFoundError('Install OVMF code and variables for the UEFI trial')
        code, variables = firmware
        vars_copy = out / 'OVMF_VARS.fd'
        shutil.copyfile(variables, vars_copy)
        cmd += ['-drive', f'if=pflash,format=raw,unit=0,readonly=on,file={code}',
                '-drive', f'if=pflash,format=raw,unit=1,file={vars_copy}']
    result = {'guest_ram_mib': args.ram, 'network_mode': args.mode,
              'virtual_read_cap_bytes_per_second': args.bandwidth or None,
              'virtual_firmware': args.firmware, 'virtual_media': args.media,
              'virtual_cpu_model': args.cpu_model,
              'outbound_https_intentionally_blocked': args.expect_no_https,
              'startup_probe_optional_for_test': args.allow_no_startup_probe,
              'acer_vendor_id_only_emulated': args.emulate_acer_id,
              'measurement': 'host monotonic clock from immediately before QEMU process launch',
              'boot_menu_key_sent': False, 'first_home_seen_seconds': None,
              'timestamps_are_qemu_not_physical_acer': True,
              'media_ejected': False, 'input_sent_after_eject': False,
              'keep_media_experiment': args.keep_media, 'input_sent': False,
              'network_restored_signal_observed': False, 'qemu_running_at_end': False,
              'errors': [], 'screenshots': [], 'serial_marker_first_seen_seconds': {}}
    markers = ['PUPPY50_V85_NETWORK_PROBE_START', 'PUPPY50_V85_NETWORK_MODE=',
               'P50_V91_LIGHTDM_AUTOLOGIN_PREPARED', 'P50_V91_NONROOT_FIREFOX_PROCESS_SEEN']
    with (out / 'qemu.log').open('wb') as log:
        started = time.monotonic()
        vm = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
        try:
            last_checkpoint = -10
            while time.monotonic() - started < args.seconds and vm.poll() is None:
                elapsed = time.monotonic() - started
                if (args.boot_enter_at is not None and not result['boot_menu_key_sent']
                        and elapsed >= args.boot_enter_at and monitor.exists()):
                    from web103.site_test import send_key
                    send_key(monitor, ['ret'], 110)
                    result['boot_menu_key_sent'] = True
                    result['boot_enter_seconds'] = round(time.monotonic() - started, 2)
                if serial.exists():
                    serial_text = serial.read_text(errors='replace')
                    for marker in markers:
                        if marker in serial_text and marker not in result['serial_marker_first_seen_seconds']:
                            result['serial_marker_first_seen_seconds'][marker] = round(elapsed, 2)
                if monitor.exists():
                    try:
                        checkpoint = int(elapsed // 10) * 10
                        name = f'checkpoint_{checkpoint:03d}.png' if checkpoint > last_checkpoint else None
                        visible = capture(monitor, out, name)
                        if name:
                            last_checkpoint = checkpoint
                            result['screenshots'].append(name)
                        if visible:
                            result['first_home_seen_seconds'] = round(time.monotonic() - started, 2)
                            capture(monitor, out, 'first_home.png')
                            result['screenshots'].append('first_home.png')
                            break
                    except Exception as exc:
                        result['errors'].append(f'frame at {elapsed:.1f}: {exc!r}')
                time.sleep(.8)
            if result['first_home_seen_seconds'] is not None:
                if args.media == 'optical' and not args.keep_media:
                    qmp(monitor, 'human-monitor-command', {'command-line': 'eject -f livecd'})
                    info = str(qmp(monitor, 'human-monitor-command', {'command-line': 'info block livecd'})).lower()
                    result['media_ejected'] = 'not inserted' in info or 'no media' in info
                elif not args.keep_media:
                    before = str(qmp(monitor, 'human-monitor-command', {'command-line': 'info qtree'}))
                    if 'id "bootusb"' not in before:
                        raise RuntimeError('Cannot find the virtual USB device before unplugging')
                    qmp(monitor, 'device_del', {'id': 'bootusb'})
                    time.sleep(2)
                    info = str(qmp(monitor, 'human-monitor-command', {'command-line': 'info qtree'}))
                    result['media_ejected'] = 'id "bootusb"' not in info
                if not result['media_ejected'] and not args.keep_media:
                    result['errors'].append('Boot media did not report removed')
                time.sleep(2)
                nonce = os.environ.get('P50_NONCE', 'P50-TEST')
                local = 'http://10.0.2.2:8765/after.html?nonce=' + nonce
                navigate(monitor, local if args.mode == 'online' else 'about:about')
                result['input_sent'] = True
                result['input_sent_after_eject'] = result['media_ejected']
                time.sleep(18)
                capture(monitor, out, 'after_input.png')
                result['screenshots'].append('after_input.png')
                if args.test_network_restore:
                    result['network_restored_signal_observed'] = request_network_restore(out)
                    if not result['network_restored_signal_observed']:
                        raise RuntimeError('Host never acknowledged HTTPS restoration')
                if args.mode == 'online' and (not args.expect_no_https or args.test_network_restore):
                    navigate(monitor, 'https://example.com/')
                    time.sleep(25)
                    capture(monitor, out, 'external_https.png')
                    result['screenshots'].append('external_https.png')
            result['qemu_running_at_end'] = vm.poll() is None
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
    serial_text = serial.read_text(errors='replace') if serial.exists() else ''
    result['guest_ca_https_probe'] = ('PUPPY50_V85_GUEST_CA_VERIFIED_PUBLIC_HTTPS_DIRECT=PASS' in serial_text
                                     or 'PUPPY50_V85_GUEST_CA_VERIFIED_PUBLIC_HTTPS_BRIDGE=PASS' in serial_text)
    result['screenshots_need_visual_review'] = True
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2), flush=True)
    if not (result['first_home_seen_seconds'] is not None and result['qemu_running_at_end']
            and media_condition_passed(args.keep_media, result['media_ejected'], result['input_sent'])):
        raise SystemExit('Benchmark failed its stated media and browser-interaction condition')
    if missing_required_probe(args.mode, args.expect_no_https, args.allow_no_startup_probe,
                              result['guest_ca_https_probe']):
        raise SystemExit('Guest CA-verified HTTPS probe was not observed')
    if args.test_network_restore and not result['network_restored_signal_observed']:
        raise SystemExit('Network restoration handshake failed')


if __name__ == '__main__':
    main()

