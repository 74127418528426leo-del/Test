#!/bin/sh
# Diagnostic only: mincore observes existing file-cache pages without reading.
set -u
B=/run/p50-stage/tools/busybox
O=/run/p50-stage/hotpages.tsv
printf 'P50_HOT_TRACE_V1\n' >"$O"
for i in $("$B" seq 0 13); do
    u=$("$B" cut -d ' ' -f1 /proc/uptime)
    printf 'SNAP\t%s\t%s\n' "$i" "$u" >>"$O"
    for f in /usr/lib/firefox-esr/libxul.so /usr/lib/firefox-esr/omni.ja /usr/lib/firefox-esr/browser/omni.ja; do
        /run/p50-stage/tools/p50-resident "$f" >>"$O" 2>>/run/p50-stage/hotpages-errors.log || echo "P50_HOT_PROBE_ERROR $f" >/dev/ttyS0
    done
    printf 'ENDSNAP\t%s\n' "$i" >>"$O"
    printf 'P50_HOT_SNAPSHOT_%02d\n' "$i" >/dev/ttyS0
    "$B" sleep 1
done
printf 'P50_HOT_TRACE_END\n' >>"$O"
/usr/bin/curl --fail --connect-timeout 5 --max-time 15 --noproxy '*' --data-binary "@$O" http://10.0.2.2:8767/trace --output /run/p50-stage/hot-response.txt || echo P50_HOT_UPLOAD_FAILED >/dev/ttyS0
