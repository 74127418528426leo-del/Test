#!/usr/bin/env python3
"""Serve one local 4K test clip and save first-party browser playback metrics."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import threading
from urllib.parse import parse_qs, urlsplit

HTML = b'''<!doctype html><html><head><meta charset="utf-8"><title>Puppy50 local 4K test</title>
<style>body{margin:0;background:#111;color:white;font:18px sans-serif}video{display:block;width:100%;height:calc(100vh - 65px);object-fit:contain}p{margin:12px}</style></head>
<body><p id="stats">Synthetic local 4K test: loading...</p><video id="v" muted autoplay playsinline loop src="/sample.mp4"></video>
<script>
const v=document.getElementById('v'), label=document.getElementById('stats');
v.play().catch(e=>{label.textContent='Playback request failed: '+e.name;});
setInterval(()=>{let q=v.getVideoPlaybackQuality();let d={width:v.videoWidth,height:v.videoHeight,
 wall_ms:Math.round(performance.now()),media_time:v.currentTime,total_frames:q.totalVideoFrames,
 dropped_frames:q.droppedVideoFrames,ready_state:v.readyState,paused:Number(v.paused)};
 label.textContent=`Synthetic local video ${d.width}x${d.height} | time ${d.media_time.toFixed(1)} s | decoded ${d.total_frames} | dropped ${d.dropped_frames}`;
 fetch('/telemetry?'+new URLSearchParams(d),{cache:'no-store'}).catch(()=>{});},1000);
</script></body></html>'''


def make_server(port, video, telemetry):
    lock=threading.Lock()
    class Handler(BaseHTTPRequestHandler):
        def send_bytes(self, status, payload, content_type):
            self.send_response(status);self.send_header('Content-Type',content_type)
            self.send_header('Content-Length',str(len(payload)));self.send_header('Cache-Control','no-store')
            self.end_headers();self.wfile.write(payload)
        def do_GET(self):
            u=urlsplit(self.path)
            if u.path=='/':
                self.send_bytes(200,HTML,'text/html; charset=utf-8');return
            if u.path=='/telemetry':
                values=parse_qs(u.query)
                try:
                    row={key: (float(values[key][0]) if key=='media_time' else int(values[key][0]))
                         for key in ('width','height','wall_ms','media_time','total_frames','dropped_frames','ready_state','paused')}
                except (KeyError,ValueError,IndexError):
                    self.send_bytes(400,b'invalid telemetry','text/plain');return
                with lock:
                    with telemetry.open('a') as f:f.write(json.dumps(row,sort_keys=True)+'\n')
                self.send_bytes(200,b'ok','text/plain');return
            if u.path!='/sample.mp4':
                self.send_bytes(404,b'not found','text/plain');return
            size=video.stat().st_size;start=0;end=size-1;status=200
            raw=self.headers.get('Range')
            if raw:
                match=re.fullmatch(r'bytes=(\d+)-(\d*)',raw)
                if not match:
                    self.send_bytes(416,b'invalid range','text/plain');return
                start=int(match.group(1));end=min(int(match.group(2)) if match.group(2) else end,end);status=206
                if start>end:
                    self.send_bytes(416,b'invalid range','text/plain');return
            self.send_response(status);self.send_header('Content-Type','video/mp4')
            self.send_header('Accept-Ranges','bytes');self.send_header('Content-Length',str(end-start+1))
            self.send_header('Cache-Control','no-store')
            if status==206:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
            self.end_headers()
            with video.open('rb') as f:
                f.seek(start);remaining=end-start+1
                while remaining:
                    chunk=f.read(min(262144,remaining))
                    if not chunk:break
                    try:self.wfile.write(chunk)
                    except (BrokenPipeError,ConnectionResetError):break
                    remaining-=len(chunk)
    return ThreadingHTTPServer(('127.0.0.1',port),Handler)


def main():
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8766)
    p.add_argument('--video',type=Path,required=True);p.add_argument('--telemetry',type=Path,required=True)
    a=p.parse_args()
    if not a.video.is_file():raise ValueError('Test video does not exist')
    make_server(a.port,a.video,a.telemetry).serve_forever()

if __name__=='__main__':main()
