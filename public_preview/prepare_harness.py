#!/usr/bin/env python3
"""Prepare disposable VM test harness variants; never alter guest ISO bytes."""
import argparse
import ast
from pathlib import Path
import subprocess
import sys


def replace_function(text, name, body):
    tree = ast.parse(text)
    funcs = [x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == name]
    if len(funcs) != 1:
        raise ValueError('Unexpected function: ' + name)
    lines = text.splitlines(keepends=True)
    f = funcs[0]
    return ''.join(lines[:f.lineno - 1]) + body.rstrip() + '\n' + ''.join(lines[f.end_lineno:])


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--preview', type=Path, required=True)
    p.add_argument('--retry', type=Path, required=True)
    a = p.parse_args()
    src = a.source.resolve()
    sys.path.insert(0, str(src))
    from web112.early_probe import patch_harness
    original = (src/'web109/boot_bench_staged.py').read_text()
    detector = (a.preview/'home_detector.py').read_text()
    original = replace_function(original, 'home_visible', detector)
    pause = "time.sleep(.05 if args.select_fullram_fallback and not result['fullram_fallback_selected'] else .8)"
    if original.count(pause) != 1:
        raise ValueError('Unexpected capture interval')
    original = original.replace(pause, pause.replace('else .8', 'else .2'), 1)
    original = patch_harness(original)
    early = src/'web112/early_probe.py'
    revised = replace_function(early.read_text(), 'page_color_visible', '''def page_color_visible(image, color):
    image = image.convert('RGB')
    width, height = image.size
    points = [(0.1, 0.5), (0.5, 0.5), (0.85, 0.5), (0.2, 0.8), (0.8, 0.8)]
    return all(all(abs(image.getpixel((int(width*x), int(height*y)))[i]-color[i]) <= 5
                   for i in range(3)) for x,y in points)
''')
    ast.parse(revised)
    early.write_text(revised)
    staged = src/'web109/boot_bench_ahci.py'
    staged.write_text(original)
    subprocess.run([sys.executable, str(a.retry), str(staged)], check=True)
    staged_text = staged.read_text()
    capture = "                capture(monitor, out, 'after_input.png')"
    if staged_text.count(capture) != 1:
        raise ValueError('Unexpected post-eject screenshot location')
    staged_text = staged_text.replace(capture, '                time.sleep(3)\n' + capture, 1)
    usb = src/'web109/boot_bench_usb_public.py'
    usb.write_text(staged_text)
    old = "cmd += ['-device', 'qemu-xhci,id=xhci', '-device', 'usb-storage,drive=livecd,id=bootusb,bootindex=1']"
    new = "cmd += ['-device', 'ich9-ahci,id=ahci', '-device', 'ide-cd,drive=livecd,bus=ahci.0,id=bootusb,bootindex=1']"
    if staged_text.count(old) != 1 or staged_text.count("if args.media == 'optical':") != 1:
        raise ValueError('Unexpected virtual media logic')
    ahci = staged_text.replace(old, new, 1).replace("if args.media == 'optical':", "if True:  # AHCI CD eject", 1)
    ast.parse(ahci)
    staged.write_text(ahci)
    graphics_base = usb.read_text()
    marker = "'-display', 'none', '-vga', 'std',"
    if graphics_base.count(marker) != 1:
        raise ValueError('Unexpected virtual video logic')
    for graphics in ('cirrus', 'virtio'):
        variant = graphics_base.replace(marker, "'-display', 'none', '-vga', '" + graphics + "',", 1)
        ast.parse(variant)
        (src/f'web109/boot_bench_{graphics}_public.py').write_text(variant)
    print('Prepared standard, AHCI, Cirrus and VirtIO harnesses; guest ISO unchanged')


if __name__ == '__main__':
    main()
