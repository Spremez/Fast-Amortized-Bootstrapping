import csv
from dataclasses import replace
import json
import shutil
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from scripts.apply_candidate_b_factorized_gate import apply_gate
from scripts.mat_sab_research_state import validate_state
import scripts.run_candidate_b_factorized_gate as gate


ROOT = Path(__file__).resolve().parents[2]
RUN_MARKER = "candidate-b-factorized-gate-001"
HYPOTHESIS_KEY = "H_candidate_b_factorized_mechanism:"
HYPOTHESIS_START = "# candidate-b-factorized-gate-hypothesis-start"
HYPOTHESIS_END = "# candidate-b-factorized-gate-hypothesis-end"
MANIFEST_START = "<!-- candidate-b-factorized-gate-manifest-start -->"
MANIFEST_END = "<!-- candidate-b-factorized-gate-manifest-end -->"
CHECKLIST_START = "<!-- candidate-b-factorized-gate-checklist-start -->"
CHECKLIST_END = "<!-- candidate-b-factorized-gate-checklist-end -->"
PREDECESSOR = "REJECT_CANDIDATE_A_STANDARD_PVW_RANDOMIZATION_ROUTE_TO_B"
GATE_INPUTS = tuple(
    sorted(
        {
            relative for _, relative, _, _ in gate.SOURCE_SPECS
        }
        | {
            relative
            for _, _, relative, _, _, _, _ in gate.LITERATURE_SPECS
        }
        | {
            "main.c",
            "paper_techgraphs/candidate_b_factorized_selector.yaml",
            (
                "repro/stage335_source_and_compact_route/"
                "sharing_mask_anchor_hits.csv"
            ),
            "theory_checks/candidate_b_factorized_standard_pvw_model.md",
        }
    )
)


