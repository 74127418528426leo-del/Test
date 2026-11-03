#!/usr/bin/env python3
"""Re-evaluate preserved v69 QEMU raw evidence using correct later frame stages.

The original job failed a legacy frame timing/regex gate. We do NOT
rewrite its conclusion, and cannot infer a website from curl/keypress.
Release qualification requires real guest strict CA HTTPS, RAM ejection,
actual DOM color transitions at 145/195/245s, and visual review of the
exact final public webpage frame bound by SHA256.
"""
import argparse,hashlib,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"web56"))
from frame_stages import compare_stages,profile

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def validate(iso,evidence,review):
    iso=Path(iso);evidence=Path(evidence)
    root=evidence/"evidence"/"ram_1024MiB"
    if not iso.is_file() or iso.stat().st_size<100*1024*1024:
        raise ValueError("Tested ISO missing or unexpectedly small")
    with iso.open('rb') as f:
        f.seek(16*2048+1)
        if f.read(5)!=b'CD001':raise ValueError("ISO9660 signature failed")
    result=json.loads((root/"result.json").read_text())
    serial=(root/"serial.log").read_text(errors="replace")
    human=json.loads(Path(review).read_text())
    checks={
      "ram_copy":result.get("ram_copy_complete") is True,
      "ram_switch":result.get("ram_root_switch") is True,
      "cd_ejected":result.get("media_ejection_verified") is True,
      "guest_dhcp":'PUPPY50_V67_DHCP=PASS' in serial,
      "guest_dns":'PUPPY50_V67_DNS=PASS' in serial,
      "guest_tls_ca_verified":'PUPPY50_V67_EXTERNAL_TLS_CA_VERIFIED=PASS' in serial,
      "guest_host_bridge_tls":'PUPPY50_V67_EXTERNAL_TLS_VIA_HOST_CONNECT=PASS' in serial,
      "firefox_proxy_policy":'PUPPY50_V67_FIREFOX_HTTPS_PROXY_POLICY=APPLIED' in serial,
      "native_firefox_new_tab_requested":'PUPPY50_V69_NATIVE_FIREFOX_NAV_REQUESTED=https://example.com/' in serial,
      "native_firefox_new_tab_exit_success":'PUPPY50_V69_NATIVE_FIREFOX_NAV_EXIT=0' in serial,
      "QEMU_actual_mouse_command":result.get("mouse_click_submitted") is True,
      "QEMU_actual_key_command":result.get("keypress_submitted_to_qemu") is True,
    }
    stages=compare_stages(root/"frame_145.ppm",root/"frame_195.ppm",root/"frame_245.ppm")
    checks['dom_js_mouse_keyboard_frame_stages']=stages['full_input_proof']
    final=root/"frame_375.ppm"
    checks['review_binds_exact_iso']=human.get('iso_sha256')==digest(iso)
    checks['review_binds_exact_final_frame']=human.get('screenshot_sha256')==digest(final)
    checks['reviewed_public_https_site_visible']=all(human.get(k) is True for k in
      ("reviewed_screenshot","public_website_actually_visible_in_firefox","firefox_HTTPS_URL_confirmed"))
    checks['reviewed_correct_run']=human.get('run_id')==41656250129
    checks['reviewed_correct_website']=human.get('website')=="https://example.com/"
    post=profile(final)
    checks['public_page_replaces_green_local_page']=post['fractions']['keyboard']<0.05
    missing=[key for key,passed in checks.items() if not passed]
    if missing:raise ValueError("Reject public release: "+repr(missing))
    return {
      "schema":"PUPPY50_V69_PUBLIC_TESTED_ONLINE_ISO_PROOF",
      "source_run_id":41656250129,
      "original_KVM_workflow_conclusion":"failure; legacy parser and mistimed local input frames, re-evaluated from raw artifacts",
      "iso_file":iso.name,"iso_sha256":digest(iso),"iso_bytes":iso.stat().st_size,
      "actual_1gib_RAM_root_boot_and_cd_ejection":True,
      "actual_Firefox_JavaScript_mouse_keyboard_proven":True,
      "actual_public_example_com_HTTPS_frame_reviewed":True,
      "guest_CA_verified_external_HTTPS":True,
      "reviewed_frame_sha256":digest(final),
      "independent_input_pixel_stages":stages,
      "384mib_Firefox_working":False,
      "physical_any_network_or_WIFI_verified":False,
      "network_security_updates_certified":False,
      "HTTPS_other_websites_independently_tested":False,
      "experimental_demo_automatically_opens_example_com_after_test":True,
      "safe_for_sensitive_browsing":False
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--iso',type=Path,required=True)
    p.add_argument('--evidence',type=Path,required=True)
    p.add_argument('--review',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    report=validate(a.iso,a.evidence,a.review)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="independent_input_pixel_stages"},indent=2))
if __name__=="__main__":main()
