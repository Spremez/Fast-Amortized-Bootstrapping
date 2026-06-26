#!/usr/bin/env python3
"""Build the Stage94 local optimization frontier audit."""

from __future__ import annotations

import argparse
import csv
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "repro" / "stage94_local_frontier_audit"
OUT_MD = ROOT / "docs" / "stage94_local_frontier_audit_log.md"

STAGE69 = ROOT / "repro" / "stage69_local_variant_feasibility.csv"
STAGE81 = ROOT / "repro" / "stage81_next_variant_triage.csv"
STAGE82_DECISION = ROOT / "repro" / "stage82_post_h11_profile" / "decision.csv"
STAGE82_PROFILE = ROOT / "repro" / "stage82_post_h11_profile" / "profile_metrics.csv"
STAGE84 = ROOT / "repro" / "stage84_h13_r6_tile_sweep_preflight" / "summary.csv"
STAGE86 = ROOT / "repro" / "stage86_secondary_cmux_materialization" / "candidates.csv"
STAGE89 = ROOT / "repro" / "stage89_h14_promotion_policy_integration" / "summary.csv"
STAGE91 = ROOT / "repro" / "stage91_final_package" / "summary.csv"
STAGE91_CLAIMS = ROOT / "repro" / "stage91_final_package" / "claim_boundary.csv"
STAGE93 = ROOT / "repro" / "stage93_external_lane_attempt" / "summary.csv"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def by_key(path: Path, key: str) -> Dict[str, Dict[str, str]]:
    return {row.get(key, ""): row for row in read_csv(path)}


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fieldnames: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def row(gate: str, status: str, evidence: str, detail: str, next_action: str) -> Dict[str, str]:
    return {
        "gate": gate,
        "status": status,
        "evidence": evidence,
        "detail": detail,
        "next_action": next_action,
    }


def status_of(rows: Dict[str, Dict[str, str]], key: str) -> str:
    return rows.get(key, {}).get("status", "MISSING")


def git_source_changes_after_stage89() -> List[str]:
    cmd = [
        "git",
        "diff",
        "--name-only",
        "8422cf5..HEAD",
        "--",
        "main.c",
        "include",
        "src",
        "src/mosfhet/include",
        "src/mosfhet/src",
    ]
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        return [f"git_diff_failed:{proc.stderr.strip() or proc.returncode}"]
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def profile_numbers() -> Dict[str, float]:
    rows = read_csv(STAGE82_PROFILE)
    if not rows:
        return {}
    first = rows[0]
    numbers = {}
    for key in [
        "mat_ep_share_of_full",
        "from_dft_share_of_full",
        "cmux_add_share_of_full",
        "cmux_sub_share_of_full",
        "ncmux_share_of_full",
        "sub_a_share_of_full",
        "non_mat_share_of_full",
    ]:
        try:
            numbers[key] = float(first.get(key, "nan"))
        except ValueError:
            pass
    return numbers


