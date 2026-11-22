"""Prepare the isolated compact BIOS images for device and window-manager trials."""
import argparse
from pathlib import Path
import shutil
import subprocess

from repack import replace_once


def keep_rng_evidence(root):
    init = root / 'init'
    text = init.read_text()
    at = text.index('# Start kernel randomness initialization while drivers load.')
    end = text.index('\n\n', at)
    worker = text[at:end]
    if worker.count('--initialize-rng') != 1 or worker.count('P50_FIVE_RNG_READY') != 1:
        raise ValueError('Unexpected entropy worker')
    # The initramfs loses its /dev and /proc paths during switch_root. The
    # shell writes the result from the same successful getrandom call through
    # descriptors opened before it blocks. No executable is looked up afterward.
    stable = r'''# Start kernel randomness initialization while drivers load.
(
    if /usr/lib/p50-stage/p50-write-xauthority --initialize-rng; then
        read -r stamp idle <&3 || stamp=unknown
        printf 'P50_FIVE_RNG_READY %s\n' "$stamp" >&4
    else
        printf 'P50_FIVE_RNG_INIT_FAILED\n' >&4
    fi
) 3</proc/uptime 4>/dev/ttyS0 </dev/null >/dev/null 2>&1 &'''
    init.write_text(text[:at] + stable + text[end:])


def add_early_module(root, source, module):
    versions = list((root / 'usr/lib/modules').glob('*/kernel'))
    if len(versions) != 1:
        raise ValueError('Expected a single compact kernel')
    release = versions[0].parent.name
    module_dir = source / 'usr/lib/modules' / release
    result = subprocess.run(
        ['modprobe', '-d', str(source.resolve()), '-S', release, '--ignore-install', '--show-depends', module],
        check=True, text=True, capture_output=True,
    )
    modules = [Path(line.split()[1]).resolve(strict=True)
               for line in result.stdout.splitlines() if line.startswith('insmod ')]
    if not any(m.name.split('.ko', 1)[0].replace('-', '_') == module.replace('-', '_') for m in modules):
        raise ValueError(f'The source root does not contain the pinned {module} driver')
    for path in modules:
        relative = path.relative_to(module_dir.resolve())
        target = versions[0].parent / relative
        if target.exists():
            if target.read_bytes() != path.read_bytes():
                raise ValueError(f'Existing module has a different build: {relative}')
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    subprocess.run(['depmod', '-b', str(root.resolve()), '-a', release], check=True)


def prepare_devices(root, modules):
    add_early_module(root, modules, 'bochs')
    init = root / 'init'
    marker = '\nexport P50_OPTICAL_PATH\n'
    probe = r'''
if [ "$P50_OPTICAL_PATH" = 1 ]; then
    (
        if modprobe -q -b bochs; then
            read -r stamp idle <&3 || stamp=unknown
            printf 'P50_BIOS_EARLY_DRM %s\n' "$stamp" >&4
        fi
    ) 3</proc/uptime 4>/dev/ttyS0 </dev/null >/dev/null 2>&1 &
fi
'''
    init.write_text(replace_once(init.read_text(), marker, marker + probe))
    helpers = root / 'usr/lib/live/boot/9990-misc-helpers.sh'
    text = helpers.read_text()
    begin = text.index('\tlosetup -f 1>/dev/null\n', text.index('\nsetup_loop ()'))
    end = text.index("\n\toptions=''", begin)
    fallback = text[begin:end]
    fast = r'''
    if [ "${P50_OPTICAL_PATH:-0}" = 1 ] && [ "$fspath" = /run/live/medium/live/filesystem.squashfs ] &&
       dev="$(losetup -f 2>/dev/null)" && [ -b "$dev" ]; then
        read -r stamp idle </proc/uptime
        printf 'P50_BIOS_LOOP_READY %s\n' "$stamp" >/dev/ttyS0
    else
'''
    text = text[:begin] + fast + fallback + '    fi\n' + text[end:]
    old = '            udevadm settle\n            p50_mm='
    new = '            if [ "${P50_OPTICAL_PATH:-0}" != 1 ]; then udevadm settle; fi\n            p50_mm='
    text = replace_once(text, old, new)
    old = 'mknod /dev/mapper/p50-staged-root b "${p50_major}" "${p50_minor}" || panic'
    new = 'mknod /dev/mapper/p50-staged-root b "${p50_major}" "${p50_minor}" || [ -b /dev/mapper/p50-staged-root ] || panic'
    text = replace_once(text, old, new)
    text = replace_once(text, "stat -c '%t:%T' /dev/mapper/p50-staged-root", "stat -L -c '%t:%T' /dev/mapper/p50-staged-root")
    helpers.write_text(text)


