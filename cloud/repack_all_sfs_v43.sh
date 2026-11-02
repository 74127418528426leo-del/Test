#!/bin/sh
# Puppy50 v43: Lossless XZ repack of ALL original BookwormPup64 SFS files.
# Fail closed on missing layers, metadata differences, or inability to round-trip.
set -eu
[ "$#" -eq 3 ] || { echo 'Usage: repack_all_sfs_v43.sh ORIGINAL_SFS_DIR NEW_SFS_DIR REPORT_DIR' >&2; exit 2; }
original=$1
out=$2
reports=$3
[ -d "$original" ] && [ ! -e "$out" ] || { echo 'Missing input or output already exists' >&2; exit 2; }
mkdir -p "$out" "$reports"
printf 'sfs,original_bytes,xz_bytes,delta_bytes,percent_saved,roundtrip_verified\n' > "$reports/recompression.csv"
count=0
for name in \
 adrv_dpupbw64_10.0.12.sfs \
 bdrv_dpupbw64_10.0.12.sfs \
 fdrv_dpupbw64_10.0.12.sfs \
 kbuild-6.1.148.sfs \
 puppy_dpupbw64_10.0.12.sfs \
 zdrv_dpupbw64_10.0.12.sfs; do
  src="$original/$name"; dest="$out/$name"
  [ -s "$src" ] || { echo "Missing original $name" >&2; exit 4; }
  base=$(mktemp -d)
  after=$(mktemp -d)
  echo "PUPPY50_V43_REPACK_START name=$name"
  unsquashfs -s "$src" > "$reports/$name.original_superblock.txt"
  unsquashfs -f -d "$base" "$src" > "$reports/$name.extract.log" 2>&1
  mksquashfs "$base" "$dest" -comp xz -b 1M -Xbcj x86 -processors 2 -mem 1024M -exit-on-error -noappend -no-progress > "$reports/$name.build.log" 2>&1
  unsquashfs -s "$dest" > "$reports/$name.repacked_superblock.txt"
  unsquashfs -f -d "$after" "$dest" > "$reports/$name.verify_unpack.log" 2>&1
  python3 cloud/compare_sfs_v41.py "$base" "$after" "$reports/$name.fidelity.json" > "$reports/$name.fidelity.log" 2>&1
  origbytes=$(stat -c %s "$src"); newbytes=$(stat -c %s "$dest")
  python3 - "$reports/recompression.csv" "$name" "$origbytes" "$newbytes" <<'PY'
import sys
file,name,a,b=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4])
with open(file,'a') as f:f.write(f'{name},{a},{b},{a-b},{(a-b)*100/a:.4f},YES\n')
PY
  rm -rf "$base" "$after"
  count=$((count+1))
  echo "PUPPY50_V43_REPACK_SUCCESS name=$name old=$origbytes new=$newbytes"
done
[ "$count" -eq 6 ] || { echo 'Wrong original layer count' >&2; exit 5; }
python3 - "$original" "$out" "$reports" <<'PY'
import csv,json,sys,pathlib
original,out,reports=map(pathlib.Path,sys.argv[1:]);rows=list(csv.DictReader((reports/'recompression.csv').open()))
orig={p.name:p.stat().st_size for p in original.glob('*.sfs')}
repacked={p.name:p.stat().st_size for p in out.glob('*.sfs')}
if len(orig)!=6 or len(repacked)!=6 or set(orig)!=set(repacked) or len(rows)!=6:
    raise SystemExit('Six-layer manifest mismatch')
a=sum(orig.values());b=sum(repacked.values())
result={'all_six_layers_byte_metadata_verified':True,'original_manifest':orig,'repacked_manifest':repacked,
'original_bytes':a,'repacked_xz_bytes':b,'saved_bytes':a-b,'saved_mib':round((a-b)/1048576,3),
'savings_percent':round((a-b)*100/a,3),
'fits_384mib_before_kernel_apps':b<=384*1048576,
'fits_384mib_with_192mib_runtime_reserve':b<=192*1048576,'sfs_rows':rows}
(reports/'FINAL_REPACK_MANIFEST.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
PY
