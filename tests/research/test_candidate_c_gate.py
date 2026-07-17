import csv
from dataclasses import replace
import hashlib
import importlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APPROVED_TERMINAL_HASH = (
    "8ad876708aa4a736c0f0f9adae33bab766272f411e90fbc23a5ac23e10a73cb6"
)
EXPECTED_ARTIFACTS = {
    "summary.csv",
    "source_mapping.csv",
    "schedule_trace.csv",
    "operator_tensor.csv",
    "evaluator_sample_relations.csv",
    "conversion_material.csv",
    "registered_object_hash.csv",
    "terminal_record.csv",
    "rank_growth.csv",
    "compression_gate.csv",
    "complete_cost.csv",
    "amdahl_projection.csv",
    "mechanism_matrix.csv",
    "proof_gate.csv",
    "input_manifest.csv",
    "environment.csv",
    "artifact_index.csv",
    "reproduction_commands.md",
}


def load_gate():
    try:
        return importlib.import_module("scripts.run_candidate_c_rank_bounded_gate")
    except ModuleNotFoundError:
        return None


class CandidateCGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate = load_gate()
        cls.result = (
            cls.gate.evaluate_candidate_c(ROOT)
            if cls.gate is not None
            else None
        )

    def setUp(self):
        self.assertIsNotNone(
            self.gate,
            "Task 5 Candidate C gate module has not been implemented",
        )

    def test_actual_terminal_route_is_scoped_reject(self):
        gate = self.gate
        result = self.result
        self.assertEqual(result.decision, gate.REJECT)
        self.assertEqual(result.terminal_classification, "REJECT")
        self.assertEqual(
            result.terminal_decision,
            "REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL",
        )
        self.assertEqual(result.terminal_record_hash, APPROVED_TERMINAL_HASH)
        self.assertEqual(result.task4_status, gate.SKIPPED)
        self.assertEqual(result.complete_cost_status, gate.SKIPPED)
        self.assertEqual(result.amdahl_status, gate.SKIPPED)
        self.assertIsNone(result.complete_cost)
        self.assertIsNone(result.amdahl_projection)
        self.assertFalse(result.production_hot_path_permission)

    def test_canonical_summary_has_every_required_gate(self):
        summary = self.gate.canonical_summary_record(self.result)
        required = {
            "decision",
            "source_status",
            "equation_status",
            "symbolic_independence_status",
            "phase_status",
            "schedule_status",
            "rank_status",
            "compression_status",
            "complete_cost_status",
            "complete_cost",
            "amdahl_status",
            "amdahl_projection",
            "terminal_decision",
            "terminal_record_hash",
        }
        self.assertTrue(required.issubset(summary))
        self.assertEqual(tuple(summary), self.gate.SUMMARY_FIELDS)
        self.assertEqual(summary["complete_cost_status"], self.gate.SKIPPED)
        self.assertEqual(summary["amdahl_status"], self.gate.SKIPPED)
        self.assertEqual(summary["complete_cost"], "")
        self.assertEqual(summary["amdahl_projection"], "")

    def test_decision_cannot_be_changed_independently(self):
        fabricated = replace(self.result, decision=self.gate.ADMIT)
        with self.assertRaisesRegex(
            ValueError,
            "decision does not match mechanism and terminal evidence",
        ):
            self.gate.canonical_summary_record(fabricated)

    def test_terminal_hash_cannot_be_changed_independently(self):
        fabricated = replace(self.result, terminal_record_hash="0" * 64)
        with self.assertRaisesRegex(ValueError, "terminal record"):
            self.gate.canonical_summary_record(fabricated)

    def test_admit_requires_every_mechanism_gate_and_numeric_task4(self):
        admitted = self.gate.synthetic_gate_result(self.result, self.gate.ADMIT)
        self.assertEqual(
            self.gate.canonical_summary_record(admitted)["decision"],
            self.gate.ADMIT,
        )
        mechanism = admitted.mechanisms[0]
        cases = (
            replace(mechanism, max_rho=3),
            replace(
                mechanism,
                compression_interval=mechanism.b_min - 1,
            ),
            replace(mechanism, phase_status="FAIL"),
            replace(mechanism, closed_next_state_consumption=False),
            replace(mechanism, amdahl_projection=0.0),
        )
        for failed in cases:
            with self.subTest(failed=failed):
                forged = replace(admitted, mechanisms=(failed,))
                with self.assertRaisesRegex(
                    ValueError,
                    (
                        "decision does not match mechanism and terminal "
                        "evidence|terminal record"
                    ),
                ):
                    self.gate.canonical_summary_record(forged)

    def test_inconclusive_requires_hash_bound_evidence_exhaustion(self):
        inconclusive = self.gate.synthetic_gate_result(
            self.result,
            self.gate.INCONCLUSIVE,
        )
        self.assertEqual(
            self.gate.canonical_summary_record(inconclusive)["decision"],
            self.gate.INCONCLUSIVE,
        )
        forged = replace(
            inconclusive,
            terminal_decision="MISSING_UNBOUND_EVIDENCE",
        )
        with self.assertRaisesRegex(ValueError, "terminal record"):
            self.gate.canonical_summary_record(forged)

    def test_reject_after_task4_preserves_numeric_cost_and_amdahl(self):
        builder = getattr(self.gate, "synthetic_reject_after_cost", None)
        self.assertIsNotNone(builder)
        rejected = builder(self.result)
        summary = self.gate.canonical_summary_record(rejected)
        self.assertEqual(summary["decision"], self.gate.REJECT)
        self.assertEqual(summary["complete_cost_status"], "PASS")
        self.assertEqual(
            summary["amdahl_status"],
            "FAIL_NONPOSITIVE_CENTRAL_PROJECTION",
        )
        self.assertNotEqual(summary["complete_cost"], "")
        self.assertNotEqual(summary["amdahl_projection"], "")
        self.assertNotEqual(summary["task4_status"], self.gate.SKIPPED)

    def test_generator_emits_complete_byte_identical_pack(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp)
            first = self.gate.write_gate_artifacts(
                ROOT,
                self.result,
                destination_root=destination,
            )
            before = {
                path.relative_to(destination).as_posix(): path.read_bytes()
                for path in first
            }
            second = self.gate.write_gate_artifacts(
                ROOT,
                self.result,
                destination_root=destination,
            )
            after = {
                path.relative_to(destination).as_posix(): path.read_bytes()
                for path in second
            }
            generated = destination / "repro/candidate_c_rank_bounded_gate"
            self.assertEqual(
                {path.name for path in generated.iterdir()},
                EXPECTED_ARTIFACTS,
            )
            self.assertEqual(before, after)

    def test_artifact_index_and_input_manifest_are_hash_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp)
            self.gate.write_gate_artifacts(
                ROOT,
                self.result,
                destination_root=destination,
            )
            generated = destination / "repro/candidate_c_rank_bounded_gate"
            with (generated / "artifact_index.csv").open(
                newline="",
                encoding="ascii",
            ) as handle:
                index = {
                    row["path"]: row["sha256"]
                    for row in csv.DictReader(handle)
                }
            for relative, digest in index.items():
                self.assertEqual(
                    hashlib.sha256((destination / relative).read_bytes()).hexdigest(),
                    digest,
                )
            with (generated / "input_manifest.csv").open(
                newline="",
                encoding="ascii",
            ) as handle:
                manifest = {
                    row["path"]: row["sha256"]
                    for row in csv.DictReader(handle)
                }
            script = "scripts/run_candidate_c_rank_bounded_gate.py"
            self.assertEqual(
                manifest[script],
                hashlib.sha256((ROOT / script).read_bytes()).hexdigest(),
            )
            self.assertNotIn("research_state.yaml", manifest)

    def test_generated_pack_is_ascii(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp)
            paths = self.gate.write_gate_artifacts(
                ROOT,
                self.result,
                destination_root=destination,
            )
            for path in paths:
                with self.subTest(path=path.name):
                    path.read_bytes().decode("ascii")

    def test_task5_clis_import_from_outside_repository(self):
        scripts = (
            "scripts/run_candidate_c_rank_bounded_gate.py",
            "scripts/apply_candidate_c_rank_bounded_gate.py",
        )
        for relative in scripts:
            with self.subTest(script=relative):
                with tempfile.TemporaryDirectory() as tmp:
                    completed = subprocess.run(
                        [
                            sys.executable,
                            str(ROOT / relative),
                            "--help",
                        ],
                        cwd=tmp,
                        capture_output=True,
                        text=True,
                    )
                self.assertEqual(
                    completed.returncode,
                    0,
                    completed.stderr,
                )


if __name__ == "__main__":
    unittest.main()
