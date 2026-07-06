#!/usr/bin/env python3
"""Stage339: refresh scoped paper/package evidence after the Stage338 gate."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage339_scoped_paper_package_refresh"

DOC = ROOT / "docs" / "stage339_scoped_paper_package_refresh.md"
CLAIM_DOC = ROOT / "docs" / "pvw_mat_sab_claim_matrix_stage339.md"
THEORY = ROOT / "theory_checks" / "stage339_metric_and_claim_ladder.md"
PLAN = ROOT / "experiments" / "stage340_parameter_matrix_or_new_mechanism_gate.md"
BUILDER = ROOT / "scripts" / "build_stage339_scoped_paper_package_refresh.py"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"

SUMMARY = OUT / "summary.csv"
PRIMARY_RESULT = OUT / "primary_result.csv"
CLAIM_MATRIX = OUT / "claim_matrix.csv"
NEGATIVE_ABLATIONS = OUT / "negative_ablation_table.csv"
PARAM_COVERAGE = OUT / "parameter_coverage.csv"
REVIEWER_RISK = OUT / "reviewer_risk_register.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
BLUEPRINT = OUT / "paper_section_blueprint.md"
REPORT = OUT / "stage339_report.md"
COMMANDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"

STAGE338_SUMMARY = ROOT / "repro" / "stage338_new_mechanism_or_proof_intake" / "summary.csv"
STAGE338_PACKAGE = ROOT / "repro" / "stage338_new_mechanism_or_proof_intake" / "package_route.csv"
STAGE337_CLOSED = ROOT / "repro" / "stage337_frontier_correction" / "closed_candidate_audit.csv"
STAGE331_SUMMARY = ROOT / "repro" / "stage331_current_head_highstat_refresh" / "summary.csv"
STAGE331_PERF = ROOT / "repro" / "stage331_current_head_highstat_refresh" / "perf_summary.csv"
STAGE331_NOISE = ROOT / "repro" / "stage331_current_head_highstat_refresh" / "noise_summary.csv"
STAGE36_TARGET_PERF = ROOT / "repro" / "stage36_target_perf_summary.csv"
STAGE36_TARGET_NOISE = ROOT / "repro" / "stage36_target_noise_seeds50" / "aggregate.csv"
STAGE36_ADDED_PERF = ROOT / "repro" / "stage36_added_params_runs10_seeds20" / "performance_stats.csv"
STAGE36_ADDED_NOISE = ROOT / "repro" / "stage36_added_params_runs10_seeds20" / "noise_summary.csv"
STAGE328_REQ = ROOT / "repro" / "stage328_active_goal_requirement_audit" / "requirement_matrix.csv"
STAGE335_PROOF = ROOT / "repro" / "stage335_source_and_compact_route" / "proof_gate.csv"

DECISION = "PASS_STAGE339_SCOPED_PACKAGE_REFRESH_NO_STRONGER_CLAIM"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return (
        path.read_text(encoding="utf-8", errors="replace")
        .replace("\x00", "")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: Iterable[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        if current and not current.endswith("\n"):
            handle.write("\n")
        handle.write(text.lstrip())
        if not text.endswith("\n"):
            handle.write("\n")


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_size(path: Path) -> int:
    return path.stat().st_size if path.exists() and path.is_file() else 0


def first_row(path: Path) -> dict[str, str]:
    rows = read_csv(path)
    return rows[0] if rows else {}


def md_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    lines = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
    for row in rows:
        cells = [str(row.get(field, "")).replace("|", "\\|") for field in fields]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def fnum(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def primary_result_rows() -> list[dict[str, object]]:
    stage331 = first_row(STAGE331_SUMMARY)
    perf = first_row(STAGE331_PERF)
    noise = first_row(STAGE331_NOISE)
    r = 4
    pvw_lane = fnum(stage331.get("t_bootstrap_over_r_mean_us"))
    scalar_lane = fnum(stage331.get("scalar_t_bootstrap_over_r_mean_us"))
    return [
        {
            "evidence_class": "current_head_primary",
            "path": "direct_pvw_mat_sab",
            "parameter": "BINARY SET_2_3_2048 include-zero",
            "backend": "spqlios_avx512 WSL",
            "r_body_lanes": r,
            "samples": stage331.get("samples", ""),
            "correctness": stage331.get("correctness", ""),
            "pvw_total_bootstrap_us": f"{pvw_lane * r:.3f}",
            "pvw_t_bootstrap_over_r_us": stage331.get("t_bootstrap_over_r_mean_us", ""),
            "pvw_t_over_r_ci95_us": f"{stage331.get('t_bootstrap_over_r_ci95_low_us', '')}..{stage331.get('t_bootstrap_over_r_ci95_high_us', '')}",
            "scalar_repeated_total_us": f"{scalar_lane * r:.3f}",
            "scalar_repeated_t_over_r_us": stage331.get("scalar_t_bootstrap_over_r_mean_us", ""),
            "speedup_vs_repeated_scalar": stage331.get("speedup_vs_repeated_scalar_mean", ""),
            "noise_trials": noise.get("trials", stage331.get("noise_trials", "")),
            "noise_pair_failures": noise.get("pair_failures", stage331.get("noise_pair_failures", "")),
            "maxrss_kb": stage331.get("time_maxrss_kb", ""),
            "source_head": stage331.get("git_head", ""),
            "source": rel(STAGE331_SUMMARY),
        }
    ]


def claim_matrix_rows(primary: list[dict[str, object]]) -> list[dict[str, object]]:
    row = primary[0]
    speedup = row.get("speedup_vs_repeated_scalar", "")
    return [
        {
            "claim_id": "C1_metric",
            "status": "PASS",
            "paper_safe_statement": "The primary endpoint is complete bootstrapping wall time divided by r processed MAT/RLWE body lanes.",
            "blocked_statement": "Single-lane latency speedup over one scalar bootstrap.",
            "evidence": rel(STAGE331_SUMMARY),
        },
        {
            "claim_id": "C2_current_head_r4_speedup",
            "status": "PASS_SCOPED",
            "paper_safe_statement": f"For the measured r=4 BINARY SET_2_3_2048 include-zero path, direct PVW/MAT-SAB reaches {speedup}x T_bootstrap/r speedup over repeated scalar SAB.",
            "blocked_statement": "Universal PVW/MAT-SAB speedup or all-parameter generality.",
            "evidence": rel(STAGE331_SUMMARY),
        },
        {
            "claim_id": "C3_correctness_noise_resource",
            "status": "PASS_SCOPED",
            "paper_safe_statement": f"Current-head output equivalence has {row.get('noise_pair_failures')}/{row.get('noise_trials')} pair failures and max RSS {row.get('maxrss_kb')} KB.",
            "blocked_statement": "Security proof for compact selector variants.",
            "evidence": rel(STAGE331_NOISE),
        },
        {
            "claim_id": "C4_algorithmic_metric_vs_backend",
            "status": "PASS_SCOPED",
            "paper_safe_statement": "The primary comparison is same-backend repeated scalar SAB versus r-body PVW/MAT-SAB by T_bootstrap/r.",
            "blocked_statement": "Attributing the full speedup to AVX512 instructions alone or to backend changes.",
            "evidence": rel(STAGE338_PACKAGE),
        },
        {
            "claim_id": "C5_mat_rlwe_theoretical_optimality",
            "status": "BLOCK",
            "paper_safe_statement": "Current exact dense MAT/RLWE route is closed under recorded local evidence.",
            "blocked_statement": "The current MAT/RLWE SAB implementation is theoretically optimal.",
            "evidence": rel(STAGE328_REQ),
        },
        {
            "claim_id": "C6_compact_or_structured_sab",
            "status": "BLOCK",
            "paper_safe_statement": "Compact/structured selector remains a proof-gated future route.",
            "blocked_statement": "Compact selector has complete SAB acceleration or production security.",
            "evidence": rel(STAGE335_PROOF),
        },
        {
            "claim_id": "C7_parameter_generalization",
            "status": "PARTIAL_HISTORICAL_NEEDS_CURRENT_HEAD_REFRESH",
            "paper_safe_statement": "Historical r=2/r=4 and added binary parameter evidence exists, but the current-head primary claim remains r=4 SET_2_3_2048.",
            "blocked_statement": "Current-head all-parameter claim.",
            "evidence": f"{rel(STAGE36_TARGET_PERF)}; {rel(STAGE36_ADDED_PERF)}",
        },
        {
            "claim_id": "C8_novelty",
            "status": "BLOCK_UNTIL_CITATION_VERIFIED",
            "paper_safe_statement": "Novelty wording must wait for real, source-checked related-work support.",
            "blocked_statement": "Novel shared-mask/common-mask or multi-output bootstrapping claim without verified sources.",
            "evidence": rel(STAGE338_PACKAGE),
        },
    ]


def negative_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in read_csv(STAGE337_CLOSED):
        rows.append(
            {
                "candidate": row.get("candidate", ""),
                "status": row.get("status", ""),
                "usable_in_paper_as": "negative_ablation_or_route_boundary",
                "reason": row.get("reason", ""),
                "reopen_condition": row.get("reopen_condition", ""),
                "evidence": row.get("evidence", ""),
            }
        )
    return rows


def parameter_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    primary = primary_result_rows()[0]
    rows.append(
        {
            "parameter": primary["parameter"],
            "r": primary["r_body_lanes"],
            "status": "CURRENT_HEAD_PRIMARY_PASS",
            "speedup": primary["speedup_vs_repeated_scalar"],
            "performance_samples": primary["samples"],
            "noise_status": f"{primary['noise_pair_failures']}/{primary['noise_trials']} pair failures",
            "claim_use": "main scoped claim",
            "source": primary["source"],
        }
    )

    target_noise_by_r = {row.get("r", ""): row for row in read_csv(STAGE36_TARGET_NOISE)}
    for row in read_csv(STAGE36_TARGET_PERF):
        r = row.get("r", "")
        noise = target_noise_by_r.get(r, {})
        status = "HISTORICAL_PASS_NEEDS_CURRENT_HEAD_REFRESH"
        if r == "4":
            status = "HISTORICAL_PASS_SUPERSEDED_BY_CURRENT_HEAD_R4"
        rows.append(
            {
                "parameter": "BINARY SET_2_3_2048",
                "r": r,
                "status": status,
                "speedup": row.get("mean_speedup", ""),
                "performance_samples": row.get("samples", ""),
                "noise_status": f"{noise.get('pair_failures', '')}/{noise.get('seeds', '')} seed failures",
                "claim_use": "supporting historical matrix only",
                "source": rel(STAGE36_TARGET_PERF),
            }
        )

    added_noise = {
        (row.get("param", ""), row.get("r", "")): row
        for row in read_csv(STAGE36_ADDED_NOISE)
    }
    for row in read_csv(STAGE36_ADDED_PERF):
        key = (row.get("param", ""), row.get("r", ""))
        noise = added_noise.get(key, {})
        rows.append(
            {
                "parameter": f"BINARY {row.get('param', '')}",
                "r": row.get("r", ""),
                "status": "HISTORICAL_ADDED_BINARY_PASS_NEEDS_CURRENT_HEAD_REFRESH",
                "speedup": row.get("mean_speedup", ""),
                "performance_samples": row.get("runs", ""),
                "noise_status": f"{noise.get('pair_failures', '')}/{noise.get('seeds', '')} seed failures",
                "claim_use": "do not use as current-head generality without rerun",
                "source": rel(STAGE36_ADDED_PERF),
            }
        )

    rows.append(
        {
            "parameter": "ternary/include-zero branches beyond recorded binary target",
            "r": "n/a",
            "status": "NOT_COVERED_BY_CURRENT_STAGE339_CLAIM",
            "speedup": "",
            "performance_samples": "",
            "noise_status": "",
            "claim_use": "blocked until measured",
            "source": "",
        }
    )
    return rows


def reviewer_risk_rows() -> list[dict[str, object]]:
    return [
        {
            "risk": "metric_confusion",
            "severity": "high",
            "problem": "Readers may compare one PVW r=4 run to one scalar bootstrap instead of repeated scalar per processed bit.",
            "mitigation": "Always report T_bootstrap/r and repeated scalar T/r; include total times only as derivation.",
            "next_action": "Keep C1 metric gate in every report table.",
        },
        {
            "risk": "theoretical_optimality_overclaim",
            "severity": "high",
            "problem": "Current exact dense route is closed locally but not proven globally optimal for MAT-RLWE SAB.",
            "mitigation": "Use not-proven language; require a formal lower bound or compact proof to strengthen.",
            "next_action": "Stage340 may open proof route only with a concrete proof object.",
        },
        {
            "risk": "novelty_prior_art",
            "severity": "high",
            "problem": "Shared-mask, common-mask, multi-output, and amortized bootstrapping prior art can overlap broad claims.",
            "mitigation": "Do not claim novelty until source-verified literature matrix is complete.",
            "next_action": "Run citation/literature verification before manuscript novelty wording.",
        },
        {
            "risk": "parameter_generality",
            "severity": "medium",
            "problem": "Current-head primary result covers r=4 SET_2_3_2048; older matrices are historical.",
            "mitigation": "Mark historical rows and rerun current-head parameter matrix before broader claims.",
            "next_action": "Stage340 parameter matrix refresh.",
        },
        {
            "risk": "resource_cost",
            "severity": "medium",
            "problem": "PVW/MAT key size, memory peak, and keygen time must be reported with throughput.",
            "mitigation": "Current max RSS is recorded; broader resource matrix should be refreshed with parameter reruns.",
            "next_action": "Include RSS/key/keygen fields in any Stage340 run.",
        },
        {
            "risk": "backend_attribution",
            "severity": "medium",
            "problem": "AVX512/backend effects can be mistaken for algorithmic MAT-SAB effects.",
            "mitigation": "Same-backend A/B remains primary; perf counters are attribution, not the final speedup metric.",
            "next_action": "Use native counters only to explain, not replace, complete SAB A/B.",
        },
    ]


def proof_rows(
    claims: list[dict[str, object]],
    params: list[dict[str, object]],
) -> list[dict[str, object]]:
    stage338 = first_row(STAGE338_SUMMARY)
    stage331 = first_row(STAGE331_SUMMARY)
    current_rows = [row for row in params if row.get("status") == "CURRENT_HEAD_PRIMARY_PASS"]
    blocked_claims = [row for row in claims if str(row.get("status", "")).startswith("BLOCK")]
    return [
        {
            "gate": "G1_stage338_route",
            "status": "PASS" if stage338.get("decision") else "MISSING",
            "metric": "Stage338 decision",
            "value": stage338.get("decision", ""),
            "interpretation": "Stage339 follows the no-new-mechanism scoped package route.",
        },
        {
            "gate": "G2_current_head_primary",
            "status": "PASS" if stage331.get("decision") == "PASS_STAGE331_CURRENT_HEAD_HIGHSTAT_REFRESH" else "FAIL",
            "metric": "Stage331 decision",
            "value": stage331.get("decision", ""),
            "interpretation": "The primary result is high-stat current-head complete-SAB evidence.",
        },
        {
            "gate": "G3_claim_boundary",
            "status": "PASS" if blocked_claims else "FAIL",
            "metric": "blocked stronger claims",
            "value": str(len(blocked_claims)),
            "interpretation": "The package keeps optimality, compact, novelty, and universal claims blocked.",
        },
        {
            "gate": "G4_parameter_scope",
            "status": "PASS_SCOPED",
            "metric": "current-head primary rows",
            "value": str(len(current_rows)),
            "interpretation": "Current-head claim is intentionally scoped; historical rows are not promoted.",
        },
        {
            "gate": "G5_decision",
            "status": DECISION,
            "metric": "stage decision",
            "value": "scoped_package_refreshed",
            "interpretation": "Proceed to Stage340 only for parameter refresh, literature verification, new mechanism, or formal proof.",
        },
    ]


def next_rows() -> list[dict[str, object]]:
    return [
        {
            "priority": "P0",
            "route": "stage340_parameter_matrix_current_head_refresh",
            "entry_condition": "A broader than r=4 SET_2_3_2048 claim is desired.",
            "gate": "same-backend complete SAB T_bootstrap/r A/B plus noise/RSS for each parameter and r.",
            "failure_action": "Keep Stage339 claim scoped to the primary row.",
        },
        {
            "priority": "P1",
            "route": "stage340_verified_related_work_matrix",
            "entry_condition": "Any novelty or paper contribution wording is needed.",
            "gate": "real source-checked citations only; no broad shared-mask/common-mask novelty overclaim.",
            "failure_action": "Write as scoped engineering systems result.",
        },
        {
            "priority": "P2",
            "route": "stage340_new_mechanism_protocol",
            "entry_condition": "A concrete new load/store/count/backend primitive is identified.",
            "gate": "mechanism model, isolated equivalence, isolated microbench, then complete SAB A/B.",
            "failure_action": "Reject before hot-path integration.",
        },
        {
            "priority": "P3",
            "route": "stage340_formal_compact_state_proof",
            "entry_condition": "A neighbor/cross-body closed compact state proof is available.",
            "gate": "distribution/keygen/security/noise proof before production code.",
            "failure_action": "Keep compact SAB claim blocked.",
        },
    ]


def append_run_log() -> None:
    marker = "stage339-scoped-paper-package-refresh-001"
    if marker in read_text(RUN_LOG):
        return
    exists = RUN_LOG.exists()
    RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    with RUN_LOG.open("a", encoding="utf-8", newline="\n") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        if not exists:
            writer.writerow(
                [
                    "run_id",
                    "date",
                    "git_head",
                    "stage",
                    "backend",
                    "command",
                    "params",
                    "seed",
                    "status",
                    "interpretation",
                    "artifacts",
                ]
            )
        writer.writerow(
            [
                marker,
                "2026-07-06",
                git_head(),
                "Stage 339",
                "evidence-package",
                "python scripts/build_stage339_scoped_paper_package_refresh.py",
                "Stage338 package route plus Stage331 current-head evidence",
                "n/a",
                DECISION,
                "Refreshes scoped paper/package claims, negative ablations, parameter coverage, and reviewer-risk gates without stronger speedup claims.",
                f"{rel(DOC)}; {rel(PRIMARY_RESULT)}; {rel(CLAIM_MATRIX)}; {rel(PARAM_COVERAGE)}; {rel(REVIEWER_RISK)}",
            ]
        )


def artifact_index(paths: list[Path]) -> None:
    rows = []
    for path in paths:
        rows.append(
            {
                "artifact": rel(path),
                "exists": path.exists(),
                "bytes": file_size(path),
                "sha256": sha256_file(path),
            }
        )
    write_csv(ARTIFACT, rows, ["artifact", "exists", "bytes", "sha256"])


def main() -> int:
    primary = primary_result_rows()
    claims = claim_matrix_rows(primary)
    negatives = negative_rows()
    params = parameter_rows()
    risks = reviewer_risk_rows()
    proof = proof_rows(claims, params)
    nextq = next_rows()
    p = primary[0]
    summary = [
        {
            "decision": DECISION,
            "primary_metric": "complete_sab_T_bootstrap_over_r",
            "primary_scope": "current_head_r4_SET_2_3_2048_include_zero_spqlios_avx512",
            "supported_speedup": p.get("speedup_vs_repeated_scalar", ""),
            "samples": p.get("samples", ""),
            "noise_pair_failures": f"{p.get('noise_pair_failures', '')}/{p.get('noise_trials', '')}",
            "parameter_claim_status": "scoped_current_head_plus_historical_matrix_needs_refresh",
            "next_required_for_stronger_claim": "current_head_parameter_matrix_or_verified_literature_or_new_mechanism_proof",
        }
    ]

    write_csv(
        SUMMARY,
        summary,
        [
            "decision",
            "primary_metric",
            "primary_scope",
            "supported_speedup",
            "samples",
            "noise_pair_failures",
            "parameter_claim_status",
            "next_required_for_stronger_claim",
        ],
    )
    write_csv(
        PRIMARY_RESULT,
        primary,
        [
            "evidence_class",
            "path",
            "parameter",
            "backend",
            "r_body_lanes",
            "samples",
            "correctness",
            "pvw_total_bootstrap_us",
            "pvw_t_bootstrap_over_r_us",
            "pvw_t_over_r_ci95_us",
            "scalar_repeated_total_us",
            "scalar_repeated_t_over_r_us",
            "speedup_vs_repeated_scalar",
            "noise_trials",
            "noise_pair_failures",
            "maxrss_kb",
            "source_head",
            "source",
        ],
    )
    write_csv(
        CLAIM_MATRIX,
        claims,
        ["claim_id", "status", "paper_safe_statement", "blocked_statement", "evidence"],
    )
    write_csv(
        NEGATIVE_ABLATIONS,
        negatives,
        ["candidate", "status", "usable_in_paper_as", "reason", "reopen_condition", "evidence"],
    )
    write_csv(
        PARAM_COVERAGE,
        params,
        ["parameter", "r", "status", "speedup", "performance_samples", "noise_status", "claim_use", "source"],
    )
    write_csv(
        REVIEWER_RISK,
        risks,
        ["risk", "severity", "problem", "mitigation", "next_action"],
    )
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "gate", "failure_action"])
    write_text(
        COMMANDS,
        """# Stage339 Reproduction Commands

