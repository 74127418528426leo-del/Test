"""Host-clock observations for the disposable QEMU screenshot harness.

The detector recognizes a particular rendered home page, not the first
possible Firefox chrome frame. The bracket records observations; it cannot
recover an unobserved transient frame or align guest and host clocks.
"""
import math
import time


def _upper(seconds):
    # Round toward the conservative side of the strict five-second boundary.
    return math.ceil(seconds * 1_000_000) / 1_000_000


def probe_frame(capture, monitor, out, name, started, result, clock=time.monotonic):
    before = clock() - started
    visible = capture(monitor, out, name)
    after = clock() - started
    event = {"capture_start_seconds": math.floor(before * 1_000_000) / 1_000_000,
             "capture_end_seconds": _upper(after), "home_page_visible": bool(visible)}
    trace = result.setdefault("frame_probe_trace", [])
    trace.append(event)
    if visible:
        previous = next((p for p in reversed(trace[:-1]) if not p["home_page_visible"]), None)
        result["home_frame_observation"] = {
            "last_nonmatching_probe_start_seconds": previous["capture_start_seconds"] if previous else None,
            "first_matching_probe_end_seconds": event["capture_end_seconds"],
            "meaning": "host-monotonic screenshot observations of rendered home page; not exact first Firefox paint",
        }
    return visible


def observe_markers(serial_text, result, markers, now, started):
    """Record when the host first observed a serial marker, not guest uptime."""
    observed = result.setdefault("serial_marker_first_seen_seconds", {})
    for marker in markers:
        if marker in serial_text and marker not in observed:
            observed[marker] = _upper(now - started)
