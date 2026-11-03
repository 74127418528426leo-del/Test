# UNTESTED Windows convenience wrapper. Tested VM used Linux KVM.
$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Iso = Join-Path $Here "Puppy50_Web_QEMU_Preview_v62.iso"
if (-not (Test-Path $Iso)) { throw "Missing ISO: $Iso" }
$Sums = Join-Path $Here "SHA256SUMS"
if (-not (Test-Path $Sums)) { throw "Missing SHA256SUMS" }
$Expected = ((Get-Content $Sums | Select-Object -First 1) -split '\s+')[0].ToLowerInvariant()
$Actual = (Get-FileHash $Iso -Algorithm SHA256).Hash.ToLowerInvariant()
if ($Expected -ne $Actual) { throw "ISO checksum does not match" }
$Qemu = Get-Command "qemu-system-x86_64.exe" -ErrorAction SilentlyContinue
$Exe = if ($Qemu) { $Qemu.Source } else { "C:\Program Files\qemu\qemu-system-x86_64.exe" }
if (-not (Test-Path $Exe)) { throw "Install QEMU for Windows first." }
Write-Warning "Offline QEMU standard VGA; untested on Windows host. This is NOT hardware/Internet certified."
& $Exe -machine pc,accel=tcg -cpu qemu64 -m 1024 -smp 2 -drive "file=$Iso,if=ide,media=cdrom,readonly=on" -boot order=d -vga std -nic none -no-reboot