```powershell
python scripts\\build_stage339_scoped_paper_package_refresh.py
```

Inputs:

- `repro/stage338_new_mechanism_or_proof_intake/`
- `repro/stage331_current_head_highstat_refresh/`
- `repro/stage337_frontier_correction/`
- historical parameter evidence under `repro/stage36_*`
""",
    )

    write_text(
        BLUEPRINT,
        f"""# Stage339 Paper Section Blueprint

## Method Claim

Describe PVW/MAT-SAB as an r-body MAT/RLWE adaptation of the SAB
bootstrapping flow. The implementation claim is for complete SAB throughput per
processed plaintext lane, not for isolated external product speed alone.

## Experimental Endpoint

Primary endpoint: `T_bootstrap/r`.

Primary current-head row:

{md_table(primary, ["parameter", "backend", "r_body_lanes", "samples", "pvw_t_bootstrap_over_r_us", "scalar_repeated_t_over_r_us", "speedup_vs_repeated_scalar", "noise_pair_failures", "maxrss_kb"])}

## Required Caveats

- Current-head main claim is scoped to the primary row.
- Historical r=2 and added-parameter rows need current-head reruns before
  broader wording.
- Negative ablations explain why old exact kernel paths are closed.
- Theoretical optimality, compact SAB, and novelty remain blocked.

