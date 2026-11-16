"""Unit tests for the bounded Qwen tool-call protocol probe."""
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location(
    "qwen_toolcall_probe", Path(__file__).with_name("qwen_toolcall_probe.py")
)
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


def response(name=None, args=None, calls=None):
    if calls is None:
        calls = [{"function": {
            "name": name or probe.TOOL,
            "arguments": args if args is not None else '{"path":"probe.txt"}',
        }}]
    return {"choices": [{"message": {"tool_calls": calls}}]}


class QwenToolCallProbeTests(unittest.TestCase):
    def test_payload_forces_one_bounded_nonexecuting_tool(self):
        p = probe.payload()
        self.assertEqual(p["tool_choice"], "required")
        self.assertEqual(len(p["tools"]), 1)
        self.assertEqual(p["max_tokens"], 128)
        schema = p["tools"][0]["function"]["parameters"]
        self.assertEqual(schema["properties"]["path"]["enum"], ["probe.txt"])
        self.assertFalse(schema["additionalProperties"])

    def test_accepts_expected_call_with_json_string_args(self):
        self.assertEqual(probe.parse_response(response()), {
            "name": probe.TOOL, "arguments": {"path": "probe.txt"}
        })

    def test_accepts_expected_call_with_object_args(self):
        self.assertEqual(
            probe.parse_response(response(args={"path": "probe.txt"}))["arguments"],
            {"path": "probe.txt"},
        )

    def test_rejects_plain_text(self):
        with self.assertRaisesRegex(ValueError, "no single"):
            probe.parse_response({"choices": [{"message": {"content": "read it"}}]})

    def test_rejects_wrong_name_path_extra_args_and_multiple_calls(self):
        cases = [
            response(name="terminal"),
            response(args='{"path":"/etc/passwd"}'),
            response(args='{"path":"probe.txt","command":"id"}'),
            response(calls=[{}, {}]),
        ]
        for item in cases:
            with self.subTest(item=item), self.assertRaises(ValueError):
                probe.parse_response(item)

    def test_rejects_malformed_arguments(self):
        with self.assertRaisesRegex(ValueError, "invalid JSON"):
            probe.parse_response(response(args="{bad"))

    def test_template_properties_are_diagnostic_only(self):
        self.assertEqual(
            probe.template_capabilities({
                "chat_template": "x",
                "chat_template_tool_use": "y",
            }),
            {"chat_template_available": True, "tool_template_available": True},
        )
        self.assertEqual(
            probe.template_capabilities({}),
            {"chat_template_available": False, "tool_template_available": False},
        )


if __name__ == "__main__":
    unittest.main()
