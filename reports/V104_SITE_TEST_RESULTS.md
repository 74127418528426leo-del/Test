# Puppy50 v104 — website test results

These are single QEMU/KVM trials of the exact v104 experimental ISO using a virtual wired network. Guest RAM values are allocations for the tests, not guaranteed minimums. Screenshots were inspected manually; a loaded page does not establish that all features work.

| Website | Allocated guest RAM | Observed result |
|---|---:|---|
| CNN | 3,072 MiB | Homepage displayed behind a privacy prompt. Firefox showed a DRM notice and part of the page reported DRM unsupported. Video playback was not verified. |
| Gospel of John | 3,072 MiB | Homepage and chapter selection appeared. An individual panorama was not opened. |
| 3D Bible | 4,096 MiB | Genesis page and a 3D scene appeared. Walking and sailing were not exercised. |
| YouTube 4K sample | 4,096 MiB | Watch page appeared, but YouTube requested sign-in to confirm the viewer was not a bot. Video height and playback position remained zero; no 4K playback was verified. |
| Requested Pexels video page | 4,096 MiB | In a separate trial, a human-verification challenge blocked automated access to the video. No 4K playback was verified. |

The challenges were not bypassed. These results do not certify physical Wi-Fi, the user's Acer hardware, audio, DRM content, every website or universal network compatibility.

Evidence: https://github.com/74127418528426leo-del/Test/actions/runs/42326668886 and https://github.com/74127418528426leo-del/Test/actions/runs/42325761511
