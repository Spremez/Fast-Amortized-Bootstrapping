import csv
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
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
CONTROLLER_COMMIT = subprocess.run(
    [
        "git",
        "log",
        "-1",
        "--format=%H",
        "--",
        "scripts/run_candidate_d_admission.py",
        "scripts/apply_candidate_d_admission.py",
        "research/mat_sab/candidate_d_stage_replay.py",
        "docs/candidate_d_task9_replay_contract.md",
    ],
    cwd=ROOT,
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()
RUN_DATE = "2026-07-21"
EXECUTION_PLATFORM = (
    "Windows-PowerShell; CPython-3.12; evidence-controller-only; "
    "no-performance-claim"
)


def evaluate_candidate_d_admission(
    root: Path = ROOT,
    *,
    input_commit: str,
    controller_commit: str = CONTROLLER_COMMIT,
    run_date: str = RUN_DATE,
    execution_platform: str = EXECUTION_PLATFORM,
) -> AdmissionResult:
    return gate.evaluate_candidate_d_admission(
        root,
        input_commit=input_commit,
        controller_commit=controller_commit,
        run_date=run_date,
        execution_platform=execution_platform,
    )


def verify_candidate_d_artifacts(
    root: Path = ROOT,
    *,
    input_commit: str,
    controller_commit: str = CONTROLLER_COMMIT,
    run_date: str = RUN_DATE,
    execution_platform: str = EXECUTION_PLATFORM,
) -> AdmissionResult:
    return gate.verify_candidate_d_artifacts(
        root,
        input_commit=input_commit,
        controller_commit=controller_commit,
        run_date=run_date,
        execution_platform=execution_platform,
    )

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
        d2_replay_authenticated=True,
        d3_replay_authenticated=True,
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
        controller_commit="c" * 40,
        run_date=RUN_DATE,
        execution_platform=EXECUTION_PLATFORM,
        source_hashes=(),
        runtime_source_hashes=(),
    )
    return replace(result, **changes)


def _write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="ascii", newline="")


def _write_csv(
    root: Path,
    relative: str,
    fields: tuple[str, ...],
    rows: list[dict[str, object]],
) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _digest(value: str) -> str:
    return sha256(value.encode("ascii")).hexdigest()


