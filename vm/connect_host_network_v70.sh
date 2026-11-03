#!/usr/bin/env bash
# Optional, explicit user-initiated HOST connection assistant for Puppy50 QEMU.
# This does not run automatically and never bypasses Wi-Fi authentication.
# Firefox's guest uses whichever authorized host network is connected.
set -euo pipefail
command -v nmcli >/dev/null || {
  echo "NetworkManager CLI is unavailable; connect your host in its normal network settings." >&2
  exit 2
}
echo "Active host network links:"
nmcli -f DEVICE,TYPE,STATE device status || true
echo
echo "Available wireless networks (when a host Wi-Fi device exists):"
nmcli -f IN-USE,SSID,SIGNAL,SECURITY device wifi list || true
echo
echo "Only join networks that you own or are authorized to access."
echo "NetworkManager may save an authorized network profile on your HOST computer."
read -r -p "Enter an authorized Wi-Fi SSID to join, or press Enter to cancel: " ssid
if [[ -z "$ssid" ]]; then
  echo "No network changes made."
  exit 0
fi
if [[ "$ssid" == -* ]]; then
  echo "Invalid SSID argument prefix." >&2
  exit 3
fi
echo "NetworkManager will handle any password/certificate prompts."
# nmcli --ask prompts for authorized Wi-Fi credentials itself. The script
# never handles, echoes or writes passwords and cannot bypass a captive portal.
nmcli --ask device wifi connect "$ssid"
echo "Host connection attempt complete. Test your host's internet before starting Puppy50."
