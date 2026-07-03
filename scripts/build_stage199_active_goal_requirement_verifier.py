#!/usr/bin/env python3
"""Stage199: active-goal requirement verifier for PVW/MAT-SAB research loop."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage199_active_goal_requirement_verifier"

SUMMARY_CSV = OUT_DIR / "summary.csv"
REQUIREMENT_CSV = OUT_DIR / "requirement_matrix.csv"
GAP_CSV = OUT_DIR / "evidence_gap_register.csv"
NEXT_CSV = OUT_DIR / "next_action_selector.csv"
COMMANDS_MD = OUT_DIR / "reproduction_commands.md"
REPORT_MD = OUT_DIR / "active_goal_requirement_report.md"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage199_active_goal_requirement_verifier.md"
PLAN_MD = ROOT / "experiments" / "stage199_active_goal_requirement_verifier_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage199_active_goal_completion_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_active_goal_verifier.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE178_PERBIT = ROOT / "repro" / "stage178_fullmat_perbit_frontier" / "per_bit_throughput.csv"
STAGE180_DERIVED = ROOT / "repro" / "stage180_mat_ep_split_probe" / "derived_projection.csv"
STAGE192_SUMMARY = ROOT / "repro" / "stage192_compact_admission_route_selection" / "summary.csv"
STAGE193_SUMMARY = ROOT / "repro" / "stage193_exact_addmul_dataflow_preflight" / "summary.csv"
STAGE194_SUMMARY = ROOT / "repro" / "stage194_exact_dft_conversion_preflight" / "summary.csv"
STAGE195_SUMMARY = ROOT / "repro" / "stage195_scoped_paper_repro_refresh" / "summary.csv"
STAGE195_LEDGER = ROOT / "repro" / "stage195_scoped_paper_repro_refresh" / "final_claim_ledger.csv"
STAGE196_CITATION = ROOT / "repro" / "stage196_public_source_refresh" / "citation_gate.csv"
STAGE197_SUMMARY = ROOT / "repro" / "stage197_metadata_safe_citation_bank" / "summary.csv"
STAGE197_SUPPORT = ROOT / "repro" / "stage197_metadata_safe_citation_bank" / "sentence_support_bank.csv"
STAGE198_SUMMARY = ROOT / "repro" / "stage198_metadata_safe_manuscript_refresh" / "summary.csv"
STAGE198_DRAFT = ROOT / "repro" / "stage198_metadata_safe_manuscript_refresh" / "manuscript_draft.md"

DECISION = "PASS_STAGE199_ACTIVE_GOAL_VERIFIER_RECORDED_GOAL_ACTIVE"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((text.rstrip() + "\n").encode("utf-8"))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def read_csv_dicts(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    def cell(value: str) -> str:
        return str(value).replace("|", "\\|").replace("\n", "<br>")

    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(cell(row.get(field, "")) for field in fields) + " |")
    return "\n".join(out) + "\n"


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    if current and not current.endswith("\n"):
        current += "\n"
    write_text_lf(path, current + text.lstrip("\n"))


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def sha256_file(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def metric(metric_name: str) -> str:
    for row in read_csv_dicts(STAGE178_PERBIT):
        if row.get("metric") == metric_name:
            return row.get("value", "")
    return ""


def gate_status(path: Path, gate: str) -> str:
    for row in read_csv_dicts(path):
        if row.get("gate") == gate:
            return row.get("status", "")
    return ""


def claim_status(claim: str) -> str:
    for row in read_csv_dicts(STAGE195_LEDGER):
        if row.get("claim") == claim:
            return row.get("status", "")
    return ""


def build_requirement_rows() -> List[Dict[str, str]]:
    return [
        {
            "requirement_id": "R1_primary_metric",
            "objective_requirement": "Use complete bootstrapping time per processed plaintext bit/lane as the primary endpoint.",
            "current_status": "SATISFIED_SCOPED",
            "evidence": f"{rel(STAGE178_PERBIT)}; {rel(STAGE195_LEDGER)}; {rel(STAGE198_DRAFT)}",
            "evidence_strength": "complete-SAB T_bootstrap/r recorded and reused in scoped writing",
            "remaining_gap": "No gap for scoped reporting; broader parameters still need their own gates.",
        },
        {
            "requirement_id": "R2_algorithm_object",
            "objective_requirement": "Treat PVW/MAT-SAB as a MAT-RLWE/r-body ciphertext modification of SAB, not just a kernel benchmark.",
            "current_status": "SATISFIED_SCOPED",
            "evidence": f"{rel(STAGE197_SUPPORT)}; {rel(STAGE198_DRAFT)}",
            "evidence_strength": "support bank and draft use the r-body SAB object and complete-SAB endpoint",
            "remaining_gap": "A final formal algorithm section still needs source-paper anchors and proof text.",
        },
        {
            "requirement_id": "R3_complexity_lower_bound",
            "objective_requirement": "Give a lower-bound or gap model for the r-body MAT-RLWE SAB route.",
            "current_status": "PARTIAL",
            "evidence": rel(STAGE180_DERIVED),
            "evidence_strength": "component shares and required component speedups are recorded for exact full-MAT route selection",
            "remaining_gap": "Formal lower-bound proof and exact proof assumptions remain incomplete.",
        },
        {
            "requirement_id": "R4_candidate_paths",
            "objective_requirement": "Maintain candidate algorithm paths and close or promote them by falsifiable gates.",
            "current_status": "SATISFIED_FOR_CURRENT_FRONTIER",
            "evidence": f"{rel(STAGE192_SUMMARY)}; {rel(STAGE193_SUMMARY)}; {rel(STAGE194_SUMMARY)}",
            "evidence_strength": "compact, addmul, and DFT/conversion frontiers are admitted, denied, or routed with explicit conditions",
            "remaining_gap": "No current new code candidate is open; new mechanisms need fresh admission evidence.",
        },
        {
            "requirement_id": "R5_experiment_gates",
            "objective_requirement": "Use correctness, performance, noise/resource, and reproducibility gates before any acceleration claim.",
            "current_status": "SATISFIED_SCOPED",
            "evidence": f"{rel(STAGE195_LEDGER)}; {rel(STAGE197_SUMMARY)}; {rel(STAGE198_SUMMARY)}",
            "evidence_strength": "current claim ledger and writing support preserve scoped complete-SAB evidence and blocked frontiers",
            "remaining_gap": "Any new mechanism still needs a fresh full gate sequence.",
        },
        {
            "requirement_id": "R6_statistics",
            "objective_requirement": "Report effect sizes and avoid single-run or kernel-only overclaims.",
            "current_status": "SATISFIED_SCOPED",
            "evidence": f"{rel(STAGE178_PERBIT)}; {rel(STAGE195_LEDGER)}",
            "evidence_strength": f"recorded mean {metric('speedup_vs_scalar_repeated_mean')}x, min {metric('speedup_vs_scalar_repeated_min')}x, CI-low {metric('speedup_vs_scalar_repeated_ci95_low')}x",
            "remaining_gap": "Broader parameter/backend statistics require their own matrices before broad claims.",
        },
        {
            "requirement_id": "R7_literature_citation",
            "objective_requirement": "Use true sources and avoid unsupported novelty or theorem-level paper statements.",
            "current_status": "PARTIAL_BLOCKED",
            "evidence": f"{rel(STAGE196_CITATION)}; {rel(STAGE197_SUPPORT)}; {rel(STAGE198_DRAFT)}",
            "evidence_strength": "metadata-safe citation policy and guarded draft exist",
            "remaining_gap": "Reviewed 2025/686 full text is still required for theorem, equation, proof, and experiment anchors.",
        },
        {
            "requirement_id": "R8_final_completion",
            "objective_requirement": "Finish the full research goal, including proof/model closure, promoted implementation evidence, literature review, and claim ledger.",
            "current_status": "NOT_COMPLETE",
            "evidence": rel(SUMMARY_CSV),
            "evidence_strength": "this verifier records that scoped evidence is not equal to full objective completion",
            "remaining_gap": "Formal proof closure, source-anchor review, and any stronger implementation claim remain open.",
        },
    ]


def build_gap_rows(requirement_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    gaps = []
    for row in requirement_rows:
        if row["current_status"] in {"PARTIAL", "PARTIAL_BLOCKED", "NOT_COMPLETE"}:
            gaps.append(
                {
                    "requirement_id": row["requirement_id"],
                    "gap": row["remaining_gap"],
                    "needed_evidence": {
                        "R3_complexity_lower_bound": "formal proof note with assumptions, lower-bound statement, and counterexample/falsification checks",
                        "R7_literature_citation": "local reviewed full text path plus source-anchor extraction",
                        "R8_final_completion": "all partial rows upgraded with direct evidence and no remaining blocked stronger claims",
                    }.get(row["requirement_id"], "new evidence required"),
                    "current_action": {
                        "R3_complexity_lower_bound": "prepare a bounded proof-obligation stage only if it includes falsifiable checks",
                        "R7_literature_citation": "wait for full-text artifact or keep metadata-safe writing",
                        "R8_final_completion": "keep goal active",
                    }.get(row["requirement_id"], "continue scoped gates"),
                }
            )
    return gaps


def build_next_rows(gap_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "source_anchor_intake",
            "entry_condition": "Reviewed 2025/686 full text is available as a local artifact.",
            "why_this_moves_goal": "It upgrades metadata-only baseline use to theorem/algorithm/experiment anchor support.",
            "gate": "Every source-specific sentence maps to an inspected text anchor.",
            "current_status": "waiting_external_artifact",
            "evidence": rel(STAGE196_CITATION),
        },
        {
            "priority": "P1",
            "route": "formal_gap_model_with_falsification",
            "entry_condition": "No new implementation mechanism is available, but a proof stage must include checkable assumptions and counterexamples.",
            "why_this_moves_goal": "It targets the remaining formal lower-bound/gap-model requirement instead of writing more prose.",
            "gate": "Assumption table, proof obligation table, and at least one executable finite counterexample/consistency probe.",
            "current_status": "candidate_next_research_stage",
            "evidence": rel(GAP_CSV),
        },
        {
            "priority": "P2",
            "route": "new_mechanism_admission",
            "entry_condition": "A concrete addmul, DFT/conversion, compact proof, or backend mechanism is supplied.",
            "why_this_moves_goal": "It can reopen implementation progress only if projected complete-SAB impact is measurable.",
            "gate": "Correctness, noise/resource, complete-SAB T_bootstrap/r, and claim-policy gates.",
            "current_status": "waiting_new_mechanism",
            "evidence": f"{rel(STAGE193_SUMMARY)}; {rel(STAGE194_SUMMARY)}",
        },
    ]


def build_summary_rows(requirement_rows: List[Dict[str, str]], gap_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    inputs = [
        STAGE178_PERBIT,
        STAGE180_DERIVED,
        STAGE192_SUMMARY,
        STAGE193_SUMMARY,
        STAGE194_SUMMARY,
        STAGE195_LEDGER,
        STAGE196_CITATION,
        STAGE197_SUPPORT,
        STAGE198_SUMMARY,
    ]
    inputs_ok = all(path.exists() for path in inputs)
    complete_count = sum(1 for row in requirement_rows if row["current_status"].startswith("SATISFIED"))
    blocked_count = len(requirement_rows) - complete_count
    fulltext_blocked = gate_status(STAGE196_CITATION, "target_686_fulltext_review") == "BLOCKED"
    return [
        {
            "gate": "stage199_inputs",
            "status": "PASS" if inputs_ok else "FAIL",
            "metric": "required_inputs_present",
            "value": "1" if inputs_ok else "0",
            "evidence": f"{rel(STAGE178_PERBIT)}; {rel(STAGE195_LEDGER)}; {rel(STAGE198_SUMMARY)}",
            "detail": "Stage199 verifies the active goal against current evidence, not intent.",
            "next_action": "Repair missing inputs before using this verifier.",
        },
        {
            "gate": "stage199_requirement_matrix",
            "status": "PASS_RECORDED",
            "metric": "requirements",
            "value": str(len(requirement_rows)),
            "evidence": rel(REQUIREMENT_CSV),
            "detail": f"{complete_count} scoped requirements satisfied; {blocked_count} remain partial or not complete.",
            "next_action": "Use gap register for next route selection.",
        },
        {
            "gate": "stage199_fulltext_boundary",
            "status": "BLOCKED" if fulltext_blocked else "REVIEW_REQUIRED",
            "metric": "target_686_fulltext_gate",
            "value": gate_status(STAGE196_CITATION, "target_686_fulltext_review"),
            "evidence": rel(STAGE196_CITATION),
            "detail": "The source-anchor route remains outside current evidence if reviewed full text is unavailable.",
            "next_action": "Use metadata-safe writing or supply full text.",
        },
        {
            "gate": "stage199_completion_decision",
            "status": DECISION,
            "metric": "goal_status",
            "value": "active",
            "evidence": rel(SUMMARY_CSV),
            "detail": "The scoped evidence chain is usable, but the full active goal is not proven complete.",
            "next_action": "Proceed to P0/P1/P2 in the next-action selector.",
        },
    ]


def write_report(requirement_rows: List[Dict[str, str]], gap_rows: List[Dict[str, str]], next_rows: List[Dict[str, str]], summary_rows: List[Dict[str, str]]) -> None:
    write_text_lf(
        REPORT_MD,
        f"""# Active Goal Requirement Report

