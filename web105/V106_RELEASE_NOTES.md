# Puppy50 v106 — automatic boot experiment

This is an experimental Debian-based live browser image. It automatically starts the default live system after a two-second menu and opens Firefox. The standard live entry requests `toram`. The fail-safe menu entries do not request `toram` and have not been verified for use after removing the boot media. The browser and operating system are intended to run from a temporary live session; save files somewhere persistent before shutting down.

The previous v104 image remained at its boot menu waiting for Enter. The new image includes a safer network-probe change: the optional developer QEMU HTTPS bridge is disabled by default and requires both an explicit kernel boot option and QEMU/KVM detection. Ordinary network setup still uses NetworkManager, and Firefox's TLS certificate checking was not disabled.

**The eight-second goal was not met.** In one QEMU/KVM trial the default BIOS/optical boot displayed Firefox after 33.4 seconds with 2,560 MiB assigned. A virtual USB trial with reads capped at 30 MiB/s displayed Firefox after 62.51 seconds with 3,072 MiB assigned. These are individual virtual-machine observations, not a benchmark of the Acer Aspire X3950. Firmware, CPU, storage speed, memory, hardware support, and network conditions will affect real startup time; the capped trial is a simulation, not a measurement of a particular USB stick.

The image is a prerelease, not a supported or security-certified daily-driver operating system. Physical USB boot, the Acer itself, physical Wi-Fi, all network types, Secure Boot, DRM, and 4K playback have not been verified. A VM with 2,560 MiB or 3,072 MiB assigned was used in the tests; that is not a determined minimum RAM requirement. The older 384 MiB goal has not been established for this image running Firefox.

Back up a USB stick before writing the ISO to it: writing an ISO normally erases the stick. A live session can lose downloaded files, browser history, bookmarks, and other changes on shutdown unless they are saved to a separate persistent location.

SHA-256 of `Puppy50_v106_AutoBoot_EXPERIMENTAL.iso`:

```
537e1129bcbe0373778e30fcf3e15815b184493a0c67d00b036c5e960c75935e
```

The build and test source is in the `puppy50-v105-fast-boot` branch of this repository. The optional bridge is only for test environments and is not a general network proxy or a security boundary.
