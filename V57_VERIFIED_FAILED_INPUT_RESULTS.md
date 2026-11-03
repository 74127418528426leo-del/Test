# Puppy50 v57 — Verified failed input-interaction acceptance

Completed KVM Actions run: https://github.com/74127418528426leo-del/Test/actions/runs/41557809792

The workflow finished with conclusion **failure** on its explicit, honest 384MiB offline interaction acceptance gate. Its build, custom LLVM-free Mesa integration, real ISO construction and full KVM evidence upload had otherwise completed.

Measured bootless firmwareless LLVM-free Softpipe XZ root:
- **155,881,472 bytes = 148.66015625 MiB**.
- In the identical-XZ reference build the unmodified Mesa/LLVM root was 212,209,664 bytes, so the matched compressed savings were **56,328,192 bytes = 53.71875 MiB**.
- This v57 filesystem is around 40,960 compressed bytes larger than the earlier v54 148.621 MiB root (minor driver/HTML differences). Do not repeat the older number as a new v57 measurement.

Actual real KVM results:
| Test | 384MiB | 1024MiB |
|---|---|---|
| SquashFS copied to tmpfs | PASS | PASS |
| Switched RAM root and ejected CD | PASS | PASS |
| Firefox visible in screenshot | NO | YES |
| Gold script-ready DOM indicator | NO | YES |
| Orange click response | NO | NO |
| Green keyboard T response | NO | NO |

QEMU monitor accepted its input commands, but guest serial still showed:
```
PUPPY50_V56_INPUT_MODULE_FAILED=evdev
PUPPY50_V56_INPUT_MODULE_FAILED=psmouse
PUPPY50_V56_INPUT_MODULE_FAILED=mousedev
H: Handlers=sysrq kbd
```

The v57 branch retained these drivers in the initial RAM disk but had **not yet included them in the generated direct-insmod early loader**. The absence of eventX and browser input was therefore not fixed in v57.

Specific follow-up:
- v58 isolates loading evdev, psmouse, and mousedev **before switch_root**, with early kernel checks: https://github.com/74127418528426leo-del/Test/actions/runs/41559290419
- v59 incorporates the exact early-input handoff into the smaller custom-Mesa image and uses a strict 384MiB DOM interaction gate: https://github.com/74127418528426leo-del/Test/actions/runs/41560016480

These are VM-specific experiments. No secure Internet browser, WebGL, sound, updateable APK package set, or real Intel GMA 8086:0042 deployment was verified. Do not infer browser success at 384MiB from a boot-only marker or a passing filesystem-size audit.