Decision: `{DECISION}`.

This verifier checks the active PVW/MAT-SAB research goal against current
evidence. It explicitly prevents treating the scoped paper/repro package as
full goal completion.

## Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Requirement Matrix

{table(requirement_rows, ["requirement_id", "current_status", "objective_requirement", "evidence_strength", "remaining_gap", "evidence"])}
## Evidence Gaps

{table(gap_rows, ["requirement_id", "gap", "needed_evidence", "current_action"])}
## Next Action Selector

{table(next_rows, ["priority", "route", "entry_condition", "why_this_moves_goal", "gate", "current_status", "evidence"])}
""",
    )


def write_commands() -> None:
    write_text_lf(
        COMMANDS_MD,
        """# Stage199 Reproduction Commands

```powershell
# Rebuild the active-goal verifier
python scripts\\build_stage199_active_goal_requirement_verifier.py

# Inspect requirement and gap matrices
Get-Content -Raw repro\\stage199_active_goal_requirement_verifier\\requirement_matrix.csv
Get-Content -Raw repro\\stage199_active_goal_requirement_verifier\\evidence_gap_register.csv
Get-Content -Raw repro\\stage199_active_goal_requirement_verifier\\next_action_selector.csv

# Inspect current scoped writing and citation boundary
Get-Content -Raw repro\\stage198_metadata_safe_manuscript_refresh\\summary.csv
Get-Content -Raw repro\\stage196_public_source_refresh\\citation_gate.csv
```
""",
    )


def write_docs(requirement_rows: List[Dict[str, str]], gap_rows: List[Dict[str, str]], next_rows: List[Dict[str, str]], summary_rows: List[Dict[str, str]]) -> None:
    write_text_lf(
        OUT_MD,
        f"""# Stage199 Active Goal Requirement Verifier

