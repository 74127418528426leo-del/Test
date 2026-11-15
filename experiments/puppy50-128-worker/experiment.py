#!/usr/bin/env python3
"""128 REAL CPU codec tasks, not 128 LLM agents and not an OS/VM boot test."""
from __future__ import annotations
import argparse, concurrent.futures, csv, hashlib, json, os, platform
import random, statistics, subprocess, time
from pathlib import Path
from datetime import datetime, timezone

MiB=1048576
CODECS=([("gzip",i) for i in range(1,10)]
        + [("zstd",i) for i in range(1,17)]
        + [("xz",i) for i in range(0,7)])
DATASETS=("configs","binaries","mixed","repetitive")
assert len(CODECS)==32

def sha(x):
    return hashlib.sha256(x).hexdigest()

def command(codec,level=None,decompress=False):
    if decompress:
        return [codec,"-d","-c"] if codec!="zstd" else ["zstd","-q","-d","-c"]
    if codec=="gzip": return ["gzip","-n",f"-{level}","-c"]
    if codec=="zstd": return ["zstd","-q","-T1",f"-{level}","-c"]
    return ["xz","--threads=1",f"-{level}","-c"]

def pipe(args,data):
    p=subprocess.run(args,input=data,stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE,check=False)
    if p.returncode:
        raise RuntimeError(f"{args[0]} failed: {p.stderr[:180]!r}")
    return p.stdout

