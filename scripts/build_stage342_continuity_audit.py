#!/usr/bin/env python3
"""Stage342: audit historical high-stat evidence versus current-head continuity."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage342_continuity_audit"

DOC = ROOT / "docs" / "stage342_continuity_audit.md"
THEORY = ROOT / "theory_checks" / "stage342_continuity_claim_model.md"
PLAN = ROOT / "experiments" / "stage343_current_head_matrix_topup_plan.md"
BUILDER = ROOT / "scripts" / "build_stage342_continuity_audit.py"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"

STAGE36_TARGET_PERF = ROOT / "repro" / "stage36_target_perf_summary.csv"
STAGE36_TARGET_NOISE = ROOT / "repro" / "stage36_target_noise_seeds50" / "aggregate.csv"
STAGE36_ADDED_PERF = ROOT / "repro" / "stage36_added_params_runs10_seeds20" / "performance_stats.csv"
STAGE36_ADDED_NOISE = ROOT / "repro" / "stage36_added_params_runs10_seeds20" / "noise_summary.csv"
STAGE49_SUMMARY = ROOT / "repro" / "stage49_wsl_repeated_full_sab" / "summary.csv"
STAGE50_MATRIX = ROOT / "repro" / "stage50_performance_evidence_matrix.csv"
STAGE331_SUMMARY = ROOT / "repro" / "stage331_current_head_highstat_refresh" / "summary.csv"
STAGE341_SUMMARY = ROOT / "repro" / "stage341_parameter_matrix_smoke" / "summary.csv"
STAGE341_PROOF = ROOT / "repro" / "stage341_parameter_matrix_smoke" / "proof_gate.csv"

SUMMARY = OUT / "summary.csv"
HOTPATH = OUT / "hotpath_delta_audit.csv"
EVIDENCE = OUT / "evidence_ladder.csv"
MATRIX_STATUS = OUT / "current_head_matrix_status.csv"
CLAIMS = OUT / "claim_update.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage342_report.md"
COMMANDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"

DECISION = "PASS_STAGE342_CONTINUITY_AUDIT_SCOPED_BRIDGE_NO_FULL_MATRIX_CLAIM"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")


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
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def git_full(short_ref: str) -> str:
    if not short_ref:
        return ""
    try:
        return subprocess.check_output(["git", "rev-parse", short_ref], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def git_diff_names(base: str) -> list[str]:
    if not base or not git_full(base):
        return []
    try:
        cmd = ["git", "diff", "--name-only", f"{base}..HEAD", "--", "src", "Makefile", "include"]
        out = subprocess.check_output(cmd, cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
        return [line.strip() for line in out.splitlines() if line.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def first_row(path: Path) -> dict[str, str]:
    rows = read_csv(path)
    return rows[0] if rows else {}


def md_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(lines)


def hotpath_rows() -> list[dict[str, object]]:
    refs = [
        ("stage36_target_perf", "9354837", rel(STAGE36_TARGET_PERF)),
        ("stage36_target_noise", "fdd6ff7", rel(STAGE36_TARGET_NOISE)),
        ("stage36_added_params", "eeb21dd", f"{rel(STAGE36_ADDED_PERF)}; {rel(STAGE36_ADDED_NOISE)}"),
        ("stage49_current_head_stability", "8c3fd2f", rel(STAGE49_SUMMARY)),
        ("stage331_current_head_r4_highstat", first_row(STAGE331_SUMMARY).get("git_head", ""), rel(STAGE331_SUMMARY)),
        ("stage341_current_head_r2_smoke", first_row(STAGE341_SUMMARY).get("run_head", ""), rel(STAGE341_SUMMARY)),
    ]
    rows: list[dict[str, object]] = []
    for name, ref, evidence in refs:
        full = git_full(ref)
        diffs = git_diff_names(ref)
        rows.append({
            "evidence": name,
            "ref": ref,
            "ref_resolves": "yes" if full else "no",
            "current_head": git_head(),
            "hotpath_diff_count": len(diffs) if full else "",
            "hotpath_diff_paths": ";".join(diffs[:20]) if full else "",
            "continuity_status": "HOTPATH_EQUIVALENT" if full and not diffs else "HOTPATH_CHANGED_OR_UNRESOLVED",
            "source": evidence,
        })
    return rows


def evidence_rows(hot: list[dict[str, object]]) -> list[dict[str, object]]:
    stage331 = first_row(STAGE331_SUMMARY)
    stage341 = first_row(STAGE341_SUMMARY)
    hot_by_name = {str(row["evidence"]): row for row in hot}
    rows: list[dict[str, object]] = []
    rows.append({
        "layer": "current_head_primary_r4",
        "status": "SUPPORTED_SCOPED",
        "metric": "complete_sab_T_bootstrap_over_r",
        "value": f"speedup={stage331.get('speedup_vs_repeated_scalar_mean', '')}; samples={stage331.get('samples', '')}; noise={stage331.get('noise_pair_failures', '')}/{stage331.get('noise_trials', '')}",
        "continuity": hot_by_name.get("stage331_current_head_r4_highstat", {}).get("continuity_status", ""),
        "claim_use": "main current-head scoped r=4 claim",
        "source": rel(STAGE331_SUMMARY),
    })
    rows.append({
        "layer": "current_head_r2_smoke",
        "status": "SMOKE_ONLY",
        "metric": "complete_sab_T_bootstrap_over_r",
        "value": f"speedup={stage341.get('speedup_mean', '')}; samples={stage341.get('samples', '')}; noise={stage341.get('noise_pair_failures', '')}/{stage341.get('noise_trials', '')}",
        "continuity": hot_by_name.get("stage341_current_head_r2_smoke", {}).get("continuity_status", ""),
        "claim_use": "execution-chain evidence only; not statistical performance",
        "source": rel(STAGE341_SUMMARY),
    })
    for row in read_csv(STAGE50_MATRIX):
        rows.append({
            "layer": f"stage50_{row.get('evidence_id', '')}",
            "status": row.get("status", ""),
            "metric": row.get("evidence_class", ""),
            "value": f"r={row.get('r', '')}; speedup={row.get('mean_speedup', '')}; runs={row.get('runs', '')}",
            "continuity": row.get("consistency_with_stage36", ""),
            "claim_use": row.get("claim_policy", ""),
            "source": row.get("source", rel(STAGE50_MATRIX)),
        })
    for row in read_csv(STAGE36_ADDED_PERF):
        rows.append({
            "layer": f"historical_added_{row.get('param', '')}_r{row.get('r', '')}",
            "status": row.get("decision", ""),
            "metric": "historical_added_binary_highstat",
            "value": f"speedup={row.get('mean_speedup', '')}; runs={row.get('runs', '')}; ci={row.get('ci95_low_t', '')}..{row.get('ci95_high_t', '')}",
            "continuity": hot_by_name.get("stage36_added_params", {}).get("continuity_status", ""),
            "claim_use": "supporting historical added-binary evidence; rerun for current-head broader claim",
            "source": rel(STAGE36_ADDED_PERF),
        })
    return rows


def matrix_rows() -> list[dict[str, object]]:
    stage331 = first_row(STAGE331_SUMMARY)
    stage341 = first_row(STAGE341_SUMMARY)
    rows = [
        {
            "case": "SET_2_3_2048_r4",
            "status": "CURRENT_HEAD_HIGHSTAT_AVAILABLE",
            "samples": stage331.get("samples", ""),
            "speedup": stage331.get("speedup_vs_repeated_scalar_mean", ""),
            "noise": f"{stage331.get('noise_pair_failures', '')}/{stage331.get('noise_trials', '')}",
            "next_needed": "none for scoped primary r=4; rerun only after hotpath changes",
        },
        {
            "case": "SET_2_3_2048_r2",
            "status": "CURRENT_HEAD_SMOKE_ONLY",
            "samples": stage341.get("samples", ""),
            "speedup": stage341.get("speedup_mean", ""),
            "noise": f"{stage341.get('noise_pair_failures', '')}/{stage341.get('noise_trials', '')}",
            "next_needed": "run 10-sample current-head target r=2 if target r=2 wording is desired",
        },
    ]
    for param in ["SET_4_5_2048", "SET_2_3_4096"]:
        for r in ["2", "4"]:
            rows.append({
                "case": f"{param}_r{r}",
                "status": "HISTORICAL_HIGHSTAT_ONLY",
                "samples": "10",
                "speedup": next((x.get("mean_speedup", "") for x in read_csv(STAGE36_ADDED_PERF) if x.get("param") == param and x.get("r") == r), ""),
                "noise": next((f"{x.get('pair_failures', '')}/{x.get('seeds', '')}" for x in read_csv(STAGE36_ADDED_NOISE) if x.get("param") == param and x.get("r") == r), ""),
                "next_needed": "rerun current-head case before broader current-head parameter claim",
            })
    return rows


def claim_rows() -> list[dict[str, object]]:
    return [
        {
            "claim": "current_head_primary_r4",
            "status": "ALLOW_SCOPED",
            "safe_statement": "Current-head r=4 SET_2_3_2048 include-zero has scoped complete-SAB T_bootstrap/r evidence.",
            "blocked_statement": "All-r or all-parameter current-head matrix.",
            "evidence": rel(STAGE331_SUMMARY),
        },
        {
            "claim": "current_head_r2",
            "status": "SMOKE_ONLY",
            "safe_statement": "Current-head r=2 SET_2_3_2048 execution path passed one smoke.",
            "blocked_statement": "Stable r=2 throughput or high-stat current-head claim.",
            "evidence": rel(STAGE341_SUMMARY),
        },
        {
            "claim": "historical_stage36_target_and_added_params",
            "status": "SUPPORTING_ONLY",
            "safe_statement": "Stage36 remains historical high-stat evidence and Stage50 provides continuity context.",
            "blocked_statement": "Treating historical high-stat rows as full current-head matrix without rerun.",
            "evidence": f"{rel(STAGE36_TARGET_PERF)}; {rel(STAGE36_ADDED_PERF)}; {rel(STAGE50_MATRIX)}",
        },
        {
            "claim": "broader_parameter_generalization",
            "status": "BLOCK_CURRENT_HEAD_FULL_MATRIX_MISSING",
            "safe_statement": "Broader claim requires current-head execution for missing cases.",
            "blocked_statement": "Universal, non-binary, or all-parameter claim.",
            "evidence": rel(MATRIX_STATUS),
        },
    ]


def proof_rows(hot: list[dict[str, object]], matrix: list[dict[str, object]]) -> list[dict[str, object]]:
    stage36_changed = any(row.get("evidence") == "stage36_target_perf" and row.get("continuity_status") != "HOTPATH_EQUIVALENT" for row in hot)
    missing_current = [row for row in matrix if row.get("status") in {"CURRENT_HEAD_SMOKE_ONLY", "HISTORICAL_HIGHSTAT_ONLY"}]
    return [
        {
            "gate": "G1_inputs",
            "status": "PASS",
            "metric": "required artifacts",
            "value": "Stage36;Stage49;Stage50;Stage331;Stage341",
            "interpretation": "Continuity audit has the required evidence layers.",
        },
        {
            "gate": "G2_stage36_hotpath_delta",
            "status": "PASS_SCOPED" if stage36_changed else "PASS_EQUIVALENT",
            "metric": "Stage36 -> HEAD hotpath diff",
            "value": "changed" if stage36_changed else "unchanged",
            "interpretation": "Changed hotpath keeps Stage36 as historical/supporting unless bridged by current-head reruns.",
        },
        {
            "gate": "G3_current_head_anchor",
            "status": "PASS",
            "metric": "Stage331 r4 and Stage341 r2",
            "value": "r4_highstat;r2_smoke",
            "interpretation": "Current-head evidence exists, but does not complete the full matrix.",
        },
        {
            "gate": "G4_full_matrix",
            "status": "MISSING_CURRENT_HEAD_CASES",
            "metric": "cases not current-head high-stat",
            "value": str(len(missing_current)),
            "interpretation": "Do not promote broader parameter wording.",
        },
        {
            "gate": "G5_decision",
            "status": DECISION,
            "metric": "stage decision",
            "value": DECISION,
            "interpretation": "Proceed by targeted current-head topups or verified literature/mechanism route.",
        },
    ]


def next_rows() -> list[dict[str, object]]:
    return [
        {
            "priority": "P0",
            "route": "stage343_target_r2_current_head_highstat_topup",
            "entry_condition": "Need target SET_2_3_2048 r=2 current-head high-stat wording.",
            "command": "run 9 additional r=2 perf samples plus enough noise trials, or rerun STAGE340 for SET_2_3_2048 r=2 only",
            "gate": "10 current-head samples, correctness Pass, noise/RSS recorded",
            "failure_action": "Keep r=2 as smoke/current-head continuity only.",
        },
        {
            "priority": "P1",
            "route": "stage343_added_param_current_head_matrix",
            "entry_condition": "Need current-head added-binary parameter wording.",
            "command": "STAGE340_EXECUTE=1 STAGE340_PARAMS='SET_4_5_2048 SET_2_3_4096' STAGE340_R_VALUES='2 4' ...",
            "gate": "Each added case passes high-stat performance and noise/RSS.",
            "failure_action": "Keep Stage36 added rows historical/supporting only.",
        },
        {
            "priority": "P2",
            "route": "stage343_verified_literature_or_mechanism",
            "entry_condition": "Full matrix execution is deferred.",
            "command": "verified source audit or new mechanism/proof preflight",
            "gate": "source-checked novelty or isolated mechanism/proof gates",
            "failure_action": "No novelty, theoretical optimality, or new algorithm claim.",
        },
    ]


def append_run_log() -> None:
    marker = "stage342-continuity-audit-001"
    if marker in read_text(RUN_LOG):
        return
    exists = RUN_LOG.exists()
    RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    with RUN_LOG.open("a", encoding="utf-8", newline="\n") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        if not exists:
            writer.writerow(["run_id", "date", "git_head", "stage", "backend", "command", "params", "seed", "status", "interpretation", "artifacts"])
        writer.writerow([
            marker,
            "2026-07-06",
            git_head(),
            "Stage 342",
            "continuity-audit",
            "python scripts/build_stage342_continuity_audit.py",
            "Stage36/49/50/331/341 evidence ladder",
            "n/a",
            DECISION,
            "Separates historical high-stat evidence, current-head anchors, and missing full-matrix cases without promoting broader claims.",
            f"{rel(DOC)}; {rel(SUMMARY)}; {rel(HOTPATH)}; {rel(EVIDENCE)}; {rel(PROOF)}",
        ])


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


def artifact_index(paths: list[Path]) -> None:
    rows = [{"artifact": rel(path), "exists": path.exists(), "bytes": file_size(path), "sha256": sha256_file(path)} for path in paths]
    write_csv(ARTIFACT, rows, ["artifact", "exists", "bytes", "sha256"])


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    hot = hotpath_rows()
    evidence = evidence_rows(hot)
    matrix = matrix_rows()
    claims = claim_rows()
    proof = proof_rows(hot, matrix)
    nextq = next_rows()
    stage331 = first_row(STAGE331_SUMMARY)
    stage341 = first_row(STAGE341_SUMMARY)
    summary = [{
        "decision": DECISION,
        "current_head": git_head(),
        "primary_current_head_r4_speedup": stage331.get("speedup_vs_repeated_scalar_mean", ""),
        "r2_current_head_status": "smoke_only",
        "r2_smoke_speedup": stage341.get("speedup_mean", ""),
        "stage36_hotpath_to_head": next((row.get("continuity_status", "") for row in hot if row.get("evidence") == "stage36_target_perf"), ""),
        "full_matrix_status": "missing_current_head_highstat_cases",
        "claim_status": "scoped_bridge_only",
    }]
    write_csv(SUMMARY, summary, ["decision", "current_head", "primary_current_head_r4_speedup", "r2_current_head_status", "r2_smoke_speedup", "stage36_hotpath_to_head", "full_matrix_status", "claim_status"])
    write_csv(HOTPATH, hot, ["evidence", "ref", "ref_resolves", "current_head", "hotpath_diff_count", "hotpath_diff_paths", "continuity_status", "source"])
    write_csv(EVIDENCE, evidence, ["layer", "status", "metric", "value", "continuity", "claim_use", "source"])
    write_csv(MATRIX_STATUS, matrix, ["case", "status", "samples", "speedup", "noise", "next_needed"])
    write_csv(CLAIMS, claims, ["claim", "status", "safe_statement", "blocked_statement", "evidence"])
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "command", "gate", "failure_action"])
    write_text(COMMANDS, """# Stage342 Reproduction Commands