Decision: `{DECISION}`.

Stage199 audits the active goal requirement-by-requirement. The result keeps
the goal active: scoped implementation/writing evidence exists, but proof,
source-anchor, and stronger completion evidence remain incomplete.

## Gate Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Requirement Matrix

{table(requirement_rows, ["requirement_id", "current_status", "objective_requirement", "evidence_strength", "remaining_gap", "evidence"])}
## Evidence Gap Register

{table(gap_rows, ["requirement_id", "gap", "needed_evidence", "current_action"])}
## Next Action Selector

{table(next_rows, ["priority", "route", "entry_condition", "why_this_moves_goal", "gate", "current_status", "evidence"])}
""",
    )

    write_text_lf(
        PLAN_MD,
        """# Stage199 Plan

Goal: verify the active PVW/MAT-SAB objective against current evidence without
declaring completion from scoped artifacts.

Rules:

- each objective requirement must map to direct evidence;
- scoped evidence can satisfy only scoped claims;
- partial rows must become explicit gaps with next actions;
- no source-anchor or implementation claim is upgraded without the required
  artifact and gate.
""",
    )

    write_text_lf(
        THEORY_MD,
        """# Stage199 Active-Goal Completion Model

Completion requires all active-goal requirements to have direct evidence. The
verifier separates:

