import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.apply_mat_sab_candidate_gate import apply_gate
from scripts.mat_sab_research_state import validate_state
from scripts.run_candidate_a_star_cycle_gate import ADMIT, REJECT


ROOT = Path(__file__).resolve().parents[2]
HYPOTHESIS_MARKER = "H_candidate_a_star_cycle_mechanism:"
RUN_MARKER = "candidate-a-star-cycle-gate-001"
MANIFEST_MARKER = "<!-- candidate-a-star-cycle-gate-manifest -->"
CHECKLIST_MARKER = "<!-- candidate-a-star-cycle-gate-checklist -->"


class CandidateACloseoutTests(unittest.TestCase):
    def _make_root(self, directory: str) -> tuple[Path, Path]:
        root = Path(directory)
        (root / "hypotheses").mkdir()
        (root / "repro").mkdir()
        state = json.loads((ROOT / "research_state.yaml").read_text(encoding="ascii"))
        state["goal_status"] = "ACTIVE"
        state["paper_gate"] = "BLOCKED"
        state["production_hot_path_permission"] = False
        state["active_candidate"] = "A"
        state["candidates"]["A"]["status"] = "EQUATIONS_DEFINED"
        state["candidates"]["B"]["status"] = "QUEUED"
        state["candidates"]["C"]["status"] = "QUEUED"
        state["last_decision"] = "CANDIDATE_A_PRODUCTION_EQUATIONS_DEFINED"
        state_path = root / "research_state.yaml"
        state_path.write_text(
            json.dumps(state, indent=2) + "\n",
            encoding="ascii",
            newline="\n",
        )
        (root / "repro/run_log.csv").write_text(
            "run_id,date,commit_or_state,stage,backend,command,params,seed,"
            "status,summary,artifacts\n",
            encoding="ascii",
            newline="\n",
        )
        return root, state_path

    def _write_summary(self, root: Path, decisions: list[str]) -> Path:
        summary = root / "summary.csv"
        with summary.open("w", newline="", encoding="ascii") as handle:
            writer = csv.DictWriter(handle, fieldnames=["decision"])
            writer.writeheader()
            writer.writerows({"decision": decision} for decision in decisions)
        return summary

    def _tracked_outputs(self, root: Path, state_path: Path) -> dict[Path, bytes]:
        paths = (
            state_path,
            root / "hypotheses/hypothesis_register.yaml",
            root / "repro/run_log.csv",
            root / "repro/artifact_manifest.md",
            root / "repro/reproduction_checklist.md",
        )
        return {path: path.read_bytes() for path in paths}

    def _assert_markers_once(self, root: Path) -> None:
        markers = (
            (root / "hypotheses/hypothesis_register.yaml", HYPOTHESIS_MARKER),
            (root / "repro/run_log.csv", RUN_MARKER),
            (root / "repro/artifact_manifest.md", MANIFEST_MARKER),
            (root / "repro/reproduction_checklist.md", CHECKLIST_MARKER),
        )
        for path, marker in markers:
            with self.subTest(path=path.name, marker=marker):
                self.assertEqual(path.read_text(encoding="ascii").count(marker), 1)

    def test_reject_decision_activates_b_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            summary = self._write_summary(root, [REJECT])

            first = apply_gate(root, state_path, summary)
            after_first = self._tracked_outputs(root, state_path)
            second = apply_gate(root, state_path, summary)
            changed = json.loads(state_path.read_text(encoding="ascii"))

            self.assertEqual(first, REJECT)
            self.assertEqual(second, REJECT)
            self.assertEqual(after_first, self._tracked_outputs(root, state_path))
            self.assertEqual(changed["candidates"]["A"]["status"], "REJECTED")
            self.assertEqual(changed["candidates"]["B"]["status"], "INTAKE")
            self.assertEqual(changed["candidates"]["C"]["status"], "QUEUED")
            self.assertEqual(changed["active_candidate"], "B")
            self.assertEqual(changed["goal_status"], "ACTIVE")
            self.assertEqual(changed["paper_gate"], "BLOCKED")
            self.assertFalse(changed["production_hot_path_permission"])
            self.assertEqual(changed["last_decision"], REJECT)
            validate_state(changed)
            self._assert_markers_once(root)

    def test_admit_decision_advances_only_to_adversarial_checker_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            summary = self._write_summary(root, [ADMIT])

            self.assertEqual(apply_gate(root, state_path, summary), ADMIT)
            changed = json.loads(state_path.read_text(encoding="ascii"))

            self.assertEqual(
                changed["candidates"]["A"]["status"],
                "ADVERSARIAL_CHECKER_PASS",
            )
            self.assertEqual(changed["candidates"]["B"]["status"], "QUEUED")
            self.assertEqual(changed["candidates"]["C"]["status"], "QUEUED")
            self.assertEqual(changed["active_candidate"], "A")
            self.assertEqual(changed["goal_status"], "ACTIVE")
            self.assertEqual(changed["paper_gate"], "BLOCKED")
            self.assertFalse(changed["production_hot_path_permission"])
            self.assertEqual(changed["last_decision"], ADMIT)
            validate_state(changed)
            self._assert_markers_once(root)

    def test_malformed_or_unknown_summary_is_rejected_before_mutation(self):
        malformed_rows = ([], [REJECT, REJECT], ["UNKNOWN_DECISION"])
        for decisions in malformed_rows:
            with self.subTest(decisions=decisions):
                with tempfile.TemporaryDirectory() as tmp:
                    root, state_path = self._make_root(tmp)
                    summary = self._write_summary(root, decisions)
                    state_before = state_path.read_bytes()
                    run_log_before = (root / "repro/run_log.csv").read_bytes()

                    with self.assertRaisesRegex(
                        ValueError,
                        "summary must contain one recognized decision",
                    ):
                        apply_gate(root, state_path, summary)

                    self.assertEqual(state_path.read_bytes(), state_before)
                    self.assertEqual(
                        (root / "repro/run_log.csv").read_bytes(),
                        run_log_before,
                    )
                    self.assertFalse(
                        (root / "hypotheses/hypothesis_register.yaml").exists()
                    )
                    self.assertFalse((root / "repro/artifact_manifest.md").exists())
                    self.assertFalse(
                        (root / "repro/reproduction_checklist.md").exists()
                    )

    def test_state_decision_mismatch_is_rejected_before_ledger_updates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            state = json.loads(state_path.read_text(encoding="ascii"))
            state["candidates"]["A"]["status"] = "ADVERSARIAL_CHECKER_PASS"
            state["last_decision"] = ADMIT
            state_path.write_text(
                json.dumps(state, indent=2) + "\n",
                encoding="ascii",
                newline="\n",
            )
            summary = self._write_summary(root, [REJECT])
            state_before = state_path.read_bytes()

            with self.assertRaisesRegex(ValueError, "state/decision mismatch"):
                apply_gate(root, state_path, summary)

            self.assertEqual(state_path.read_bytes(), state_before)
            self.assertFalse(
                (root / "hypotheses/hypothesis_register.yaml").exists()
            )
            self.assertNotIn(
                RUN_MARKER,
                (root / "repro/run_log.csv").read_text(encoding="ascii"),
            )
            self.assertFalse((root / "repro/artifact_manifest.md").exists())
            self.assertFalse((root / "repro/reproduction_checklist.md").exists())


if __name__ == "__main__":
    unittest.main()
