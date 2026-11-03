# Puppy50 v78 — Complete APK-managed QEMU RAM-root experiment

## Goal and provenance

Build a new QEMU-only, RAM-resident Firefox environment from the exact v76 stock-Mesa experimental ISO, keeping its already-tested **kernel and early RAM disk byte-identical**.

The original public v70 image contained 247 package records, eight Mesa digest mismatches, five unowned development aliases, and 4,327 package-recorded files intentionally removed without updating the package manager. The v76 stock-Mesa experiment fixed the existing-file digest/ownership mismatches, but did not repair the 4,327 missing installed-file records. The v77 full audit identified their owners: five kernel/firmware packages and llvm22-libs.

The v78 build changes ONLY a disposable staging copy of the v76 compressed filesystem:

1. Use actual signed Alpine 3.24 repositories and `apk del` to unregister **QEMU-unused installed linux-lts and firmware packages** from the RAM-root. The same required QEMU kernel and e1000/evdev/PS2 modules remain in the initial RAM disk copied from v76.
2. Use `apk fix --reinstall llvm22-libs` to restore `libLLVM.so.22.1`, which upstream Mesa Gallium declares as a `DT_NEEDED` dependency.
3. Require **0 missing APK-recorded paths, 0 scanned shared-library digest mismatches, 0 unowned shared libraries and the actual LLVM runtime present**.
4. Recompress with XZ; build an entirely separate ISO with unchanged kernel and initrd and verify all image-file bytes after ISO assembly.
5. Boot the exact new ISO in real 1024MiB KVM, copy it completely into RAM, eject its virtual CD, and verify the actual Firefox homepage, mouse input, guest DHCP/DNS, public TLS certificate check and real Wikipedia page transition.
6. Preserve screenshots, APK logs, full manifest results and size comparison. A green job alone is not evidence of fully secure browsing: inspect the real webpage and independently assess browser sandbox, software updates and CVEs.

**Workflow:** https://github.com/74127418528426leo-del/Test/actions/workflows/puppy50-v78-apk-complete-qemu.yml

## What this means for "any network"

This QEMU-only runtime has an emulated e1000 virtual Ethernet card and uses the host's authorized Wi-Fi, wired Ethernet or phone-hotspot connection through QEMU NAT and a restricted TLS-preserving host bridge. It has NO physical Wi-Fi chipset support, wireless SSID selection, local VPN management, captive portal bypass, enterprise Wi-Fi authentication or guarantee of reaching all websites/networks.

The missing kernel/firmware records are removed *because they are unused in the VM*, not because they are unnecessary on physical computers. A future hardware-oriented ISO must package the required NIC/Wi-Fi drivers, firmware and network GUI and pass real-device tests rather than inherit this stripped VM filesystem.

## Safety and limits

Experimental, not a physical OS installer. Do not overwrite the host's Xubuntu installation. Do not use confidential credentials while browser patching, sandbox hardening and vulnerability maintenance remain unverified. 384 MiB boot-only success remains a separate research track; functional modern Firefox was proven at 1024 MiB.

**No public release should claim "all networks" or "complete security" based solely on this VM test.**