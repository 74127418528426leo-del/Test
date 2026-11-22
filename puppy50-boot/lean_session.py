#!/usr/bin/env python3
"""Adjust the compact BIOS VM session and add early kernel stage markers."""

import argparse
from pathlib import Path

from repack import modify_boot_script, replace_once


def patch(root):
    modify_boot_script(root, 128)
    script = root / 'usr/lib/live/boot/9990-main.sh'
    text = script.read_text()
    text = replace_once(text, 'p50_cookie="$(mcookie)"\np50_mark COOKIE\n', '')
    text = replace_once(
        text,
        'xauth -f /home/user/.Xauthority add :0 . "$p50_cookie"\np50_mark XAUTH',
        r'''if /run/p50-stage/tools/p50-write-xauthority /home/user/.Xauthority; then
    p50_mark LOCAL_COOKIE_OK
else
    p50_cookie="$(mcookie)"
    xauth -f /home/user/.Xauthority add :0 . "$p50_cookie"
    p50_mark LOCAL_COOKIE_FALLBACK
fi
p50_mark XAUTH''',
    )
    text = replace_once(
        text,
        '        chmod 0644 "$p50_profile/user.js"',
        r'''        printf 'user_pref("datareporting.policy.dataSubmissionEnabled", false);\n' >>"$p50_profile/user.js" || panic "p50: cannot set live browser telemetry preference"
        chmod 0644 "$p50_profile/user.js"''',
    )
    script.write_text(text)

    init = root / 'init'
    text = init.read_text()
    start = 'mkdir -m 0700 /run/initramfs\n'
    warm = r'''# Start kernel randomness initialization while drivers load.
(
    if /usr/lib/p50-stage/p50-write-xauthority --initialize-rng; then
        printf 'P50_FIVE_RNG_READY %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
    else
        printf 'P50_FIVE_RNG_INIT_FAILED\n' >/dev/ttyS0
    fi
) </dev/null >/dev/null 2>&1 &
'''
    text = replace_once(text, start, start + warm)
    for instruction, marker in (
        ('run_scripts /scripts/init-top', 'INIT_TOP'),
        ('load_modules', 'ESSENTIAL_MODULES'),
        ('mountroot', 'ROOT_MOUNT_RETURN'),
    ):
        pos = f'\n{instruction}\n'
        after = f"printf 'P50_FIVE_{marker} %s\\n' \"$(cat /proc/uptime)\" >/dev/ttyS0"
        text = replace_once(text, pos, pos + after + '\n')
    init.write_text(text)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    patch(parser.parse_args().root)
