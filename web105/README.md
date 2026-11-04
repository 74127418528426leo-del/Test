# Puppy50 Firefox v105 — restore signed H.264/HEVC software codec

**Hypothesis:** The v104 original 3840 × 2160 Pexels MP4 failed in actual Firefox with HTML5 MediaError code **4**. The original build disabled APT recommended packages (`--apt-recommends false`) and its explicit package list omitted `libavcodec61`. Firefox ESR on Linux often uses FFmpeg's `libavcodec` to decode H.264/AAC/HEVC media. Debian bug #1129557 records unsupported MP4/HEVC when the matching libavcodec is absent.

**One-variable fix:** install `libavcodec61` and its signed Debian dependencies into a copied, verified Live root. Do not alter Firefox preferences, sandbox, HTTPS CA certificates, or NetworkManager. Build a new experimental ISO and repeat exactly the v104 KVM HTML5 video and network test.

**Acceptance:** original 4K file is actually shown in Firefox. On-screen intrinsic `video.videoWidth` and `video.videoHeight` must equal `3840 × 2160`; `currentTime` and video frame counters must increase between independent QEMU screenshots. Decoder *performance* is not proven by metadata alone. If codec unsupported or video errors persist, retain as negative evidence, do not promote ISO.

**Not required:** disabling Firefox sandbox, hardware decode/VAAPI on a virtual CPU, bypassing Cloudflare challenges, adding proprietary account credentials. This is a Live RAM-only guest, not the user's running Xubuntu OS.

**Evidence baseline:** https://github.com/74127418528426leo-del/Test/actions/runs/41757014605

**Firefox media diagnosis:** https://firefox-source-docs.mozilla.org/media/Diagnostics.html

**Debian codec bug:** https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=1129557
