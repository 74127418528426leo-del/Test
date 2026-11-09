#!/usr/bin/env python3
"""Record browser video dimensions and playback time without altering the page."""
import argparse
from pathlib import Path

MARKER="                    result['screenshots'].append('requested_site.png')\n"
EXTRA='''                    # P50_PEXELS_CONSOLE: read browser's video element only.
                    from web103.site_test import video_console
                    result['video_console_commands'] = []
                    video_console(monitor, out, result)
'''


def patch(source):
    if source.count(MARKER)!=1 or 'P50_PEXELS_CONSOLE' in source:
        raise ValueError('Unexpected or already instrumented site harness')
    return source.replace(MARKER,MARKER+EXTRA,1)


def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    if a.source.resolve()==a.output.resolve():raise ValueError('Refusing to overwrite input')
    a.output.write_text(patch(a.source.read_text()))


if __name__=='__main__':main()
