#!/usr/bin/env python3
"""Build Stage149 H14 r=6 claim-boundary and promotion-policy audit."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage149_h14_r6_claim_policy"
STAGE148 = ROOT / "repro" / "stage148_h14_r6_repeated_refresh"
MAKEFILE_DEF = ROOT / "src" / "mosfhet" / "Makefile.def"

SUMMARY_CSV = OUT_DIR / "summary.csv"
POLICY_CSV = OUT_DIR / "claim_policy.csv"
DEFAULT_GUARD_CSV = OUT_DIR / "default_guard.csv"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage149_h14_r6_claim_policy.md"
PLAN_MD = ROOT / "experiments" / "stage149_h14_r6_claim_policy_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage149_claim_boundary_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_h14_r6_claim_boundary.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"
GLOBAL_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
CHECKLIST_MD = ROOT / "repro" / "reproduction_checklist.md"

SUMMARY_FIELDS = ["gate", "status", "metric", "value", "evidence", "detail", "next_action"]
POLICY_FIELDS = [
    "input_stage", "stage148_decision", "perf_status", "noise_status",
    "resource_status", "backend_vs_wrapper_mean", "backend_vs_wrapper_min",
    "backend_vs_wrapper_ci95_low", "backend_vs_scalar_mean",
    "key_bytes_ratio", "vmhwm_ratio", "default_path_policy",
    "engineering_claim_policy", "paper_novelty_policy",
    "next_action", "decision",
]
DEFAULT_FIELDS = ["flag", "expected_default", "observed_line", "status", "evidence"]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(row.get(field, "") for field in fields) + " |")
    return "\n".join(out)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def append_once(path: Path, heading: str, block: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if heading in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(path, text + block.strip("\n") + "\n")


def status_by_gate(rows: List[Dict[str, str]], gate: str) -> str:
    for row in rows:
        if row.get("gate") == gate:
            return row.get("status", "")
    return "MISSING"


def value_by_gate(rows: List[Dict[str, str]], gate: str) -> str:
    for row in rows:
        if row.get("gate") == gate:
            return row.get("value", "")
    return ""


def default_guard_rows() -> List[Dict[str, str]]:
    text = MAKEFILE_DEF.read_text(encoding="utf-8", errors="replace")
    flags = [
        "SAB_PVW_BACKEND_FROM_DFT_ADD",
        "MAT_TRGSW_AVX512_RGT4_FUSED",
        "SAB_PVW_ACTIVE_BUFFER_FUSION",
    ]
    rows = []
    for flag in flags:
        observed = ""
        for line in text.splitlines():
            if line.startswith(f"{flag} ?="):
                observed = line.strip()
                break
        rows.append({
            "flag": flag,
            "expected_default": "false",
            "observed_line": observed,
            "status": "PASS" if observed == f"{flag} ?= false" else "FAIL",
            "evidence": rel(MAKEFILE_DEF),
        })
    return rows


def build_policy() -> tuple[List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]]]:
    stage148_summary = read_csv(STAGE148 / "summary.csv")
    perf = read_csv(STAGE148 / "perf_comparison.csv")
    resource = read_csv(STAGE148 / "resource_comparison.csv")
    defaults = default_guard_rows()

    stage148_decision = status_by_gate(stage148_summary, "stage148_decision")
    perf_status = status_by_gate(stage148_summary, "stage148_perf")
    noise_status = status_by_gate(stage148_summary, "stage148_noise")
    resource_status = status_by_gate(stage148_summary, "stage148_resource")
    defaults_ok = all(row["status"] == "PASS" for row in defaults)
    perf_row = perf[0] if perf else {}
    resource_row = resource[0] if resource else {}

    stage148_ok = stage148_decision == "PASS_STAGE148_H14_R6_REPEATED_REFRESH_PROMOTION_CANDIDATE"
    perf_ok = perf_status == "PASS_STAGE148_PERF_BACKEND_REPEATED_POSITIVE"
    noise_ok = noise_status == "PASS"
    resource_ok = resource_status == "PASS"

    if stage148_ok and perf_ok and noise_ok and resource_ok and defaults_ok:
        decision = "PASS_STAGE149_H14_R6_EXPLICIT_PROMOTION_POLICY_RECORDED_NOT_DEFAULT"
        default_policy = "KEEP_DEFAULT_UNCHANGED_EXPLICIT_FLAG_ONLY"
        engineering_policy = "ALLOW_SCOPED_EXPLICIT_ENGINEERING_CLAIM"
        novelty_policy = "DISALLOW_PAPER_NOVELTY_OR_THEORETICAL_OPTIMALITY_CLAIM"
        next_action = "Stage150 should refresh the final package/report with explicit-path wording and open stronger-claim blockers."
    elif stage148_ok and perf_ok and noise_ok and resource_ok:
        decision = "WEAK_STAGE149_POLICY_DEFAULT_GUARD_REPAIR_REQUIRED"
        default_policy = "KEEP_DEFAULT_UNCHANGED_REPAIR_GUARD"
        engineering_policy = "DEFER_CLAIM_UNTIL_DEFAULT_GUARD_REPAIRED"
        novelty_policy = "DISALLOW_PAPER_NOVELTY_OR_THEORETICAL_OPTIMALITY_CLAIM"
        next_action = "Repair default guard before writing any promoted wording."
    else:
        decision = "FAIL_STAGE149_POLICY_NO_PROMOTION"
        default_policy = "KEEP_DEFAULT_UNCHANGED"
        engineering_policy = "DISALLOW_PROMOTION_CLAIM"
        novelty_policy = "DISALLOW_PAPER_NOVELTY_OR_THEORETICAL_OPTIMALITY_CLAIM"
        next_action = "Repair failed Stage148 gate before policy promotion."

    policy = [{
        "input_stage": "Stage148",
        "stage148_decision": stage148_decision,
        "perf_status": perf_status,
        "noise_status": noise_status,
        "resource_status": resource_status,
        "backend_vs_wrapper_mean": perf_row.get("backend_vs_wrapper_mean_speedup", ""),
        "backend_vs_wrapper_min": perf_row.get("backend_vs_wrapper_min_speedup", ""),
        "backend_vs_wrapper_ci95_low": perf_row.get("backend_vs_wrapper_ci95_low", ""),
        "backend_vs_scalar_mean": perf_row.get("backend_mean_speedup_vs_scalar", ""),
        "key_bytes_ratio": resource_row.get("key_bytes_ratio", ""),
        "vmhwm_ratio": resource_row.get("vmhwm_ratio", ""),
        "default_path_policy": default_policy,
        "engineering_claim_policy": engineering_policy,
        "paper_novelty_policy": novelty_policy,
        "next_action": next_action,
        "decision": decision,
    }]

    summary = [
        {
            "gate": "stage149_precondition",
            "status": "PASS" if stage148_ok else "FAIL",
            "metric": "stage148_decision",
            "value": stage148_decision,
            "evidence": rel(STAGE148 / "summary.csv"),
            "detail": "Stage149 requires Stage148 repeated/noise/resource promotion-candidate evidence.",
            "next_action": "",
        },
        {
            "gate": "stage149_stats_sanity",
            "status": "PASS" if perf_ok and noise_ok and resource_ok else "FAIL",
            "metric": "perf;noise;resource",
            "value": f"{perf_status};{noise_status};{resource_status}",
            "evidence": f"{rel(STAGE148 / 'perf_comparison.csv')}; {rel(STAGE148 / 'noise_aggregate.csv')}; {rel(STAGE148 / 'resource_comparison.csv')}",
            "detail": "Repeated T_bootstrap/r, final-output noise, and resource gates are all required for engineering-claim promotion.",
            "next_action": "",
        },
        {
            "gate": "stage149_default_guard",
            "status": "PASS" if defaults_ok else "FAIL",
            "metric": "explicit_flags_default_false",
            "value": "SAB_PVW_BACKEND_FROM_DFT_ADD;MAT_TRGSW_AVX512_RGT4_FUSED;SAB_PVW_ACTIVE_BUFFER_FUSION",
            "evidence": f"{rel(DEFAULT_GUARD_CSV)}; {rel(MAKEFILE_DEF)}",
            "detail": "Explicit H14 r=6 route remains behind opt-in flags.",
            "next_action": "Do not change defaults without a separate default-promotion gate.",
        },
        {
            "gate": "stage149_claim_boundary",
            "status": "PASS" if policy[0]["engineering_claim_policy"] == "ALLOW_SCOPED_EXPLICIT_ENGINEERING_CLAIM" else "FAIL",
            "metric": "engineering_claim_policy",
            "value": policy[0]["engineering_claim_policy"],
            "evidence": rel(POLICY_CSV),
            "detail": "Allowed wording is scoped to current-head explicit-path engineering performance.",
            "next_action": "",
        },
        {
            "gate": "stage149_decision",
            "status": decision,
            "metric": "policy",
            "value": "not_default_not_paper_novelty",
            "evidence": rel(POLICY_CSV),
            "detail": "Stage149 records claim/promotion policy and does not modify code or defaults.",
            "next_action": next_action,
        },
    ]
    return summary, policy, defaults


def write_docs(summary: List[Dict[str, str]], policy: List[Dict[str, str]], defaults: List[Dict[str, str]]) -> None:
    decision = policy[0]["decision"]
    write_text_lf(PLAN_MD, "\n".join([
        "# Stage149 H14 r=6 Claim Policy Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Convert Stage148 repeated/noise/resource evidence into a bounded claim and promotion policy.",
        "",
        "## Rule",
        "",
        "Stage149 may allow a scoped explicit-path engineering claim only when repeated `T_bootstrap/r`, noise, resource, and default-guard checks pass. It cannot promote defaults or paper-level novelty.",
    ]) + "\n")
    write_text_lf(THEORY_MD, "\n".join([
        "# Stage149 Claim Boundary Model",
        "",
        "Date: 2026-07-03",
        "",
        "Stage148 proves a current-head explicit-path engineering result, not a new asymptotic lower bound. The claim boundary is:",
        "",
        "- allowed: explicit H14 r=6 backend FromDFT-add improves complete MAT-RLWE/SAB `T_bootstrap/r` under the recorded backend and parameter set;",
        "- allowed: resource/noise overheads are reported with the performance result;",
        "- disallowed: default-path speedup, universal theoretical optimality, or paper-level novelty without further source/literature and default-policy gates.",
    ]) + "\n")
    write_text_lf(VARIANT_MD, "\n".join([
        "# MAT-RLWE SAB H14 r=6 Claim Boundary",
        "",
        "Date: 2026-07-03",
        "",
        "The promoted object is an explicit H14 r=6 engineering path: r=6 MAT-RLWE/PVW lanes, active-buffer sparse schedule, r>4 fused MAT kernel, and backend FromDFT-add materialization.",
        "",
        "The path remains opt-in and does not replace scalar `sab_rlwe_bootstrap` or default `sab_pvw_*` behavior.",
    ]) + "\n")
    write_text_lf(OUT_MD, "\n".join([
        "# Stage149 H14 r=6 Claim Policy",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{decision}`",
        "",
        "## Summary Gates",
        "",
        table(summary, ["gate", "status", "metric", "value", "detail", "next_action"]),
        "",
        "## Policy",
        "",
        table(policy, POLICY_FIELDS),
        "",
        "## Default Guard",
        "",
        table(defaults, DEFAULT_FIELDS),
        "",
        "## Interpretation",
        "",
        "Stage149 permits a scoped explicit-path engineering claim for current-head H14 r=6 backend evidence. It does not permit default-path wording or paper-level novelty/optimality wording.",
    ]) + "\n")


def update_longform(summary: List[Dict[str, str]], policy: List[Dict[str, str]]) -> None:
    decision = policy[0]["decision"]
    block = f"""
