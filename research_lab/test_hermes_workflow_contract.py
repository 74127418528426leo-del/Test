"""Catch expensive Hermes workspace/configuration mistakes before model startup."""
from pathlib import Path
import unittest


WORKFLOW = (
    Path(__file__).resolve().parents[1]
    / ".github/workflows/puppy50-hermes-qwen-agent-pilot.yml"
)


class HermesWorkflowContractTests(unittest.TestCase):
    def test_workspace_is_minimal_and_configured_before_model_download(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        prepare = workflow.split(
            "- name: Prepare minimal credential-free Hermes/Qwen review packet", 1
        )[1].split("- name: Restore or cache pinned Qwen3.5 reviewer", 1)[0]
        cwd_line = 'cwd: "$GITHUB_WORKSPACE/agent-work"'
        self.assertIn("terminal:", prepare)
        self.assertIn(cwd_line, prepare)
        self.assertIn('Path("agent-work/packet.json")', prepare)
        self.assertIn("path packet.json", prepare)
        self.assertNotIn("git archive HEAD", prepare)
        self.assertLess(
            workflow.index(cwd_line),
            workflow.index("- name: Download and verify pinned Qwen3.5 reviewer"),
        )
        self.assertNotIn("TERMINAL_CWD=", workflow)


if __name__ == "__main__":
    unittest.main()
