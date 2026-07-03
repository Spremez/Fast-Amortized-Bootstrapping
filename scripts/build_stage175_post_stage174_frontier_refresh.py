#!/usr/bin/env python3
"""Stage175: refresh frontier after Stage174 neutral direct-scale result."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage175_post_stage174_frontier_refresh"

SUMMARY_CSV = OUT_DIR / "summary.csv"
INPUTS_CSV = OUT_DIR / "evidence_inputs.csv"
DECISIONS_CSV = OUT_DIR / "decision_matrix.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage175_post_stage174_frontier_refresh.md"
PLAN_MD = ROOT / "experiments" / "stage175_post_stage174_frontier_refresh_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage175_route_boundary.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_post_stage174_frontier.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE171_SUMMARY = ROOT / "repro" / "stage171_structured_compact_keygen_feasibility" / "summary.csv"
STAGE171_PROOF = ROOT / "repro" / "stage171_structured_compact_keygen_feasibility" / "proof_obligations.csv"
STAGE172_SUMMARY = ROOT / "repro" / "stage172_frontier_closeout" / "summary.csv"
STAGE174_SUMMARY = ROOT / "repro" / "stage174_from_dft_direct_scale_gate" / "summary.csv"
STAGE174_COMPARISON = ROOT / "repro" / "stage174_from_dft_direct_scale_gate" / "comparison.csv"
STAGE174_AGG = ROOT / "repro" / "stage174_from_dft_direct_scale_gate" / "microbench_aggregate.csv"


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


def comparison_value(scope: str, field: str) -> str:
    for row in read_csv(STAGE174_COMPARISON):
        if row.get("scope") == scope:
            return row.get(field, "")
    return ""


def agg_mean(variant: str) -> str:
    for row in read_csv(STAGE174_AGG):
        if row.get("variant") == variant:
            return row.get("mean", "")
    return ""


def build_inputs() -> List[Dict[str, str]]:
    sources = [
        ("stage171_structured_compact_feasibility", STAGE171_SUMMARY),
        ("stage172_frontier_closeout", STAGE172_SUMMARY),
        ("stage174_direct_scale_gate", STAGE174_SUMMARY),
    ]
    return [
        {
            "source": name,
            "path": rel(path),
            "present": "yes" if path.exists() else "no",
            "decision": decision_from(path),
        }
        for name, path in sources
    ]


def build_decisions() -> List[Dict[str, str]]:
    return [
        {
            "topic": "direct_scale_backend_candidate",
            "decision": "STOP_TUNING",
            "evidence": rel(STAGE174_COMPARISON),
            "quantitative_value": f"micro={comparison_value('microbench', 'value')};baseline_mean={agg_mean('baseline')};direct_scale_mean={agg_mean('direct_scale')}",
            "reason": "Correct but slower/neutral at the microbench gate, so full-SAB A/B was correctly skipped.",
        },
        {
            "topic": "from_DFT_backend_direction",
            "decision": "DO_NOT_REPEAT_COMPONENT_MAJOR_OR_DIRECT_SCALE",
            "evidence": f"repro/stage163_from_dft_batching_microbench/summary.csv;{rel(STAGE174_SUMMARY)}",
            "quantitative_value": "Stage163 neutral; Stage174 neutral",
            "reason": "Two bounded backend-order/SIMD candidates failed to promote; further backend tuning needs a new mechanism.",
        },
        {
            "topic": "structured_compact_route",
            "decision": "NEXT_BOUNDED_RESEARCH_GATE",
            "evidence": rel(STAGE171_PROOF),
            "quantitative_value": "open_proof_obligations=5",
            "reason": "This is the remaining route with potential algorithmic rather than backend-only gain, but it must start with finite phase/noise toy checks.",
        },
        {
            "topic": "complete_SAB_claim",
            "decision": "UNCHANGED_STAGE169_ONLY",
            "evidence": "repro/stage169_cb5_native_repeated_r6_gate/aggregate.csv",
            "quantitative_value": "mean=1.131666667;min=1.115000000;ci95_low=1.095041982",
            "reason": "Stage174 did not run or pass full-SAB A/B; complete-SAB claim remains the Stage169 current exact r=6 claim.",
        },
    ]


def build_next_queue() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "stage": "173",
            "name": "structured compact formal phase/noise toy",
            "entry_condition": "Stage175 closes direct-scale and leaves structured compact as the highest-upside bounded route.",
            "gate": "Define compact keygen equations; run finite phase propagation and noise toy checks for r=2/4/6.",
            "failure_rule": "If phase equations or noise toy fail, keep compact route blocked and do not implement SAB code.",
        },
        {
            "priority": "P1",
            "stage": "176",
            "name": "alias fallback audit",
            "entry_condition": "Only if a quick schedule audit shows nonzero out==addend from_DFT calls in a relevant path.",
            "gate": "Count alias fallback calls, test in-place exactness, and promote only if full-SAB path uses it.",
            "failure_rule": "If alias calls are zero in current exact path, record closure and do not optimize.",
        },
        {
            "priority": "P2",
            "stage": "177",
            "name": "literature matrix refresh",
            "entry_condition": "Before any paper-level novelty claim.",
            "gate": "Verify real related work for SAB, PVW/MAT external products, multi-output bootstrapping, and SIMD FHE kernels.",
            "failure_rule": "No novelty wording without source-backed related-work matrix.",
        },
    ]


def decide(inputs: List[Dict[str, str]]) -> str:
    if any(row["present"] != "yes" for row in inputs):
        return "BLOCKED_STAGE175_MISSING_INPUT"
    return "PASS_STAGE175_ROUTE_TO_STRUCTURED_COMPACT_TOY_GATE"


def build_summary(decision: str, inputs: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [
        {
            "gate": "stage175_inputs",
            "status": "PASS" if all(row["present"] == "yes" for row in inputs) else "BLOCKED",
            "metric": "input_count",
            "value": str(sum(1 for row in inputs if row["present"] == "yes")),
            "evidence": rel(INPUTS_CSV),
            "detail": "Stage175 consumes Stage171/172/174 evidence.",
            "next_action": "Repair missing input before route decisions.",
        },
        {
            "gate": "stage175_direct_scale_close",
            "status": "PASS",
            "metric": "microbench_status",
            "value": comparison_value("microbench", "status"),
            "evidence": rel(STAGE174_COMPARISON),
            "detail": "Direct-scale is exact but not promoted; do not keep tuning this candidate.",
            "next_action": "Route away from direct-scale.",
        },
        {
            "gate": "stage175_next_route",
            "status": "PASS",
            "metric": "next_stage",
            "value": "Stage173",
            "evidence": rel(NEXT_CSV),
            "detail": "Next work is bounded structured compact finite phase/noise toy, not open-ended theory.",
            "next_action": "Implement Stage173 only with finite/toy pass-fail gates.",
        },
        {
            "gate": "stage175_decision",
            "status": decision,
            "metric": "route_refresh",
            "value": "recorded",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Stage175 records the post-Stage174 route boundary.",
            "next_action": "Proceed to Stage173 or stop for user review.",
        },
    ]


def artifact_index(paths: List[Path]) -> None:
    fields = ["path", "exists", "sha256", "bytes"]
    rows = []
    for path in paths:
        if path == ARTIFACT_CSV:
            continue
        rows.append({
            "path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path) if path.exists() and path.is_file() else "",
            "bytes": str(path.stat().st_size) if path.exists() and path.is_file() else "",
        })
    write_csv(ARTIFACT_CSV, rows, fields)
    rows.append({
        "path": rel(ARTIFACT_CSV),
        "exists": "yes",
        "sha256": sha256_file(ARTIFACT_CSV),
        "bytes": str(ARTIFACT_CSV.stat().st_size),
    })
    write_csv(ARTIFACT_CSV, rows, fields)


def write_docs(
    decision: str,
    summary: List[Dict[str, str]],
    inputs: List[Dict[str, str]],
    decisions: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
) -> None:
    summary_fields = ["gate", "status", "metric", "value", "evidence", "detail", "next_action"]
    input_fields = ["source", "path", "present", "decision"]
    decision_fields = ["topic", "decision", "evidence", "quantitative_value", "reason"]
    next_fields = ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"]

    write_text_lf(OUT_MD, f"""# Stage175 Post-Stage174 Frontier Refresh

