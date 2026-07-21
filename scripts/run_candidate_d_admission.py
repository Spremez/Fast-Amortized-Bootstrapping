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


INPUT_COMMIT = "7ef0ef5ccd0eb99f484888ba11af27740a13182d"
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
NONE = ""
RESUME_CONDITION = (
    "Set NTRU_AMORT_FULLTEXT_PATH=<local-NTRU_AMORT_2026_068.pdf>; run "
    "NTRU_AMORT_FULLTEXT_PATH=<local-NTRU_AMORT_2026_068.pdf> bash "
    "scripts/fetch_candidate_d_primary_sources.sh; record the verified PDF "
    "SHA-256, canonical pdftotext SHA-256, page range, and claim anchors for "
    "NTRU_AMORT_2026_068 in literature/candidate_d_source_registry.json; "
    "then run python scripts/run_candidate_d_d1_literature.py and rerun the "
    "Candidate D admission generator and closeout"
)

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
    root: Path, input_commit: str
) -> tuple[tuple[str, str], ...]:
    commit = _resolve_input_commit(root, input_commit)
    rows = []
    for relative in PINNED_INPUTS:
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
    root: Path = ROOT, *, input_commit: str = INPUT_COMMIT
) -> AdmissionResult:
    root = _resolved_root(root)
    _validate_module_origins(root)
    source_hashes = _pinned_source_hashes(root, input_commit)
    runtime_hashes = _runtime_source_hashes(root)
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

    if d1_decision != PASS_D1:
        _require_skipped_outputs_absent(root, D2_OUTPUTS + D3_OUTPUTS)
        d2_status = SKIPPED_D1_BLOCK
        downstream = SKIPPED_D1_BLOCK
    else:
        # A PASS route must be supplied by Tasks 6-8. Missing gate records
        # remain incomplete evidence; this closeout never invents them.
        d2_summary = _safe_path(
            root,
            "repro/candidate_d_admission/d2_summary.csv",
            "D2 summary",
            strict=False,
        )
        d2_status = "BLOCK" if not d2_summary.exists() else "PASS"
        downstream = "BLOCK"

    state = load_state(root / "research_state.yaml")
    permission = state.get("production_hot_path_permission")
    if not isinstance(permission, bool):
        raise AdmissionEvidenceError(
            "pre-application production permission must be boolean"
        )
    result = AdmissionResult(
        d0_status="PASS",
        d0_decision=d0_decision,
        d1_status=d1_statuses[d1_decision],
        d1_decision=d1_decision,
        d1_missing_evidence=missing,
        d2_status=d2_status,
        d2_decision=NONE,
        gamma_count=None,
        negative_controls_status=(
            SKIPPED_D1_BLOCK if d1_decision != PASS_D1 else downstream
        ),
        binding_status=downstream,
        security_status=downstream,
        noise_status=downstream,
        complete_cost_status=downstream,
        resource_status=downstream,
        pessimistic_projection=NONE,
        pre_application_permission=permission,
        decision=BLOCK,
        resume_condition=(RESUME_CONDITION if d1_decision == BLOCK_D1 else "none"),
        input_commit=input_commit,
        source_hashes=source_hashes,
        runtime_source_hashes=runtime_hashes,
    )
    return replace(result, decision=derive_candidate_d_decision(result))


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


def _decision_evidence_payload(result: AdmissionResult) -> dict[str, object]:
    payload = {
        "schema": "candidate-d-task9-decision-evidence-v1",
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

    source_hashes = hashes("source_hashes", PINNED_INPUTS)
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
        "candidate-d-task9-decision-evidence-v1"
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
    return (
        {
            "gate": "D0_baseline_source_recomputation",
            "status": result.d0_status,
            "classification": "RECOMPUTED_FROM_PINNED_SOURCE",
            "evidence": result.d0_decision,
        },
        {
            "gate": "D1_fulltext_novelty_audit",
            "status": result.d1_status,
            "classification": "RECOMPUTED_FROM_HASH_BOUND_FULLTEXT_REGISTRY",
            "evidence": result.d1_decision + "; missing=" + (
                "|".join(result.d1_missing_evidence) or "none"
            ),
        },
        {
            "gate": "D2_operator_closure",
            "status": result.d2_status,
            "classification": "NO_POSITIVE_ARTIFACT_FABRICATED",
            "evidence": "D2 skipped because D1 did not pass",
        },
        {
            "gate": "D3_binding_noise_cost_resource",
            "status": result.binding_status,
            "classification": "NO_POSITIVE_ARTIFACT_FABRICATED",
            "evidence": "D3 skipped because D1 did not pass",
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


def _report(result: AdmissionResult) -> bytes:
    missing = "`, `".join(result.d1_missing_evidence) or "none"
    text = f"""# Candidate D Admission Report

## Decision

`{result.decision}`

Candidate D remains the active candidate at its last valid reached gate,
`D0_BASELINE_FROZEN`. The research goal is externally blocked, Candidate E
remains `RESERVED_FALLBACK_NOT_STARTED`, and production hot-path permission is
false.

## Recomputed Gate Chain

| gate | status | decision/evidence |
| --- | --- | --- |
| D0 baseline freeze | {result.d0_status} | `{result.d0_decision}` |
| D1 novelty/full-text audit | {result.d1_status} | `{result.d1_decision}` |
| D2 exact operator closure | {result.d2_status} | skipped; no D2 artifact exists |
| D3 binding/noise/cost/resource | {result.binding_status} | skipped; no D3 artifact exists |

D0 was regenerated from the pinned baseline anchors and compared byte for
byte with the tracked D0 artifacts. D1 was regenerated from the source
registry and locally hash-bound full texts and compared byte for byte with the
tracked D1 artifacts. The only missing review is `{missing}`. Missing evidence
is not a mathematical rejection, and no D2/D3 pass, rejection, parameter,
noise value, or cost value is inferred.

## Scope

This closeout records no Candidate D speedup, correctness theorem, security
reduction, noise margin, resource result, or encrypted implementation
permission. It does not activate Candidate E. The decision is bound to input
commit `{result.input_commit}` and decision-evidence hash
`{_decision_binding(result)}`.

## Finite Resume Condition

{result.resume_condition}.

After that exact source input is locally hash-bound and claim-reviewed, rerun
the D1 generator and this admission controller. Until then, D2 and D3 remain
skipped.
"""
    return text.encode("ascii")


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
    for relative in INDEXED_ARTIFACTS:
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


def validate_artifact_index(root: Path, index_path: Path) -> None:
    root = _resolved_root(root)
    try:
        content = Path(index_path).read_bytes()
    except OSError as error:
        raise ValueError("artifact index cannot be read") from error
    rows = _strict_csv_bytes(
        content, ("path", "sha256"), "Candidate D artifact index"
    )
    if tuple(row["path"] for row in rows) != INDEXED_ARTIFACTS:
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
    root: Path, result: AdmissionResult, *, input_commit: str = INPUT_COMMIT
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
    root: Path = ROOT, *, input_commit: str = INPUT_COMMIT
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
    validate_artifact_index(root, root / OUT / "artifact_index.csv")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--input-commit", default=INPUT_COMMIT)
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
