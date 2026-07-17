import csv
import unittest
from pathlib import Path

from scripts.run_candidate_a_star_cycle_gate import (
    REJECT,
    evaluate_candidate_a,
    write_gate_artifacts,
)


ROOT = Path(__file__).resolve().parents[2]


class CandidateAGateTests(unittest.TestCase):
    def test_current_stage203_support_is_rejected_by_standard_pvw_gate(self):
        result = evaluate_candidate_a(ROOT)
        self.assertEqual(result.decision, REJECT)
        self.assertTrue(result.support_gate)
        self.assertTrue(result.phase_gate)
        self.assertTrue(result.dense_control_gate)
        self.assertTrue(result.negative_control_gate)
        self.assertFalse(result.randomization_gate)
        self.assertFalse(result.production_code_permission)

    def test_r2_r4_r6_and_zero_one_semantics_are_covered(self):
        result = evaluate_candidate_a(ROOT)
        self.assertEqual(
            {(row["r"], row["mu"]) for row in result.phase_rows},
            {(r, mu) for r in (2, 4, 6) for mu in (0, 1)},
        )
        self.assertTrue(all(row["phase_status"] == "PASS" for row in result.phase_rows))

    def test_dense_control_keeps_one_randomizer_per_column(self):
        result = evaluate_candidate_a(ROOT)
        dense = [row for row in result.randomization_rows if row["support"] == "dense"]
        self.assertTrue(all(row["full_pvw_randomization"] == "PASS" for row in dense))

    def test_failed_randomization_gate_records_failure_interpretation(self):
        result = evaluate_candidate_a(ROOT)
        paths = write_gate_artifacts(ROOT, result)
        proof = next(path for path in paths if path.name == "proof_gate.csv")
        with proof.open(newline="", encoding="ascii") as handle:
            rows = {row["gate"]: row for row in csv.DictReader(handle)}
        row = rows["standard_pvw_randomization"]
        self.assertEqual(row["status"], "FAIL")
        self.assertEqual(
            row["interpretation"],
            "star support fails to retain one PVW kernel degree per column",
        )

    def test_generated_artifacts_are_idempotent(self):
        result = evaluate_candidate_a(ROOT)
        first = write_gate_artifacts(ROOT, result)
        before = {path: path.read_bytes() for path in first}
        second = write_gate_artifacts(ROOT, result)
        self.assertEqual(before, {path: path.read_bytes() for path in second})


if __name__ == "__main__":
    unittest.main()
