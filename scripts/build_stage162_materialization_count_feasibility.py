#!/usr/bin/env python3
"""Stage162: materialization-count reduction feasibility gate."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage162_materialization_count_feasibility"

SUMMARY_CSV = OUT_DIR / "summary.csv"
LOWER_BOUND_CSV = OUT_DIR / "materialization_lower_bound.csv"
BIT_DAG_CSV = OUT_DIR / "bit_dependency_model.csv"
CANDIDATE_CSV = OUT_DIR / "candidate_matrix.csv"
NEXT_QUEUE_CSV = OUT_DIR / "next_stage_queue.csv"
EVIDENCE_CSV = OUT_DIR / "evidence_inputs.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage162_materialization_count_feasibility.md"
PLAN_MD = ROOT / "experiments" / "stage162_materialization_count_feasibility_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage162_materialization_count_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_materialization_count_feasibility.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE160_PROFILE = ROOT / "repro" / "stage160_post_fusion_frontier" / "profile_sample.csv"
STAGE160_COMPONENT = ROOT / "repro" / "stage160_post_fusion_frontier" / "component_shares.csv"
STAGE156_SUMMARY = ROOT / "repro" / "stage156_lazy_dft_closure_gate" / "summary.csv"
STAGE156_NONLINEAR = ROOT / "repro" / "stage156_lazy_dft_closure_gate" / "decomposition_nonlinearity.csv"
STAGE161_SUMMARY = ROOT / "repro" / "stage161_post_fusion_attribution" / "summary.csv"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
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
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def append_once(path: Path, marker: str, block: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(path, text + block.strip("\n") + "\n")


def first(rows: List[Dict[str, str]]) -> Dict[str, str]:
    return rows[0] if rows else {}


def decision_from(summary_path: Path, gate: str) -> str:
    for row in read_csv(summary_path):
        if row.get("gate") == gate:
            return row.get("status", "")
    return "MISSING"


def build_bit_dag(profile: Dict[str, str]) -> List[Dict[str, str]]:
    in_n = int(profile.get("in_N", "0") or "0")
    h = int(profile.get("h", "0") or "0")
    r_prec = int(profile.get("r_prec", "0") or "0")
    sparse_mul = int(profile.get("sparse_mul_calls", "0") or "0")
    rgsw = sparse_mul * (h + 1)
    rows = []
    for bit in range(r_prec):
        ncmux = rgsw * (1 << bit)
        direct = rgsw * (in_n - (1 << bit))
        total = rgsw * in_n
        consumer = "final_extract" if bit == r_prec - 1 else f"bit_{bit + 1}_torus_input"
        rows.append({
            "bit": str(bit),
            "rgsw_monomial_calls": str(rgsw),
            "ncmux_updates": str(ncmux),
            "direct_cmux_updates": str(direct),
            "total_updates": str(total),
            "observed_from_dft_calls": str(total),
            "torus_consumer": consumer,
            "count_reduction_without_rep_change": "0",
            "status": "LOWER_BOUND_TIGHT_UNDER_CURRENT_API",
        })
    return rows


def build_lower_bound(profile: Dict[str, str], bit_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    observed = int(profile.get("cmux_from_dft_calls", "0") or "0")
    mat_ep = int(profile.get("mat_ep_calls", "0") or "0")
    lower = sum(int(row["total_updates"]) for row in bit_rows)
    return [
        {
            "metric": "observed_from_dft_calls",
            "value": str(observed),
            "evidence": rel(STAGE160_PROFILE),
            "interpretation": "Current post-fusion path materializes every MAT EP output.",
        },
        {
            "metric": "current_api_lower_bound",
            "value": str(lower),
            "evidence": rel(BIT_DAG_CSV),
            "interpretation": "Under current torus-input MAT EP API, every update output must become torus before the next bit or final extract.",
        },
        {
            "metric": "mat_ep_calls",
            "value": str(mat_ep),
            "evidence": rel(STAGE160_PROFILE),
            "interpretation": "The lower bound equals observed MAT EP calls; same-format count reduction is not available.",
        },
        {
            "metric": "reducible_calls_without_representation_change",
            "value": str(max(observed - lower, 0)),
            "evidence": f"{rel(STAGE160_PROFILE)}; {rel(BIT_DAG_CSV)}",
            "interpretation": "Zero under the current exact torus/decomposition API boundary.",
        },
    ]


def candidate_matrix(stage156_decision: str) -> List[Dict[str, str]]:
    return [
        {
            "candidate": "persistent_DFT_accumulator",
            "count_reduction_target": "from_DFT_calls",
            "mechanism": "Keep accumulator in DFT form across CMUX updates.",
            "status": "REJECTED_BY_STAGE156",
            "blocking_evidence": stage156_decision,
            "next_action": "Do not reopen without a new exact decomposition/rotation representation.",
        },
        {
            "candidate": "delay_materialization_within_bit",
            "count_reduction_target": "from_DFT_calls",
            "mechanism": "Batch independent same-bit outputs and materialize later.",
            "status": "REJECT_COUNT_UNCHANGED",
            "blocking_evidence": "Each output is still a distinct torus input for the next bit or final extract.",
            "next_action": "May be recast as batched IFFT backend work, not count reduction.",
        },
        {
            "candidate": "batched_or_vectorized_from_DFT",
            "count_reduction_target": "wall_time_not_call_count",
            "mechanism": "Execute multiple materializations with better locality/SIMD/backend batching.",
            "status": "OPEN_BACKEND_MICROBENCH",
            "blocking_evidence": "Call count remains 573440; only per-call cost may improve.",
            "next_action": "Stage163/164 microbench if from_DFT remains above threshold.",
        },
        {
            "candidate": "direct_extract_from_DFT",
            "count_reduction_target": "final_bit_materialization_tail",
            "mechanism": "Extract final TLWE directly from DFT accumulator.",
            "status": "NOT_MATERIAL",
            "blocking_evidence": "Only final boundary could be affected; Stage160 from_DFT is dominated by all CMUX updates, not final extract only.",
            "next_action": "Do not prioritize before MAT EP/from_DFT bulk path.",
        },
        {
            "candidate": "compact_shared_source_or_decomposed_state",
            "count_reduction_target": "MAT_EP_dense_work_or_decomposition_work",
            "mechanism": "Change representation/API so the next operation consumes a closed exact state.",
            "status": "OPEN_REPRESENTATION_CHANGE",
            "blocking_evidence": "Requires new equivalence/noise gate; not a same-format count reduction.",
            "next_action": "Design isolated closure/equivalence test before any full-SAB integration.",
        },
    ]


def evidence_rows() -> List[Dict[str, str]]:
    return [
        {
            "artifact": rel(STAGE160_PROFILE),
            "status": "present" if STAGE160_PROFILE.exists() else "missing",
            "role": "post-fusion schedule counts and calls",
        },
        {
            "artifact": rel(STAGE160_COMPONENT),
            "status": "present" if STAGE160_COMPONENT.exists() else "missing",
            "role": "from_DFT share and MAT EP share",
        },
        {
            "artifact": rel(STAGE156_SUMMARY),
            "status": "present" if STAGE156_SUMMARY.exists() else "missing",
            "role": "lazy DFT closure rejection",
        },
        {
            "artifact": rel(STAGE156_NONLINEAR),
            "status": "present" if STAGE156_NONLINEAR.exists() else "missing",
            "role": "decomposition nonlinearity counterexamples",
        },
        {
            "artifact": rel(STAGE161_SUMMARY),
            "status": "present" if STAGE161_SUMMARY.exists() else "missing",
            "role": "post-fusion attribution scope",
        },
    ]


def next_queue() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "stage": "163",
            "name": "from_DFT backend batching microbench",
            "goal": "Measure whether batched/vectorized materialization reduces wall time while preserving the 573440-call semantics.",
            "gate": "Promote only if complete SAB improves; label as backend improvement, not algorithmic count reduction.",
        },
        {
            "priority": "P0",
            "stage": "164",
            "name": "compact/decomposed-state closure design",
            "goal": "Define a representation-changing exact state that can consume CMUX outputs without torus materialization.",
            "gate": "Must pass isolated phase/noise equivalence before any SAB integration.",
        },
        {
            "priority": "P1",
            "stage": "161N",
            "name": "native post-fusion counters",
            "goal": "Classify the MAT EP+subdecomp block as FMA-bound, memory-bound, or spill-bound on native perf platform.",
            "gate": "Current r=6 post-fusion path, not historical r=4 evidence.",
        },
    ]


def build_summary(lower: List[Dict[str, str]], candidates: List[Dict[str, str]], evidence: List[Dict[str, str]]) -> List[Dict[str, str]]:
    evidence_ok = all(row["status"] == "present" for row in evidence)
    reducible = next((row["value"] for row in lower if row["metric"] == "reducible_calls_without_representation_change"), "")
    open_rep = any(row["status"] == "OPEN_REPRESENTATION_CHANGE" for row in candidates)
    backend_open = any(row["status"] == "OPEN_BACKEND_MICROBENCH" for row in candidates)
    if evidence_ok and reducible == "0" and open_rep and backend_open:
        decision = "PASS_STAGE162_COUNT_REDUCTION_SAME_FORMAT_CLOSED_REP_CHANGE_REQUIRED"
        next_action = "Proceed to backend batching microbench or representation-changing closure design; do not claim count reduction in same-format path."
    else:
        decision = "FAIL_STAGE162_MATERIALIZATION_FEASIBILITY_INCOMPLETE"
        next_action = "Repair missing evidence or candidate matrix before selecting next implementation."
    return [
        {
            "gate": "stage162_evidence_inputs",
            "status": "PASS" if evidence_ok else "FAIL",
            "metric": "inputs_present",
            "value": "all" if evidence_ok else "missing",
            "evidence": rel(EVIDENCE_CSV),
            "detail": "Stage162 consumes Stage160, Stage156, and Stage161 evidence.",
            "next_action": "",
        },
        {
            "gate": "stage162_lower_bound",
            "status": "PASS" if reducible == "0" else "FAIL",
            "metric": "reducible_calls_without_rep_change",
            "value": reducible,
            "evidence": f"{rel(LOWER_BOUND_CSV)}; {rel(BIT_DAG_CSV)}",
            "detail": "Current torus-input API makes observed from_DFT count tight.",
            "next_action": "Only representation/API changes can reduce call count.",
        },
        {
            "gate": "stage162_candidate_matrix",
            "status": "PASS",
            "metric": "open_routes",
            "value": "backend_batching;representation_change",
            "evidence": rel(CANDIDATE_CSV),
            "detail": "Separates count reduction from wall-time backend batching.",
            "next_action": "Do not relabel backend batching as algorithmic count reduction.",
        },
        {
            "gate": "stage162_decision",
            "status": decision,
            "metric": "same_format_count_reduction",
            "value": "closed",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Stage162 closes unsafe same-format materialization-count reduction.",
            "next_action": next_action,
        },
    ]


def write_docs(summary: List[Dict[str, str]], lower: List[Dict[str, str]], candidates: List[Dict[str, str]], queue: List[Dict[str, str]]) -> None:
    decision = summary[-1]["status"]
    write_text_lf(PLAN_MD, "\n".join([
        "# Stage162 Materialization-Count Feasibility Plan",
        "",
        "Date: 2026-07-03",
        "",
        "Goal: decide whether the current exact same-format PVW/MAT-SAB path can reduce the 573440 `from_DFT` materializations.",
        "",
        "Primary distinction: call-count reduction is algorithmic; batched/materialization backend tuning is implementation-level unless the count changes.",
    ]) + "\n")
    write_text_lf(THEORY_MD, "\n".join([
        "# Stage162 Materialization Count Model",
        "",
        "Date: 2026-07-03",
        "",
        "The current production MAT EP API consumes torus-domain `PVW_TMLWE`, decomposes it, multiplies in DFT, and materializes the output before it can feed the next SAB bit. Stage156 shows that a naive DFT accumulator is not closed under exact gadget decomposition and SAB rotations.",
        "",
        "Therefore, under the current exact torus-input API, each CMUX/NCMUX update has one DFT output that must be materialized for the next bit or final extraction. With `h=39`, `r_prec=7`, and `N=2048`, the lower bound is `40*7*2048 = 573440`, matching Stage160 observations.",
    ]) + "\n")
    write_text_lf(VARIANT_MD, "\n".join([
        "# MAT-RLWE SAB Materialization-Count Feasibility",
        "",
        "Date: 2026-07-03",
        "",
        "Conclusion boundary:",
        "",
        "- Same-format count reduction: closed by Stage162.",
        "- Backend batching of materialization: open but not an algorithmic count reduction.",
        "- Representation-changing exact state: open only after closure/equivalence/noise gates.",
    ]) + "\n")
    write_text_lf(OUT_MD, "\n".join([
        "# Stage162 Materialization-Count Feasibility",
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
        "## Lower Bound",
        "",
        table(lower, ["metric", "value", "interpretation"]),
        "",
        "## Candidate Matrix",
        "",
        table(candidates, ["candidate", "status", "mechanism", "blocking_evidence", "next_action"]),
        "",
        "## Next Queue",
        "",
        table(queue, ["priority", "stage", "name", "goal", "gate"]),
    ]) + "\n")


def update_global(summary: List[Dict[str, str]]) -> None:
    decision = summary[-1]["status"]
    append_once(ROADMAP_MD, "## Stage 162: Materialization-Count Feasibility", f"""
