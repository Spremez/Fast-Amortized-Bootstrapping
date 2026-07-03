#!/usr/bin/env python3
"""Stage172: close out the current PVW/MAT-SAB frontier."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage172_frontier_closeout"

SUMMARY_CSV = OUT_DIR / "summary.csv"
INPUTS_CSV = OUT_DIR / "evidence_inputs.csv"
CLAIMS_CSV = OUT_DIR / "claim_matrix.csv"
FRONTIER_CSV = OUT_DIR / "engineering_frontier.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage172_frontier_closeout.md"
PLAN_MD = ROOT / "experiments" / "stage172_frontier_closeout_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage172_claim_boundary.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_frontier_closeout.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE169_SUMMARY = ROOT / "repro" / "stage169_cb5_native_repeated_r6_gate" / "summary.csv"
STAGE169_AGG = ROOT / "repro" / "stage169_cb5_native_repeated_r6_gate" / "aggregate.csv"
STAGE170_SUMMARY = ROOT / "repro" / "stage170_native_split_counter_microbench" / "summary.csv"
STAGE170_RUN = ROOT / "repro" / "stage170_native_split_counter_microbench" / "run_metrics.csv"
STAGE170_DERIVED = ROOT / "repro" / "stage170_native_split_counter_microbench" / "derived_counter_ratios.csv"
STAGE171_SUMMARY = ROOT / "repro" / "stage171_structured_compact_keygen_feasibility" / "summary.csv"
STAGE171_PROJECTION = ROOT / "repro" / "stage171_structured_compact_keygen_feasibility" / "speed_projection.csv"
STAGE171_PROOF = ROOT / "repro" / "stage171_structured_compact_keygen_feasibility" / "proof_obligations.csv"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)
    normalized = [{field: row.get(field, "") for field in fields} for row in row_list]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    def cell(value: str) -> str:
        return str(value).replace("|", "\\|").replace("\n", "<br>")

    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(cell(row.get(field, "")) for field in fields) + " |")
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


def decision_from(path: Path) -> str:
    for row in read_csv(path):
        if row.get("gate", "").endswith("decision"):
            return row.get("status", "")
    return "MISSING"


def agg_value(metric: str, field: str) -> str:
    for row in read_csv(STAGE169_AGG):
        if row.get("metric") == metric:
            return row.get(field, "")
    return ""


def run_value(path: Path, variant: str, field: str) -> str:
    for row in read_csv(path):
        if row.get("variant") == variant:
            return row.get(field, "")
    return ""


def derived_value(variant: str, metric: str) -> str:
    for row in read_csv(STAGE170_DERIVED):
        if row.get("variant") == variant and row.get("metric") == metric:
            return row.get("value", "")
    return ""


def projection_value(field: str) -> str:
    for row in read_csv(STAGE171_PROJECTION):
        if row.get("r") == "6":
            return row.get(field, "")
    return ""


def build_inputs() -> List[Dict[str, str]]:
    paths = [
        ("stage169_native_repeated_full_sab", STAGE169_SUMMARY, decision_from(STAGE169_SUMMARY)),
        ("stage170_native_split_counters", STAGE170_SUMMARY, decision_from(STAGE170_SUMMARY)),
        ("stage171_structured_compact_feasibility", STAGE171_SUMMARY, decision_from(STAGE171_SUMMARY)),
    ]
    return [
        {
            "source": name,
            "path": rel(path),
            "present": "yes" if path.exists() else "no",
            "decision": decision,
        }
        for name, path, decision in paths
    ]


def build_claims() -> List[Dict[str, str]]:
    speed_mean = agg_value("speedup_vs_scalar_repeated", "mean")
    speed_min = agg_value("speedup_vs_scalar_repeated", "min")
    speed_ci_low = agg_value("speedup_vs_scalar_repeated", "ci95_low")
    mat_us = run_value(STAGE170_RUN, "mat_ep_subdecomp", "per_call_us")
    dft_us = run_value(STAGE170_RUN, "from_dft_materialize", "per_call_us")
    compact_upper = projection_value("upper_component_speedup")
    return [
        {
            "claim": "current exact r=6 PVW/MAT-SAB improves complete-SAB amortized throughput on CB5",
            "status": "ALLOWED_ENGINEERING_CLAIM",
            "evidence": rel(STAGE169_AGG),
            "quantitative_value": f"mean={speed_mean};min={speed_min};ci95_low={speed_ci_low}",
            "boundary": "Metric is T_bootstrap/r versus repeated scalar SAB under spqlios_avx512 on CB5; not all parameters/backends.",
        },
        {
            "claim": "MAT EP/subdecomp and from_DFT are both material component costs",
            "status": "ALLOWED_ATTRIBUTION",
            "evidence": rel(STAGE170_RUN),
            "quantitative_value": f"mat_ep_us={mat_us};from_dft_us={dft_us}",
            "boundary": "Component microbench/counter attribution only; not a replacement for full-SAB A/B.",
        },
        {
            "claim": "from_DFT locality remains a concrete engineering frontier",
            "status": "ALLOWED_NEXT_EXPERIMENT",
            "evidence": rel(STAGE170_DERIVED),
            "quantitative_value": f"cache_miss_rate={derived_value('from_dft_materialize', 'cache_miss_rate')};ls_fp512={derived_value('from_dft_materialize', 'load_store_to_fp512_ratio')}",
            "boundary": "Needs bounded microbench and full-SAB promotion gate.",
        },
        {
            "claim": "structured compact could offer larger algorithmic gain",
            "status": "MOTIVATING_UPPER_BOUND_ONLY",
            "evidence": rel(STAGE171_PROJECTION),
            "quantitative_value": f"r6_component_upper={compact_upper}",
            "boundary": "Requires keygen/phase/noise/security/API proof before implementation or paper claim.",
        },
        {
            "claim": "current MAT AVX512 implementation is theoretically optimal",
            "status": "BLOCKED",
            "evidence": f"{rel(STAGE170_DERIVED)};{rel(STAGE171_PROOF)}",
            "quantitative_value": "not_established",
            "boundary": "Counters and negative variants do not prove a lower bound.",
        },
        {
            "claim": "compact/shared-output SAB is implemented and accelerates full SAB",
            "status": "BLOCKED",
            "evidence": rel(STAGE171_PROOF),
            "quantitative_value": "proof_obligations_open=5",
            "boundary": "No structured keygen implementation, noise run, or full-SAB benchmark exists.",
        },
        {
            "claim": "paper-level novelty is established",
            "status": "BLOCKED_LITERATURE_AND_PROOF",
            "evidence": rel(STAGE171_PROOF),
            "quantitative_value": "not_established",
            "boundary": "Requires real literature matrix, proof status, ablations, and reproducibility package.",
        },
    ]


def build_frontier() -> List[Dict[str, str]]:
    return [
        {
            "rank": "P0",
            "frontier": "from_DFT locality and materialization cost",
            "why_now": "Stage170 shows from_DFT is about 35.21 us/call with high cache-miss and load/store-to-FP512 ratios.",
            "next_gate": "Stage174 bounded from_DFT locality microbench; promote only with full-SAB A/B.",
            "risk": "Backend-only wins may not move complete SAB if MAT EP or sparse schedule remains dominant.",
        },
        {
            "rank": "P1",
            "frontier": "structured compact keygen proof route",
            "why_now": "Stage171 gives an r=6 component upper bound but leaves five proof obligations open.",
            "next_gate": "Stage173 formal equations plus finite/noise toy; no production code before proof.",
            "risk": "May require a new security assumption or fail closed-state/API constraints.",
        },
        {
            "rank": "P2",
            "frontier": "full-SAB repeated statistics after any promoted variant",
            "why_now": "Stage169 is the current complete-SAB endpoint; every new change must return to it.",
            "next_gate": "Native no-perf repeated A/B with T_bootstrap/r, correctness, and resource reporting.",
            "risk": "Microbench speedups can disappear at SAB schedule level.",
        },
    ]


def build_next_queue() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "stage": "174",
            "name": "from_DFT locality experiment",
            "entry_condition": "Stage172 selects a concrete non-proof-loop engineering frontier from Stage170 counters.",
            "gate": "Design one bounded locality/layout/scratch candidate; require exactness, microbench win, then full-SAB A/B.",
            "failure_rule": "If microbench is neutral or full-SAB A/B does not improve, reject/neutral and do not keep tuning blindly.",
        },
        {
            "priority": "P1",
            "stage": "173",
            "name": "structured compact formal phase/noise toy",
            "entry_condition": "Only if the project explicitly pursues new keygen/security proof work.",
            "gate": "Formal equations plus finite/noise toy checks for compact distribution.",
            "failure_rule": "If equations do not close, compact route remains blocked.",
        },
        {
            "priority": "P2",
            "stage": "175",
            "name": "full-SAB claim refresh",
            "entry_condition": "After Stage174 or Stage173 produces a promotable variant.",
            "gate": "Repeat Stage169-style native full-SAB A/B and update claim matrix.",
            "failure_rule": "No complete-SAB claim from microbench-only evidence.",
        },
    ]


def decide(inputs: List[Dict[str, str]]) -> str:
    if any(row["present"] != "yes" for row in inputs):
        return "BLOCKED_STAGE172_MISSING_INPUT"
    return "PASS_STAGE172_FRONTIER_CLOSEOUT_RECORDED"


def build_summary(decision: str, inputs: List[Dict[str, str]], claims: List[Dict[str, str]]) -> List[Dict[str, str]]:
    blocked = sum(1 for row in claims if row["status"].startswith("BLOCKED"))
    allowed = sum(1 for row in claims if row["status"].startswith("ALLOWED"))
    return [
        {
            "gate": "stage172_inputs",
            "status": "PASS" if all(row["present"] == "yes" for row in inputs) else "BLOCKED",
            "metric": "input_stages",
            "value": ";".join(row["source"] for row in inputs if row["present"] == "yes"),
            "evidence": rel(INPUTS_CSV),
            "detail": "Stage172 consumes Stage169 complete-SAB stats, Stage170 split counters, and Stage171 proof-route status.",
            "next_action": "Repair missing input before claim refresh.",
        },
        {
            "gate": "stage172_claim_boundary",
            "status": "PASS",
            "metric": "allowed;blocked",
            "value": f"{allowed};{blocked}",
            "evidence": rel(CLAIMS_CSV),
            "detail": "Allowed complete-SAB engineering claim is separated from blocked optimality/compact/paper claims.",
            "next_action": "Use this matrix when writing reports or deciding next stages.",
        },
        {
            "gate": "stage172_next_route",
            "status": "PASS",
            "metric": "next_engineering_stage",
            "value": "Stage174_from_DFT_locality",
            "evidence": rel(NEXT_CSV),
            "detail": "Near-term automatic work should use a bounded microbench/full-SAB loop, not open-ended proof work.",
            "next_action": "Run Stage174 unless the user explicitly prioritizes Stage173 proof route.",
        },
        {
            "gate": "stage172_decision",
            "status": decision,
            "metric": "frontier_closeout",
            "value": "recorded",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Stage172 closes the Stage169-171 evidence loop and prevents claim drift.",
            "next_action": "Proceed to Stage174 engineering loop or Stage173 proof loop with explicit scope.",
        },
    ]


def artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        rows.append({
            "path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path) if path.exists() and path.is_file() else "",
            "bytes": str(path.stat().st_size) if path.exists() and path.is_file() else "",
        })
    write_csv(ARTIFACT_CSV, rows, ["path", "exists", "sha256", "bytes"])


def write_docs(
    decision: str,
    summary: List[Dict[str, str]],
    inputs: List[Dict[str, str]],
    claims: List[Dict[str, str]],
    frontier: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
) -> None:
    summary_fields = ["gate", "status", "metric", "value", "evidence", "detail", "next_action"]
    input_fields = ["source", "path", "present", "decision"]
    claim_fields = ["claim", "status", "evidence", "quantitative_value", "boundary"]
    frontier_fields = ["rank", "frontier", "why_now", "next_gate", "risk"]
    next_fields = ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"]

    write_text_lf(OUT_MD, f"""# Stage172 Frontier Closeout

