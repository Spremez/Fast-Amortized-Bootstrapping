from dataclasses import replace
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import scripts.apply_candidate_d_admission as closeout
from scripts.mat_sab_research_state import load_state, validate_state, write_state
from scripts.run_candidate_d_admission import (
    ADMIT,
    BLOCK,
    evaluate_candidate_d_admission,
)


ROOT = Path(__file__).resolve().parents[2]
RUN_HEADER = (ROOT / "repro/run_log.csv").read_text(encoding="ascii").splitlines()[0]


class CandidateDCloseoutTests(unittest.TestCase):
    def setUp(self):
        self.result = evaluate_candidate_d_admission(ROOT)
        self.assertEqual(self.result.decision, BLOCK)

    def _root(self, directory: str) -> Path:
        root = Path(directory)
        (root / "hypotheses").mkdir(parents=True)
        (root / "repro").mkdir(parents=True)
        (root / "hypotheses/hypothesis_register.yaml").write_bytes(
            b"# hypotheses\n"
        )
        (root / "repro/artifact_manifest.md").write_bytes(b"# artifacts\n")
        (root / "repro/reproduction_checklist.md").write_bytes(
            b"# checklist\n"
        )
        (root / "repro/run_log.csv").write_bytes(
            (RUN_HEADER + "\n").encode("ascii")
        )
        state = load_state(ROOT / "research_state.yaml")
        state["goal_status"] = "ACTIVE"
        state["active_candidate"] = "D"
        state["paper_gate"] = "BLOCKED"
        state["production_hot_path_permission"] = False
        state["last_decision"] = "PASS_D0_CANDIDATE_D_BASELINES_FROZEN"
        state["last_decision_source_status"] = "PLAN_APPROVED"
        state["candidates"]["D"]["status"] = "D0_BASELINE_FROZEN"
        state["candidates"]["D"]["last_reached_status"] = "D0_BASELINE_FROZEN"
        state["candidates"]["E"]["status"] = "RESERVED_FALLBACK_NOT_STARTED"
        state["candidates"]["E"]["last_reached_status"] = (
            "RESERVED_FALLBACK_NOT_STARTED"
        )
        write_state(root / "research_state.yaml", state)
        return root

    def _apply(self, root: Path, result=None) -> str:
        selected = self.result if result is None else result
        with patch.object(closeout, "verify_candidate_d_artifacts", return_value=selected):
            return closeout.apply_candidate_d_decision(root, selected)

    @staticmethod
    def _snapshot(root: Path) -> dict[str, bytes]:
        paths = (
            "research_state.yaml",
            "hypotheses/hypothesis_register.yaml",
            "repro/artifact_manifest.md",
            "repro/reproduction_checklist.md",
            "repro/run_log.csv",
        )
        return {path: (root / path).read_bytes() for path in paths}

    def test_block_preserves_d0_and_does_not_activate_e(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            self.assertEqual(self._apply(root), BLOCK)
            state = load_state(root / "research_state.yaml")
            self.assertEqual(state["goal_status"], "EXTERNAL_BLOCKED")
            self.assertEqual(state["active_candidate"], "D")
            self.assertEqual(state["paper_gate"], "BLOCKED")
            self.assertFalse(state["production_hot_path_permission"])
            self.assertEqual(
                state["candidates"]["D"]["status"],
                "D0_BASELINE_FROZEN",
            )
            self.assertEqual(
                state["candidates"]["D"]["last_reached_status"],
                "D0_BASELINE_FROZEN",
            )
            self.assertEqual(
                state["candidates"]["E"]["status"],
                "RESERVED_FALLBACK_NOT_STARTED",
            )
            self.assertEqual(state["last_decision"], BLOCK)
            self.assertEqual(
                state["last_decision_source_status"],
                "D0_BASELINE_FROZEN",
            )
            validate_state(state)

    def test_identical_second_apply_is_byte_for_byte_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            self._apply(root)
            first = self._snapshot(root)
            self._apply(root)
            self.assertEqual(self._snapshot(root), first)
            for relative in (
                "hypotheses/hypothesis_register.yaml",
                "repro/artifact_manifest.md",
                "repro/reproduction_checklist.md",
            ):
                text = (root / relative).read_text(encoding="ascii")
                self.assertEqual(text.count("candidate-d-admission"), 2)
            run_log = (root / "repro/run_log.csv").read_text(encoding="ascii")
            self.assertEqual(run_log.count(closeout.RUN_MARKER), 1)

    def test_divergent_second_apply_is_rejected_without_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            self._apply(root)
            before = self._snapshot(root)
            divergent = replace(
                self.result,
                d1_status="PASS",
                d1_decision=(
                    "PASS_D1_DISTINCT_SAB_OPERATOR_CLAIM_REMAINS_TESTABLE"
                ),
                d1_missing_evidence=(),
                d2_status="PASS",
                d2_decision="PASS_D2_OPERATOR_CLOSURE_G_LE_4",
                gamma_count=2,
                negative_controls_status="PASS",
                binding_status="PASS",
                security_status="PASS",
                noise_status="PASS",
                complete_cost_status="PASS",
                resource_status="PASS",
                pessimistic_projection="1.10",
                decision=ADMIT,
                resume_condition="none",
            )
            with self.assertRaises(ValueError):
                self._apply(root, divergent)
            self.assertEqual(self._snapshot(root), before)

    def test_partial_or_changed_ledger_marker_is_rejected(self):
        cases = (
            closeout.HYPOTHESIS_START + "\n",
            (
                closeout.HYPOTHESIS_START
                + "\nchanged\n"
                + closeout.HYPOTHESIS_END
                + "\n"
            ),
        )
        for content in cases:
            with self.subTest(content=content):
                with tempfile.TemporaryDirectory() as directory:
                    root = self._root(directory)
                    path = root / "hypotheses/hypothesis_register.yaml"
                    path.write_text(content, encoding="ascii")
                    before = self._snapshot(root)
                    with self.assertRaises(ValueError):
                        self._apply(root)
                    self.assertEqual(self._snapshot(root), before)

    def test_run_log_marker_with_different_content_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            run_log = root / "repro/run_log.csv"
            run_log.write_text(
                RUN_HEADER + "\n" + closeout.RUN_MARKER + ",changed\n",
                encoding="ascii",
            )
            before = self._snapshot(root)
            with self.assertRaises(ValueError):
                self._apply(root)
            self.assertEqual(self._snapshot(root), before)

    def test_write_failure_rolls_back_all_closeout_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            before = self._snapshot(root)
            original = closeout._write_bytes_atomic
            calls = 0

            def fail_on_third(path, content):
                nonlocal calls
                calls += 1
                if calls == 3:
                    raise OSError("injected write failure")
                return original(path, content)

            with patch.object(
                closeout,
                "verify_candidate_d_artifacts",
                return_value=self.result,
            ), patch.object(closeout, "_write_bytes_atomic", side_effect=fail_on_third):
                with self.assertRaisesRegex(OSError, "injected"):
                    closeout.apply_candidate_d_decision(root, self.result)
            self.assertEqual(self._snapshot(root), before)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_symlinked_ledger_parent_outside_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = self._root(str(base / "repo"))
            outside = base / "outside"
            outside.mkdir()
            hypotheses = root / "hypotheses"
            for child in hypotheses.iterdir():
                child.unlink()
            hypotheses.rmdir()
            try:
                hypotheses.symlink_to(outside, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"directory symlinks unavailable: {error}")
            with self.assertRaises(ValueError):
                self._apply(root)
            self.assertEqual(tuple(outside.iterdir()), ())

    def test_closeout_text_is_ascii_and_names_exact_resume_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            self._apply(root)
            for relative in (
                "hypotheses/hypothesis_register.yaml",
                "repro/artifact_manifest.md",
                "repro/reproduction_checklist.md",
                "repro/run_log.csv",
            ):
                data = (root / relative).read_bytes()
                data.decode("ascii")
                self.assertNotIn(b"\r", data)
            joined = "\n".join(
                (root / relative).read_text(encoding="ascii")
                for relative in (
                    "hypotheses/hypothesis_register.yaml",
                    "repro/reproduction_checklist.md",
                )
            )
            self.assertIn("NTRU_AMORT_2026_068", joined)
            self.assertIn("NTRU_AMORT_FULLTEXT_PATH", joined)
            self.assertNotIn("Candidate E is active", joined)


if __name__ == "__main__":
    unittest.main()
