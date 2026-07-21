#!/usr/bin/env python3
"""Derive and publish the atomic Candidate D D0-D3 admission decision."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, replace
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
from research.mat_sab.candidate_d_literature import (  # noqa: E402
    BLOCK_D1,
    PASS_D1,
    REJECT_D1,
)
from scripts.mat_sab_research_state import load_state  # noqa: E402
import scripts.run_candidate_d_d1_literature as d1_literature  # noqa: E402


CURRENT_INPUT_COMMIT = "c8221ad0fcd8413753ca4c3072f49460972de454"
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
RESUME_CONDITION = (
    "Obtain the latest second revision of IACR ePrint 2026/068 dated "
    "2026-07-16 (not the archived January first-version PDF); set "
    "NTRU_AMORT_FULLTEXT_PATH=<latest-NTRU_AMORT_2026_068.pdf>; run "
    "NTRU_AMORT_FULLTEXT_PATH=<latest-NTRU_AMORT_2026_068.pdf> bash "
    "scripts/fetch_candidate_d_primary_sources.sh; record the verified PDF "
    "SHA-256, canonical pdftotext SHA-256, page range, and claim anchors for "
    "NTRU_AMORT_2026_068 in literature/candidate_d_source_registry.json; "
    "update its REQUIRED_SOURCE_BINDINGS entry in "
    "research/mat_sab/candidate_d_literature.py; then run python "
    "scripts/run_candidate_d_d1_literature.py; commit the "
    "corrected registry, binding, and regenerated D1 artifacts with git commit; "
    "finally run python scripts/run_candidate_d_admission.py --input-commit "
    "<new-D1-commit> and python scripts/apply_candidate_d_admission.py "
    "--input-commit <new-D1-commit>"
)

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


def _runtime_source_hashes(root: Path) -> tuple[tuple[str, str], ...]:
    rows = []
    for relative in RUNTIME_SOURCES:
        path = _safe_path(
            root,
            relative,
            f"runtime source {relative}",
            strict=True,
            require_file=True,
        )
        rows.append((relative, _sha256_bytes(path.read_bytes())))
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
    required_fields: tuple[str, ...],
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
    fields = tuple(records[0])
    if any(field not in fields for field in required_fields) or any(
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


def _recompute_d2(root: Path) -> D2Evidence:
    _require_source_artifacts(root, D2_OUTPUTS)
    summary = _one_source_row(
        root, "repro/candidate_d_admission/d2_summary.csv", ("decision",)
    )
    decision = summary["decision"]
    if decision == D2_PASS_DECISION:
        status = "PASS"
    elif decision in D2_REJECT_DECISIONS:
        status = "REJECT"
    elif decision in D2_BLOCK_DECISIONS:
        status = "BLOCK"
    else:
        raise AdmissionEvidenceError("D2 summary contains an unknown decision")

    basis_rows = _source_csv_rows(
        root,
        "repro/candidate_d_admission/closure_basis.csv",
        ("basis_index", "status"),
    )
    basis_indices = [row["basis_index"] for row in basis_rows]
    if len(basis_indices) != len(set(basis_indices)) or any(
        row["status"] not in {"PASS", "REJECT", "BLOCK"}
        for row in basis_rows
    ):
        raise AdmissionEvidenceError("D2 closure basis is malformed")
    gamma_count = len(basis_rows) or None

    control_rows = _source_csv_rows(
        root,
        "repro/candidate_d_admission/negative_controls.csv",
        ("control", "status"),
    )
    controls = [row["control"] for row in control_rows]
    control_statuses = [row["status"] for row in control_rows]
    if (
        not controls
        or len(controls) != len(set(controls))
        or any(
            value not in {"DETECTED", "MISSED", "INCOMPLETE"}
            for value in control_statuses
        )
    ):
        raise AdmissionEvidenceError("D2 negative controls are malformed")
    if "MISSED" in control_statuses:
        negative_status = "REJECT"
    elif "INCOMPLETE" in control_statuses:
        negative_status = "BLOCK"
    else:
        negative_status = "PASS"
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
    summary = _one_source_row(
        root, "repro/candidate_d_admission/d3_summary.csv", ("decision",)
    )
    decision = summary["decision"]
    if decision not in {
        D3_PASS_DECISION,
        *D3_REJECT_DECISIONS,
        *D3_BLOCK_DECISIONS,
    }:
        raise AdmissionEvidenceError("D3 summary contains an unknown decision")

    binding = _aggregate_status(
        _source_csv_rows(
            root,
            "repro/candidate_d_admission/binding_domain.csv",
            ("status",),
        ),
        "D3 binding evidence",
    )
    security = _aggregate_status(
        _source_csv_rows(
            root,
            "repro/candidate_d_admission/security_object_map.csv",
            ("status",),
        ),
        "D3 security-object evidence",
    )
    noise = _aggregate_status(
        _source_csv_rows(
            root,
            "repro/candidate_d_admission/noise_bound.csv",
            ("status",),
        ),
        "D3 noise/decode evidence",
    )
    resource = _aggregate_status(
        _source_csv_rows(
            root,
            "repro/candidate_d_admission/resource_projection.csv",
            ("status",),
        ),
        "D3 resource evidence",
    )
    projection_rows = _source_csv_rows(
        root,
        "repro/candidate_d_admission/amdahl_projection.csv",
        ("scenario", "speedup_vs_b1", "status"),
    )
    pessimistic = [
        row for row in projection_rows if row["scenario"] == "pessimistic"
    ]
    if len(pessimistic) != 1:
        raise AdmissionEvidenceError(
            "D3 projection must contain one pessimistic row"
        )
    projection = pessimistic[0]["speedup_vs_b1"]
    cost = _aggregate_status((pessimistic[0],), "D3 complete-cost evidence")
    if projection:
        try:
            numeric_projection = Decimal(projection)
        except InvalidOperation as error:
            raise AdmissionEvidenceError(
                "D3 pessimistic projection is malformed"
            ) from error
        if not numeric_projection.is_finite() or numeric_projection <= 0:
            raise AdmissionEvidenceError(
                "D3 pessimistic projection is malformed"
            )
        if numeric_projection < Decimal("1.10"):
            cost = "REJECT"
    elif cost != "BLOCK":
        raise AdmissionEvidenceError(
            "D3 non-block cost evidence requires a pessimistic projection"
        )

    if decision not in _d3_expected_decisions(
        binding, security, noise, cost, resource
    ):
        raise AdmissionEvidenceError("D3 decision does not match source gates")
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


def evaluate_candidate_d_admission(
    root: Path = ROOT, *, input_commit: str
) -> AdmissionResult:
    root = _resolved_root(root)
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
        if d1_decision == BLOCK_D1:
            resume_condition = RESUME_CONDITION
    else:
        d2 = _recompute_d2(root)
        pinned_paths = (*pinned_paths, *D2_OUTPUTS)
        if d2.status == "PASS":
            d3 = _recompute_d3(root)
            pinned_paths = (*pinned_paths, *D3_OUTPUTS)
        else:
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
                resume_condition = (
                    "Run python scripts/run_candidate_d_d2_closure.py, commit "
                    "the corrected D2 source artifacts, then pass that commit "
                    "explicitly to both Task 9 commands with --input-commit."
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
            resume_condition = (
                "Run python scripts/run_candidate_d_d3_admission.py, commit "
                "the corrected D3 source artifacts, then pass that commit "
                "explicitly to both Task 9 commands with --input-commit."
            )

    source_hashes = _pinned_source_hashes(root, input_commit, pinned_paths)
    runtime_hashes = _runtime_source_hashes(root)
    state = load_state(root / "research_state.yaml")
    provisional = AdmissionResult(
        d0_status="PASS",
        d0_decision=d0_decision,
        d1_status=d1_statuses[d1_decision],
        d1_decision=d1_decision,
        d1_missing_evidence=missing,
        d2_status=d2.status,
        d2_decision=d2.decision,
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
    if result.d1_status == "PASS":
        paths = (*paths, *D2_OUTPUTS)
    if result.d2_status == "PASS":
        paths = (*paths, *D3_OUTPUTS)
    return paths


def _decision_evidence_payload(result: AdmissionResult) -> dict[str, object]:
    payload = {
        "schema": "candidate-d-task9-decision-evidence-v2",
        "input_commit": result.input_commit,
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
    if gates["d1_status"] == "PASS":
        expected_source_paths = (*expected_source_paths, *D2_OUTPUTS)
    if gates["d2_status"] == "PASS":
        expected_source_paths = (*expected_source_paths, *D3_OUTPUTS)
    source_hashes = hashes("source_hashes", expected_source_paths)
    runtime_hashes = hashes("runtime_source_hashes", RUNTIME_SOURCES)
    string_fields = expected_gate_keys - {
        "d1_missing_evidence",
        "gamma_count",
        "pre_application_permission",
    }
    if any(not isinstance(gates[field], str) for field in string_fields):
        raise ValueError("decision evidence gate values are malformed")
    decision = payload.get("claimed_decision")
    resume = payload.get("resume_condition")
    input_commit = payload.get("input_commit")
    if (
        not isinstance(decision, str)
        or decision not in DECISIONS
        or not isinstance(resume, str)
        or not isinstance(input_commit, str)
        or re.fullmatch(r"[0-9a-f]{40}", input_commit) is None
    ):
        raise ValueError("decision evidence terminal fields are malformed")
    return AdmissionResult(
        d0_status=gates["d0_status"],
        d0_decision=gates["d0_decision"],
        d1_status=gates["d1_status"],
        d1_decision=gates["d1_decision"],
        d1_missing_evidence=tuple(missing),
        d2_status=gates["d2_status"],
        d2_decision=gates["d2_decision"],
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
        source_hashes=source_hashes,
        runtime_source_hashes=runtime_hashes,
    )


def validate_decision_evidence(payload: object) -> AdmissionResult:
    if not isinstance(payload, Mapping):
        raise ValueError("decision evidence must be an object")
    expected_keys = {
        "schema",
        "input_commit",
        "claimed_decision",
        "gate_evidence",
        "source_hashes",
        "runtime_source_hashes",
        "resume_condition",
        "binding_sha256",
    }
    if set(payload) != expected_keys or payload.get("schema") != (
        "candidate-d-task9-decision-evidence-v2"
    ):
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
| D2 gamma / negative controls | {result.gamma_count if result.gamma_count is not None else 'missing'} | `{result.negative_controls_status}` |
| D3 integer binding | {result.binding_status} | {d3_evidence} |
| D3 standard security objects | {result.security_status} | {d3_evidence} |
| D3 absolute noise/decode | {result.noise_status} | {d3_evidence} |
| D3 complete cost / resource | {result.complete_cost_status} / {result.resource_status} | {d3_evidence}; pessimistic speedup `{result.pessimistic_projection or 'missing'}` |

D0 was regenerated from the pinned baseline anchors and compared byte for
byte with the tracked D0 artifacts. D1 was regenerated from the source
registry and locally hash-bound full texts and compared byte for byte with the
tracked D1 artifacts. Missing D1 reviews: `{missing}`. D2 and D3 values above
are parsed only when their canonical source artifacts are present after their
predecessor passes; skipped values are never promoted to PASS.

## Scope

No D0-D3 terminal route is itself a complete SAB speedup or paper claim. The
decision is bound to input commit `{result.input_commit}` and decision-evidence
hash `{_decision_binding(result)}`.
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
    if result.d1_status == "PASS":
        paths.update(D2_OUTPUTS)
    if result.d2_status == "PASS":
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
    root: Path, result: AdmissionResult, *, input_commit: str
) -> None:
    root = _resolved_root(root)
    fresh = evaluate_candidate_d_admission(root, input_commit=input_commit)
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
    root: Path = ROOT, *, input_commit: str
) -> AdmissionResult:
    root = _resolved_root(root)
    result = evaluate_candidate_d_admission(root, input_commit=input_commit)
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
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the tracked Task 9 artifacts without changing them",
    )
    args = parser.parse_args(argv)
    if args.check:
        result = verify_candidate_d_artifacts(
            args.root, input_commit=args.input_commit
        )
    else:
        result = evaluate_candidate_d_admission(
            args.root, input_commit=args.input_commit
        )
        write_candidate_d_artifacts(
            args.root, result, input_commit=args.input_commit
        )
        result = verify_candidate_d_artifacts(
            args.root, input_commit=args.input_commit
        )
    print(result.decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
