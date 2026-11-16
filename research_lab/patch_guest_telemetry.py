#!/usr/bin/env python3
"""Add inert serial timing markers to an extracted research-only initrd."""
import argparse
from pathlib import Path


def patch(root):
    root = Path(root).resolve(strict=True)
    if root == Path("/") or not root.is_dir():
        raise ValueError("refuse to modify host root")
    path = root / "usr/lib/live/boot/9990-main.sh"
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root):
        raise ValueError("expected an extracted initrd boot script")
    src = path.read_text()
    if "P50_V123_BEFORE_PID1" not in src or "P50_TRACE_LAUNCHER_ENTER" in src:
        raise ValueError("unexpected or already instrumented launcher")
    def marker(tag):
        return "printf '" + tag + " %s\\n' \"$(cat /proc/uptime)\" > /dev/ttyS0\n"
    anchors = [
        ('p50_cookie="$(mcookie)"', marker("P50_TRACE_LAUNCHER_ENTER"), marker("P50_TRACE_COOKIE_READY")),
        ('xauth -f /home/user/.Xauthority add :0 . "$p50_cookie"',
         marker("P50_TRACE_XAUTH_BEGIN"), marker("P50_TRACE_XAUTH_READY")),
    ]
    for anchor, before, after in anchors:
        if src.count(anchor) != 1:
            raise ValueError("unexpected or ambiguous launcher anchor")
        src = src.replace(anchor, before + anchor + "\n" + after.rstrip("\n"), 1)
    path.write_text(src)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("extracted_root", type=Path)
    print(patch(parser.parse_args().extracted_root))
