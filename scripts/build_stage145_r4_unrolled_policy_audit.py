#!/usr/bin/env python3
"""Build Stage145 r4-unrolled promotion-policy audit."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
STAGE144 = ROOT / "repro" / "stage144_full_sab_repeated_r4_unrolled_gate"
OUT_DIR = ROOT / "repro" / "stage145_r4_unrolled_policy_audit"

SUMMARY_CSV = OUT_DIR / "summary.csv"
POLICY_CSV = OUT_DIR / "policy.csv"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage145_r4_unrolled_policy_audit.md"
PLAN_MD = ROOT / "experiments" / "stage145_r4_unrolled_policy_audit_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage145_policy_boundary.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"
GLOBAL_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
CHECKLIST_MD = ROOT / "repro" / "reproduction_checklist.md"

SUMMARY_FIELDS = ["gate", "status", "metric", "value", "evidence", "detail", "next_action"]
POLICY_FIELDS = [
    "input_stage", "stage144_perf_status", "stage144_noise_status",
    "stage144_resource_status", "mean_speedup", "min_speedup", "ci95_low",
    "ci95_high", "default_path_policy", "claim_policy",
    "next_research_action", "decision",
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
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
    write_text_lf(path, text + block.strip() + "\n")


def status_by_gate(rows: List[Dict[str, str]], gate: str) -> str:
    for row in rows:
        if row.get("gate") == gate:
            return row.get("status", "")
    return "MISSING"


def build_policy() -> tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    s144_summary = read_csv(STAGE144 / "summary.csv")
    perf = read_csv(STAGE144 / "perf_comparison.csv")[0]
    perf_status = status_by_gate(s144_summary, "stage144_perf")
    noise_status = status_by_gate(s144_summary, "stage144_noise")
    resource_status = status_by_gate(s144_summary, "stage144_resource")

    strong_perf = perf_status.startswith("PASS_STAGE144_PERF")
    weak_perf = perf_status.startswith("WEAK_STAGE144_PERF")
    noise_ok = noise_status == "PASS"
    resource_ok = resource_status == "PASS"

    if strong_perf and noise_ok and resource_ok:
        decision = "PASS_STAGE145_POLICY_PROMOTE_EXPLICIT_R4_UNROLLED_CANDIDATE"
        default_policy = "KEEP_DEFAULT_UNCHANGED_EXPLICIT_FLAG_ALLOWED"
        claim_policy = "ALLOW_SCOPED_ENGINEERING_CANDIDATE_CLAIM"
        next_action = "Run higher-stat final package before any default change."
    elif weak_perf and noise_ok and resource_ok:
        decision = "WEAK_STAGE145_POLICY_KEEP_EXPLICIT_DO_NOT_PROMOTE"
        default_policy = "KEEP_DEFAULT_UNCHANGED_EXPLICIT_EXPERIMENT_ONLY"
        claim_policy = "DISALLOW_FINAL_SPEEDUP_CLAIM_ALLOW_NEGATIVE_ABLATION"
        next_action = "Stage146 should attribute variance or route to another algorithmic candidate."
    else:
        decision = "FAIL_STAGE145_POLICY_REJECT_OR_REPAIR_REQUIRED"
        default_policy = "KEEP_DEFAULT_UNCHANGED"
        claim_policy = "DISALLOW_SPEEDUP_CLAIM"
        next_action = "Repair failed gate before any further promotion discussion."

    policy = [{
        "input_stage": "Stage144",
        "stage144_perf_status": perf_status,
        "stage144_noise_status": noise_status,
        "stage144_resource_status": resource_status,
        "mean_speedup": perf["r4_vs_generic_mean_speedup"],
        "min_speedup": perf["r4_vs_generic_min_speedup"],
        "ci95_low": perf["r4_vs_generic_ci95_low"],
        "ci95_high": perf["r4_vs_generic_ci95_high"],
        "default_path_policy": default_policy,
        "claim_policy": claim_policy,
        "next_research_action": next_action,
        "decision": decision,
    }]
    summary = [
        {"gate": "stage145_precondition", "status": "PASS" if s144_summary and perf else "FAIL", "metric": "stage144_inputs", "value": "summary;perf", "evidence": f"{rel(STAGE144 / 'summary.csv')}; {rel(STAGE144 / 'perf_comparison.csv')}", "detail": "Stage145 reads Stage144 gate outputs.", "next_action": ""},
        {"gate": "stage145_default_guard", "status": "PASS", "metric": "default_policy", "value": default_policy, "evidence": rel(POLICY_CSV), "detail": "No default/scalar path change is authorized.", "next_action": ""},
        {"gate": "stage145_claim_guard", "status": decision, "metric": "claim_policy", "value": claim_policy, "evidence": rel(POLICY_CSV), "detail": "Promotion wording follows Stage144 evidence strength.", "next_action": next_action},
    ]
    return summary, policy


def write_docs(summary: List[Dict[str, str]], policy: List[Dict[str, str]]) -> None:
    decision = policy[0]["decision"]
    write_text_lf(PLAN_MD, "\n".join([
        "# Stage145 r4-Unrolled Policy Audit Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Translate Stage144 repeated/noise/resource evidence into an explicit promotion policy without rerunning benchmarks.",
        "",
        "## Rule",
        "",
        "Only a Stage144 performance PASS plus noise/resource PASS can become a promotion candidate. A WEAK performance gate stays explicit-only and cannot support final speedup wording.",
    ]) + "\n")
    write_text_lf(THEORY_MD, "\n".join([
        "# Stage145 Policy Boundary",
        "",
        "Date: 2026-07-03",
        "",
        "A kernel-level improvement or a positive one-run complete-SAB smoke is insufficient for a final bootstrapping acceleration claim. The policy boundary is the repeated complete-SAB endpoint `T_bootstrap/r`, plus noise and resource gates.",
        "",
        "Stage145 does not change the algorithm. It prevents overclaiming when the repeated evidence is weak or negative.",
    ]) + "\n")
    write_text_lf(OUT_MD, "\n".join([
        "# Stage145 r4-Unrolled Policy Audit",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{decision}`",
        "",
        "## Gates",
        "",
        table(summary, ["gate", "status", "metric", "value", "detail"]),
        "",
        "## Policy",
        "",
        table(policy, POLICY_FIELDS),
        "",
        "## Interpretation",
        "",
        "The r4-unrolled AVX512 path remains useful as an ablation and variance target, but Stage144 does not justify default promotion or final SAB speedup wording.",
    ]) + "\n")


def update_longform(summary: List[Dict[str, str]], policy: List[Dict[str, str]]) -> None:
    row = policy[0]
    block = f"""
