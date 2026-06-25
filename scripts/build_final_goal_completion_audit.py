#!/usr/bin/env python3
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "repro" / "final_goal_completion_audit.csv"
OUT_MD = ROOT / "docs" / "final_goal_completion_audit.md"

READINESS = ROOT / "repro" / "stage27_completion_readiness_audit.csv"
PERFORMANCE = ROOT / "repro" / "stage27_final_evidence_package" / "performance_scope.csv"
NOISE = ROOT / "repro" / "stage27_final_evidence_package" / "noise_scope.csv"
RESOURCE = ROOT / "repro" / "stage27_final_evidence_package" / "resource_scope.csv"
CLAIMS = ROOT / "repro" / "stage27_final_evidence_package" / "claim_scope.csv"
MANIFEST = ROOT / "repro" / "stage27_final_evidence_package" / "manifest.csv"
STAGE28 = ROOT / "repro" / "stage28_native_perf_counter_gate" / "summary.csv"
EXTERNAL = ROOT / "repro" / "external_evidence_intake" / "summary.csv"
STAGE33 = ROOT / "repro" / "stage33_current_smoke" / "summary.csv"
RUN_LOG = ROOT / "repro" / "run_log.csv"


@dataclass
class AuditRow:
    item_id: str
    category: str
    requirement: str
    status: str
    evidence: str
    scope: str
    remaining_action: str


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_csv_if_exists(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    return read_csv(path)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_csv(path: Path, rows: list[AuditRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "item_id",
                "category",
                "requirement",
                "status",
                "evidence",
                "scope",
                "remaining_action",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def row_by(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str] | None:
    for row in rows:
        if row.get(key) == value:
            return row
    return None


def rows_by(rows: list[dict[str, str]], key: str, value: str) -> list[dict[str, str]]:
    return [row for row in rows if row.get(key) == value]


def as_float(row: dict[str, str], key: str) -> float:
    return float(row.get(key, "nan"))


def as_int(row: dict[str, str], key: str) -> int:
    return int(float(row.get(key, "0")))


def existing_manifest_paths(rows: list[dict[str, str]]) -> tuple[bool, str]:
    missing = []
    for row in rows:
        path = row.get("path", "")
        if path and not (ROOT / path).exists():
            missing.append(path)
    if missing:
        return False, "; ".join(missing)
    return True, "all final package manifest paths exist"


def audit() -> list[AuditRow]:
    readiness = read_csv(READINESS)
    performance = read_csv(PERFORMANCE)
    noise = read_csv(NOISE)
    resource = read_csv(RESOURCE)
    claims = read_csv(CLAIMS)
    manifest = read_csv(MANIFEST)
    stage28 = read_csv(STAGE28)
    external = read_csv_if_exists(EXTERNAL)
    stage33 = read_csv_if_exists(STAGE33)
    run_log = read_csv(RUN_LOG)

    out: list[AuditRow] = []

    final_ready = [
        row
        for row in readiness
        if row.get("category") == "final_standard"
        and row.get("status", "").startswith("SATISFIED")
    ]
    out.append(
        AuditRow(
            "A1",
            "scoped_engineering",
            "Final engineering standards F1-F8 are mapped to evidence",
            "PASS_SCOPED" if len(final_ready) == 8 else "FAIL_INCOMPLETE",
            rel(READINESS),
            f"{len(final_ready)}/8 final standards satisfied or scoped-satisfied",
            "Fill missing final-standard evidence before claiming scoped engineering completion.",
        )
    )

    target_perf = [
        row
        for row in performance
        if row.get("scope") == "target_binary_final_rerun"
        and row.get("param") == "SET_2_3_2048"
        and row.get("r") in {"2", "4"}
        and row.get("status", "").lower() == "pass"
        and as_float(row, "mean_speedup") > 1.0
    ]
    out.append(
        AuditRow(
            "A2",
            "performance",
            "Target complete-SAB r=2/r=4 speedups over repeated scalar are positive under the same backend",
            "PASS_SCOPED" if len(target_perf) == 2 else "FAIL_INCOMPLETE",
            rel(PERFORMANCE),
            "target binary SET_2_3_2048, r=2/r=4, spqlios_avx512 final rerun",
            "Re-run target full-SAB A/B until both r=2 and r=4 pass with positive speedup.",
        )
    )

    target_noise = [
        row
        for row in noise
        if row.get("scope") == "target_binary_50_seed"
        and row.get("param") == "SET_2_3_2048"
        and row.get("r") in {"2", "4"}
        and row.get("status") == "PASS"
        and as_int(row, "seeds") >= 50
        and as_int(row, "pvw_failures") == 0
        and as_int(row, "scalar_failures") == 0
        and as_int(row, "pair_failures") == 0
    ]
    out.append(
        AuditRow(
            "A3",
            "correctness_noise",
            "Target promoted path has 50-seed final-output noise/correctness support",
            "PASS_SCOPED" if len(target_noise) == 2 else "FAIL_INCOMPLETE",
            rel(NOISE),
            "target binary SET_2_3_2048, r=2/r=4",
            "Expand or rerun final-output noise until both target r values pass 50 seeds.",
        )
    )

    resource_modes = {
        (row.get("r"), row.get("mode"))
        for row in resource
        if row.get("scope") == "target_binary_resource_smoke"
    }
    expected_resource = {
        ("1", "pvw"),
        ("1", "scalar"),
        ("2", "pvw"),
        ("2", "scalar"),
        ("4", "pvw"),
        ("4", "scalar"),
    }
    out.append(
        AuditRow(
            "A4",
            "resources",
            "Resource snapshot covers scalar and PVW r=1/2/4 key/time/RSS fields",
            "PASS_SMOKE_RESOURCE"
            if expected_resource.issubset(resource_modes)
            else "FAIL_INCOMPLETE",
            rel(RESOURCE),
            "resource smoke, not statistical resource campaign",
            "Repeat resource matrix if final paper requires statistical resource tables.",
        )
    )

    manifest_ok, manifest_detail = existing_manifest_paths(manifest)
    run_log_has_stage28 = any(
        row.get("run_id") == "stage28-native-perf-counter-gate-001"
        for row in run_log
    )
    out.append(
        AuditRow(
            "A5",
            "reproducibility",
            "Final evidence package manifest paths exist and Stage 28 gate is logged",
            "PASS_SCOPED" if manifest_ok and run_log_has_stage28 else "FAIL_INCOMPLETE",
            f"{rel(MANIFEST)}; {rel(RUN_LOG)}",
            manifest_detail,
            "Fix missing manifest paths or run-log entries before claiming reproducibility.",
        )
    )

    stage33_expected = {
        "scalar_binary_full_run",
        "pvw_target_full_gate",
        "scalar_ternary_build",
    }
    stage33_passed = {
        row.get("step")
        for row in stage33
        if row.get("status") == "PASS"
    }
    out.append(
        AuditRow(
            "A5b",
            "current_smoke",
            "Current commit scalar baseline, PVW target gate, and scalar ternary build smoke pass",
            "PASS_CURRENT_SMOKE"
            if stage33_expected.issubset(stage33_passed)
            else "MISSING_CURRENT_SMOKE",
            rel(STAGE33) if STAGE33.exists() else "",
            "current commit smoke only; not a performance claim",
            "Run bash scripts/run_stage33_current_smoke.sh before relying on current-commit smoke evidence.",
        )
    )

    claim_ids = {row.get("claim_id"): row for row in claims}
    blocked_claims = ["C7", "C8", "C10"]
    blocked_ok = all(
        claim_ids.get(claim_id, {}).get("status_label", "").startswith("BLOCKED")
        for claim_id in blocked_claims
    )
    out.append(
        AuditRow(
            "A6",
            "claim_boundary",
            "Novelty, non-binary support, and theorem-level 2025/686 citation claims remain explicitly blocked",
            "PASS_BLOCKED_BOUNDARY" if blocked_ok else "FAIL_OVERCLAIM_RISK",
            rel(CLAIMS),
            "blocked claims are preserved as part of the evidence chain",
            "Restore blocked labels before drafting stronger manuscript claims.",
        )
    )

    added_perf = [
        row
        for row in performance
        if row.get("scope") == "added_binary_small_sample"
        and row.get("status") == "PASS"
        and as_float(row, "mean_speedup") > 1.0
    ]
    added_noise = [
        row
        for row in noise
        if row.get("scope") == "added_binary_5_seed"
        and row.get("status") == "PASS"
        and as_int(row, "pvw_failures") == 0
        and as_int(row, "scalar_failures") == 0
        and as_int(row, "pair_failures") == 0
    ]
    out.append(
        AuditRow(
            "A7",
            "generalization",
            "Added binary parameters have r=2/r=4 small-sample performance and noise support",
            "PASS_SMALL_SAMPLE" if len(added_perf) == 4 and len(added_noise) == 4 else "FAIL_INCOMPLETE",
            f"{rel(PERFORMANCE)}; {rel(NOISE)}",
            "small-sample only; not broad all-parameter evidence",
            "Increase runs/seeds before broad parameter-generalization claims.",
        )
    )

    gate = row_by(stage28, "probe", "hardware_counter_gate")
    stage28_status = gate.get("status", "") if gate else "MISSING"
    if stage28_status == "PASS":
        stage28_audit_status = "PASS_COUNTER_ATTRIBUTION"
    elif stage28_status == "READY_FOR_BENCH":
        stage28_audit_status = "CONDITIONAL_COUNTER_SMOKE_ONLY"
    elif stage28_status == "BLOCKED":
        stage28_audit_status = "BLOCKED_EXTERNAL"
    else:
        stage28_audit_status = "FAIL_MISSING"
    out.append(
        AuditRow(
            "A8",
            "theory_backend",
            "MAT-AVX512 theoretical load/store optimality has hardware-counter support",
            stage28_audit_status,
            rel(STAGE28),
            gate.get("detail", "missing Stage 28 gate") if gate else "missing Stage 28 gate",
            "Run Stage 28 on native Linux or perf-enabled WSL with STAGE28_RUN_BENCH=1 before claiming theoretical optimality.",
        )
    )

    external_statuses = {row.get("evidence_id"): row for row in external}
    fulltext_status = external_statuses.get("fab686_fulltext", {}).get("status", "MISSING")
    native_perf_status = external_statuses.get("stage28_native_perf_summary", {}).get("status", "MISSING")
    if fulltext_status == "AVAILABLE_UNREVIEWED" or native_perf_status == "PASS_COUNTER_ATTRIBUTION_AVAILABLE":
        external_audit_status = "EXTERNAL_EVIDENCE_AVAILABLE_REVIEW_REQUIRED"
        external_scope = (
            "external artifact registered; manual citation/perf interpretation gates "
            "still required before claim upgrade"
        )
    elif fulltext_status == "MISSING" and native_perf_status == "MISSING":
        external_audit_status = "MISSING_OPTIONAL_EXTERNAL_EVIDENCE"
        external_scope = "no full-text or native perf external evidence registered"
    else:
        external_audit_status = "EXTERNAL_EVIDENCE_INTAKE_RECORDED"
        external_scope = f"fab686_fulltext={fulltext_status}; native_perf={native_perf_status}"
    out.append(
        AuditRow(
            "A8b",
            "external_evidence",
            "Optional external full-text and native perf artifacts are registered when supplied",
            external_audit_status,
            rel(EXTERNAL) if EXTERNAL.exists() else "",
            external_scope,
            "Register external artifacts with scripts/register_external_evidence.py, then rerun final recheck.",
        )
    )

    scoped_ready_ids = {"A1", "A2", "A3", "A4", "A5", "A5b", "A6", "A7"}
    status_by_id = {row.item_id: row.status for row in out}
    scoped_ready = all(
        status_by_id.get(item_id, "").startswith("PASS")
        for item_id in scoped_ready_ids
    )
    theory_status = status_by_id.get("A8", "")
    external_status = status_by_id.get("A8b", "")
    if scoped_ready and theory_status in {
        "BLOCKED_EXTERNAL",
        "CONDITIONAL_COUNTER_SMOKE_ONLY",
    }:
        if external_status == "EXTERNAL_EVIDENCE_AVAILABLE_REVIEW_REQUIRED":
            overall_status = "SCOPED_ENGINEERING_CHAIN_READY__EXTERNAL_REVIEW_REQUIRED"
        else:
            overall_status = "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED"
    elif scoped_ready and theory_status == "PASS_COUNTER_ATTRIBUTION":
        overall_status = "SCOPED_ENGINEERING_CHAIN_READY__COUNTER_EVIDENCE_AVAILABLE_REVIEW_REQUIRED"
    else:
        overall_status = "NOT_READY"

    out.append(
        AuditRow(
            "A9",
            "overall",
            "Original optimization goal status under current evidence",
            overall_status,
            f"{rel(OUT_CSV)}; {rel(OUT_MD)}",
            "complete scoped engineering acceleration evidence exists; novelty/theory/all-parameter claims are not complete",
            "Keep the active goal open until external full-text/perf/native evidence is supplied or the scope is explicitly narrowed.",
        )
    )

    return out


def markdown_table(rows: list[AuditRow]) -> str:
    columns = [
        "item_id",
        "category",
        "status",
        "requirement",
        "scope",
        "remaining_action",
    ]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        data = row.__dict__
        lines.append("| " + " | ".join(data[col] for col in columns) + " |")
    return "\n".join(lines)


def write_markdown(path: Path, rows: list[AuditRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    decision = rows[-1]
    body = f"""# Final Goal Completion Audit

Date: 2026-06-25

## Purpose

This generated audit maps the active PVW/MAT-SAB optimization goal to current
authoritative evidence. It deliberately separates the scoped engineering
acceleration package from stronger claims that still require external evidence.

Generator:

```text
scripts/build_final_goal_completion_audit.py
```

Primary CSV:

```text
repro/final_goal_completion_audit.csv
```

## Decision

```text
{decision.status}
```

Interpretation:

```text
{decision.scope}
```

## Matrix

{markdown_table(rows)}
"""
    path.write_text(body, encoding="utf-8", newline="\n")


def main() -> None:
    rows = audit()
    write_csv(OUT_CSV, rows)
    write_markdown(OUT_MD, rows)
    print(f"Wrote {rel(OUT_CSV)}")
    print(f"Wrote {rel(OUT_MD)}")


if __name__ == "__main__":
    main()
