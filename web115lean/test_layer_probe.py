import unittest
from layer_probe import patch_migrate

class LayerProbeTests(unittest.TestCase):
 def test_inserts_nonblocking_loop_diagnostic_without_changing_guard_or_copy(self):
  src='head\n"$B" sleep 8\nemit P50_STAGE_START\n[ "$mem_k" -ge $((need_k + 393216)) ] || fail\ncopy\n'
  out=patch_migrate(src)
  self.assertIn('P50_V114_LAYER_PROBE_BEGIN',out);self.assertIn('/sys/block/loop*/loop/backing_file',out)
  self.assertIn('"$B" sleep 8\nemit P50_STAGE_START\n',out);self.assertIn('[ "$mem_k" -ge $((need_k + 393216)) ]',out)
  self.assertLess(out.index('P50_V114_LAYER_PROBE_BEGIN'),out.index('emit P50_STAGE_START'))
 def test_refuses_missing_duplicate_and_already_patched_hook(self):
  marker='"$B" sleep 8\nemit P50_STAGE_START\n'
  for text in ('wrong',marker+marker,'P50_V114_LAYER_PROBE_BEGIN\n'+marker):
   with self.subTest(text=text):
    with self.assertRaises(ValueError):patch_migrate(text)
if __name__=='__main__':unittest.main()
