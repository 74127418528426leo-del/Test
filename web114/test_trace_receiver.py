import http.client
import tempfile
import threading
import unittest
from pathlib import Path
from trace_receiver import make_server

class TraceReceiverTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.target=Path(self.tmp.name)/'trace.tsv'
        self.server=make_server(self.target,host='127.0.0.1',port=0,max_bytes=32)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()
    def post(self,path,data):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=3)
        conn.request('POST',path,body=data,headers={'Content-Type':'text/plain'});res=conn.getresponse();result=res.status;res.read();conn.close();return result
    def test_writes_one_exact_trace_without_overwriting(self):
        self.assertEqual(self.post('/trace',b'EV\t1\n'),201)
        self.assertEqual(self.target.read_bytes(),b'EV\t1\n')
        self.assertEqual(self.post('/trace',b'changed'),409)
        self.assertEqual(self.target.read_bytes(),b'EV\t1\n')
    def test_rejects_wrong_path_empty_body_and_oversize(self):
        self.assertEqual(self.post('/other',b'x'),404)
        self.assertEqual(self.post('/trace',b''),400)
        self.assertEqual(self.post('/trace',b'x'*33),413)
        self.assertFalse(self.target.exists())

if __name__=='__main__':unittest.main()
