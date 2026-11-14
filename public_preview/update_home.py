#!/usr/bin/env python3
"""Update the public preview's built-in help while preserving its layout."""
from pathlib import Path
import argparse

REPLACEMENTS = {
    '<title>Puppy50 — Maintained Browser Pilot</title>': '<title>Puppy50 Browser Live — Public Preview</title>',
    'PUPPY50 — MAINTAINED BROWSER EXPERIMENT': 'PUPPY50 — BROWSER LIVE PUBLIC PREVIEW',
    'This experimental Debian Live edition is a second engineering track. It uses distribution-updated Firefox ESR and a Linux NetworkManager panel for choosing authorized wired and wireless connections.': 'This experimental Debian Live browser starts from removable media and uses Firefox ESR. Choose an available network from the panel below.',
    'No public website has yet been verified in this NEW Debian build until the independent QEMU tests pass.': 'Network availability and hardware support vary by computer.',
    'Boot option <code>toram</code> requests a copy of the live filesystem into memory. It requires additional RAM and is not guaranteed on 2 GiB systems. This live pilot does not overwrite your existing OS.': 'This is a temporary live session. Keep your boot device connected while using it, and save files elsewhere before shutdown. Session changes and ordinary updates do not persist after reboot.',
}


def update(path):
    data = path.read_text()
    for old, new in REPLACEMENTS.items():
        if data.count(old) != 1:
            raise ValueError('Unexpected home-page layout: ' + old[:70])
        data = data.replace(old, new, 1)
    path.write_text(data)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('html', type=Path)
    update(p.parse_args().html)
