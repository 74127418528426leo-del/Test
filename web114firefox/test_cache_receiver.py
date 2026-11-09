import http.client
import tempfile
import threading
import unittest
from pathlib import Path
from cache_receiver import make_server
class ReceiverTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.dest=Path(self.tmp.name)/'seed.bin';self.s=make_server(self.dest,port=0,max_bytes=16);self.t=threading.Thread(target=self.s.serve_forever,daemon=True);self.t.start()
    def tearDown(self):self.s.shutdown();self.s.server_close();self.t.join();self.tmp.cleanup()
    def post(self,path,data):
        c=http.client.HTTPConnection('127.0.0.1',self.s.server_port,timeout=3);c.request('POST',path,body=data);r=c.getresponse();status=r.status;r.read();c.close();return status
    def test_accepts_one_exact_cache_and_never_overwrites(self):
        self.assertEqual(self.post('/cache',b'first'),201);self.assertEqual(self.dest.read_bytes(),b'first');self.assertEqual(self.post('/cache',b'second'),409);self.assertEqual(self.dest.read_bytes(),b'first')
    def test_rejects_wrong_path_empty_and_excessive_content(self):
        self.assertEqual(self.post('/wrong',b'xx'),404);self.assertEqual(self.post('/cache',b''),400);self.assertEqual(self.post('/cache',b'x'*17),413);self.assertFalse(self.dest.exists())
if __name__=='__main__':unittest.main()
