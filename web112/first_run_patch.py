#!/usr/bin/env python3
"""Add one first-run-page policy to a test-only live initramfs."""

import argparse
from pathlib import Path

MARKER = '\n\tFstab\n\tNetbase\n'
HOOK = r'''
\t# P50_V112_FIRST_RUN_POLICY: test-only; leave full-RAM fallback alone.
\tif [ -z "${TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then
\t\tp50_distribution_link="${rootmnt}/usr/lib/firefox-esr/distribution"
\t\t[ -L "${p50_distribution_link}" ] && [ "$(readlink "${p50_distribution_link}")" = '../../share/firefox-esr/distribution' ] || panic "p50: unexpected Firefox distribution link"
\t\tp50_policy_dir="${rootmnt}/usr/share/firefox-esr/distribution"
\t\t[ -d "${p50_policy_dir}" ] && [ ! -L "${p50_policy_dir}" ] || panic "p50: unexpected Firefox policy directory"
\t\tfor p50_policy in "${rootmnt}/etc/firefox/policies/policies.json" "${rootmnt}/etc/firefox-esr/policies/policies.json" "${p50_policy_dir}/policies.json"; do
\t\t\t[ ! -e "${p50_policy}" ] && [ ! -L "${p50_policy}" ] || panic "p50: unexpected existing Firefox policy"
\t\tdone
\t\tprintf '%s\n' '{"policies":{"OverrideFirstRunPage":""}}' > "${p50_policy_dir}/policies.json" || panic "p50: cannot write first-run policy"
\tfi
'''.replace('\\t', '\t')


def patch_main(text):
    if text.count(MARKER) != 1 or 'P50_V112_FIRST_RUN_POLICY' in text:
        raise ValueError('Unexpected or already patched live boot script')
    return text.replace(MARKER, HOOK + MARKER, 1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('initrd_root', type=Path)
    args = p.parse_args()
    root = args.initrd_root.resolve(strict=True)
    if root == Path('/'):
        raise ValueError('Refusing to modify the running system')
    path = root/'usr/lib/live/boot/9990-main.sh'
    if path.is_symlink() or not path.is_file():
        raise ValueError('Expected a regular extracted live boot script')
    path.write_text(patch_main(path.read_text()))


if __name__ == '__main__':
    main()