## Stage 145: r4-Unrolled Promotion-Policy Audit

Goal:

```text
Convert Stage144 evidence into an explicit keep/promote/reject policy without
overstating the full-SAB result.
```

Status:

```text
Completed. Stage145 records {row['decision']}. Default behavior remains
unchanged. Claim policy is {row['claim_policy']}. Next action:
{row['next_research_action']}
```
"""
    append_once(ROADMAP_MD, "## Stage 145: r4-Unrolled Promotion-Policy Audit", block)
    append_once(GOAL_MD, "Stage145 records the r4-unrolled promotion boundary", f"""
Stage145 records the r4-unrolled promotion boundary: Stage144 repeated
performance is weak, although noise/resource pass. Therefore r4-unrolled stays
explicit-only and cannot be used as a final complete-SAB acceleration claim.
""")
    append_once(CURRENT_GOAL_MD, "49. Treat Stage145 as the r4-unrolled promotion-policy audit", f"""
49. Treat Stage145 as the r4-unrolled promotion-policy audit:
    `{row['decision']}`. The explicit r4-unrolled path is retained only for
    ablation/variance analysis; it is not promoted to default or final claim.
""")


def upsert_hypothesis(policy: List[Dict[str, str]]) -> None:
    row = policy[0]
    block = f"""  - id: H69_r4_unrolled_policy_boundary
    statement: >
      r4-unrolled AVX512 should not be promoted beyond an explicit experimental
      path unless repeated complete-SAB T_bootstrap/r evidence is statistically
      stable and noise/resource gates pass.
    mechanism: >
      Stage144 shows noise/resource pass, but performance is weak with CI
      crossing one, so Stage145 prevents kernel/smoke gains from being
      overclaimed as final bootstrapping acceleration.
    status: stage145_r4_unrolled_policy_audit
    evidence: docs/stage145_r4_unrolled_policy_audit.md; experiments/stage145_r4_unrolled_policy_audit_plan.md; theory_checks/stage145_policy_boundary.md; scripts/build_stage145_r4_unrolled_policy_audit.py; repro/stage145_r4_unrolled_policy_audit/summary.csv; repro/stage145_r4_unrolled_policy_audit/policy.csv
    current_decision: >
      Stage145 records {row['decision']}. Default policy is
      {row['default_path_policy']}; claim policy is {row['claim_policy']}.
    failure_criteria:
      - default path changes without a PASS repeated full-SAB gate
      - weak full-SAB evidence is written as a final speedup claim
