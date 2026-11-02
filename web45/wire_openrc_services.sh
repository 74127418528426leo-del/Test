#!/bin/sh
# Stage OpenRC runlevel services inside an Alpine rootfs.
# Never runs rc-update on the build host; edits only the given staging tree.
set -eu

if [ "$#" -ne 1 ] || [ ! -d "$1/etc/init.d" ]; then
  echo "usage: wire_openrc_services.sh STAGED_ROOT_WITH_ETC_INIT_D" >&2
  exit 2
fi
ROOT=$1

enable_if_installed() {
  service=$1
  level=$2
  source="$ROOT/etc/init.d/$service"
  target_dir="$ROOT/etc/runlevels/$level"
  target="$target_dir/$service"

  # Different builds may omit optional packages; do not invent an init script.
  if [ ! -e "$source" ]; then
    echo "PUPPY50_V47_SERVICE_SKIPPED service=$service level=$level"
    return 0
  fi

  mkdir -p "$target_dir"
  if [ -e "$target" ] && [ ! -L "$target" ]; then
    echo "PUPPY50_V47_SERVICE_REFUSE_OVERWRITE service=$service" >&2
    exit 3
  fi
  # From /etc/runlevels/LEVEL back up to /etc/init.d: exactly TWO parents.
  ln -sfn "../../init.d/$service" "$target"
  if [ ! -e "$target" ]; then
    echo "PUPPY50_V47_SERVICE_BROKEN_LINK service=$service level=$level" >&2
    exit 4
  fi
  echo "PUPPY50_V47_SERVICE_ENABLED service=$service level=$level"
}

# Alpine eudev provides 'udev' (not 'eudev'); enumeration must run in sysinit.
enable_if_installed udev sysinit
enable_if_installed udev-trigger sysinit
enable_if_installed udev-settle sysinit
enable_if_installed udev-postmount default

# Browser network connectivity and interprocess services.
enable_if_installed dbus default
enable_if_installed dhcpcd default
echo 'PUPPY50_V47_SERVICE_WIRING_COMPLETE'
