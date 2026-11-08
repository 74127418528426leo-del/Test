#!/usr/bin/env python3
"""Check exact candidate measurements, failed memory cases, audits and reviewed frames."""
import hashlib
import json
import os
from pathlib import Path

root=Path(os.environ.get('P50_EVIDENCE_DIR','evidence'))
review=json.loads(Path(os.environ.get('P50_REVIEW_FILE','web113/V113_MANUAL_REVIEW.json')).read_text())
assert review['iso_sha256']=='4e6dc9b9d1f8f416b47ea046ffcfc5f1c6a7a732dc9ac0e67ff49bd53d271ea1'
assert tuple(review[k] for k in ('benchmark_run_id','repeat_run_id','validation_run_id','audit_run_id','memory_run_id'))==(42535754369,42536479145,42536475888,42536473883,42536910497)

def load(path):return json.loads(path.read_text())
def frames(folder,expected):
    for name,digest in expected.items():
        p=folder/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,str(p)
def check_success(r):
    assert r['first_home_seen_seconds'] is not None
    assert r['media_ejected'] and r['input_sent_after_eject'] and r['qemu_running_at_end']
    assert not r['errors'],r['errors']
def checksums(path):
    lines=path.read_text().splitlines()
    assert len(lines)==293 and all(x.endswith(': OK') for x in lines)

b=root/'benchmark';frames(b,review['screenshots']['benchmark'])
x=load(b/'reports/comparison.json')
assert x['mode']=='drivers' and not x['physical_acer_tested'] and x['sample_interval_seconds']==.2
for key,value in {'baseline_mean_first_home_seen_seconds':14.9,'candidate_mean_first_home_seen_seconds':14.815,'baseline_mean_early_js_response_seconds':18.065,'candidate_mean_early_js_response_seconds':17.965}.items():assert abs(x[key]-value)<1e-6,(key,x[key])
assert (b/'reports/main-archive-identity.txt').read_text().startswith('The main initramfs archive is byte-identical')
assert (b/'reports/iso-hashes.txt').read_text().splitlines()[-1].startswith(review['iso_sha256'])
checksums(b/'reports/media-checksums.txt')
for n in ('base1','cand1','cand2','base2'):
    r=load(b/n/'result.json');check_success(r)
    assert r['early_js_response_seconds'] is not None and r['early_media_attached_before_navigation'] and r['early_media_attached_after_js_response']

a=root/'repeat';frames(a,review['screenshots']['repeat'])
x=load(a/'reports/comparison.json')
for key,value in {'baseline_mean_first_home_seen_seconds':16.26,'candidate_mean_first_home_seen_seconds':15.70,'baseline_mean_early_js_response_seconds':19.69666666666667,'candidate_mean_early_js_response_seconds':19.066666666666666,'baseline_mean_staged_ram_ready_seconds':37.70666666666666,'candidate_mean_staged_ram_ready_seconds':37.083333333333336}.items():assert abs(x[key]-value)<1e-6,(key,x[key])
assert not x['physical_acer_tested'] and x['home_gain_seconds']>.2 and x['js_gain_seconds']>0
for n in ('base1','cand1','cand2','base2','base3','cand3'):
    r=load(a/n/'result.json');check_success(r)
    assert r['early_js_response_seconds'] is not None and r['early_media_attached_before_navigation'] and r['early_media_attached_after_js_response']

v=root/'validation'
assert len(review['screenshots']['validation'])==5
for name,expected in review['screenshots']['validation'].items():
    folder=v/('Puppy50-v113-clean-network-validation-'+name);frames(folder,expected)
    r=load(folder/'qemu/result.json');serial=(folder/'qemu/serial.log').read_text(errors='replace')
    if name=='bios-usb-2048':
        assert r['guest_ram_mib']==2048 and r['first_home_seen_seconds'] is not None
        assert not r['media_ejected'] and r['staged_ram_ready_seconds'] is None
        assert 'P50_STAGE_FAILED: insufficient available memory and reserve' in serial and 'P50_STAGE_NOT_READY' in serial
        continue
    check_success(r);assert r['guest_ram_mib']==3072
    if name=='bios-fullram-fallback':assert r['fullram_fallback_selected'] and 'P50_STAGE_READY' not in serial
    else:
        assert r['staged_ram_ready_seconds'] is not None
        assert all(marker in serial for marker in ('P50_STAGE_COPY_VERIFIED','P50_STAGE_RAM_BACKING=','P50_STAGE_READY'))
    if r['network_mode']=='online':assert 'GET /after.html?nonce=P50-42536475888 HTTP/1.1" 200' in (folder/'reports/fixture.log').read_text()
    if name=='connectivity-restored':assert r['outbound_https_intentionally_blocked'] and r['network_restored_signal_observed']

m=root/'memory'
for size,expected in review['screenshots']['memory'].items():
    folder=m/('Puppy50-v113-memory-'+size+'-evidence');frames(folder,expected)
    r=load(folder/'reports/outcome.json')
    assert r['ram_mib']==int(size) and not r['ram_only_test_passed'] and not r['media_ejected']
    if size=='384':assert r['browser_home_seen_seconds'] is None
    else:assert r['early_js_response_seconds'] is not None and r['ram_ready_seconds'] is None

audit=root/'audit';summary=(audit/'audit-result.txt').read_text()
for phrase in ('compressed main archive','199 early network modules','all 293'):
    assert phrase.lower() in summary.lower(),phrase
assert len(load(audit/'verified-drivers.json'))==199
assert not (audit/'early-forward.txt').read_bytes() and not (audit/'early-reverse.txt').read_bytes()
checksums(audit/'media-checksums.txt')
print('Verified the exact candidate, both timing comparisons, four 3 GiB scenarios, failed 2 GiB and low-memory outcomes, independent audit, and reviewed frames.')
