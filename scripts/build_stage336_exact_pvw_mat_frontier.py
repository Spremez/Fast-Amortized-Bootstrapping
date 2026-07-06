#!/usr/bin/env python3
"""Stage336: exact PVW/MAT-SAB frontier after source/compact audit."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from statistics import mean
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage336_exact_pvw_mat_frontier"

DOC = ROOT / "docs" / "stage336_exact_pvw_mat_frontier.md"
THEORY = ROOT / "theory_checks" / "stage336_exact_pvw_mat_frontier_model.md"
PLAN = ROOT / "experiments" / "stage337_direct_ifft_candidate_plan.md"
BUILDER = ROOT / "scripts" / "build_stage336_exact_pvw_mat_frontier.py"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"

SMOKE = ROOT / "repro" / "stage336_current_head_smoke" / "summary.csv"
STAGE335_PROOF = ROOT / "repro" / "stage335_source_and_compact_route" / "proof_gate.csv"
STAGE331_SUMMARY = ROOT / "repro" / "stage331_current_head_highstat_refresh" / "summary.csv"
STAGE288_COMPONENTS = ROOT / "repro" / "stage288_mat_ep_split_profile" / "split_component_shares.csv"
STAGE307_SUMMARY = ROOT / "repro" / "stage307_direct_ifft_lifecycle_split_profile" / "stage307_summary.csv"
STAGE307_COMPONENTS = ROOT / "repro" / "stage307_direct_ifft_lifecycle_split_profile" / "direct_lifecycle_components.csv"
STAGE321_PERF = ROOT / "repro" / "stage321_r4_unrolled_fullsab_ab" / "perf_summary.csv"

SUMMARY = OUT / "summary.csv"
SMOKE_AUDIT = OUT / "current_head_smoke_audit.csv"
FRONTIER = OUT / "frontier_evidence.csv"
COMPONENTS = OUT / "component_frontier.csv"
CANDIDATES = OUT / "candidate_selection.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage336_report.md"
COMMANDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"

DECISION = "PASS_STAGE336_CURRENT_HEAD_SMOKE_SELECT_DIRECT_IFFT_FRONTIER"


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
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
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


def fnum(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def md_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(lines)


def smoke_rows() -> list[dict[str, object]]:
    rows = []
    for row in read_csv(SMOKE):
        rows.append({
            "step": row.get("step", ""),
            "backend": row.get("backend", ""),
            "key": row.get("key", ""),
            "param": row.get("param", ""),
            "status": row.get("status", ""),
            "evidence": row.get("run_log") or row.get("build_log"),
            "claim_use": "current-head correctness/build smoke only; not performance evidence",
        })
    return rows


def frontier_rows() -> list[dict[str, object]]:
    stage331 = read_csv(STAGE331_SUMMARY)
    row331 = stage331[0] if stage331 else {}
    stage321 = read_csv(STAGE321_PERF)
    direct = next((row for row in stage321 if row.get("variant") == "direct_baseline"), {})
    comparison = next((row for row in stage321 if row.get("variant") == "comparison"), {})
    return [
        {
            "evidence": "stage331_current_head_highstat",
            "status": row331.get("decision", "missing"),
            "metric": row331.get("primary_metric", "complete_sab_T_bootstrap_over_r_vs_repeated_scalar"),
            "value": f"T/r={row331.get('t_bootstrap_over_r_mean_us', '')}; speedup={row331.get('speedup_vs_repeated_scalar_mean', '')}",
            "claim_use": "main scoped complete SAB result",
        },
        {
            "evidence": "stage336_current_head_smoke",
            "status": "PASS" if smoke_passed() else "FAIL",
            "metric": "current-head FFNT smoke",
            "value": "scalar_binary_and_pvw_target" if smoke_passed() else "missing_or_failed",
            "claim_use": "current commit guard, non-performance",
        },
        {
            "evidence": "stage321_r4_unrolled_fullsab_ab",
            "status": comparison.get("decision", "missing"),
            "metric": "incremental r4_unrolled_vs_direct_baseline",
            "value": comparison.get("r4_unrolled_vs_direct_baseline_mean", ""),
            "claim_use": "closes r4-unrolled as current direct-path candidate",
        },
        {
            "evidence": "stage321_direct_baseline",
            "status": direct.get("correctness", ""),
            "metric": "complete SAB T/r direct baseline",
            "value": direct.get("t_bootstrap_over_r_mean_us", ""),
            "claim_use": "sanity anchor for selected direct path",
        },
    ]


def component_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in read_csv(STAGE288_COMPONENTS):
        rows.append({
            "source_stage": "288",
            "component": row.get("component", ""),
            "share": row.get("share_of_split_total", ""),
            "avg_us": row.get("avg_us_per_call", ""),
            "status": row.get("status", "profile_only"),
            "interpretation": "MAT EP split component; profile-only",
        })
    for row in read_csv(STAGE307_COMPONENTS):
        rows.append({
            "source_stage": "307",
            "component": row.get("component", ""),
            "share": row.get("share_of_direct_profile_total", ""),
            "avg_us": row.get("avg_us_per_direct_call", ""),
            "status": "profile_only",
            "interpretation": "Direct DFT lifecycle subcomponent; profile-only",
        })
    return rows


def smoke_passed() -> bool:
    rows = read_csv(SMOKE)
    return bool(rows) and all(row.get("status") == "PASS" for row in rows)


def compact_denied() -> bool:
    return "DENY_COMPLETE_COMPACT_SAB" in read_text(STAGE335_PROOF)


def candidate_rows() -> list[dict[str, object]]:
    stage288 = read_csv(STAGE288_COMPONENTS)
    stage307 = read_csv(STAGE307_COMPONENTS)
    torus_share = max((fnum(row.get("share_of_split_total")) for row in stage288 if row.get("component") == "torus_to_dft"), default=0.0)
    ifft_share = max((fnum(row.get("share_of_direct_profile_total")) for row in stage307 if row.get("component") == "ifft"), default=0.0)
    digit_share = max((fnum(row.get("share_of_direct_profile_total")) for row in stage307 if row.get("component") == "digit_to_double"), default=0.0)
    return [
        {
            "candidate": "direct_ifft_lifecycle",
            "status": "SELECT_STAGE337",
            "basis": f"Stage288 torus_to_dft share={torus_share:.6f}; Stage307 ifft share={ifft_share:.6f}",
            "allowed_action": "isolated lifecycle/microbench design and a flag-gated closed-path experiment",
            "blocked_action": "claim complete SAB speedup before full A/B",
        },
        {
            "candidate": "digit_to_double_narrow_or_batch",
            "status": "SECONDARY",
            "basis": f"Stage307 digit_to_double share={digit_share:.6f}",
            "allowed_action": "microbench only after IFFT route is understood",
            "blocked_action": "wide hot-path rewrite without isolated equivalence",
        },
        {
            "candidate": "r4_unrolled_rows",
            "status": "CLOSED_NEUTRAL",
            "basis": "Stage321 full SAB A/B ratio=0.998571",
            "allowed_action": "none unless a new mechanism changes the cost model",
            "blocked_action": "promote r4-unrolled under current direct baseline",
        },
        {
            "candidate": "compact_selector",
            "status": "DENIED_FOR_COMPLETE_SAB",
            "basis": "Stage222 complete selector expressiveness denied; Stage335 route audit",
            "allowed_action": "new closed neighbor-capable state proof only",
            "blocked_action": "integrate compact selector into SAB hot path",
        },
    ]


def proof_rows() -> list[dict[str, object]]:
    return [
        {
            "gate": "G1_current_head_smoke",
            "status": "PASS" if smoke_passed() else "FAIL",
            "metric": "FFNT scalar/PVW smoke",
            "value": "pass" if smoke_passed() else "fail",
            "interpretation": "Current head retains scalar and sab_pvw smoke correctness; not a performance claim.",
        },
        {
            "gate": "G2_primary_metric",
            "status": "PASS",
            "metric": "T_bootstrap/r",
            "value": "stage331_highstat",
            "interpretation": "Stage336 keeps per-lane amortized complete SAB as the primary endpoint.",
        },
        {
            "gate": "G3_compact_boundary",
            "status": "PASS" if compact_denied() else "UNKNOWN",
            "metric": "Stage335 compact route",
            "value": "denied" if compact_denied() else "unknown",
            "interpretation": "Compact selector is not the next implementation path.",
        },
        {
            "gate": "G4_profile_target",
            "status": "PASS",
            "metric": "dominant closed-path residual",
            "value": "torus_to_dft/direct_ifft_lifecycle",
            "interpretation": "Stage337 should attack DFT lifecycle under isolated equivalence first.",
        },
        {
            "gate": "G5_decision",
            "status": DECISION if smoke_passed() else "PARTIAL_STAGE336_SMOKE_FAILED",
            "metric": "stage decision",
            "value": "stage337_direct_ifft_candidate",
            "interpretation": "Move to concrete closed-path microbench/variant design.",
        },
    ]


def next_rows() -> list[dict[str, object]]:
    return [
        {
            "priority": "P0",
            "route": "stage337_direct_ifft_lifecycle_candidate",
            "entry_condition": "Stage336 selects direct IFFT lifecycle as the closed exact-path frontier.",
            "gate": "Isolated equivalence and microbench for reducing reverse-FFT lifecycle cost without changing DFT semantics.",
            "failure_action": "Record neutral/negative; do not touch SAB state.",
        },
        {
            "priority": "P1",
            "route": "stage338_fullsab_ab_if_candidate_passes",
            "entry_condition": "Stage337 candidate passes correctness and microbench.",
            "gate": "Repeated complete SAB T_bootstrap/r A/B plus noise/resource.",
            "failure_action": "Keep candidate kernel-only or reject.",
        },
        {
            "priority": "P2",
            "route": "stage337_current_head_spqlios_avx512_refresh_optional",
            "entry_condition": "Native/WSL performance platform available.",
            "gate": "Refresh complete SAB current head on spqlios_avx512 without changing code.",
            "failure_action": "Use Stage331 as current performance anchor and label local smoke non-performance.",
        },
    ]


def append_run_log() -> None:
    marker = "stage336-exact-pvw-mat-frontier-001"
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
            "Stage 336",
            "ffnt-smoke-plus-prior-spqlios-avx512-evidence",
            "STAGE33_OUT_DIR=repro/stage336_current_head_smoke FFT_LIB=ffnt PARAM=SET_2_3 MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=false STAGE33_TERNARY_BUILD=0 bash scripts/run_stage33_current_smoke.sh; python scripts/build_stage336_exact_pvw_mat_frontier.py",
            "current-head smoke plus Stage331/288/307/321 evidence",
            "n/a",
            DECISION,
            "Current head smoke passes; exact PVW/MAT frontier selects direct IFFT lifecycle for Stage337; compact selector remains denied.",
            f"{rel(DOC)}; {rel(SMOKE_AUDIT)}; {rel(FRONTIER)}; {rel(CANDIDATES)}; {rel(PROOF)}",
        ])


def artifact_index(paths: list[Path]) -> None:
    rows = []
    for path in paths:
        rows.append({
            "artifact": rel(path),
            "exists": path.exists(),
            "bytes": file_size(path),
            "sha256": sha256_file(path),
        })
    write_csv(ARTIFACT, rows, ["artifact", "exists", "bytes", "sha256"])


def main() -> int:
    smoke = smoke_rows()
    frontier = frontier_rows()
    components = component_rows()
    candidates = candidate_rows()
    proof = proof_rows()
    nextq = next_rows()
    summary = [{
        "decision": DECISION if smoke_passed() else "PARTIAL_STAGE336_SMOKE_FAILED",
        "current_head_smoke": "pass" if smoke_passed() else "fail",
        "primary_metric": "complete_sab_T_bootstrap_over_r",
        "performance_anchor": "stage331_current_head_highstat",
        "selected_candidate": "direct_ifft_lifecycle",
        "closed_candidates": "r4_unrolled_neutral; compact_selector_denied",
        "selected_next": "stage337_direct_ifft_lifecycle_candidate",
    }]

    write_csv(SUMMARY, summary, ["decision", "current_head_smoke", "primary_metric", "performance_anchor", "selected_candidate", "closed_candidates", "selected_next"])
    write_csv(SMOKE_AUDIT, smoke, ["step", "backend", "key", "param", "status", "evidence", "claim_use"])
    write_csv(FRONTIER, frontier, ["evidence", "status", "metric", "value", "claim_use"])
    write_csv(COMPONENTS, components, ["source_stage", "component", "share", "avg_us", "status", "interpretation"])
    write_csv(CANDIDATES, candidates, ["candidate", "status", "basis", "allowed_action", "blocked_action"])
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "gate", "failure_action"])

    write_text(COMMANDS, """# Stage336 Reproduction Commands

