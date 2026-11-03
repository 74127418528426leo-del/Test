# Puppy50 v80 — Resilient host-network bridge add-on for the published v70 ISO

**Experimental add-on, not a new ISO.** The published v70 remains byte-for-byte unchanged and still boots Firefox at 1024 MiB in QEMU.

This improves a concrete reliability issue in the v70 Linux launcher: the HTTPS CONNECT bridge is started once and is not restarted if its process crashes. The new `host_https_bridge_supervisor_v80.py` monitors only **the bridge child that it spawned**, restarting that child when necessary with a bounded crash-loop limit. It does not restart QEMU, copy files to the guest, or modify the operating system.

## Install over the existing v70 complete VM bundle

Place these three files beside your extracted `Puppy50_Web_v70_Normal_Browser_Online.iso` and its existing `SHA256SUMS`:

- `launch_linux_v80.sh`
- `host_https_bridge_supervisor_v80.py`
- `host_https_bridge.py` (the same existing restricted host bridge from v70)

Run using your **already authorized** Wi-Fi, Ethernet or hotspot connection on your host:

```bash
sudo apt-get install qemu-system-x86 python3
bash launch_linux_v80.sh
```

The script verifies the original ISO SHA-256 before booting and refuses an unknown service already using `127.0.0.1:3128`. It starts one unprivileged Python supervisor, which starts the host-only HTTPS CONNECT bridge. HTTPS certificates are still validated in Firefox inside the guest; the bridge only forwards encrypted TLS bytes to public destinations on approved ports. No guest hard disk is attached. Session changes disappear at shutdown.

When the host changes Internet networks, the next *new* outbound connection can use the host's new route subject to its policies. The supervisor also repairs an unexpected **bridge process crash** automatically, but cannot restore the host's Wi-Fi, bypass a captive portal or force access to a blocked destination.

## What it does NOT establish

- No actual physical SSID roaming has been verified. The guest has an emulated e1000 Ethernet interface and does not select Wi-Fi networks.
- A long-lived HTTPS connection may break on host network change. Firefox may require a page reload to establish new sockets.
- The security lifecycle of Firefox and the stripped Linux filesystem is not yet certified. Do **not** use passwords, financial sites or sensitive accounts with this experimental browser.
- It cannot work around firewalls, restricted enterprise proxy authentication or the host lacking permission to join a network.
- Only the host-side bridge recovery is improved; the 384 MiB functional Firefox target is not achieved.

## Testing and acceptance

The CI regression tests intentionally kill the supervised bridge child, confirm that its process ID changes, and verify that the new local TCP listener works. They also verify the original ISO SHA validation, immutable read-only CD boot, and no unknown process port adoption.

The prior v75 KVM test already verified that Firefox can open Wikipedia after a real host-side HTTPS bridge interruption and restart. This new add-on automates that recovery on the host; a dedicated long-running VM integration test will be necessary before claiming complete end-to-end recovery under every network failure.

Sources: [v75 genuine KVM recovery proof](https://github.com/74127418528426leo-del/Test/actions/runs/41674232157) and [v70 public ISO](https://github.com/74127418528426leo-del/Test/releases/tag/puppy50-qemu-normal-v70).