"""
    text = HYPOTHESIS_YAML.read_text(encoding="utf-8") if HYPOTHESIS_YAML.exists() else "hypotheses:\n"
    marker = "  - id: H69_r4_unrolled_policy_boundary"
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n"
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(HYPOTHESIS_YAML, text + block)


def upsert_run_log(policy: List[Dict[str, str]]) -> None:
    fields = ["run_id", "date", "commit_or_state", "stage", "backend", "command", "params", "seed", "status", "summary", "artifacts"]
    run_id = "stage145-r4-unrolled-policy-audit-001"
    rows = [row for row in read_csv(RUN_LOG) if row.get("run_id") != run_id]
    artifacts = stage_artifacts()
    rows.append({
        "run_id": run_id,
        "date": "2026-07-03",
        "commit_or_state": f"working-tree-after-{git_head()}",
        "stage": "Stage 145",
        "backend": "n/a policy audit",
        "command": "python scripts/build_stage145_r4_unrolled_policy_audit.py",
        "params": "reads Stage144 summary/perf/noise/resource decisions",
        "seed": "n/a",
        "status": policy[0]["decision"],
        "summary": "Policy audit keeps r4-unrolled explicit-only when Stage144 repeated performance is weak.",
        "artifacts": "; ".join(rel(p) for p in artifacts),
    })
    write_csv(RUN_LOG, rows, fields)


def upsert_manifest() -> None:
    append_once(GLOBAL_MANIFEST, "## Stage 145 r4-Unrolled Policy Audit", """
## Stage 145 r4-Unrolled Policy Audit

- `docs/stage145_r4_unrolled_policy_audit.md`
- `experiments/stage145_r4_unrolled_policy_audit_plan.md`
- `theory_checks/stage145_policy_boundary.md`
- `scripts/build_stage145_r4_unrolled_policy_audit.py`
- `repro/stage145_r4_unrolled_policy_audit/summary.csv`
- `repro/stage145_r4_unrolled_policy_audit/policy.csv`
- `repro/stage145_r4_unrolled_policy_audit/artifact_index.csv`
""")


def update_checklist(policy: List[Dict[str, str]]) -> None:
    text = CHECKLIST_MD.read_text(encoding="utf-8") if CHECKLIST_MD.exists() else ""
    line = f"- [x] Run Stage145 r4-unrolled promotion-policy audit; decision `{policy[0]['decision']}` keeps the path explicit-only unless future repeated evidence becomes stable."
    if line not in text:
        if text and not text.endswith("\n"):
            text += "\n"
        text += line + "\n"
    write_text_lf(CHECKLIST_MD, text)


def stage_artifacts() -> List[Path]:
    return [OUT_MD, PLAN_MD, THEORY_MD, SUMMARY_CSV, POLICY_CSV, ARTIFACT_INDEX, Path(__file__).resolve()]


def write_artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        if path == ARTIFACT_INDEX:
            rows.append({"artifact": rel(path), "exists": "self", "sha256": "", "size_bytes": ""})
            continue
        rows.append({
            "artifact": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path) if path.exists() else "",
            "size_bytes": str(path.stat().st_size) if path.exists() else "0",
        })
    write_csv(ARTIFACT_INDEX, rows, ["artifact", "exists", "sha256", "size_bytes"])


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary, policy = build_policy()
    write_csv(SUMMARY_CSV, summary, SUMMARY_FIELDS)
    write_csv(POLICY_CSV, policy, POLICY_FIELDS)
    write_docs(summary, policy)
    update_longform(summary, policy)
    upsert_hypothesis(policy)
    upsert_run_log(policy)
    upsert_manifest()
    update_checklist(policy)
    write_artifact_index(stage_artifacts())
    print(f"Stage145 r4-unrolled policy audit: {policy[0]['decision']}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
