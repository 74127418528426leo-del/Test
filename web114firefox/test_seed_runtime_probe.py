import subprocess
import unittest
from seed_runtime_probe import instrument


class SeedRuntimeProbeTests(unittest.TestCase):
    def test_preserves_single_migration_marker_and_is_shell(self):
        source = '#!/bin/sh\n"$B" sleep 8\nemit P50_STAGE_START\n'
        result = instrument(source)
        self.assertIn('P50_V114_SEED_MAPPING_OK', result)
        self.assertIn('"$B" sleep 8\nemit P50_STAGE_START\n', result)
        check = subprocess.run(['sh', '-n'], input=result, text=True, capture_output=True)
        self.assertEqual(check.returncode, 0, check.stderr)
        with self.assertRaises(ValueError):
            instrument(result)

    def test_rejects_missing_or_multiple_markers(self):
        marker='"$B" sleep 8\nemit P50_STAGE_START\n'
        for text in ('missing', marker + marker):
            with self.assertRaises(ValueError):
                instrument(text)
