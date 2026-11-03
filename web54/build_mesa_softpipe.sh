#!/bin/sh
# Puppy50 v53: compile software-only Mesa subset using clean Alpine 3.24/musl.
# NOT an installed system image and NOT a hardware/driver benchmark.
set -eu
OUT=/out
mkdir -p "$OUT"
cd /tmp
apk add --no-cache   build-base linux-headers meson ninja python3 py3-mako py3-yaml   py3-packaging py3-setuptools py3-ply bison flex pkgconf   libdrm-dev expat-dev libxml2-dev zlib-dev zstd-dev   libx11-dev libxcb-dev libxext-dev libxfixes-dev libxshmfence-dev   libxrandr-dev libxdamage-dev libxxf86vm-dev xorgproto   elfutils-dev wayland-dev wayland-protocols   > "$OUT/apk-build-deps.log" 2>&1 || {
    echo 'PUPPY50_V53_BUILD_DEPS_FAILED'
    tail -30 "$OUT/apk-build-deps.log"
    exit 10
  }
wget -q -T 60 -O mesa-26.1.6.tar.xz https://archive.mesa3d.org/mesa-26.1.6.tar.xz
echo '5296b88a0f1e012e2cb9ada150a2bbadf728ca81e5a4fb2ab43c83a4d2158606  mesa-26.1.6.tar.xz' | sha256sum -c -
tar -xf mesa-26.1.6.tar.xz
cd mesa-26.1.6
# Attempt a software-only (QEMU baseline) GL build; Crocus has a separate CLC compiler requirement.
# Fail on missing Meson options. Never silently add llvmpipe.
if ! meson setup out   --prefix=/usr   -Dbuildtype=release   -Dgallium-drivers=softpipe   -Dllvm=disabled   -Dplatforms=x11   -Dglx=dri   -Degl=enabled   -Dgbm=enabled   -Dvulkan-drivers=   -Dgallium-rusticl=false   -Dgallium-va=disabled         -Dbuild-tests=false   > "$OUT/meson-setup.log" 2>&1; then
  echo 'PUPPY50_V53_MESON_CONFIGURE_FAILED'
  tail -65 "$OUT/meson-setup.log"
  exit 11
fi
echo 'PUPPY50_V53_MESON_CONFIGURE_PASS'
meson configure out > "$OUT/meson-config.txt"
if ! ninja -C out -j2 > "$OUT/ninja-build.log" 2>&1; then
  echo 'PUPPY50_V53_COMPILE_FAILED'
  tail -65 "$OUT/ninja-build.log"
  exit 12
fi
echo 'PUPPY50_V53_MESA_COMPILE_PASS'
DESTDIR=/tmp/mesa-install ninja -C out install > "$OUT/ninja-install.log" 2>&1
find /tmp/mesa-install -type f \( -name '*.so' -o -name '*.so.*' \) -print > "$OUT/installed-shared-libraries.txt"
if [ ! -s "$OUT/installed-shared-libraries.txt" ]; then
  echo 'PUPPY50_V53_NO_SHARED_LIBRARIES'
  exit 13
fi
# Verify no DT_NEEDED edges to LLVM on any produced ELF; positive evidence
# for an LLVM-less ABI, but never proof the Intel GPU actually renders.
: > "$OUT/llvm-dynamic-links.txt"
while IFS= read -r path; do
  readelf -dW "$path" 2>/dev/null | grep -i 'NEEDED.*llvm' >> "$OUT/llvm-dynamic-links.txt" || :
done < "$OUT/installed-shared-libraries.txt"
test ! -s "$OUT/llvm-dynamic-links.txt" || {
  echo 'PUPPY50_V53_LLVM_DYNAMIC_DEPENDENCY_REMAINS'
  exit 14
}
du -sb /tmp/mesa-install > "$OUT/staged-installed-files-raw-bytes.txt"
find /tmp/mesa-install -type f -size +10M -printf '%s %p\n' | sort -rn | head -30 > "$OUT/largest-binaries.txt"
# Preserve staged program files (including symlinks) so an independently
# audited integration job can actually test the replacement in real QEMU.
tar -C /tmp/mesa-install -czf "$OUT/mesa-softpipe-root.tar.gz" .
(cd "$OUT" && sha256sum mesa-softpipe-root.tar.gz > mesa-softpipe-root.sha256)
tar -tzf "$OUT/mesa-softpipe-root.tar.gz" > "$OUT/mesa-softpipe-root-manifest.txt"
echo "PUPPY50_V53_SOFTPIPE_ARCHIVE_BYTES=$(wc -c < "$OUT/mesa-softpipe-root.tar.gz")"
echo 'PUPPY50_V53_SOFTPIPE_ONLY_LLVMFREE_ABI_PASS_NO_GPU_TEST'
