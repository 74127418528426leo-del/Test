#!/usr/bin/env python3
"""Add a click and keyboard pan to the generated panorama snapshot harness."""
import argparse
from pathlib import Path

MARKER="                    result['screenshots'].append('requested_site.png')\n"
EXTRA='''                    # P50_PANORAMA_KEY_PROBE: focus canvas at the default center and press arrows.
                    from web103.site_test import send_key
                    qmp(monitor, 'human-monitor-command', {'command-line':'mouse_button 1'})
                    time.sleep(.2)
                    qmp(monitor, 'human-monitor-command', {'command-line':'mouse_button 0'})
                    for _ in range(12):
                        send_key(monitor, ['right'], 100)
                        time.sleep(.12)
                    time.sleep(5)
                    capture(monitor, out, 'panorama_after_keys.png')
                    result['screenshots'].append('panorama_after_keys.png')
'''

def patch(source):
    if source.count(MARKER)!=1 or 'P50_PANORAMA_KEY_PROBE' in source:
        raise ValueError('Unexpected or previously patched site benchmark')
    return source.replace(MARKER,MARKER+EXTRA,1)

def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    if a.source.resolve()==a.output.resolve():raise ValueError('Refusing to overwrite input')
    a.output.write_text(patch(a.source.read_text()))

if __name__=='__main__':main()