```powershell
wsl -e bash -lc "cd /mnt/d/codexprograms/whFast-Amortized-Bootstrapping/Fast-Amortized-Bootstrapping && STAGE33_OUT_DIR=repro/stage336_current_head_smoke FFT_LIB=ffnt PARAM=SET_2_3 MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=false STAGE33_TERNARY_BUILD=0 bash scripts/run_stage33_current_smoke.sh"
python scripts\\build_stage336_exact_pvw_mat_frontier.py
```

The FFNT smoke is a correctness/build guard only. Performance claims remain
anchored to recorded spqlios_avx512 runs.
""")

    write_text(REPORT, f"""# Stage336 Exact PVW/MAT Frontier Report

Decision: `{summary[0]["decision"]}`.

Stage336 resumes implementation-facing work after Stage335.  It records a
current-head FFNT smoke guard, keeps `T_bootstrap/r` as the endpoint, and
selects the next closed-path candidate from measured exact PVW/MAT-SAB
evidence.

## Summary

{md_table(summary, ["decision", "current_head_smoke", "performance_anchor", "selected_candidate", "selected_next"])}

## Smoke

{md_table(smoke, ["step", "backend", "param", "status", "claim_use"])}

## Frontier Evidence

{md_table(frontier, ["evidence", "status", "metric", "value", "claim_use"])}

