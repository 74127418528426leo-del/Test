"""Create equivalent firmware and direct-entry measurements for the exact ISO files."""
import argparse
from pathlib import Path
from boot_latency_lab import AHCI, VIRTIO, prepare_harness
from repack import replace_once


def make_drivers(source, boot, route, variant):
    prepare_harness(source, boot)
    template = source.with_name('boot_bench_lab_virtio.py' if route == 'bios' else 'boot_bench_lab_direct.py')
    base = template.read_text()
    if route == 'direct':
        base = replace_once(base, AHCI, VIRTIO)
    rng = "cmd += ['-object', 'rng-random,id=p50rng,filename=/dev/urandom', '-device', 'virtio-rng-pci,rng=p50rng']"
    with_rng = replace_once(base, VIRTIO, VIRTIO + '\n        ' + rng)
    four = replace_once(with_rng, "'-smp', '2',", "'-smp', '4',")
    for profile, code in (('plain', base), ('two', with_rng), ('four', four)):
        path = source.with_name(f'boot_bench_{variant}_{profile}.py')
        compile(code, str(path), 'exec')
        path.write_text(code)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('boot', type=Path)
    parser.add_argument('route', choices=['bios', 'direct'])
    parser.add_argument('variant', choices=['control', 'tuned'])
    opts = parser.parse_args()
    make_drivers(**vars(opts))