## Stage 149: H14 r=6 Claim Policy

Goal:

```text
Convert Stage148 repeated/noise/resource evidence into a bounded claim policy
without changing defaults or overclaiming novelty.
```

Status:

```text
Completed. Stage149 records {decision}. It allows scoped explicit-path
engineering wording only; default-path and paper-level novelty claims remain
disallowed.
```
"""
    append_once(ROADMAP_MD, "## Stage 149: H14 r=6 Claim Policy", block)
    append_once(GOAL_MD, "Stage149 records H14 r=6 claim policy", f"""
Stage149 records H14 r=6 claim policy after Stage148 repeated/noise/resource
evidence. The allowed claim is scoped to the explicit backend route under the
recorded parameter/backend. Default-path and paper-level novelty/optimality
wording remain disallowed.
""")
    append_once(CURRENT_GOAL_MD, "Treat Stage149 as the H14 r=6 claim-policy gate", f"""
53. Treat Stage149 as the H14 r=6 claim-policy gate:
    `{decision}`. It permits only scoped explicit-path engineering wording and
    keeps default-path/paper-novelty claims blocked.
""")
    append_once(HYPOTHESIS_YAML, "H73_h14_r6_claim_policy", f"""
  - id: H73_h14_r6_claim_policy
    statement: >
      Stage148 evidence is sufficient to promote H14 r=6 backend as a scoped
      explicit engineering path, but insufficient to claim default-path speedup
      or paper-level novelty/optimality.
    mechanism: >
      Repeated T_bootstrap/r, final-output noise, resource reporting, and
      default false flag checks bound the allowed claim scope.
    status: stage149_h14_r6_claim_policy
    evidence: docs/stage149_h14_r6_claim_policy.md; experiments/stage149_h14_r6_claim_policy_plan.md; theory_checks/stage149_claim_boundary_model.md; scripts/build_stage149_h14_r6_claim_policy.py; repro/stage149_h14_r6_claim_policy/summary.csv; repro/stage149_h14_r6_claim_policy/claim_policy.csv
    current_decision: >
      {decision}
    failure_criteria:
      - explicit-path evidence is written as default-path speedup
      - engineering speedup is written as theoretical optimality or novelty
      - defaults change without a separate default-promotion gate