Decision: `{decision}`.

Stage172 consolidates the current evidence loop:

- Stage169 is the complete-SAB throughput endpoint.
- Stage170 is component/counter attribution.
- Stage171 is a proof-route boundary for structured compact keygen.

The project can currently claim complete-SAB amortized throughput improvement
for the current exact r=6 PVW/MAT-SAB path on CB5. It cannot claim theoretical
optimality, implemented compact SAB, or paper-level novelty yet.

## Gate Summary

{table(summary, summary_fields)}

## Evidence Inputs

{table(inputs, input_fields)}

## Claim Matrix

{table(claims, claim_fields)}

## Frontier

{table(frontier, frontier_fields)}

## Next Queue

{table(next_rows, next_fields)}
""")

    write_text_lf(PLAN_MD, """# Stage172 Validation Plan

Goal: close the current Stage169-171 loop without making unsupported claims.

Inputs:

- Stage169 native repeated full-SAB A/B;
- Stage170 native split component counters;
- Stage171 structured compact proof-route gate.

Acceptance:

- every input artifact is present;
- claim matrix separates allowed engineering claims from blocked optimality,
  compact, and paper-level claims;
- next stage is bounded by a correctness/performance gate.
""")

    write_text_lf(THEORY_MD, """# Stage172 Claim Boundary

