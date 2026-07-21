#!/usr/bin/env python3
"""Derive and publish the atomic Candidate D D0-D3 admission decision."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
from io import StringIO
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import research.mat_sab.candidate_d_baseline as d0_baseline  # noqa: E402
from research.mat_sab.candidate_d_stage_replay import (  # noqa: E402
    StageReplayContract,
    StageReplayError,
    StageReplayUnavailable,
    execute_stage_replay,
)
from research.mat_sab.candidate_d_literature import (  # noqa: E402
    BLOCK_D1,
    PASS_D1,
    REJECT_D1,
)
from scripts.mat_sab_research_state import load_state  # noqa: E402
import scripts.run_candidate_d_d1_literature as d1_literature  # noqa: E402


CURRENT_INPUT_COMMIT = "c8221ad0fcd8413753ca4c3072f49460972de454"
HISTORICAL_BLOCK_COMMIT = "fba794ce8820fb2ab167bf928c9cdae67ed508b9"
ERRATUM_PREDECESSOR_EVIDENCE_COMMIT = (
    "95bc17959e6bfa25e8504481cbd26ee265bbe9c7"
)
ERRATUM_PREDECESSOR_CONTROLLER_COMMIT = (
    "8a953a54b8799089d2e7fef6d3951581b4cf8fd4"
)
ERRATUM_PREDECESSOR_EVIDENCE_PATH = (
    "repro/candidate_d_admission/decision_evidence.json"
)
ERRATUM_PREDECESSOR_EVIDENCE_SHA256 = (
    "7287a6d11ca0a61ff4abb8371fd4d6c24a0fe005781e38d53e3964cbd5506036"
)
OUT = Path("repro/candidate_d_admission")
REPORT = Path("docs/candidate_d_admission_report.md")

ADMIT = "ADMIT_CANDIDATE_D_TO_ISOLATED_ENCRYPTED_OPERATOR_IMPLEMENTATION"
REJECT_PRIOR_ART = "REJECT_CANDIDATE_D_PRIOR_ART_SUBSUMPTION_ROUTE_E"
REJECT_CLOSURE = "REJECT_CANDIDATE_D_OPERATOR_CLOSURE_ROUTE_E"
REJECT_BINDING_NOISE_SECURITY = (
    "REJECT_CANDIDATE_D_BINDING_NOISE_SECURITY_ROUTE_E"
)
REJECT_COMPLETE_COST = (
    "REJECT_CANDIDATE_D_NONPOSITIVE_COMPLETE_COST_ROUTE_E"
)
BLOCK = "BLOCK_CANDIDATE_D_INCOMPLETE_EVIDENCE"
DECISIONS = {
    ADMIT,
    REJECT_PRIOR_ART,
    REJECT_CLOSURE,
    REJECT_BINDING_NOISE_SECURITY,
    REJECT_COMPLETE_COST,
    BLOCK,
}

SKIPPED_D1_BLOCK = "SKIPPED_D1_BLOCK"
SKIPPED_D1_REJECT = "SKIPPED_D1_REJECT"
SKIPPED_D2_BLOCK = "SKIPPED_D2_BLOCK"
SKIPPED_D2_REJECT = "SKIPPED_D2_REJECT"
NONE = ""

D2_PASS_DECISION = "PASS_D2_OPERATOR_CLOSURE_G_LE_4"
D2_REJECT_DECISIONS = {
    "REJECT_D2_PHASE_EQUIVALENCE",
    "REJECT_D2_CLOSURE_GT_4",
    "REJECT_D2_NEGATIVE_CONTROL",
    "REJECT_D2_REVISION_EXHAUSTED",
}
D2_BLOCK_DECISIONS = {"BLOCK_D2_SOURCE_OR_EXACT_CHECKER_INCOMPLETE"}
D3_PASS_DECISION = (
    "PASS_D3_STANDARD_NOISE_FEASIBLE_COMPLETE_PROJECTION_GE_1_10"
)
D3_REJECT_DECISIONS = {
    "REJECT_D3_ILLEGAL_BINDING_DOMAIN",
    "REJECT_D3_NONSTANDARD_SECURITY_OBJECT",
    "REJECT_D3_DECODING_MARGIN",
    "REJECT_D3_COMPLETE_PROJECTION_LT_1_10",
    "REJECT_D3_RESOURCE_OVERHEAD",
}
D3_BLOCK_DECISIONS = {
    "BLOCK_D3_NOISE_LEMMA_INCOMPLETE",
    "BLOCK_D3_NOISE_TARGET_UNANCHORED",
    "BLOCK_D3_COST_INPUT_INCOMPLETE",
}

D0_OUTPUTS = (
    "docs/candidate_d_d0_baseline.md",
    "repro/candidate_d_admission/baseline_manifest.csv",
    "repro/candidate_d_admission/environment.csv",
    "repro/candidate_d_admission/reproduction_commands.md",
)
D1_OUTPUTS = (
    "docs/candidate_d_d1_novelty_audit.md",
    "repro/candidate_d_admission/literature_sources.csv",
    "repro/candidate_d_admission/claim_overlap.csv",
    "repro/candidate_d_admission/novelty_gate.csv",
)
D2_OUTPUTS = (
    "theory_checks/candidate_d_operator_closure.md",
    "repro/candidate_d_admission/d2_summary.csv",
    "repro/candidate_d_admission/closure_basis.csv",
    "repro/candidate_d_admission/phase_equivalence.csv",
    "repro/candidate_d_admission/negative_controls.csv",
    "repro/candidate_d_admission/schedule_trace.csv",
)
D3_OUTPUTS = (
    "theory_checks/candidate_d_security_noise.md",
    "theory_checks/candidate_d_complete_cost.md",
    "repro/candidate_d_admission/binding_domain.csv",
    "repro/candidate_d_admission/security_object_map.csv",
    "repro/candidate_d_admission/noise_bound.csv",
    "repro/candidate_d_admission/structural_cost.csv",
    "repro/candidate_d_admission/amdahl_projection.csv",
    "repro/candidate_d_admission/resource_projection.csv",
    "repro/candidate_d_admission/d3_summary.csv",
)

D2_REPLAY_CONTRACT = StageReplayContract(
    stage="D2",
    runner="scripts/run_candidate_d_d2_closure.py",
    scientific_sources=(
        "research/__init__.py",
        "research/mat_sab/__init__.py",
        "research/mat_sab/candidate_d_operator_closure.py",
        "research/mat_sab/candidate_d_source_map.py",
        "research/mat_sab/finite_linear.py",
        "research/mat_sab/negacyclic_operator.py",
        "scripts/__init__.py",
    ),
    required_inputs=(
        "src/sparse_amortized_bootstrap.c",
        "src/sab_pvw.c",
        "include/sab.h",
        "include/sab_pvw.h",
        "main.c",
    ),
    canonical_outputs=D2_OUTPUTS,
    decisions=(D2_PASS_DECISION, *sorted(D2_REJECT_DECISIONS), *sorted(D2_BLOCK_DECISIONS)),
    scientific_authority=True,
)
D3_REPLAY_CONTRACT = StageReplayContract(
    stage="D3",
    runner="scripts/run_candidate_d_d3_admission.py",
    scientific_sources=(
        "research/__init__.py",
        "research/mat_sab/__init__.py",
        "research/mat_sab/candidate_d_admission.py",
        "research/mat_sab/candidate_d_operator_closure.py",
        "research/mat_sab/candidate_d_source_map.py",
        "research/mat_sab/negacyclic_operator.py",
        "scripts/__init__.py",
    ),
    required_inputs=(
        *D2_OUTPUTS,
        "repro/candidate_d_admission/baseline_manifest.csv",
        "repro/stage331_current_head_highstat_refresh/summary.csv",
        "repro/stage322_schedule_profile_attribution/profile_summary.csv",
        "repro/stage322_schedule_profile_attribution/component_budget.csv",
        "src/sparse_amortized_bootstrap.c",
        "src/sab_pvw.c",
        "include/sab.h",
        "include/sab_pvw.h",
        "main.c",
    ),
    canonical_outputs=D3_OUTPUTS,
    decisions=(D3_PASS_DECISION, *sorted(D3_REJECT_DECISIONS), *sorted(D3_BLOCK_DECISIONS)),
    scientific_authority=True,
)


def _task9_command(input_placeholder: str, controller_commit: str) -> str:
    metadata = (
        "--run-date <YYYY-MM-DD> "
        "--execution-platform <audited-evidence-platform>"
    )
    return (
        "python scripts/run_candidate_d_admission.py --input-commit "
        f"{input_placeholder} --controller-commit {controller_commit} {metadata}; "
        "python scripts/apply_candidate_d_admission.py --input-commit "
        f"{input_placeholder} --controller-commit {controller_commit} {metadata}"
    )


def resume_condition_for(stage: str, *, controller_commit: str) -> str:
    if re.fullmatch(r"[0-9a-f]{40}", controller_commit) is None:
        raise ValueError("controller commit must be a full lowercase SHA-1")
    if stage == "D1_BLOCK":
        return (
            "Obtain the latest second revision of IACR ePrint 2026/068 dated "
            "2026-07-16 (not the archived January first-version PDF); set "
            "NTRU_AMORT_FULLTEXT_PATH=<latest-NTRU_AMORT_2026_068.pdf>; run "
            "NTRU_AMORT_FULLTEXT_PATH=<latest-NTRU_AMORT_2026_068.pdf> bash "
            "scripts/fetch_candidate_d_primary_sources.sh; record the verified "
            "PDF SHA-256, canonical pdftotext SHA-256, page range, and claim "
            "anchors for NTRU_AMORT_2026_068 in "
            "literature/candidate_d_source_registry.json; update "
            "REQUIRED_SOURCE_BINDINGS in "
            "research/mat_sab/candidate_d_literature.py; run python "
            "scripts/run_candidate_d_d1_literature.py and commit as "
            "<new-D1-commit>. If D1 REJECT/BLOCK, do not run D2; run Task 9 "
            "with the last-stage <new-D1-commit>: "
            + _task9_command("<new-D1-commit>", controller_commit)
            + ". If D1 PASS, implement the canonical Tasks 4-6 D2 replay "
            "contract, then run python scripts/run_candidate_d_d2_closure.py "
            "--root <absolute-repository-root> --output-root "
            "<staging-output-directory> --input-commit <new-D1-commit> "
            f"--controller-commit {controller_commit}; install the verified "
            "canonical D2 outputs and commit as <new-D2-commit>. If D2 "
            "REJECT/BLOCK, do not run D3; run Task 9 with the last-stage "
            "<new-D2-commit>: "
            + _task9_command("<new-D2-commit>", controller_commit)
            + ". If D2 PASS, implement canonical Tasks 7-8 D3, then run "
            "python scripts/run_candidate_d_d3_admission.py --root "
            "<absolute-repository-root> --output-root "
            "<staging-output-directory> --input-commit <new-D2-commit> "
            f"--controller-commit {controller_commit}; install the verified "
            "canonical D3 outputs, commit as <new-D3-commit>, then run Task 9: "
            + _task9_command("<new-D3-commit>", controller_commit)
            + ". Every stage commit must descend from the frozen input; Task "
            "9 appends a commit-specific terminal record and never rewrites "
            "the historical Task 9 ledgers or BLOCK."
        )
    if stage == "D2_BLOCK":
        return (
            "Implement or repair the canonical Tasks 4-6 D2 generator and "
            "exact checker under docs/candidate_d_task9_replay_contract.md; "
            "run python scripts/run_candidate_d_d2_closure.py --root "
            "<absolute-repository-root> --output-root "
            "<staging-output-directory> --input-commit "
            "<last-valid-stage-commit> --controller-commit "
            f"{controller_commit}; install the verified outputs and commit "
            "the source-derived D2 artifacts as "
            "<new-D2-commit>, and rerun Task 9 with "
            + _task9_command("<new-D2-commit>", controller_commit)
            + ". If D2 REJECT/BLOCK, do not run D3; only D2 PASS may run "
            "python scripts/run_candidate_d_d3_admission.py --root "
            "<absolute-repository-root> --output-root "
            "<staging-output-directory> --input-commit <new-D2-commit> "
            f"--controller-commit {controller_commit} and proceed to Tasks "
            "7-8."
        )
    if stage == "D3_BLOCK":
        return (
            "Implement or repair the canonical Tasks 7-8 D3 generator, fixed "
            "noise/security anchors, frozen B1 profile binding, and complete "
            "cost/resource model under "
            "docs/candidate_d_task9_replay_contract.md; run python "
            "scripts/run_candidate_d_d3_admission.py --root "
            "<absolute-repository-root> --output-root "
            "<staging-output-directory> --input-commit "
            "<last-valid-stage-commit> --controller-commit "
            f"{controller_commit}; install the verified outputs, commit the "
            "canonical D3 artifacts as <new-D3-commit>, then rerun Task 9 with "
            + _task9_command("<new-D3-commit>", controller_commit)
            + "."
        )
    if stage in {"D1_REJECT", "D2_REJECT", "D3_TERMINAL", "NONE"}:
        return "none"
    raise ValueError(f"unknown Candidate D resume stage: {stage}")

D2_SUMMARY_FIELDS = (
    "decision",
    "gamma_count",
    "phase_status",
    "negative_controls_status",
    "schedule_status",
    "equation_revisions_used",
)
D2_CLOSURE_FIELDS = (
    "basis_index",
    "automorphism_label",
    "gamma_count",
    "equation_revision",
    "search_status",
    "status",
)
D2_PHASE_FIELDS = (
    "N",
    "schedule_case",
    "basis_index",
    "operation",
    "accumulator_index",
    "selector_bit",
    "gamma_count",
    "matrix_rank",
    "expected_hash",
    "actual_hash",
    "status",
)
D2_NEGATIVE_FIELDS = ("control", "failed_invariant", "status")
D2_SCHEDULE_FIELDS = (
    "N",
    "schedule_case",
    "step",
    "operation",
    "accumulator_index",
    "selector_bit",
    "status",
)
D2_NEGATIVE_CONTROLS = {
    "remove_tau_minus_one_channel": "operator_basis_closure",
    "omit_tau_minus_one_swap": "ncmux_channel_permutation",
    "positive_negacyclic_wrap": "negacyclic_wrap_sign",
    "skip_sub_a_rotation": "sub_a_phase_equivalence",
    "coeff_one_fast_with_zero_selector": "include_zero_fast_path_guard",
    "wrong_butterfly_source_index": "rgsw_butterfly_schedule",
}
D2_TRACE_OPERATIONS = (
    "setup",
    "cmux_mu0",
    "cmux_mu1",
    "ncmux_mu0",
    "ncmux_mu1",
    "rgsw_monomial",
    "sub_a",
    "final_bind",
)

D3_SUMMARY_FIELDS = (
    "decision",
    "binding_status",
    "security_status",
    "noise_status",
    "complete_cost_status",
    "resource_status",
    "pessimistic_projection",
)
D3_BINDING_FIELDS = (
    "plaintext_bits",
    "delta_integer",
    "delta_torus",
    "coefficient_min",
    "coefficient_max",
    "checker_min",
    "checker_max",
    "binder_operation",
    "status",
)
D3_SECURITY_FIELDS = ("object", "realization", "assumption", "status")
D3_NOISE_FIELDS = ("case", "value", "limit", "source_anchor", "status")
D3_STRUCTURAL_FIELDS = (
    "variant",
    "r",
    "g",
    "selector_events",
    "products_per_event",
    "selector_ring_products",
    "materialized_components",
    "late_binding_products",
    "ncmux_events",
    "sub_a_calls",
    "status",
)
D3_AMDAHL_FIELDS = (
    "scenario",
    "complete_ratio_vs_b1",
    "speedup_vs_b1",
    "ep_ratio",
    "materialization_ratio",
    "automorphism_ratio",
    "late_binding_us",
    "status",
)
D3_RESOURCE_FIELDS = (
    "variant",
    "selector_key_bytes",
    "automorphism_key_bytes",
    "operator_state_bytes",
    "scratch_bytes",
    "output_bytes",
    "rerandomization_bytes",
    "keygen_work",
    "late_binding_transforms",
    "status",
)
D3_BINDER = "public_bounded_integer_polynomial_multiplication"
D3_SECURITY_OBJECTS = {
    "initial_operator_basis": (
        "public_trivial_rlwe_encoding_of_scaled_monomials",
        "public_setup_no_hidden_secret",
    ),
    "operator_channel": (
        "ordinary_trlwe_under_one_output_secret",
        "standard_rlwe",
    ),
    "selector_bit": (
        "existing_scalar_trgsw_sample",
        "standard_ggsw",
    ),
    "ncmux_automorphism": (
        "existing_trlwe_automorphism_key_switch",
        "standard_rlwe_key_switching",
    ),
    "rotation": ("public_monomial_multiplication", "public_linear_map"),
    "late_binding": (
        D3_BINDER,
        "public_integer_polynomial_linear_map",
    ),
    "extraction_packing": (
        "existing_extraction_and_key_switching",
        "standard_lwe_rlwe_key_switching",
    ),
    "vector_of_outputs": (
        "public_post_processing_with_d4_rerandomization_if_required",
        "semantic_security_not_independent_ciphertext_distribution",
    ),
}
D3_NOISE_CASES = (
    "external_product_lemma",
    "covariance_lambda_max",
    "deterministic_l1",
    "deterministic_linf",
    "decode_margin",
    "union_failure_bound",
    "scalar_failure_bound",
    "b1_failure_bound",
    "target_failure_bound",
)
D3_RESOURCE_VARIANTS = ("B0a", "B0b", "B1", "B2", "D")
RESUME_PINNED_INPUTS = (
    "hypotheses/hypothesis_register.yaml",
    "repro/artifact_manifest.md",
    "repro/reproduction_checklist.md",
    "repro/run_log.csv",
    "research_state.yaml",
)

PINNED_INPUTS = (
    "docs/superpowers/plans/2026-07-20-candidate-d-lut-late-binding-admission.md",
    "docs/superpowers/specs/2026-07-20-lut-late-binding-operator-sab-design.md",
    "literature/candidate_d_source_registry.json",
    "research/mat_sab/candidate_d_baseline.py",
    "research/mat_sab/candidate_d_literature.py",
    "scripts/run_candidate_d_d0_freeze.py",
    "scripts/run_candidate_d_d1_literature.py",
    *D0_OUTPUTS,
    *D1_OUTPUTS,
)
RUNTIME_SOURCES = (
    "scripts/run_candidate_d_admission.py",
    "scripts/apply_candidate_d_admission.py",
    "scripts/mat_sab_research_state.py",
    "research/mat_sab/candidate_d_stage_replay.py",
    "docs/candidate_d_task9_replay_contract.md",
    "docs/candidate_d_task9_threat_model.md",
)
DECISION_EVIDENCE_V3_RUNTIME_SOURCES = (
    "scripts/run_candidate_d_admission.py",
    "scripts/apply_candidate_d_admission.py",
    "scripts/mat_sab_research_state.py",
    "research/mat_sab/candidate_d_stage_replay.py",
    "docs/candidate_d_task9_replay_contract.md",
)
GENERATED_OUTPUTS = (
    REPORT.as_posix(),
    (OUT / "summary.csv").as_posix(),
    (OUT / "proof_gate.csv").as_posix(),
    (OUT / "decision_evidence.json").as_posix(),
    (OUT / "artifact_index.csv").as_posix(),
)
INDEXED_ARTIFACTS = tuple(
    sorted(
        {
            *D0_OUTPUTS,
            *D1_OUTPUTS,
            REPORT.as_posix(),
            (OUT / "summary.csv").as_posix(),
            (OUT / "proof_gate.csv").as_posix(),
            (OUT / "decision_evidence.json").as_posix(),
        }
    )
)

SUMMARY_FIELDS = (
    "decision",
    "d0_status",
    "d0_decision",
    "d1_status",
    "d1_decision",
    "d1_missing_evidence",
    "d2_status",
    "d2_decision",
    "d2_replay_authenticated",
    "d3_replay_authenticated",
    "gamma_count",
    "negative_controls_status",
    "binding_status",
    "security_status",
    "noise_status",
    "complete_cost_status",
    "resource_status",
    "pessimistic_projection",
    "pre_application_permission",
    "production_hot_path_permission",
    "input_commit",
    "controller_commit",
    "historical_block_commit",
    "predecessor_evidence_commit",
    "predecessor_controller_commit",
    "predecessor_decision_evidence_sha256",
    "run_date",
    "execution_platform",
    "resume_condition",
    "decision_evidence_binding_sha256",
)
PROOF_FIELDS = ("gate", "status", "classification", "evidence")


class AdmissionEvidenceError(RuntimeError):
    pass


@dataclass(frozen=True)
class AdmissionResult:
    d0_status: str
    d0_decision: str
    d1_status: str
    d1_decision: str
    d1_missing_evidence: tuple[str, ...]
    d2_status: str
    d2_decision: str
    d2_replay_authenticated: bool
    d3_replay_authenticated: bool
    gamma_count: int | None
    negative_controls_status: str
    binding_status: str
    security_status: str
    noise_status: str
    complete_cost_status: str
    resource_status: str
    pessimistic_projection: str
    pre_application_permission: bool
    decision: str
    resume_condition: str
    input_commit: str
    controller_commit: str
    run_date: str
    execution_platform: str
    source_hashes: tuple[tuple[str, str], ...]
    runtime_source_hashes: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class D2Evidence:
    status: str
    decision: str
    gamma_count: int | None
    negative_controls_status: str


@dataclass(frozen=True)
class D3Evidence:
    decision: str
    binding_status: str
    security_status: str
    noise_status: str
    complete_cost_status: str
    resource_status: str
    pessimistic_projection: str


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _canonical_json(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        + "\n"
    ).encode("ascii")


def _csv_bytes(
    fields: tuple[str, ...], rows: Iterable[Mapping[str, object]]
) -> bytes:
    stream = StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=fields,
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("ascii")


def _resolved_root(root: Path) -> Path:
    try:
        resolved = Path(root).resolve(strict=True)
    except OSError as error:
        raise AdmissionEvidenceError("repository root cannot be resolved") from error
    if not resolved.is_dir():
        raise AdmissionEvidenceError("repository root is not a directory")
    return resolved


def _safe_path(
    root: Path,
    relative: str | Path,
    label: str,
    *,
    strict: bool,
    require_file: bool = False,
) -> Path:
    root = _resolved_root(root)
    declared = Path(relative)
    if declared.is_absolute() or ".." in declared.parts:
        raise AdmissionEvidenceError(f"{label} escapes repository root")
    current = root
    for part in declared.parts:
        current = current / part
        if current.is_symlink():
            raise AdmissionEvidenceError(f"{label} may not be a symlink")
    try:
        resolved = (root / declared).resolve(strict=strict)
    except OSError as error:
        raise AdmissionEvidenceError(f"{label} cannot be resolved") from error
    if not resolved.is_relative_to(root):
        raise AdmissionEvidenceError(f"{label} escapes repository root")
    if require_file and not resolved.is_file():
        raise AdmissionEvidenceError(f"{label} is not a regular file")
    return resolved


def _resolve_input_commit(root: Path, input_commit: str) -> str:
    if re.fullmatch(r"[0-9a-f]{40}", input_commit) is None:
        raise AdmissionEvidenceError("input commit must be a full lowercase SHA-1")
    try:
        resolved = subprocess.run(
            ["git", "rev-parse", "--verify", input_commit],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise AdmissionEvidenceError("input commit cannot be resolved") from error
    if resolved != input_commit:
        raise AdmissionEvidenceError("input commit did not resolve exactly")
    try:
        object_type = subprocess.run(
            ["git", "cat-file", "-t", resolved],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise AdmissionEvidenceError("input commit type cannot be read") from error
    if object_type != "commit":
        raise AdmissionEvidenceError("input commit does not name a commit")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", input_commit, "HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if ancestor.returncode != 0:
        raise AdmissionEvidenceError("input commit is not an ancestor of HEAD")
    return resolved


def _git_blob(root: Path, commit: str, relative: str) -> bytes:
    try:
        entry = subprocess.run(
            ["git", "ls-tree", commit, "--", relative],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.rstrip("\n")
    except (OSError, subprocess.CalledProcessError) as error:
        raise AdmissionEvidenceError(
            f"cannot inspect pinned input: {relative}"
        ) from error
    if not entry or "\t" not in entry:
        raise AdmissionEvidenceError(f"pinned input is missing: {relative}")
    metadata, recorded_path = entry.split("\t", 1)
    try:
        mode, object_type, object_id = metadata.split()
    except ValueError as error:
        raise AdmissionEvidenceError(
            f"malformed pinned input entry: {relative}"
        ) from error
    if (
        recorded_path != relative
        or object_type != "blob"
        or mode not in {"100644", "100755"}
    ):
        raise AdmissionEvidenceError(
            f"pinned input is not a regular file: {relative}"
        )
    try:
        return subprocess.run(
            ["git", "cat-file", "blob", object_id],
            cwd=root,
            check=True,
            capture_output=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as error:
        raise AdmissionEvidenceError(
            f"cannot read pinned input: {relative}"
        ) from error


def _pinned_source_hashes(
    root: Path,
    input_commit: str,
    paths: tuple[str, ...] = PINNED_INPUTS,
) -> tuple[tuple[str, str], ...]:
    commit = _resolve_input_commit(root, input_commit)
    if input_commit != CURRENT_INPUT_COMMIT:
        if subprocess.run(
            ["git", "merge-base", "--is-ancestor", CURRENT_INPUT_COMMIT, input_commit],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        ).returncode != 0:
            raise AdmissionEvidenceError(
                "resume input commit is not a strict descendant of the frozen BLOCK input"
            )
    rows = []
    for relative in paths:
        path = _safe_path(
            root,
            relative,
            f"pinned input {relative}",
            strict=True,
            require_file=True,
        )
        blob = _git_blob(root, commit, relative)
        content = path.read_bytes()
        if content != blob:
            raise AdmissionEvidenceError(
                f"working input differs from pinned commit: {relative}"
            )
        rows.append((relative, _sha256_bytes(blob)))
    return tuple(rows)


def _commit_only_hashes(
    root: Path, input_commit: str, paths: tuple[str, ...]
) -> tuple[tuple[str, str], ...]:
    commit = _resolve_input_commit(root, input_commit)
    return tuple(
        (relative, _sha256_bytes(_git_blob(root, commit, relative)))
        for relative in paths
    )


def _controller_source_hashes(
    root: Path, controller_commit: str
) -> tuple[tuple[str, str], ...]:
    commit = _resolve_input_commit(root, controller_commit)
    rows = []
    for relative in RUNTIME_SOURCES:
        path = _safe_path(
            root,
            relative,
            f"runtime source {relative}",
            strict=True,
            require_file=True,
        )
        blob = _git_blob(root, commit, relative)
        if path.read_bytes() != blob:
            raise AdmissionEvidenceError(
                f"working controller source differs from controller commit: {relative}"
            )
        rows.append((relative, _sha256_bytes(blob)))
    return tuple(rows)


def _validate_module_origins(root: Path) -> None:
    expected = {
        d0_baseline: "research/mat_sab/candidate_d_baseline.py",
        d1_literature: "scripts/run_candidate_d_d1_literature.py",
    }
    for module, relative in expected.items():
        origin = getattr(module, "__file__", None)
        if origin is None or Path(origin).resolve() != (root / relative).resolve():
            raise AdmissionEvidenceError(
                f"local module origin mismatch: {relative}"
            )


def _strict_csv_bytes(
    content: bytes, fields: tuple[str, ...], label: str
) -> tuple[dict[str, str], ...]:
    try:
        text = content.decode("ascii")
        records = list(csv.reader(StringIO(text, newline=""), strict=True))
    except (UnicodeError, csv.Error) as error:
        raise AdmissionEvidenceError(f"{label} is malformed") from error
    if (
        not records
        or tuple(records[0]) != fields
        or len(records[0]) != len(set(records[0]))
        or any(len(row) != len(fields) for row in records[1:])
    ):
        raise AdmissionEvidenceError(f"{label} is malformed")
    return tuple(dict(zip(fields, row)) for row in records[1:])


def _recompute_d0(root: Path) -> str:
    stage = Path(tempfile.mkdtemp(prefix=".candidate-d-d0-", dir=root))
    try:
        decision = d0_baseline.build_d0_artifacts(root, stage)
        for relative in D0_OUTPUTS:
            expected = stage / relative
            actual = _safe_path(
                root,
                relative,
                f"D0 artifact {relative}",
                strict=True,
                require_file=True,
            )
            if not expected.is_file() or expected.read_bytes() != actual.read_bytes():
                raise AdmissionEvidenceError(
                    f"D0 artifact does not match fresh source evidence: {relative}"
                )
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    return decision


def _recompute_d1(root: Path) -> tuple[str, tuple[str, ...]]:
    decision, artifacts = d1_literature.build_candidate_d_d1_artifacts(root)
    for relative in D1_OUTPUTS:
        key = Path(relative)
        actual = _safe_path(
            root,
            key,
            f"D1 artifact {relative}",
            strict=True,
            require_file=True,
        )
        if key not in artifacts or actual.read_bytes() != artifacts[key]:
            raise AdmissionEvidenceError(
                f"D1 artifact does not match fresh source evidence: {relative}"
            )
    fields = (
        "source_id",
        "title",
        "year",
        "official_url",
        "fulltext_url",
        "registry_status",
        "verification_status",
        "pdf_sha256",
        "text_sha256",
        "page_range",
        "source_binding_sha256",
        "validation_errors",
    )
    rows = _strict_csv_bytes(
        artifacts[Path("repro/candidate_d_admission/literature_sources.csv")],
        fields,
        "fresh D1 literature sources",
    )
    missing = tuple(
        row["source_id"]
        for row in rows
        if row["verification_status"] != "FULLTEXT_REVIEWED"
    )
    return decision, missing


def _replay_d2(
    root: Path, *, input_commit: str, controller_commit: str
) -> tuple[D2Evidence, bool]:
    try:
        replayed = execute_stage_replay(
            root,
            D2_REPLAY_CONTRACT,
            input_commit=input_commit,
            controller_commit=controller_commit,
        )
    except (StageReplayUnavailable, StageReplayError):
        return (
            D2Evidence(
                "BLOCK",
                "BLOCK_D2_SOURCE_OR_EXACT_CHECKER_INCOMPLETE",
                None,
                "BLOCK",
            ),
            False,
        )
    if not replayed.scientific_authority:
        raise AdmissionEvidenceError("non-scientific D2 replay cannot authorize a gate")
    evidence = _recompute_d2(root)
    if replayed.decision != evidence.decision:
        raise AdmissionEvidenceError(
            "D2 replay decision differs from secondary artifact parsing"
        )
    return evidence, True


def _replay_d3(
    root: Path, *, input_commit: str, controller_commit: str
) -> tuple[D3Evidence, bool]:
    try:
        replayed = execute_stage_replay(
            root,
            D3_REPLAY_CONTRACT,
            input_commit=input_commit,
            controller_commit=controller_commit,
        )
    except (StageReplayUnavailable, StageReplayError):
        return (
            D3Evidence(
                "BLOCK_D3_COST_INPUT_INCOMPLETE",
                "BLOCK",
                "BLOCK",
                "BLOCK",
                "BLOCK",
                "BLOCK",
                NONE,
            ),
            False,
        )
    if not replayed.scientific_authority:
        raise AdmissionEvidenceError("non-scientific D3 replay cannot authorize a gate")
    evidence = _recompute_d3(root)
    if replayed.decision != evidence.decision:
        raise AdmissionEvidenceError(
            "D3 replay decision differs from secondary artifact parsing"
        )
    return evidence, True


def _require_source_artifacts(root: Path, paths: tuple[str, ...]) -> None:
    for relative in paths:
        path = _safe_path(
            root,
            relative,
            f"source artifact {relative}",
            strict=True,
            require_file=True,
        )
        if not path.read_bytes():
            raise AdmissionEvidenceError(f"source artifact is empty: {relative}")


def _source_csv_rows(
    root: Path,
    relative: str,
    fields: tuple[str, ...],
) -> tuple[dict[str, str], ...]:
    path = _safe_path(
        root,
        relative,
        f"source artifact {relative}",
        strict=True,
        require_file=True,
    )
    content = path.read_bytes()
    try:
        text = content.decode("ascii")
        records = list(csv.reader(StringIO(text, newline=""), strict=True))
    except (UnicodeError, csv.Error) as error:
        raise AdmissionEvidenceError(
            f"source artifact is malformed: {relative}"
        ) from error
    if not records or len(records[0]) != len(set(records[0])):
        raise AdmissionEvidenceError(f"source artifact is malformed: {relative}")
    if tuple(records[0]) != fields or any(
        len(row) != len(fields) for row in records[1:]
    ):
        raise AdmissionEvidenceError(f"source artifact is malformed: {relative}")
    return tuple(dict(zip(fields, row)) for row in records[1:])


def _one_source_row(
    root: Path,
    relative: str,
    required_fields: tuple[str, ...],
) -> dict[str, str]:
    rows = _source_csv_rows(root, relative, required_fields)
    if len(rows) != 1:
        raise AdmissionEvidenceError(
            f"source artifact must contain one row: {relative}"
        )
    return rows[0]


def _aggregate_status(rows: tuple[dict[str, str], ...], label: str) -> str:
    if not rows:
        raise AdmissionEvidenceError(f"{label} contains no evidence rows")
    statuses = [row["status"] for row in rows]
    if any(status not in {"PASS", "REJECT", "BLOCK"} for status in statuses):
        raise AdmissionEvidenceError(f"{label} contains an unknown status")
    if "REJECT" in statuses:
        return "REJECT"
    if "BLOCK" in statuses:
        return "BLOCK"
    return "PASS"


def _parse_int(
    value: str,
    label: str,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    if re.fullmatch(r"-?[0-9]+", value) is None:
        raise AdmissionEvidenceError(f"{label} is not an integer")
    parsed = int(value)
    if minimum is not None and parsed < minimum:
        raise AdmissionEvidenceError(f"{label} is below its minimum")
    if maximum is not None and parsed > maximum:
        raise AdmissionEvidenceError(f"{label} is above its maximum")
    return parsed


def _parse_decimal(
    value: str,
    label: str,
    *,
    positive: bool = False,
    nonnegative: bool = False,
) -> Decimal:
    try:
        parsed = Decimal(value)
    except InvalidOperation as error:
        raise AdmissionEvidenceError(f"{label} is not numeric") from error
    if not parsed.is_finite():
        raise AdmissionEvidenceError(f"{label} is not finite")
    if positive and parsed <= 0:
        raise AdmissionEvidenceError(f"{label} must be positive")
    if nonnegative and parsed < 0:
        raise AdmissionEvidenceError(f"{label} must be nonnegative")
    return parsed


def _d2_required_cases() -> tuple[tuple[int, str], ...]:
    cases: list[tuple[int, str]] = []
    for n, r_prec in ((8, 3), (16, 4)):
        names = [
            "binary_all_zero",
            "binary_all_one",
            "binary_alternating",
            *(f"binary_one_hot_{index}" for index in range(r_prec)),
            "binary_source_mixed",
            "include_zero_mu0",
            "include_zero_mu1",
            "coeff_one_fast_mu1",
        ]
        cases.extend((n, name) for name in names)
    return tuple(cases)


def _aggregate_d2_rows(statuses: Iterable[str], label: str) -> str:
    values = tuple(statuses)
    if not values or any(value not in {"PASS", "REJECT", "BLOCK"} for value in values):
        raise AdmissionEvidenceError(f"{label} contains an invalid status")
    if "REJECT" in values:
        return "REJECT"
    if "BLOCK" in values:
        return "BLOCK"
    return "PASS"


def _recompute_d2(root: Path) -> D2Evidence:
    _require_source_artifacts(root, D2_OUTPUTS)
    basis_rows = _source_csv_rows(
        root,
        "repro/candidate_d_admission/closure_basis.csv",
        D2_CLOSURE_FIELDS,
    )
    if not basis_rows:
        raise AdmissionEvidenceError("D2 closure basis contains no rows")
    basis_indices = [
        _parse_int(row["basis_index"], "D2 basis_index", minimum=0)
        for row in basis_rows
    ]
    gamma_values = [
        _parse_int(row["gamma_count"], "D2 gamma_count", minimum=1, maximum=32)
        for row in basis_rows
    ]
    revisions = [
        _parse_int(row["equation_revision"], "D2 equation revision", minimum=0, maximum=1)
        for row in basis_rows
    ]
    labels = [
        _parse_int(row["automorphism_label"], "D2 automorphism label", minimum=0)
        for row in basis_rows
    ]
    if (
        len(set(gamma_values)) != 1
        or len(set(revisions)) != 1
        or len(set(row["search_status"] for row in basis_rows)) != 1
        or basis_indices != list(range(len(basis_rows)))
        or len(set(labels)) != len(labels)
        or gamma_values[0] != len(basis_rows)
    ):
        raise AdmissionEvidenceError("D2 closure basis is inconsistent")
    gamma_count = gamma_values[0]
    search_status = basis_rows[0]["search_status"]
    closure_expected = {
        "FOUND": "PASS" if gamma_count <= 4 else "REJECT",
        "OVERFLOW": "REJECT",
        "REVISION_EXHAUSTED": "REJECT",
        "INCOMPLETE": "BLOCK",
    }.get(search_status)
    if closure_expected is None or any(
        row["status"] != closure_expected for row in basis_rows
    ):
        raise AdmissionEvidenceError("D2 closure search status is inconsistent")
    if search_status == "FOUND" and gamma_count > 4:
        raise AdmissionEvidenceError("D2 FOUND closure exceeds four channels")
    if search_status == "OVERFLOW" and gamma_count <= 4:
        raise AdmissionEvidenceError("D2 OVERFLOW closure does not exceed four channels")

    phase_rows = _source_csv_rows(
        root,
        "repro/candidate_d_admission/phase_equivalence.csv",
        D2_PHASE_FIELDS,
    )
    expected_phase_keys = {
        (n, case, basis_index)
        for n, case in _d2_required_cases()
        for basis_index in range(n)
    }
    phase_keys: set[tuple[int, str, int]] = set()
    phase_statuses = []
    for row in phase_rows:
        n = _parse_int(row["N"], "D2 phase N")
        basis_index = _parse_int(
            row["basis_index"], "D2 phase basis_index", minimum=0
        )
        key = (n, row["schedule_case"], basis_index)
        if key in phase_keys:
            raise AdmissionEvidenceError("D2 phase evidence contains a duplicate row")
        phase_keys.add(key)
        if (
            row["operation"] != "final_bind"
            or row["accumulator_index"] != "final"
            or row["selector_bit"] not in {"0", "1", "mixed", "public"}
            or _parse_int(row["gamma_count"], "D2 phase gamma_count") != gamma_count
            or not 1 <= _parse_int(row["matrix_rank"], "D2 matrix_rank") <= gamma_count
            or re.fullmatch(r"[0-9a-f]{64}", row["expected_hash"]) is None
            or row["status"] not in {"PASS", "REJECT", "BLOCK"}
        ):
            raise AdmissionEvidenceError("D2 phase evidence is malformed")
        if row["status"] == "PASS":
            if row["actual_hash"] != row["expected_hash"]:
                raise AdmissionEvidenceError("D2 PASS phase row has unequal hashes")
        elif row["status"] == "REJECT":
            if (
                re.fullmatch(r"[0-9a-f]{64}", row["actual_hash"]) is None
                or row["actual_hash"] == row["expected_hash"]
            ):
                raise AdmissionEvidenceError("D2 REJECT phase row lacks a mismatch")
        elif row["actual_hash"]:
            raise AdmissionEvidenceError("D2 BLOCK phase row must omit actual_hash")
        phase_statuses.append(row["status"])
    if phase_keys != expected_phase_keys:
        raise AdmissionEvidenceError("D2 phase evidence does not cover the exact case set")
    phase_status = _aggregate_d2_rows(phase_statuses, "D2 phase evidence")

    control_rows = _source_csv_rows(
        root,
        "repro/candidate_d_admission/negative_controls.csv",
        D2_NEGATIVE_FIELDS,
    )
    controls = {row["control"]: row for row in control_rows}
    if len(controls) != len(control_rows) or set(controls) != set(D2_NEGATIVE_CONTROLS):
        raise AdmissionEvidenceError("D2 negative controls do not match the exact set")
    for name, invariant in D2_NEGATIVE_CONTROLS.items():
        row = controls[name]
        if (
            row["failed_invariant"] != invariant
            or row["status"] not in {"DETECTED", "MISSED", "INCOMPLETE"}
        ):
            raise AdmissionEvidenceError("D2 negative-control evidence is inconsistent")
    control_statuses = [row["status"] for row in control_rows]
    if "MISSED" in control_statuses:
        negative_status = "REJECT"
    elif "INCOMPLETE" in control_statuses:
        negative_status = "BLOCK"
    else:
        negative_status = "PASS"

    schedule_rows = _source_csv_rows(
        root,
        "repro/candidate_d_admission/schedule_trace.csv",
        D2_SCHEDULE_FIELDS,
    )
    expected_trace_keys = {
        (n, case, step)
        for n, case in _d2_required_cases()
        for step in range(len(D2_TRACE_OPERATIONS))
    }
    trace_keys: set[tuple[int, str, int]] = set()
    schedule_statuses = []
    for row in schedule_rows:
        n = _parse_int(row["N"], "D2 schedule N")
        step = _parse_int(row["step"], "D2 schedule step", minimum=0)
        key = (n, row["schedule_case"], step)
        if key in trace_keys:
            raise AdmissionEvidenceError("D2 schedule contains a duplicate row")
        trace_keys.add(key)
        if (
            step >= len(D2_TRACE_OPERATIONS)
            or row["operation"] != D2_TRACE_OPERATIONS[step]
            or re.fullmatch(r"(?:final|[0-9]+)", row["accumulator_index"]) is None
            or row["selector_bit"] not in {"0", "1", "mixed", "public"}
            or row["status"] not in {"PASS", "REJECT", "BLOCK"}
        ):
            raise AdmissionEvidenceError("D2 schedule evidence is malformed")
        schedule_statuses.append(row["status"])
    if trace_keys != expected_trace_keys:
        raise AdmissionEvidenceError("D2 schedule does not cover the exact trace set")
    schedule_status = _aggregate_d2_rows(schedule_statuses, "D2 schedule")

    if phase_status == "REJECT" or schedule_status == "REJECT":
        decision = "REJECT_D2_PHASE_EQUIVALENCE"
        status = "REJECT"
    elif search_status == "OVERFLOW" or gamma_count > 4:
        decision = "REJECT_D2_CLOSURE_GT_4"
        status = "REJECT"
    elif negative_status == "REJECT":
        decision = "REJECT_D2_NEGATIVE_CONTROL"
        status = "REJECT"
    elif search_status == "REVISION_EXHAUSTED":
        decision = "REJECT_D2_REVISION_EXHAUSTED"
        status = "REJECT"
    elif "BLOCK" in {phase_status, schedule_status, negative_status, closure_expected}:
        decision = "BLOCK_D2_SOURCE_OR_EXACT_CHECKER_INCOMPLETE"
        status = "BLOCK"
    else:
        decision = D2_PASS_DECISION
        status = "PASS"

    summary = _one_source_row(
        root, "repro/candidate_d_admission/d2_summary.csv", D2_SUMMARY_FIELDS
    )
    expected_summary = {
        "decision": decision,
        "gamma_count": str(gamma_count),
        "phase_status": phase_status,
        "negative_controls_status": negative_status,
        "schedule_status": schedule_status,
        "equation_revisions_used": str(revisions[0]),
    }
    if summary != expected_summary:
        raise AdmissionEvidenceError("D2 summary does not match recomputed evidence")
    return D2Evidence(status, decision, gamma_count, negative_status)


def _d3_expected_decisions(
    binding: str,
    security: str,
    noise: str,
    cost: str,
    resource: str,
) -> set[str]:
    if binding == "REJECT":
        return {"REJECT_D3_ILLEGAL_BINDING_DOMAIN"}
    if security == "REJECT":
        return {"REJECT_D3_NONSTANDARD_SECURITY_OBJECT"}
    if noise == "REJECT":
        return {"REJECT_D3_DECODING_MARGIN"}
    if "BLOCK" in (binding, security, noise):
        return D3_BLOCK_DECISIONS
    if cost == "REJECT":
        return {"REJECT_D3_COMPLETE_PROJECTION_LT_1_10"}
    if resource == "REJECT":
        return {"REJECT_D3_RESOURCE_OVERHEAD"}
    if "BLOCK" in (cost, resource):
        return {"BLOCK_D3_COST_INPUT_INCOMPLETE"}
    return {D3_PASS_DECISION}


def _recompute_d3(root: Path) -> D3Evidence:
    _require_source_artifacts(root, D3_OUTPUTS)
    binding_rows = _source_csv_rows(
        root, "repro/candidate_d_admission/binding_domain.csv", D3_BINDING_FIELDS
    )
    binding_by_bits: dict[int, dict[str, str]] = {}
    binding_statuses = []
    for row in binding_rows:
        bits = _parse_int(row["plaintext_bits"], "D3 plaintext_bits")
        if bits in binding_by_bits:
            raise AdmissionEvidenceError("D3 binding evidence contains duplicates")
        binding_by_bits[bits] = row
        valid = (
            _parse_int(row["delta_integer"], "D3 delta_integer") == 2 ** (64 - bits)
            and row["delta_torus"] == f"2^-{bits}"
            and _parse_int(row["coefficient_min"], "D3 coefficient_min") == -(2 ** (bits - 1))
            and _parse_int(row["coefficient_max"], "D3 coefficient_max") == 2 ** (bits - 1) - 1
            and row["checker_min"] == "-128"
            and row["checker_max"] == "128"
            and row["binder_operation"] == D3_BINDER
        )
        expected = "PASS" if valid else "REJECT"
        if row["status"] != expected:
            raise AdmissionEvidenceError("D3 binding status is not source-derived")
        binding_statuses.append(expected)
    if set(binding_by_bits) != {2, 3, 5, 8}:
        raise AdmissionEvidenceError("D3 binding evidence has the wrong domain set")
    binding = "REJECT" if "REJECT" in binding_statuses else "PASS"

    security_rows = _source_csv_rows(
        root, "repro/candidate_d_admission/security_object_map.csv", D3_SECURITY_FIELDS
    )
    security_by_object = {row["object"]: row for row in security_rows}
    if len(security_by_object) != len(security_rows) or set(security_by_object) != set(D3_SECURITY_OBJECTS):
        raise AdmissionEvidenceError("D3 security evidence has the wrong object set")
    security_statuses = []
    for name, (realization, assumption) in D3_SECURITY_OBJECTS.items():
        row = security_by_object[name]
        valid = row["realization"] == realization and row["assumption"] == assumption
        expected = "PASS" if valid else "REJECT"
        if row["status"] != expected:
            raise AdmissionEvidenceError("D3 security status is not source-derived")
        security_statuses.append(expected)
    security = "REJECT" if "REJECT" in security_statuses else "PASS"

    noise_rows = _source_csv_rows(
        root, "repro/candidate_d_admission/noise_bound.csv", D3_NOISE_FIELDS
    )
    noise_by_case = {row["case"]: row for row in noise_rows}
    if len(noise_by_case) != len(noise_rows) or tuple(noise_by_case) != D3_NOISE_CASES:
        raise AdmissionEvidenceError("D3 noise evidence has the wrong case set or order")
    lemma = noise_by_case["external_product_lemma"]
    noise_reason = ""
    if lemma["value"] == "MISSING":
        expected_lemma = "BLOCK"
        noise_reason = "BLOCK_D3_NOISE_LEMMA_INCOMPLETE"
    elif lemma["value"] == "ANCHORED" and lemma["limit"] == "REQUIRED" and lemma["source_anchor"]:
        expected_lemma = "PASS"
    else:
        raise AdmissionEvidenceError("D3 external-product lemma row is malformed")
    if lemma["status"] != expected_lemma:
        raise AdmissionEvidenceError("D3 external-product lemma status is inconsistent")
    numeric_noise: dict[str, Decimal] = {}
    for case in D3_NOISE_CASES[1:]:
        row = noise_by_case[case]
        if not row["source_anchor"]:
            raise AdmissionEvidenceError("D3 noise row lacks a source anchor")
        if not row["value"] or not row["limit"]:
            if row["status"] != "BLOCK":
                raise AdmissionEvidenceError("D3 missing noise input is not blocked")
            if case == "target_failure_bound":
                noise_reason = "BLOCK_D3_NOISE_TARGET_UNANCHORED"
            elif not noise_reason:
                noise_reason = "BLOCK_D3_NOISE_LEMMA_INCOMPLETE"
            continue
        value = _parse_decimal(row["value"], f"D3 noise {case}", nonnegative=True)
        limit = _parse_decimal(row["limit"], f"D3 noise limit {case}", nonnegative=True)
        numeric_noise[case] = value
        valid = value >= limit if case == "decode_margin" else value <= limit
        expected = "PASS" if valid else "REJECT"
        if row["status"] != expected:
            raise AdmissionEvidenceError("D3 noise status is not source-derived")
    if noise_reason:
        noise = "BLOCK"
    elif any(row["status"] == "REJECT" for row in noise_rows):
        noise = "REJECT"
    else:
        required_bounds = (
            "union_failure_bound",
            "scalar_failure_bound",
            "b1_failure_bound",
            "target_failure_bound",
        )
        if any(case not in numeric_noise for case in required_bounds):
            raise AdmissionEvidenceError("D3 noise comparison inputs are incomplete")
        union = numeric_noise["union_failure_bound"]
        if any(union > numeric_noise[case] for case in required_bounds[1:]):
            raise AdmissionEvidenceError("D3 union failure bound exceeds a reference bound")
        noise = "PASS"

    structural_rows = _source_csv_rows(
        root, "repro/candidate_d_admission/structural_cost.csv", D3_STRUCTURAL_FIELDS
    )
    structural_by_key = {(row["variant"], row["r"]): row for row in structural_rows}
    expected_keys = {
        (variant, str(r))
        for variant in ("B1_exact_dense", "D_operator_generic", "D_operator_coeff_one_fast")
        for r in (1, 2, 4, 8)
    }
    if len(structural_by_key) != len(structural_rows) or set(structural_by_key) != expected_keys:
        raise AdmissionEvidenceError("D3 structural cost has the wrong row set")
    h = 573440
    generic_h = h + 79872
    d_gamma: int | None = None
    for (variant, r_text), row in structural_by_key.items():
        r = int(r_text)
        if variant == "B1_exact_dense":
            expected = (h, (1 + r) ** 2, h * (1 + r) ** 2, 1 + r, 0)
            if row["g"]:
                raise AdmissionEvidenceError("D3 B1 structural row has a gamma value")
        else:
            g = _parse_int(row["g"], "D3 structural gamma", minimum=1, maximum=4)
            if d_gamma is None:
                d_gamma = g
            elif d_gamma != g:
                raise AdmissionEvidenceError("D3 structural rows disagree on gamma")
            events = generic_h if variant == "D_operator_generic" else h
            expected = (events, 4 * g, events * 4 * g, 2 * g, 2 * g * r)
        actual = tuple(
            _parse_int(row[field], f"D3 structural {field}", minimum=0)
            for field in (
                "selector_events",
                "products_per_event",
                "selector_ring_products",
                "materialized_components",
                "late_binding_products",
            )
        )
        if (
            actual != expected
            or row["ncmux_events"] != "5080"
            or row["sub_a_calls"] != "39"
            or row["status"] != "PASS"
        ):
            raise AdmissionEvidenceError("D3 structural cost arithmetic is inconsistent")
    if d_gamma is None:
        raise AdmissionEvidenceError("D3 structural cost lacks Candidate D rows")

    projection_rows = _source_csv_rows(
        root, "repro/candidate_d_admission/amdahl_projection.csv", D3_AMDAHL_FIELDS
    )
    projection_by_scenario = {row["scenario"]: row for row in projection_rows}
    if len(projection_by_scenario) != len(projection_rows) or tuple(projection_by_scenario) != ("central", "pessimistic"):
        raise AdmissionEvidenceError("D3 projection has the wrong scenario set or order")
    central_ep = Decimal(4 * d_gamma) / Decimal(25)
    central_materialization = Decimal(2 * d_gamma) / Decimal(5)
    cost = "PASS"
    projection = ""
    for scenario in ("central", "pessimistic"):
        row = projection_by_scenario[scenario]
        if row["status"] == "BLOCK":
            if any(row[field] for field in D3_AMDAHL_FIELDS[1:-1]):
                raise AdmissionEvidenceError("D3 blocked projection contains numeric claims")
            cost = "BLOCK"
            continue
        ratio = _parse_decimal(row["complete_ratio_vs_b1"], f"D3 {scenario} complete ratio", positive=True)
        speedup = _parse_decimal(row["speedup_vs_b1"], f"D3 {scenario} speedup", positive=True)
        ep_ratio = _parse_decimal(row["ep_ratio"], f"D3 {scenario} EP ratio", positive=True)
        materialization = _parse_decimal(row["materialization_ratio"], f"D3 {scenario} materialization ratio", positive=True)
        automorphism = _parse_decimal(row["automorphism_ratio"], f"D3 {scenario} automorphism ratio", positive=True)
        _parse_decimal(row["late_binding_us"], f"D3 {scenario} late binding", positive=True)
        if abs(ratio * speedup - Decimal(1)) > Decimal("0.000001"):
            raise AdmissionEvidenceError("D3 projection ratio and speedup disagree")
        if scenario == "central":
            if ep_ratio != central_ep or materialization != central_materialization:
                raise AdmissionEvidenceError("D3 central structural ratios disagree")
            expected_status = "PASS"
        else:
            if ep_ratio < central_ep or materialization < central_materialization or automorphism < 1:
                raise AdmissionEvidenceError("D3 pessimistic ratios are optimistic")
            projection = row["speedup_vs_b1"]
            expected_status = "PASS" if speedup >= Decimal("1.10") else "REJECT"
            cost = expected_status
        if row["status"] != expected_status:
            raise AdmissionEvidenceError("D3 projection status is not source-derived")

    resource_rows = _source_csv_rows(
        root, "repro/candidate_d_admission/resource_projection.csv", D3_RESOURCE_FIELDS
    )
    resource_by_variant = {row["variant"]: row for row in resource_rows}
    if len(resource_by_variant) != len(resource_rows) or tuple(resource_by_variant) != D3_RESOURCE_VARIANTS:
        raise AdmissionEvidenceError("D3 resource projection has the wrong variant set or order")
    resource_values: dict[str, tuple[int, ...]] = {}
    numeric_resource_fields = D3_RESOURCE_FIELDS[1:-1]
    for variant in D3_RESOURCE_VARIANTS:
        row = resource_by_variant[variant]
        if variant in {"B0b", "B2"}:
            if row["status"] != "REQUIRED_NOT_YET_LOCAL" or any(row[field] for field in numeric_resource_fields):
                raise AdmissionEvidenceError("D3 required baseline resource row is malformed")
            continue
        if any(not row[field] for field in numeric_resource_fields):
            if variant != "D" or row["status"] != "BLOCK":
                raise AdmissionEvidenceError("D3 resource row has missing numeric inputs")
            continue
        values = tuple(
            _parse_int(row[field], f"D3 resource {field}", minimum=0)
            for field in numeric_resource_fields
        )
        resource_values[variant] = values
        if variant in {"B0a", "B1"} and row["status"] != "REFERENCE":
            raise AdmissionEvidenceError("D3 resource baseline status is malformed")
    if "D" not in resource_values:
        resource = "BLOCK"
    else:
        if "B1" not in resource_values:
            raise AdmissionEvidenceError("D3 resource projection lacks B1 values")
        d_values = resource_values["D"]
        b1_values = resource_values["B1"]
        d_key = d_values[0] + d_values[1]
        b1_key = b1_values[0] + b1_values[1]
        d_memory = sum(d_values[2:6])
        b1_memory = sum(b1_values[2:6])
        resource = (
            "PASS"
            if d_key <= 2 * max(1, b1_key) and d_memory <= 2 * max(1, b1_memory)
            else "REJECT"
        )
        if resource_by_variant["D"]["status"] != resource:
            raise AdmissionEvidenceError("D3 resource status is not source-derived")

    if binding == "REJECT":
        decision = "REJECT_D3_ILLEGAL_BINDING_DOMAIN"
    elif security == "REJECT":
        decision = "REJECT_D3_NONSTANDARD_SECURITY_OBJECT"
    elif noise == "REJECT":
        decision = "REJECT_D3_DECODING_MARGIN"
    elif noise == "BLOCK":
        decision = noise_reason or "BLOCK_D3_NOISE_LEMMA_INCOMPLETE"
    elif cost == "REJECT":
        decision = "REJECT_D3_COMPLETE_PROJECTION_LT_1_10"
    elif resource == "REJECT":
        decision = "REJECT_D3_RESOURCE_OVERHEAD"
    elif "BLOCK" in {cost, resource}:
        decision = "BLOCK_D3_COST_INPUT_INCOMPLETE"
    else:
        decision = D3_PASS_DECISION

    summary = _one_source_row(
        root, "repro/candidate_d_admission/d3_summary.csv", D3_SUMMARY_FIELDS
    )
    expected_summary = {
        "decision": decision,
        "binding_status": binding,
        "security_status": security,
        "noise_status": noise,
        "complete_cost_status": cost,
        "resource_status": resource,
        "pessimistic_projection": projection,
    }
    if summary != expected_summary:
        raise AdmissionEvidenceError("D3 summary does not match recomputed evidence")
    return D3Evidence(
        decision,
        binding,
        security,
        noise,
        cost,
        resource,
        projection,
    )


def _require_skipped_outputs_absent(root: Path, paths: tuple[str, ...]) -> None:
    present = []
    for relative in paths:
        path = _safe_path(
            root,
            relative,
            f"skipped artifact {relative}",
            strict=False,
        )
        if path.exists():
            present.append(relative)
    if present:
        raise AdmissionEvidenceError(
            "skipped D2/D3 artifacts must not be fabricated: " + ", ".join(present)
        )


def _effective_pre_application_permission(
    root: Path,
    state: Mapping[str, object],
    expected: AdmissionResult,
) -> bool:
    permission = state.get("production_hot_path_permission")
    if not isinstance(permission, bool):
        raise AdmissionEvidenceError(
            "pre-application production permission must be boolean"
        )
    if not permission:
        return False
    candidates = state.get("candidates")
    applied_admit = (
        state.get("last_decision") == ADMIT
        and state.get("active_candidate") == "D"
        and state.get("goal_status") == "ACTIVE"
        and isinstance(candidates, Mapping)
        and isinstance(candidates.get("D"), Mapping)
        and candidates["D"].get("status") == "D3_ADMISSION_PASS"
    )
    if not applied_admit:
        return True
    evidence_path = _safe_path(
        root,
        OUT / "decision_evidence.json",
        "preserved pre-application permission evidence",
        strict=True,
        require_file=True,
    )
    try:
        payload = json.loads(evidence_path.read_text(encoding="ascii"))
        recovered = validate_decision_evidence(payload)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise AdmissionEvidenceError(
            "applied ADMIT lacks valid pre-application permission evidence"
        ) from error
    if recovered != expected or recovered.pre_application_permission:
        raise AdmissionEvidenceError(
            "applied ADMIT permission evidence differs from source gates"
        )
    return False


def derive_candidate_d_decision(result: AdmissionResult) -> str:
    if result.d0_status != "PASS":
        return BLOCK
    if result.d1_status == "REJECT":
        return REJECT_PRIOR_ART
    if result.d1_status != "PASS":
        return BLOCK
    if result.d2_status in {"PASS", "REJECT"} and not result.d2_replay_authenticated:
        return BLOCK
    if (
        result.d2_status == "REJECT"
        or (result.gamma_count is not None and result.gamma_count > 4)
        or result.negative_controls_status == "REJECT"
    ):
        return REJECT_CLOSURE
    if result.gamma_count is not None and result.gamma_count <= 0:
        return BLOCK
    if (
        result.d2_status != "PASS"
        or result.gamma_count is None
        or result.negative_controls_status != "PASS"
    ):
        return BLOCK
    if not result.d3_replay_authenticated:
        return BLOCK
    binding_gates = (
        result.binding_status,
        result.security_status,
        result.noise_status,
    )
    if "REJECT" in binding_gates:
        return REJECT_BINDING_NOISE_SECURITY
    if any(status != "PASS" for status in binding_gates):
        return BLOCK
    completion_gates = (
        result.complete_cost_status,
        result.resource_status,
    )
    if "REJECT" in completion_gates:
        return REJECT_COMPLETE_COST
    if any(status != "PASS" for status in completion_gates):
        return BLOCK
    try:
        projection = Decimal(result.pessimistic_projection)
    except InvalidOperation:
        return BLOCK
    if not projection.is_finite() or projection <= 0:
        return BLOCK
    if projection < Decimal("1.10"):
        return REJECT_COMPLETE_COST
    if result.pre_application_permission:
        return BLOCK
    return ADMIT


def _validate_run_metadata(run_date: str, execution_platform: str) -> None:
    try:
        parsed = date.fromisoformat(run_date)
    except ValueError as error:
        raise AdmissionEvidenceError("run date must be an ISO-8601 calendar date") from error
    if parsed.isoformat() != run_date:
        raise AdmissionEvidenceError("run date must be canonical ISO-8601")
    if (
        not execution_platform
        or len(execution_platform) > 240
        or any(ord(character) < 32 or ord(character) > 126 for character in execution_platform)
    ):
        raise AdmissionEvidenceError("execution platform must be printable ASCII")


def evaluate_candidate_d_admission(
    root: Path = ROOT,
    *,
    input_commit: str,
    controller_commit: str,
    run_date: str,
    execution_platform: str,
) -> AdmissionResult:
    root = _resolved_root(root)
    _validate_run_metadata(run_date, execution_platform)
    runtime_hashes = _controller_source_hashes(root, controller_commit)
    _validate_module_origins(root)
    d0_decision = _recompute_d0(root)
    if d0_decision != d0_baseline.D0_DECISION:
        raise AdmissionEvidenceError("D0 returned an unknown decision")
    d1_decision, missing = _recompute_d1(root)
    d1_statuses = {
        PASS_D1: "PASS",
        REJECT_D1: "REJECT",
        BLOCK_D1: "BLOCK",
    }
    if d1_decision not in d1_statuses:
        raise AdmissionEvidenceError("D1 returned an unknown decision")

    pinned_paths = PINNED_INPUTS
    resume_condition = "none"
    if d1_decision != PASS_D1:
        _require_skipped_outputs_absent(root, D2_OUTPUTS + D3_OUTPUTS)
        skipped = (
            SKIPPED_D1_BLOCK if d1_decision == BLOCK_D1 else SKIPPED_D1_REJECT
        )
        d2 = D2Evidence(skipped, NONE, None, skipped)
        d3 = D3Evidence(NONE, skipped, skipped, skipped, skipped, skipped, NONE)
        d2_replayed = False
        d3_replayed = False
        if d1_decision == BLOCK_D1:
            resume_condition = resume_condition_for(
                "D1_BLOCK", controller_commit=controller_commit
            )
    else:
        d2, d2_replayed = _replay_d2(
            root,
            input_commit=input_commit,
            controller_commit=controller_commit,
        )
        if d2_replayed:
            pinned_paths = (*pinned_paths, *D2_REPLAY_CONTRACT.pinned_paths)
        if d2.status == "PASS":
            d3, d3_replayed = _replay_d3(
                root,
                input_commit=input_commit,
                controller_commit=controller_commit,
            )
            if d3_replayed:
                pinned_paths = (*pinned_paths, *D3_REPLAY_CONTRACT.pinned_paths)
        else:
            d3_replayed = False
            _require_skipped_outputs_absent(root, D3_OUTPUTS)
            skipped = (
                SKIPPED_D2_REJECT
                if d2.status == "REJECT"
                else SKIPPED_D2_BLOCK
            )
            d3 = D3Evidence(
                NONE, skipped, skipped, skipped, skipped, skipped, NONE
            )
            if d2.status == "BLOCK":
                resume_condition = resume_condition_for(
                    "D2_BLOCK", controller_commit=controller_commit
                )
        if d2.status == "PASS" and (
            "BLOCK"
            in {
                d3.binding_status,
                d3.security_status,
                d3.noise_status,
                d3.complete_cost_status,
                d3.resource_status,
            }
        ):
            resume_condition = resume_condition_for(
                "D3_BLOCK", controller_commit=controller_commit
            )

    pinned_paths = tuple(dict.fromkeys(pinned_paths))
    source_hashes = _pinned_source_hashes(root, input_commit, pinned_paths)
    if input_commit != CURRENT_INPUT_COMMIT:
        source_hashes = (
            *source_hashes,
            *_commit_only_hashes(root, input_commit, RESUME_PINNED_INPUTS),
        )
    state = load_state(root / "research_state.yaml")
    provisional = AdmissionResult(
        d0_status="PASS",
        d0_decision=d0_decision,
        d1_status=d1_statuses[d1_decision],
        d1_decision=d1_decision,
        d1_missing_evidence=missing,
        d2_status=d2.status,
        d2_decision=d2.decision,
        d2_replay_authenticated=d2_replayed,
        d3_replay_authenticated=d3_replayed,
        gamma_count=d2.gamma_count,
        negative_controls_status=d2.negative_controls_status,
        binding_status=d3.binding_status,
        security_status=d3.security_status,
        noise_status=d3.noise_status,
        complete_cost_status=d3.complete_cost_status,
        resource_status=d3.resource_status,
        pessimistic_projection=d3.pessimistic_projection,
        pre_application_permission=False,
        decision=BLOCK,
        resume_condition=resume_condition,
        input_commit=input_commit,
        controller_commit=controller_commit,
        run_date=run_date,
        execution_platform=execution_platform,
        source_hashes=source_hashes,
        runtime_source_hashes=runtime_hashes,
    )
    provisional = replace(
        provisional, decision=derive_candidate_d_decision(provisional)
    )
    permission = _effective_pre_application_permission(root, state, provisional)
    result = replace(provisional, pre_application_permission=permission)
    result = replace(result, decision=derive_candidate_d_decision(result))
    if result.decision == BLOCK and result.resume_condition == "none":
        result = replace(
            result,
            resume_condition=(
                "Restore production_hot_path_permission=false in the reviewed "
                "pre-application Candidate D state, then rerun Task 9 with the "
                "explicit input commit."
            ),
        )
    return result


def _gate_payload(result: AdmissionResult) -> dict[str, object]:
    return {
        "d0_status": result.d0_status,
        "d0_decision": result.d0_decision,
        "d1_status": result.d1_status,
        "d1_decision": result.d1_decision,
        "d1_missing_evidence": list(result.d1_missing_evidence),
        "d2_status": result.d2_status,
        "d2_decision": result.d2_decision,
        "d2_replay_authenticated": result.d2_replay_authenticated,
        "d3_replay_authenticated": result.d3_replay_authenticated,
        "gamma_count": result.gamma_count,
        "negative_controls_status": result.negative_controls_status,
        "binding_status": result.binding_status,
        "security_status": result.security_status,
        "noise_status": result.noise_status,
        "complete_cost_status": result.complete_cost_status,
        "resource_status": result.resource_status,
        "pessimistic_projection": result.pessimistic_projection,
        "pre_application_permission": result.pre_application_permission,
    }


def _pinned_inputs_for_result(result: AdmissionResult) -> tuple[str, ...]:
    paths = PINNED_INPUTS
    if result.d2_replay_authenticated:
        paths = (*paths, *D2_REPLAY_CONTRACT.pinned_paths)
    if result.d3_replay_authenticated:
        paths = (*paths, *D3_REPLAY_CONTRACT.pinned_paths)
    return tuple(dict.fromkeys(paths))


def _predecessor_evidence_record() -> dict[str, str]:
    return {
        "evidence_commit": ERRATUM_PREDECESSOR_EVIDENCE_COMMIT,
        "controller_commit": ERRATUM_PREDECESSOR_CONTROLLER_COMMIT,
        "decision_evidence_path": ERRATUM_PREDECESSOR_EVIDENCE_PATH,
        "decision_evidence_sha256": ERRATUM_PREDECESSOR_EVIDENCE_SHA256,
    }


def _decision_evidence_payload(result: AdmissionResult) -> dict[str, object]:
    payload = {
        "schema": "candidate-d-task9-decision-evidence-v4",
        "input_commit": result.input_commit,
        "controller_commit": result.controller_commit,
        "historical_block_commit": HISTORICAL_BLOCK_COMMIT,
        "predecessor_evidence": _predecessor_evidence_record(),
        "run_date": result.run_date,
        "execution_platform": result.execution_platform,
        "claimed_decision": result.decision,
        "gate_evidence": _gate_payload(result),
        "source_hashes": [
            {"path": path, "sha256": digest}
            for path, digest in result.source_hashes
        ],
        "runtime_source_hashes": [
            {"path": path, "sha256": digest}
            for path, digest in result.runtime_source_hashes
        ],
        "resume_condition": result.resume_condition,
    }
    payload["binding_sha256"] = _sha256_bytes(_canonical_json(payload))
    return payload


def _decision_binding(result: AdmissionResult) -> str:
    return str(_decision_evidence_payload(result)["binding_sha256"])


def canonical_summary_record(result: AdmissionResult) -> dict[str, str]:
    if result.decision != derive_candidate_d_decision(result):
        raise ValueError("result decision does not match gate evidence")
    return {
        "decision": result.decision,
        "d0_status": result.d0_status,
        "d0_decision": result.d0_decision,
        "d1_status": result.d1_status,
        "d1_decision": result.d1_decision,
        "d1_missing_evidence": "|".join(result.d1_missing_evidence),
        "d2_status": result.d2_status,
        "d2_decision": result.d2_decision,
        "d2_replay_authenticated": (
            "yes" if result.d2_replay_authenticated else "no"
        ),
        "d3_replay_authenticated": (
            "yes" if result.d3_replay_authenticated else "no"
        ),
        "gamma_count": "" if result.gamma_count is None else str(result.gamma_count),
        "negative_controls_status": result.negative_controls_status,
        "binding_status": result.binding_status,
        "security_status": result.security_status,
        "noise_status": result.noise_status,
        "complete_cost_status": result.complete_cost_status,
        "resource_status": result.resource_status,
        "pessimistic_projection": result.pessimistic_projection,
        "pre_application_permission": (
            "yes" if result.pre_application_permission else "no"
        ),
        "production_hot_path_permission": (
            "yes" if result.decision == ADMIT else "no"
        ),
        "input_commit": result.input_commit,
        "controller_commit": result.controller_commit,
        "historical_block_commit": HISTORICAL_BLOCK_COMMIT,
        "predecessor_evidence_commit": ERRATUM_PREDECESSOR_EVIDENCE_COMMIT,
        "predecessor_controller_commit": (
            ERRATUM_PREDECESSOR_CONTROLLER_COMMIT
        ),
        "predecessor_decision_evidence_sha256": (
            ERRATUM_PREDECESSOR_EVIDENCE_SHA256
        ),
        "run_date": result.run_date,
        "execution_platform": result.execution_platform,
        "resume_condition": result.resume_condition,
        "decision_evidence_binding_sha256": _decision_binding(result),
    }


def _result_from_evidence(payload: Mapping[str, object]) -> AdmissionResult:
    gates = payload.get("gate_evidence")
    if not isinstance(gates, Mapping):
        raise ValueError("decision evidence gate_evidence is malformed")
    expected_gate_keys = {
        "d0_status",
        "d0_decision",
        "d1_status",
        "d1_decision",
        "d1_missing_evidence",
        "d2_status",
        "d2_decision",
        "d2_replay_authenticated",
        "d3_replay_authenticated",
        "gamma_count",
        "negative_controls_status",
        "binding_status",
        "security_status",
        "noise_status",
        "complete_cost_status",
        "resource_status",
        "pessimistic_projection",
        "pre_application_permission",
    }
    if set(gates) != expected_gate_keys:
        raise ValueError("decision evidence gate fields are malformed")
    missing = gates["d1_missing_evidence"]
    if not isinstance(missing, list) or not all(
        isinstance(value, str) for value in missing
    ):
        raise ValueError("decision evidence missing-source list is malformed")
    gamma = gates["gamma_count"]
    if gamma is not None and type(gamma) is not int:
        raise ValueError("decision evidence gamma_count is malformed")
    permission = gates["pre_application_permission"]
    if not isinstance(permission, bool):
        raise ValueError("decision evidence permission is malformed")
    replay_flags = (
        gates["d2_replay_authenticated"],
        gates["d3_replay_authenticated"],
    )
    if any(not isinstance(value, bool) for value in replay_flags):
        raise ValueError("decision evidence replay flags are malformed")

    def hashes(key: str, expected: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
        rows = payload.get(key)
        if not isinstance(rows, list) or len(rows) != len(expected):
            raise ValueError(f"decision evidence {key} is malformed")
        parsed = []
        for row, expected_path in zip(rows, expected, strict=True):
            if not isinstance(row, Mapping) or set(row) != {"path", "sha256"}:
                raise ValueError(f"decision evidence {key} is malformed")
            path = row["path"]
            digest = row["sha256"]
            if (
                path != expected_path
                or not isinstance(digest, str)
                or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            ):
                raise ValueError(f"decision evidence {key} is malformed")
            parsed.append((path, digest))
        return tuple(parsed)

    expected_source_paths = PINNED_INPUTS
    if gates["d2_replay_authenticated"]:
        expected_source_paths = (
            *expected_source_paths,
            *D2_REPLAY_CONTRACT.pinned_paths,
        )
    if gates["d3_replay_authenticated"]:
        expected_source_paths = (
            *expected_source_paths,
            *D3_REPLAY_CONTRACT.pinned_paths,
        )
    expected_source_paths = tuple(dict.fromkeys(expected_source_paths))
    if payload.get("input_commit") != CURRENT_INPUT_COMMIT:
        expected_source_paths = (*expected_source_paths, *RESUME_PINNED_INPUTS)
    source_hashes = hashes("source_hashes", expected_source_paths)
    runtime_paths = (
        DECISION_EVIDENCE_V3_RUNTIME_SOURCES
        if payload.get("schema") == "candidate-d-task9-decision-evidence-v3"
        else RUNTIME_SOURCES
    )
    runtime_hashes = hashes("runtime_source_hashes", runtime_paths)
    string_fields = expected_gate_keys - {
        "d1_missing_evidence",
        "gamma_count",
        "pre_application_permission",
        "d2_replay_authenticated",
        "d3_replay_authenticated",
    }
    if any(not isinstance(gates[field], str) for field in string_fields):
        raise ValueError("decision evidence gate values are malformed")
    decision = payload.get("claimed_decision")
    resume = payload.get("resume_condition")
    input_commit = payload.get("input_commit")
    controller_commit = payload.get("controller_commit")
    historical_commit = payload.get("historical_block_commit")
    run_date = payload.get("run_date")
    execution_platform = payload.get("execution_platform")
    if (
        not isinstance(decision, str)
        or decision not in DECISIONS
        or not isinstance(resume, str)
        or not isinstance(input_commit, str)
        or re.fullmatch(r"[0-9a-f]{40}", input_commit) is None
        or not isinstance(controller_commit, str)
        or re.fullmatch(r"[0-9a-f]{40}", controller_commit) is None
        or historical_commit != HISTORICAL_BLOCK_COMMIT
        or not isinstance(run_date, str)
        or not isinstance(execution_platform, str)
    ):
        raise ValueError("decision evidence terminal fields are malformed")
    try:
        _validate_run_metadata(run_date, execution_platform)
    except AdmissionEvidenceError as error:
        raise ValueError(str(error)) from error
    return AdmissionResult(
        d0_status=gates["d0_status"],
        d0_decision=gates["d0_decision"],
        d1_status=gates["d1_status"],
        d1_decision=gates["d1_decision"],
        d1_missing_evidence=tuple(missing),
        d2_status=gates["d2_status"],
        d2_decision=gates["d2_decision"],
        d2_replay_authenticated=gates["d2_replay_authenticated"],
        d3_replay_authenticated=gates["d3_replay_authenticated"],
        gamma_count=gamma,
        negative_controls_status=gates["negative_controls_status"],
        binding_status=gates["binding_status"],
        security_status=gates["security_status"],
        noise_status=gates["noise_status"],
        complete_cost_status=gates["complete_cost_status"],
        resource_status=gates["resource_status"],
        pessimistic_projection=gates["pessimistic_projection"],
        pre_application_permission=permission,
        decision=decision,
        resume_condition=resume,
        input_commit=input_commit,
        controller_commit=controller_commit,
        run_date=run_date,
        execution_platform=execution_platform,
        source_hashes=source_hashes,
        runtime_source_hashes=runtime_hashes,
    )


def validate_decision_evidence(payload: object) -> AdmissionResult:
    if not isinstance(payload, Mapping):
        raise ValueError("decision evidence must be an object")
    base_keys = {
        "schema",
        "input_commit",
        "controller_commit",
        "historical_block_commit",
        "run_date",
        "execution_platform",
        "claimed_decision",
        "gate_evidence",
        "source_hashes",
        "runtime_source_hashes",
        "resume_condition",
        "binding_sha256",
    }
    schema = payload.get("schema")
    if schema == "candidate-d-task9-decision-evidence-v3":
        expected_keys = base_keys
    elif schema == "candidate-d-task9-decision-evidence-v4":
        expected_keys = {*base_keys, "predecessor_evidence"}
        if payload.get("predecessor_evidence") != _predecessor_evidence_record():
            raise ValueError("decision evidence predecessor binding is malformed")
    else:
        raise ValueError("decision evidence schema is malformed")
    if set(payload) != expected_keys:
        raise ValueError("decision evidence schema is malformed")
    binding = payload.get("binding_sha256")
    if not isinstance(binding, str) or re.fullmatch(r"[0-9a-f]{64}", binding) is None:
        raise ValueError("decision evidence binding is malformed")
    unbound = dict(payload)
    del unbound["binding_sha256"]
    if _sha256_bytes(_canonical_json(unbound)) != binding:
        raise ValueError("decision evidence binding is stale")
    result = _result_from_evidence(payload)
    if result.decision != derive_candidate_d_decision(result):
        raise ValueError("decision evidence decision does not match gates")
    return result


def _proof_rows(result: AdmissionResult) -> tuple[dict[str, str], ...]:
    def source_classification(status: str, canonical: str) -> str:
        return (
            "PREDECESSOR_DID_NOT_PASS"
            if status.startswith("SKIPPED_")
            else canonical
        )

    return (
        {
            "gate": "D0_baseline",
            "status": result.d0_status,
            "classification": "RECOMPUTED_FROM_PINNED_SOURCE",
            "evidence": result.d0_decision,
        },
        {
            "gate": "D1_novelty",
            "status": result.d1_status,
            "classification": "RECOMPUTED_FROM_HASH_BOUND_FULLTEXT_REGISTRY",
            "evidence": result.d1_decision + "; missing=" + (
                "|".join(result.d1_missing_evidence) or "none"
            ),
        },
        {
            "gate": "D2_closure",
            "status": result.d2_status,
            "classification": source_classification(
                result.d2_status, "CANONICAL_D2_SOURCE_ARTIFACT"
            ),
            "evidence": result.d2_decision or result.d2_status,
        },
        {
            "gate": "D2_replay_authentication",
            "status": "PASS" if result.d2_replay_authenticated else "NOT_REACHED",
            "classification": "PINNED_CANONICAL_REPLAY_REQUIRED",
            "evidence": D2_REPLAY_CONTRACT.runner,
        },
        {
            "gate": "D2_gamma_count",
            "status": (
                "MISSING" if result.gamma_count is None else str(result.gamma_count)
            ),
            "classification": source_classification(
                result.d2_status, "CLOSURE_BASIS_CARDINALITY"
            ),
            "evidence": "required range is 1..4",
        },
        {
            "gate": "D2_negative_controls",
            "status": result.negative_controls_status,
            "classification": source_classification(
                result.negative_controls_status,
                "CANONICAL_NEGATIVE_CONTROL_ROWS",
            ),
            "evidence": "every control must be detected",
        },
        {
            "gate": "D3_integer_binding",
            "status": result.binding_status,
            "classification": source_classification(
                result.binding_status, "CANONICAL_BINDING_DOMAIN_ROWS"
            ),
            "evidence": result.binding_status,
        },
        {
            "gate": "D3_replay_authentication",
            "status": "PASS" if result.d3_replay_authenticated else "NOT_REACHED",
            "classification": "PINNED_CANONICAL_REPLAY_REQUIRED",
            "evidence": D3_REPLAY_CONTRACT.runner,
        },
        {
            "gate": "D3_standard_object_security",
            "status": result.security_status,
            "classification": source_classification(
                result.security_status,
                "CANONICAL_SECURITY_OBJECT_MAP_ROWS",
            ),
            "evidence": result.security_status,
        },
        {
            "gate": "D3_noise_decode",
            "status": result.noise_status,
            "classification": source_classification(
                result.noise_status, "CANONICAL_NOISE_BOUND_ROWS"
            ),
            "evidence": result.noise_status,
        },
        {
            "gate": "D3_complete_cost",
            "status": result.complete_cost_status,
            "classification": source_classification(
                result.complete_cost_status,
                "CANONICAL_AMDAHL_PROJECTION_ROW",
            ),
            "evidence": result.complete_cost_status,
        },
        {
            "gate": "D3_resource",
            "status": result.resource_status,
            "classification": source_classification(
                result.resource_status,
                "CANONICAL_RESOURCE_PROJECTION_ROWS",
            ),
            "evidence": result.resource_status,
        },
        {
            "gate": "D3_pessimistic_projection",
            "status": result.pessimistic_projection or "MISSING",
            "classification": source_classification(
                result.complete_cost_status, "B1_SPEEDUP_RATIO"
            ),
            "evidence": "admission threshold is >=1.10",
        },
        {
            "gate": "pre_application_permission",
            "status": "YES" if result.pre_application_permission else "NO",
            "classification": "PRESERVED_PRE_APPLICATION_STATE",
            "evidence": "admission requires NO",
        },
        {
            "gate": "production_hot_path_permission",
            "status": "NO" if result.decision != ADMIT else "YES",
            "classification": "COMPLETION_BOUNDARY",
            "evidence": result.decision,
        },
        {
            "gate": "terminal_decision",
            "status": result.decision,
            "classification": "DERIVED_PRIORITY_ORDER",
            "evidence": _decision_binding(result),
        },
        {
            "gate": "finite_resume_condition",
            "status": "REQUIRED" if result.decision == BLOCK else "NONE",
            "classification": "EXACT_EXTERNAL_INPUT",
            "evidence": result.resume_condition,
        },
    )


def _last_reached_status(result: AdmissionResult) -> str:
    if result.d0_status != "PASS":
        return "PLAN_APPROVED"
    if result.d1_status != "PASS":
        return "D0_BASELINE_FROZEN"
    if result.d2_status != "PASS":
        return "D1_NOVELTY_AUDIT_PASS"
    return "D2_OPERATOR_CLOSURE_PASS"


def _decision_effect(result: AdmissionResult) -> str:
    if result.decision == ADMIT:
        return (
            "Candidate D advances to D3_ADMISSION_PASS, remains active, and "
            "receives permission only for a separate opt-in D4 isolated "
            "encrypted-operator experiment. Scalar defaults are unchanged."
        )
    if result.decision == BLOCK:
        return (
            f"Candidate D remains active at {_last_reached_status(result)}; "
            "the research goal is externally blocked, Candidate E remains "
            "reserved, and production hot-path permission is false."
        )
    return (
        f"Candidate D is rejected at {_last_reached_status(result)}; Candidate "
        "E enters SECURITY_NOVELTY_PREFLIGHT and production hot-path "
        "permission remains false."
    )


def _report(result: AdmissionResult) -> bytes:
    missing = "`, `".join(result.d1_missing_evidence) or "none"
    resume = ""
    if result.decision == BLOCK:
        resume = f"""
