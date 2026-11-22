"""Assemble a release from matched and independent measurements of one ISO."""
from pathlib import Path
import argparse
import hashlib
import json
from statistics import mean


def span(rows, key):
    values = [item[key] for item in rows]
    return f'{min(values):.2f}–{max(values):.2f} s'


def frame_table(label, rows):
    values = [row['first_home_seen_seconds'] for row in rows]
    first = sum(row['early_navigation_attempts'] == 1 for row in rows)
    return (f'| {label} | {span(rows, "first_home_seen_seconds")} | {mean(values):.2f} s | '
            f'{span(rows, "early_js_response_seconds")} | {first}/{len(rows)} | '
            f'{span(rows, "staged_ram_ready_seconds")} |')


def data(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--source-sha', required=True)
    parser.add_argument('--matched', required=True)
    parser.add_argument('--independent', required=True)
    parser.add_argument('--sha', required=True)
    args = parser.parse_args()
    assets = Path('assets')
    iso = assets / 'Puppy50_Fast_VirtIO_BIOS_Preview.iso'
    with iso.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != args.sha:
            raise ValueError('The selected ISO differs from the tested image')
    matched_root = Path('evidence/matched')
    indep_root = Path('evidence/independent')
    matched = data(matched_root / 'reports/comparison.json')
    independent = data(indep_root / 'reports/independent.json')
    direct_root = Path('evidence/direct')
    direct = data(direct_root / 'reports/comparison.json')
    pair = matched['samples']
    reps = independent['samples']
    if independent['candidate_sha256'] != args.sha or not independent['all_verified']:
        raise ValueError('Independent checks or ISO digest failed')
    for folder in (matched_root, direct_root, indep_root):
        if f'{args.sha}  tuned.iso' not in (folder / 'reports/iso-sha256.txt').read_text().splitlines():
            raise ValueError('The distributed ISO differs from the bytes used in one of the experiments')
    if matched['route'] != 'bios' or direct['route'] != 'direct':
        raise ValueError('Unexpected boot entry in an evidence archive')
    if not all(row['functional_ok'] for row in direct['samples'].values()):
        raise ValueError('At least one direct-kernel boot failed')
    if not all(row['functional_ok'] for row in pair.values()) or not all(row['verified'] for row in reps.values()):
        raise ValueError('At least one required guest boot failed')
    def select(rows, prefix):
        return [rows[k] for k in sorted(rows) if k.startswith(prefix)]
    matched_preview = select(pair, 'four')
    repeated_preview = select(reps, 'repeat')
    if len(matched_preview) != 3 or len(repeated_preview) != 3:
        raise ValueError('Six complete conservative VirtIO BIOS cold boots are required')
    if any(x['early_navigation_attempts'] != 1 for x in matched_preview + repeated_preview):
        raise ValueError('At least one conservative VirtIO boot needed a second navigation attempt')
    base_url = f'https://github.com/{args.repo}'
    lines = [
        '# Puppy50 Fast VirtIO BIOS Preview',
        '',
        'Puppy50 opens Firefox ESR directly from a live ISO. The tested fast entry starts the display driver and, when present, the VirtIO random-device driver during early Linux startup. Firefox runs as the live user. The ISO also contains the standard firmware and graphics boot entries.',
        '',
        '## Downloads',
        '',
        'Use `Puppy50_Fast_VirtIO_BIOS_Preview.iso` to boot. `SHA256SUMS` covers every distributed asset. The evidence archive contains all 26 boots from the matched BIOS, direct-kernel and independent verification runs, including screenshots, serial logs, real Firefox interaction results and a separately recorded HTTP receipt for each boot.',
        '',
        '## Verified cold boots',
        '',
        '| Configuration | Firefox visible | Mean visible | Keyboard and JavaScript test complete | First attempt worked | Verified RAM ready |',
        '| --- | ---: | ---: | ---: | ---: | ---: |',
        frame_table('Matched BIOS control, two vCPUs and VirtIO RNG', select(pair, 'control')),
        frame_table('Matched BIOS preview, two vCPUs and VirtIO RNG', select(pair, 'tuned')),
        frame_table('Matched BIOS preview, four vCPUs and VirtIO RNG', matched_preview),
        frame_table('Independent BIOS, four vCPUs and VirtIO RNG', repeated_preview),
        frame_table('Independent BIOS, four vCPUs and host CPU features', select(reps, 'native')),
        frame_table('BIOS preview without the optional RNG device', select(pair, 'plain')),
        frame_table('UEFI fallback', [reps['uefi1']]),
        frame_table('Alternate graphics fallback', [reps['graphics1']]),
        frame_table('Standard BIOS fallback', [reps['standard1']]),
        '',
        f"The separate direct-kernel trial loads the kernel and initrd from this same ISO using QEMU. With two vCPUs its three Firefox first frames were {span(select(direct['samples'], 'tuned'), 'first_home_seen_seconds')}. Ordinary ISO users boot through firmware. The BIOS rows above use that route.",
        '',
        'The timer starts before each new QEMU process launches and stops when the Puppy50 home page appears in an actual Firefox window. Every boot starts with a fresh guest. The tests request eviction of host ISO page-cache entries before each run. The interaction test types an address, loads a page and triggers JavaScript with keyboard input. Its timing includes those actions.',
        '',
        'After each boot, the guest verifies the complete root filesystem copy in RAM. The test ejects the virtual boot medium and requires a new browser request with a unique identifier and a matching HTTP 200 response. Timings vary by runner and hardware. The one-second cold-boot target remains open. Physical Acer startup times have yet to be measured.',
        '',
        '## Boot the tested VM configuration',
        '',
        'On a Linux host with QEMU, hardware virtualization and KVM access, run this command from the download directory. The default BIOS entry opens Firefox automatically. No installation or virtual hard disk is required.',
        '',
        '```sh',
        'qemu-system-x86_64 -machine pc,accel=kvm -m 3072 -smp 4 ' + chr(92),
        "  -cpu 'Westmere,-aes,-pclmulqdq,-x2apic,-3dnowprefetch' -vga std " + chr(92),
        '  -drive if=none,id=livecd,media=cdrom,readonly=on,format=raw,file=Puppy50_Fast_VirtIO_BIOS_Preview.iso ' + chr(92),
        '  -device virtio-scsi-pci,id=p50scsi -device scsi-cd,drive=livecd,bus=p50scsi.0,bootindex=1 ' + chr(92),
        '  -object rng-random,id=p50rng,filename=/dev/urandom -device virtio-rng-pci,rng=p50rng ' + chr(92),
        '  -nic user,model=e1000,ipv6=off',
        '```',
        '',
        'The primary four-vCPU results and the two-vCPU control use a conservative Westmere feature mask and 3 GiB of guest RAM. The four-vCPU BIOS configuration accepted the first keyboard navigation in all six trials across two runners. Two-vCPU timing and navigation counts are listed separately in the table. Host CPU speed, virtual storage and firmware affect VM performance. The physical-machine entry uses the standard boot path. Keep physical media connected during use.',
        '',
        f'[Matched boot evidence]({base_url}/actions/runs/{args.matched}) · [Independent verification]({base_url}/actions/runs/{args.independent}) · [Build source]({base_url}/tree/{args.source_sha}/puppy50-boot) · [General preview and Debian source archives]({base_url}/releases/tag/puppy50-browser-live-public-preview-20261114)',
    ]
    (assets / 'README.md').write_text('\n'.join(lines) + '\n')
    (assets / 'MATCHED_RESULTS.json').write_text(json.dumps(matched, indent=2) + '\n')
    (assets / 'DIRECT_KERNEL_RESULTS.json').write_text(json.dumps(direct, indent=2) + '\n')
    (assets / 'INDEPENDENT_RESULTS.json').write_text(json.dumps(independent, indent=2) + '\n')


if __name__ == '__main__':
    main()
