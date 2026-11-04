#!/usr/bin/env python3
"""Actual Pexels 3840x2160 original MP4 embedded in Firefox native HTML5 <video>.
Pexels serves direct file as Content-Disposition: attachment; embedding inside an
in-memory data: document avoids download-only navigation while fetching the same
public file with normal HTTPS certificate checks.

No page impersonation: test harness is explicitly identified and no credentials
or third-party resources beyond the original Pexels video are requested.
"""
import base64,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from web102 import pexels_kvm

DIRECT_MP4="https://videos.pexels.com/video-files/27251986/12102943_3840_2160_30fps.mp4"
HTML="""<!doctype html><meta charset=utf-8><style>body{background:#001522;color:#fff;font:23px sans-serif}video{width:100%;height:69vh;background:#000}p{padding:6px}</style><h2>Puppy50 / actual Pexels 3840x2160 original video</h2><video controls autoplay muted playsinline src='"""+DIRECT_MP4+"""'></video><p id=s>Loading native source video...</p><script>setInterval(function(){var v=document.querySelector('video'),q=v.getVideoPlaybackQuality();s.textContent='decoded='+v.videoWidth+'x'+v.videoHeight+' time='+v.currentTime.toFixed(1)+' ready='+v.readyState+' frames='+q.totalVideoFrames+' dropped='+q.droppedVideoFrames+' error='+(v.error?v.error.code:0)},1000)</script>"""
DATA_URL="data:text/html;base64,"+base64.b64encode(HTML.encode()).decode()
pexels_kvm.URL=DATA_URL
def navigate_embedded_4k(mon):
    pexels_kvm.send_key(mon,['ctrl','l'],125)
    time.sleep(1)
    pexels_kvm.type_text(mon,DATA_URL,.042)
    pexels_kvm.send_key(mon,['ret'],120)
pexels_kvm.navigation=navigate_embedded_4k
if __name__=="__main__":
    pexels_kvm.main()