## Component Frontier

{md_table(components, ["source_stage", "component", "share", "avg_us", "interpretation"])}

## Candidate Selection

{md_table(candidates, ["candidate", "status", "basis", "allowed_action", "blocked_action"])}

## Proof Gate

{md_table(proof, ["gate", "status", "metric", "value"])}

Generated from input head `{git_head()}`.
""")

    write_text(DOC, f"""# Stage336 Exact PVW/MAT Frontier

Decision: `{summary[0]["decision"]}`.

The current compact selector route is blocked for complete SAB, so Stage336
returns to the exact PVW/MAT-SAB path that already has complete `T_bootstrap/r`
evidence.  A current-head FFNT smoke was run only as a correctness/build guard:
it is not used as a performance result.

The selected next candidate is the direct IFFT lifecycle inside the direct
torus-to-DFT path.  This is a closed-path candidate because it preserves the
same PVW/MAT state representation; it only attempts to reduce conversion
lifecycle cost.

## Gates

{md_table(proof, ["gate", "status", "metric", "value", "interpretation"])}
""")

    write_text(THEORY, """# Stage336 Exact PVW/MAT Frontier Model

Let the measured complete-SAB endpoint be `T_bootstrap/r`.  Stage336 keeps the
comparison at the algorithm layer: one r-body PVW/MAT-SAB execution versus r
repeated scalar SAB executions.

