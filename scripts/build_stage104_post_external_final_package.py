#!/usr/bin/env python3
"""Build Stage104 post-external final scoped package refresh."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage104_post_external_final_package"
OUT_SUMMARY = OUT_DIR / "summary.csv"
OUT_PERF = OUT_DIR / "performance_claims.csv"
OUT_CLAIMS = OUT_DIR / "claim_boundary.csv"
OUT_BRIDGE = OUT_DIR / "evidence_bridge.csv"
OUT_COMMANDS = OUT_DIR / "reproduction_commands.csv"
OUT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage104_post_external_final_package.md"

STAGE91_SUMMARY = ROOT / "repro" / "stage91_final_package" / "summary.csv"
STAGE91_PERF = ROOT / "repro" / "stage91_final_package" / "performance_claims.csv"
STAGE91_NOISE = ROOT / "repro" / "stage91_final_package" / "noise_resource_claims.csv"
FINAL_AUDIT = ROOT / "repro" / "final_goal_completion_audit.csv"
BLOCKERS = ROOT / "repro" / "remaining_blocker_dashboard.csv"
STAGE101 = ROOT / "repro" / "stage101_cb5_remote_native_perf" / "summary.csv"
STAGE101_COUNTERS = ROOT / "repro" / "stage101_cb5_remote_native_perf" / "counter_metrics.csv"
STAGE102 = ROOT / "repro" / "stage102_686_source_anchor_review" / "summary.csv"
STAGE102_MATRIX = ROOT / "repro" / "stage102_686_source_anchor_review" / "review_matrix.csv"
STAGE103 = ROOT / "repro" / "stage103_related_work_novelty_review" / "summary.csv"
STAGE103_NOVELTY = ROOT / "repro" / "stage103_related_work_novelty_review" / "novelty_claim_matrix.csv"
STAGE42 = ROOT / "repro" / "stage42_evidence_closure_audit.csv"
RUN_LOG = ROOT / "repro" / "run_log.csv"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def status(path: Path, key: str, value: str, field: str = "status") -> str:
    for row in read_csv(path):
        if row.get(key) == value:
            return row.get(field, "MISSING")
    return "MISSING"


def row_by(rows: List[Dict[str, str]], key: str, value: str) -> Dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def artifact_index(paths: List[Path]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path in paths:
        rows.append(
            {
                "artifact": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256_file(path) if path.exists() else "",
                "size_bytes": str(path.stat().st_size) if path.exists() else "",
            }
        )
    return rows


def metric(source: str, metric_name: str) -> str:
    for row in read_csv(STAGE101_COUNTERS):
        if row.get("source") == source and row.get("metric") == metric_name:
            return row.get("value", "")
    return ""


def build_performance_claims() -> List[Dict[str, str]]:
    fields = [
        "lane",
        "param",
        "r",
        "evidence_level",
        "status",
        "mean_speedup",
        "min_speedup",
        "max_speedup",
        "ci95_low",
        "ci95_high",
        "claim_level",
        "source",
    ]
    rows = [{field: row.get(field, "") for field in fields} for row in read_csv(STAGE91_PERF)]
    rows.append(
        {
            "lane": "native_counter_sample_r4",
            "param": "SET_2_3_2048",
            "r": "4",
            "evidence_level": "1_run_native_perf_counter_attribution",
            "status": "PASS_STAGE101_COUNTER_SAMPLE_NOT_STATISTICAL",
            "mean_speedup": metric("attribution_run", "speedup_vs_scalar_repeated"),
            "min_speedup": "",
            "max_speedup": "",
            "ci95_low": "",
            "ci95_high": "",
            "claim_level": "counter_attribution_sample_not_final_latency_claim",
            "source": rel(STAGE101_COUNTERS),
        }
    )
    return rows


def build_claim_boundary() -> List[Dict[str, str]]:
    return [
        {
            "claim_id": "C1",
            "claim": "PVW/MAT-SAB explicit path improves complete SAB throughput over repeated scalar SAB for tested binary target r=2/r=4.",
            "status": "ENGINEERING_SUPPORTED",
            "evidence": "repro/stage36_target_perf_summary.csv; repro/stage36_target_noise_seeds50/aggregate.csv; repro/stage36_resource_summary.csv",
            "allowed_wording": "Scoped engineering throughput improvement under tested binary parameters and same backend.",
            "blocked_wording": "Universal, all-parameter, novelty, or theoretical-optimality claim.",
        },
        {
            "claim_id": "C2",
            "claim": "H14 backend FromDFT-add is the preferred explicit r=6 engineering path.",
            "status": "ENGINEERING_SUPPORTED_EXPLICIT_NOT_DEFAULT",
            "evidence": "repro/stage88_h14_backend_repeated_gates/full_sab_repeated.csv; repro/stage89_h14_promotion_policy_integration/summary.csv",
            "allowed_wording": "Preferred explicit r=6 local engineering path with 3-run/noise/resource support.",
            "blocked_wording": "Default path promotion or high-stat/paper-level r=6 claim.",
        },
        {
            "claim_id": "C3",
            "claim": "MAT-AVX512 load/store/FMA attribution.",
            "status": "COUNTER_EVIDENCE_AVAILABLE_NOT_OPTIMALITY",
            "evidence": f"{rel(STAGE101)}; {rel(STAGE101_COUNTERS)}; {rel(FINAL_AUDIT)}",
            "allowed_wording": "Native perf counters are available for attribution and record retired load/store and AVX512 FP events.",
            "blocked_wording": "Theoretical optimality or memory-operation superiority without model/assembly interpretation.",
        },
        {
            "claim_id": "C4",
            "claim": "Novelty beyond scoped engineering/systems integration.",
            "status": "SCOPED_NOVELTY_REVIEWED_BROAD_CLAIMS_BLOCKED",
            "evidence": f"{rel(STAGE103)}; {rel(STAGE103_NOVELTY)}",
            "allowed_wording": "Scoped implementation and empirical study of PVW/MAT external-product batching for the 2025/686 SAB hot path.",
            "blocked_wording": "Broad first shared-mask, batch/SIMD, new-asymptotic, all-parameter, or non-binary novelty.",
        },
        {
            "claim_id": "C5",
            "claim": "Theorem-level 2025/686 protocol, table, figure, or experiment citations.",
            "status": "SOURCE_ANCHORS_REVIEWED_SCOPED_CITATIONS",
            "evidence": f"{rel(STAGE102)}; {rel(STAGE102_MATRIX)}",
            "allowed_wording": "Use reviewed 2025/686 page/section anchors for protocol, complexity, noise, and parameter context.",
            "blocked_wording": "Use 2025/686 anchors as proof that the original paper proposed the local PVW/MAT path.",
        },
    ]


def build_bridge() -> List[Dict[str, str]]:
    final = read_csv(FINAL_AUDIT)
    blockers = read_csv(BLOCKERS)
    bridge: List[Dict[str, str]] = []
    for item_id in ["A8", "A8b", "A9"]:
        row = row_by(final, "item_id", item_id)
        bridge.append(
            {
                "bridge_id": item_id,
                "status": row.get("status", "MISSING"),
                "evidence": row.get("evidence", ""),
                "meaning": row.get("scope", ""),
                "claim_policy": row.get("remaining_action", ""),
            }
        )
    for blocker_id in ["CB5", "CB6", "CB7"]:
        row = row_by(blockers, "blocker_id", blocker_id)
        bridge.append(
            {
                "bridge_id": blocker_id,
                "status": row.get("current_status", "MISSING"),
                "evidence": row.get("evidence", ""),
                "meaning": row.get("blocking_condition", ""),
                "claim_policy": row.get("claim_policy", ""),
            }
        )
    return bridge


def build_commands() -> List[Dict[str, str]]:
    return [
        {
            "step": "stage101_parse_remote_native_perf",
            "command": "python scripts/build_stage101_cb5_remote_native_perf.py",
            "purpose": "Rebuild CB5 native perf summary from preserved raw logs.",
        },
        {
            "step": "stage102_review_686_anchors",
            "command": "python scripts/build_stage102_686_source_anchor_review.py",
            "purpose": "Rebuild reviewed 2025/686 source-anchor matrix.",
        },
        {
            "step": "stage103_related_work_boundary",
            "command": "python scripts/build_stage103_related_work_novelty_review.py",
            "purpose": "Rebuild scoped related-work/novelty matrix.",
        },
        {
            "step": "stage104_refresh_final_package",
            "command": "python scripts/build_stage104_post_external_final_package.py",
            "purpose": "Rebuild post-external final package refresh.",
        },
        {
            "step": "closure_audit",
            "command": "python scripts/build_stage42_evidence_closure_audit.py && python scripts/verify_stage42_closure.py",
            "purpose": "Regenerate and verify the closure package from a clean input state.",
        },
    ]


def upsert_run_log() -> None:
    fields = [
        "run_id",
        "date",
        "commit_or_state",
        "stage",
        "backend",
        "command",
        "params",
        "seed",
        "status",
        "summary",
        "artifacts",
    ]
    rows = read_csv(RUN_LOG)
    rows = [row for row in rows if row.get("run_id") != "stage104-post-external-final-package-001"]
    rows.append(
        {
            "run_id": "stage104-post-external-final-package-001",
            "date": "2026-06-30",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 104",
            "backend": "n/a",
            "command": "python scripts/build_stage104_post_external_final_package.py",
            "params": "post-Stage103 final package refresh; no heavy benchmark rerun",
            "seed": "repro-pack",
            "status": "PASS_STAGE104_POST_EXTERNAL_FINAL_PACKAGE_REFRESHED_SCOPED",
            "summary": "Stage104 refreshes the final scoped SAB package after CB5/CB6/CB7 are resolved. It preserves Stage91 performance/noise/resource claims, adds Stage101 native counter attribution sample, and updates claim boundaries to scoped-reviewed status.",
            "artifacts": "docs/stage104_post_external_final_package.md; experiments/stage104_post_external_final_package_plan.md; scripts/build_stage104_post_external_final_package.py; repro/stage104_post_external_final_package/summary.csv; repro/stage104_post_external_final_package/performance_claims.csv; repro/stage104_post_external_final_package/claim_boundary.csv; repro/stage104_post_external_final_package/evidence_bridge.csv; repro/stage104_post_external_final_package/reproduction_commands.csv; repro/stage104_post_external_final_package/artifact_index.csv",
        }
    )
    write_csv(RUN_LOG, rows, fields)


def write_md(summary_rows: List[Dict[str, str]], claims: List[Dict[str, str]], perf_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage104 Post-External Final Package",
        "",
        "Date: 2026-06-30",
        "",
        "## Decision",
        "",
        "`PASS_STAGE104_POST_EXTERNAL_FINAL_PACKAGE_REFRESHED_SCOPED`",
        "",
        "Stage104 refreshes the final scoped SAB optimization package after",
        "Stage101-103 resolved CB5/CB6/CB7. It does not rerun heavy benchmarks",
        "and does not upgrade beyond scoped systems/engineering claims.",
        "",
        "## Gates",
        "",
        "| gate | status | detail |",
        "|---|---|---|",
    ]
    for row in summary_rows:
        lines.append(f"| {row['gate']} | {row['status']} | {row['detail']} |")
    lines.extend(["", "## Performance Claims", "", "| lane | r | evidence | speedup | claim level |", "|---|---:|---|---:|---|"])
    for row in perf_rows:
        lines.append(
            f"| {row['lane']} | {row['r']} | {row['evidence_level']} | {row['mean_speedup']} | {row['claim_level']} |"
        )
    lines.extend(["", "## Claim Boundary", "", "| claim | status | allowed | blocked |", "|---|---|---|---|"])
    for row in claims:
        lines.append(
            f"| {row['claim_id']} | {row['status']} | {row['allowed_wording']} | {row['blocked_wording']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The final package is now post-external-review but remains scoped. The",
            "complete-SAB speedup evidence still comes from the Stage36/Stage88",
            "campaigns; Stage101 is a native counter-attribution sample, not a",
            "replacement for statistical performance evidence. Stage102 enables",
            "scoped 2025/686 source citations, and Stage103 bounds novelty wording.",
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    final_a9 = status(FINAL_AUDIT, "item_id", "A9")
    stage101 = status(STAGE101, "gate", "stage101_cb5_decision")
    stage102 = status(STAGE102, "gate", "stage102_decision")
    stage103 = status(STAGE103, "gate", "stage103_decision")
    stage91_perf = status(STAGE91_SUMMARY, "gate", "stage91_performance_gate")
    stage91_noise = status(STAGE91_SUMMARY, "gate", "stage91_noise_resource_gate")
    stage42_overall = status(STAGE42, "check_id", "S42-OVERALL")

    performance_rows = build_performance_claims()
    claim_rows = build_claim_boundary()
    bridge_rows = build_bridge()
    command_rows = build_commands()

    summary_rows = [
        {
            "gate": "stage104_final_audit_precondition",
            "status": "PASS"
            if final_a9 == "SCOPED_ENGINEERING_CHAIN_READY__EXTERNAL_REVIEWED_STRONGER_CLAIMS_SCOPED"
            else "FAIL",
            "evidence": rel(FINAL_AUDIT),
            "detail": f"A9={final_a9}",
            "next_action": "Refresh final audit after Stage101-103 before Stage104.",
        },
        {
            "gate": "stage104_stage101_counter_gate",
            "status": "PASS" if stage101 == "PASS_STAGE101_CB5_NATIVE_PERF_COUNTERS_RECORDED" else "FAIL",
            "evidence": rel(STAGE101),
            "detail": f"stage101={stage101}; native_sample_speedup={metric('attribution_run', 'speedup_vs_scalar_repeated')}x",
            "next_action": "Rerun Stage101 parser if native counter evidence is missing.",
        },
        {
            "gate": "stage104_stage102_source_anchor_gate",
            "status": "PASS" if stage102 == "PASS_STAGE102_686_SOURCE_ANCHORS_REVIEWED" else "FAIL",
            "evidence": rel(STAGE102),
            "detail": f"stage102={stage102}",
            "next_action": "Rerun Stage102 if reviewed source anchors are missing.",
        },
        {
            "gate": "stage104_stage103_novelty_gate",
            "status": "PASS" if stage103 == "PASS_STAGE103_RELATED_WORK_NOVELTY_REVIEW_SCOPED" else "FAIL",
            "evidence": rel(STAGE103),
            "detail": f"stage103={stage103}",
            "next_action": "Rerun Stage103 if scoped novelty boundary is missing.",
        },
        {
            "gate": "stage104_stage91_perf_noise_inheritance",
            "status": "PASS"
            if stage91_perf == "PASS_SCOPED_COMPLETE_SAB_PERFORMANCE"
            and stage91_noise == "PASS_SCOPED_NOISE_RESOURCE"
            else "FAIL",
            "evidence": f"{rel(STAGE91_SUMMARY)}; {rel(STAGE91_PERF)}; {rel(STAGE91_NOISE)}",
            "detail": f"performance={stage91_perf}; noise_resource={stage91_noise}",
            "next_action": "Rerun heavy performance/noise/resource gates if source or backend changes.",
        },
        {
            "gate": "stage104_closure_precondition",
            "status": "PASS" if stage42_overall == "PASS_SCOPED_EVIDENCE_CLOSURE_STRONGER_CLAIMS_BLOCKED" else "FAIL",
            "evidence": rel(STAGE42),
            "detail": f"stage42={stage42_overall}",
            "next_action": "Regenerate closure audit after Stage104 files are added.",
        },
        {
            "gate": "stage104_decision",
            "status": "PASS_STAGE104_POST_EXTERNAL_FINAL_PACKAGE_REFRESHED_SCOPED"
            if all(
                row["status"].startswith("PASS")
                for row in [
                    {
                        "status": "PASS"
                        if final_a9 == "SCOPED_ENGINEERING_CHAIN_READY__EXTERNAL_REVIEWED_STRONGER_CLAIMS_SCOPED"
                        else "FAIL"
                    },
                    {"status": "PASS" if stage101 == "PASS_STAGE101_CB5_NATIVE_PERF_COUNTERS_RECORDED" else "FAIL"},
                    {"status": "PASS" if stage102 == "PASS_STAGE102_686_SOURCE_ANCHORS_REVIEWED" else "FAIL"},
                    {"status": "PASS" if stage103 == "PASS_STAGE103_RELATED_WORK_NOVELTY_REVIEW_SCOPED" else "FAIL"},
                    {"status": "PASS" if stage91_perf == "PASS_SCOPED_COMPLETE_SAB_PERFORMANCE" and stage91_noise == "PASS_SCOPED_NOISE_RESOURCE" else "FAIL"},
                ]
            )
            else "FAIL_STAGE104_POST_EXTERNAL_FINAL_PACKAGE",
            "evidence": rel(OUT_SUMMARY),
            "detail": "Post-external final package refreshed with scoped claim boundaries.",
            "next_action": "Use Stage104 as the current final package until source/backend/claim scope changes.",
        },
    ]

    write_csv(
        OUT_PERF,
        performance_rows,
        [
            "lane",
            "param",
            "r",
            "evidence_level",
            "status",
            "mean_speedup",
            "min_speedup",
            "max_speedup",
            "ci95_low",
            "ci95_high",
            "claim_level",
            "source",
        ],
    )
    write_csv(
        OUT_CLAIMS,
        claim_rows,
        ["claim_id", "claim", "status", "evidence", "allowed_wording", "blocked_wording"],
    )
    write_csv(
        OUT_BRIDGE,
        bridge_rows,
        ["bridge_id", "status", "evidence", "meaning", "claim_policy"],
    )
    write_csv(OUT_COMMANDS, command_rows, ["step", "command", "purpose"])
    write_csv(
        OUT_SUMMARY,
        summary_rows,
        ["gate", "status", "evidence", "detail", "next_action"],
    )
    write_md(summary_rows, claim_rows, performance_rows)
    write_csv(
        OUT_INDEX,
        artifact_index([OUT_SUMMARY, OUT_PERF, OUT_CLAIMS, OUT_BRIDGE, OUT_COMMANDS, OUT_MD]),
        ["artifact", "exists", "sha256", "size_bytes"],
    )
    upsert_run_log()
    decision = summary_rows[-1]["status"]
    print(f"Wrote {rel(OUT_SUMMARY)}")
    print(f"Wrote {rel(OUT_PERF)}")
    print(f"Wrote {rel(OUT_CLAIMS)}")
    print(f"Wrote {rel(OUT_MD)}")
    print(f"Stage104 post-external final package: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