## Finite Resume Condition

{result.resume_condition}
"""
    d3_evidence = (
        "predecessor did not pass"
        if result.binding_status.startswith("SKIPPED_")
        else "canonical D3 source evidence"
    )
    terminal_boundary = ""
    if result.d1_status == "BLOCK":
        terminal_boundary = (
            "\nThis D1 BLOCK is independent of D2/D3 runtime replay; D2 and "
            "D3 are SKIPPED / NOT_REACHED.\n"
        )
    text = f"""# Candidate D Admission Report

## Decision

`{result.decision}`

{_decision_effect(result)}

## Recomputed Gate Chain

| gate | status | decision/evidence |
| --- | --- | --- |
| D0 baseline freeze | {result.d0_status} | `{result.d0_decision}` |
| D1 novelty/full-text audit | {result.d1_status} | `{result.d1_decision}` |
| D2 exact operator closure | {result.d2_status} | `{result.d2_decision or result.d2_status}` |
| D2 deterministic replay | {'PASS' if result.d2_replay_authenticated else 'NOT_REACHED'} | canonical scientific runner required |
| D2 gamma / negative controls | {result.gamma_count if result.gamma_count is not None else 'missing'} | `{result.negative_controls_status}` |
| D3 deterministic replay | {'PASS' if result.d3_replay_authenticated else 'NOT_REACHED'} | canonical scientific runner required |
| D3 integer binding | {result.binding_status} | {d3_evidence} |
| D3 standard security objects | {result.security_status} | {d3_evidence} |
| D3 absolute noise/decode | {result.noise_status} | {d3_evidence} |
| D3 complete cost / resource | {result.complete_cost_status} / {result.resource_status} | {d3_evidence}; pessimistic speedup `{result.pessimistic_projection or 'missing'}` |

