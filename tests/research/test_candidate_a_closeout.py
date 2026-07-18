import csv
from dataclasses import replace
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.apply_mat_sab_candidate_gate import apply_gate
from scripts.mat_sab_research_state import validate_state
import scripts.run_candidate_a_star_cycle_gate as gate


ROOT = Path(__file__).resolve().parents[2]
RUN_MARKER = "candidate-a-star-cycle-gate-001"
HYPOTHESIS_KEY = "H_candidate_a_star_cycle_mechanism:"
HYPOTHESIS_START = "# candidate-a-star-cycle-gate-hypothesis-start"
HYPOTHESIS_END = "# candidate-a-star-cycle-gate-hypothesis-end"
MANIFEST_START = "<!-- candidate-a-star-cycle-gate-manifest-start -->"
MANIFEST_END = "<!-- candidate-a-star-cycle-gate-manifest-end -->"
CHECKLIST_START = "<!-- candidate-a-star-cycle-gate-checklist-start -->"
CHECKLIST_END = "<!-- candidate-a-star-cycle-gate-checklist-end -->"
GATE_INPUTS = (
    "src/mosfhet/src/pvwtmlwe.c",
    "src/mosfhet/src/mattrgsw.c",
    "repro/stage203_production_selector_equation_probe/equation_map.csv",
)
SUMMARY_FIELDS = (
    "decision",
    "support_gate",
    "phase_gate",
    "dense_control_gate",
    "negative_control_gate",
    "standard_pvw_randomization_gate",
    "production_code_permission",
    "route",
)


