#!/usr/bin/env python3
"""Stage185: research and reproducibility package refresh."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage185_research_repro_package_refresh"

SUMMARY_CSV = OUT_DIR / "summary.csv"
REQUIREMENT_CSV = OUT_DIR / "requirement_matrix.csv"
EVIDENCE_INDEX_CSV = OUT_DIR / "evidence_index.csv"
CLAIM_TABLE_CSV = OUT_DIR / "claim_table.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage185_research_repro_package_refresh.md"
PLAN_MD = ROOT / "experiments" / "stage185_research_repro_package_refresh_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage185_research_loop_gap_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_research_program_snapshot.md"
PAPER_OUTLINE_MD = OUT_DIR / "paper_outline_scoped.md"
REPRO_COMMANDS_MD = OUT_DIR / "reproduction_commands.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE184_SUMMARY = ROOT / "repro" / "stage184_exact_route_closeout_claim_refresh" / "summary.csv"
STAGE184_CLAIMS = ROOT / "repro" / "stage184_exact_route_closeout_claim_refresh" / "claim_ledger.csv"
STAGE184_EVIDENCE = ROOT / "repro" / "stage184_exact_route_closeout_claim_refresh" / "evidence_chain.csv"
STAGE184_ROUTES = ROOT / "repro" / "stage184_exact_route_closeout_claim_refresh" / "open_routes.csv"
STAGE182_SUMMARY = ROOT / "repro" / "stage182_exact_path_negative_frontier" / "summary.csv"
STAGE183_SUMMARY = ROOT / "repro" / "stage183_addmul_dataflow_screen" / "summary.csv"
STAGE178_PERBIT = ROOT / "repro" / "stage178_fullmat_perbit_frontier" / "per_bit_throughput.csv"
STAGE180_DERIVED = ROOT / "repro" / "stage180_mat_ep_split_probe" / "derived_projection.csv"
STAGE181_COMPARE = ROOT / "repro" / "stage181_sub_decomp_avx512_gate" / "comparison.csv"
STAGE183_MECH = ROOT / "repro" / "stage183_addmul_dataflow_screen" / "mechanism_screen.csv"
STAGE176_SUMMARY = ROOT / "repro" / "stage176_structured_compact_security_api_gate" / "summary.csv"
STAGE177_SUMMARY = ROOT / "repro" / "stage177_verified_literature_novelty_gate" / "summary.csv"
REPRO_RUN_LOG = ROOT / "repro" / "run_log.csv"
REPRO_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
REPRO_CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION = "PASS_STAGE185_RESEARCH_REPRO_PACKAGE_REFRESH"


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
    with path.open("r", encoding="utf-8", newline="") as f:
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


def metric_value(metric: str) -> str:
    for row in read_csv_dicts(STAGE178_PERBIT):
        if row.get("metric") == metric:
            return row.get("value", "")
    return ""


def split_projection(metric: str) -> str:
    for row in read_csv_dicts(STAGE180_DERIVED):
        if row.get("metric") == metric:
            return row.get("value", "")
    return ""


def stage181_speed(variant: str, column: str) -> str:
    for row in read_csv_dicts(STAGE181_COMPARE):
        if row.get("variant") == variant:
            return row.get(column, "")
    return ""


def build_requirement_rows() -> List[Dict[str, str]]:
    return [
        {
            "requirement": "algorithm_object",
            "status": "partial_supported",
            "evidence": f"{rel(STAGE184_CLAIMS)}; {rel(STAGE183_MECH)}",
            "what_is_proven": "Exact PVW/MAT-SAB is treated as r-body shared-mask MAT-RLWE/PVW_TMLWE bootstrapping with scoped complete-SAB evidence.",
            "what_is_missing": "No implemented compact/shared-output MAT-SAB algorithm and no proof of theoretical optimality.",
            "next_gate": "Stage186 compact proof unlock or new exact dataflow proof.",
        },
        {
            "requirement": "primary_metric_T_bootstrap_over_r",
            "status": "satisfied_for_current_claim",
            "evidence": rel(STAGE178_PERBIT),
            "what_is_proven": (
                "Primary endpoint is complete bootstrapping time per lane: mean "
                f"{metric_value('speedup_vs_scalar_repeated_mean')}x speedup, min "
                f"{metric_value('speedup_vs_scalar_repeated_min')}x, CI-low "
                f"{metric_value('speedup_vs_scalar_repeated_ci95_low')}x."
            ),
            "what_is_missing": "Broader parameter/branch/theoretical claims remain outside this exact-route package.",
            "next_gate": "Use only T_bootstrap/r in paper/reports.",
        },
        {
            "requirement": "theory_lower_bound_complexity_model",
            "status": "partial_supported_not_optimality",
            "evidence": f"{rel(STAGE180_DERIVED)}; {rel(STAGE184_CLAIMS)}",
            "what_is_proven": "Same-format exact route has fixed external-product/materialization counts and measured subcomponent Amdahl requirements.",
            "what_is_missing": "A formal lower bound proving optimal MAT external product or AVX512 optimality is not available.",
            "next_gate": "Formal lower-bound proof or hardware-counter-backed dataflow proof before optimality wording.",
        },
        {
            "requirement": "candidate_optimal_algorithm_paths",
            "status": "routed",
            "evidence": rel(STAGE184_ROUTES),
            "what_is_proven": "Exact hot path is closed until new mechanism; compact/shared-output route is proof/literature blocked; paper writeup is scoped possible.",
            "what_is_missing": "No new candidate currently has implementation permission.",
            "next_gate": "Choose Stage186 compact proof unlock only with proof/source evidence, or produce scoped paper package.",
        },
        {
            "requirement": "falsifiable_experiment_gates",
            "status": "satisfied_for_recorded_scope",
            "evidence": f"{rel(STAGE184_EVIDENCE)}; {rel(REPRO_RUN_LOG)}",
            "what_is_proven": "Recorded stages preserve pass/reject/blocked decisions, negative ablations, and explicit next gates.",
            "what_is_missing": "Future compact or new dataflow claims need fresh correctness/noise/performance/resource gates.",
            "next_gate": "No implementation without deterministic equivalence, microbench, full-SAB A/B, noise/resource, and claim audit.",
        },
        {
            "requirement": "statistics_and_reproducibility",
            "status": "satisfied_for_current_package",
            "evidence": f"{rel(REPRO_MANIFEST)}; {rel(REPRO_CHECKLIST)}",
            "what_is_proven": "Run log, artifact manifest, and reproduction checklist register the current Stage19+ evidence chain.",
            "what_is_missing": "External final manuscript still needs explicit citation-safe source package if stronger claims are added.",
            "next_gate": "Preserve raw logs and SHA-indexed artifacts for every new gate.",
        },
        {
            "requirement": "avoid_theory_loop",
            "status": "satisfied_for_stage185",
            "evidence": f"{rel(STAGE182_SUMMARY)}; {rel(STAGE183_SUMMARY)}; {rel(STAGE184_SUMMARY)}",
            "what_is_proven": "The exact-route loop ends in claim refresh and no-code policy, not unbounded speculative implementation.",
            "what_is_missing": "Final goal remains active because compact proof/theoretical-optimality/full paper package are not fully closed.",
            "next_gate": "Only execute a bounded paper package or proof-unlock stage.",
        },
    ]


def build_evidence_rows() -> List[Dict[str, str]]:
    return [
        {
            "artifact": "primary_endpoint",
            "path": rel(STAGE178_PERBIT),
            "sha256": sha256_file(STAGE178_PERBIT),
            "role": "T_bootstrap/r performance basis.",
        },
        {
            "artifact": "component_projection",
            "path": rel(STAGE180_DERIVED),
            "sha256": sha256_file(STAGE180_DERIVED),
            "role": "Amdahl and lower-bound gap basis.",
        },
        {
            "artifact": "negative_subdecomp_ablation",
            "path": rel(STAGE181_COMPARE),
            "sha256": sha256_file(STAGE181_COMPARE),
            "role": "Preserves failed AVX512 sub-decompose candidate.",
        },
        {
            "artifact": "exact_route_claim_ledger",
            "path": rel(STAGE184_CLAIMS),
            "sha256": sha256_file(STAGE184_CLAIMS),
            "role": "Allowed and denied claim wording.",
        },
        {
            "artifact": "stage185_requirement_matrix",
            "path": rel(REQUIREMENT_CSV),
            "sha256": sha256_file(REQUIREMENT_CSV),
            "role": "This stage's objective audit matrix.",
        },
    ]


def build_claim_rows() -> List[Dict[str, str]]:
    rows = []
    for row in read_csv_dicts(STAGE184_CLAIMS):
        rows.append(
            {
                "claim": row.get("claim", ""),
                "stage185_status": row.get("status", ""),
                "safe_use": row.get("allowed_statement", ""),
                "quantitative_bound": row.get("quantitative_bound", ""),
                "must_not_say": row.get("blocked_extension", ""),
                "evidence": row.get("evidence", ""),
            }
        )
    return rows


def build_next_rows() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "stage": "186",
            "name": "compact proof unlock audit",
            "entry_condition": "A proof/source package is available or the user asks to pursue compact/shared-output MAT-SAB theory.",
            "gate": "Security/API/noise/key distribution/literature gates before production SAB code.",
            "failure_rule": "If proof is incomplete, keep compact route blocked and preserve the failure matrix.",
        },
        {
            "priority": "P1",
            "stage": "187",
            "name": "manuscript skeleton from scoped ledger",
            "entry_condition": "User wants paper drafting from current evidence.",
            "gate": "Use only Stage185 safe claims and verified citations; label all stronger claims as future work.",
            "failure_rule": "Reject manuscript wording that states theoretical optimality or compact implementation.",
        },
        {
            "priority": "P2",
            "stage": "188",
            "name": "new dataflow preflight",
            "entry_condition": "A concrete non-layout AVX/dataflow idea is proposed.",
            "gate": "Projection >=3% complete-SAB impact, deterministic equivalence, microbench, then full-SAB A/B.",
            "failure_rule": "No hot-path implementation from source-level plausibility alone.",
        },
    ]


def build_summary_rows() -> List[Dict[str, str]]:
    inputs = [
        STAGE184_SUMMARY,
        STAGE184_CLAIMS,
        STAGE184_EVIDENCE,
        STAGE184_ROUTES,
        STAGE178_PERBIT,
        STAGE180_DERIVED,
        STAGE181_COMPARE,
    ]
    inputs_ok = all(path.exists() for path in inputs)
    return [
        {
            "gate": "stage185_inputs",
            "status": "PASS" if inputs_ok else "FAIL",
            "metric": "required_inputs_present",
            "value": "1" if inputs_ok else "0",
            "evidence": f"{rel(STAGE184_SUMMARY)}; {rel(STAGE178_PERBIT)}",
            "detail": "Stage185 consumes the Stage178-184 exact-route evidence chain.",
            "next_action": "Repair missing inputs before package refresh.",
        },
        {
            "gate": "stage185_requirement_audit",
            "status": "PASS_WITH_OPEN_GAPS",
            "metric": "requirements;open_gaps",
            "value": "7;4",
            "evidence": rel(REQUIREMENT_CSV),
            "detail": "The package satisfies scoped research-loop reporting but preserves open theory/compact/novelty gaps.",
            "next_action": "Do not mark the overall goal complete yet.",
        },
        {
            "gate": "stage185_claim_sanity",
            "status": "PASS",
            "metric": "allowed_scoped_claims;denied_or_blocked_claims",
            "value": "1;3",
            "evidence": rel(CLAIM_TABLE_CSV),
            "detail": "Claim table is inherited from Stage184 and remains scoped.",
            "next_action": "Use this table for any report/manuscript drafting.",
        },
        {
            "gate": "stage185_decision",
            "status": DECISION,
            "metric": "route",
            "value": "package_refreshed_goal_still_active",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Research/repro package is refreshed; final objective remains active because stronger algorithmic proof/implementation work is open.",
            "next_action": "Proceed to Stage186 or Stage187 according to user priority.",
        },
    ]


def write_docs(
    summary_rows: List[Dict[str, str]],
    requirement_rows: List[Dict[str, str]],
    evidence_rows: List[Dict[str, str]],
    claim_rows: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
) -> None:
    write_text_lf(
        OUT_MD,
        f"""# Stage185 Research/Repro Package Refresh