def prepare_session(root, session_source, monitor):
    seed = root / 'usr/lib/p50-wm'
    seed.mkdir()
    original = session_source.read_text()
    stock = '/usr/lib/x86_64-linux-gnu/openbox-autostart'
    session = replace_once(original, stock, '/usr/local/libexec/p50-openbox-ready')
    (seed / 'openbox-session').write_text(session)
    shutil.copyfile(monitor, seed / 'wait-firefox')
    after = r'''#!/bin/sh
set -eu
read -r stamp idle </proc/uptime
printf '%s\n' "$stamp" >"$XDG_RUNTIME_DIR/p50-openbox-ready"
if /usr/local/libexec/p50-wait-firefox; then
    read -r stamp idle </proc/uptime
    printf '%s\n' "$stamp" >"$XDG_RUNTIME_DIR/p50-first-window"
fi
exec /usr/lib/x86_64-linux-gnu/openbox-autostart "$@"
'''
    (seed / 'openbox-ready').write_text(after)
    main = root / 'usr/lib/live/boot/9990-main.sh'
    text = main.read_text()
    here = 'cat > "$p50_start" <<\'P50_V123_START_X\''
    install = r'''        mkdir -p "$p50_root/usr/local/libexec" || panic "p50: cannot stage window monitor"
        for p50_part in openbox-session openbox-ready wait-firefox; do
            p50_target="$p50_root/usr/local/libexec/p50-$p50_part"
            [ ! -e "$p50_target" ] && [ ! -L "$p50_target" ] || panic "p50: unexpected window helper"
            cp "/usr/lib/p50-wm/$p50_part" "$p50_target" || panic "p50: cannot install window helper"
            chmod 0755 "$p50_target" || panic "p50: cannot set window helper permissions"
        done
'''
    text = replace_once(text, here, install + here)
    firefox = text.index("printf 'P50_V127_FIREFOX_DIRECT_EXEC")
    watch = text.index("printf 'P50_V137_OPENBOX_DEFERRED", firefox)
    end = text.index('>/run/p50-v123-openbox.log 2>&1 &\n', watch) + len('>/run/p50-v123-openbox.log 2>&1 &\n')
    manager = text[watch:end]
    manager = replace_once(manager, '/bin/sh -c "sleep 2; exec /usr/bin/openbox-session"', '/usr/local/libexec/p50-openbox-session')
    manager = replace_once(manager, 'P50_V137_OPENBOX_DEFERRED', 'P50_BIOS_EARLY_OPENBOX')
    text = text[:firefox] + manager + text[firefox:watch] + text[end:]
    observation = "printf 'P50_V123_EARLY_X11_FORENSICS_END\\n'"
    text = replace_once(text, observation, r'''for mark in p50-openbox-ready p50-first-window; do
        if [ -s "/run/puppy50-browser-session/$mark" ]; then
            printf 'P50_WM_OBSERVED %s ' "$mark"
            cat "/run/puppy50-browser-session/$mark"
        fi
    done
    ''' + observation)
    main.write_text(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--modules', type=Path)
    parser.add_argument('--session', type=Path)
    parser.add_argument('--monitor', type=Path)
    args = parser.parse_args()
    keep_rng_evidence(args.root)
    if args.modules:
        prepare_devices(args.root, args.modules)
    if args.session:
        if not args.monitor:
            parser.error('--session needs --monitor')
        prepare_session(args.root, args.session, args.monitor)


if __name__ == '__main__':
    main()