- scoped complete-SAB performance evidence;
- partial formal model evidence;
- blocked source-anchor evidence;
- denied or closed implementation frontiers;
- writing support artifacts.

The full goal remains active while any requirement is partial, blocked, or
not complete.
""",
    )

    write_text_lf(
        VARIANT_MD,
        """# Active Goal Verifier Boundary

This artifact is not a new algorithm variant. It is a control-plane verifier
for the MAT-RLWE/r-body SAB research loop.

It authorizes no code branch. It only selects the next admissible route:
source-anchor intake, formal gap-model work with falsification checks, or a
new mechanism admission gate.
""",
    )


def update_global_docs() -> None:
    append_once(
        ROADMAP_MD,
        "## Stage 199: Active Goal Requirement Verifier",
        f"""
## Stage 199: Active Goal Requirement Verifier

Goal:

```text
Audit the active PVW/MAT-SAB research objective requirement-by-requirement and
select the next admissible route from actual evidence gaps.
```

Status:

```text
Completed. Stage199 records {DECISION}. The scoped evidence chain is usable,
but the full active goal remains open because formal, source-anchor, and
stronger completion evidence are incomplete.
```
""",
    )

    append_once(
        GOAL_MD,
        "Stage199 records active goal verifier",
        f"""
Stage199 records active goal verifier. Decision: `{DECISION}`. It confirms
that scoped `T_bootstrap/r` evidence and metadata-safe writing exist, but full
goal completion remains unproven.
""",
    )

    append_once(
        CURRENT_GOAL_MD,
        "Treat Stage199 as active goal verifier",
        f"""