def collected(paths,n):
    out=bytearray()
    for path in sorted(paths):
        try: data=path.read_bytes()
        except OSError: continue
        if 100<len(data)<12*MiB: out.extend(data[:max(0,n-len(out))])
        if len(out)>=n: break
    if not out: raise RuntimeError("no usable source files")
    return (bytes(out)*(n//len(out)+1))[:n]

def datasets(n):
    texts=[p for root in ("/etc","/usr/share/doc","/usr/lib/python3.11")
           for p in Path(root).rglob("*") if p.is_file() and
           p.suffix in (".conf",".ini",".txt",".py",".cfg",".list",".md",".service")]
    binaries=[p for root in ("/usr/bin","/bin")
              for p in Path(root).iterdir() if p.is_file() and not p.is_symlink()]
    text_data=collected(texts,n); binary_data=collected(binaries,n)
    mixed=b"".join(text_data[i:i+4096]+binary_data[i:i+4096]
                   for i in range(0,n//2,4096))[:n]
    r=random.Random(50)
    lines=b"".join(f"{i%200:04d} service boot stage={i%8} token={r.randrange(100):02d}\n".encode()
                   for i in range(7000))
    repetitive=(lines*(n//len(lines)+1))[:n]
    return dict(configs=text_data,binaries=binary_data,mixed=mixed,repetitive=repetitive)

def worker(mission):
    dataset,codec,level,data,digest=mission
    t=time.perf_counter_ns()
    compressed=pipe(command(codec,level),data)
    compression=(time.perf_counter_ns()-t)/1e6
    timing=[]
    for _ in range(3):
        t=time.perf_counter_ns()
        decoded=pipe(command(codec,decompress=True),compressed)
        timing.append((time.perf_counter_ns()-t)/1e6)
        if sha(decoded)!=digest:
            raise AssertionError(f"bad checksum: {dataset} {codec} {level}")
    return dict(worker_id=f"{dataset}-{codec}-{level}",dataset=dataset,codec=codec,
        level=level,input_bytes=len(data),compressed_bytes=len(compressed),
        ratio=round(len(compressed)/len(data),6),
        compress_ms=round(compression,3),
        decompress_median_ms=round(statistics.median(timing),3),verified=True)

def replay(results,data):
    payload=data["mixed"]; digest=sha(payload)
    baseline=next(x for x in results if x["dataset"]=="mixed"
                  and x["codec"]=="gzip" and x["level"]==6)
    eligible=[x for x in results if x["dataset"]=="mixed"
              and x["compressed_bytes"]<=int(baseline["compressed_bytes"]*1.15)]
    chosen=sorted(eligible,key=lambda x:x["decompress_median_ms"])[:12]
    if baseline not in chosen: chosen.append(baseline)
    out=[]
    for x in chosen:
        encoded=pipe(command(x["codec"],x["level"]),payload)
        timings=[]
        for i in range(9):
            t=time.perf_counter_ns()
            dec=pipe(command(x["codec"],decompress=True),encoded)
            dt=(time.perf_counter_ns()-t)/1e6
            assert sha(dec)==digest
            if i>=2: timings.append(dt)
        out.append({**x,"replay_median_ms":round(statistics.median(timings),3),
            "replay_min_ms":round(min(timings),3),
            "replay_max_ms":round(max(timings),3),"replay_trials":len(timings)})
    return sorted(out,key=lambda x:x["replay_median_ms"]),baseline

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="results")
    p.add_argument("--slots",type=int,default=min(4,os.cpu_count() or 1))
    p.add_argument("--mib",type=int,default=1,choices=[1,2,4])
    opt=p.parse_args()
    folder=Path(opt.output);folder.mkdir(parents=True,exist_ok=True)
    data=datasets(opt.mib*MiB)
    missions=[(ds,codec,level,data[ds],sha(data[ds]))
              for ds in DATASETS for codec,level in CODECS]
    completed=[]; errors=[]; started=time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=opt.slots) as pool:
        future={pool.submit(worker,m):m[:3] for m in missions}
        for f in concurrent.futures.as_completed(future):
            try: completed.append(f.result())
            except Exception as e: errors.append(dict(task=future[f],error=str(e)))
    duration=time.perf_counter()-started
    completed.sort(key=lambda x:(x["dataset"],x["codec"],x["level"]))
    ranked,baseline=replay(completed,data) if len(completed)==128 else ([],None)
    result=dict(experiment="Puppy50 128 CPU codec tasks",
       disclaimer="NOT 128 AI agents, GPU jobs, real Puppy50 ISO or VM boot tests",
       timestamp_utc=datetime.now(timezone.utc).isoformat(),
       platform=platform.platform(),cpu_count=os.cpu_count(),
       parallel_slots=opt.slots,duration_seconds=round(duration,3),
       submitted_tasks=128,completed_tasks=len(completed),
       verified_tasks=sum(bool(x["verified"]) for x in completed),
       failed_tasks=len(errors), errors=errors,
       sample_sha256={k:sha(v) for k,v in data.items()},
       sample_bytes=opt.mib*MiB,baseline_mixed_gzip6=baseline,
       sequential_replay_ranked=ranked)
    cols=("worker_id","dataset","codec","level","input_bytes",
          "compressed_bytes","ratio","compress_ms","decompress_median_ms","verified")
    with (folder/"all_128_tasks.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(completed)
    (folder/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
    lines=["# Puppy50 128 task CPU micro-experiment","",
        f"- Submitted: 128; passed verification: {result['verified_tasks']}; failed: {len(errors)}",
        f"- Parallel worker slots: {opt.slots}; execution: {duration:.2f} sec",
        "- These data are representative local Linux files, NOT the Puppy50 initramfs.",
        "- Each task was checked using SHA256 on 3 independent decompressions.",
        "- Replay uses 2 warmups and 7 sequential timed measurements.",
        "","## Mixed-payload sequential replay","",
        "| Codec | Level | Size (KiB) | Median decompress (ms) |",
        "|:--|--:|--:|--:|"]
    for r in ranked:
        lines.append(f"| {r['codec']} | {r['level']} | {r['compressed_bytes']/1024:.1f} | {r['replay_median_ms']:.3f} |")
    lines.extend(["","## Scope caveat","",
        "This does not test OS boot, Firefox, VM, GPU, or RAM-only migration. "
        "No Puppy50 optimization should be claimed from these data alone."])
    (folder/"REPORT.md").write_text("\n".join(lines)+"\n")
    print(json.dumps({"submitted":128,"verified":result["verified_tasks"],
       "failed":len(errors),"first_replay_candidate":ranked[0] if ranked else None},
       indent=2))
    if errors: raise SystemExit(1)

if __name__=="__main__":
    main()