Decision: `{decision}`.

Stage175 closes the direct-scale branch. The result is useful negative
evidence: the flag is exact, but it did not pass the microbench promotion gate,
so no full-SAB claim changes.

The next bounded route is Stage173: structured compact finite phase/noise toy.
That route is not a paper claim or implementation permission; it is the next
pass-fail check for the higher-upside algorithmic path identified in Stage171.

## Gate Summary

{table(summary, summary_fields)}

## Evidence Inputs

{table(inputs, input_fields)}

## Decision Matrix

{table(decisions, decision_fields)}

## Next Queue

{table(next_rows, next_fields)}
""")

    write_text_lf(PLAN_MD, """# Stage175 Validation Plan

Goal: record the post-Stage174 route and prevent direct-scale neutral evidence
from being retuned indefinitely.

Acceptance:

- Stage174 evidence is present and neutral/non-promoted;
- direct-scale route is marked closed unless a new mechanism appears;
- next route is bounded by finite/toy gates, not open-ended theory;
- complete-SAB claim remains unchanged from Stage169.
""")

    write_text_lf(THEORY_MD, """# Stage175 Route Boundary

After Stage174, backend-level from_DFT tuning has two neutral data points:

```text
Stage163: component-major batching not promoted
Stage174: AVX512 direct-scale not promoted
```

