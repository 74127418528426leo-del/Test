#!/usr/bin/env python3
"""Conservatively evaluate Firefox telemetry for a synthetic 4K video."""
import argparse
import json
from pathlib import Path


def evaluate(samples):
    usable = sorted((r for r in samples if r.get('width') == 3840 and r.get('height') == 2160
                     and all(isinstance(r.get(k), (int, float)) for k in
                             ('wall_ms', 'media_time', 'total_frames', 'dropped_frames'))),
                    key=lambda r: r['wall_ms'])
    if len(usable) < 3:
        raise ValueError('Fewer than three correctly sized telemetry samples')
    first, last = usable[0], usable[-1]
    seconds = (last['wall_ms'] - first['wall_ms']) / 1000
    total = last['total_frames'] - first['total_frames']
    dropped = last['dropped_frames'] - first['dropped_frames']
    media_advanced = any(b['media_time'] - a['media_time'] > .25
                         for a, b in zip(usable, usable[1:]))
    if seconds < 2 or total < 4 or dropped < 0 or dropped > total or not media_advanced:
        raise ValueError('Video counters or playback time did not show valid progress')
    return {'verified_4k_frame_progress': True,
            'source_width': 3840, 'source_height': 2160,
            'telemetry_samples': len(usable), 'observation_seconds': seconds,
            'observed_total_frames': total, 'observed_dropped_frames': dropped,
            'observed_displayed_frames': total - dropped,
            'observed_total_frames_per_second': round(total/seconds, 2),
            'observed_displayed_frames_per_second': round((total-dropped)/seconds, 2),
            'interpretation': 'Synthetic local 4K video in a virtual machine; not evidence of YouTube, Pexels, physical hardware, or every 4K codec/bitrate.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('telemetry',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    samples=[json.loads(line) for line in a.telemetry.read_text().splitlines() if line.strip()]
    report=evaluate(samples)
    a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__ == '__main__': main()
