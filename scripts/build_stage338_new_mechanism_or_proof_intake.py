#!/usr/bin/env python3
"""Stage338: gate new mechanisms, formal proofs, or scoped packaging."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage338_new_mechanism_or_proof_intake"

DOC = ROOT / "docs" / "stage338_new_mechanism_or_proof_intake.md"
THEORY = ROOT / "theory_checks" / "stage338_route_decision_model.md"
PLAN = ROOT / "experiments" / "stage339_scoped_package_or_new_mechanism_plan.md"
BUILDER = ROOT / "scripts" / "build_stage338_new_mechanism_or_proof_intake.py"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"

SUMMARY = OUT / "summary.csv"
INPUT_STATUS = OUT / "input_status.csv"
MECHANISM = OUT / "mechanism_intake.csv"
FORMAL = OUT / "formal_proof_intake.csv"
PACKAGE = OUT / "package_route.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage338_report.md"
COMMANDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"

STAGE337_NEXT = ROOT / "repro" / "stage337_frontier_correction" / "next_stage_queue.csv"
STAGE337_ROUTES = ROOT / "repro" / "stage337_frontier_correction" / "route_decision.csv"
STAGE337_CLOSED = ROOT / "repro" / "stage337_frontier_correction" / "closed_candidate_audit.csv"
STAGE328_REQ = ROOT / "repro" / "stage328_active_goal_requirement_audit" / "requirement_matrix.csv"
STAGE328_EVIDENCE = ROOT / "repro" / "stage328_active_goal_requirement_audit" / "evidence_grade.csv"
STAGE331_SUMMARY = ROOT / "repro" / "stage331_current_head_highstat_refresh" / "summary.csv"
STAGE335_PROOF = ROOT / "repro" / "stage335_source_and_compact_route" / "proof_gate.csv"

DECISION = "PASS_STAGE338_NO_NEW_MECHANISM_SELECT_SCOPED_PACKAGE_OR_EXTERNAL_PROOF"


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


def md_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    lines = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
    for row in rows:
        cells = [str(row.get(field, "")).replace("|", "\\|") for field in fields]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def first_row(path: Path) -> dict[str, str]:
    rows = read_csv(path)
    return rows[0] if rows else {}


def input_status_rows() -> list[dict[str, object]]:
    checks = [
        {
            "input": "stage337_next_queue",
            "path": STAGE337_NEXT,
            "role": "Defines the only admitted continuation routes.",
        },
        {
            "input": "stage337_route_decision",
            "path": STAGE337_ROUTES,
            "role": "Blocks repeated failed exact-kernel work.",
        },
        {
            "input": "stage337_closed_candidates",
            "path": STAGE337_CLOSED,
            "role": "Records closed IFFT, digit, unrolled, selector, and compact candidates.",
        },
        {
            "input": "stage328_requirement_matrix",
            "path": STAGE328_REQ,
            "role": "Keeps the active goal open until optimality/proof gaps are closed.",
        },
        {
            "input": "stage328_evidence_grade",
            "path": STAGE328_EVIDENCE,
            "role": "Separates scoped complete-SAB evidence from paper-level/global claims.",
        },
        {
            "input": "stage331_highstat_complete_sab",
            "path": STAGE331_SUMMARY,
            "role": "Supplies the current strongest scoped T_bootstrap/r measurement.",
        },
        {
            "input": "stage335_compact_boundary",
            "path": STAGE335_PROOF,
            "role": "Blocks complete compact selector integration without a new proof.",
        },
    ]
    rows: list[dict[str, object]] = []
    for check in checks:
        path = check["path"]
        rows.append(
            {
                "input": check["input"],
                "status": "PRESENT" if path.exists() else "MISSING",
                "path": rel(path),
                "role": check["role"],
            }
        )
    return rows


def mechanism_rows() -> list[dict[str, object]]:
    return [
        {
            "candidate_input": "new_exact_backend_or_loadstore_mechanism",
            "status": "NOT_PRESENT_IN_CURRENT_WORKTREE",
            "evidence": rel(STAGE337_ROUTES),
            "admission_gate": "mechanism_model plus isolated equivalence plus isolated speedup",
            "action": "Do not edit SAB hot path until a concrete count/load/store primitive exists.",
        },
        {
            "candidate_input": "repeat_direct_ifft_batch5_family",
            "status": "DENIED_ALREADY_CLOSED",
            "evidence": rel(STAGE337_CLOSED),
            "admission_gate": "new backend primitive not equivalent to Stage318/319",
            "action": "Reject repeat implementation work.",
        },
        {
            "candidate_input": "repeat_digit_narrow32_or_r4_unrolled",
            "status": "DENIED_FULLSAB_NEUTRAL",
            "evidence": rel(STAGE337_CLOSED),
            "admission_gate": "new mechanism with full-SAB positive A/B",
            "action": "Keep as negative ablation.",
        },
        {
            "candidate_input": "native_perf_counter_refresh",
            "status": "ATTRIBUTION_ONLY_NOT_NEW_MECHANISM",
            "evidence": rel(STAGE331_SUMMARY),
            "admission_gate": "may explain speedup but cannot by itself claim a new algorithm",
            "action": "Use only for attribution if native Linux counters are available.",
        },
    ]


def formal_rows() -> list[dict[str, object]]:
    return [
        {
            "proof_input": "neighbor_capable_compact_selector_state",
            "status": "NOT_PRESENT_IN_CURRENT_WORKTREE",
            "evidence": rel(STAGE335_PROOF),
            "required_before_code": "closed state invariant for every SAB neighbor/cross-body selector",
            "action": "Keep compact route blocked.",
        },
        {
            "proof_input": "current_lane_local_compact_state",
            "status": "DENIED_FOR_COMPLETE_SAB",
            "evidence": rel(STAGE335_PROOF),
            "required_before_code": "distribution, keygen, security, noise, and finite equivalence gates",
            "action": "Do not integrate into complete SAB.",
        },
        {
            "proof_input": "shared_mask_or_common_mask_novelty",
            "status": "NOVELTY_BOUNDARY_ONLY",
            "evidence": rel(STAGE335_PROOF),
            "required_before_code": "not a proof of complete SAB acceleration",
            "action": "Use as related-work boundary, not as an implementation trigger.",
        },
    ]


def package_rows() -> list[dict[str, object]]:
    stage331 = first_row(STAGE331_SUMMARY)
    speedup = stage331.get("speedup_vs_repeated_scalar_mean", "")
    t_over_r = stage331.get("t_bootstrap_over_r_mean_us", "")
    ci_low = stage331.get("t_bootstrap_over_r_ci95_low_us", "")
    ci_high = stage331.get("t_bootstrap_over_r_ci95_high_us", "")
    samples = stage331.get("samples", "")
    return [
        {
            "claim_or_task": "scoped_complete_sab_t_bootstrap_over_r",
            "decision": "ALLOW",
            "support": f"speedup={speedup}; T_over_r_us={t_over_r}; CI95={ci_low}..{ci_high}; samples={samples}",
            "boundary": "same repo, same backend, r=4 current-head scoped comparison only",
        },
        {
            "claim_or_task": "negative_ablation_table",
            "decision": "ALLOW",
            "support": rel(STAGE337_CLOSED),
            "boundary": "closed candidates explain why old exact routes should not be repeated",
        },
        {
            "claim_or_task": "theoretical_optimality_of_mat_rlwe_sab",
            "decision": "BLOCK",
            "support": rel(STAGE328_REQ),
            "boundary": "same-format lower bound exists; global optimum is not proven",
        },
        {
            "claim_or_task": "universal_or_multi_parameter_speedup",
            "decision": "BLOCK",
            "support": rel(STAGE328_EVIDENCE),
            "boundary": "requires parameter matrix beyond the current scoped result",
        },
        {
            "claim_or_task": "novel_shared_mask_or_common_mask_claim",
            "decision": "BLOCK",
            "support": rel(STAGE335_PROOF),
            "boundary": "adjacent fulltext audit blocks broad novelty wording",
        },
    ]


def proof_rows(
    inputs: list[dict[str, object]],
    mechanisms: list[dict[str, object]],
    formal: list[dict[str, object]],
) -> list[dict[str, object]]:
    all_inputs_present = all(row.get("status") == "PRESENT" for row in inputs)
    new_mechanism_present = any(
        row.get("status") == "PRESENT" for row in mechanisms
    )
    formal_proof_present = any(row.get("status") == "PRESENT" for row in formal)
    return [
        {
            "gate": "G1_inputs",
            "status": "PASS" if all_inputs_present else "MISSING_INPUT",
            "metric": "required prior stage artifacts",
            "value": "all_present" if all_inputs_present else "some_missing",
            "interpretation": "Stage338 consumes prior evidence instead of reopening closed paths.",
        },
        {
            "gate": "G2_new_mechanism",
            "status": "NO_NEW_MECHANISM_FOUND",
            "metric": "concrete load/store/count/backend primitive",
            "value": "absent" if not new_mechanism_present else "present",
            "interpretation": "No SAB code is admitted without an isolated mechanism gate.",
        },
        {
            "gate": "G3_formal_compact_proof",
            "status": "NO_FORMAL_PROOF_FOUND",
            "metric": "neighbor-capable closed state proof",
            "value": "absent" if not formal_proof_present else "present",
            "interpretation": "Compact selector remains blocked for complete SAB integration.",
        },
        {
            "gate": "G4_scoped_package_route",
            "status": "PASS",
            "metric": "supported current evidence",
            "value": "scoped_T_bootstrap_over_r_plus_negative_ablations",
            "interpretation": "Proceed to paper/parameter package unless a new mechanism or proof is supplied.",
        },
        {
            "gate": "G5_decision",
            "status": DECISION,
            "metric": "selected next route",
            "value": "stage339_scoped_package_refresh_or_external_mechanism_proof",
            "interpretation": "The active research goal remains open; Stage338 prevents an ungrounded theory loop.",
        },
    ]


def next_rows() -> list[dict[str, object]]:
    return [
        {
            "priority": "P0",
            "route": "stage339_scoped_paper_package_refresh",
            "entry_condition": "No new mechanism or formal proof is available.",
            "gate": "Produce claim matrix, parameter status, negative ablation table, and repro pack without stronger wording.",
            "failure_action": "Downgrade to engineering note; do not claim optimality.",
        },
        {
            "priority": "P1",
            "route": "stage339_new_mechanism_protocol",
            "entry_condition": "A concrete new exact mechanism is supplied or derived.",
            "gate": "Count model, isolated equivalence, isolated microbench, then full SAB T_bootstrap/r A/B.",
            "failure_action": "Reject before hot-path integration if isolated gate fails.",
        },
        {
            "priority": "P2",
            "route": "stage339_formal_compact_state_proof",
            "entry_condition": "A neighbor/cross-body closed compact state proof is available.",
            "gate": "Distribution/keygen/security/noise proof followed by finite checker and isolated equivalence.",
            "failure_action": "Keep compact route as future work only.",
        },
        {
            "priority": "P3",
            "route": "stage339_parameter_matrix_refresh",
            "entry_condition": "Paper claim needs more than the current r=4 scoped result.",
            "gate": "Run available parameter/r matrix and mark unsupported branches explicitly.",
            "failure_action": "Limit claims to the measured parameter set.",
        },
    ]


def append_run_log() -> None:
    marker = "stage338-new-mechanism-intake-001"
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
                "Stage 338",
                "evidence-gate",
                "python scripts/build_stage338_new_mechanism_or_proof_intake.py",
                "Stage337/328/331/335 evidence",
                "n/a",
                DECISION,
                "No current new mechanism or formal compact proof is present; select scoped package route and keep implementation gates explicit.",
                f"{rel(DOC)}; {rel(SUMMARY)}; {rel(MECHANISM)}; {rel(FORMAL)}; {rel(PACKAGE)}",
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
    inputs = input_status_rows()
    mechanisms = mechanism_rows()
    formal = formal_rows()
    package = package_rows()
    proof = proof_rows(inputs, mechanisms, formal)
    nextq = next_rows()
    stage331 = first_row(STAGE331_SUMMARY)
    summary = [
        {
            "decision": DECISION,
            "new_mechanism_input": "none_detected",
            "formal_proof_input": "none_detected",
            "selected_route": "stage339_scoped_paper_package_refresh",
            "goal_status": "active_not_complete",
            "supported_metric": "complete_sab_T_bootstrap_over_r_vs_repeated_scalar",
            "supported_speedup": stage331.get("speedup_vs_repeated_scalar_mean", ""),
            "blocked_claims": "theoretical_optimality;universal_speedup;compact_sab;shared_mask_novelty",
        }
    ]

    write_csv(
        SUMMARY,
        summary,
        [
            "decision",
            "new_mechanism_input",
            "formal_proof_input",
            "selected_route",
            "goal_status",
            "supported_metric",
            "supported_speedup",
            "blocked_claims",
        ],
    )
    write_csv(INPUT_STATUS, inputs, ["input", "status", "path", "role"])
    write_csv(
        MECHANISM,
        mechanisms,
        ["candidate_input", "status", "evidence", "admission_gate", "action"],
    )
    write_csv(
        FORMAL,
        formal,
        ["proof_input", "status", "evidence", "required_before_code", "action"],
    )
    write_csv(PACKAGE, package, ["claim_or_task", "decision", "support", "boundary"])
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "gate", "failure_action"])
    write_text(
        COMMANDS,
        """# Stage338 Reproduction Commands