def build_candidate_rows() -> List[Dict[str, str]]:
    stage69 = by_key(STAGE69, "gate")
    stage81 = by_key(STAGE81, "gate")
    stage84 = by_key(STAGE84, "gate")
    stage86 = by_key(STAGE86, "candidate_id")
    stage89 = by_key(STAGE89, "gate")
    profile = profile_numbers()
    sub_share = profile.get("cmux_sub_share_of_full", 0.0)
    half_sub_ceiling = 1.0 / (1.0 - 0.5 * sub_share) if sub_share < 2.0 else 0.0
    tail_status = status_of(stage81, "stage81_postprocessing_candidate")
    h13_status = status_of(stage84, "stage84_full_sab_smoke")
    h14_decision = status_of(stage89, "stage89_decision")
    c3_status = stage86.get("H14-C3-dual-butterfly-shared-input-wrapper", {}).get("status", "MISSING")
    return [
        {
            "candidate_id": "H14-C1-backend-from-dft-add",
            "current_status": "PROMOTED_EXPLICIT_R6_PREFERRED" if h14_decision == "PASS_STAGE89_H14_BACKEND_PROMOTE_EXPLICIT_PATH_NOT_DEFAULT" else "MISSING_PROMOTION",
            "evidence": rel(STAGE89),
            "local_impact_bound": "observed_backend_vs_wrapper_mean=1.035516; backend_vs_scalar_mean=1.437",
            "risk": "explicit flag only; default path unchanged",
            "stage94_decision": "KEEP_PREFERRED_EXPLICIT_NO_DEFAULT_CHANGE",
            "next_action": "Use as the preferred explicit r=6 local engineering path; do not upgrade paper/default claims.",
        },
        {
            "candidate_id": "H14-C3-dual-butterfly-shared-input-wrapper",
            "current_status": c3_status,
            "evidence": f"{rel(STAGE86)}; {rel(STAGE82_PROFILE)}",
            "local_impact_bound": f"sub_share={sub_share:.6f}; half_sub_body_ceiling={half_sub_ceiling:.6f}",
            "risk": "irregular butterfly pairing and NCMUX automorphism complexity",
            "stage94_decision": "DEFER_LOW_AMDAHL_AFTER_C1_SUCCESS",
            "next_action": "Reopen only if a future profile raises sub share or H14-C1 regresses.",
        },
        {
            "candidate_id": "H13-r6-full-output-tile-sweep",
            "current_status": status_of(stage84, "stage84_decision"),
            "evidence": rel(STAGE84),
            "local_impact_bound": f"full_sab_status={h13_status}",
            "risk": "kernel-positive but complete-SAB neutral or negative",
            "stage94_decision": "REJECT_NO_PROMOTION",
            "next_action": "Do not spend another implementation pass without a new profile-backed mechanism.",
        },
        {
            "candidate_id": "H2-postprocessing-pvw-tail",
            "current_status": tail_status,
            "evidence": f"{rel(STAGE81)}; repro/stage24_postproc_tail_avx512_runs1/summary.csv",
            "local_impact_bound": "stage81_tail_max_pct=1.261195; threshold_pct=2.000000",
            "risk": "tail is too small to justify direct PVW packing/HW-KS complexity",
            "stage94_decision": "DEFER_TAIL_SMALL",
            "next_action": "Reopen only after a body optimization makes tail cost material.",
        },
        {
            "candidate_id": "H3-sparse-selector-shortcut",
            "current_status": status_of(stage69, "stage69_h3_sparse_selector_theory"),
            "evidence": rel(STAGE69),
            "local_impact_bound": "no safe complexity reduction under encrypted dense selector rows",
            "risk": "key-format and secret-dependent metadata risk",
            "stage94_decision": "REJECT_SECURITY_KEY_FORMAT_RISK",
            "next_action": "Require a new key-format/security design before any code.",
        },
        {
            "candidate_id": "H7-avx512-layout-after-stage65",
            "current_status": status_of(stage69, "stage69_h7_avx512_layout"),
            "evidence": rel(STAGE69),
            "local_impact_bound": "Stage65A row-unrolled r=4 was negative; native counters still missing",
            "risk": "blind register/layout work without hardware counters",
            "stage94_decision": "BLOCKED_NATIVE_COUNTERS_OR_NEW_ISOLATED_HYPOTHESIS_REQUIRED",
            "next_action": "Run native perf or propose a distinct falsifiable layout hypothesis.",
        },
        {
            "candidate_id": "H8-nonbinary-pvw-sab",
            "current_status": status_of(stage69, "stage69_h8_nonbinary_branch"),
            "evidence": rel(STAGE69),
            "local_impact_bound": "current PVW target harness is binary-only",
            "risk": "requires 2025/686 full-text branch semantics and new staged correctness plan",
            "stage94_decision": "BLOCKED_FULLTEXT_AND_DESIGN",
            "next_action": "Supply reviewed 2025/686 full text before non-binary PVW-SAB design work.",
        },
    ]