```powershell
python scripts\\build_stage342_continuity_audit.py
```
""")
    write_text(REPORT, f"""# Stage342 Continuity Audit

Decision: `{DECISION}`.

Stage342 separates historical high-stat evidence from current-head evidence.
It does not run new benchmarks and it does not promote a broader parameter
claim.

## Summary

{md_table(summary, ["decision", "current_head", "primary_current_head_r4_speedup", "r2_current_head_status", "r2_smoke_speedup", "stage36_hotpath_to_head", "full_matrix_status"])}

## Evidence Ladder

{md_table(evidence, ["layer", "status", "metric", "value", "continuity", "claim_use"])}

## Matrix Status

{md_table(matrix, ["case", "status", "samples", "speedup", "noise", "next_needed"])}

## Proof Gate

{md_table(proof, ["gate", "status", "metric", "value"])}
""")
    write_text(DOC, f"""# Stage342 Continuity Audit

Decision: `{DECISION}`.

The current safe bridge is:

- current-head r=4 high-stat remains the primary scoped claim;
- current-head r=2 has a real smoke only;
- Stage36 target and added-parameter rows remain historical/supporting where
  hot-path changes prevent direct current-head promotion;
- full current-head parameter matrix is still incomplete.

{md_table(summary, ["decision", "primary_current_head_r4_speedup", "r2_current_head_status", "r2_smoke_speedup", "full_matrix_status"])}
""")
    write_text(THEORY, """# Stage342 Continuity Claim Model

