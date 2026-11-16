"""The coding-model probe must never execute returned code."""
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parent / "coder_smoke.py"


class CoderSmokeTests(unittest.TestCase):
    def module(self):
        self.assertTrue(PATH.is_file())
        spec = importlib.util.spec_from_file_location("coder_smoke", PATH)
        obj = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(obj)
        return obj

    def test_recognizes_exact_small_function_without_executing(self):
        m = self.module()
        answer = "```python\ndef below_five(seconds):\n    return 0 < seconds < 5\n```"
        result = m.inspect_response(answer, m.TASKS[0]["expected"])
        self.assertTrue(result["exact_ast_match"])
        self.assertFalse(result["model_code_executed"])

    def test_rejects_extraneous_statements_and_oversized_response(self):
        m = self.module()
        bad = "import os\ndef below_five(seconds):\n    return 0 < seconds < 5"
        self.assertFalse(m.inspect_response(bad, m.TASKS[0]["expected"])["exact_ast_match"])
        self.assertFalse(m.inspect_response("x" * 20000, m.TASKS[0]["expected"])["exact_ast_match"])


if __name__ == "__main__":
    unittest.main()