## Next Evidence To Add

{md_table(nextq, ["priority", "route", "gate"])}
""",
    )

    write_text(
        REPORT,
        f"""# Stage339 Scoped Paper Package Refresh

Decision: `{DECISION}`.

Stage339 executes the Stage338 P0 route. It refreshes the scoped paper/package
state without introducing a stronger performance claim. The current supported
speedup remains `{p.get('speedup_vs_repeated_scalar', '')}x`, measured as
complete SAB `T_bootstrap/r` for the current-head r=4
`BINARY SET_2_3_2048` include-zero path.

## Summary

{md_table(summary, ["decision", "primary_metric", "primary_scope", "supported_speedup", "samples", "noise_pair_failures", "parameter_claim_status"])}

## Claim Matrix

{md_table(claims, ["claim_id", "status", "paper_safe_statement", "blocked_statement"])}

## Negative Ablations

{md_table(negatives, ["candidate", "status", "reason", "reopen_condition"])}

## Parameter Coverage

{md_table(params, ["parameter", "r", "status", "speedup", "performance_samples", "noise_status", "claim_use"])}

## Reviewer Risks

{md_table(risks, ["risk", "severity", "mitigation", "next_action"])}

## Proof Gate

{md_table(proof, ["gate", "status", "metric", "value"])}
""",
    )

    write_text(
        DOC,
        f"""# Stage339 Scoped Paper Package Refresh