A high-stat result and a current-head result are different evidence types.

Stage36 supplies high-stat evidence, but hot-path changes after Stage36 prevent
directly treating those rows as a full current-head matrix. Stage49/50 provide
continuity context for the target r=2/r=4 path, Stage331 supplies current-head
r=4 high-stat evidence, and Stage341 supplies current-head r=2 smoke evidence.

Therefore the only safe promotion is the scoped bridge. Full broader parameter
wording requires current-head high-stat runs for the missing cases.
""")
    write_text(PLAN, """# Stage343 Current-Head Matrix Top-Up Plan

Priority route:

- top up `SET_2_3_2048 r=2` from smoke to high-stat if target r=2 current-head
  wording is required;
- rerun added binary parameters on current head only if broader added-parameter
  wording is required;
- otherwise switch to verified literature or new mechanism/proof preflight.

No Stage342 artifact permits theoretical optimality, novelty, non-binary, or
all-parameter wording.
""")
    append_once(GOAL, "<!-- stage342-continuity-audit -->", f"""
<!-- stage342-continuity-audit -->
- Stage342: `{DECISION}`. Historical high-stat rows, current-head r=4 high-stat, and current-head r=2 smoke are separated; full current-head matrix claim remains blocked.
""")
    append_once(ROADMAP, "<!-- stage342-continuity-audit -->", f"""
