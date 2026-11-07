#!/usr/bin/env python3
"""Check pinned virtual evidence and manual visual-review hashes before release."""
from pathlib import Path
import hashlib
import json

review = json.loads(Path('web109/V109_MANUAL_REVIEW.json').read_text())
assert review['iso_sha256'] == 'e6b341ae3a272bb6bfa063814b2b61a14ba9dadd5f41137a8203f651120671da'

def load(path):
    return json.loads(Path(path).read_text())

def frames(folder, hashes):
    for rel, expected in hashes.items():
        p = Path(folder) / rel
        assert hashlib.sha256(p.read_bytes()).hexdigest() == expected, str(p)

def serial(folder):
    return (Path(folder)/'qemu/serial.log').read_text(errors='replace')

def fixture(folder, run):
    data=(Path(folder)/'reports/fixture.log').read_text()
    assert f'GET /after.html?nonce=P50-{run} HTTP/1.1" 200' in data, str(folder)

def ok_after_eject(result):
    assert result['media_ejected'] and result['input_sent_after_eject'] and result['qemu_running_at_end']
    assert not result['errors'], result['errors']

smoke=Path('evidence/smoke')
assert review['candidate_smoke']['run_id']==42422358970
frames(smoke,review['candidate_smoke']['screenshots_sha256'])
ok_after_eject(load(smoke/'qemu/result.json'))
fixture(smoke,42422358970)
checks=(smoke/'reports/media-checksums.txt').read_text().splitlines()
assert len(checks)==292 and all(x.endswith(': OK') for x in checks)

assert review['validation_run_id']==42422727615 and len(review['validation'])==6
for name,case in review['validation'].items():
    folder=Path('evidence/validation')/('Puppy50-v109-validation-'+name)
    r=load(folder/'qemu/result.json')
    frames(folder,case['screenshots_sha256'])
    assert r['first_home_seen_seconds']==case['first_home_seconds']
    assert r['staged_ram_ready_seconds']==case['ram_ready_seconds']
    s=serial(folder)
    if name=='bios-usb-1536':
        assert not r['media_ejected'] and r['staged_ram_ready_seconds'] is None
        assert 'insufficient available memory and reserve' in s and 'P50_STAGE_READY' not in s
        assert r['errors'] and case['outcome']=='failure'
        continue
    assert case['outcome']=='success'
    ok_after_eject(r)
    if name=='bios-fullram-fallback':
        assert r['fullram_fallback_selected'] and 'P50_STAGE_READY' not in s
    else:
        assert r['staged_ram_ready_seconds'] is not None
        for marker in ('P50_STAGE_COPY_VERIFIED','P50_STAGE_RAM_BACKING=','P50_STAGE_READY'):
            assert marker in s, (name,marker)
    if r['network_mode']=='online':
        fixture(folder,42422727615)
    if name=='connectivity-restored':
        assert r['outbound_https_intentionally_blocked'] and r['network_restored_signal_observed']

folder=Path('evidence/invalid-copy')
assert review['invalid_copy']['run_id']==42422636222
frames(folder,review['invalid_copy']['screenshots_sha256'])
r=load(folder/'qemu/result.json'); s=serial(folder)
assert r['keep_media_experiment'] and not r['media_ejected'] and r['input_sent'] and r['qemu_running_at_end']
assert not r['errors'] and 'copied hash differs from ISO manifest' in s and 'P50_STAGE_READY' not in s
fixture(folder,42422636222)

folder=Path('evidence/comparison')
assert review['benchmark']['run_id']==42422773595
frames(folder,review['benchmark']['screenshots_sha256'])
c=load(folder/'reports/comparison.json')
assert c['baseline_mean_seconds']==45.34 and c['candidate_mean_seconds']==19.46
assert c['candidate_ready_seconds']==[38.11,38.14] and not c['physical_acer_tested']
assert (folder/'reports/fixture.log').read_text().count('GET /after.html?nonce=P50-42422773595 HTTP/1.1" 200')==4
for trial in ('base1','cand1','cand2','base2'):
    ok_after_eject(load(folder/trial/'result.json'))

folder=Path('evidence/sites')
assert review['requested_sites']['run_id']==42422912399
frames(folder,review['requested_sites']['screenshots_sha256'])
r=load(folder/'qemu/result.json')
ok_after_eject(r)
assert len(r['site_smokes'])==4 and not any(x['verified_js_result'] for x in r['video_console_commands'])
fixture(folder,42422912399)

folder=Path('evidence/initrd-audit')
for name in ('rsync-forward.txt','rsync-reverse.txt'):
    assert not (folder/name).read_bytes(), name
assert 'Root SquashFS and early prefix byte-identical' in (folder/'audit-result.txt').read_text()
notes=Path('web109/V109_RELEASE_NOTES.md').read_text()
for text in ('eight-second goal has not been achieved','physical Acer','1.5 GiB','Pexels','not been tested'):
    assert text in notes,text
print('Pinned ISO test evidence, image audit, and visually reviewed frames verified.')
