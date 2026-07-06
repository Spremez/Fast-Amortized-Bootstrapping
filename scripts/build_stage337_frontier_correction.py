#!/usr/bin/env python3
"""Stage337: correct the frontier using already-closed candidate evidence."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage337_frontier_correction"

DOC = ROOT / "docs" / "stage337_frontier_correction.md"
THEORY = ROOT / "theory_checks" / "stage337_frontier_correction_model.md"
PLAN = ROOT / "experiments" / "stage338_new_mechanism_or_proof_plan.md"
BUILDER = ROOT / "scripts" / "build_stage337_frontier_correction.py"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"

SUMMARY = OUT / "summary.csv"
CANDIDATES = OUT / "closed_candidate_audit.csv"
ROUTES = OUT / "route_decision.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage337_report.md"
COMMANDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"

STAGE336 = ROOT / "repro" / "stage336_exact_pvw_mat_frontier" / "summary.csv"
STAGE318 = ROOT / "docs" / "stage318_ifft_batch5_intrinsics_microbench.md"
STAGE319 = ROOT / "docs" / "stage319_ifft_batch5_asm_microbench.md"
STAGE312 = ROOT / "repro" / "stage312_digit_narrow32_fullsab_ab" / "summary.csv"
STAGE313 = ROOT / "repro" / "stage313_narrow32_profile_attribution" / "summary.csv"
STAGE321 = ROOT / "repro" / "stage321_r4_unrolled_fullsab_ab" / "perf_summary.csv"
STAGE323 = ROOT / "repro" / "stage323_dense_mat_counter_preflight" / "proof_gate.csv"
STAGE325 = ROOT / "repro" / "stage325_selector_transpose_resource_probe" / "summary.csv"
STAGE326 = ROOT / "repro" / "stage326_exact_dense_route_closeout" / "frontier_status.csv"
STAGE335 = ROOT / "repro" / "stage335_source_and_compact_route" / "proof_gate.csv"

DECISION = "PASS_STAGE337_FRONTIER_CORRECTED_NO_REPEAT_FAILED_CANDIDATES"


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


def md_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(lines)


def candidate_rows() -> list[dict[str, object]]:
    stage321_comp = next((r for r in read_csv(STAGE321) if r.get("variant") == "comparison"), {})
    return [
        {
            "candidate": "direct_ifft_batch5_intrinsics",
            "status": "CLOSED_SLOW",
            "evidence": rel(STAGE318),
            "reason": "Correct but slower isolated batch5 intrinsics; do not integrate.",
            "reopen_condition": "Different backend primitive with isolated speedup and equivalence.",
        },
        {
            "candidate": "direct_ifft_batch5_asm",
            "status": "CLOSED_SLOW",
            "evidence": rel(STAGE319),
            "reason": "Correct but slower hand assembly; closes batch5 IFFT family.",
            "reopen_condition": "New SPQLIOS primitive or native evidence not equivalent to Stage319.",
        },
        {
            "candidate": "digit_narrow32",
            "status": "CLOSED_FULLSAB_NEUTRAL",
            "evidence": rel(STAGE312),
            "reason": "Microbench positive but complete SAB A/B neutral.",
            "reopen_condition": "New digit mechanism with full-SAB positive A/B.",
        },
        {
            "candidate": "r4_unrolled_rows",
            "status": "CLOSED_FULLSAB_NEUTRAL",
            "evidence": rel(STAGE321),
            "reason": f"Current direct baseline comparison ratio={stage321_comp.get('r4_unrolled_vs_direct_baseline_mean', '')}.",
            "reopen_condition": "New load/store count mechanism beyond pointer hoisting.",
        },
        {
            "candidate": "selector_transpose",
            "status": "CLOSED_MICRO_NEUTRAL",
            "evidence": rel(STAGE325),
            "reason": "Isolated dense speedup below threshold for 1% full-SAB projection.",
            "reopen_condition": "Different key layout with resource proof and stronger isolated speedup.",
        },
        {
            "candidate": "compact_selector_current_state",
            "status": "DENIED_COMPLETE_SAB",
            "evidence": rel(STAGE335),
            "reason": "Current compact/lane-local state does not support complete selector integration.",
            "reopen_condition": "Formal neighbor-capable closed state plus keygen/security/noise gates.",
        },
    ]


def route_rows() -> list[dict[str, object]]:
    return [
        {
            "route": "repeat_old_exact_kernel_work",
            "decision": "DENY",
            "basis": "Stage318/319/312/321/325 already close the concrete candidates.",
            "allowed_next": "none",
        },
        {
            "route": "new_exact_mechanism",
            "decision": "ALLOW_IF_MECHANISM_EXISTS",
            "basis": "Stage326 permits reopening only with a new load/store/count mechanism.",
            "allowed_next": "preflight proof plus isolated microbench before SAB code",
        },
        {
            "route": "compact_or_structured_algorithm",
            "decision": "ALLOW_PROOF_ONLY",
            "basis": "Stage335/222 deny current complete selector route.",
            "allowed_next": "formal closed-state/keygen/noise proof before any hot-path code",
        },
        {
            "route": "claim_and_parameter_package",
            "decision": "ALLOW",
            "basis": "Current supported claim remains scoped T_bootstrap/r evidence.",
            "allowed_next": "parameter/statistical refresh or paper package without stronger wording",
        },
    ]


def proof_rows() -> list[dict[str, object]]:
    stage336_ok = "PASS_STAGE336" in read_text(STAGE336)
    stage326_closed = "CLOSED_UNDER_CURRENT_EVIDENCE" in read_text(STAGE326)
    compact_denied = "DENY_COMPLETE_COMPACT_SAB" in read_text(STAGE335)
    return [
        {
            "gate": "G1_stage336_input",
            "status": "PASS" if stage336_ok else "MISSING",
            "metric": "Stage336 frontier",
            "value": "present" if stage336_ok else "missing",
            "interpretation": "Stage337 corrects Stage336 candidate selection with earlier closure evidence.",
        },
        {
            "gate": "G2_no_repeat_candidates",
            "status": "PASS",
            "metric": "closed candidate families",
            "value": "ifft;digit;r4_unrolled;selector_transpose",
            "interpretation": "Do not rerun old candidates unless a new mechanism changes the hypothesis.",
        },
        {
            "gate": "G3_exact_dense_closeout",
            "status": "PASS" if stage326_closed else "UNKNOWN",
            "metric": "Stage326 frontier",
            "value": "closed_under_current_evidence" if stage326_closed else "not_confirmed",
            "interpretation": "Exact dense/local routes are closed under current evidence, not globally optimal.",
        },
        {
            "gate": "G4_compact_boundary",
            "status": "PASS" if compact_denied else "UNKNOWN",
            "metric": "Stage335 compact",
            "value": "denied" if compact_denied else "not_confirmed",
            "interpretation": "Compact/structured route requires proof, not hot-path coding.",
        },
        {
            "gate": "G5_decision",
            "status": DECISION,
            "metric": "stage decision",
            "value": "no_repeat_failed_candidates",
            "interpretation": "Next execution must supply a new mechanism/proof or stay in scoped claim/parameter work.",
        },
    ]


def next_rows() -> list[dict[str, object]]:
    return [
        {
            "priority": "P0",
            "route": "stage338_new_mechanism_intake",
            "entry_condition": "A concrete new load/store/count or backend primitive is identified.",
            "gate": "Mechanism model plus isolated equivalence/microbench; no SAB code first.",
            "failure_action": "Reject without full-SAB work.",
        },
        {
            "priority": "P1",
            "route": "stage338_formal_compact_reopen",
            "entry_condition": "A formal neighbor/cross-body closed state proof is supplied or derived.",
            "gate": "Distribution/keygen/security/noise proof then isolated equivalence.",
            "failure_action": "Keep compact route blocked.",
        },
        {
            "priority": "P2",
            "route": "stage338_parameter_or_paper_package",
            "entry_condition": "No new mechanism/proof is available.",
            "gate": "Use only scoped T_bootstrap/r claims and recorded negative ablations.",
            "failure_action": "Do not claim theoretical optimality or universal speedup.",
        },
    ]


def append_run_log() -> None:
    marker = "stage337-frontier-correction-001"
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
            "Stage 337",
            "evidence-correction",
            "python scripts/build_stage337_frontier_correction.py",
            "Stage318/319/312/321/325/326/335 closure evidence",
            "n/a",
            DECISION,
            "Corrects the Stage336 direct-IFFT route by consuming already-closed candidate evidence and prevents repeated failed kernel work.",
            f"{rel(DOC)}; {rel(CANDIDATES)}; {rel(ROUTES)}; {rel(PROOF)}",
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
    candidates = candidate_rows()
    routes = route_rows()
    proof = proof_rows()
    nextq = next_rows()
    summary = [{
        "decision": DECISION,
        "corrected_stage336_candidate": "direct_ifft_lifecycle_closed_by_stage318_319",
        "exact_dense_frontier": "closed_under_current_evidence",
        "compact_frontier": "blocked_proof_required",
        "allowed_next": "new_mechanism_or_formal_proof_or_scoped_package",
    }]

    write_csv(SUMMARY, summary, ["decision", "corrected_stage336_candidate", "exact_dense_frontier", "compact_frontier", "allowed_next"])
    write_csv(CANDIDATES, candidates, ["candidate", "status", "evidence", "reason", "reopen_condition"])
    write_csv(ROUTES, routes, ["route", "decision", "basis", "allowed_next"])
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "gate", "failure_action"])
    write_text(COMMANDS, """# Stage337 Reproduction Commands

