#!/usr/bin/env python3
"""Verify exact post-release virtual video and panorama evidence."""
import hashlib
import json
import os
from pathlib import Path

root=Path(os.environ.get('P50_SUPPLEMENTAL_DIR','evidence'))
def load(p): return json.loads(p.read_text())
def check(p,expected):
    actual=hashlib.sha256(p.read_bytes()).hexdigest()
    assert actual==expected,(p,actual)
def boot_ok(p):
    r=load(p)
    assert r['guest_ram_mib']==3072 and r['media_ejected'] and r['input_sent_after_eject'] and r['qemu_running_at_end']
    assert r['staged_ram_ready_seconds'] is not None and not r['errors']

video=root/'video'
boot_ok(video/'qemu/result.json')
check(video/'qemu/requested_site.png','1bd4d15775c2662082eae7dd7712f4c6cd62313635802b017b4e99613da08be3')
meta=load(video/'reports/clip-metadata.json')['streams'][0]
assert (meta['codec_name'],meta['width'],meta['height'],meta['r_frame_rate'])==('h264',3840,2160,'24/1')
result=load(video/'reports/playback-result.json')
assert result['verified_4k_frame_progress'] and (result['source_width'],result['source_height'])==(3840,2160)
assert (result['observed_total_frames'],result['observed_dropped_frames'])==(770,0)
assert abs(result['observation_seconds']-32.08)<1e-6
from video4k_evaluate import evaluate
rows=[json.loads(line) for line in (video/'reports/telemetry.jsonl').read_text().splitlines() if line.strip()]
assert evaluate(rows)==result

panorama=root/'panorama'
boot_ok(panorama/'qemu/result.json')
check(panorama/'qemu/requested_site.png','83739c6d4d8b7689b2a31780879898b5563011d89bb78747c0d177efb8376e0c')
check(panorama/'qemu/panorama_after_keys.png','d21e6af8930b80506e8ac140367fcbbb7ea4a0e8318d42808037c560c1f4a298')
r=load(panorama/'reports/panorama-change.json')
assert r['keyboard_events_sent']==12 and r['changed_pixel_fraction']>.9
print('Exact video telemetry and visually reviewed panorama frames verified.')
