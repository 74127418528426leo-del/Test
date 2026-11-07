# Puppy50 v103: controlled locale-size experiment

Goal: reduce RAM-resident compressed filesystem size while preserving English and Spanish UI translations, browser security, all network and wireless firmware, and the exact same boot method.

Method: start from the published, SHA-256-pinned v102 Intel ISO; remove only other language translation directories from the extracted filesystem; reconstruct the ISO with its existing bootloader. Record the uncompressed and compressed changes instead of assuming a benefit.

Verification: unit-test pruning on temporary directory trees, including symlinks; verify that all files outside the locale tree are untouched; require unchanged network, browser and certificate files; checksum the ISO; run separate KVM guest trials at multiple RAM levels with HTTPS, screenshots, memory observations and media-ejection evidence. Do not infer physical Wi-Fi support, universal compatibility, or a 384 MiB success from these tests. Keep v102 intact.
