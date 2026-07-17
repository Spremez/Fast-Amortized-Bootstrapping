import csv
import importlib
import json
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
    try:
        return importlib.import_module(
            "scripts.apply_candidate_c_rank_bounded_gate"
        )
    except ModuleNotFoundError:
        return None


class CandidateCCloseoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.closeout = load_closeout()
        cls.actual = gate.evaluate_candidate_c(ROOT)

    def setUp(self):
        self.assertIsNotNone(
            self.closeout,
            "Task 5 Candidate C closeout module has not been implemented",
        )

    @staticmethod
    def _make_root(directory: str) -> tuple[Path, Path]:
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

    @staticmethod
    def _write_summary(root: Path, result: gate.GateResult) -> Path:
        path = root / "summary.csv"
        with path.open("w", newline="", encoding="ascii") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=gate.SUMMARY_FIELDS,
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerow(gate.canonical_summary_record(result))
        return path

    @staticmethod
    def _tracked(root: Path, state_path: Path) -> dict[Path, bytes | None]:
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
    def _assert_markers_once(root: Path) -> None:
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

    def _apply_twice(
        self,
        root: Path,
        state_path: Path,
        result: gate.GateResult,
    ) -> dict[str, object]:
        summary = self._write_summary(root, result)
        with patch.object(
            self.closeout,
            "evaluate_candidate_c",
            return_value=result,
        ):
            first = self.closeout.apply_gate(root, state_path, summary)
            after_first = self._tracked(root, state_path)
            second = self.closeout.apply_gate(root, state_path, summary)
        self.assertEqual(first, result.decision)
        self.assertEqual(second, result.decision)
        self.assertEqual(after_first, self._tracked(root, state_path))
        self._assert_markers_once(root)
        return json.loads(state_path.read_text(encoding="ascii"))

    def test_admit_advances_c_only_to_adversarial_checker_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            admitted = gate.synthetic_gate_result(self.actual, gate.ADMIT)
            state = self._apply_twice(root, state_path, admitted)
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

    def test_reject_exhausts_the_finite_campaign(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            state = self._apply_twice(root, state_path, self.actual)
        self.assertEqual(state["active_candidate"], "C")
        self.assertEqual(state["candidates"]["A"]["status"], "REJECTED")
        self.assertEqual(state["candidates"]["B"]["status"], "REJECTED")
        self.assertEqual(state["candidates"]["C"]["status"], "REJECTED")
        self.assertEqual(state["goal_status"], "RESEARCH_CAMPAIGN_EXHAUSTED")
        self.assertEqual(state["paper_gate"], "BLOCKED")
        self.assertFalse(state["production_hot_path_permission"])
        self.assertEqual(state["last_decision"], gate.REJECT)
        validate_state(state)

    def test_inconclusive_closes_without_external_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            inconclusive = gate.synthetic_gate_result(
                self.actual,
                gate.INCONCLUSIVE,
            )
            state = self._apply_twice(root, state_path, inconclusive)
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
            self._apply_twice(root, state_path, self.actual)
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
                    summary = self._write_summary(root, self.actual)
                    before = self._tracked(root, state_path)
                    with patch.object(
                        self.closeout,
                        "evaluate_candidate_c",
                        return_value=self.actual,
                    ):
                        with self.assertRaisesRegex(
                            ValueError,
                            "run log rows must match canonical schema",
                        ):
                            self.closeout.apply_gate(
                                root,
                                state_path,
                                summary,
                            )
                    self.assertEqual(before, self._tracked(root, state_path))

    def test_summary_tamper_is_rejected_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            summary = self._write_summary(root, self.actual)
            text = summary.read_text(encoding="ascii")
            summary.write_text(
                text.replace(gate.REJECT, gate.ADMIT, 1),
                encoding="ascii",
                newline="\n",
            )
            before = self._tracked(root, state_path)
            with patch.object(
                self.closeout,
                "evaluate_candidate_c",
                return_value=self.actual,
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "summary does not match recomputed gate evidence",
                ):
                    self.closeout.apply_gate(root, state_path, summary)
            self.assertEqual(before, self._tracked(root, state_path))

    def test_write_failure_rolls_back_every_closeout_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            summary = self._write_summary(root, self.actual)
            before = self._tracked(root, state_path)
            with (
                patch.object(
                    self.closeout,
                    "evaluate_candidate_c",
                    return_value=self.actual,
                ),
                patch.object(
                    self.closeout,
                    "_append_once",
                    side_effect=OSError("injected write failure"),
                ),
            ):
                with self.assertRaisesRegex(OSError, "injected write failure"):
                    self.closeout.apply_gate(root, state_path, summary)
            self.assertEqual(before, self._tracked(root, state_path))

    def test_closeout_outputs_are_ascii(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            self._apply_twice(root, state_path, self.actual)
            for path in self._tracked(root, state_path):
                with self.subTest(path=path.name):
                    path.read_bytes().decode("ascii")


if __name__ == "__main__":
    unittest.main()