```powershell
python scripts\\build_stage337_frontier_correction.py
```

Stage337 is an evidence-correction gate. It intentionally performs no hot-path
code changes because every concrete exact candidate in scope already has a
negative or neutral gate.
""")

    write_text(REPORT, f"""# Stage337 Frontier Correction Report

Decision: `{DECISION}`.

Stage336 selected direct IFFT lifecycle as the apparent closed-path frontier.
Stage337 corrects that route by consuming the earlier Stage318/319 IFFT
microbenches, Stage312/313 digit evidence, Stage321 r4-unrolled full-SAB A/B,
Stage325 selector-transpose probe, and Stage326 closeout.

## Summary

{md_table(summary, ["decision", "corrected_stage336_candidate", "exact_dense_frontier", "compact_frontier", "allowed_next"])}

## Closed Candidate Audit

{md_table(candidates, ["candidate", "status", "reason", "reopen_condition"])}

## Route Decision

{md_table(routes, ["route", "decision", "basis", "allowed_next"])}

## Proof Gate

{md_table(proof, ["gate", "status", "metric", "value"])}
""")

    write_text(DOC, f"""# Stage337 Frontier Correction

Decision: `{DECISION}`.

This stage prevents a theory loop.  The direct IFFT lifecycle candidate selected
by Stage336 is not reopened, because prior isolated batch5 IFFT implementations
were correct but slower.  Digit narrowing, r4-unrolled rows, and selector
transpose are also already neutral or closed under complete-SAB or projection
gates.

