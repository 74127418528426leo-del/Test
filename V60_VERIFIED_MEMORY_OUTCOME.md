# Puppy50 v60 — verified bounded zram test result

Real KVM workflow (conclusion: FAIL on explicit 384MiB offline-interaction gate):
https://github.com/74127418528426leo-del/Test/actions/runs/41561951905

- Same early-evdev + LLVM-free Softpipe Firefox architecture as v59.
- Actual matched XZ root was **148.695 MiB** after adding the zram setup and telemetry.
- Real **384MiB** and **1024MiB** physical guest RAM allocations both copied the root entirely into RAM, switched root and ejected the virtual boot CD.
- The guest loaded zram from the early initrd, activated 256MiB **virtual** swap with a 128MiB **physical allocator** cap and measured actual use with `/sys/block/zram0/mm_stat`.
- At **384MiB**, peak sampled orig_data_size was **191.672 MiB**, compr_data_size **127.108 MiB**, and mem_used_total **128.0 MiB**. That is only about **1.51:1** data compression. Firefox still did NOT render the local page within the observation interval, and DOM mouse/keyboard verification failed.
- At **1024MiB**, peak sampled orig_data_size was **132.664 MiB**, compressed data **124.740 MiB**, actual allocated **126.32 MiB**, and the offline JavaScript, mouse click and keyboard checks passed. This zram workload had a much poorer compression ratio than the 384MiB example.
- Neither nominal virtual swap capacity nor a working swap device constitutes an addition to physical RAM. This experiment is diskless and cannot prove the browser needed less physical RAM overall.
- No secure HTTPS, real Internet websites, Intel graphics or physical PC capability was verified.

**Decision:** The current 128MiB zram cap is fully used in the 384MiB guest yet cannot make Firefox render. Do not increase the cap simply to report a larger virtual memory figure. Preserve v59 as the unmodified QEMU preview baseline and investigate a functioning smaller browser engine or carefully measured browser-process memory changes.

Source: https://github.com/74127418528426leo-del/Test/tree/puppy50-v60-zram-384-memory
