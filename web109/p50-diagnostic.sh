#!/bin/sh
sleep 30
{
 echo P50_DIAG_BEGIN
 echo P50_DIAG_CMDLINE; cat /proc/cmdline
 echo P50_DIAG_STAGE_DIR; ls -la /run/p50-stage /run/p50-stage/tools 2>&1 || true
 echo P50_DIAG_MAPPER_NODE; ls -l /dev/mapper /sys/block/dm-*/dm/name 2>&1 || true
 echo P50_DIAG_SERVICE_FILES; ls -l /etc/systemd/system/p50-staged-migration.service /etc/systemd/system/graphical.target.wants/ 2>&1 || true
 echo P50_DIAG_SERVICE_STATUS; systemctl status p50-staged-migration.service --no-pager -l 2>&1 || true
 echo P50_DIAG_SERVICE_ENABLED; systemctl is-enabled p50-staged-migration.service 2>&1 || true
 echo P50_DIAG_SERVICE_JOURNAL; journalctl -b --no-pager -u p50-staged-migration.service -n 100 2>&1 || true
 echo P50_DIAG_GRAPHICAL_TARGET; systemctl status graphical.target --no-pager -l 2>&1 || true
 echo P50_DIAG_TOOLS_MOUNT; findmnt -T /run/p50-stage/tools -o TARGET,SOURCE,FSTYPE,OPTIONS 2>&1 || true
 echo P50_DIAG_MOUNTS; findmnt -rn -o TARGET,SOURCE,FSTYPE | grep -E '^/ |/run/live|/lib/live' || true
 echo P50_DIAG_END
} >/dev/ttyS0 2>&1