Use the following boundary:

```text
Complete-SAB speedup claim requires complete-SAB A/B evidence.
Component counters explain bottlenecks but do not prove complete-SAB speedup.
Structured compact projection motivates proof work but does not implement SAB.
Theoretical optimality requires a lower-bound argument, not just counters.
Paper novelty requires real literature, proof status, and ablations.
```

Therefore the near-term engineering route is a bounded from_DFT locality
experiment, while the higher-risk algorithmic route is a separate structured
compact keygen proof track.
""")

    write_text_lf(VARIANT_MD, f"""# PVW/MAT-SAB Frontier Closeout

This artifact defines no production variant. It records the current claim and
route boundary.

Decision:

```text
{decision}
```

Current complete-SAB endpoint:

```text
Stage169 native repeated T_bootstrap/r speedup versus repeated scalar SAB.
```

Next automatic engineering route:

```text
Stage174 from_DFT locality experiment.
```
""")


def update_global_docs(decision: str) -> None:
    append_once(ROADMAP_MD, "## Stage 172: Frontier Closeout", f"""
## Stage 172: Frontier Closeout

Goal:

```text
Close the Stage169-171 evidence loop, record allowed/blocked claims, and route
the next bounded experiment.
```

Status:

```text
Completed. Stage172 records {decision}. The next automatic engineering route
is Stage174 from_DFT locality; Stage173 remains a separate proof route.
```
""")
    append_once(GOAL_MD, "Stage172 records the frontier closeout", f"""
