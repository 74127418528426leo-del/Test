#!/bin/sh
# Configure only-browser login on a new Alpine root (no full Puppy apps).
# Does not weaken Firefox's sandbox, Fission/site isolation, or trust store.
set -eu
[ "$#" -eq 1 ] || exit 2
ROOT=$1
test -f "$ROOT/etc/passwd"
mkdir -p "$ROOT/usr/local/bin" "$ROOT/usr/share/puppy50web" "$ROOT/home/web" \
 "$ROOT/etc/runlevels/default" "$ROOT/etc/runlevels/sysinit" "$ROOT/etc/runlevels/boot"
if ! grep -q '^web:' "$ROOT/etc/passwd"; then
 echo 'web:x:1000:1000:Puppy50 Web:/home/web:/bin/sh' >> "$ROOT/etc/passwd"
 echo 'web:x:!:20000:0:99999:7:::' >> "$ROOT/etc/shadow"
 echo 'web:x:1000:' >> "$ROOT/etc/group"
fi
chown -R 1000:1000 "$ROOT/home/web"
chmod 700 "$ROOT/home/web"
mkdir -p "$ROOT/etc/apk"
cat > "$ROOT/etc/inittab" <<'EOF'
::sysinit:/sbin/openrc sysinit
::sysinit:/sbin/openrc boot
::wait:/sbin/openrc default
tty1::respawn:/usr/local/bin/puppy50-web-launch
tty2::respawn:/sbin/getty 38400 tty2
::ctrlaltdel:/sbin/reboot
::shutdown:/sbin/openrc shutdown
EOF
cat > "$ROOT/usr/local/bin/puppy50-web-launch" <<'EOF'
#!/bin/sh
set -u
mkdir -p /tmp/.X11-unix /run
chmod 1777 /tmp/.X11-unix /tmp
# GLib gspawn posix_spawn aborts if the unprivileged browser cannot open /dev/null.
# Real v46 guest logs showed this exact assertion; fix standard device permissions,
# not Firefox sandboxing or multi-process isolation.
if [ ! -c /dev/null ]; then
  rm -f /dev/null
  mknod /dev/null c 1 3 || { echo 'PUPPY50_WEB_V46_DEV_NULL_CREATE_FAILED' > /dev/ttyS0; exit 42; }
fi
chmod 0666 /dev/null || { echo 'PUPPY50_WEB_V46_DEV_NULL_CHMOD_FAILED' > /dev/ttyS0; exit 43; }
echo 'PUPPY50_WEB_V46_DEV_NULL_STATUS' > /dev/ttyS0 2>/dev/null || true
ls -l /dev/null > /dev/ttyS0 2>/dev/null || true
if su -s /bin/sh web -c 'test -r /dev/null && test -w /dev/null && (: </dev/null) && (: >/dev/null)'; then
  echo 'PUPPY50_WEB_V46_DEV_NULL_NONROOT_RW_PASS' > /dev/ttyS0 2>/dev/null || true
else
  echo 'PUPPY50_WEB_V46_DEV_NULL_NONROOT_RW_FAILED' > /dev/ttyS0 2>/dev/null || true
  exit 44
fi
chown 1000:1000 /home/web
COOKIE=$(od -An -N16 -tx1 /dev/urandom | tr -d ' \n')
XAUTH=/home/web/.Xauthority
rm -f "$XAUTH"
xauth -f "$XAUTH" add :0 . "$COOKIE"
chown 1000:1000 "$XAUTH"
# Linux console handlers are not enough for Xorg/libinput: the guest must
# have the evdev event interface. A real v55 QEMU guest displayed only
# "Handlers=sysrq kbd" with no eventX, and Firefox ignored virtual input.
for driver in evdev psmouse mousedev; do
  if /sbin/modprobe -v "$driver" > /dev/ttyS0 2>&1; then
    echo "PUPPY50_V56_INPUT_MODULE_LOADED=$driver" >/dev/ttyS0 2>/dev/null || true
  else
    echo "PUPPY50_V56_INPUT_MODULE_FAILED=$driver" >/dev/ttyS0 2>/dev/null || true
  fi
done
echo 'PUPPY50_V56_INPUT_HANDLERS_BEFORE_XORG' >/dev/ttyS0 2>/dev/null || true
cat /proc/bus/input/devices >/dev/ttyS0 2>/dev/null || true
ls -la /dev/input >/dev/ttyS0 2>/dev/null || true
echo 'PUPPY50_WEB_V45_XORG_START' > /dev/ttyS0 2>/dev/null || true
Xorg :0 vt1 -nolisten tcp -auth "$XAUTH" > /var/log/Xorg0.log 2>&1 &
XPID=$!
sleep 8
if ! kill -0 "$XPID" 2>/dev/null; then
  echo 'PUPPY50_WEB_V45_XORG_FAILED' >/dev/ttyS0 2>/dev/null || true
  echo 'PUPPY50_WEB_V46_XORG_ERROR_LOG_BEGIN' >/dev/ttyS0 2>/dev/null || true
  tail -85 /var/log/Xorg0.log >/dev/ttyS0 2>/dev/null || true
  ls -l /dev/dri/ >/dev/ttyS0 2>/dev/null || true
  echo 'PUPPY50_WEB_V46_XORG_ERROR_LOG_END' >/dev/ttyS0 2>/dev/null || true
  sleep 30
  exit 1