```powershell
python scripts\\build_stage338_new_mechanism_or_proof_intake.py
```

Stage338 is an intake gate. It does not modify the SAB hot path. It decides
whether the next step is admitted implementation, admitted formal proof, or
scoped paper/package work.
""",
    )

    write_text(
        REPORT,
        f"""# Stage338 New Mechanism Or Proof Intake Report

Decision: `{DECISION}`.

Stage338 consumes the Stage337 frontier correction and checks whether the
current worktree contains a new exact mechanism or a formal compact-state proof
that would justify additional SAB hot-path implementation. It finds neither, so
the next automatic route is a scoped paper/package refresh. This is intentional:
the loop continues with runnable/reproducible evidence instead of re-entering
theory or repeating closed implementations.

## Summary

{md_table(summary, ["decision", "new_mechanism_input", "formal_proof_input", "selected_route", "goal_status", "supported_speedup"])}

## Mechanism Intake

{md_table(mechanisms, ["candidate_input", "status", "admission_gate", "action"])}

## Formal Proof Intake

{md_table(formal, ["proof_input", "status", "required_before_code", "action"])}

## Package Route

{md_table(package, ["claim_or_task", "decision", "support", "boundary"])}

## Proof Gate

{md_table(proof, ["gate", "status", "metric", "value", "interpretation"])}
""",
    )

    write_text(
        DOC,
        f"""# Stage338 New Mechanism Or Proof Intake

