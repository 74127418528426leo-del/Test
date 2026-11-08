import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.parse import urlencode
import video4k_fixture as fixture

class VideoFixtureTests(unittest.TestCase):
    def test_telemetry_and_partial_media_response(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);video=p/'sample.mp4';video.write_bytes(b'0123456789')
            telemetry=p/'telemetry.jsonl'
            server=fixture.make_server(0,video,telemetry)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            base='http://127.0.0.1:'+str(server.server_port)
            try:
                self.assertIn(b'getVideoPlaybackQuality',urlopen(base+'/').read())
                req=Request(base+'/sample.mp4',headers={'Range':'bytes=2-5'})
                with urlopen(req) as res:
                    self.assertEqual(res.status,206)
                    self.assertEqual(res.read(),b'2345')
                d=dict(width=3840,height=2160,wall_ms=1000,media_time=1.25,total_frames=24,dropped_frames=2,ready_state=4,paused=0)
                self.assertEqual(urlopen(base+'/telemetry?'+urlencode(d)).status,200)
                self.assertEqual(json.loads(telemetry.read_text()),d)
            finally:
                server.shutdown();thread.join();server.server_close()

if __name__=='__main__':unittest.main()
