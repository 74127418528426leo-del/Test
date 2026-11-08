#!/usr/bin/env python3
"""Check a real Firefox navigation and JavaScript action before media removal."""

import argparse
import time
from pathlib import Path

from PIL import Image

SAMPLE_POINTS = [(30, 300), (600, 300), (1100, 400), (150, 650), (1000, 700)]
LOADED_COLOR = (137, 31, 89)
RESPONDED_COLOR = (17, 169, 83)
HARNESS_MARKER = "            if result['first_home_seen_seconds'] is not None:\n                if args.wait_ram_ready:\n"

HARNESS_INJECTION = '''            if result['first_home_seen_seconds'] is not None:
                if args.mode == 'online':
                    from web112.early_probe import run_early_probe
                    early = run_early_probe(monitor, out, started, serial)
                    result.update(early)
                    result['screenshots'].extend(early['early_screenshots'])
                    if early['early_js_response_seconds'] is None:
                        raise RuntimeError('Early browser navigation and JavaScript response not verified')
                if args.wait_ram_ready:
'''


def page_color_visible(image, color):
    if image.size != (1280, 800):
        return False
    image = image.convert('RGB')
    return all(image.getpixel(point) == color for point in SAMPLE_POINTS)


def patch_harness(source):
    if source.count(HARNESS_MARKER) != 1 or 'run_early_probe' in source:
        raise ValueError('Unexpected or already instrumented boot harness')
    return source.replace(HARNESS_MARKER, HARNESS_INJECTION, 1)


def ram_ready(serial):
    if not Path(serial).exists():
        return False
    return 'P50_STAGE_READY' in {x.strip() for x in Path(serial).read_text(errors='replace').splitlines()}


def wait_for_color(monitor, out, color, filename, timeout=20):
    from web85.qemu_debian_live_smoke import qmp
    deadline = time.monotonic() + timeout
    ppm = Path(out)/'early-current.ppm'
    while time.monotonic() < deadline:
        qmp(monitor, 'screendump', {'filename': str(ppm)})
        with Image.open(ppm) as image:
            image.load()
            if page_color_visible(image, color):
                image.save(Path(out)/filename, 'PNG', optimize=True)
                return True
        time.sleep(0.2)
    if ppm.exists():
        with Image.open(ppm) as image:
            image.save(Path(out)/('failed-'+filename), 'PNG', optimize=True)
    return False


def run_early_probe(monitor, out, started, serial):
    from web103.site_test import char_keys, send_key
    report = {'early_navigation_start_seconds': round(time.monotonic()-started, 2),
              'early_page_seen_seconds': None, 'early_js_response_seconds': None,
              'early_media_removed': False, 'ram_ready_before_early_navigation': ram_ready(serial),
              'ram_ready_before_early_js_response': None, 'early_screenshots': []}
    send_key(monitor, ['ctrl', 'l'], 100)
    time.sleep(0.25)
    for char in 'http://10.0.2.2:8766/e':
        send_key(monitor, char_keys(char), 35)
        time.sleep(0.07)
    send_key(monitor, ['ret'], 100)
    if not wait_for_color(monitor, out, LOADED_COLOR, 'early_loaded.png'):
        return report
    report['early_page_seen_seconds'] = round(time.monotonic()-started, 2)
    report['early_screenshots'].append('early_loaded.png')
    time.sleep(0.3)
    send_key(monitor, ['ret'], 100)
    if not wait_for_color(monitor, out, RESPONDED_COLOR, 'early_responded.png'):
        return report
    report['early_js_response_seconds'] = round(time.monotonic()-started, 2)
    report['ram_ready_before_early_js_response'] = ram_ready(serial)
    report['early_screenshots'].append('early_responded.png')
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('destination', type=Path)
    args = p.parse_args()
    if args.source.resolve() == args.destination.resolve():
        raise ValueError('Never overwrite the reference harness')
    args.destination.write_text(patch_harness(args.source.read_text()))


if __name__ == '__main__':
    main()