D0 was regenerated from the pinned baseline anchors and compared byte for
byte with the tracked D0 artifacts. D1 was regenerated from the source
registry and locally hash-bound full texts and compared byte for byte with the
tracked D1 artifacts. Missing D1 reviews: `{missing}`. D2 and D3 PASS/REJECT
values have authority only after their reviewed, commit-pinned canonical
runner executes under the finite threat model in a temporary output root and
every artifact compares byte for byte. Static CSV parsing is secondary;
skipped or hand-written values are never promoted.

## Replay Claim Boundary

This controller authenticates reviewed deterministic execution, not arbitrary
untrusted code. Mandatory source review of the canonical runner and its exact
recursive local closure is a prerequisite for scientific authority. The
import guard, execution audit, checkout snapshot, output-tree validation, and
completion attestation are defense in depth, not a hostile-code sandbox. A
malicious commit-pinned runner and arbitrary native code are out of scope; see
`docs/candidate_d_task9_threat_model.md`.{terminal_boundary}

## Scope

No D0-D3 terminal route is itself a complete SAB speedup or paper claim. The
decision is bound to input commit `{result.input_commit}`, controller commit
`{result.controller_commit}`, immutable historical BLOCK commit
`{HISTORICAL_BLOCK_COMMIT}`, predecessor evidence commit
`{ERRATUM_PREDECESSOR_EVIDENCE_COMMIT}` with controller
`{ERRATUM_PREDECESSOR_CONTROLLER_COMMIT}` and decision-evidence SHA-256
`{ERRATUM_PREDECESSOR_EVIDENCE_SHA256}`, run date `{result.run_date}`,
execution platform `{result.execution_platform}`, and decision-evidence hash
`{_decision_binding(result)}`.
{resume}
"""
    return (text.rstrip() + "\n").encode("ascii")


def _render_artifacts(root: Path, result: AdmissionResult) -> dict[str, bytes]:
    summary = _csv_bytes(SUMMARY_FIELDS, (canonical_summary_record(result),))
    proof = _csv_bytes(PROOF_FIELDS, _proof_rows(result))
    evidence = (
        json.dumps(
            _decision_evidence_payload(result),
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
        )
        + "\n"
    ).encode("ascii")
    generated = {
        REPORT.as_posix(): _report(result),
        (OUT / "summary.csv").as_posix(): summary,
        (OUT / "proof_gate.csv").as_posix(): proof,
        (OUT / "decision_evidence.json").as_posix(): evidence,
    }
    index_rows = []
    for relative in _indexed_artifacts(result):
        if relative in generated:
            content = generated[relative]
        else:
            path = _safe_path(
                root,
                relative,
                f"indexed artifact {relative}",
                strict=True,
                require_file=True,
            )
            content = path.read_bytes()
        index_rows.append({"path": relative, "sha256": _sha256_bytes(content)})
    generated[(OUT / "artifact_index.csv").as_posix()] = _csv_bytes(
        ("path", "sha256"), index_rows
    )
    return generated


def _indexed_artifacts(result: AdmissionResult) -> tuple[str, ...]:
    paths = set(INDEXED_ARTIFACTS)
    if result.d2_replay_authenticated:
        paths.update(D2_OUTPUTS)
    if result.d3_replay_authenticated:
        paths.update(D3_OUTPUTS)
    return tuple(sorted(paths))


def read_canonical_summary(path: Path) -> dict[str, str]:
    try:
        content = Path(path).read_bytes()
    except OSError as error:
        raise ValueError("summary cannot be read") from error
    try:
        rows = _strict_csv_bytes(
            content, SUMMARY_FIELDS, "Candidate D summary"
        )
    except AdmissionEvidenceError as error:
        raise ValueError(str(error)) from error
    if len(rows) != 1:
        raise ValueError("summary must contain one canonical decision")
    row = rows[0]
    if row["decision"] not in DECISIONS:
        raise ValueError("summary contains an unknown decision")
    return row


def validate_artifact_index(
    root: Path,
    index_path: Path,
    result: AdmissionResult | None = None,
) -> None:
    root = _resolved_root(root)
    try:
        content = Path(index_path).read_bytes()
    except OSError as error:
        raise ValueError("artifact index cannot be read") from error
    rows = _strict_csv_bytes(
        content, ("path", "sha256"), "Candidate D artifact index"
    )
    if result is None:
        evidence_path = root / OUT / "decision_evidence.json"
        try:
            payload = json.loads(evidence_path.read_text(encoding="ascii"))
            result = validate_decision_evidence(payload)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            raise ValueError("decision evidence is unavailable for artifact index") from error
    if tuple(row["path"] for row in rows) != _indexed_artifacts(result):
        raise ValueError("artifact index path set or order changed")
    for row in rows:
        digest = row["sha256"]
        if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ValueError("artifact index digest is malformed")
        try:
            path = _safe_path(
                root,
                row["path"],
                f"indexed artifact {row['path']}",
                strict=True,
                require_file=True,
            )
        except AdmissionEvidenceError as error:
            raise ValueError(str(error)) from error
        if _sha256_bytes(path.read_bytes()) != digest:
            raise ValueError(f"artifact index hash is stale: {row['path']}")


def _write_bytes_atomic(path: Path, content: bytes) -> None:
    descriptor, name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists() and not temporary.is_symlink():
            temporary.unlink()


def write_candidate_d_artifacts(
    root: Path,
    result: AdmissionResult,
    *,
    input_commit: str,
    controller_commit: str,
    run_date: str,
    execution_platform: str,
) -> None:
    root = _resolved_root(root)
    fresh = evaluate_candidate_d_admission(
        root,
        input_commit=input_commit,
        controller_commit=controller_commit,
        run_date=run_date,
        execution_platform=execution_platform,
    )
    if result != fresh:
        raise AdmissionEvidenceError(
            "admission result does not match fresh repository evidence"
        )
    artifacts = _render_artifacts(root, result)
    destinations = {}
    for relative in GENERATED_OUTPUTS:
        destination = _safe_path(
            root,
            relative,
            f"generated output {relative}",
            strict=False,
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination = _safe_path(
            root,
            relative,
            f"generated output {relative}",
            strict=False,
        )
        if destination.exists() and not destination.is_file():
            raise AdmissionEvidenceError(
                f"generated output is not a regular file: {relative}"
            )
        destinations[relative] = destination
    snapshot = {
        path: path.read_bytes() if path.exists() else None
        for path in destinations.values()
    }
    try:
        for relative in GENERATED_OUTPUTS:
            _write_bytes_atomic(destinations[relative], artifacts[relative])
    except Exception:
        for path, previous in snapshot.items():
            if previous is None:
                if path.exists() and not path.is_symlink():
                    path.unlink()
            else:
                _write_bytes_atomic(path, previous)
        raise


def verify_candidate_d_artifacts(
    root: Path = ROOT,
    *,
    input_commit: str,
    controller_commit: str,
    run_date: str,
    execution_platform: str,
) -> AdmissionResult:
    root = _resolved_root(root)
    result = evaluate_candidate_d_admission(
        root,
        input_commit=input_commit,
        controller_commit=controller_commit,
        run_date=run_date,
        execution_platform=execution_platform,
    )
    expected = _render_artifacts(root, result)
    for relative in GENERATED_OUTPUTS:
        path = _safe_path(
            root,
            relative,
            f"published output {relative}",
            strict=True,
            require_file=True,
        )
        if path.read_bytes() != expected[relative]:
            raise AdmissionEvidenceError(f"published artifact drift: {relative}")
    evidence_path = root / OUT / "decision_evidence.json"
    try:
        payload = json.loads(evidence_path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AdmissionEvidenceError("decision evidence is malformed") from error
    if validate_decision_evidence(payload) != result:
        raise AdmissionEvidenceError(
            "decision evidence does not match fresh repository evidence"
        )
    if read_canonical_summary(root / OUT / "summary.csv") != (
        canonical_summary_record(result)
    ):
        raise AdmissionEvidenceError(
            "summary does not match fresh repository evidence"
        )
    validate_artifact_index(root, root / OUT / "artifact_index.csv", result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--input-commit", required=True)
    parser.add_argument("--controller-commit", required=True)
    parser.add_argument("--run-date", required=True)
    parser.add_argument("--execution-platform", required=True)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the tracked Task 9 artifacts without changing them",
    )
    args = parser.parse_args(argv)
    if args.check:
        result = verify_candidate_d_artifacts(
            args.root,
            input_commit=args.input_commit,
            controller_commit=args.controller_commit,
            run_date=args.run_date,
            execution_platform=args.execution_platform,
        )
    else:
        result = evaluate_candidate_d_admission(
            args.root,
            input_commit=args.input_commit,
            controller_commit=args.controller_commit,
            run_date=args.run_date,
            execution_platform=args.execution_platform,
        )
        write_candidate_d_artifacts(
            args.root,
            result,
            input_commit=args.input_commit,
            controller_commit=args.controller_commit,
            run_date=args.run_date,
            execution_platform=args.execution_platform,
        )
        result = verify_candidate_d_artifacts(
            args.root,
            input_commit=args.input_commit,
            controller_commit=args.controller_commit,
            run_date=args.run_date,
            execution_platform=args.execution_platform,
        )
    print(result.decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
