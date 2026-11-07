#!/usr/bin/env python3
"""Check that the real BIOS boot menu accepts a recovery-selection key."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def highlighted(image):
    image = image.convert('RGB')
    if image.size != (640, 480):
        return None
    blue, black = (113, 147, 181), (0, 0, 0)
    if image.getpixel((500, 255)) == blue and image.getpixel((500, 270)) == black:
        return 'default'
    if image.getpixel((500, 255)) == black and image.getpixel((500, 270)) == blue:
        return 'recovery'
    return None


def run(iso, out):
    from web85.qemu_debian_live_smoke import qmp
    from web103.site_test import send_key
    out.mkdir(parents=True, exist_ok=True)
    iso, out = iso.resolve(strict=True), out.resolve()
    monitor = out / 'menu.sock'
    cmd = ['qemu-system-x86_64', '-machine', 'pc,accel=kvm', '-cpu', 'host',
           '-m', '2560', '-smp', '2', '-drive', f'file={iso},if=ide,media=cdrom,readonly=on',
           '-boot', 'order=d', '-display', 'none', '-vga', 'std', '-nic', 'none',
           '-qmp', f'unix:{monitor},server=on,wait=off', '-no-reboot']
    result = {'default_seen': False, 'recovery_highlight_seen': False,
              'automatic_recovery_boot_tested': False, 'physical_keyboard_tested': False}
    with (out / 'menu-qemu.log').open('wb') as log:
        start = time.monotonic()
        vm = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
        try:
            sent = False
            while vm.poll() is None and time.monotonic() - start < 15:
                if not monitor.exists():
                    time.sleep(.05)
                    continue
                ppm = out / 'current.ppm'
                qmp(monitor, 'screendump', {'filename': str(ppm)})
                with Image.open(ppm) as img:
                    img.load()
                    state = highlighted(img)
                    if state == 'default' and not sent:
                        img.save(out / 'default.png')
                        result['default_seen'] = True
                        result['default_seen_seconds'] = round(time.monotonic() - start, 2)
                        send_key(monitor, ['down'], 100)
                        sent = True
                    elif state == 'recovery' and sent:
                        img.save(out / 'recovery-selected.png')
                        result['recovery_highlight_seen'] = True
                        result['recovery_seen_seconds'] = round(time.monotonic() - start, 2)
                        break
                time.sleep(.06)
        finally:
            if vm.poll() is None:
                vm.terminate()
                try:
                    vm.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    vm.kill()
                    vm.wait(timeout=5)
    (out / 'menu-result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    if not result['recovery_highlight_seen']:
        raise SystemExit('Could not establish recovery selection in the actual BIOS menu')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--iso', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    run(args.iso, args.out)
