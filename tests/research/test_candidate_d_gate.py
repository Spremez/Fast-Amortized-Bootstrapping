import csv
from dataclasses import replace
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import scripts.run_candidate_d_admission as gate
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
FIXTURE_COMMIT = "f" * 40

D2_PASS = "PASS_D2_OPERATOR_CLOSURE_G_LE_4"
D2_REJECT = "REJECT_D2_PHASE_EQUIVALENCE"
D2_BLOCK = "BLOCK_D2_SOURCE_OR_EXACT_CHECKER_INCOMPLETE"
D3_PASS = "PASS_D3_STANDARD_NOISE_FEASIBLE_COMPLETE_PROJECTION_GE_1_10"
D3_BINDING_REJECT = "REJECT_D3_ILLEGAL_BINDING_DOMAIN"
D3_SECURITY_REJECT = "REJECT_D3_NONSTANDARD_SECURITY_OBJECT"
D3_NOISE_REJECT = "REJECT_D3_DECODING_MARGIN"
D3_COST_REJECT = "REJECT_D3_COMPLETE_PROJECTION_LT_1_10"
D3_RESOURCE_REJECT = "REJECT_D3_RESOURCE_OVERHEAD"
D3_NOISE_BLOCK = "BLOCK_D3_NOISE_LEMMA_INCOMPLETE"
D3_COST_BLOCK = "BLOCK_D3_COST_INPUT_INCOMPLETE"


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


def _write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="ascii", newline="")


def write_d2_fixture(
    root: Path,
    *,
    decision: str = D2_PASS,
    gamma_count: int = 2,
    negative_control_status: str = "DETECTED",
) -> None:
    _write(root, gate.D2_OUTPUTS[0], "# fixture operator closure\n")
    _write(root, gate.D2_OUTPUTS[1], f"decision\n{decision}\n")
    _write(
        root,
        gate.D2_OUTPUTS[2],
        "basis_index,status\n"
        + "".join(f"{index},PASS\n" for index in range(gamma_count)),
    )
    _write(root, gate.D2_OUTPUTS[3], "case,status\nphase,PASS\n")
    _write(
        root,
        gate.D2_OUTPUTS[4],
        "control,status\nwrong_phase,"
        + negative_control_status
        + "\nwrong_basis,"
        + negative_control_status
        + "\n",
    )
    _write(root, gate.D2_OUTPUTS[5], "case,status\nschedule,PASS\n")


def _d3_decision(
    binding: str,
    security: str,
    noise: str,
    cost: str,
    resource: str,
    projection: str,
) -> str:
    if binding == "REJECT":
        return D3_BINDING_REJECT
    if security == "REJECT":
        return D3_SECURITY_REJECT
    if noise == "REJECT":
        return D3_NOISE_REJECT
    if noise == "BLOCK":
        return D3_NOISE_BLOCK
    if cost == "REJECT" or (
        projection and float(projection) < 1.10
    ):
        return D3_COST_REJECT
    if resource == "REJECT":
        return D3_RESOURCE_REJECT
    if cost == "BLOCK" or resource == "BLOCK" or not projection:
        return D3_COST_BLOCK
    return D3_PASS


def write_d3_fixture(
    root: Path,
    *,
    binding: str = "PASS",
    security: str = "PASS",
    noise: str = "PASS",
    cost: str = "PASS",
    resource: str = "PASS",
    projection: str = "1.10",
    decision: str | None = None,
) -> None:
    selected = decision or _d3_decision(
        binding, security, noise, cost, resource, projection
    )
    _write(root, gate.D3_OUTPUTS[0], "# fixture security and noise\n")
    _write(root, gate.D3_OUTPUTS[1], "# fixture complete cost\n")
    _write(root, gate.D3_OUTPUTS[2], f"case,status\ninteger,{binding}\n")
    _write(root, gate.D3_OUTPUTS[3], f"object,status\nstandard,{security}\n")
    _write(root, gate.D3_OUTPUTS[4], f"case,status\ndecode,{noise}\n")
    _write(root, gate.D3_OUTPUTS[5], "case,value\ncomplete,1\n")
    _write(
        root,
        gate.D3_OUTPUTS[6],
        "scenario,speedup_vs_b1,status\npessimistic,"
        + projection
        + ","
        + cost
        + "\n",
    )
    _write(root, gate.D3_OUTPUTS[7], f"case,status\ncomplete,{resource}\n")
    _write(root, gate.D3_OUTPUTS[8], f"decision\n{selected}\n")