Therefore continuing to tune the same backend boundary without a new mechanism
would be weak research process. The next high-upside path is structured compact
MAT-SAB, but it must start with finite phase/noise checks and keep complete-SAB
claims blocked until implementation and full A/B evidence exist.
""")

    write_text_lf(VARIANT_MD, f"""# Post-Stage174 Frontier

Decision:

```text
{decision}
```

Closed for now:

```text
SPQLIOS_AVX512_DIRECT_SCALE
component-major from_DFT batching
```

Next bounded route:

```text
Stage173 structured compact finite phase/noise toy
```
""")


def update_global_docs(decision: str) -> None:
    append_once(ROADMAP_MD, "## Stage 175: Post-Stage174 Frontier Refresh", f"""
## Stage 175: Post-Stage174 Frontier Refresh

Goal:

```text
Close the neutral direct-scale backend branch and route the next bounded
research step.
```

Status:

```text
Completed. Stage175 records {decision}. Direct-scale is not promoted; the next
bounded route is Stage173 structured compact finite phase/noise toy.
```
""")
    append_once(GOAL_MD, "Stage175 records the post-Stage174 route refresh", f"""
Stage175 records the post-Stage174 route refresh. Decision: `{decision}`.
Direct-scale backend tuning is closed for now; the next bounded route is a
finite phase/noise toy gate for structured compact MAT-SAB.
""")
    append_once(CURRENT_GOAL_MD, "78. Treat Stage175 as the post-direct-scale route refresh", f"""
78. Treat Stage175 as the post-direct-scale route refresh:
    `{decision}`. Complete-SAB claims remain unchanged; next bounded work is
    Stage173 structured compact finite phase/noise toy.
""")
    append_once(HYPOTHESIS_YAML, "id: H98_post_stage174_frontier", f"""
  - id: H98_post_stage174_frontier
    statement: >
      After Stage174, direct-scale from_DFT backend tuning should stop unless a
      new mechanism appears; the next bounded high-upside route is structured
      compact phase/noise validation.
    mechanism: >
      Stage163 and Stage174 give neutral backend evidence, while Stage171
      identifies structured compact as a proof-gated algorithmic path with
      larger potential term-count reduction.
    status: stage175_post_stage174_frontier_refresh
    evidence: docs/stage175_post_stage174_frontier_refresh.md; experiments/stage175_post_stage174_frontier_refresh_plan.md; theory_checks/stage175_route_boundary.md; repro/stage175_post_stage174_frontier_refresh/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - direct-scale is retuned without a new mechanism
      - structured compact proceeds to implementation before finite phase/noise gates
      - complete-SAB claim is changed without full-SAB A/B
""")
    append_once(RUN_LOG, "stage175-post-stage174-frontier-refresh-001", f"""
stage175-post-stage174-frontier-refresh-001,2026-07-04,{git_head()},Stage 175,analysis,python scripts/build_stage175_post_stage174_frontier_refresh.py,Stage171/172/174 evidence synthesis,none,{decision},Post-Stage174 frontier refresh.,repro/stage175_post_stage174_frontier_refresh
""")
    append_once(MANIFEST, "stage175_post_stage174_frontier_refresh", f"""
- stage175_post_stage174_frontier_refresh: `{decision}`
  - `docs/stage175_post_stage174_frontier_refresh.md`
  - `experiments/stage175_post_stage174_frontier_refresh_plan.md`
  - `theory_checks/stage175_route_boundary.md`
  - `algorithm_variants/mat_rlwe_sab_post_stage174_frontier.md`
  - `repro/stage175_post_stage174_frontier_refresh/`
""")
    append_once(CHECKLIST, "Stage175 post-Stage174 frontier refresh pack recorded", """
- [x] Stage175 post-Stage174 frontier refresh pack recorded.
""")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    inputs = build_inputs()
    decisions = build_decisions()
    next_rows = build_next_queue()
    decision = decide(inputs)
    summary = build_summary(decision, inputs)

    write_csv(INPUTS_CSV, inputs, ["source", "path", "present", "decision"])
    write_csv(DECISIONS_CSV, decisions, ["topic", "decision", "evidence", "quantitative_value", "reason"])
    write_csv(NEXT_CSV, next_rows, ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"])
    write_csv(SUMMARY_CSV, summary, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])

    write_docs(decision, summary, inputs, decisions, next_rows)
    update_global_docs(decision)
    artifact_index([
        SUMMARY_CSV,
        INPUTS_CSV,
        DECISIONS_CSV,
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