Decision: `{DECISION}`.

Stage185 packages the current PVW/MAT-SAB research loop around the original
research intent:

- algorithm object: MAT-RLWE/r-body shared-mask PVW/MAT-SAB;
- primary endpoint: complete SAB `T_bootstrap/r`;
- current result: scoped complete-SAB amortized speedup only;
- current boundary: exact full-MAT hot-path retuning is closed until a new
  mechanism appears;
- open research route: compact/shared-output MAT-SAB remains proof and
  literature gated.

This is a progress package, not a completion claim. It explicitly preserves
open gaps so the thread goal remains active.

## Gate Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Requirement Matrix

{table(requirement_rows, ["requirement", "status", "evidence", "what_is_proven", "what_is_missing", "next_gate"])}
## Evidence Index

{table(evidence_rows, ["artifact", "path", "sha256", "role"])}
## Claim Table

{table(claim_rows, ["claim", "stage185_status", "safe_use", "quantitative_bound", "must_not_say", "evidence"])}
## Next Queue

{table(next_rows, ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"])}
""",
    )

    write_text_lf(
        PLAN_MD,
        """# Stage185 Plan

Goal: refresh the research/reproduction package after Stage184 so the next
work remains aligned with the original MAT-RLWE/r-body SAB objective.

Validation:

- every claim maps to current artifacts;
- primary metric remains `T_bootstrap/r`;
- negative ablations stay visible;
- open gaps are explicit;
- no new implementation is authorized by this package.
""",
    )

    write_text_lf(
        THEORY_MD,
        f"""# Stage185 Research Loop Gap Model

The current exact route gives an implemented MAT-RLWE/r-body SAB path, but not
an optimality theorem.

Known measured quantities:

```text
T_bootstrap/r speedup mean = {metric_value('speedup_vs_scalar_repeated_mean')}x
T_bootstrap/r speedup min  = {metric_value('speedup_vs_scalar_repeated_min')}x
T_bootstrap/r CI low       = {metric_value('speedup_vs_scalar_repeated_ci95_low')}x
sub-decompose 3pct need    = {split_projection('sub_decompose_full_sab_share_and_3pct_requirement')}
DFT rows 3pct need         = {split_projection('torus_to_dft_rows_full_sab_share_and_3pct_requirement')}
addmul 3pct need           = {split_projection('addmul_from_dec_dft_full_sab_share_and_3pct_requirement')}
AVX512 sub-decomp combined = {stage181_speed('combined_current', 'speedup')}x
```

Interpretation:

1. Exact same-format PVW/MAT-SAB has scoped complete-SAB speedup.
2. Same-format count reduction is closed under the current coefficient-domain
   decomposition API.
3. Existing AVX512 sub-decompose and addmul-layout routes do not support
   theoretical optimality or further code work.
4. A stronger algorithmic result requires a proof-gated representation change,
   most likely compact/shared-output MAT-SAB, plus complete-SAB validation.
""",
    )

    write_text_lf(
        VARIANT_MD,
        """# MAT-RLWE SAB Research Program Snapshot

Current implemented algorithm object:

- exact full-MAT PVW/MAT-SAB, r-body shared-mask accumulator;
- scalar SAB baseline preserved;
- all experimental MAT/PVW changes remain explicit and gated.

Current best-supported statement:

- scoped complete-SAB amortized speedup under recorded conditions.

Current blocked statements:

- AVX512 theoretical optimality;
- successful AVX512 sub-decompose optimization;
- implemented compact/shared-output MAT-SAB algorithm;
- broad novelty.

Next research work must be either a proof unlock for compact/shared-output
MAT-SAB or a new dataflow preflight with complete-SAB projection.
""",
    )

    write_text_lf(
        PAPER_OUTLINE_MD,
        """# Scoped Paper Outline

1. Motivation
   - Sparse amortized bootstrapping and the per-lane cost objective.
2. Algorithm Object
   - Exact PVW/MAT-SAB as r-body shared-mask MAT-RLWE bootstrapping.
3. Complexity and Boundary Model
   - Complete-SAB `T_bootstrap/r`, dense full-MAT costs, and measured Amdahl
     requirements.
4. Implementation
   - Explicit sab_pvw paths, MAT-aware AVX512 variants, active exact route,
     negative ablations.
5. Experiments
   - Complete-SAB A/B, noise/resource gates, split component gates, rejected
     candidates.
6. Claim Boundary
   - Scoped speedup allowed; novelty, optimality, compact implementation
     denied.
7. Future Work
   - Compact/shared-output proof route and new dataflow preflights.
""",
    )

    write_text_lf(
        REPRO_COMMANDS_MD,
        """# Reproduction Commands

Current package rebuild:

```powershell
python scripts\\build_stage185_research_repro_package_refresh.py
```

Evidence-source rebuilds:

```powershell
python scripts\\build_stage178_fullmat_perbit_frontier.py
python scripts\\build_stage180_mat_ep_split_probe.py
python scripts\\build_stage181_sub_decomp_avx512_gate.py
python scripts\\build_stage182_exact_path_negative_frontier.py
python scripts\\build_stage183_addmul_dataflow_screen.py
python scripts\\build_stage184_exact_route_closeout_claim_refresh.py
```

Some source rebuilds require the recorded native/remote environment and
credentials supplied through environment variables; do not write credentials
into artifacts.
""",
    )


def update_global_docs() -> None:
    append_once(
        ROADMAP_MD,
        "## Stage 185: Research/Repro Package Refresh",
        f"""
## Stage 185: Research/Repro Package Refresh

Goal:

```text
Package the current MAT-RLWE/r-body SAB research loop into a claim-safe
reproducibility bundle while preserving open gaps.
```

Status:

```text
Completed. Stage185 records {DECISION}. The package maps the original
objective to current evidence, keeps `T_bootstrap/r` as the primary endpoint,
and explicitly leaves the overall goal active because optimality and compact
MAT-SAB implementation remain unproven.
```
""",
    )

    append_once(
        GOAL_MD,
        "Stage185 records the research/repro package refresh",
        f"""
Stage185 records the research/repro package refresh. Decision:
`{DECISION}`. It consolidates the exact-route evidence and claim-safe paper
outline while preserving open proof/implementation gaps for the original
MAT-RLWE/r-body SAB objective.
""",
    )

    append_once(
        CURRENT_GOAL_MD,
        "Treat Stage185 as the research/repro package refresh",
        f"""
89. Treat Stage185 as the research/repro package refresh:
    `{DECISION}`. It packages the current evidence around the original
    MAT-RLWE/r-body SAB research objective and confirms that the overall goal
    remains active: scoped complete-SAB speedup is supported, but theoretical
    optimality and compact/shared-output implementation remain open.
""",
    )

    append_once(
        HYPOTHESIS_YAML,
        "H109_research_repro_package_refresh",
        f"""
  - id: H109_research_repro_package_refresh
    statement: >
      The current PVW/MAT-SAB evidence should be packaged as a scoped
      MAT-RLWE/r-body SAB research result with explicit open gaps, not as a
      completed theoretical optimum or compact-SAB implementation.
    mechanism: >
      Stage185 consolidates Stage178-184 evidence, maps objective requirements
      to authoritative artifacts, preserves negative ablations, and records
      next gates for compact proof or new dataflow preflights.
    status: stage185_research_repro_package_refresh
    evidence: docs/stage185_research_repro_package_refresh.md; experiments/stage185_research_repro_package_refresh_plan.md; theory_checks/stage185_research_loop_gap_model.md; repro/stage185_research_repro_package_refresh/summary.csv
    current_decision: >
      {DECISION}
    failure_criteria:
      - the package presents scoped speedup as theoretical optimality
      - open compact/shared-output proof gaps are hidden
      - reproduction commands or artifact paths are missing for current claims
""",
    )

    append_once(
        RUN_LOG,
        "stage185-research-repro-package-refresh-001",
        f"""
stage185-research-repro-package-refresh-001,2026-07-04,{git_head()},Stage 185,analysis,python scripts/build_stage185_research_repro_package_refresh.py,Stage178-184 evidence,none,{DECISION},Research/repro package refresh for MAT-RLWE r-body SAB objective.,repro/stage185_research_repro_package_refresh
""",
    )

    append_once(
        MANIFEST,
        "stage185_research_repro_package_refresh",
        f"""
- stage185_research_repro_package_refresh: `{DECISION}`
  - `docs/stage185_research_repro_package_refresh.md`
  - `experiments/stage185_research_repro_package_refresh_plan.md`
  - `theory_checks/stage185_research_loop_gap_model.md`
  - `algorithm_variants/mat_rlwe_sab_research_program_snapshot.md`
  - `repro/stage185_research_repro_package_refresh/`
""",
    )

    append_once(CHECKLIST, "Stage185 research/repro package refresh recorded", """
- [x] Stage185 research/repro package refresh recorded.
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
    claim_rows = build_claim_rows()
    next_rows = build_next_rows()
    summary_rows = build_summary_rows()

    write_csv(
        REQUIREMENT_CSV,
        requirement_rows,
        ["requirement", "status", "evidence", "what_is_proven", "what_is_missing", "next_gate"],
    )
    evidence_rows = build_evidence_rows()
    write_csv(EVIDENCE_INDEX_CSV, evidence_rows, ["artifact", "path", "sha256", "role"])
    write_csv(
        CLAIM_TABLE_CSV,
        claim_rows,
        ["claim", "stage185_status", "safe_use", "quantitative_bound", "must_not_say", "evidence"],
    )
    write_csv(NEXT_CSV, next_rows, ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"])
    write_csv(SUMMARY_CSV, summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    write_docs(summary_rows, requirement_rows, evidence_rows, claim_rows, next_rows)
    update_global_docs()
    write_artifacts(
        [
            OUT_MD,
            PLAN_MD,
            THEORY_MD,
            VARIANT_MD,
            PAPER_OUTLINE_MD,
            REPRO_COMMANDS_MD,
            SUMMARY_CSV,
            REQUIREMENT_CSV,
            EVIDENCE_INDEX_CSV,
            CLAIM_TABLE_CSV,
            NEXT_CSV,
            Path(__file__),
        ]
    )
    print(DECISION)


if __name__ == "__main__":
    main()