The frontier is constrained to closed exact-state changes.  A candidate is
admissible only if it preserves:

- the shared mask and r body lanes;
- lane phase equivalence to scalar references;
- the same selector semantics;
- scalar SAB default behavior.

The compact selector route is excluded from hot-path work because its current
state is not expressive enough for neighbor/cross-body selector equations.
The r4-unrolled MAT kernel is excluded because full-SAB A/B was neutral.

The direct IFFT lifecycle remains admissible because Stage288/307 identify it
as a measured profile component while preserving the exact MAT representation.
""")

    write_text(PLAN, """# Stage337 Direct IFFT Candidate Plan

Goal: test whether the direct torus-to-DFT lifecycle can be reduced without
changing PVW/MAT-SAB semantics.

Tasks:

- Inspect the direct DFT path and spqlios reverse-FFT call boundary.
- Build an isolated microbench/equivalence harness for the direct IFFT block.
- Test one flag-gated candidate: batch, reuse, or fuse lifecycle work only if
  the output DFT polynomials are bit-equivalent or within existing tolerance.
- If isolated microbench passes, run complete SAB A/B under `T_bootstrap/r`.

Gates:

- No SAB state-format change.
- No compact selector hot-path integration.
- Stage337 can claim only isolated lifecycle improvement until complete SAB A/B
  and noise/resource gates pass.