Decision: `{DECISION}`.

The active goal is still not complete. Current evidence supports a scoped
complete-SAB `T_bootstrap/r` claim, but it does not prove theoretical optimality
for MAT-RLWE SAB and does not admit the compact selector route.

Stage338 therefore fixes the continuation rule:

- implement only after a concrete new load/store/count or backend primitive
  passes an isolated gate;
- reopen compact/structured SAB only after a closed-state proof covers
  neighbor/cross-body selector behavior;
- otherwise proceed with a scoped paper/parameter package using the existing
  complete-SAB evidence and negative ablations.

## Route Decision

{md_table(nextq, ["priority", "route", "entry_condition", "gate", "failure_action"])}

## Claim Boundary

{md_table(package, ["claim_or_task", "decision", "boundary"])}
""",
    )

    write_text(
        THEORY,
        """# Stage338 Route Decision Model

The research loop uses a three-way admission test.

1. New exact mechanism route:
   A new candidate must change a concrete count, load/store stream, backend
   primitive, or data movement invariant. Large profile share alone is not
   enough. The first gate is isolated equivalence and isolated microbench.

2. Formal compact route:
   A compact or structured state is allowed only if it is closed under every
   SAB selector and neighbor/cross-body transition used by the sparse schedule.
   The first gate is proof and finite checking, not production hot-path code.

