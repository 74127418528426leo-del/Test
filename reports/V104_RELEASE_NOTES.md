# Puppy50 v104 — experimental Intel Firefox Live with media libraries

This is an experimental browser-focused Debian Live image, not an official Puppy Linux release and not a production-certified operating system. It is intended for Intel graphics; AMD and NVIDIA graphics firmware were removed in the earlier Intel-specific build.

## Changes and size

- This ISO is **733.31 MiB**. The v103 browser-only image was 706.31 MiB; the additional media packages add approximately **27 MiB** to the ISO.
- Added the Debian `libavcodec61` package and 29 dependencies to investigate H.264 video support. The package transaction recorded zero upgrades and zero removals. Adding decoders expands the media-processing code present in the image and is not a security certification.
- In the preceding v103 image, unused system translation directories were removed while existing English and Spanish gettext catalogs were retained. This does not establish that a Spanish desktop or Firefox interface is available.
- The compressed RAM-loaded system is **594.83 MiB**. The 384 MiB entire-system target and the earlier 50 MiB ISO target are **not met**.

## What was tested

At 2,048 and 2,560 MiB allocated guest RAM, one trial at each size ejected the virtual boot disc. The guest heartbeat continued, Firefox loaded a unique local test page, and then displayed an external HTTPS page with a new URL. The initial keyboard input in the 2,048 MiB run lost characters, so one successful later navigation does not establish a reliable minimum. These are virtual-machine results.

At 4,096 MiB, a controlled 640×360 H.264 test clip without audio failed to decode on v103 but played on v104; reviewed video frames advanced from approximately 31 to 54 seconds. This demonstrates playback of that clip in the VM, not 4K playback, audio, smoothness, or performance on the Acer.

The requested Pexels page presented a human-verification challenge during the v104 automated test, so its video and 4K playback were not tested. In an earlier v103 trial the page loaded but reported an unsupported media source. The challenge was not bypassed.

The post-repack audit compared 4,628 protected entries between v103 and v104, including firmware files and symlink targets; selected Firefox, NetworkManager and certificate paths; selected NSS/TLS libraries; and `/dev`, `/proc`, `/sys` and the resolver file. It compared content, ownership, mode, symlink target and extended attributes for those paths. This is not a full operating-system security audit.

Tests used QEMU/KVM with an emulated wired adapter and no physical disk swap. This does not establish compatibility with physical Wi-Fi devices, UEFI firmware, USB boot, the Acer computer, every website, or every network. The built-in local homepage includes historical wording written before external-site testing; this document and the linked evidence contain the current results.

## Using the image

Download the ISO and check it against `SHA256SUMS`. Write it to a spare USB drive using a trusted disk-image writer; writing the image erases the selected USB drive. Boot the live session from the USB without installing over the existing system. On supported hardware, choose your authorized wired or Wi-Fi connection using the network icon, enter any requested password normally, and open Firefox.

This experimental release has not had an independent security audit; avoid sensitive credentials, banking, medical sessions and confidential data until its security and update behavior have been verified. RAM-only session changes generally disappear at shutdown unless saved externally.

The real VM checks used the computer's existing network through QEMU. Physical Wi-Fi, captive portals, enterprise authentication, IPv6-only networks, VPNs and tethering remain unverified. No operating system can guarantee access to every network or device.

## Reproduction and evidence

- Exact v104 image build: https://github.com/74127418528426leo-del/Test/actions/runs/42325281517
- v104 filesystem comparison and guest tests: https://github.com/74127418528426leo-del/Test/actions/runs/42325761511
- Additional v104 CNN, YouTube, and Bible site trials: https://github.com/74127418528426leo-del/Test/actions/runs/42326668886
- v103 CNN and Bible site trials: https://github.com/74127418528426leo-del/Test/actions/runs/42322593275
- Source: https://github.com/74127418528426leo-del/Test/tree/puppy50-v103-lean-firefox-network-preserved
