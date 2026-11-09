# Puppy50 dual-layer recovery: real VM suspension test

This diagnostic was run against the previously tested dual-layer prototype, not the published v114 ISO. In a BIOS VM with 3 GiB RAM, the helper successfully suspended the extra device-mapper target using a real kernel ioctl. The test then **simulated** an error at the first resume step. It issued real table-clear and recovery-resume ioctls, which returned success; the migration script confirmed that the extra device's active table matched the saved original table.

The core had already switched to its RAM copy. The test retained both original and RAM loop backings and copies, did not signal RAM ready, and left the virtual USB attached. Firefox subsequently displayed the firmware directory while the red keep-USB-connected warning was visible. The saved logs and screenshots record these observations.

This is one virtual test of a simulated initial failure. It does not establish behavior for a real kernel resume error, an error during the recovery ioctls, unexpected power loss, physical Wi-Fi or hotplug, the Acer's graphics, UEFI, or lower-memory configurations. The dual-layer prototype remains research rather than the general-use release.

Test run: https://github.com/74127418528426leo-del/Test/actions/runs/42696000366