3. Scoped package route:
   If neither input exists, the correct progress is to package the measured
   complete-SAB T_bootstrap/r result, resource/noise evidence, and negative
   ablations with explicit claim boundaries.

This model prevents both kinds of drift: claiming more than the data supports
and spending implementation time on already-closed candidates.
""",
    )

    write_text(
        PLAN,
        """# Stage339 Scoped Package Or New Mechanism Plan

Stage339 has two valid entry modes.

## Mode A: Scoped Package Refresh

Use this mode when no new mechanism or formal proof is available.

- update the paper claim matrix;
- bind every timing claim to commit, backend, CPU, parameter set, and raw log;
- include negative ablations from the closed-candidate audit;
- mark theoretical optimality, universal speedup, and compact SAB as not proven.

Gate: the package must not use stronger wording than the evidence supports.

## Mode B: New Mechanism Protocol

Use this mode only after a concrete mechanism is identified.

- write a count/load/store model before code;
- implement an isolated checker or microbench first;
- require equivalence before speed claims;
- run full SAB T_bootstrap/r A/B only after the isolated gate passes.

Gate: failure at isolated equivalence or isolated performance rejects the route
without SAB hot-path integration.
""",
    )

    append_once(
        GOAL,
        "<!-- stage338-new-mechanism-intake -->",
        f"""