""")


def update_repro(policy: List[Dict[str, str]]) -> None:
    decision = policy[0]["decision"]
    existing = read_csv(RUN_LOG)
    run_fields = list(existing[0].keys()) if existing else [
        "run_id", "date", "commit_or_state", "stage", "backend", "command",
        "params", "seed", "status", "summary", "artifacts",
    ]
    base_row = {field: "" for field in run_fields}
    base_row.update({
        "run_id": "stage149-h14-r6-claim-policy-001",
        "date": "2026-07-03",
        "commit_or_state": git_head(),
        "stage": "Stage 149",
        "backend": "policy audit",
        "command": "python scripts/build_stage149_h14_r6_claim_policy.py",
        "params": "reads Stage148 perf/noise/resource and Makefile explicit-default guards",
        "seed": "n/a",
        "status": decision,
        "summary": "H14 r=6 explicit-path claim boundary and promotion policy audit.",
        "artifacts": rel(OUT_DIR),
    })
    run_row = {field: base_row.get(field, "") for field in run_fields}
    existing = [
        row for row in existing
        if row.get("run_id") != run_row["run_id"]
        and row.get("stage") != run_row["stage"]
    ]
    existing.append(run_row)
    write_csv(RUN_LOG, existing, run_fields)

    append_once(GLOBAL_MANIFEST, "stage149_h14_r6_claim_policy", f"""
