#!/usr/bin/env python3
"""Instrument the pinned disposable QEMU harness; never modify guest OS files."""
import argparse
import ast
from pathlib import Path


def patch_text(src):
    if "post_eject_browser_http200_confirmed" not in src or "p50_measurement_probe" in src:
        raise ValueError("requires uninstrumented, HTTP-verified AHCI harness")
    replacements = [
        ("from PIL import Image\n", "from PIL import Image\nfrom p50_measurement_probe import probe_frame, observe_markers\n"),
        ("'virtual_firmware': args.firmware, 'virtual_media': args.media,",
         "'virtual_firmware': args.firmware, 'virtual_media': 'ahci-cd',"),
        ("    with (out / 'qemu.log').open('wb') as log:\n",
         "    markers += ['BdsDxe: loading Boot', 'BdsDxe: starting Boot',\n"
         "                'P50_V118_EARLY_USER_READY', 'P50_V125_DRM_GATE_START',\n"
         "                'P50_V125_EARLY_DRM_READY', 'P50_V123_INITRD_LAUNCH_REQUEST',\n"
         "                'P50_TRACE_LAUNCHER_ENTER', 'P50_TRACE_COOKIE_READY',\n"
         "                'P50_TRACE_COOKIE_BG_START', 'P50_TRACE_COOKIE_BG_READY',\n"
         "                'P50_TRACE_COOKIE_BG_GENERATED', 'P50_TRACE_COOKIE_BG_FAILED',\n"
         "                'P50_TRACE_COOKIE_WAIT_FAILED', 'P50_TRACE_COOKIE_WAIT_TIMEOUT',\n"
         "                'P50_TRACE_XAUTH_BEGIN', 'P50_TRACE_XAUTH_READY',\n"
         "                'P50_V123_XORG_START', 'P50_V127_FIREFOX_DIRECT_EXEC',\n"
         "                'P50_STAGE_COPY_VERIFIED', 'P50_STAGE_READY']\n"
         "    with (out / 'qemu.log').open('wb') as log:\n"),
        ("                    for marker in markers:\n"
         "                        if marker in serial_text and marker not in result['serial_marker_first_seen_seconds']:\n"
         "                            result['serial_marker_first_seen_seconds'][marker] = round(elapsed, 2)\n",
         "                    observe_markers(serial_text, result, markers, time.monotonic(), started)\n"),
        ("                        visible = capture(monitor, out, name)\n",
         "                        visible = probe_frame(capture, monitor, out, name, started, result)\n"),
        ("                            result['first_home_seen_seconds'] = round(time.monotonic() - started, 2)\n"
         "                            capture(monitor, out, 'first_home.png')\n",
         "                            result['first_home_seen_seconds'] = round(result['home_frame_observation']['first_matching_probe_end_seconds'], 2)\n"
         "                            with Image.open(out / 'current.ppm') as detected_frame:\n"
         "                                detected_frame.load()\n"
         "                                detected_frame.save(out / 'first_home.png', 'PNG', optimize=True)\n"),
        ("                        state = migration_status(serial.read_text(errors='replace') if serial.exists() else '')\n",
         "                        serial_text = serial.read_text(errors='replace') if serial.exists() else ''\n"
         "                        observe_markers(serial_text, result, markers, time.monotonic(), started)\n"
         "                        state = migration_status(serial_text)\n"),
        ("                    if result['post_eject_browser_http200_confirmed'] or args.mode != 'online':\n"
         "                        break\n",
         "                    if result['post_eject_browser_http200_confirmed'] or args.mode != 'online':\n"
         "                        break\n"
         "                    try:\n"
         "                        failed_name = f'failed_navigation_{attempt}.png'\n"
         "                        capture(monitor, out, failed_name)\n"
         "                        result['screenshots'].append(failed_name)\n"
         "                    except Exception as exc:\n"
         "                        result['errors'].append('failed-navigation screenshot: ' + repr(exc))\n"),
    ]
    for old, new in replacements:
        if src.count(old) != 1:
            raise ValueError("unknown or ambiguous harness anchor: " + old[:70])
        src = src.replace(old, new, 1)
    ast.parse(src)
    return src


def patch(path):
    path = Path(path).resolve(strict=True)
    if not path.is_file() or path.name != "boot_bench_ahci.py":
        raise ValueError("only the disposable generated AHCI benchmark may be patched")
    path.write_text(patch_text(path.read_text()))
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("benchmark", type=Path)
    print(patch(parser.parse_args().benchmark))
