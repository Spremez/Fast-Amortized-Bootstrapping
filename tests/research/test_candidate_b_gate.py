import csv
from dataclasses import replace
import hashlib
import inspect
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.run_candidate_b_factorized_gate as gate


ROOT = Path(__file__).resolve().parents[2]


class CandidateBMechanismGateTests(unittest.TestCase):
    @staticmethod
    def _copy_evaluation_inputs(root: Path) -> None:
        inputs = {
            relative
            for _, relative, _, _ in gate.SOURCE_SPECS
        }
        inputs.update(
            relative
            for _, _, relative, _, _, _, _ in gate.LITERATURE_SPECS
        )
        inputs.add("main.c")
        inputs.add("src/mosfhet/src/misc.c")
        for relative in inputs:
            source = ROOT / relative
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    @staticmethod
    def _write_registered_alternative(
        root: Path,
        mechanism_id: str,
    ) -> Path:
        package = root / "repro/candidate_b_registered_alternative"
        package.mkdir(parents=True)
        proof = {
            field: mechanism_id if field == "mechanism_id" else "PASS"
            for field in gate.ALTERNATIVE_PROOF_FIELDS
        }
        with (package / "proof_gate.csv").open(
            "w",
            newline="",
            encoding="ascii",
        ) as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=gate.ALTERNATIVE_PROOF_FIELDS,
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerow(proof)

        index_rows = []
        for kind in sorted(gate.ALTERNATIVE_ARTIFACT_KINDS):
            relative = f"repro/candidate_b_registered_alternative/{kind}.txt"
            artifact = root / relative
            artifact.write_text(kind + "\n", encoding="ascii")
            index_rows.append(
                {
                    "kind": kind,
                    "path": relative,
                    "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                }
            )
        with (package / "artifact_index.csv").open(
            "w",
            newline="",
            encoding="ascii",
        ) as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=("kind", "path", "sha256"),
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(index_rows)
        return package

    def test_current_standard_distribution_route_is_rejected_to_candidate_c(self):
        result = gate.evaluate_candidate_b(ROOT)
        self.assertEqual(result.decision, gate.REJECT)
        self.assertTrue(result.source_gate)
        self.assertTrue(result.literature_scope_gate)
        self.assertTrue(result.sampler_parity_gate)
        self.assertTrue(result.phase_identity_gate)
        self.assertTrue(result.mutation_control_gate)
        self.assertTrue(result.full_rank_control_gate)
        self.assertTrue(result.low_rank_control_gate)
        self.assertTrue(result.cost_accounting_gate)
        self.assertFalse(result.exact_standard_factorization_gate)
        self.assertFalse(result.noiseless_only_linear_gate)
        self.assertFalse(result.concrete_alternative_gate)
        self.assertFalse(result.production_code_permission)

    def test_sampler_support_has_explicit_even_and_odd_formula_witnesses(self):
        result = gate.evaluate_candidate_b(ROOT)
        self.assertEqual(
            {row["parity"] for row in result.sampler_rows},
            {"even", "odd"},
        )
        self.assertEqual(
            {row["value"] for row in result.sampler_rows},
            {-11446, 1791},
        )
        self.assertTrue(all(row["status"] == "PASS" for row in result.sampler_rows))
        self.assertEqual({row["out_k"] for row in result.sampler_rows}, {1})
        self.assertEqual({row["T"] for row in result.sampler_rows}, {1})
        self.assertEqual({row["N"] for row in result.sampler_rows}, {2048})
        self.assertEqual({row["sigma"] for row in result.sampler_rows}, {"2^-50"})
        self.assertEqual({row["torus_bits"] for row in result.sampler_rows}, {64})

    def test_target_parameters_are_strictly_derived_from_default_sources(self):
        target = gate._target_parameters(ROOT)
        self.assertEqual(target.out_k, 1)
        self.assertEqual(target.l, 1)
        self.assertEqual(target.out_N, 2048)
        self.assertEqual(target.sigma_out_exponent, -50)
        self.assertEqual(target.torus_bits, 64)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in ("main.c", "src/mosfhet/src/misc.c"):
                source = ROOT / relative
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
            main = root / "main.c"
            main.write_text(
                main.read_text(encoding="utf-8").replace(
                    "int l;",
                    "int rounds;",
                    1,
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(gate.GateEvidenceError, "target_parameters"):
                gate._target_parameters(root)

    def test_phase_rows_cover_r2_r4_r6_and_both_selector_bits(self):
        result = gate.evaluate_candidate_b(ROOT)
        self.assertEqual(
            {(row["r"], row["mu"]) for row in result.phase_rows},
            {(r, mu) for r in (2, 4, 6) for mu in (0, 1)},
        )
        self.assertTrue(
            all(row["status"] == "PASS" for row in result.phase_rows)
        )

    def test_rank_controls_cover_every_q_below_r(self):
        result = gate.evaluate_candidate_b(ROOT)
        full = [
            row for row in result.rank_rows
            if row["control"] == "standard_support_full_rank_image"
        ]
        low = [
            row for row in result.rank_rows
            if row["control"] == "constructed_low_rank_image"
        ]
        expected = {(r, q) for r in (2, 4, 6) for q in range(1, r)}
        self.assertEqual({(row["r"], row["q"]) for row in full}, expected)
        self.assertEqual({(row["r"], row["q"]) for row in low}, expected)
        self.assertTrue(all(row["observed_possible"] == "no" for row in full))
        self.assertTrue(all(row["observed_possible"] == "yes" for row in low))
        self.assertTrue(all(row["status"] == "PASS" for row in result.rank_rows))

    def test_cost_rows_expose_dense_error_and_full_rank_factor_cost(self):
        result = gate.evaluate_candidate_b(ROOT)
        full_rank_rows = [
            row for row in result.cost_rows if row["q"] == row["r"]
        ]
        self.assertEqual({row["r"] for row in full_rank_rows}, {2, 4, 6})
        for row in full_rank_rows:
            with self.subTest(r=row["r"]):
                self.assertGreaterEqual(
                    row["generic_dense_factor_products"],
                    row["dense_products"],
                )
                self.assertEqual(
                    row["generic_dense_factor_beats_dense"],
                    "no",
                )
                self.assertEqual(row["retained_dense_error_order"], "Theta(r^2)")

    def test_missing_source_anchors_are_inconclusive(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(gate.GateEvidenceError) as caught:
                gate.evaluate_candidate_b(Path(tmp))
        self.assertIn("source_anchors", str(caught.exception))
        self.assertNotIn(gate.ADMIT, str(caught.exception))
        self.assertNotIn(gate.REJECT, str(caught.exception))

    def test_broken_phase_or_mutation_control_is_inconclusive(self):
        original = gate.expected_phase

        def wrong_expected(*args, **kwargs):
            values = list(original(*args, **kwargs))
            values[0] = (values[0] + 1) % gate.PRIME
            return tuple(values)

        with patch.object(gate, "expected_phase", side_effect=wrong_expected):
            with self.assertRaises(gate.GateEvidenceError) as caught:
                gate.evaluate_candidate_b(ROOT)
        self.assertIn("phase_identity", str(caught.exception))
        self.assertNotIn(gate.REJECT, str(caught.exception))

    def test_broken_low_rank_negative_control_is_inconclusive(self):
        original = gate.homomorphic_image_fits_inner_dimension

        def reject_low_rank(image, q):
            if gate.homomorphic_image_rank(image) == q:
                return False
            return original(image, q)

        with patch.object(
            gate,
            "homomorphic_image_fits_inner_dimension",
            side_effect=reject_low_rank,
        ):
            with self.assertRaises(gate.GateEvidenceError) as caught:
                gate.evaluate_candidate_b(ROOT)
        self.assertIn("low_rank_controls", str(caught.exception))

    def test_summary_and_proof_separate_failed_mechanism_from_failed_evidence(self):
        result = gate.evaluate_candidate_b(ROOT)
        paths = gate.write_gate_artifacts(ROOT, result)
        proof = next(path for path in paths if path.name == "proof_gate.csv")
        with proof.open(newline="", encoding="ascii") as handle:
            rows = {row["gate"]: row for row in csv.DictReader(handle)}
        self.assertEqual(rows["source_anchors"]["status"], "PASS")
        self.assertEqual(rows["literature_scope"]["status"], "PASS")
        self.assertEqual(rows["full_rank_control"]["status"], "PASS")
        self.assertEqual(rows["sampler_parity_support"]["status"], "PASS")
        self.assertEqual(
            rows["exact_standard_q_lt_r_factorization"]["status"],
            "FAIL",
        )
        self.assertEqual(
            rows["exact_standard_q_lt_r_factorization"]["classification"],
            "mechanism_rejection",
        )
        self.assertEqual(
            rows["production_hot_path_permission"]["status"],
            "NO",
        )

    def test_literature_boundary_uses_verified_primary_source_urls(self):
        result = gate.evaluate_candidate_b(ROOT)
        paths = gate.write_gate_artifacts(ROOT, result)
        reports = [
            path.read_text(encoding="ascii")
            for path in paths
            if path.name in {
                "candidate_b_factorized_mechanism_gate.md",
                "candidate_b_factorized_star_cycle.md",
            }
        ]
        self.assertEqual(len(reports), 2)
        for content in reports:
            self.assertIn("https://eprint.iacr.org/2025/2112", content)
            self.assertIn("https://eprint.iacr.org/2025/686", content)
            self.assertIn("not a general impossibility theorem", content)

    def test_literature_rows_separate_fulltext_from_metadata_background(self):
        result = gate.evaluate_candidate_b(ROOT)
        rows = {row["source_id"]: row for row in result.literature_rows}
        self.assertEqual(
            rows["FAB686_2025"]["support_level"],
            "FULLTEXT_ANCHORS_REVIEWED",
        )
        self.assertEqual(
            rows["SHAREMASK25"]["support_level"],
            "LOCAL_FULLTEXT_AUDITED",
        )
        self.assertEqual(
            rows["SHAREMASK25"]["local_evidence"],
            "repro/stage335_source_and_compact_route/source_acquisition_audit.csv",
        )
        self.assertEqual(
            rows["BGH2012_565"]["support_level"],
            "PRIMARY_METADATA_BACKGROUND_ONLY",
        )
        self.assertEqual(
            rows["CGGI2018_421"]["support_level"],
            "PRIMARY_METADATA_BACKGROUND_ONLY",
        )
        self.assertTrue(
            all(row["status"] == "PASS" for row in result.literature_rows)
        )

    def test_generated_artifacts_are_idempotent(self):
        result = gate.evaluate_candidate_b(ROOT)
        first = gate.write_gate_artifacts(ROOT, result)
        before = {path: path.read_bytes() for path in first}
        second = gate.write_gate_artifacts(ROOT, result)
        self.assertEqual(before, {path: path.read_bytes() for path in second})

    def test_fabricated_admission_cannot_be_obtained_by_changing_decision_only(self):
        result = gate.evaluate_candidate_b(ROOT)
        fabricated = replace(result, decision=gate.ADMIT)
        with self.assertRaisesRegex(
            ValueError,
            "decision does not match mechanism gates",
        ):
            gate.canonical_summary_record(fabricated)

    def test_registered_semantic_package_reaches_canonical_admit_preflight(self):
        self.assertEqual(
            tuple(inspect.signature(gate.evaluate_candidate_b).parameters),
            ("root",),
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_evaluation_inputs(root)
            mechanism_id = "test_factorized_mechanism"
            package = self._write_registered_alternative(root, mechanism_id)

            self.assertFalse(gate.validate_registered_alternative(root))
            self.assertEqual(gate.evaluate_candidate_b(root).decision, gate.REJECT)

            def semantic_checker(
                checker_root: Path,
                proof: dict[str, str],
                rows: tuple[dict[str, str], ...],
            ) -> bool:
                return (
                    checker_root == root
                    and proof["mechanism_id"] == mechanism_id
                    and {row["kind"] for row in rows}
                    == gate.ALTERNATIVE_ARTIFACT_KINDS
                )

            with patch.dict(
                gate.REGISTERED_ALTERNATIVE_CHECKERS,
                {mechanism_id: semantic_checker},
                clear=True,
            ):
                result = gate.evaluate_candidate_b(root)
                self.assertEqual(result.decision, gate.ADMIT)
                self.assertFalse(result.exact_standard_factorization_gate)
                self.assertTrue(result.concrete_alternative_gate)
                self.assertFalse(result.production_code_permission)
                self.assertEqual(
                    gate.canonical_summary_record(result)["route"],
                    "candidate_b_key_distribution_preflight",
                )
                (package / "cost.txt").write_text(
                    "tampered\n",
                    encoding="ascii",
                )
                with self.assertRaises(gate.GateEvidenceError):
                    gate.evaluate_candidate_b(root)

    def test_artifacts_bind_inputs_and_execution_environment(self):
        result = gate.evaluate_candidate_b(ROOT)
        paths = gate.write_gate_artifacts(ROOT, result)
        manifest_path = next(
            path for path in paths if path.name == "input_manifest.csv"
        )
        environment_path = next(
            path for path in paths if path.name == "environment.csv"
        )
        with manifest_path.open(newline="", encoding="ascii") as handle:
            manifest = {row["path"]: row["sha256"] for row in csv.DictReader(handle)}
        script = ROOT / "scripts/run_candidate_b_factorized_gate.py"
        self.assertEqual(
            manifest["scripts/run_candidate_b_factorized_gate.py"],
            hashlib.sha256(script.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            manifest["main.c"],
            hashlib.sha256((ROOT / "main.c").read_bytes()).hexdigest(),
        )
        self.assertNotIn("research_state.yaml", manifest)
        self.assertIn(
            "repro/stage335_source_and_compact_route/sharing_mask_anchor_hits.csv",
            manifest,
        )
        with environment_path.open(newline="", encoding="ascii") as handle:
            environment = {
                row["key"]: row["value"] for row in csv.DictReader(handle)
            }
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(environment["input_head"], head)
        self.assertEqual(environment["target_out_k"], "1")
        self.assertEqual(environment["target_T"], "1")
        self.assertEqual(environment["target_N"], "2048")
        self.assertEqual(environment["target_sigma"], "2^-50")
        self.assertEqual(environment["torus_bits"], "64")

    def test_reports_use_finite_ring_and_parity_pattern_witness_wording(self):
        result = gate.evaluate_candidate_b(ROOT)
        paths = gate.write_gate_artifacts(ROOT, result)
        report = next(
            path for path in paths if path.name == "candidate_b_factorized_mechanism_gate.md"
        )
        proof = next(path for path in paths if path.name == "proof_gate.csv")
        report_text = report.read_text(encoding="ascii")
        proof_text = proof.read_text(encoding="ascii")
        self.assertIn("(Z/2^64Z)[X]/(X^N + 1)", report_text)
        self.assertNotIn("torus polynomial ring", report_text)
        self.assertIn("parity-pattern witness", proof_text)
        self.assertNotIn("constant-polynomial witness", proof_text)


if __name__ == "__main__":
    unittest.main()