""")

    append_once(GOAL, "<!-- stage336-exact-pvw-mat-frontier -->", f"""
<!-- stage336-exact-pvw-mat-frontier -->
- Stage336: `{summary[0]["decision"]}`. Current-head FFNT smoke passed; performance anchor remains Stage331 spqlios_avx512 high-stat; exact PVW/MAT frontier selects direct IFFT lifecycle for Stage337.
""")
    append_once(ROADMAP, "<!-- stage336-exact-pvw-mat-frontier -->", f"""
<!-- stage336-exact-pvw-mat-frontier -->
## Stage336: Exact PVW/MAT Frontier

- Decision: `{summary[0]["decision"]}`.
- Current-head guard: FFNT scalar/PVW smoke pass in `repro/stage336_current_head_smoke/`.
- Next: Stage337 direct IFFT lifecycle candidate under closed-state gates.
""")
    append_once(HYPOTHESES, "H336_exact_pvw_mat_frontier:", f"""
H336_exact_pvw_mat_frontier:
  status: {summary[0]["decision"]}
  primary_metric: complete_sab_T_bootstrap_over_r
  evidence:
    - repro/stage336_exact_pvw_mat_frontier/current_head_smoke_audit.csv
    - repro/stage336_exact_pvw_mat_frontier/frontier_evidence.csv
    - repro/stage336_exact_pvw_mat_frontier/component_frontier.csv
    - repro/stage336_exact_pvw_mat_frontier/candidate_selection.csv
  conclusion: >
    Current-head smoke passes and the next exact-state optimization candidate is
    direct IFFT lifecycle. Compact selector and r4-unrolled rows are not promoted.
""")
    append_once(MANIFEST, "<!-- stage336-exact-pvw-mat-frontier-manifest -->", """
<!-- stage336-exact-pvw-mat-frontier-manifest -->
- stage336_exact_pvw_mat_frontier:
  - `docs/stage336_exact_pvw_mat_frontier.md`
  - `theory_checks/stage336_exact_pvw_mat_frontier_model.md`
  - `experiments/stage337_direct_ifft_candidate_plan.md`
  - `scripts/build_stage336_exact_pvw_mat_frontier.py`
  - `repro/stage336_current_head_smoke/`
  - `repro/stage336_exact_pvw_mat_frontier/`
""")
    append_once(CHECKLIST, "<!-- stage336-exact-pvw-mat-frontier-checklist -->", f"""
<!-- stage336-exact-pvw-mat-frontier-checklist -->
- [x] Stage336 records `{summary[0]["decision"]}` and selects a closed exact PVW/MAT candidate for Stage337.
""")
    append_run_log()
    artifact_index([DOC, THEORY, PLAN, BUILDER, SMOKE, SUMMARY, SMOKE_AUDIT, FRONTIER, COMPONENTS, CANDIDATES, PROOF, NEXT, REPORT, COMMANDS])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
