#!/usr/bin/env python3
"""Fail-closed gate for a downloadable, explicitly QEMU-only Puppy50 ISO.

This intentionally does NOT demand functional 384MiB browsing. It demands:
- actual offline Firefox mouse/keyboard interaction at 1024MiB;
- actual copied RAM-root and removable-media ejection at 384MiB;
- the same real ISO used by both KVM tests;
- early evdev/psmouse kernel event interfaces in the positive control.
A boot, a submitted QEMU HMP command, or process PID alone cannot pass.
"""
import argparse
import hashlib
import json
from pathlib import Path

MIB=1048576
REQUIRED_1024=("ram_copy","root_switch","cd_ejected","script_ready",
               "mouse_event_visually_confirmed","keyboard_event_visually_confirmed")
REQUIRED_384=("ram_copy","root_switch","cd_ejected")
EARLY_SIGNALS=(
 "PUPPY50_V58_INPUT_EARLY_LOADED=evdev",
 "PUPPY50_V58_INPUT_EARLY_LOADED=psmouse",
 "PUPPY50_V58_EVENT_HANDLER_PRESENT=PASS",
)

def check(iso, results, evidence, commit=""):
    iso=Path(iso)
    if not iso.is_file() or iso.stat().st_size < 50*MIB:
        raise ValueError("A complete experimental ISO file is missing or implausibly small")
    with iso.open("rb") as fh:
        fh.seek(16*2048+1)
        if fh.read(5)!=b"CD001":
            raise ValueError("The build does not contain the expected ISO9660 volume descriptor")
    data=json.loads(Path(results).read_text())
    for memory,required in (("384",REQUIRED_384),("1024",REQUIRED_1024)):
        d=data.get(memory,{})
        missing=[name for name in required if d.get(name) is not True]
        if missing:
            raise ValueError(f"{memory}MiB QEMU evidence did not pass: {missing}")
        serial=Path(evidence)/f"ram_{memory}MiB"/"serial.log"
        if not serial.is_file():
            raise ValueError(f"Missing real guest serial log for {memory}MiB")
        s=serial.read_text(errors="replace")
        if not all(marker in s for marker in EARLY_SIGNALS):
            raise ValueError(f"Missing Linux kernel input-event proof for {memory}MiB")
    h=hashlib.sha256()
    with iso.open("rb") as fh:
        for chunk in iter(lambda:fh.read(1024*1024),b""):
            h.update(chunk)
    size=iso.stat().st_size
    return {
      "schema":"PUPPY50_V62_EXPERIMENTAL_QEMU_ISO",
      "source_commit":commit,
      "iso_filename":iso.name,
      "iso_bytes":size,
      "iso_mib":round(size/MIB,3),
      "sha256":h.hexdigest(),
      "1024mib_offline_script_mouse_keyboard":True,
      "384mib_full_ram_copy_root_switch_and_cd_eject":True,
      "384mib_functional_browser":False,
      "physical_computer_compatibility_proven":False,
      "internet_https_and_general_websites_proven":False,
      "real_hardware_firmware_included":False,
      "software_graphics_only":True,
      "package_database_and_update_security_validated":False,
      "public_release_status":"not_published",
      "warning":"QEMU standard VGA ONLY. No Intel GPU firmware/acceleration, no secure online use, no production, no physical installation. Experimental browser and Linux RAM-root proof only."
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--iso",required=True,type=Path)
    p.add_argument("--results",required=True,type=Path)
    p.add_argument("--evidence",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--commit",default="")
    a=p.parse_args()
    result=check(a.iso,a.results,a.evidence,a.commit)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":
    main()
