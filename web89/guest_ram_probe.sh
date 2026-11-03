#!/bin/sh
# Puppy50 v89: guest /proc memory sampling to serial. Diagnostic only.
set -u
label=${1:-sample}
case "$label" in *[!a-zA-Z0-9_.-]*|'') label=invalid;; esac
P=${PUPPY50_PROC_ROOT:-/proc}
M=$(awk '/^(MemAvailable|MemFree|MemTotal|Cached|Shmem|AnonPages|Slab|SReclaimable|PageTables|KernelStack|SwapFree|SwapTotal):/{gsub(":","",$1);a[$1]=$2} END {for(i=1;i<=12;i++){key=(i==1?"MemTotal":i==2?"MemAvailable":i==3?"MemFree":i==4?"Cached":i==5?"Shmem":i==6?"AnonPages":i==7?"Slab":i==8?"SReclaimable":i==9?"PageTables":i==10?"KernelStack":i==11?"SwapFree":"SwapTotal");printf "%s%s",(i==1?"":" "),(key"="(key in a?a[key]:"NA"))} print ""}' "$P/meminfo" 2>/dev/null || echo 'meminfo_unavailable=1')
work=$(mktemp /tmp/p50mem.XXXXXX 2>/dev/null) || { echo "P50MEM phase=$label error=tempfile";exit 1; }
trap 'rm -f "$work"' EXIT HUP INT TERM
printf 'pid\tppid\tcomm\tpss_kib\tuss_kib\tswap_kib\n' > "$work"
for entry in "$P"/[0-9]*;do
  [ -d "$entry" ] || continue
  pid=${entry##*/}
  [ -r "$entry/status" ] || continue
  ppid=$(awk '/^PPid:/{print $2;exit}' "$entry/status" 2>/dev/null || true)
  [ -n "$ppid" ] || ppid=0
  comm=$(cat "$entry/comm" 2>/dev/null | tr '\t\r' '  ' | tr -d '\n' || true)
  [ -n "$comm" ] || comm=unknown
  vals='NA NA NA'
  if [ -r "$entry/smaps_rollup" ];then
    vals=$(awk '/^Pss:/{pss=$2} /^Private_Clean:/{pc=$2} /^Private_Dirty:/{pd=$2} /^Swap:/{sw=$2} END {if(pss!=""&&pc!=""&&pd!=""&&sw!="") printf "%d %d %d",pss,pc+pd,sw; else print "NA NA NA"}' "$entry/smaps_rollup" 2>/dev/null || echo 'NA NA NA')
  fi
  set -- $vals
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$pid" "$ppid" "$comm" "${1:-NA}" "${2:-NA}" "${3:-NA}" >> "$work"
done
AGG=$(awk -F '\t' '
 NR>1 {par[$1]=$2;nm[$1]=$3;ps[$1]=$4;us[$1]=$5;sw[$1]=$6;ids[$1]=1}
 END {
  for(id in ids)if(nm[id]=="firefox-esr"||nm[id]=="firefox")ff[id]=1
  for(iter=0;iter<80;iter++){new=0;for(id in ids)if(!ff[id]&&ff[par[id]]){ff[id]=1;new++}if(!new)break}
  pss=uss=swap=allpss=nff=nmiss=nallmiss=0
  for(id in ids){if(ps[id]=="NA")nallmiss++;else allpss+=ps[id];if(ff[id]){nff++;if(ps[id]=="NA")nmiss++;else{pss+=ps[id];uss+=us[id];swap+=sw[id]}}}
  printf "firefox_count=%d firefox_pss_kib=%d firefox_uss_kib=%d firefox_swap_kib=%d firefox_pss_missing=%d all_process_pss_kib=%d all_process_pss_missing=%d",nff,pss,uss,swap,nmiss,allpss,nallmiss
 }' "$work")
SFS=NA
for f in /.web-ram/webroot.sfs /ram/webroot.sfs;do
 if [ -f "$f" ];then SFS=$(wc -c < "$f"|tr -d ' ');break;fi
done
PRESS=NA
if [ -r "$P/pressure/memory" ];then PRESS=$(awk '/^some /{for(i=1;i<=NF;i++)if($i~/^avg10=/){split($i,a,"=");print a[2];exit}}' "$P/pressure/memory" 2>/dev/null || echo NA);fi
OOM=NA
if [ -r "$P/vmstat" ];then OOM=$(awk '/^oom_kill /{print $2;exit}' "$P/vmstat" 2>/dev/null||echo NA);fi
printf 'P50MEM phase=%s %s %s compressed_root_bytes=%s psi_some_avg10=%s oom_kills=%s\n' "$label" "$M" "$AGG" "$SFS" "$PRESS" "$OOM"