Decision: `{DECISION}`.

The research loop is now at a clean boundary:

- the current supported result is a scoped complete-SAB `T_bootstrap/r` result;
- no new exact implementation mechanism is admitted by Stage338;
- compact/structured SAB remains proof-gated;
- broader parameter and novelty claims require Stage340 evidence.

## Primary Result

{md_table(primary, ["path", "parameter", "backend", "r_body_lanes", "samples", "pvw_t_bootstrap_over_r_us", "scalar_repeated_t_over_r_us", "speedup_vs_repeated_scalar", "noise_pair_failures", "maxrss_kb"])}

## Next Routes

{md_table(nextq, ["priority", "route", "entry_condition", "gate", "failure_action"])}
""",
    )

    write_text(
        CLAIM_DOC,
        f"""# PVW/MAT-SAB Claim Matrix Stage339

This document is the current safe wording source for paper/report drafting.

{md_table(claims, ["claim_id", "status", "paper_safe_statement", "blocked_statement", "evidence"])}

The strongest supported current-head statement is:

> For the measured r=4 BINARY SET_2_3_2048 include-zero path, direct PVW/MAT-SAB
> reaches {p.get('speedup_vs_repeated_scalar', '')}x complete-SAB throughput
> per processed lane, measured by T_bootstrap/r against repeated scalar SAB.

