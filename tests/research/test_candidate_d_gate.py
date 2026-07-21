import csv
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from scripts.run_candidate_d_admission import (
    ADMIT,
    BLOCK,
    REJECT_BINDING_NOISE_SECURITY,
    REJECT_CLOSURE,
    REJECT_COMPLETE_COST,
    REJECT_PRIOR_ART,
    AdmissionResult,
    canonical_summary_record,
    derive_candidate_d_decision,
    evaluate_candidate_d_admission,
    read_canonical_summary,
    validate_artifact_index,
    validate_decision_evidence,
    verify_candidate_d_artifacts,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "repro/candidate_d_admission"


def passing_result(**changes) -> AdmissionResult:
    result = AdmissionResult(
        d0_status="PASS",
        d0_decision="PASS_D0_CANDIDATE_D_BASELINES_FROZEN",
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
        pre_application_permission=False,
        decision=ADMIT,
        resume_condition="none",
        input_commit="7ef0ef5ccd0eb99f484888ba11af27740a13182d",
        source_hashes=(),
        runtime_source_hashes=(),
    )
    return replace(result, **changes)


class CandidateDGateTests(unittest.TestCase):
    def test_decision_priority_is_fail_closed_and_ordered(self):
        cases = (
            ("d0 block", {"d0_status": "BLOCK"}, BLOCK),
            ("d1 reject", {"d1_status": "REJECT"}, REJECT_PRIOR_ART),
            ("d1 block", {"d1_status": "BLOCK"}, BLOCK),
            ("d2 reject", {"d2_status": "REJECT"}, REJECT_CLOSURE),
            ("d2 block", {"d2_status": "BLOCK"}, BLOCK),
            (
                "gamma overflow",
                {"gamma_count": 5},
                REJECT_CLOSURE,
            ),
            ("zero channels", {"gamma_count": 0}, BLOCK),
            (
                "negative control",
                {"negative_controls_status": "REJECT"},
                REJECT_CLOSURE,
            ),
            (
                "binding reject",
                {"binding_status": "REJECT"},
                REJECT_BINDING_NOISE_SECURITY,
            ),
            (
                "security reject",
                {"security_status": "REJECT"},
                REJECT_BINDING_NOISE_SECURITY,
            ),
            (
                "noise reject",
                {"noise_status": "REJECT"},
                REJECT_BINDING_NOISE_SECURITY,
            ),
            ("noise block", {"noise_status": "BLOCK"}, BLOCK),
            (
                "complete cost reject",
                {"complete_cost_status": "REJECT"},
                REJECT_COMPLETE_COST,
            ),
            (
                "resource reject",
                {"resource_status": "REJECT"},
                REJECT_COMPLETE_COST,
            ),
            (
                "resource block",
                {"resource_status": "BLOCK"},
                BLOCK,
            ),
            (
                "missing pessimistic projection",
                {"pessimistic_projection": ""},
                BLOCK,
            ),
            (
                "subthreshold pessimistic projection",
                {"pessimistic_projection": "1.09"},
                REJECT_COMPLETE_COST,
            ),
            (
                "permission already true",
                {"pre_application_permission": True},
                BLOCK,
            ),
            ("all pass", {}, ADMIT),
        )
        for label, changes, expected in cases:
            with self.subTest(label=label):
                result = passing_result(**changes)
                self.assertEqual(derive_candidate_d_decision(result), expected)

    def test_earlier_rejection_cannot_be_overridden_by_later_passes(self):
        result = passing_result(
            d1_status="REJECT",
            d2_status="PASS",
            binding_status="PASS",
            security_status="PASS",
            noise_status="PASS",
            complete_cost_status="PASS",
            resource_status="PASS",
        )
        self.assertEqual(
            derive_candidate_d_decision(result),
            REJECT_PRIOR_ART,
        )

    def test_current_sources_derive_only_the_incomplete_evidence_block(self):
        result = evaluate_candidate_d_admission(ROOT)
        self.assertEqual(result.d0_status, "PASS")
        self.assertEqual(
            result.d0_decision,
            "PASS_D0_CANDIDATE_D_BASELINES_FROZEN",
        )
        self.assertEqual(result.d1_status, "BLOCK")
        self.assertEqual(
            result.d1_decision,
            "BLOCK_D1_REQUIRED_FULLTEXT_OR_REVIEW_MISSING",
        )
        self.assertEqual(
            result.d1_missing_evidence,
            ("NTRU_AMORT_2026_068",),
        )
        self.assertEqual(result.d2_status, "SKIPPED_D1_BLOCK")
        self.assertEqual(result.binding_status, "SKIPPED_D1_BLOCK")
        self.assertEqual(result.complete_cost_status, "SKIPPED_D1_BLOCK")
        self.assertIsNone(result.gamma_count)
        self.assertEqual(result.pessimistic_projection, "")
        self.assertEqual(result.decision, BLOCK)
        self.assertFalse(result.pre_application_permission)
        self.assertIn("NTRU_AMORT_FULLTEXT_PATH", result.resume_condition)
        self.assertIn(
            "scripts/fetch_candidate_d_primary_sources.sh",
            result.resume_condition,
        )
        self.assertIn(
            "python scripts/run_candidate_d_d1_literature.py",
            result.resume_condition,
        )

    def test_summary_is_one_canonical_nonpermissive_record(self):
        result = evaluate_candidate_d_admission(ROOT)
        record = canonical_summary_record(result)
        self.assertEqual(record["decision"], BLOCK)
        self.assertEqual(record["d1_missing_evidence"], "NTRU_AMORT_2026_068")
        self.assertEqual(record["gamma_count"], "")
        self.assertEqual(record["pessimistic_projection"], "")
        self.assertEqual(record["production_hot_path_permission"], "no")

    def test_summary_rejects_duplicate_rows_and_header_drift(self):
        result = evaluate_candidate_d_admission(ROOT)
        record = canonical_summary_record(result)
        fields = tuple(record)
        for mutation in ("duplicate", "header"):
            with self.subTest(mutation=mutation):
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "summary.csv"
                    with path.open("w", encoding="ascii", newline="") as handle:
                        writer = csv.DictWriter(handle, fieldnames=fields)
                        writer.writeheader()
                        writer.writerow(record)
                        if mutation == "duplicate":
                            writer.writerow(record)
                    if mutation == "header":
                        data = path.read_text(encoding="ascii")
                        path.write_text(
                            data.replace("decision,", "changed,", 1),
                            encoding="ascii",
                        )
                    with self.assertRaises(ValueError):
                        read_canonical_summary(path)

    def test_decision_evidence_hash_and_source_set_are_binding(self):
        payload = json.loads((OUT / "decision_evidence.json").read_text())
        validate_decision_evidence(payload)
        mutations = (
            lambda row: row.__setitem__("claimed_decision", ADMIT),
            lambda row: row["source_hashes"].pop(),
            lambda row: row.__setitem__("binding_sha256", "0" * 64),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                changed = json.loads(json.dumps(payload))
                mutate(changed)
                with self.assertRaises(ValueError):
                    validate_decision_evidence(changed)

    def test_artifact_index_rejects_path_escape_and_stale_hash(self):
        validate_artifact_index(ROOT, OUT / "artifact_index.csv")
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            index = Path(directory) / "artifact_index.csv"
            index.write_text(
                "path,sha256\n../outside,"
                + "0" * 64
                + "\n",
                encoding="ascii",
            )
            with self.assertRaises(ValueError):
                validate_artifact_index(ROOT, index)

            index.write_text(
                "path,sha256\nrepro/candidate_d_admission/summary.csv,"
                + "0" * 64
                + "\n",
                encoding="ascii",
            )
            with self.assertRaises(ValueError):
                validate_artifact_index(ROOT, index)

    def test_generated_artifacts_are_fresh_ascii_and_deterministic(self):
        first = verify_candidate_d_artifacts(ROOT)
        second = verify_candidate_d_artifacts(ROOT)
        self.assertEqual(first, second)
        for path in (
            ROOT / "docs/candidate_d_admission_report.md",
            OUT / "summary.csv",
            OUT / "proof_gate.csv",
            OUT / "decision_evidence.json",
            OUT / "artifact_index.csv",
        ):
            with self.subTest(path=path):
                data = path.read_bytes()
                data.decode("ascii")
                self.assertNotIn(b"\r", data)


if __name__ == "__main__":
    unittest.main()
