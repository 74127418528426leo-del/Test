#!/usr/bin/env python3
"""V99: patch a copy of the previously verified Firefox Debian Live root.
No modification of browser, TLS, NetworkManager, or any host operating system.
"""
import argparse,json
from pathlib import Path

ZRAM=r'''#!/bin/sh
# In-memory compressed swap for experimental Live OS: no disk writes.
set -eu
say(){ printf '%s\n' "$1" >/dev/ttyS0 2>/dev/null || true; }
if ! grep -q 'boot=live' /proc/cmdline; then say P50_V99_ZRAM_REFUSED_NONLIVE; exit 30; fi
say P50_V99_ZRAM_START
if ! command -v modprobe >/dev/null 2>&1; then
 say P50_V99_ZRAM_ERROR_MODPROBE_MISSING
 exit 31
fi
if ! modprobe zram num_devices=1; then
 say P50_V99_ZRAM_ERROR_NO_MODULE
 exit 32
fi
i=0
while [ ! -e /sys/block/zram0/disksize ] && [ "$i" -lt 12 ]; do
 i=$((i+1)); sleep 1
done
if [ ! -e /sys/block/zram0/disksize ];then
 say P50_V99_ZRAM_ERROR_NO_DEVICE
 exit 33
fi
if grep -q '^/dev/zram0[[:space:]]' /proc/swaps;then
 say P50_V99_ZRAM_ALREADY_ENABLED
 exit 0
fi
if grep -qw lz4 /sys/block/zram0/comp_algorithm; then
 printf '%s\n' lz4 >/sys/block/zram0/comp_algorithm
 say P50_V99_ZRAM_COMPRESSOR=lz4
else
 say P50_V99_ZRAM_COMPRESSOR=kernel-default
fi
# Logical disk size is NOT physically allocated in advance.
printf '%s\n' 1024M >/sys/block/zram0/disksize
mkswap -L P50_RAM_SWAP /dev/zram0 >/dev/null
swapon -p 100 /dev/zram0
if ! grep -q '^/dev/zram0[[:space:]]' /proc/swaps;then
 say P50_V99_ZRAM_SWAPON_NOT_VERIFIED
 exit 34
fi
say P50_V99_ZRAM_ENABLED=1
say P50_V99_ZRAM_NO_PHYSICAL_DISK=1
'''

TELEMETRY=r'''#!/bin/sh
# Guest-only RAM and browser process telemetry, no credentials or URLs.
set -u
say(){ printf '%s\n' "$1" >/dev/ttyS0 2>/dev/null || true; }
if ! grep -q 'boot=live' /proc/cmdline;then exit 0;fi
n=0
while [ "$n" -lt 19 ];do
 mem="$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)"
 free="$(awk '/^SwapFree:/ {print $2}' /proc/meminfo)"
 total="$(awk '/^SwapTotal:/ {print $2}' /proc/meminfo)"
 swapin="$(awk '/^pswpin / {print $2}' /proc/vmstat)"
 swapout="$(awk '/^pswpout / {print $2}' /proc/vmstat)"
 oom="$(awk '/^oom_kill / {print $2}' /proc/vmstat)"
 zram="unavailable"
 if [ -r /sys/block/zram0/mm_stat ];then
  zram="$(awk '{print "originalBytes="$1",compressedBytes="$2",physicalBytes="$3}' /sys/block/zram0/mm_stat)"
 fi
 psi="missing"
 if [ -r /proc/pressure/memory ];then
  psi="$(awk 'NR==1 {for (i=1;i<=NF;i++)if($i~/^avg10=/){print $i;exit}}' /proc/pressure/memory)"
 fi
 ffcount=0
 if id user >/dev/null 2>&1;then
  ffcount="$(pgrep -u user -f '[f]irefox' | wc -l)" || ffcount=0
 fi
 say "P50_V99_RAM_SAMPLE step=$n availableKiB=$mem swapFreeKiB=$free swapTotalKiB=$total pswpin=$swapin pswpout=$swapout oomKill=$oom firefoxPids=$ffcount psi=$psi zram:$zram"
 n=$((n+1))
 sleep 15
done
'''

ZRAM_UNIT="""[Unit]
Description=Puppy50 Experimental In-RAM Compressed Swap
Documentation=https://docs.kernel.org/admin-guide/blockdev/zram.html
After=local-fs.target
Before=lightdm.service

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/puppy50-zram-live
RemainAfterExit=yes
NoNewPrivileges=false

[Install]
WantedBy=multi-user.target
"""
DIAG_UNIT="""[Unit]
Description=Puppy50 Live RAM Pressure and Compressed Swap Diagnostics
After=lightdm.service

[Service]
Type=simple
ExecStart=/usr/local/sbin/puppy50-memory-diagnostics
User=root
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
"""
LIGHTDM_DROP="""[Unit]
Wants=puppy50-zram-live.service
After=puppy50-zram-live.service
"""

def write(root,relative,data,mode=0o644):
    p=root/relative
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(data)
    p.chmod(mode)

def patch(root):
    root=Path(root).resolve(strict=True)
    if root==Path("/") or not root.is_dir():raise ValueError("Refusing running host root")
    expected=["usr/bin/firefox-esr","usr/sbin/lightdm",
              "etc/systemd/system/lightdm.service.d/10-puppy50-live-preflight.conf",
              "usr/local/sbin/puppy50-prepare-session",
              "usr/local/sbin/puppy50-network-probe",
              "etc/ssl/certs/ca-certificates.crt"]
    missing=[name for name in expected if not (root/name).is_file()]
    if missing:raise ValueError("Cannot identify intact v91 Live root: "+repr(missing))
    if "P50_V91_LIGHTDM_AUTOLOGIN_PREPARED" not in (root/expected[3]).read_text():
        raise ValueError("Unexpected prior Live preflight")
    write(root,"usr/local/sbin/puppy50-zram-live",ZRAM,0o755)
    write(root,"usr/local/sbin/puppy50-memory-diagnostics",TELEMETRY,0o755)
    write(root,"etc/systemd/system/puppy50-zram-live.service",ZRAM_UNIT)
    write(root,"etc/systemd/system/puppy50-memory-diagnostics.service",DIAG_UNIT)
    write(root,"etc/systemd/system/lightdm.service.d/15-puppy50-zram-before-browser.conf",LIGHTDM_DROP)
    return {"schema":"PUPPY50_V99_EXPERIMENTAL_ZRAM_ISO",
       "root_unchanged_except_service_scripts":True,
       "guaranteed_swap_enabled":False,
       "guest_proof_required":True,
       "physical_disk_swap_created":False,
       "browser_or_TLS_policies_modified":False,
       "zram_logical_swap_mib":1024,
       "must_measure_2048Mib_guest":True}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("root",type=Path)
    args=p.parse_args()
    print(json.dumps(patch(args.root),indent=2))