Do not broaden this statement without the Stage340 gates.
""",
    )

    write_text(
        THEORY,
        """# Stage339 Metric And Claim Ladder

The correct comparison dimension for PVW/MAT-SAB is amortized complete
bootstrapping time per processed plaintext lane:

`T_lane = T_complete_bootstrap / r`.

The current primary speedup is therefore:

`speedup = (T_scalar_repeated / r) / (T_pvw_mat_sab / r)`.

For equal r in numerator and denominator, this is also the ratio of total time
for processing r scalar outputs by repeated scalar SAB versus one r-body
PVW/MAT-SAB execution. It is not a comparison between one PVW r-body run and a
single scalar bootstrap.

Claim ladder:

1. Supported: scoped systems result for the measured parameter/backend/path.
2. Historical/partial: older r=2 and added-binary parameter rows.
3. Blocked: theoretical optimality, compact SAB acceleration, universal
   parameter generality, and novelty without verified literature.
""",
    )

    write_text(
        PLAN,
        """# Stage340 Parameter Matrix Or New Mechanism Gate

Stage340 must choose one route.

## Route A: Current-Head Parameter Matrix

Use this when broader experimental wording is needed.

- rerun complete SAB `T_bootstrap/r` A/B for r=2 and r=4;
- include SET_2_3_2048 and any added binary parameter claimed in the paper;
- record correctness, noise, RSS, key size, keygen time, backend, CPU flags,
  raw logs, and commit;
