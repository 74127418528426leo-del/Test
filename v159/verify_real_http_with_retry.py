#!/usr/bin/env python3
"""Patch only disposable QEMU benchmark harness, never shipping OS bytes.

Original benchmark sends a single QMP Ctrl+L + typed URL after the verified
RAM transition and interprets "keys sent" as browser network success.
That is NOT evidence that Firefox got a server HTTP200. This patch retries
inside the SAME already-running VM (never reboots, no host-generated HTTP),
and rejects the run if the web server never observes the real browser GET.

Keep authentic Firefox framebuffer first-frame timing unchanged.
"""
from pathlib import Path
import argparse,ast

OLD = """                nonce = os.environ.get('P50_NONCE', 'P50-TEST')
                local = 'http://10.0.2.2:8765/after.html?nonce=' + nonce
                navigate(monitor, local if args.mode == 'online' else 'about:about')
                result['input_sent_after_eject'] = True
                time.sleep(18)
                capture(monitor, out, 'after_input.png')
                result['screenshots'].append('after_input.png')"""

NEW = """                nonce = os.environ.get('P50_NONCE', 'P50-TEST')
                local = 'http://10.0.2.2:8765/after.html?nonce=' + nonce
                expected = 'GET /after.html?nonce=' + nonce + ' HTTP/1.1" 200 '
                fixture_log = out.parent / 'reports' / 'fixture-after.log'
                def real_guest_http_receipts():
                    return (fixture_log.read_text(errors='replace').count(expected)
                            if fixture_log.is_file() else 0)
                baseline_receipts = real_guest_http_receipts()
                result['post_eject_browser_http200_confirmed'] = False
                result['post_eject_navigation_attempts'] = 0
                for attempt in range(1, 4):
                    if attempt > 1:
                        from web103.site_test import send_key
                        send_key(monitor, ['esc'], 115)
                        time.sleep(.8)
                    navigate(monitor, local if args.mode == 'online' else 'about:about')
                    result['input_sent_after_eject'] = True
                    result['post_eject_navigation_attempts'] = attempt
                    deadline = time.monotonic() + (12 if args.mode == 'online' else 3)
                    while time.monotonic() < deadline:
                        if args.mode != 'online' or real_guest_http_receipts() > baseline_receipts:
                            result['post_eject_browser_http200_confirmed'] = args.mode == 'online'
                            break
                        time.sleep(.4)
                    if result['post_eject_browser_http200_confirmed'] or args.mode != 'online':
                        break
                if args.mode == 'online' and not result['post_eject_browser_http200_confirmed']:
                    raise RuntimeError(
                        'Guest Firefox post-eject HTTP200 missing after three actual QMP '
                        'navigation attempts; no fake host GET substituted')
                capture(monitor, out, 'after_input.png')
                result['screenshots'].append('after_input.png')"""

def patch(path:Path):
    path=path.resolve(strict=True)
    if not path.is_file() or path.name!='boot_bench_ahci.py':
        raise ValueError('Only generated QEMU AHCI benchmark script may be patched')
    s=path.read_text()
    if s.count(OLD)!=1 or 'post_eject_browser_http200_confirmed' in s:
        raise ValueError(f'Unexpected harness; original navigation count={s.count(OLD)}')
    out=s.replace(OLD,NEW,1)
    ast.parse(out)
    if out.count("first_home_seen_seconds")!=s.count("first_home_seen_seconds"):
        raise ValueError('First-frame timing unexpectedly modified')
    path.write_text(out)
    return path

if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument('benchmark_harness',type=Path)
    print(patch(a.parse_args().benchmark_harness))
