import csv
from dataclasses import replace
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.run_candidate_a_star_cycle_gate as gate
from research.mat_sab.star_cycle_model import star_cycle_support


ROOT = Path(__file__).resolve().parents[2]


class CandidateAGateTests(unittest.TestCase):
    def test_current_stage203_support_is_rejected_by_standard_pvw_gate(self):
        result = gate.evaluate_candidate_a(ROOT)
        self.assertEqual(result.decision, gate.REJECT)
        self.assertTrue(result.support_gate)
        self.assertTrue(result.phase_gate)
        self.assertTrue(result.dense_control_gate)
        self.assertTrue(result.negative_control_gate)
        self.assertFalse(result.randomization_gate)
        self.assertFalse(result.production_code_permission)

    def test_r2_r4_r6_and_zero_one_semantics_are_covered(self):
        result = gate.evaluate_candidate_a(ROOT)
        self.assertEqual(
            {(row["r"], row["mu"]) for row in result.phase_rows},
            {(r, mu) for r in (2, 4, 6) for mu in (0, 1)},
        )
        self.assertTrue(all(row["phase_status"] == "PASS" for row in result.phase_rows))

    def test_dense_control_keeps_one_randomizer_per_column(self):
        result = gate.evaluate_candidate_a(ROOT)
        dense = [row for row in result.randomization_rows if row["support"] == "dense"]
        self.assertTrue(all(row["full_pvw_randomization"] == "PASS" for row in dense))

    def test_missing_source_anchors_are_inconclusive_not_a_route_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(gate.GateEvidenceError) as caught:
                gate.evaluate_candidate_a(Path(tmp))

        self.assertNotIn(gate.ADMIT, str(caught.exception))
        self.assertNotIn(gate.REJECT, str(caught.exception))

    def test_omitted_term_oracle_is_exact_for_r2_r4_r6(self):
        for r in (2, 4, 6):
            support = star_cycle_support(r)
            for removed in sorted(support):
                row, column = removed
                if column == 0:
                    expected = "inconsistent"
                elif row == column and r > 2:
                    expected = "inconsistent"
                else:
                    expected = "consistent"
                with self.subTest(r=r, removed=removed):
                    self.assertEqual(
                        gate.removal_control_expected_outcome(r, removed),
                        expected,
                    )

    def test_every_omitted_term_row_matches_its_independent_oracle(self):
        result = gate.evaluate_candidate_a(ROOT)
        removal_rows = [
            row for row in result.negative_rows
            if str(row["control"]).startswith("remove_")
        ]
        self.assertEqual(len(removal_rows), sum(4 * r for r in (2, 4, 6)))
        for row in removal_rows:
            _, output_row, input_column = str(row["control"]).split("_")
            removed = (int(output_row), int(input_column))
            with self.subTest(r=row["r"], removed=removed):
                self.assertEqual(
                    row["expected"],
                    gate.removal_control_expected_outcome(int(row["r"]), removed),
                )
                self.assertEqual(row["observed"], row["expected"])
                self.assertEqual(row["status"], "PASS")

    def test_one_wrong_omitted_term_outcome_makes_evidence_inconclusive(self):
        original = gate.analyze_support

        def swap_one_outcome(secret, mu, support, modulus):
            analysis = original(secret, mu, support, modulus)
            r = len(secret)
            if len(support) == 4 * r - 1 and (0, 1) not in support:
                return replace(analysis, consistent=not analysis.consistent)
            return analysis

        with patch.object(gate, "analyze_support", side_effect=swap_one_outcome):
            with self.assertRaises(gate.GateEvidenceError) as caught:
                gate.evaluate_candidate_a(ROOT)

        self.assertIn("negative_controls", str(caught.exception))
        self.assertNotIn(gate.ADMIT, str(caught.exception))
        self.assertNotIn(gate.REJECT, str(caught.exception))

    def test_failed_randomization_gate_records_failure_interpretation(self):
        result = gate.evaluate_candidate_a(ROOT)
        paths = gate.write_gate_artifacts(ROOT, result)
        proof = next(path for path in paths if path.name == "proof_gate.csv")
        with proof.open(newline="", encoding="ascii") as handle:
            rows = {row["gate"]: row for row in csv.DictReader(handle)}
        row = rows["standard_pvw_randomization"]
        self.assertEqual(row["status"], "FAIL")
        self.assertEqual(
            row["interpretation"],
            "star support fails to retain one PVW kernel degree per column",
        )

    def test_generated_docs_record_the_structural_removal_oracle(self):
        result = gate.evaluate_candidate_a(ROOT)
        paths = gate.write_gate_artifacts(ROOT, result)
        docs = [
            path.read_text(encoding="ascii")
            for path in paths
            if path.name in {
                "candidate_a_star_cycle_mechanism_gate.md",
                "candidate_a_star_cycle_gate_plan.md",
            }
        ]
        self.assertEqual(len(docs), 2)
        for content in docs:
            with self.subTest(document=content.splitlines()[0]):
                self.assertIn(
                    "diagonal removal is consistent for r=2 and "
                    "inconsistent for r=4/6",
                    content,
                )

    def test_generated_artifacts_are_idempotent(self):
        result = gate.evaluate_candidate_a(ROOT)
        first = gate.write_gate_artifacts(ROOT, result)
        before = {path: path.read_bytes() for path in first}
        second = gate.write_gate_artifacts(ROOT, result)
        self.assertEqual(before, {path: path.read_bytes() for path in second})


if __name__ == "__main__":
    unittest.main()