class CandidateBCloseoutTests(unittest.TestCase):
    def _make_root(self, directory: str) -> tuple[Path, Path]:
        root = Path(directory)
        root.mkdir(parents=True, exist_ok=True)
        (root / "hypotheses").mkdir()
        (root / "repro").mkdir()
        for relative in GATE_INPUTS:
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)

        state = json.loads(
            (ROOT / "research_state.yaml").read_text(encoding="ascii")
        )
        state["goal_status"] = "ACTIVE"
        state["paper_gate"] = "BLOCKED"
        state["production_hot_path_permission"] = False
        state["active_candidate"] = "B"
        state["candidates"]["A"]["status"] = "REJECTED"
        state["candidates"]["B"]["status"] = "INTAKE"
        state["candidates"]["C"]["status"] = "QUEUED"
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

    def _gate_result(self, root: Path, decision: str) -> gate.GateResult:
        if decision == gate.ADMIT:
            with patch.object(
                gate,
                "validate_registered_alternative",
                return_value=True,
            ):
                return gate.evaluate_candidate_b(root)
        result = gate.evaluate_candidate_b(root)
        if decision != gate.REJECT:
            return replace(result, decision=decision)
        return result

    def _write_summary(
        self,
        root: Path,
        results: list[gate.GateResult],
    ) -> Path:
        summary = root / "summary.csv"
        with summary.open("w", newline="", encoding="ascii") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=gate.SUMMARY_FIELDS,
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(
                gate.canonical_summary_record(result) for result in results
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
        return {
            path: path.read_bytes() if path.exists() else b"<missing>"
            for path in paths
        }

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
                text = path.read_text(encoding="ascii")
                self.assertEqual(text.count(marker), 1)

    def test_reject_routes_to_c_and_second_application_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            result = self._gate_result(root, gate.REJECT)
            summary = self._write_summary(root, [result])

            first = apply_gate(root, state_path, summary)
            after_first = self._tracked_outputs(root, state_path)
            second = apply_gate(root, state_path, summary)
            changed = json.loads(state_path.read_text(encoding="ascii"))

            self.assertEqual(first, gate.REJECT)
            self.assertEqual(second, gate.REJECT)
            self.assertEqual(after_first, self._tracked_outputs(root, state_path))
            self.assertEqual(changed["candidates"]["A"]["status"], "REJECTED")
            self.assertEqual(changed["candidates"]["B"]["status"], "REJECTED")
            self.assertEqual(changed["candidates"]["C"]["status"], "INTAKE")
            self.assertEqual(changed["active_candidate"], "C")
            self.assertEqual(changed["goal_status"], "ACTIVE")
            self.assertEqual(changed["paper_gate"], "BLOCKED")
            self.assertFalse(changed["production_hot_path_permission"])
            self.assertEqual(changed["last_decision"], gate.REJECT)
            validate_state(changed)
            self._assert_markers_once(root)

            with (root / "repro/run_log.csv").open(
                newline="",
                encoding="ascii",
            ) as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(
                [row["run_id"] for row in rows].count(RUN_MARKER),
                1,
            )

    def test_admit_advances_b_only_to_adversarial_checker_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            admitted = self._gate_result(root, gate.ADMIT)
            summary = self._write_summary(root, [admitted])

            def recompute_admit(resolved_root: Path) -> gate.GateResult:
                self.assertEqual(resolved_root, root.resolve())
                return admitted

            with patch(
                "scripts.apply_candidate_b_factorized_gate."
                "evaluate_candidate_b",
                side_effect=recompute_admit,
            ):
                self.assertEqual(
                    apply_gate(root, state_path, summary),
                    gate.ADMIT,
                )
                after_first = self._tracked_outputs(root, state_path)
                self.assertEqual(
                    apply_gate(root, state_path, summary),
                    gate.ADMIT,
                )
            changed = json.loads(state_path.read_text(encoding="ascii"))

            self.assertEqual(after_first, self._tracked_outputs(root, state_path))
            self.assertEqual(changed["candidates"]["A"]["status"], "REJECTED")
            self.assertEqual(
                changed["candidates"]["B"]["status"],
                "ADVERSARIAL_CHECKER_PASS",
            )
            self.assertEqual(changed["candidates"]["C"]["status"], "QUEUED")
            self.assertEqual(changed["active_candidate"], "B")
            self.assertEqual(changed["goal_status"], "ACTIVE")
            self.assertEqual(changed["paper_gate"], "BLOCKED")
            self.assertFalse(changed["production_hot_path_permission"])
            self.assertEqual(changed["last_decision"], gate.ADMIT)
            validate_state(changed)
            self._assert_markers_once(root)

    def test_apply_gate_rejects_public_evaluator_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            result = self._gate_result(root, gate.REJECT)
            summary = self._write_summary(root, [result])
            before = self._tracked_outputs(root, state_path)

            with self.assertRaisesRegex(
                TypeError,
                "unexpected keyword argument 'evaluator'",
            ):
                apply_gate(
                    root,
                    state_path,
                    summary,
                    evaluator=gate.evaluate_candidate_b,
                )

            self.assertEqual(before, self._tracked_outputs(root, state_path))

    def test_fabricated_admit_summary_is_rejected_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            admitted = self._gate_result(root, gate.ADMIT)
            summary = self._write_summary(root, [admitted])
            before = self._tracked_outputs(root, state_path)

            with self.assertRaisesRegex(
                ValueError,
                "summary does not match recomputed gate evidence",
            ):
                apply_gate(root, state_path, summary)

            self.assertEqual(before, self._tracked_outputs(root, state_path))

    def test_nondecision_summary_change_is_rejected_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            result = self._gate_result(root, gate.REJECT)
            summary = self._write_summary(root, [result])
            rows = list(csv.DictReader(summary.read_text(encoding="ascii").splitlines()))
            rows[0]["cost_accounting_gate"] = "FAIL"
            with summary.open("w", newline="", encoding="ascii") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=gate.SUMMARY_FIELDS,
                    lineterminator="\n",
                )
                writer.writeheader()
                writer.writerows(rows)
            before = self._tracked_outputs(root, state_path)

            with self.assertRaisesRegex(
                ValueError,
                "summary does not match recomputed gate evidence",
            ):
                apply_gate(root, state_path, summary)

            self.assertEqual(before, self._tracked_outputs(root, state_path))

    def test_stale_summary_is_rejected_after_recomputation_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            result = self._gate_result(root, gate.REJECT)
            summary = self._write_summary(root, [result])
            source = root / "src/mosfhet/src/pvwtmlwe.c"
            source.write_text(
                source.read_text(encoding="utf-8").replace(
                    "void pvmtmlwe_sample(",
                    "void stale_pvmtmlwe_sample(",
                    1,
                ),
                encoding="utf-8",
                newline="\n",
            )
            before = self._tracked_outputs(root, state_path)

            with self.assertRaises(gate.GateEvidenceError):
                apply_gate(root, state_path, summary)

            self.assertEqual(before, self._tracked_outputs(root, state_path))

    def test_missing_equation_prerequisite_is_rejected_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            result = self._gate_result(root, gate.REJECT)
            summary = self._write_summary(root, [result])
            model = (
                root
                / "theory_checks/candidate_b_factorized_standard_pvw_model.md"
            )
            model.unlink()
            before = self._tracked_outputs(root, state_path)

            with self.assertRaisesRegex(
                ValueError,
                "Candidate B source/equation prerequisites",
            ):
                apply_gate(root, state_path, summary)

            self.assertEqual(before, self._tracked_outputs(root, state_path))

    def test_malformed_duplicate_and_unknown_summaries_are_rejected(self):
        canonical_header = ",".join(gate.SUMMARY_FIELDS)
        malformed = (
            "",
            canonical_header + "\n",
            (
                canonical_header
                + "\n"
                + ",".join(
                    gate.canonical_summary_record(
                        self._gate_result_for_template(gate.REJECT)
                    )[field]
                    for field in gate.SUMMARY_FIELDS
                )
                + "\n"
                + ",".join(
                    gate.canonical_summary_record(
                        self._gate_result_for_template(gate.REJECT)
                    )[field]
                    for field in gate.SUMMARY_FIELDS
                )
                + "\n"
            ),
            f"decision,decision\n{gate.REJECT},{gate.REJECT}\n",
            f"decision\n{gate.REJECT},surplus\n",
            "decision\nUNKNOWN_DECISION\n",
            f'decision\n"{gate.REJECT}',
        )
        for index, content in enumerate(malformed):
            with self.subTest(case=index):
                with tempfile.TemporaryDirectory() as tmp:
                    root, state_path = self._make_root(tmp)
                    if index == 2:
                        result = self._gate_result(root, gate.REJECT)
                        record = gate.canonical_summary_record(result)
                        row = ",".join(record[field] for field in gate.SUMMARY_FIELDS)
                        content = canonical_header + "\n" + row + "\n" + row + "\n"
                    summary = self._write_raw_summary(root, content)
                    before = self._tracked_outputs(root, state_path)

                    with self.assertRaisesRegex(
                        ValueError,
                        "summary must contain one canonical decision",
                    ):
                        apply_gate(root, state_path, summary)

                    self.assertEqual(
                        before,
                        self._tracked_outputs(root, state_path),
                    )

    def _gate_result_for_template(self, decision: str) -> gate.GateResult:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self._make_root(tmp)
            return self._gate_result(root, decision)

    def test_state_and_summary_paths_must_resolve_under_root(self):
        for escaped in ("state", "summary"):
            with self.subTest(escaped=escaped):
                with tempfile.TemporaryDirectory() as tmp:
                    base = Path(tmp)
                    root, state_path = self._make_root(str(base / "root"))
                    result = self._gate_result(root, gate.REJECT)
                    summary = self._write_summary(root, [result])
                    outside_state = base / "outside-state.yaml"
                    outside_state.write_bytes(state_path.read_bytes())
                    outside_summary = base / "outside-summary.csv"
                    outside_summary.write_bytes(summary.read_bytes())
                    before = self._tracked_outputs(root, state_path)

                    with self.assertRaisesRegex(ValueError, "escapes root"):
                        apply_gate(
                            root,
                            (
                                outside_state
                                if escaped == "state"
                                else state_path
                            ),
                            (
                                outside_summary
                                if escaped == "summary"
                                else summary
                            ),
                        )

                    self.assertEqual(
                        before,
                        self._tracked_outputs(root, state_path),
                    )

    def test_exact_pre_state_is_required_before_any_ledger_mutation(self):
        mutations = (
            ("goal_status", "EXTERNAL_BLOCKED"),
            ("last_decision", "STALE_PREDECESSOR"),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as tmp:
                    root, state_path = self._make_root(tmp)
                    result = self._gate_result(root, gate.REJECT)
                    summary = self._write_summary(root, [result])
                    state = json.loads(state_path.read_text(encoding="ascii"))
                    state[field] = value
                    state_path.write_text(
                        json.dumps(state, indent=2) + "\n",
                        encoding="ascii",
                        newline="\n",
                    )
                    before = self._tracked_outputs(root, state_path)

                    with self.assertRaisesRegex(
                        ValueError,
                        "state is not at the Candidate B mechanism gate",
                    ):
                        apply_gate(root, state_path, summary)

                    self.assertEqual(
                        before,
                        self._tracked_outputs(root, state_path),
                    )

    def test_b_must_start_at_intake_on_first_application(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            result = self._gate_result(root, gate.REJECT)
            summary = self._write_summary(root, [result])
            state = json.loads(state_path.read_text(encoding="ascii"))
            state["candidates"]["B"]["status"] = "TECHGRAPH_ANCHORED"
            state_path.write_text(
                json.dumps(state, indent=2) + "\n",
                encoding="ascii",
                newline="\n",
            )
            before = self._tracked_outputs(root, state_path)

            with self.assertRaisesRegex(
                ValueError,
                "state is not at the Candidate B mechanism gate",
            ):
                apply_gate(root, state_path, summary)

            self.assertEqual(before, self._tracked_outputs(root, state_path))

    def test_conflicting_bounded_block_is_rejected_before_state_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            result = self._gate_result(root, gate.REJECT)
            summary = self._write_summary(root, [result])
            hypothesis = root / "hypotheses/hypothesis_register.yaml"
            hypothesis.write_text(
                HYPOTHESIS_START
                + "\nconflicting: true\n"
                + HYPOTHESIS_END
                + "\n",
                encoding="ascii",
                newline="\n",
            )
            before = self._tracked_outputs(root, state_path)

            with self.assertRaisesRegex(
                ValueError,
                "ledger block/content mismatch",
            ):
                apply_gate(root, state_path, summary)

            self.assertEqual(before, self._tracked_outputs(root, state_path))

    def test_duplicate_run_log_marker_is_rejected_before_state_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            result = self._gate_result(root, gate.REJECT)
            summary = self._write_summary(root, [result])
            run_log = root / "repro/run_log.csv"
            with run_log.open("a", newline="", encoding="ascii") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=(
                        "run_id",
                        "date",
                        "commit_or_state",
                        "stage",
                        "backend",
                        "command",
                        "params",
                        "seed",
                        "status",
                        "summary",
                        "artifacts",
                    ),
                    lineterminator="\n",
                )
                row = {field: "" for field in writer.fieldnames}
                row["run_id"] = RUN_MARKER
                writer.writerow(row)
                writer.writerow(row)
            before = self._tracked_outputs(root, state_path)

            with self.assertRaisesRegex(
                ValueError,
                "duplicate run-log marker",
            ):
                apply_gate(root, state_path, summary)

            self.assertEqual(before, self._tracked_outputs(root, state_path))

    def test_duplicate_physical_run_id_header_is_rejected_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            result = self._gate_result(root, gate.REJECT)
            summary = self._write_summary(root, [result])
            run_log = root / "repro/run_log.csv"
            run_log.write_text(
                "run_id,run_id,date,commit_or_state,stage,backend,command,"
                "params,seed,status,summary,artifacts\n"
                f"{RUN_MARKER},,2026-07-17,forged,forged,forged,forged,"
                "forged,forged,forged,forged,forged\n",
                encoding="ascii",
                newline="\n",
            )
            before = self._tracked_outputs(root, state_path)

            with self.assertRaisesRegex(
                ValueError,
                "run log header must match canonical schema",
            ):
                apply_gate(root, state_path, summary)

            self.assertEqual(before, self._tracked_outputs(root, state_path))

    def test_surplus_unheaded_run_marker_column_is_rejected_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            result = self._gate_result(root, gate.REJECT)
            summary = self._write_summary(root, [result])
            run_log = root / "repro/run_log.csv"
            run_log.write_text(
                "run_id,date,commit_or_state,stage,backend,command,params,seed,"
                "status,summary,artifacts\n"
                "ordinary-run,2026-07-17,commit,stage,backend,command,params,"
                f"seed,PASS,summary,artifacts,{RUN_MARKER}\n",
                encoding="ascii",
                newline="\n",
            )
            before = self._tracked_outputs(root, state_path)

            with self.assertRaisesRegex(
                ValueError,
                "run log rows must match canonical schema",
            ):
                apply_gate(root, state_path, summary)

            self.assertEqual(before, self._tracked_outputs(root, state_path))

    def test_missing_run_log_column_is_rejected_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            result = self._gate_result(root, gate.REJECT)
            summary = self._write_summary(root, [result])
            run_log = root / "repro/run_log.csv"
            run_log.write_text(
                "run_id,date,commit_or_state,stage,backend,command,params,seed,"
                "status,summary,artifacts\n"
                "ordinary-run,2026-07-17,commit,stage,backend,command,params,"
                "seed,PASS,summary\n",
                encoding="ascii",
                newline="\n",
            )
            before = self._tracked_outputs(root, state_path)

            with self.assertRaisesRegex(
                ValueError,
                "run log rows must match canonical schema",
            ):
                apply_gate(root, state_path, summary)

            self.assertEqual(before, self._tracked_outputs(root, state_path))

    def test_write_failure_rolls_back_all_closeout_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            result = self._gate_result(root, gate.REJECT)
            summary = self._write_summary(root, [result])
            before = self._tracked_outputs(root, state_path)

            with patch(
                "scripts.apply_candidate_b_factorized_gate._append_once",
                side_effect=OSError("injected ledger write failure"),
            ):
                with self.assertRaisesRegex(
                    OSError,
                    "injected ledger write failure",
                ):
                    apply_gate(root, state_path, summary)

            self.assertEqual(before, self._tracked_outputs(root, state_path))

    def test_applied_state_with_other_decision_is_rejected_before_ledgers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            admitted = self._gate_result(root, gate.ADMIT)
            state = json.loads(state_path.read_text(encoding="ascii"))
            state["candidates"]["B"]["status"] = "ADVERSARIAL_CHECKER_PASS"
            state["last_decision"] = gate.ADMIT
            state_path.write_text(
                json.dumps(state, indent=2) + "\n",
                encoding="ascii",
                newline="\n",
            )
            rejected = self._gate_result(root, gate.REJECT)
            summary = self._write_summary(root, [rejected])
            before = self._tracked_outputs(root, state_path)

            with self.assertRaisesRegex(ValueError, "state/decision mismatch"):
                apply_gate(root, state_path, summary)

            self.assertEqual(before, self._tracked_outputs(root, state_path))
            self.assertEqual(admitted.decision, gate.ADMIT)

    def test_all_new_closeout_outputs_are_ascii(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            result = self._gate_result(root, gate.REJECT)
            summary = self._write_summary(root, [result])

            apply_gate(root, state_path, summary)

            for path in self._tracked_outputs(root, state_path):
                with self.subTest(path=path.name):
                    path.read_bytes().decode("ascii")


if __name__ == "__main__":
    unittest.main()
