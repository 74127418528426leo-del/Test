#!/usr/bin/env python3
"""Stage a real network-enabled browser launcher after standard Puppy50 config.

No edits to the user's Xubuntu host, no TLS bypass or Firefox sandbox changes.
"""
import argparse
from pathlib import Path

START="echo 'PUPPY50_WEB_V45_XORG_START' > /dev/ttyS0 2>/dev/null || true"
BLOCK="""# DHCP/DNS/verified-HTTPS smoke test. Failed networks must not prevent
# opening the browser so the user can use local pages and captive portals.
echo 'PUPPY50_V64_BROWSER_NETWORK_TEST_REQUESTED' > /dev/ttyS0 2>/dev/null || true
/usr/local/bin/puppy50-network-probe > /dev/ttyS0 2>&1 || true
"""
def patch(root):
    root=Path(root)
    launch=root/"usr/local/bin/puppy50-web-launch"
    probe=root/"usr/local/bin/puppy50-network-probe"
    html=root/"usr/share/puppy50web/index.html"
    source=Path(__file__).with_name("network_probe.sh")
    if not launch.is_file() or not html.is_file():
        raise ValueError("Expected staged browser launch and HTML page")
    if not (root/"usr/bin/curl").exists():
        raise ValueError("HTTPS test requires actual curl package in staged system")
    text=launch.read_text()
    if text.count(START)!=1:
        raise ValueError("Xorg launch anchor must appear exactly once")
    if "PUPPY50_V64_BROWSER_NETWORK_TEST_REQUESTED" in text:
        raise ValueError("Network injection must not run twice")
    launch.write_text(text.replace(START,BLOCK+START))
    data=source.read_bytes()
    probe.parent.mkdir(parents=True,exist_ok=True)
    probe.write_bytes(data)
    probe.chmod(0o755)
    page=html.read_text()
    marker="The normal Firefox address bar, tabs and downloads remain available."
    if marker not in page:
        raise ValueError("Offline browser page must retain normal navigation guidance")
    page=page.replace(marker,marker+
        " In the online QEMU edition, type HTTPS addresses in the Firefox address bar; "
        "the virtual Ethernet connection is configured automatically by DHCP.")
    html.write_text(page)
    return {"network_script_bytes":len(data),"qemu_nat_only":True,
            "firefox_sandbox_unchanged":True,"curl_certificate_check_enabled":True}
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root",type=Path)
    args=ap.parse_args()
    print("PUPPY50_V64_STAGED_ONLINE_BROWSER",patch(args.root))
if __name__=="__main__":main()