Stage172 records the frontier closeout after Stage169/170/171. Decision:
`{decision}`. It allows the current r=6 complete-SAB engineering speedup claim
under the recorded platform and blocks optimality, compact-SAB, and paper-level
claims until their gates close.
""")
    append_once(CURRENT_GOAL_MD, "76. Treat Stage172 as the current claim boundary", f"""
76. Treat Stage172 as the current claim boundary:
    `{decision}`. The next automatic engineering route is Stage174
    from_DFT locality; Stage173 is proof work only if explicitly prioritized.
""")
    append_once(HYPOTHESIS_YAML, "id: H96_frontier_closeout", f"""
  - id: H96_frontier_closeout
    statement: >
      The current PVW/MAT-SAB evidence supports an r=6 complete-SAB engineering
      throughput claim on CB5, but not theoretical optimality, implemented
      compact SAB, or paper-level novelty.
    mechanism: >
      Stage169 supplies complete-SAB repeated A/B, Stage170 supplies split
      component counters, and Stage171 separates structured compact into a
      proof route with open obligations.
    status: stage172_frontier_closeout
    evidence: docs/stage172_frontier_closeout.md; experiments/stage172_frontier_closeout_plan.md; theory_checks/stage172_claim_boundary.md; repro/stage172_frontier_closeout/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - missing Stage169/170/171 input evidence
      - component microbench evidence is written as complete-SAB speedup
      - compact projection is written as implemented algorithmic acceleration
""")
    append_once(RUN_LOG, "stage172-frontier-closeout-001", f"""
stage172-frontier-closeout-001,2026-07-04,{git_head()},Stage 172,analysis,python scripts/build_stage172_frontier_closeout.py,Stage169/170/171 evidence synthesis,none,{decision},Current claim boundary and next-route closeout.,repro/stage172_frontier_closeout
""")
    append_once(MANIFEST, "stage172_frontier_closeout", f"""
- stage172_frontier_closeout: `{decision}`
  - `docs/stage172_frontier_closeout.md`
  - `experiments/stage172_frontier_closeout_plan.md`
  - `theory_checks/stage172_claim_boundary.md`
  - `algorithm_variants/mat_rlwe_sab_frontier_closeout.md`
  - `repro/stage172_frontier_closeout/`
""")
    append_once(CHECKLIST, "Stage172 frontier closeout pack recorded", """
- [x] Stage172 frontier closeout pack recorded.
""")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    inputs = build_inputs()
    claims = build_claims()
    frontier = build_frontier()
    next_rows = build_next_queue()
    decision = decide(inputs)
    summary = build_summary(decision, inputs, claims)

    write_csv(INPUTS_CSV, inputs, ["source", "path", "present", "decision"])
    write_csv(CLAIMS_CSV, claims, ["claim", "status", "evidence", "quantitative_value", "boundary"])
    write_csv(FRONTIER_CSV, frontier, ["rank", "frontier", "why_now", "next_gate", "risk"])
    write_csv(NEXT_CSV, next_rows, ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"])
    write_csv(SUMMARY_CSV, summary, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])

    write_docs(decision, summary, inputs, claims, frontier, next_rows)
    update_global_docs(decision)
    artifact_index([
        SUMMARY_CSV,
        INPUTS_CSV,
        CLAIMS_CSV,
        FRONTIER_CSV,
        NEXT_CSV,
        ARTIFACT_CSV,
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
    ])
    print(decision)


if __name__ == "__main__":
    main()