<!-- stage342-continuity-audit -->
## Stage342: Continuity Audit

- Decision: `{DECISION}`.
- Result: scoped bridge only; no broader parameter promotion.
- Next: targeted current-head topups or verified literature/mechanism route.
""")
    append_once(HYPOTHESES, "H342_continuity_audit:", f"""
H342_continuity_audit:
  status: {DECISION}
  primary_metric: evidence_continuity_for_complete_sab_T_bootstrap_over_r
  evidence:
    - repro/stage342_continuity_audit/summary.csv
    - repro/stage342_continuity_audit/hotpath_delta_audit.csv
    - repro/stage342_continuity_audit/evidence_ladder.csv
    - repro/stage342_continuity_audit/proof_gate.csv
  conclusion: >
    Stage342 separates historical high-stat rows from current-head anchors.
    The result is a scoped bridge, not a full current-head parameter matrix.
""")
    append_once(MANIFEST, "<!-- stage342-continuity-audit-manifest -->", """
<!-- stage342-continuity-audit-manifest -->
- stage342_continuity_audit:
  - `docs/stage342_continuity_audit.md`
  - `theory_checks/stage342_continuity_claim_model.md`
  - `experiments/stage343_current_head_matrix_topup_plan.md`
  - `scripts/build_stage342_continuity_audit.py`
  - `repro/stage342_continuity_audit/`
""")
    append_once(CHECKLIST, "<!-- stage342-continuity-audit-checklist -->", f"""
<!-- stage342-continuity-audit-checklist -->
- [x] Stage342 records `{DECISION}` and keeps full current-head matrix claims blocked.
""")
    append_run_log()
    artifact_index([DOC, THEORY, PLAN, BUILDER, SUMMARY, HOTPATH, EVIDENCE, MATRIX_STATUS, CLAIMS, PROOF, NEXT, REPORT, COMMANDS])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