- mark any unsupported branch explicitly.

## Route B: Verified Related Work

Use this before novelty wording.

- verify real sources and exact claim support;
- cite only what has been source-checked;
- keep broad shared-mask/common-mask novelty blocked unless the literature
  matrix supports a narrower claim.

## Route C: New Mechanism Or Formal Proof

Use this only with a concrete mechanism or proof object.

- mechanism route starts with count/load/store model and isolated gates;
- compact route starts with closed-state/keygen/security/noise proof;
- full SAB hot-path work starts only after those gates pass.
""",
    )

    append_once(
        GOAL,
        "<!-- stage339-scoped-paper-package-refresh -->",
        f"""
<!-- stage339-scoped-paper-package-refresh -->
- Stage339: `{DECISION}`. The current safe result is scoped complete-SAB `T_bootstrap/r` speedup `{p.get('speedup_vs_repeated_scalar', '')}x`; broader parameter, novelty, compact, and optimality claims remain gated.
""",
    )
    append_once(
        ROADMAP,
        "<!-- stage339-scoped-paper-package-refresh -->",
        f"""
<!-- stage339-scoped-paper-package-refresh -->
## Stage339: Scoped Paper Package Refresh

- Decision: `{DECISION}`.
- Result: current-head r=4 SET_2_3_2048 complete-SAB `T_bootstrap/r` claim remains the primary supported result.
- Next: Stage340 parameter matrix, verified related work, new mechanism protocol, or formal compact proof.
""",
    )
    append_once(
        HYPOTHESES,
        "H339_scoped_paper_package_refresh:",
        f"""