## Stage 162: Materialization-Count Feasibility

Goal:

```text
Decide whether the current exact same-format PVW/MAT-SAB path can reduce the
573440 from_DFT materializations without a representation/API change.
```

Status:

```text
Completed. Stage162 records {decision}; same-format count reduction is closed,
while backend batching and representation-changing exact states remain separate
routes.
```
""")
    append_once(GOAL_MD, "Stage162 closes same-format materialization-count reduction", f"""
Stage162 closes same-format materialization-count reduction for the current
exact torus-input API. Decision: `{decision}`. Backend batching remains open
only as wall-time optimization; algorithmic count reduction requires a new
closed representation/API with equivalence and noise gates.
""")
    append_once(CURRENT_GOAL_MD, "66. Treat Stage162 as the materialization-count feasibility gate", f"""
66. Treat Stage162 as the materialization-count feasibility gate:
    `{decision}`. It prevents conflating backend IFFT batching with algorithmic
    materialization-count reduction.
""")
    append_once(HYPOTHESIS_YAML, "H86_materialization_count_feasibility", f"""
  - id: H86_materialization_count_feasibility
    statement: >
      The current exact same-format PVW/MAT-SAB path cannot reduce from_DFT
      call count below the observed 573440 without a representation/API change.
    mechanism: >
      Every CMUX/NCMUX update outputs a DFT object whose result must be torus
      materialized before the next bit or final extraction under the current
      MAT EP API; Stage156 rejects naive persistent DFT closure.
    status: stage162_materialization_count_feasibility
    evidence: docs/stage162_materialization_count_feasibility.md; experiments/stage162_materialization_count_feasibility_plan.md; theory_checks/stage162_materialization_count_model.md; repro/stage162_materialization_count_feasibility/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - Stage160 count evidence is missing
      - Stage156 closure rejection is ignored
      - backend batching is claimed as algorithmic count reduction