class CandidateACloseoutTests(unittest.TestCase):
    def _make_root(self, directory: str) -> tuple[Path, Path]:
        root = Path(directory)
        root.mkdir(parents=True, exist_ok=True)
        (root / "hypotheses").mkdir()
        (root / "repro").mkdir()
        for relative in GATE_INPUTS:
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
        state = json.loads((ROOT / "research_state.yaml").read_text(encoding="ascii"))
        state["goal_status"] = "ACTIVE"
        state["paper_gate"] = "BLOCKED"
        state["production_hot_path_permission"] = False
        state["active_candidate"] = "A"
        state["candidates"]["A"]["status"] = "EQUATIONS_DEFINED"
        state["candidates"]["B"]["status"] = "QUEUED"
        state["candidates"]["C"]["status"] = "QUEUED"
        state["candidates"]["C"]["equation_revisions_used"] = 0
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

    def _gate_result(self, root: Path, decision: str) -> gate.GateResult:
        result = gate.evaluate_candidate_a(root)
        if decision == gate.ADMIT:
            return replace(
                result,
                decision=gate.ADMIT,
                randomization_gate=True,
            )
        if decision != gate.REJECT:
            return replace(result, decision=decision)
        return result

    def _summary_row(self, result: gate.GateResult) -> dict[str, str]:
        return {
            "decision": result.decision,
            "support_gate": "PASS" if result.support_gate else "FAIL",
            "phase_gate": "PASS" if result.phase_gate else "FAIL",
            "dense_control_gate": (
                "PASS" if result.dense_control_gate else "FAIL"
            ),
            "negative_control_gate": (
                "PASS" if result.negative_control_gate else "FAIL"
            ),
            "standard_pvw_randomization_gate": (
                "PASS" if result.randomization_gate else "FAIL"
            ),
            "production_code_permission": (
                "yes" if result.production_code_permission else "no"
            ),
            "route": (
                "candidate_a_keygen_preflight"
                if result.decision == gate.ADMIT
                else "candidate_b_factorized_star_cycle"
            ),
        }

    def _write_summary(self, root: Path, decisions: list[str]) -> Path:
        summary = root / "summary.csv"
        with summary.open("w", newline="", encoding="ascii") as handle:
            writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
            writer.writeheader()
            writer.writerows(
                self._summary_row(self._gate_result(root, decision))
                for decision in decisions
            )
        return summary

    def _write_raw_summary(self, root: Path, content: str) -> Path:
        summary = root / "summary.csv"
        summary.write_text(content, encoding="ascii", newline="\n")
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
            (root / "hypotheses/hypothesis_register.yaml", HYPOTHESIS_START),
            (root / "hypotheses/hypothesis_register.yaml", HYPOTHESIS_END),
            (root / "hypotheses/hypothesis_register.yaml", HYPOTHESIS_KEY),
            (root / "repro/run_log.csv", RUN_MARKER),
            (root / "repro/artifact_manifest.md", MANIFEST_START),
            (root / "repro/artifact_manifest.md", MANIFEST_END),
            (root / "repro/reproduction_checklist.md", CHECKLIST_START),
            (root / "repro/reproduction_checklist.md", CHECKLIST_END),
        )
        for path, marker in markers:
            with self.subTest(path=path.name, marker=marker):
                self.assertEqual(path.read_text(encoding="ascii").count(marker), 1)

    def test_reject_decision_activates_b_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            summary = self._write_summary(root, [gate.REJECT])

            first = apply_gate(root, state_path, summary)
            after_first = self._tracked_outputs(root, state_path)
            second = apply_gate(root, state_path, summary)
            changed = json.loads(state_path.read_text(encoding="ascii"))

            self.assertEqual(first, gate.REJECT)
            self.assertEqual(second, gate.REJECT)
            self.assertEqual(after_first, self._tracked_outputs(root, state_path))
            self.assertEqual(changed["candidates"]["A"]["status"], "REJECTED")
            self.assertEqual(changed["candidates"]["B"]["status"], "INTAKE")
            self.assertEqual(changed["candidates"]["C"]["status"], "QUEUED")
            self.assertEqual(changed["active_candidate"], "B")
            self.assertEqual(changed["goal_status"], "ACTIVE")
            self.assertEqual(changed["paper_gate"], "BLOCKED")
            self.assertFalse(changed["production_hot_path_permission"])
            self.assertEqual(changed["last_decision"], gate.REJECT)
            validate_state(changed)
            self._assert_markers_once(root)

    def test_admit_decision_advances_only_to_adversarial_checker_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            admitted = self._gate_result(root, gate.ADMIT)
            summary = self._write_summary(root, [gate.ADMIT])

            def recompute_admit(resolved_root):
                self.assertEqual(resolved_root, root.resolve())
                return admitted

            self.assertEqual(
                apply_gate(
                    root,
                    state_path,
                    summary,
                    evaluator=recompute_admit,
                ),
                gate.ADMIT,
            )
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
            self.assertEqual(changed["last_decision"], gate.ADMIT)
            validate_state(changed)
            self._assert_markers_once(root)

    def test_fabricated_admit_summary_is_rejected_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            summary = self._write_summary(root, [gate.ADMIT])
            state_before = state_path.read_bytes()
            run_log_before = (root / "repro/run_log.csv").read_bytes()

            with self.assertRaisesRegex(
                ValueError,
                "summary does not match recomputed gate evidence",
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
            self.assertFalse((root / "repro/reproduction_checklist.md").exists())

    def test_nondecision_summary_mismatch_is_rejected_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            summary = self._write_summary(root, [gate.REJECT])
            rows = list(
                csv.DictReader(
                    summary.read_text(encoding="ascii").splitlines()
                )
            )
            rows[0]["dense_control_gate"] = "FAIL"
            with summary.open("w", newline="", encoding="ascii") as handle:
                writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
                writer.writeheader()
                writer.writerows(rows)
            state_before = state_path.read_bytes()

            with self.assertRaisesRegex(
                ValueError,
                "summary does not match recomputed gate evidence",
            ):
                apply_gate(root, state_path, summary)

            self.assertEqual(state_path.read_bytes(), state_before)
            self.assertNotIn(
                RUN_MARKER,
                (root / "repro/run_log.csv").read_text(encoding="ascii"),
            )

    def test_one_column_summary_is_rejected_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            summary = self._write_raw_summary(
                root,
                f"decision\n{gate.REJECT}\n",
            )
            state_before = state_path.read_bytes()

            with self.assertRaisesRegex(
                ValueError,
                "summary must contain one recognized decision",
            ):
                apply_gate(root, state_path, summary)

            self.assertEqual(state_path.read_bytes(), state_before)
            self.assertNotIn(
                RUN_MARKER,
                (root / "repro/run_log.csv").read_text(encoding="ascii"),
            )

    def test_malformed_or_unknown_summary_is_rejected_before_mutation(self):
        malformed_rows = (
            [],
            [gate.REJECT, gate.REJECT],
            ["UNKNOWN_DECISION"],
        )
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

    def test_summary_rejects_duplicate_ragged_and_missing_values(self):
        malformed = (
            f"decision,decision\n{gate.REJECT},{gate.REJECT}\n",
            f"decision\n{gate.REJECT},surplus\n",
            f"decision,route\n{gate.REJECT}\n",
        )
        for content in malformed:
            with self.subTest(content=content):
                with tempfile.TemporaryDirectory() as tmp:
                    root, state_path = self._make_root(tmp)
                    summary = self._write_raw_summary(root, content)
                    state_before = state_path.read_bytes()

                    with self.assertRaisesRegex(
                        ValueError,
                        "summary must contain one recognized decision",
                    ):
                        apply_gate(root, state_path, summary)

                    self.assertEqual(state_path.read_bytes(), state_before)
                    self.assertNotIn(
                        RUN_MARKER,
                        (root / "repro/run_log.csv").read_text(encoding="ascii"),
                    )

    def test_unterminated_quoted_summary_is_rejected_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            summary = self._write_raw_summary(
                root,
                f'decision\n"{gate.REJECT}',
            )
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
            self.assertFalse((root / "repro/reproduction_checklist.md").exists())

    def test_real_complete_gate_summary_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            summary = root / "summary.csv"
            summary.write_bytes(
                (
                    ROOT
                    / "repro/candidate_a_star_cycle_gate/summary.csv"
                ).read_bytes()
            )

            self.assertEqual(apply_gate(root, state_path, summary), gate.REJECT)

    def test_explicit_state_and_summary_paths_must_resolve_under_root(self):
        for escaped_input in ("state", "summary"):
            with self.subTest(escaped_input=escaped_input):
                with tempfile.TemporaryDirectory() as tmp:
                    base = Path(tmp)
                    root, state_path = self._make_root(str(base / "root"))
                    summary = self._write_summary(root, [gate.REJECT])
                    outside_state = base / "outside-state.yaml"
                    outside_state.write_bytes(state_path.read_bytes())
                    outside_summary = base / "outside-summary.csv"
                    outside_summary.write_bytes(summary.read_bytes())
                    state_before = state_path.read_bytes()

                    with self.assertRaisesRegex(ValueError, "escapes root"):
                        apply_gate(
                            root,
                            outside_state if escaped_input == "state" else state_path,
                            (
                                outside_summary
                                if escaped_input == "summary"
                                else summary
                            ),
                        )

                    self.assertEqual(state_path.read_bytes(), state_before)
                    self.assertNotIn(
                        RUN_MARKER,
                        (root / "repro/run_log.csv").read_text(encoding="ascii"),
                    )

    def test_fixed_ledger_symlink_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root, state_path = self._make_root(str(base / "root"))
            summary = self._write_summary(root, [gate.REJECT])
            outside = base / "outside-hypotheses"
            outside.mkdir()
            hypotheses = root / "hypotheses"
            hypotheses.rmdir()
            if os.name == "nt":
                subprocess.run(
                    [
                        "cmd",
                        "/c",
                        "mklink",
                        "/J",
                        str(hypotheses),
                        str(outside),
                    ],
                    check=True,
                    capture_output=True,
                )
            else:
                hypotheses.symlink_to(outside, target_is_directory=True)
            state_before = state_path.read_bytes()

            with self.assertRaisesRegex(ValueError, "escapes root"):
                apply_gate(root, state_path, summary)

            self.assertEqual(state_path.read_bytes(), state_before)
            self.assertEqual(list(outside.iterdir()), [])

    def test_run_log_without_terminal_newline_preserves_bom_and_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            summary = self._write_summary(root, [gate.REJECT])
            run_log = root / "repro/run_log.csv"
            header = (
                "run_id,date,commit_or_state,stage,backend,command,params,seed,"
                "status,summary,artifacts"
            )
            run_log.write_text(
                header,
                encoding="utf-8-sig",
                newline="",
            )

            self.assertEqual(apply_gate(root, state_path, summary), gate.REJECT)

            raw = run_log.read_bytes()
            self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
            self.assertIn(b"artifacts\ncandidate-a-star-cycle-gate-001,", raw)
            with run_log.open(newline="", encoding="utf-8-sig") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["run_id"], RUN_MARKER)

    def test_first_transition_requires_exact_predecessor_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            summary = self._write_summary(root, [gate.REJECT])
            state = json.loads(state_path.read_text(encoding="ascii"))
            state["last_decision"] = "OTHER_EQUATIONS_DEFINED_DECISION"
            state_path.write_text(
                json.dumps(state, indent=2) + "\n",
                encoding="ascii",
                newline="\n",
            )
            state_before = state_path.read_bytes()

            with self.assertRaisesRegex(
                ValueError,
                "state is not at the Candidate A mechanism gate",
            ):
                apply_gate(root, state_path, summary)

            self.assertEqual(state_path.read_bytes(), state_before)
            self.assertNotIn(
                RUN_MARKER,
                (root / "repro/run_log.csv").read_text(encoding="ascii"),
            )

    def test_altered_content_inside_bounded_ledger_block_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            summary = self._write_summary(root, [gate.REJECT])
            apply_gate(root, state_path, summary)
            hypothesis = root / "hypotheses/hypothesis_register.yaml"
            current = hypothesis.read_text(encoding="ascii")
            self.assertIn(HYPOTHESIS_END, current)
            hypothesis.write_text(
                current.replace(
                    HYPOTHESIS_END,
                    "  conflicting_claim: true\n" + HYPOTHESIS_END,
                ),
                encoding="ascii",
                newline="\n",
            )
            state_before = state_path.read_bytes()

            with self.assertRaisesRegex(ValueError, "ledger block/content mismatch"):
                apply_gate(root, state_path, summary)

            self.assertEqual(state_path.read_bytes(), state_before)

    def test_marker_substrings_in_larger_lines_are_rejected(self):
        alterations = (
            (
                HYPOTHESIS_START,
                "prefix-" + HYPOTHESIS_START,
            ),
            (
                HYPOTHESIS_END,
                HYPOTHESIS_END + "-suffix",
            ),
        )
        for marker, replacement in alterations:
            with self.subTest(marker=marker):
                with tempfile.TemporaryDirectory() as tmp:
                    root, state_path = self._make_root(tmp)
                    summary = self._write_summary(root, [gate.REJECT])
                    apply_gate(root, state_path, summary)
                    hypothesis = root / "hypotheses/hypothesis_register.yaml"
                    current = hypothesis.read_text(encoding="ascii")
                    hypothesis.write_text(
                        current.replace(marker, replacement),
                        encoding="ascii",
                        newline="\n",
                    )
                    before = self._tracked_outputs(root, state_path)

                    with self.assertRaisesRegex(
                        ValueError,
                        "ledger block marker mismatch",
                    ):
                        apply_gate(root, state_path, summary)

                    self.assertEqual(
                        self._tracked_outputs(root, state_path),
                        before,
                    )

    def test_state_decision_mismatch_is_rejected_before_ledger_updates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            state = json.loads(state_path.read_text(encoding="ascii"))
            state["candidates"]["A"]["status"] = "ADVERSARIAL_CHECKER_PASS"
            state["last_decision"] = gate.ADMIT
            state_path.write_text(
                json.dumps(state, indent=2) + "\n",
                encoding="ascii",
                newline="\n",
            )
            summary = self._write_summary(root, [gate.REJECT])
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
