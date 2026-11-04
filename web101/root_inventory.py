#!/usr/bin/env python3
"""Read-only squashfs metadata inventory. Numeric sizes are UNCOMPRESSED sizes.
This is not a validated ISO shrink, or a claim of booting in less RAM.
"""
import argparse,collections,csv,json,re
from pathlib import Path

def classify(path):
    p=path.lstrip("/")
    areas=[
      ("firefox_runtime","usr/lib/firefox-esr/"),
      ("network_firmware","usr/lib/firmware/"),
      ("kernel_modules","usr/lib/modules/"),
      ("locale_translations","usr/share/locale/"),
      ("docs_and_examples","usr/share/doc/"),
      ("man_and_info_pages","usr/share/man/","usr/share/info/"),
      ("fonts","usr/share/fonts/"),
      ("icons_and_themes","usr/share/icons/","usr/share/themes/"),
      ("python_packages","usr/lib/python"),
      ("desktop_applications","usr/share/applications/")]
    for section,*prefixes in areas:
        if any(p.startswith(prefix) for prefix in prefixes):return section
    return (p.split("/",2)[0] or "root")+"/"+(p.split("/",2)[1] if "/" in p else ".")
def parse_listing(contents):
    rows=[]
    for line in contents.splitlines():
        parts=line.split(maxsplit=5)
        if len(parts)<6 or not parts[0].startswith("-"):continue
        if not parts[2].isdigit():continue
        name=parts[5]
        if name.startswith("squashfs-root/"):name=name[len("squashfs-root/"):]
        if name.startswith("->") or name.startswith("/"):continue
        if not (parts[0][:1]=="-"):continue
        rows.append({"path":name,"bytes":int(parts[2]),"category":classify(name)})
    return rows
def summarize(rows,iso_bytes=None,squashfs_bytes=None):
    areas=collections.Counter()
    for x in rows:areas[x["category"]]+=x["bytes"]
    total=sum(x["bytes"] for x in rows)
    top_files=sorted(rows,key=lambda d:d["bytes"],reverse=True)[:150]
    return {
      "schema":"PUPPY50_V101_UNCOMPRESSED_ROOT_INVENTORY",
      "method":"unsquashfs -ll metadata: regular-file uncompressed logical bytes; may exclude symlinks/directories and shared-link duplication",
      "size_uncompressed_regular_files_bytes":total,
      "compressed_squashfs_file_size_bytes":squashfs_bytes,
      "complete_original_iso_file_size_bytes":iso_bytes,
      "NOT_measured_compressed_savings_from_removing_files":True,
      "NOT_measured_384mib_boot":True,
      "NOT_production_safe_prune_list":True,
      "per_category_bytes":[{"category":x,"bytes":v,"file_count":sum(y["category"]==x for y in rows)} for x,v in areas.most_common()],
      "top_150_regular_files":top_files,
      "total_regular_file_entries":len(rows)}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--listing",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--iso-size",type=int)
    p.add_argument("--squashfs-size",type=int)
    a=p.parse_args()
    data=summarize(parse_listing(a.listing.read_text(errors="replace")),a.iso_size,a.squashfs_size)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(data,indent=2)+"\n")
    print(json.dumps({k:v for k,v in data.items() if k not in ("top_150_regular_files","per_category_bytes")},indent=2))
    for x in data["per_category_bytes"][:30]:
        print(f'{x["category"]:30s} {x["bytes"]/1048576:10.2f} MiB ({x["file_count"]} files)')
    if data["total_regular_file_entries"]<2000:
        raise SystemExit("Incomplete extraction metadata; cannot use size inventory")
if __name__=="__main__":main()
