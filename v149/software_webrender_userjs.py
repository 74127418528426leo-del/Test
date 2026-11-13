#!/usr/bin/env python3
"""Research-only test Mozilla software WebRender on QEMU virtual GPU.

Mozilla Bugzilla 2084921 documents ~1.5sec first-paint stall on llvmpipe.
Unlike old ineffective v129 global policies, explicitly write ONE preference
to the actual -profile /home/user/.mozilla/firefox/p50-default created by v139.
Do not touch GTK, HTTPS, sandbox, site isolation, DNS, full RAM or recovery.
Accept no acceleration claim without real Firefox GUI, actual loaded profile,
and original post-eject browsing proof.
"""
from pathlib import Path
import argparse

OWN='chown -R 1000:1000 "$p50_root/home/user/.mozilla" || panic "v139: could not grant profile to nonroot user"'
HOOK=r'''        # P50_V149_SOFTWARE_WEBRENDER: no GPU-accelerated llvmpipe shader JIT
        # on the testing QEMU std VGA path. All other prefs unchanged.
        [ ! -e "$p50_profile/user.js" ] && [ ! -L "$p50_profile/user.js" ] || panic "v149: Firefox user.js already exists"
        printf 'user_pref("gfx.webrender.software", true);\n' >"$p50_profile/user.js" || panic "v149: failed to create Firefox pref"
        chmod 0644 "$p50_profile/user.js" || panic "v149: cannot set Firefox user.js permission"
        printf 'P50_V149_WEBRENDER_USERJS_READY %s\n' "$(cat /proc/uptime)" >/dev/ttyS0
'''
DIAGMARK='printf \'\\nP50_V124_FORENSICS_END\\n\''
DIAG=r'''printf '\nP50_V149_USERJS_CONTENT_BEGIN\n'
    cat /home/user/.mozilla/firefox/p50-default/user.js 2>&1 || true
    printf '\nP50_V149_USERJS_CONTENT_END\n'
    p50_fxpid="$(pgrep -u user -x firefox-esr | head -1)"
    if [ -n "$p50_fxpid" ] && [ -r "/proc/$p50_fxpid/cmdline" ]; then
        printf 'P50_V149_FIREFOX_ACTUAL_COMMAND '
        tr '\000' ' ' <"/proc/$p50_fxpid/cmdline"
        printf '\n'
    fi
    printf 'P50_V149_PREFSJS_OBSERVATION\n'
    grep -F 'gfx.webrender.software' /home/user/.mozilla/firefox/p50-default/prefs.js 2>&1 || true
    '''
def patch(root:Path)->Path:
    root=root.resolve(strict=True)
    if root==Path('/') or not root.is_dir():raise ValueError('Host filesystem prohibited')
    p=root/'usr/lib/live/boot/9990-main.sh'
    if p.is_symlink() or not p.is_file():raise ValueError('Unrecognized disposable initramfs')
    s=p.read_text()
    prereqs=('P50_V139_EXPLICIT_EMPTY_FIREFOX_PROFILE','P50_V144_XORG_VT7_SELECTED',
             'P50_V141_PRIORITY_EXPERIMENT','P50_V127_FIREFOX_DIRECT_EXEC')
    if any(x not in s for x in prereqs):raise ValueError('Expected secured v147 setup including explicit Firefox profile')
    if s.count(OWN)!=1 or s.count(DIAGMARK)!=1 or 'P50_V149_SOFTWARE_WEBRENDER' in s:
        raise ValueError(f'Unexpected source owner={s.count(OWN)} diagnostic={s.count(DIAGMARK)}')
    s=s.replace(OWN,HOOK+OWN,1)
    s=s.replace(DIAGMARK,DIAG+DIAGMARK,1)
    p.write_text(s)
    return p
if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('extracted_root',type=Path)
    print(patch(a.parse_args().extracted_root))