def build_summary(out_dir: Path, candidates: List[Dict[str, str]]) -> List[Dict[str, str]]:
    stage69 = by_key(STAGE69, "gate")
    stage82 = by_key(STAGE82_DECISION, "gate")
    stage84 = by_key(STAGE84, "gate")
    stage89 = by_key(STAGE89, "gate")
    stage91 = by_key(STAGE91, "gate")
    stage91_claims = by_key(STAGE91_CLAIMS, "claim_id")
    stage93 = by_key(STAGE93, "gate")
    source_changes = git_source_changes_after_stage89()

    expected_inputs = {
        "stage69_decision": status_of(stage69, "stage69_decision"),
        "stage82_decision": status_of(stage82, "stage82_decision"),
        "stage84_decision": status_of(stage84, "stage84_decision"),
        "stage89_decision": status_of(stage89, "stage89_decision"),
        "stage91_decision": status_of(stage91, "stage91_decision"),
        "stage93_decision": status_of(stage93, "stage93_decision"),
    }
    expected_ok = {
        "stage69_decision": "PASS_LOCAL_VARIANT_FEASIBILITY_AUDIT_STRONGER_CLAIMS_BLOCKED",
        "stage82_decision": "PASS_STAGE82_POST_H11_PROFILE_MAT_BODY_PRIMARY",
        "stage84_decision": "PASS_STAGE84_H13_R6_TILE_SWEEP_KERNEL_ONLY_NOT_PROMOTED",
        "stage89_decision": "PASS_STAGE89_H14_BACKEND_PROMOTE_EXPLICIT_PATH_NOT_DEFAULT",
        "stage91_decision": "PASS_STAGE91_FINAL_SCOPED_PACKAGE_STRONGER_CLAIMS_BLOCKED",
        "stage93_decision": "PASS_STAGE93_EXTERNAL_LANE_ATTEMPT_RECORDED_STRONGER_CLAIMS_BLOCKED",
    }
    mismatches = [
        f"{key}={got}" for key, got in expected_inputs.items()
        if got != expected_ok[key]
    ]
    promoted_ok = expected_inputs["stage89_decision"] == expected_ok["stage89_decision"]
    no_new_hotpath = not source_changes
    claim_statuses = [
        stage91_claims.get("C3", {}).get("status", "MISSING"),
        stage91_claims.get("C4", {}).get("status", "MISSING"),
        stage91_claims.get("C5", {}).get("status", "MISSING"),
    ]
    claims_blocked = all("BLOCKED" in item or "MISSING_OPTIONAL" in item for item in claim_statuses)
    actionable = [
        c for c in candidates
        if c["stage94_decision"].startswith("PROMOTE")
        or c["stage94_decision"].startswith("IMPLEMENT")
    ]
    local_closed = len(actionable) == 0

    rows = [
        row(
            "stage94_inputs_available",
            "PASS" if not mismatches else "FAIL_INPUTS",
            "; ".join(rel(p) for p in [STAGE69, STAGE82_DECISION, STAGE84, STAGE89, STAGE91, STAGE93]),
            "all required prior-stage decisions match expected scoped statuses"
            if not mismatches else "; ".join(mismatches),
            "Restore or rerun the missing prior stage before relying on Stage94.",
        ),
        row(
            "stage94_preferred_path_guard",
            "PASS_H14_C1_EXPLICIT_PATH_PREFERRED" if promoted_ok else "FAIL_PREFERRED_PATH",
            rel(STAGE89),
            "H14-C1 backend FromDFT-add remains the preferred explicit r=6 path"
            if promoted_ok else f"stage89_decision={expected_inputs['stage89_decision']}",
            "Rerun Stage89 before changing the preferred explicit path.",
        ),
        row(
            "stage94_no_new_hotpath_guard",
            "PASS_NO_SAB_SOURCE_CHANGES_AFTER_STAGE89" if no_new_hotpath else "FAIL_SOURCE_CHANGED",
            "git diff --name-only 8422cf5..HEAD -- main.c include src",
            "no SAB source changes after Stage89 policy anchor"
            if no_new_hotpath else "; ".join(source_changes),
            "Rerun current-head smoke and performance gates if SAB source changes.",
        ),
        row(
            "stage94_candidate_frontier",
            "PASS_NO_UNBLOCKED_LOCAL_HOTPATH_CANDIDATE" if local_closed else "FAIL_ACTIONABLE_CANDIDATE_EXISTS",
            rel(out_dir / "candidates.csv"),
            "remaining candidates are keep/defer/reject/external-blocked under current evidence"
            if local_closed else "; ".join(c["candidate_id"] for c in actionable),
            "Open a new code stage only for a candidate with a falsifiable gate and material expected gain.",
        ),
        row(
            "stage94_claim_guard",
            "PASS_STRONGER_CLAIMS_BLOCKED" if claims_blocked else "FAIL_CLAIM_GUARD",
            rel(STAGE91_CLAIMS),
            "C3/C4/C5 remain blocked or missing-optional under Stage91 claim boundary"
            if claims_blocked else f"claim_statuses={claim_statuses}",
            "Do not change claim wording before external full-text/perf/novelty gates pass.",
        ),
    ]
    decision_ok = all(r["status"].startswith("PASS") for r in rows)
    rows.append(
        row(
            "stage94_decision",
            "PASS_STAGE94_LOCAL_FRONTIER_AUDIT_NO_NEW_HOTPATH"
            if decision_ok else "FAIL_STAGE94_LOCAL_FRONTIER_AUDIT",
            rel(out_dir / "summary.csv"),
            "No additional local hot-path implementation is justified under current evidence; keep H14-C1 explicit and preserve stronger-claim blockers."
            if decision_ok else "Fix failed Stage94 gates before using the frontier audit.",
            "Continue via external unlock lanes or introduce a new falsifiable hypothesis if new evidence appears.",
        )
    )
    return rows