- stage149_h14_r6_claim_policy: `{decision}`
  - `docs/stage149_h14_r6_claim_policy.md`
  - `experiments/stage149_h14_r6_claim_policy_plan.md`
  - `theory_checks/stage149_claim_boundary_model.md`
  - `repro/stage149_h14_r6_claim_policy/`
""")
    append_once(CHECKLIST_MD, "Stage149 H14 r=6 claim-policy pack", """
- [x] Stage149 H14 r=6 claim-policy pack recorded.
""")


def write_artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        if path == ARTIFACT_INDEX:
            rows.append({"artifact": rel(path), "exists": "self", "sha256": "", "size_bytes": ""})
        else:
            rows.append({
                "artifact": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256_file(path) if path.exists() else "",
                "size_bytes": str(path.stat().st_size) if path.exists() else "",
            })
    write_csv(ARTIFACT_INDEX, rows, ["artifact", "exists", "sha256", "size_bytes"])


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary, policy, defaults = build_policy()
    write_csv(SUMMARY_CSV, summary, SUMMARY_FIELDS)
    write_csv(POLICY_CSV, policy, POLICY_FIELDS)
    write_csv(DEFAULT_GUARD_CSV, defaults, DEFAULT_FIELDS)
    write_docs(summary, policy, defaults)
    update_longform(summary, policy)
    update_repro(policy)
    artifacts = [
        OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD,
        SUMMARY_CSV, POLICY_CSV, DEFAULT_GUARD_CSV,
        ARTIFACT_INDEX, Path(__file__).resolve(),
    ]
    write_artifact_index(artifacts)
    print(f"Stage149 H14 r=6 claim policy: {policy[0]['decision']}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if policy[0]["decision"].startswith(("PASS_", "WEAK_")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