H339_scoped_paper_package_refresh:
  status: {DECISION}
  primary_metric: complete_sab_T_bootstrap_over_r
  evidence:
    - repro/stage339_scoped_paper_package_refresh/summary.csv
    - repro/stage339_scoped_paper_package_refresh/primary_result.csv
    - repro/stage339_scoped_paper_package_refresh/claim_matrix.csv
    - repro/stage339_scoped_paper_package_refresh/parameter_coverage.csv
  conclusion: >
    The current safe claim is scoped to the current-head r=4 SET_2_3_2048
    complete-SAB T_bootstrap/r result. Historical parameter evidence is kept
    separate, and stronger claims require Stage340 gates.
""",
    )
    append_once(
        MANIFEST,
        "<!-- stage339-scoped-paper-package-refresh-manifest -->",
        """
<!-- stage339-scoped-paper-package-refresh-manifest -->
- stage339_scoped_paper_package_refresh:
  - `docs/stage339_scoped_paper_package_refresh.md`
  - `docs/pvw_mat_sab_claim_matrix_stage339.md`
  - `theory_checks/stage339_metric_and_claim_ladder.md`
  - `experiments/stage340_parameter_matrix_or_new_mechanism_gate.md`
  - `scripts/build_stage339_scoped_paper_package_refresh.py`
  - `repro/stage339_scoped_paper_package_refresh/`
""",
    )
    append_once(
        CHECKLIST,
        "<!-- stage339-scoped-paper-package-refresh-checklist -->",
        f"""
<!-- stage339-scoped-paper-package-refresh-checklist -->
- [x] Stage339 records `{DECISION}` and refreshes scoped claim, parameter, negative-ablation, and reviewer-risk artifacts.
""",
    )
    append_run_log()
    artifact_index(
        [
            DOC,
            CLAIM_DOC,
            THEORY,
            PLAN,
            BUILDER,
            SUMMARY,
            PRIMARY_RESULT,
            CLAIM_MATRIX,
            NEGATIVE_ABLATIONS,
            PARAM_COVERAGE,
            REVIEWER_RISK,
            PROOF,
            NEXT,
            BLUEPRINT,
            REPORT,
            COMMANDS,
        ]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
