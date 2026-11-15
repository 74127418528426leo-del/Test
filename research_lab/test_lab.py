"""No-network regression tests for the Puppy50 research planner."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import lab

class LabTests(unittest.TestCase):
    def test_128_slots_and_roles(self):
        tasks=lab.task_grid()
        self.assertEqual(len(tasks),128)
        self.assertEqual(len({x["task_id"] for x in tasks}),128)
        self.assertEqual(len({x["role"] for x in tasks}),8)

    def test_reject_untrusted_code_and_invalid_parameters(self):
        self.assertRaises(ValueError,lab.validate,{"nice":0,"zstd":3,"hypothesis":"not safe"})
        self.assertRaises(ValueError,lab.validate,{"nice":True,"zstd":3,"hypothesis":"not safe"})
        self.assertRaises(ValueError,lab.validate,{"nice":-10,"zstd":9,"hypothesis":"not safe"})
        self.assertRaises(ValueError,lab.validate,{"nice":-10,"zstd":3,"hypothesis":"x"})
        self.assertRaises(ValueError,lab.validate,{"nice":-10,"zstd":3,
            "hypothesis":"valid string","architecture_idea":"x"*701})

    def test_no_automatic_llm_connection(self):
        with patch.dict("os.environ",{},clear=True):
            self.assertRaises(ValueError,lab.OpenAI,"gpt-6-luna",None)

    def test_deterministic_offline_output_is_never_claimed_as_ai(self):
        with tempfile.TemporaryDirectory() as td:
            output=Path(td)/"output"
            command=[sys.executable,str(Path(lab.__file__)),"--output",str(output)]
            subprocess.run(command,check=True,capture_output=True,text=True)
            report=json.loads((output/"summary.json").read_text())
            queue=json.loads((output/"queue.json").read_text())
            self.assertEqual(report["mode"],"OFFLINE_NO_AI")
            self.assertEqual(report["task_slots_planned"],128)
            self.assertEqual(report["real_ai_agent_sessions_confirmed"],0)
            self.assertEqual(report["real_VM_boots_executed_by_this_workflow"],0)
            self.assertEqual(len(queue["candidates"]),8)
            self.assertEqual(len({x["id"] for x in queue["candidates"]}),8)
            self.assertTrue(all(x["source"]=="deterministic_scheduler"
                                for x in queue["candidates"]))

    def test_queue_deduplicates_and_history_skips_tested(self):
        first=lab.deterministic_hypotheses(set(),[],3)
        self.assertEqual(len(first),3)
        taken={lab.candidate_key(x) for x in first}
        second=lab.deterministic_hypotheses(taken,[],3)
        q=lab.merge_queue({"candidates":first},second)
        self.assertEqual(len(q["candidates"]),6)
        self.assertEqual(len({x["id"] for x in q["candidates"]}),6)
        hist=[{"candidate_id":x["id"]} for x in q["candidates"]]
        remaining=lab.deterministic_hypotheses(set(),hist,1)
        self.assertNotIn(remaining[0]["id"],{x["id"] for x in q["candidates"]})

    def test_max_model_calls_must_not_overrun(self):
        class Provider:
            def __init__(self): self.calls=0
            def call(self,inst,prompt,max_tokens=500):
                self.calls+=1
                if "independent OS-experiment safety reviewer" in inst:
                    return {"approve":True,"reason":"allowlisted"}
                n=[-10,-9,-11,-8][min(self.calls-1,3)]
                return {"nice":n,"zstd":3,"hypothesis":"Try one strictly bounded candidate."}
        p=Provider()
        # Duplicated proposals are acceptable rejection, but never exceed 8 calls.
        accepted,errors=lab.ai_hypotheses(p,lab.task_grid(),set(),[],4,8,4)
        self.assertLessEqual(p.calls,8)
        self.assertTrue(all(x["source"]=="openai_model" for x in accepted))

if __name__=="__main__":
    unittest.main()