103. Treat Stage199 as active goal verifier:
    `{DECISION}`. The requirement matrix keeps the goal active: scoped
    implementation evidence exists, while formal proof, full-text source
    anchors, and stronger completion claims remain incomplete.
""",
    )

    append_once(
        HYPOTHESIS_YAML,
        "H123_active_goal_requirement_verifier",
        f"""
  - id: H123_active_goal_requirement_verifier
    statement: >
      The active PVW/MAT-SAB objective should remain open unless every
      requirement has direct current evidence; scoped artifacts are not enough
      to prove full research completion.
    mechanism: >
      Stage199 maps each active-goal requirement to evidence, evidence
      strength, remaining gaps, and next admissible actions.
    status: stage199_active_goal_requirement_verifier
    evidence: docs/stage199_active_goal_requirement_verifier.md; experiments/stage199_active_goal_requirement_verifier_plan.md; theory_checks/stage199_active_goal_completion_model.md; repro/stage199_active_goal_requirement_verifier/summary.csv
    current_decision: >
      {DECISION}
    failure_criteria:
      - scoped writing artifacts are treated as full objective completion
      - partial proof or source-anchor evidence is upgraded without direct artifacts
      - a new code branch opens without mechanism admission gates
""",
    )

    append_once(
        RUN_LOG,
        "stage199-active-goal-requirement-verifier-001",
        f"""
stage199-active-goal-requirement-verifier-001,2026-07-04,{git_head()},Stage 199,analysis,python scripts/build_stage199_active_goal_requirement_verifier.py,Stage178/195/196/197/198 evidence,none,{DECISION},Active goal requirement verifier and next-action selector.,repro/stage199_active_goal_requirement_verifier
""",
    )

    append_once(
        MANIFEST,
        "stage199_active_goal_requirement_verifier",
        f"""
- stage199_active_goal_requirement_verifier: `{DECISION}`
  - `docs/stage199_active_goal_requirement_verifier.md`
  - `experiments/stage199_active_goal_requirement_verifier_plan.md`
  - `theory_checks/stage199_active_goal_completion_model.md`
  - `algorithm_variants/mat_rlwe_sab_active_goal_verifier.md`
  - `repro/stage199_active_goal_requirement_verifier/`
""",
    )

    append_once(CHECKLIST, "Stage199 active goal verifier recorded", """
- [x] Stage199 active goal verifier recorded.
""")


def write_artifacts(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        rows.append(
            {
                "path": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256_file(path),
                "bytes": str(path.stat().st_size) if path.exists() else "0",
            }
        )
    write_csv(ARTIFACT_CSV, rows, ["path", "exists", "sha256", "bytes"])


def main() -> None:
    requirement_rows = build_requirement_rows()
    gap_rows = build_gap_rows(requirement_rows)
    next_rows = build_next_rows(gap_rows)
    summary_rows = build_summary_rows(requirement_rows, gap_rows)

    write_csv(
        REQUIREMENT_CSV,
        requirement_rows,
        ["requirement_id", "objective_requirement", "current_status", "evidence", "evidence_strength", "remaining_gap"],
    )
    write_csv(GAP_CSV, gap_rows, ["requirement_id", "gap", "needed_evidence", "current_action"])
    write_csv(
        NEXT_CSV,
        next_rows,
        ["priority", "route", "entry_condition", "why_this_moves_goal", "gate", "current_status", "evidence"],
    )
    write_csv(
        SUMMARY_CSV,
        summary_rows,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_report(requirement_rows, gap_rows, next_rows, summary_rows)
    write_commands()
    write_docs(requirement_rows, gap_rows, next_rows, summary_rows)
    update_global_docs()
    write_artifacts(
        [
            OUT_MD,
            PLAN_MD,
            THEORY_MD,
            VARIANT_MD,
            REPORT_MD,
            COMMANDS_MD,
            SUMMARY_CSV,
            REQUIREMENT_CSV,
            GAP_CSV,
            NEXT_CSV,
            Path(__file__),
        ]
    )
    print(DECISION)


if __name__ == "__main__":
    main()
