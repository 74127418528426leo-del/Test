#!/usr/bin/env python3
"""Generate a VM harness that records, but does not assert, a public site frame."""
from pathlib import Path
import argparse

MARKER = "                    result['screenshots'].append('external_https.png')\n"
EXTRA = '''                    # P50_V112_OPTIONAL_SITE_PROBE: snapshot only; human review required.
                    navigate(monitor, os.environ['P50_TEST_URL'])
                    time.sleep(35)
                    capture(monitor, out, 'requested_site.png')
                    result['screenshots'].append('requested_site.png')
'''

def patch(source):
    if source.count(MARKER) != 1 or 'P50_V112_OPTIONAL_SITE_PROBE' in source:
        raise ValueError('Unexpected or previously patched benchmark')
    return source.replace(MARKER, MARKER + EXTRA, 1)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    args = p.parse_args()
    if args.source.resolve() == args.output.resolve():
        raise ValueError('Refusing to overwrite input harness')
    args.output.write_text(patch(args.source.read_text()))

if __name__ == '__main__': main()