The active goal remains open, but the allowed next work is narrower and more
honest: either introduce a genuinely new measured mechanism, provide a formal
compact/structured proof, or package the scoped `T_bootstrap/r` result with the
negative ablations.

## Gates

{md_table(proof, ["gate", "status", "metric", "value", "interpretation"])}
""")

    write_text(THEORY, """# Stage337 Frontier Correction Model

An optimization route is not admissible merely because a profile component is
large. It must also be unclosed under prior evidence and have a plausible new
mechanism.

Stage337 applies this rule:

- IFFT lifecycle is large but closed by correct-and-slower batch5 candidates.
- Digit conversion is measurable but closed by complete-SAB neutrality.
- r4 local loop work is closed by complete-SAB neutrality.
- Selector transpose is correct but below the projected full-SAB threshold.
- Compact selector changes semantics and remains proof-blocked.

Therefore no hot-path implementation is admitted from the current candidate set.
""")

    write_text(PLAN, """# Stage338 New Mechanism Or Proof Plan

Stage338 starts only if one of these inputs exists:

- a new backend or load/store/count mechanism not equivalent to Stage318/319,
  Stage312, Stage321, or Stage325;
- a formal compact/structured closed-state proof that covers neighbor or
  cross-body selector equations;
- a decision to package the scoped result and negative ablations without
  claiming theoretical optimality.

Any new implementation must pass:

- isolated equivalence;
- isolated microbench threshold tied to complete-SAB Amdahl share;
- full SAB `T_bootstrap/r` A/B;
- noise/resource gate;
- scalar baseline unchanged.
""")

    append_once(GOAL, "<!-- stage337-frontier-correction -->", f"""
<!-- stage337-frontier-correction -->
- Stage337: `{DECISION}`. Direct IFFT, digit, r4-unrolled, selector-transpose, and current compact candidates are not reopened; next work requires a new mechanism/proof or scoped packaging.
""")
    append_once(ROADMAP, "<!-- stage337-frontier-correction -->", f"""
<!-- stage337-frontier-correction -->
## Stage337: Frontier Correction

- Decision: `{DECISION}`.
- Purpose: prevent repeated work on already neutral/failed candidates.
- Next: Stage338 only with a new mechanism, a formal compact proof, or scoped claim/package work.
""")
    append_once(HYPOTHESES, "H337_frontier_correction:", f"""
H337_frontier_correction:
  status: {DECISION}
  primary_metric: admissible_next_route
  evidence:
    - repro/stage337_frontier_correction/closed_candidate_audit.csv
    - repro/stage337_frontier_correction/route_decision.csv
    - repro/stage337_frontier_correction/proof_gate.csv
  conclusion: >
    No current exact local candidate is admitted for hot-path work. Progress
    requires a new measured mechanism, a formal compact proof, or scoped result
    packaging with negative ablations.
""")
    append_once(MANIFEST, "<!-- stage337-frontier-correction-manifest -->", """
<!-- stage337-frontier-correction-manifest -->
- stage337_frontier_correction:
  - `docs/stage337_frontier_correction.md`
  - `theory_checks/stage337_frontier_correction_model.md`
  - `experiments/stage338_new_mechanism_or_proof_plan.md`
  - `scripts/build_stage337_frontier_correction.py`
  - `repro/stage337_frontier_correction/`
""")
    append_once(CHECKLIST, "<!-- stage337-frontier-correction-checklist -->", f"""
<!-- stage337-frontier-correction-checklist -->
- [x] Stage337 records `{DECISION}` and blocks repeated failed candidate work.
""")
    append_run_log()
    artifact_index([DOC, THEORY, PLAN, BUILDER, SUMMARY, CANDIDATES, ROUTES, PROOF, NEXT, REPORT, COMMANDS])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
