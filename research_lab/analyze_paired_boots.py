#!/usr/bin/env python3
"""Summarize paired QEMU evidence without mixing guest and host clocks."""
import argparse
import json
import math
import re
from pathlib import Path
from statistics import median


GUEST_MARKERS = {
    "drm_ready": "P50_V125_EARLY_DRM_READY",
    "launch_request": "P50_V123_INITRD_LAUNCH_REQUEST",
    "launcher_enter": "P50_TRACE_LAUNCHER_ENTER",
    "cookie_ready": "P50_TRACE_COOKIE_READY",
    "cookie_bg_start": "P50_TRACE_COOKIE_BG_START",
    "cookie_bg_ready": "P50_TRACE_COOKIE_BG_READY",
    "xauth_begin": "P50_TRACE_XAUTH_BEGIN",
    "xauth_ready": "P50_TRACE_XAUTH_READY",
    "xorg_start": "P50_V123_XORG_START",
    "firefox_exec": "P50_V127_FIREFOX_DIRECT_EXEC",
}
MATCHED_CONFIGURATION = ("guest_ram_mib", "virtual_cpu_model", "virtual_media",
                         "network_mode", "virtual_read_cap_bytes_per_second")


def number(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError("invalid timestamp")
    return float(value)


def summarize_boot(root, label):
    p = root / label
    result = json.loads((p / "result.json").read_text())
    if (result.get("errors") or result.get("media_ejected") is not True or
            result.get("post_eject_browser_http200_confirmed") is not True or
            result.get("input_sent_after_eject") is not True or
            result.get("qemu_running_at_end") is not True or
            number(result.get("staged_ram_ready_seconds")) <= 0):
        raise ValueError(label + ": missing successful functional observations")
    if any(key not in result for key in MATCHED_CONFIGURATION):
        raise ValueError(label + ": missing VM configuration")
    host = result.get("serial_marker_first_seen_seconds", {})
    home = number(result["home_frame_observation"]["first_matching_probe_end_seconds"])
    receipt_raw = host.get("P50_V127_FIREFOX_DIRECT_EXEC")
    receipt = number(receipt_raw) if receipt_raw is not None else None
    serial = (p / "serial.log").read_text(errors="replace")
    if any(marker not in serial for marker in ("P50_STAGE_COPY_VERIFIED", "P50_STAGE_READY",
                                                "P50_V127_FIREFOX_DIRECT_EXEC")):
        raise ValueError(label + ": missing RAM verification or Firefox execution evidence")
    guest = {}
    for key, tag in GUEST_MARKERS.items():
        hits = re.findall(r"^" + re.escape(tag) + r"\s+(\d+(?:\.\d+)?)\b", serial, re.M)
        if len(hits) == 1:
            guest[key] = float(hits[0])
    guest_deltas = {}
    for name, begin, end in (
        ("drm_ready_to_xorg", "drm_ready", "xorg_start"),
        ("launch_request_to_launcher_enter", "launch_request", "launcher_enter"),
        ("launcher_enter_to_cookie_ready", "launcher_enter", "cookie_ready"),
        ("background_cookie_generation", "cookie_bg_start", "cookie_bg_ready"),
        ("xauth_begin_to_ready", "xauth_begin", "xauth_ready"),
        ("xorg_to_firefox_exec", "xorg_start", "firefox_exec"),
    ):
        if begin in guest and end in guest and guest[end] >= guest[begin]:
            guest_deltas[name] = round(guest[end] - guest[begin], 4)
    return {
        "firmware": result.get("virtual_firmware"),
        "guest_ram_mib": result.get("guest_ram_mib"),
        "vm_configuration": {key:result[key] for key in MATCHED_CONFIGURATION},
        "sampled_home_observation_upper_seconds": home,
        "host_firefox_exec_receipt_seconds": receipt,
        # A marker may be emitted before the frame but first read by the host
        # during the later RAM polling loop. Its receipt is not event order.
        "host_exec_receipt_to_home_observation_seconds": round(home - receipt, 6) if receipt is not None and receipt <= home else None,
        "guest_uptime_markers_seconds": guest,
        "guest_only_stage_deltas_seconds": guest_deltas,
        "host_serial_marker_receipts_seconds": host,
        "home_frame_observation": result["home_frame_observation"],
    }


def analyze(root, labels):
    root = Path(root)
    pairs = []
    for label in labels:
        if not re.fullmatch(r"(?:bios|uefi)[1-9][0-9]*", label):
            raise ValueError("invalid boot label")
        candidate = summarize_boot(root, label)
        control = summarize_boot(root, "matched_" + label)
        expected = re.sub(r"[0-9]+$", "", label)
        if candidate["firmware"] != expected or control["firmware"] != expected:
            raise ValueError(label + ": firmware mismatch")
        if candidate["vm_configuration"] != control["vm_configuration"]:
            raise ValueError(label + ": machine configuration mismatch")
        pairs.append({"label":label, "candidate":candidate, "control":control,
                      "control_minus_candidate_seconds":round(
                          control["sampled_home_observation_upper_seconds"] -
                          candidate["sampled_home_observation_upper_seconds"], 6)})
    by_firmware = {}
    for fw in ("bios", "uefi"):
        group = [p for p in pairs if p["candidate"]["firmware"] == fw]
        if group:
            diffs = [p["control_minus_candidate_seconds"] for p in group]
            by_firmware[fw] = {"pairs":len(group), "median_control_minus_candidate_seconds":median(diffs),
                               "min_seconds":min(diffs), "max_seconds":max(diffs)}
    return {"scope":"diagnostic QEMU pairing recorded by one workflow job; provenance is not independently attested",
            "pairs":pairs, "firmware_comparison":by_firmware,
            "timing_note":"Host receipt-to-screenshot differences use host monotonic time; "
                          "guest stage differences use guest uptime only. Both are sampled observations, "
                          "not exact first paint or proof of a cause.",
            "five_second_goal_verified":False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--labels", nargs="+", required=True)
    args = parser.parse_args()
    report = analyze(args.source, args.labels)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["firmware_comparison"], indent=2))