def source_route_result(
    *,
    d1_decision: str = gate.PASS_D1,
    d2_decision: str = D2_PASS,
    gamma_count: int = 2,
    negative_control_status: str = "DETECTED",
    binding: str = "PASS",
    security: str = "PASS",
    noise: str = "PASS",
    cost: str = "PASS",
    resource: str = "PASS",
    projection: str = "1.10",
    permission: bool = False,
) -> AdmissionResult:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for relative in (*gate.D0_OUTPUTS, *gate.D1_OUTPUTS):
            _write(root, relative, f"fixture:{relative}\n")
        if d1_decision == gate.PASS_D1:
            write_d2_fixture(
                root,
                decision=d2_decision,
                gamma_count=gamma_count,
                negative_control_status=negative_control_status,
            )
            if d2_decision == D2_PASS:
                write_d3_fixture(
                    root,
                    binding=binding,
                    security=security,
                    noise=noise,
                    cost=cost,
                    resource=resource,
                    projection=projection,
                )
        missing = (
            ("NTRU_AMORT_2026_068",)
            if d1_decision == gate.BLOCK_D1
            else ()
        )
        source_paths = tuple(
            dict.fromkeys((*gate.PINNED_INPUTS, *gate.D2_OUTPUTS, *gate.D3_OUTPUTS))
        )
        source_hashes = tuple((path, "0" * 64) for path in source_paths)
        runtime_hashes = tuple((path, "1" * 64) for path in gate.RUNTIME_SOURCES)
        state = {"production_hot_path_permission": permission}
        with (
            patch.object(gate, "_validate_module_origins"),
            patch.object(
                gate,
                "_pinned_source_hashes",
                return_value=source_hashes,
            ),
            patch.object(
                gate,
                "_runtime_source_hashes",
                return_value=runtime_hashes,
            ),
            patch.object(
                gate,
                "_recompute_d0",
                return_value=gate.d0_baseline.D0_DECISION,
            ),
            patch.object(
                gate,
                "_recompute_d1",
                return_value=(d1_decision, missing),
            ),
            patch.object(gate, "load_state", return_value=state),
        ):
            return gate.evaluate_candidate_d_admission(
                root, input_commit=FIXTURE_COMMIT
            )