fi
echo 'PUPPY50_WEB_V45_XORG_RUNNING' > /dev/ttyS0 2>/dev/null || true
echo 'PUPPY50_V55_INPUT_DEVICES_BEGIN' > /dev/ttyS0 2>/dev/null || true
cat /proc/bus/input/devices > /dev/ttyS0 2>/dev/null || true
ls -la /dev/input > /dev/ttyS0 2>/dev/null || true
echo 'PUPPY50_V55_XORG_INPUT_LOG_BEGIN' > /dev/ttyS0 2>/dev/null || true
grep -Ei 'input|keyboard|mouse|libinput|evdev|device added' /var/log/Xorg0.log > /dev/ttyS0 2>/dev/null || true
echo 'PUPPY50_V55_XORG_INPUT_LOG_END' > /dev/ttyS0 2>/dev/null || true
echo 'PUPPY50_V55_INPUT_DEVICES_END' > /dev/ttyS0 2>/dev/null || true
su -s /bin/sh web -c 'DISPLAY=:0 XAUTHORITY=/home/web/.Xauthority openbox' >/var/log/openbox.log 2>&1 &
sleep 2
echo 'PUPPY50_WEB_V45_FIREFOX_REQUESTED' > /dev/ttyS0 2>/dev/null || true
su -s /bin/sh web -c 'DISPLAY=:0 XAUTHORITY=/home/web/.Xauthority HOME=/home/web firefox-esr file:///usr/share/puppy50web/index.html' >/var/log/firefox.log 2>&1
code=$?
echo "PUPPY50_WEB_V46_FIREFOX_EXIT_CODE=$code" > /dev/ttyS0 2>/dev/null || true
echo 'PUPPY50_WEB_V46_FIREFOX_LOG_BEGIN' > /dev/ttyS0 2>/dev/null || true
tail -90 /var/log/firefox.log > /dev/ttyS0 2>/dev/null || true
echo 'PUPPY50_WEB_V46_FIREFOX_LOG_END' > /dev/ttyS0 2>/dev/null || true
echo 'PUPPY50_WEB_V46_OPENBOX_LOG_BEGIN' > /dev/ttyS0 2>/dev/null || true
tail -35 /var/log/openbox.log > /dev/ttyS0 2>/dev/null || true
echo 'PUPPY50_WEB_V46_OPENBOX_LOG_END' > /dev/ttyS0 2>/dev/null || true
echo 'PUPPY50_WEB_V46_XORG_LOG_LAST' > /dev/ttyS0 2>/dev/null || true
tail -40 /var/log/Xorg0.log > /dev/ttyS0 2>/dev/null || true
echo 'PUPPY50_WEB_V46_RUNTIME_MEMORY' > /dev/ttyS0 2>/dev/null || true
grep -E '^(MemTotal|MemAvailable|Shmem|SwapTotal|SwapFree):' /proc/meminfo >/dev/ttyS0 2>/dev/null || true
echo 'PUPPY50_WEB_V45_FIREFOX_EXITED' > /dev/ttyS0 2>/dev/null || true
kill "$XPID" 2>/dev/null || true
sleep 4
EOF
chmod 755 "$ROOT/usr/local/bin/puppy50-web-launch"
cat > "$ROOT/usr/share/puppy50web/index.html" <<'EOF'
<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Puppy50 Web — RAM Browser Test</title>
<style>
body{margin:0;background:#071020;color:#e5ecf7;font:16px system-ui,sans-serif;
min-height:100vh;display:grid;place-items:center}
main{border:1px solid #3d5368;background:#10243c;border-radius:20px;
padding:44px;max-width:700px}
h1{font-size:42px;color:#9fe1ff}p{line-height:1.65}
strong{color:#ffe498}
</style></head>
<body><main><h1>PUPPY50 WEB</h1><p>Real browser-only Linux, using RAM-backed system files.</p>
<p><strong>384 MiB target — experimental build.</strong></p>
<p>This local page proves browser rendering without needing an internet connection.</p>
<p>The normal Firefox address bar, tabs and downloads remain available.</p>
</main>
<script>
(function() {
  // Three visually distinct stages: JavaScript, pointer click, keyboard.
  // Avoid requiring focus merely to prove that JavaScript executed.
  const root=document.documentElement,body=document.body;
  const title=document.querySelector('h1');
  body.style.borderTop='80px solid #ffc044';
  title.textContent='SCRIPT READY — PUPPY50 WEB';
  root.dataset.testStage='script-ready';
  window.addEventListener('click', function(){
    if(root.dataset.testStage==='key-confirmed')return;
    root.dataset.testStage='click-confirmed';
    body.style.background='#d48c27';
    title.textContent='CLICK CONFIRMED';
  },true);
  window.addEventListener('keydown',function(event){
    if(event.key==='t'||event.key==='T'){
      root.dataset.testStage='key-confirmed';
      root.style.background='#2bcc71';
      body.style.background='#2bcc71';
      document.querySelector('main').style.background='#2bcc71';
      title.textContent='KEYBOARD CONFIRMED';
    }
  },true);
})();
</script></body></html>
EOF
# Enable services through audited OpenRC wiring. This corrects the former
# broken ../../../init.d links (must be ../../init.d under /etc/runlevels/*)
# and uses Alpine's actual udev service names and sysinit ordering.
sh "$(dirname "$0")/wire_openrc_services.sh" "$ROOT"
# Do not accidentally auto-setup a permanent root disk.
echo "puppy50-web" > "$ROOT/etc/hostname"
test -x "$ROOT/usr/local/bin/puppy50-web-launch"
test -s "$ROOT/usr/share/puppy50web/index.html"
echo 'PUPPY50_WEB_V45_USER_SESSION_CONFIGURATION=PASS'
