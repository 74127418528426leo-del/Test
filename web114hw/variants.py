#!/usr/bin/env python3
"""Create test-only QEMU configurations; the guest image stays unchanged."""
import argparse
from pathlib import Path

CPU = "'-smp', '2'"
USB = "'qemu-xhci,id=xhci'"
DISK = "'usb-storage,drive=livecd,id=bootusb,bootindex=1'"
POLL = "time.sleep(.05 if args.select_fullram_fallback and not result['fullram_fallback_selected'] else .8)"


def variant(text, mode):
    if mode not in ('control', 'cpu', 'ehci'):
        raise ValueError('Unknown mode')
    for marker in (CPU, USB, DISK, POLL):
        if text.count(marker) != 1:
            raise ValueError('Unexpected benchmark input')
    text = text.replace(POLL, POLL.replace('else .8)', 'else .2)'), 1)
    if mode == 'cpu':
        text = text.replace(CPU, "'-smp', '4,sockets=1,cores=2,threads=2'", 1)
    if mode == 'ehci':
        text = text.replace(USB, "'usb-ehci,id=ehci'", 1)
        text = text.replace(DISK, "'usb-storage,drive=livecd,id=bootusb,bootindex=1,bus=ehci.0'", 1)
    return text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('mode', choices=('control', 'cpu', 'ehci'))
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        raise ValueError('Do not overwrite the source')
    args.output.write_text(variant(args.source.read_text(), args.mode))


if __name__ == '__main__':
    main()