<!-- stage338-new-mechanism-intake -->
- Stage338: `{DECISION}`. No current new exact mechanism or formal compact proof is present; next work is scoped package refresh unless a new gated mechanism/proof is supplied.
""",
    )
    append_once(
        ROADMAP,
        "<!-- stage338-new-mechanism-intake -->",
        f"""
<!-- stage338-new-mechanism-intake -->
## Stage338: New Mechanism Or Proof Intake

- Decision: `{DECISION}`.
- Gate: no SAB hot-path code without a concrete mechanism model or formal compact proof.
- Next: Stage339 scoped package refresh, or switch to the new mechanism/proof protocol if new evidence appears.
""",
    )
    append_once(
        HYPOTHESES,
        "H338_new_mechanism_or_proof_intake:",
        f"""
H338_new_mechanism_or_proof_intake:
  status: {DECISION}
  primary_metric: admissible_research_route
  evidence:
    - repro/stage338_new_mechanism_or_proof_intake/summary.csv
    - repro/stage338_new_mechanism_or_proof_intake/mechanism_intake.csv
    - repro/stage338_new_mechanism_or_proof_intake/formal_proof_intake.csv
    - repro/stage338_new_mechanism_or_proof_intake/package_route.csv
  conclusion: >
    No new exact mechanism or formal compact proof is present in the current
    worktree. Continue with scoped paper/parameter packaging, or admit future
    code only through the explicit new-mechanism/proof gates.
""",
    )
    append_once(
        MANIFEST,
        "<!-- stage338-new-mechanism-intake-manifest -->",
        """
<!-- stage338-new-mechanism-intake-manifest -->
- stage338_new_mechanism_or_proof_intake:
  - `docs/stage338_new_mechanism_or_proof_intake.md`
  - `theory_checks/stage338_route_decision_model.md`
  - `experiments/stage339_scoped_package_or_new_mechanism_plan.md`
  - `scripts/build_stage338_new_mechanism_or_proof_intake.py`
  - `repro/stage338_new_mechanism_or_proof_intake/`
""",
    )
    append_once(
        CHECKLIST,
        "<!-- stage338-new-mechanism-intake-checklist -->",
        f"""
<!-- stage338-new-mechanism-intake-checklist -->
- [x] Stage338 records `{DECISION}` and selects scoped package work unless a new mechanism/proof is supplied.
""",
    )
    append_run_log()
    artifact_index(
        [
            DOC,
            THEORY,
            PLAN,
            BUILDER,
            SUMMARY,
            INPUT_STATUS,
            MECHANISM,
            FORMAL,
            PACKAGE,
            PROOF,
            NEXT,
            REPORT,
            COMMANDS,
        ]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