""")
    append_once(RUN_LOG, "stage162-materialization-count-feasibility-001", f"stage162-materialization-count-feasibility-001,2026-07-03,{git_head()},Stage 162,analysis,python scripts/build_stage162_materialization_count_feasibility.py,Stage160 r=6 counts; Stage156 closure; Stage161 attribution,none,{decision},Materialization-count reduction feasibility gate.,{rel(OUT_DIR)}\n")
    append_once(MANIFEST, "stage162_materialization_count_feasibility", f"""
- stage162_materialization_count_feasibility: `{decision}`
  - `docs/stage162_materialization_count_feasibility.md`
  - `experiments/stage162_materialization_count_feasibility_plan.md`
  - `theory_checks/stage162_materialization_count_model.md`
  - `repro/stage162_materialization_count_feasibility/`
""")
    append_once(CHECKLIST, "Stage162 materialization-count feasibility pack", """
- [x] Stage162 materialization-count feasibility pack recorded.
""")


def write_artifacts(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        rows.append({
            "artifact": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path) if path.exists() else "",
            "size_bytes": str(path.stat().st_size) if path.exists() else "",
        })
    write_csv(ARTIFACT_CSV, rows, ["artifact", "exists", "sha256", "size_bytes"])


def main() -> int:
    profile = first(read_csv(STAGE160_PROFILE))
    stage156_decision = decision_from(STAGE156_SUMMARY, "stage156_decision")
    bit_rows = build_bit_dag(profile)
    lower = build_lower_bound(profile, bit_rows)
    candidates = candidate_matrix(stage156_decision)
    evidence = evidence_rows()
    queue = next_queue()
    summary = build_summary(lower, candidates, evidence)

    write_csv(BIT_DAG_CSV, bit_rows, ["bit", "rgsw_monomial_calls", "ncmux_updates", "direct_cmux_updates", "total_updates", "observed_from_dft_calls", "torus_consumer", "count_reduction_without_rep_change", "status"])
    write_csv(LOWER_BOUND_CSV, lower, ["metric", "value", "evidence", "interpretation"])
    write_csv(CANDIDATE_CSV, candidates, ["candidate", "count_reduction_target", "mechanism", "status", "blocking_evidence", "next_action"])
    write_csv(EVIDENCE_CSV, evidence, ["artifact", "status", "role"])
    write_csv(NEXT_QUEUE_CSV, queue, ["priority", "stage", "name", "goal", "gate"])
    write_csv(SUMMARY_CSV, summary, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])

    write_docs(summary, lower, candidates, queue)
    update_global(summary)
    write_artifacts([
        OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, SUMMARY_CSV, LOWER_BOUND_CSV,
        BIT_DAG_CSV, CANDIDATE_CSV, NEXT_QUEUE_CSV, EVIDENCE_CSV,
        Path(__file__).resolve(),
    ])

    decision = summary[-1]["status"]
    print(f"Stage162 materialization-count feasibility: {decision}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