class CandidateDGateTests(unittest.TestCase):
    def test_source_artifacts_derive_all_six_terminal_routes(self):
        cases = (
            ("D1 block", {"d1_decision": gate.BLOCK_D1}, BLOCK),
            ("D1 reject", {"d1_decision": gate.REJECT_D1}, REJECT_PRIOR_ART),
            ("D2 reject", {"d2_decision": D2_REJECT}, REJECT_CLOSURE),
            (
                "D3 binding reject",
                {"binding": "REJECT"},
                REJECT_BINDING_NOISE_SECURITY,
            ),
            (
                "D3 cost reject",
                {"cost": "REJECT", "projection": "1.09"},
                REJECT_COMPLETE_COST,
            ),
            ("all source gates pass", {}, ADMIT),
        )
        for label, changes, expected in cases:
            with self.subTest(label=label):
                self.assertEqual(source_route_result(**changes).decision, expected)

    def test_source_artifacts_expose_each_downstream_priority_input(self):
        cases = (
            ("D2 block", {"d2_decision": D2_BLOCK}, BLOCK),
            ("gamma overflow", {"gamma_count": 5}, REJECT_CLOSURE),
            (
                "negative control missed",
                {"negative_control_status": "MISSED"},
                REJECT_CLOSURE,
            ),
            (
                "security reject",
                {"security": "REJECT"},
                REJECT_BINDING_NOISE_SECURITY,
            ),
            (
                "noise reject",
                {"noise": "REJECT"},
                REJECT_BINDING_NOISE_SECURITY,
            ),
            ("noise block", {"noise": "BLOCK"}, BLOCK),
            (
                "resource reject",
                {"resource": "REJECT"},
                REJECT_COMPLETE_COST,
            ),
            ("cost block", {"cost": "BLOCK", "projection": ""}, BLOCK),
            (
                "subthreshold projection",
                {"projection": "1.09"},
                REJECT_COMPLETE_COST,
            ),
            ("pre-application permission", {"permission": True}, BLOCK),
        )
        for label, changes, expected in cases:
            with self.subTest(label=label):
                self.assertEqual(source_route_result(**changes).decision, expected)

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
        result = evaluate_candidate_d_admission(
            ROOT, input_commit=gate.CURRENT_INPUT_COMMIT
        )
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
        self.assertIn("git commit", result.resume_condition)
        self.assertIn("REQUIRED_SOURCE_BINDINGS", result.resume_condition)
        self.assertIn("--input-commit <new-D1-commit>", result.resume_condition)
        self.assertIn("latest second revision", result.resume_condition)
        self.assertIn("2026-07-16", result.resume_condition)
        self.assertIn("not the archived January", result.resume_condition)

    def test_summary_is_one_canonical_nonpermissive_record(self):
        result = evaluate_candidate_d_admission(
            ROOT, input_commit=gate.CURRENT_INPUT_COMMIT
        )
        record = canonical_summary_record(result)
        self.assertEqual(record["decision"], BLOCK)
        self.assertEqual(record["d1_missing_evidence"], "NTRU_AMORT_2026_068")
        self.assertEqual(record["gamma_count"], "")
        self.assertEqual(record["pessimistic_projection"], "")
        self.assertEqual(record["production_hot_path_permission"], "no")

    def test_summary_rejects_duplicate_rows_and_header_drift(self):
        result = evaluate_candidate_d_admission(
            ROOT, input_commit=gate.CURRENT_INPUT_COMMIT
        )
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
        first = verify_candidate_d_artifacts(
            ROOT, input_commit=gate.CURRENT_INPUT_COMMIT
        )
        second = verify_candidate_d_artifacts(
            ROOT, input_commit=gate.CURRENT_INPUT_COMMIT
        )
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

    def test_proof_gate_names_every_admission_priority_input(self):
        rows = gate._proof_rows(passing_result())
        self.assertEqual(
            tuple(row["gate"] for row in rows),
            (
                "D0_baseline",
                "D1_novelty",
                "D2_closure",
                "D2_gamma_count",
                "D2_negative_controls",
                "D3_integer_binding",
                "D3_standard_object_security",
                "D3_noise_decode",
                "D3_complete_cost",
                "D3_resource",
                "D3_pessimistic_projection",
                "pre_application_permission",
                "production_hot_path_permission",
                "terminal_decision",
                "finite_resume_condition",
            ),
        )

    def test_admit_recheck_recovers_original_false_permission_evidence(self):
        source_paths = (*gate.PINNED_INPUTS, *gate.D2_OUTPUTS, *gate.D3_OUTPUTS)
        source_hashes = tuple((path, "0" * 64) for path in source_paths)
        runtime_hashes = tuple((path, "1" * 64) for path in gate.RUNTIME_SOURCES)
        result = passing_result(
            input_commit=FIXTURE_COMMIT,
            source_hashes=source_hashes,
            runtime_source_hashes=runtime_hashes,
        )
        state = {
            "last_decision": ADMIT,
            "active_candidate": "D",
            "goal_status": "ACTIVE",
            "production_hot_path_permission": True,
            "candidates": {"D": {"status": "D3_ADMISSION_PASS"}},
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / gate.OUT / "decision_evidence.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(gate._decision_evidence_payload(result)),
                encoding="ascii",
            )
            self.assertFalse(
                gate._effective_pre_application_permission(root, state, result)
            )

            divergent = replace(
                result,
                noise_status="BLOCK",
                decision=BLOCK,
                resume_condition="repair noise evidence",
            )
            evidence.write_text(
                json.dumps(gate._decision_evidence_payload(divergent)),
                encoding="ascii",
            )
            with self.assertRaises(gate.AdmissionEvidenceError):
                gate._effective_pre_application_permission(root, state, result)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_writer_rejects_symlinked_generated_output(self):
        result = passing_result(input_commit=FIXTURE_COMMIT)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            outside = Path(directory) / "outside"
            root.mkdir()
            outside.mkdir()
            for relative in gate.GENERATED_OUTPUTS:
                (root / relative).parent.mkdir(parents=True, exist_ok=True)
            victim = outside / "victim"
            victim.write_text("unchanged", encoding="ascii")
            report = root / gate.REPORT
            try:
                os.symlink(victim, report)
            except OSError as error:
                self.skipTest(f"file symlinks unavailable: {error}")
            rendered = {relative: b"fixture\n" for relative in gate.GENERATED_OUTPUTS}
            with (
                patch.object(
                    gate,
                    "evaluate_candidate_d_admission",
                    return_value=result,
                ),
                patch.object(gate, "_render_artifacts", return_value=rendered),
            ):
                with self.assertRaises(gate.AdmissionEvidenceError):
                    gate.write_candidate_d_artifacts(
                        root, result, input_commit=FIXTURE_COMMIT
                    )
            self.assertEqual(victim.read_text(encoding="ascii"), "unchanged")

    def test_writer_rejects_generated_output_reported_as_symlink(self):
        result = passing_result(input_commit=FIXTURE_COMMIT)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            root.mkdir()
            for relative in gate.GENERATED_OUTPUTS:
                (root / relative).parent.mkdir(parents=True, exist_ok=True)
            report = root / gate.REPORT
            rendered = {relative: b"fixture\n" for relative in gate.GENERATED_OUTPUTS}
            original_is_symlink = Path.is_symlink

            def reported_symlink(path):
                return path == report or original_is_symlink(path)

            with (
                patch.object(
                    gate,
                    "evaluate_candidate_d_admission",
                    return_value=result,
                ),
                patch.object(gate, "_render_artifacts", return_value=rendered),
                patch.object(Path, "is_symlink", reported_symlink),
            ):
                with self.assertRaises(gate.AdmissionEvidenceError):
                    gate.write_candidate_d_artifacts(
                        root, result, input_commit=FIXTURE_COMMIT
                    )

    def test_cli_requires_explicit_input_commit(self):
        with self.assertRaises(SystemExit):
            gate.main([])


if __name__ == "__main__":
    unittest.main()