def _mutate_csv(
    path: Path,
    *,
    row_index: int,
    field: str,
    value: str,
) -> None:
    with path.open("r", encoding="ascii", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = tuple(reader.fieldnames or ())
        rows = list(reader)
    rows[row_index][field] = value
    with path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_d2_fixture(
    root: Path,
    *,
    decision: str = D2_PASS,
    gamma_count: int = 2,
    negative_control_status: str = "DETECTED",
) -> None:
    _write(root, gate.D2_OUTPUTS[0], "# fixture operator closure\n")
    search_status = "FOUND"
    closure_status = "PASS"
    if decision == D2_BLOCK:
        search_status = "INCOMPLETE"
        closure_status = "BLOCK"
    elif gamma_count > 4:
        search_status = "OVERFLOW"
        closure_status = "REJECT"
    closure_rows = [
        {
            "basis_index": index,
            "automorphism_label": (1, 15, 3, 5, 7, 9, 11, 13)[index],
            "gamma_count": gamma_count,
            "equation_revision": 0,
            "search_status": search_status,
            "status": closure_status,
        }
        for index in range(gamma_count)
    ]
    _write_csv(root, gate.D2_OUTPUTS[2], gate.D2_CLOSURE_FIELDS, closure_rows)

    phase_rows = []
    reject_phase = decision == D2_REJECT
    block_phase = decision == D2_BLOCK
    for n, schedule_case in gate._d2_required_cases():
        selector = (
            "0"
            if "all_zero" in schedule_case or schedule_case.endswith("mu0")
            else "1"
            if "all_one" in schedule_case or schedule_case.endswith("mu1")
            else "mixed"
        )
        for basis_index in range(n):
            expected = _digest(f"{n}:{schedule_case}:{basis_index}")
            status = "PASS"
            actual = expected
            if reject_phase and not phase_rows:
                status = "REJECT"
                actual = "f" * 64 if expected != "f" * 64 else "e" * 64
            elif block_phase and not phase_rows:
                status = "BLOCK"
                actual = ""
            phase_rows.append(
                {
                    "N": n,
                    "schedule_case": schedule_case,
                    "basis_index": basis_index,
                    "operation": "final_bind",
                    "accumulator_index": "final",
                    "selector_bit": selector,
                    "gamma_count": gamma_count,
                    "matrix_rank": gamma_count,
                    "expected_hash": expected,
                    "actual_hash": actual,
                    "status": status,
                }
            )
    _write_csv(root, gate.D2_OUTPUTS[3], gate.D2_PHASE_FIELDS, phase_rows)

    negative_rows = [
        {
            "control": control,
            "failed_invariant": invariant,
            "status": negative_control_status,
        }
        for control, invariant in gate.D2_NEGATIVE_CONTROLS.items()
    ]
    _write_csv(
        root, gate.D2_OUTPUTS[4], gate.D2_NEGATIVE_FIELDS, negative_rows
    )

    schedule_rows = []
    for n, schedule_case in gate._d2_required_cases():
        for step, operation in enumerate(gate.D2_TRACE_OPERATIONS):
            schedule_rows.append(
                {
                    "N": n,
                    "schedule_case": schedule_case,
                    "step": step,
                    "operation": operation,
                    "accumulator_index": "final" if operation == "final_bind" else step,
                    "selector_bit": "public" if operation in {"setup", "sub_a", "final_bind"} else "mixed",
                    "status": "PASS",
                }
            )
    _write_csv(root, gate.D2_OUTPUTS[5], gate.D2_SCHEDULE_FIELDS, schedule_rows)

    if reject_phase:
        derived_decision = D2_REJECT
        phase_status = "REJECT"
    elif gamma_count > 4:
        derived_decision = "REJECT_D2_CLOSURE_GT_4"
        phase_status = "PASS"
    elif negative_control_status == "MISSED":
        derived_decision = "REJECT_D2_NEGATIVE_CONTROL"
        phase_status = "PASS"
    elif decision == D2_BLOCK:
        derived_decision = D2_BLOCK
        phase_status = "BLOCK"
    else:
        derived_decision = D2_PASS
        phase_status = "PASS"
    negative_status = {
        "DETECTED": "PASS",
        "MISSED": "REJECT",
        "INCOMPLETE": "BLOCK",
    }[negative_control_status]
    _write_csv(
        root,
        gate.D2_OUTPUTS[1],
        gate.D2_SUMMARY_FIELDS,
        [
            {
                "decision": derived_decision,
                "gamma_count": gamma_count,
                "phase_status": phase_status,
                "negative_controls_status": negative_status,
                "schedule_status": "PASS",
                "equation_revisions_used": 0,
            }
        ],
    )


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
    derived_cost = (
        "BLOCK"
        if cost == "BLOCK" or not projection
        else "REJECT"
        if Decimal(projection) < Decimal("1.10")
        else "PASS"
    )
    _write(root, gate.D3_OUTPUTS[0], "# fixture security and noise\n")
    _write(root, gate.D3_OUTPUTS[1], "# fixture complete cost\n")
    binding_rows = []
    for bits in (2, 3, 5, 8):
        valid = not (binding == "REJECT" and bits == 3)
        binding_rows.append(
            {
                "plaintext_bits": bits,
                "delta_integer": 2 ** (64 - bits),
                "delta_torus": f"2^-{bits}",
                "coefficient_min": -(2 ** (bits - 1)),
                "coefficient_max": 2 ** (bits - 1) - 1,
                "checker_min": -128,
                "checker_max": 128,
                "binder_operation": gate.D3_BINDER if valid else "torus_by_torus_multiplication",
                "status": "PASS" if valid else "REJECT",
            }
        )
    _write_csv(root, gate.D3_OUTPUTS[2], gate.D3_BINDING_FIELDS, binding_rows)

    security_rows = []
    for name, (realization, assumption) in gate.D3_SECURITY_OBJECTS.items():
        valid = not (security == "REJECT" and name == "selector_bit")
        security_rows.append(
            {
                "object": name,
                "realization": realization,
                "assumption": assumption if valid else "correlated_selector_errors",
                "status": "PASS" if valid else "REJECT",
            }
        )
    _write_csv(root, gate.D3_OUTPUTS[3], gate.D3_SECURITY_FIELDS, security_rows)

    noise_rows = [
        {
            "case": "external_product_lemma",
            "value": "MISSING" if noise == "BLOCK" else "ANCHORED",
            "limit": "REQUIRED",
            "source_anchor": "fixture:lemma",
            "status": "BLOCK" if noise == "BLOCK" else "PASS",
        }
    ]
    numeric_noise = {
        "covariance_lambda_max": ("1", "2"),
        "deterministic_l1": ("1", "2"),
        "deterministic_linf": ("1", "2"),
        "decode_margin": ("10", "5"),
        "union_failure_bound": ("0.001", "0.01"),
        "scalar_failure_bound": ("0.02", "0.02"),
        "b1_failure_bound": ("0.02", "0.02"),
        "target_failure_bound": ("0.01", "0.01"),
    }
    for case, (value, limit) in numeric_noise.items():
        status = "PASS"
        if noise == "REJECT" and case == "union_failure_bound":
            value = "0.02"
            status = "REJECT"
        noise_rows.append(
            {
                "case": case,
                "value": value,
                "limit": limit,
                "source_anchor": f"fixture:{case}",
                "status": status,
            }
        )
    _write_csv(root, gate.D3_OUTPUTS[4], gate.D3_NOISE_FIELDS, noise_rows)

    structural_rows = []
    h = 573440
    for variant in (
        "B1_exact_dense",
        "D_operator_generic",
        "D_operator_coeff_one_fast",
    ):
        for r in (1, 2, 4, 8):
            if variant == "B1_exact_dense":
                g = ""
                events = h
                products = (1 + r) ** 2
                materialized = 1 + r
                binding_products = 0
            else:
                g = 2
                events = h + 79872 if variant == "D_operator_generic" else h
                products = 8
                materialized = 4
                binding_products = 4 * r
            structural_rows.append(
                {
                    "variant": variant,
                    "r": r,
                    "g": g,
                    "selector_events": events,
                    "products_per_event": products,
                    "selector_ring_products": events * products,
                    "materialized_components": materialized,
                    "late_binding_products": binding_products,
                    "ncmux_events": 5080,
                    "sub_a_calls": 39,
                    "status": "PASS",
                }
            )
    _write_csv(root, gate.D3_OUTPUTS[5], gate.D3_STRUCTURAL_FIELDS, structural_rows)

    if cost == "BLOCK":
        pessimistic = {
            "scenario": "pessimistic",
            "complete_ratio_vs_b1": "",
            "speedup_vs_b1": "",
            "ep_ratio": "",
            "materialization_ratio": "",
            "automorphism_ratio": "",
            "late_binding_us": "",
            "status": "BLOCK",
        }
    else:
        p = Decimal(projection)
        pessimistic = {
            "scenario": "pessimistic",
            "complete_ratio_vs_b1": format(Decimal(1) / p, "f"),
            "speedup_vs_b1": projection,
            "ep_ratio": "0.40",
            "materialization_ratio": "1.00",
            "automorphism_ratio": "1.00",
            "late_binding_us": "1",
            "status": "PASS" if p >= Decimal("1.10") else "REJECT",
        }
    projection_rows = [
        {
            "scenario": "central",
            "complete_ratio_vs_b1": "0.8",
            "speedup_vs_b1": "1.25",
            "ep_ratio": "0.32",
            "materialization_ratio": "0.80",
            "automorphism_ratio": "1.00",
            "late_binding_us": "1",
            "status": "PASS",
        },
        pessimistic,
    ]
    _write_csv(root, gate.D3_OUTPUTS[6], gate.D3_AMDAHL_FIELDS, projection_rows)

    resource_rows = []
    for variant in gate.D3_RESOURCE_VARIANTS:
        if variant in {"B0b", "B2"}:
            row = {field: "" for field in gate.D3_RESOURCE_FIELDS}
            row.update({"variant": variant, "status": "REQUIRED_NOT_YET_LOCAL"})
        else:
            scale = 3 if variant == "D" and resource == "REJECT" else 1
            row = {
                "variant": variant,
                "selector_key_bytes": 100 * scale,
                "automorphism_key_bytes": 100 * scale,
                "operator_state_bytes": 100 * scale,
                "scratch_bytes": 100 * scale,
                "output_bytes": 100 * scale,
                "rerandomization_bytes": 0,
                "keygen_work": 1,
                "late_binding_transforms": 1,
                "status": (
                    "REFERENCE"
                    if variant in {"B0a", "B1"}
                    else resource
                ),
            }
            if variant == "D" and resource == "BLOCK":
                for field in gate.D3_RESOURCE_FIELDS[1:-1]:
                    row[field] = ""
        resource_rows.append(row)
    _write_csv(root, gate.D3_OUTPUTS[7], gate.D3_RESOURCE_FIELDS, resource_rows)

    _write_csv(
        root,
        gate.D3_OUTPUTS[8],
        gate.D3_SUMMARY_FIELDS,
        [
            {
                "decision": selected,
                "binding_status": binding,
                "security_status": security,
                "noise_status": noise,
                "complete_cost_status": derived_cost,
                "resource_status": resource,
                "pessimistic_projection": projection,
            }
        ],
    )


class CandidateDGateTests(unittest.TestCase):
    def test_d2_summary_is_assertion_not_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_d2_fixture(root)
            _mutate_csv(
                root / gate.D2_OUTPUTS[1],
                row_index=0,
                field="decision",
                value=D2_REJECT,
            )
            with self.assertRaisesRegex(
                gate.AdmissionEvidenceError, "summary does not match"
            ):
                gate._recompute_d2(root)

    def test_d2_exact_sets_and_status_hash_semantics_are_enforced(self):
        mutations = (
            (gate.D2_OUTPUTS[2], 1, "basis_index", "0"),
            (gate.D2_OUTPUTS[3], 0, "status", "REJECT"),
            (gate.D2_OUTPUTS[4], 0, "control", "unregistered_control"),
            (gate.D2_OUTPUTS[5], 0, "operation", "changed_operation"),
        )
        for relative, row_index, field, value in mutations:
            with self.subTest(relative=relative, field=field):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    write_d2_fixture(root)
                    _mutate_csv(
                        root / relative,
                        row_index=row_index,
                        field=field,
                        value=value,
                    )
                    with self.assertRaises(gate.AdmissionEvidenceError):
                        gate._recompute_d2(root)

    def test_d3_summary_is_assertion_not_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_d3_fixture(root)
            _mutate_csv(
                root / gate.D3_OUTPUTS[8],
                row_index=0,
                field="decision",
                value=D3_COST_REJECT,
            )
            with self.assertRaisesRegex(
                gate.AdmissionEvidenceError, "summary does not match"
            ):
                gate._recompute_d3(root)

    def test_d3_each_canonical_map_is_mutation_sensitive(self):
        mutations = (
            (gate.D3_OUTPUTS[2], 1, "delta_integer", "1"),
            (gate.D3_OUTPUTS[3], 2, "assumption", "correlated_errors"),
            (gate.D3_OUTPUTS[4], 1, "value", "3"),
            (gate.D3_OUTPUTS[5], 0, "selector_ring_products", "1"),
            (gate.D3_OUTPUTS[6], 0, "ep_ratio", "0.31"),
            (gate.D3_OUTPUTS[7], 2, "status", "PASS"),
        )
        for relative, row_index, field, value in mutations:
            with self.subTest(relative=relative, field=field):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    write_d3_fixture(root)
                    _mutate_csv(
                        root / relative,
                        row_index=row_index,
                        field=field,
                        value=value,
                    )
                    with self.assertRaises(gate.AdmissionEvidenceError):
                        gate._recompute_d3(root)

    def test_static_d2_d3_parsers_cannot_authorize_without_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_d2_fixture(root)
            write_d3_fixture(root)
            d2 = gate._recompute_d2(root)
            d3 = gate._recompute_d3(root)
            self.assertEqual(d2.decision, D2_PASS)
            self.assertEqual(d3.decision, D3_PASS)
            untrusted = passing_result(
                d2_replay_authenticated=False,
                d3_replay_authenticated=False,
            )
            self.assertEqual(gate.derive_candidate_d_decision(untrusted), BLOCK)

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
        self.assertIn("D1 REJECT/BLOCK", result.resume_condition)
        self.assertIn("do not run D2", result.resume_condition)
        self.assertIn("D2 REJECT/BLOCK", result.resume_condition)
        self.assertIn("do not run D3", result.resume_condition)
        self.assertIn(
            "--controller-commit " + CONTROLLER_COMMIT,
            result.resume_condition,
        )
        self.assertIn("run_candidate_d_d2_closure.py", result.resume_condition)
        self.assertIn("run_candidate_d_d3_admission.py", result.resume_condition)
        self.assertIn("historical Task 9 ledgers", result.resume_condition)
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
                "D2_replay_authentication",
                "D2_gamma_count",
                "D2_negative_controls",
                "D3_integer_binding",
                "D3_replay_authentication",
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
        source_paths = tuple(
            dict.fromkeys(
                (
                    *gate.PINNED_INPUTS,
                    *gate.D2_REPLAY_CONTRACT.pinned_paths,
                    *gate.D3_REPLAY_CONTRACT.pinned_paths,
                    *gate.RESUME_PINNED_INPUTS,
                )
            )
        )
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
                        root,
                        result,
                        input_commit=FIXTURE_COMMIT,
                        controller_commit=result.controller_commit,
                        run_date=result.run_date,
                        execution_platform=result.execution_platform,
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
                        root,
                        result,
                        input_commit=FIXTURE_COMMIT,
                        controller_commit=result.controller_commit,
                        run_date=result.run_date,
                        execution_platform=result.execution_platform,
                    )

    def test_cli_requires_explicit_input_commit(self):
        with self.assertRaises(SystemExit):
            gate.main([])


if __name__ == "__main__":
    unittest.main()