def artifact_rows(out_dir: Path) -> List[Dict[str, str]]:
    return [
        {"artifact": rel(out_dir / "summary.csv"), "purpose": "Stage94 gate summary", "producer": "scripts/build_stage94_local_frontier_audit.py"},
        {"artifact": rel(out_dir / "candidates.csv"), "purpose": "Remaining local candidate frontier", "producer": "scripts/build_stage94_local_frontier_audit.py"},
        {"artifact": rel(out_dir / "artifact_index.csv"), "purpose": "Stage94 artifact index", "producer": "scripts/build_stage94_local_frontier_audit.py"},
        {"artifact": rel(OUT_MD), "purpose": "Human-readable Stage94 log", "producer": "scripts/build_stage94_local_frontier_audit.py"},
    ]


def esc(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def write_md(out_dir: Path, summary: List[Dict[str, str]], candidates: List[Dict[str, str]]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    decision = summary[-1]
    lines = [
        "# Stage94 Local Frontier Audit Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Decision",
        "",
        f"`{decision['status']}`",
        "",
        decision["detail"],
        "",
        "Stage94 does not add a new hot-path implementation. It records that",
        "H14-C1 remains the preferred explicit r=6 local engineering path and",
        "that the remaining local candidates are deferred, rejected, or blocked",
        "under current evidence.",
        "",
        "## Gates",
        "",
        "| gate | status | evidence | detail | next action |",
        "|---|---|---|---|---|",
    ]
    for item in summary:
        lines.append(
            f"| {item['gate']} | {item['status']} | {esc(item['evidence'])} | {esc(item['detail'])} | {esc(item['next_action'])} |"
        )
    lines.extend([
        "",
        "## Candidate Frontier",
        "",
        "| candidate | status | bound | Stage94 decision |",
        "|---|---|---|---|",
    ])
    for item in candidates:
        lines.append(
            f"| {item['candidate_id']} | {esc(item['current_status'])} | {esc(item['local_impact_bound'])} | {esc(item['stage94_decision'])} |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    candidates = build_candidate_rows()
    summary = build_summary(out_dir, candidates)
    index = artifact_rows(out_dir)
    write_csv(out_dir / "candidates.csv", candidates, [
        "candidate_id",
        "current_status",
        "evidence",
        "local_impact_bound",
        "risk",
        "stage94_decision",
        "next_action",
    ])
    write_csv(out_dir / "summary.csv", summary, [
        "gate",
        "status",
        "evidence",
        "detail",
        "next_action",
    ])
    write_csv(out_dir / "artifact_index.csv", index, ["artifact", "purpose", "producer"])
    write_md(out_dir, summary, candidates)
    decision = summary[-1]["status"]
    print(f"Wrote {rel(out_dir / 'summary.csv')}")
    print(f"Wrote {rel(out_dir / 'candidates.csv')}")
    print(f"Wrote {rel(OUT_MD)}")
    print(f"Stage94 local frontier audit: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
