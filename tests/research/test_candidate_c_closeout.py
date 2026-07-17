import csv
from dataclasses import replace
import importlib
import inspect
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.mat_sab_research_state import validate_state
import scripts.run_candidate_c_rank_bounded_gate as gate


ROOT = Path(__file__).resolve().parents[2]
RUN_MARKER = "candidate-c-rank-bounded-gate-001"
HYPOTHESIS_START = "# candidate-c-rank-bounded-gate-hypothesis-start"
HYPOTHESIS_END = "# candidate-c-rank-bounded-gate-hypothesis-end"
MANIFEST_START = "<!-- candidate-c-rank-bounded-gate-manifest-start -->"
MANIFEST_END = "<!-- candidate-c-rank-bounded-gate-manifest-end -->"
CHECKLIST_START = "<!-- candidate-c-rank-bounded-gate-checklist-start -->"
CHECKLIST_END = "<!-- candidate-c-rank-bounded-gate-checklist-end -->"
PREDECESSOR = "REJECT_CANDIDATE_B_EXACT_STANDARD_PVW_FACTORIZATION_ROUTE_TO_C"


def load_closeout():
    return importlib.import_module(
        "scripts.apply_candidate_c_rank_bounded_gate"
    )


def fixture_raw_evidence(decision):
    mechanism = gate.MechanismEvaluation(
        mechanism_id="C1",
        registered=True,
        source_status="PASS",
        equation_status="PASS",
        symbolic_independence_status="PASS",
        phase_status="PASS",
        schedule_status="PASS",
        rank_status="PASS",
        max_rho=2,
        compression_status="PASS",
        compression_interval=4,
        b_min=4,
        closed_next_state_consumption=True,
        structural_cost_status="PASS",
        complete_cost_status="PASS",
        complete_cost=100.0,
        amdahl_status="PASS",
        amdahl_projection=1.01,
        amdahl_pessimistic_projection=0.0,
        fully_evaluated=True,
        failure_reason="",
        object_hashes=("1" * 64,),
    )
    if decision == gate.ADMIT:
        classification = "ADMIT"
        terminal_decision = "ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY"
        exhausted = False
        replay_status = "PASS"
        task3b_status = "PASS"
        task4_status = "PASS"
    elif decision == gate.REJECT:
        classification = "REJECT"
        terminal_decision = (
            "REJECT_C1_NEGATIVE_PESSIMISTIC_AMDAHL_PROJECTION_TERMINAL"
        )
        exhausted = False
        replay_status = "PASS"
        task3b_status = "PASS"
        task4_status = "PASS"
        mechanism = replace(
            mechanism,
            amdahl_pessimistic_projection=-0.01,
            failure_reason=terminal_decision,
        )
    elif decision == gate.INCONCLUSIVE:
        classification = "INCONCLUSIVE"
        terminal_decision = (
            "TERMINAL_INCONCLUSIVE_C1_EVIDENCE_EXHAUSTED"
        )
        exhausted = True
        replay_status = gate.SKIPPED
        task3b_status = "EVIDENCE_EXHAUSTED"
        task4_status = gate.SKIPPED
        mechanism = replace(
            mechanism,
            registered=False,
            symbolic_independence_status="EVIDENCE_EXHAUSTED",
            phase_status="EVIDENCE_EXHAUSTED",
            schedule_status="EVIDENCE_EXHAUSTED",
            rank_status="EVIDENCE_EXHAUSTED",
            compression_status="EVIDENCE_EXHAUSTED",
            compression_interval=0,
            closed_next_state_consumption=False,
            structural_cost_status="EVIDENCE_EXHAUSTED",
            complete_cost_status=gate.SKIPPED,
            complete_cost=None,
            amdahl_status=gate.SKIPPED,
            amdahl_projection=None,
            amdahl_pessimistic_projection=None,
            fully_evaluated=False,
            failure_reason=terminal_decision,
            object_hashes=(),
        )
    else:
        raise ValueError(decision)
    return gate.bind_fixture_decision_evidence(
        gate.RawDecisionEvidence(
            schema=gate.DECISION_EVIDENCE_SCHEMA,
            binding_kind=gate.FIXTURE_EVIDENCE,
            claimed_decision=decision,
            terminal_classification=classification,
            terminal_decision=terminal_decision,
            terminal_record_hash="",
            terminal_evidence_exhausted=exhausted,
            replay_status=replay_status,
            task3b_status=task3b_status,
            task4_status=task4_status,
            mechanisms=(mechanism,),
        )
    )


class CandidateCCloseoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.closeout = load_closeout()
        cls.input_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    @staticmethod
    def _make_root(directory):
        root = Path(directory)
        (root / "hypotheses").mkdir(parents=True)
        (root / "repro").mkdir()
        state = json.loads(
            (ROOT / "research_state.yaml").read_text(encoding="ascii")
        )
        state["goal_status"] = "ACTIVE"
        state["paper_gate"] = "BLOCKED"
        state["production_hot_path_permission"] = False
        state["active_candidate"] = "C"
        state["candidates"]["A"]["status"] = "REJECTED"
        state["candidates"]["B"]["status"] = "REJECTED"
        state["candidates"]["C"]["status"] = "INTAKE"
        state["last_decision"] = PREDECESSOR
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

    def _write_fixture_pack(self, root, raw):
        result = gate.gate_result_from_decision_evidence(
            raw,
            allow_fixture=True,
        )
        summary_record = gate.canonical_summary_record(
            result,
            root=root,
            input_commit=self.input_commit,
            allow_fixture=True,
        )
        summary = root / "summary.csv"
        with summary.open("w", newline="", encoding="ascii") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=gate.SUMMARY_FIELDS,
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerow(summary_record)
        evidence = root / "decision_evidence.json"
        evidence.write_text(
            gate.decision_evidence_json(raw),
            encoding="ascii",
            newline="\n",
        )
        return summary, evidence

    @staticmethod
    def _tracked(root, state_path):
        paths = (
            state_path,
            root / "hypotheses/hypothesis_register.yaml",
            root / "repro/run_log.csv",
            root / "repro/artifact_manifest.md",
            root / "repro/reproduction_checklist.md",
        )
        return {
            path: path.read_bytes() if path.exists() else None
            for path in paths
        }

    @staticmethod
    def _assert_markers_once(root):
        markers = (
            (root / "hypotheses/hypothesis_register.yaml", HYPOTHESIS_START),
            (root / "hypotheses/hypothesis_register.yaml", HYPOTHESIS_END),
            (root / "repro/run_log.csv", RUN_MARKER),
            (root / "repro/artifact_manifest.md", MANIFEST_START),
            (root / "repro/artifact_manifest.md", MANIFEST_END),
            (root / "repro/reproduction_checklist.md", CHECKLIST_START),
            (root / "repro/reproduction_checklist.md", CHECKLIST_END),
        )
        for path, marker in markers:
            with unittest.TestCase().subTest(path=path.name, marker=marker):
                text = path.read_text(encoding="ascii")
                unittest.TestCase().assertEqual(text.count(marker), 1)

    def _apply_twice(self, root, state_path, raw):
        summary, evidence = self._write_fixture_pack(root, raw)
        first = self.closeout.apply_gate(
            root,
            state_path,
            summary,
            input_commit=self.input_commit,
            evidence_path=evidence,
            allow_fixture=True,
        )
        after_first = self._tracked(root, state_path)
        second = self.closeout.apply_gate(
            root,
            state_path,
            summary,
            input_commit=self.input_commit,
            evidence_path=evidence,
            allow_fixture=True,
        )
        self.assertEqual(first, raw.claimed_decision)
        self.assertEqual(second, raw.claimed_decision)
        self.assertEqual(after_first, self._tracked(root, state_path))
        self._assert_markers_once(root)
        return json.loads(state_path.read_text(encoding="ascii"))

    def test_admit_fixture_pack_advances_only_to_adversarial_checker_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            state = self._apply_twice(
                root,
                state_path,
                fixture_raw_evidence(gate.ADMIT),
            )
        self.assertEqual(state["active_candidate"], "C")
        self.assertEqual(
            state["candidates"]["C"]["status"],
            "ADVERSARIAL_CHECKER_PASS",
        )
        self.assertEqual(state["goal_status"], "ACTIVE")
        self.assertEqual(state["paper_gate"], "BLOCKED")
        self.assertFalse(state["production_hot_path_permission"])
        self.assertEqual(state["last_decision"], gate.ADMIT)
        validate_state(state)

    def test_reject_after_cost_fixture_pack_exhausts_campaign(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            state = self._apply_twice(
                root,
                state_path,
                fixture_raw_evidence(gate.REJECT),
            )
        self.assertEqual(state["active_candidate"], "C")
        self.assertEqual(state["candidates"]["A"]["status"], "REJECTED")
        self.assertEqual(state["candidates"]["B"]["status"], "REJECTED")
        self.assertEqual(state["candidates"]["C"]["status"], "REJECTED")
        self.assertEqual(state["goal_status"], "RESEARCH_CAMPAIGN_EXHAUSTED")
        self.assertEqual(state["paper_gate"], "BLOCKED")
        self.assertFalse(state["production_hot_path_permission"])
        self.assertEqual(state["last_decision"], gate.REJECT)
        validate_state(state)

    def test_inconclusive_fixture_pack_closes_without_external_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            state = self._apply_twice(
                root,
                state_path,
                fixture_raw_evidence(gate.INCONCLUSIVE),
            )
        self.assertEqual(state["active_candidate"], "C")
        self.assertEqual(state["candidates"]["C"]["status"], "INCONCLUSIVE")
        self.assertEqual(
            state["goal_status"],
            "RESEARCH_CAMPAIGN_INCONCLUSIVE",
        )
        self.assertNotEqual(state["goal_status"], "EXTERNAL_BLOCKED")
        self.assertEqual(state["paper_gate"], "BLOCKED")
        self.assertFalse(state["production_hot_path_permission"])
        self.assertEqual(state["last_decision"], gate.INCONCLUSIVE)
        validate_state(state)

    def test_unrelated_noncanonical_legacy_row_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            run_log = root / "repro/run_log.csv"
            legacy = "legacy-stage,row-without-canonical-width\n"
            with run_log.open("a", encoding="ascii", newline="") as handle:
                handle.write(legacy)
            self._apply_twice(
                root,
                state_path,
                fixture_raw_evidence(gate.REJECT),
            )
            self.assertIn(legacy, run_log.read_text(encoding="ascii"))

    def test_marker_outside_canonical_run_id_is_rejected(self):
        rows = (
            (
                "other,2026-07-17,state,stage,backend,command,params,seed,"
                f"{RUN_MARKER},summary,artifacts\n"
            ),
            f"legacy,{RUN_MARKER},extra\n",
        )
        for row in rows:
            with self.subTest(row=row):
                with tempfile.TemporaryDirectory() as tmp:
                    root, state_path = self._make_root(tmp)
                    run_log = root / "repro/run_log.csv"
                    with run_log.open(
                        "a",
                        encoding="ascii",
                        newline="",
                    ) as handle:
                        handle.write(row)
                    summary, evidence = self._write_fixture_pack(
                        root,
                        fixture_raw_evidence(gate.REJECT),
                    )
                    before = self._tracked(root, state_path)
                    with self.assertRaisesRegex(
                        ValueError,
                        "run log rows must match canonical schema",
                    ):
                        self.closeout.apply_gate(
                            root,
                            state_path,
                            summary,
                            input_commit=self.input_commit,
                            evidence_path=evidence,
                            allow_fixture=True,
                        )
                    self.assertEqual(before, self._tracked(root, state_path))

    def test_summary_tamper_is_rejected_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            summary, evidence = self._write_fixture_pack(
                root,
                fixture_raw_evidence(gate.REJECT),
            )
            text = summary.read_text(encoding="ascii")
            summary.write_text(
                text.replace(gate.REJECT, gate.ADMIT, 1),
                encoding="ascii",
                newline="\n",
            )
            before = self._tracked(root, state_path)
            with self.assertRaisesRegex(
                ValueError,
                "summary does not match recomputed gate evidence",
            ):
                self.closeout.apply_gate(
                    root,
                    state_path,
                    summary,
                    input_commit=self.input_commit,
                    evidence_path=evidence,
                    allow_fixture=True,
                )
            self.assertEqual(before, self._tracked(root, state_path))

    def test_write_failure_rolls_back_every_closeout_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            summary, evidence = self._write_fixture_pack(
                root,
                fixture_raw_evidence(gate.REJECT),
            )
            before = self._tracked(root, state_path)
            with patch.object(
                self.closeout,
                "_append_once",
                side_effect=OSError("injected write failure"),
            ):
                with self.assertRaisesRegex(OSError, "injected write failure"):
                    self.closeout.apply_gate(
                        root,
                        state_path,
                        summary,
                        input_commit=self.input_commit,
                        evidence_path=evidence,
                        allow_fixture=True,
                    )
            self.assertEqual(before, self._tracked(root, state_path))

    def test_closeout_outputs_are_ascii(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            self._apply_twice(
                root,
                state_path,
                fixture_raw_evidence(gate.REJECT),
            )
            for path in self._tracked(root, state_path):
                with self.subTest(path=path.name):
                    path.read_bytes().decode("ascii")

    def test_closeout_requires_explicit_input_commit(self):
        parameter = inspect.signature(
            self.closeout.apply_gate
        ).parameters["input_commit"]
        self.assertEqual(parameter.default, inspect.Parameter.empty)


if __name__ == "__main__":
    unittest.main()
