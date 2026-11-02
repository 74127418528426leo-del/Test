#!/bin/busybox sh
# Puppy50 Web v45: experimental RAM-only compressed-root boot.
# The actual compressed Firefox/browser OS remains on tmpfs after ejecting CD.
PATH=/bin:/sbin:/usr/bin:/usr/sbin
export PATH
/busybox mkdir -p /proc /sys /dev /tmp /media /ram /lower /rw /newroot
/busybox mount -t proc proc /proc
/busybox mount -t sysfs sysfs /sys
/busybox mount -t devtmpfs devtmpfs /dev
/bin/busybox mkdir -p /dev/pts
/bin/busybox mount -t devpts devpts /dev/pts 2>/dev/null
exec >/dev/console 2>&1
echo PUPPY50_WEB_V45_INIT_STARTED
/busybox modprobe ata_piix 2>/dev/null || :
/busybox modprobe sr_mod 2>/dev/null || :
/busybox modprobe isofs 2>/dev/null || :
/busybox modprobe loop 2>/dev/null || :
/busybox modprobe squashfs 2>/dev/null || :
/busybox modprobe overlay 2>/dev/null || :
/busybox modprobe virtio_blk 2>/dev/null || :
/busybox modprobe virtio_pci 2>/dev/null || :
/bin/busybox mdev -s 2>/dev/null || :
MEDIA=""
i=0
while [ "$i" -lt 25 ]; do
 for dev in /dev/sr0 /dev/sr1 /dev/hdc /dev/cdrom /dev/vda /dev/sda; do
   if [ -b "$dev" ] && /busybox mount -t iso9660 -o ro "$dev" /media 2>/dev/null; then
     if [ -s /media/puppy_dpupbw64_10.0.12.sfs ]; then MEDIA="$dev"; break; fi
     /busybox umount /media || :
   fi
 done
 [ -n "$MEDIA" ] && break
 /busybox sleep 1
 i=$((i+1))
done
if [ -z "$MEDIA" ]; then
 echo PUPPY50_WEB_V45_FAIL_BOOT_MEDIUM_MISSING
 exec /busybox sh
fi
echo "PUPPY50_WEB_V45_CD_FOUND $MEDIA"
# tmpfs limit is virtual; its physical pages will be charged as they are used.
if ! /busybox mount -t tmpfs -o size=90% tmpfs /ram; then exec /busybox sh; fi
if ! /busybox cp /media/puppy_dpupbw64_10.0.12.sfs /ram/webroot.sfs; then
 echo PUPPY50_WEB_V45_FAIL_RAM_COPY
 exec /busybox sh
fi
echo "PUPPY50_WEB_V45_RAM_COPY_COMPLETE bytes=$(/busybox stat -c %s /ram/webroot.sfs)"
/busybox umount /media
echo PUPPY50_WEB_V45_BOOT_MEDIA_UNMOUNTED
/busybox mkdir -p /lower /rw /newroot
if ! /busybox mount -t squashfs -o loop,ro /ram/webroot.sfs /lower; then
 echo PUPPY50_WEB_V45_FAIL_SQUASHFS_MOUNT
 exec /busybox sh
fi
/busybox mount -t tmpfs -o size=128m tmpfs /rw || exec /busybox sh
/busybox mkdir -p /rw/upper /rw/work
if ! /busybox mount -t overlay overlay -o lowerdir=/lower,upperdir=/rw/upper,workdir=/rw/work /newroot; then
 echo PUPPY50_WEB_V45_FAIL_OVERLAY_MOUNT
 exec /busybox sh
fi
/bin/busybox mkdir -p /newroot/.web-ram /newroot/.web-lower /newroot/.web-rw /newroot/proc /newroot/sys /newroot/dev
/busybox mount --move /ram /newroot/.web-ram || exec /busybox sh
/busybox mount --move /lower /newroot/.web-lower || exec /busybox sh
/busybox mount --move /rw /newroot/.web-rw || exec /busybox sh
/busybox mount --move /proc /newroot/proc || exec /busybox sh
/busybox mount --move /sys /newroot/sys || exec /busybox sh
/busybox mount --move /dev /newroot/dev || exec /busybox sh
echo PUPPY50_WEB_V45_SWITCH_ROOT_RAM_ONLY
exec /busybox switch_root /newroot /sbin/init
