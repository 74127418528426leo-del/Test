# Puppy50 v64 Online QEMU VM (Windows/PowerShell host; UNTESTED host).
# Your Windows host must first connect to Wi-Fi, Ethernet, or hotspot.
$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Iso = Join-Path $Here "Puppy50_Web_v64_Online_QEMU.iso"
if (-not (Test-Path $Iso)) { throw "Missing online ISO: $Iso" }
$Sums = Join-Path $Here "SHA256SUMS"
if (-not (Test-Path $Sums)) { throw "Missing SHA256SUMS for verification." }
$Expected = ((Get-Content $Sums | Select-Object -First 1) -split '\s+')[0].ToLowerInvariant()
$Actual = (Get-FileHash $Iso -Algorithm SHA256).Hash.ToLowerInvariant()
if ($Expected -ne $Actual) { throw "ISO checksum failed. Refusing to run." }
$Qemu = Get-Command "qemu-system-x86_64.exe" -ErrorAction SilentlyContinue
$Exe = if ($Qemu) { $Qemu.Source } else { "C:\Program Files\qemu\qemu-system-x86_64.exe" }
if (-not (Test-Path $Exe)) { throw "Install QEMU for Windows first." }
$Network = if ($env:PUPPY50_NETWORK) { $env:PUPPY50_NETWORK } else { "nat" }
$Nic = switch ($Network) {
    "nat" { @("-nic","user,model=e1000,ipv6=off") }
    "off" { @("-nic","none") }
    default { throw "PUPPY50_NETWORK must be nat or off." }
}
Write-Warning "Online experimental guest over host networking, not full Wi-Fi hardware support. Windows launch NOT independently tested."
& $Exe -machine pc,accel=tcg -cpu qemu64 -m 1024 -smp 2 -drive "file=$Iso,if=ide,media=cdrom,readonly=on" -boot order=d -vga std @Nic -no-reboot
