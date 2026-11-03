#!/usr/bin/env python3
"""Supervise only Puppy50's own loopback HTTPS CONNECT bridge while QEMU runs.

This does not manage the host's Wi-Fi, bypass access controls, trust new CAs,
or reconfigure the guest. After a bridge-process crash it restarts the exact
child executable, with bounded retry attempts and cleanup on SIGTERM.
Use only the bundled, audited host_https_bridge.py (public-IP destinations,
HTTPS CONNECT only, listens at 127.0.0.1). No privileged access is required.
"""
import argparse
from collections import deque
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time

STOP=False
def stop_handler(signum,frame):
    global STOP
    STOP=True

def check_port_free(port):
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        try:sock.bind(("127.0.0.1",port))
        except OSError:raise RuntimeError("Host loopback bridge port already occupied: refusing unknown proxy")

def listener_ready(port):
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
        sock.settimeout(.3)
        return sock.connect_ex(("127.0.0.1",port))==0

def write_status(path,child,generation,port):
    data={"schema":"PUPPY50_V80_BRIDGE_SUPERVISOR_STATUS",
          "supervisor_pid":os.getpid(),
          "bridge_pid":child.pid,
          "generation":generation,
          "listener":"127.0.0.1:"+str(port),
          "ready":True}
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+".tmp."+str(os.getpid()))
    with tmp.open("w") as file:
        os.chmod(tmp,0o600)
        file.write(json.dumps(data)+"\n")
    os.replace(tmp,path)

def supervise(bridge,status,log,port,max_restarts):
    bridge=Path(bridge).resolve(strict=True)
    status=Path(status).resolve() if Path(status).exists() else Path(status).absolute()
    log=Path(log).absolute()
    if not bridge.is_file() or bridge.name!="host_https_bridge.py":
        raise ValueError("Only the known bundled host_https_bridge.py is allowed")
    if not 1024<=port<=65535:raise ValueError("Invalid high TCP port")
    check_port_free(port)
    for signum in (signal.SIGTERM,signal.SIGINT):
        signal.signal(signum,stop_handler)
    log.parent.mkdir(parents=True,exist_ok=True)
    generation=0
    child=None
    child_log=None
    attempts=deque()
    try:
        while not STOP:
            if child is None or child.poll() is not None:
                if child_log:
                    child_log.close()
                    child_log=None
                # Never trust another application occupying our fixed port.
                check_port_free(port)
                now=time.monotonic()
                while attempts and now-attempts[0]>45:attempts.popleft()
                if len(attempts)>=max_restarts:
                    raise RuntimeError("Crash loop: exhausted bridge restart limit")
                attempts.append(now)
                generation+=1
                child_log=log.open("ab",buffering=0)
                child=subprocess.Popen([sys.executable,"-u",str(bridge),"--port",str(port)],
                    stdin=subprocess.DEVNULL,stdout=child_log,stderr=subprocess.STDOUT)
                print("PUPPY50_V80_BRIDGE_SPAWN generation="+str(generation)+" pid="+str(child.pid),flush=True)
                ready=False
                for _ in range(40):
                    if STOP or child.poll() is not None:break
                    if listener_ready(port):ready=True;break
                    time.sleep(.1)
                if ready:
                    write_status(status,child,generation,port)
                    print("PUPPY50_V80_BRIDGE_LISTEN=PASS generation="+str(generation),flush=True)
                else:
                    if child.poll() is None and not STOP:child.terminate()
                    if STOP:break
                    print("PUPPY50_V80_BRIDGE_START_FAILED generation="+str(generation),flush=True)
                    time.sleep(.4)
            else:
                time.sleep(.25)
        return 0
    finally:
        if child and child.poll() is None:
            child.terminate()
            try:child.wait(timeout=4)
            except subprocess.TimeoutExpired:child.kill();child.wait(timeout=4)
        if child_log:child_log.close()
        try:
            if status.exists():
                current=json.loads(status.read_text())
                if current.get("supervisor_pid")==os.getpid():status.unlink()
        except (OSError,ValueError):pass
        print("PUPPY50_V80_BRIDGE_CLEANUP=PASS",flush=True)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bridge-script",required=True,type=Path)
    ap.add_argument("--status",required=True,type=Path)
    ap.add_argument("--log",required=True,type=Path)
    ap.add_argument("--port",type=int,default=3128)
    ap.add_argument("--max-restarts",type=int,default=6)
    args=ap.parse_args()
    if not 1<=args.max_restarts<=30:raise SystemExit("Invalid restart budget")
    try:return supervise(args.bridge_script,args.status,args.log,args.port,args.max_restarts)
    except (RuntimeError,ValueError,OSError) as exc:
        print("PUPPY50_V80_BRIDGE_FATAL="+str(exc),file=sys.stderr,flush=True)
        return 1
if __name__=="__main__":raise SystemExit(main())
