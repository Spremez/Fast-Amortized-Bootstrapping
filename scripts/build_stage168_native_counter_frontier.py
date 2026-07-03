#!/usr/bin/env python3
"""Stage168: native-counter attribution frontier and claim policy."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage168_native_counter_frontier"

SUMMARY_CSV = OUT_DIR / "summary.csv"
DERIVED_CSV = OUT_DIR / "derived_counter_ratios.csv"
INPUT_CSV = OUT_DIR / "evidence_inputs.csv"
CLAIM_CSV = OUT_DIR / "claim_policy.csv"
ROUTE_CSV = OUT_DIR / "next_stage_queue.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage168_native_counter_frontier.md"
PLAN_MD = ROOT / "experiments" / "stage168_native_counter_frontier_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage168_counter_frontier_scope.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_native_counter_frontier.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE160_COMPONENT = ROOT / "repro" / "stage160_post_fusion_frontier" / "component_shares.csv"
STAGE163_SUMMARY = ROOT / "repro" / "stage163_from_dft_batching_microbench" / "summary.csv"
STAGE165_SUMMARY = ROOT / "repro" / "stage165_closed_fullmat_streaming_microbench" / "summary.csv"
STAGE166_SUMMARY = ROOT / "repro" / "stage166_shared_output_compact_algebra_gate" / "summary.csv"
STAGE167_SUMMARY = ROOT / "repro" / "stage167_cb5_native_r6_counter_refresh" / "summary.csv"
STAGE167_COUNTERS = ROOT / "repro" / "stage167_cb5_native_r6_counter_refresh" / "counter_metrics.csv"
STAGE167_RUN = ROOT / "repro" / "stage167_cb5_native_r6_counter_refresh" / "run_metrics.csv"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
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


def decision_from(path: Path) -> str:
    for row in read_csv(path):
        if row.get("gate", "").endswith("decision"):
            return row.get("status", "")
    return "MISSING"


def metric_value(rows: List[Dict[str, str]], metric: str) -> str:
    for row in rows:
        if row.get("metric") == metric:
            return row.get("value", "")
    return ""


def float_metric(rows: List[Dict[str, str]], metric: str) -> float:
    value = metric_value(rows, metric)
    return float(value) if value else 0.0


def build_inputs() -> List[Dict[str, str]]:
    return [
        {
            "source": "stage160_component_frontier",
            "path": rel(STAGE160_COMPONENT),
            "present": "yes" if STAGE160_COMPONENT.exists() else "no",
            "decision_or_role": "post-fusion component shares",
        },
        {
            "source": "stage163_from_dft_batching",
            "path": rel(STAGE163_SUMMARY),
            "present": "yes" if STAGE163_SUMMARY.exists() else "no",
            "decision_or_role": decision_from(STAGE163_SUMMARY),
        },
        {
            "source": "stage165_streaming",
            "path": rel(STAGE165_SUMMARY),
            "present": "yes" if STAGE165_SUMMARY.exists() else "no",
            "decision_or_role": decision_from(STAGE165_SUMMARY),
        },
        {
            "source": "stage166_compact_algebra",
            "path": rel(STAGE166_SUMMARY),
            "present": "yes" if STAGE166_SUMMARY.exists() else "no",
            "decision_or_role": decision_from(STAGE166_SUMMARY),
        },
        {
            "source": "stage167_native_counters",
            "path": rel(STAGE167_COUNTERS),
            "present": "yes" if STAGE167_COUNTERS.exists() else "no",
            "decision_or_role": decision_from(STAGE167_SUMMARY),
        },
    ]


def build_derived() -> List[Dict[str, str]]:
    counters = read_csv(STAGE167_COUNTERS)
    run = read_csv(STAGE167_RUN)
    cycles = float_metric(counters, "cycles")
    instructions = float_metric(counters, "instructions")
    loads = float_metric(counters, "mem_inst_retired.all_loads")
    stores = float_metric(counters, "mem_inst_retired.all_stores")
    fp512 = float_metric(counters, "fp_arith_inst_retired.512b_packed_double")
    fp256 = float_metric(counters, "fp_arith_inst_retired.256b_packed_double")
    cache_refs = float_metric(counters, "cache-references")
    cache_misses = float_metric(counters, "cache-misses")
    branches = float_metric(counters, "branches")
    branch_misses = float_metric(counters, "branch-misses")
    pvw_us = float_metric(run, "pvw_avg_us")
    scalar_us = float_metric(run, "scalar_repeated_avg_us")
    speedup = float_metric(run, "speedup_vs_scalar_repeated")
    denom = cycles if cycles else 1.0
    rows = [
        {
            "metric": "ipc",
            "value": f"{instructions / denom:.9f}" if cycles else "0",
            "interpretation": "Instructions per cycle for the complete perf-wrapped run.",
        },
        {
            "metric": "loads_per_cycle",
            "value": f"{loads / denom:.9f}" if cycles else "0",
            "interpretation": "High value indicates substantial memory instruction pressure.",
        },
        {
            "metric": "stores_per_cycle",
            "value": f"{stores / denom:.9f}" if cycles else "0",
            "interpretation": "Store pressure remains material after copyback/sub-decomp fusions.",
        },
        {
            "metric": "fp512_per_cycle",
            "value": f"{fp512 / denom:.9f}" if cycles else "0",
            "interpretation": "AVX512 FP work is material; counters alone do not prove FMA-bound.",
        },
        {
            "metric": "fp256_per_cycle",
            "value": f"{fp256 / denom:.9f}" if cycles else "0",
            "interpretation": "Residual 256-bit FP work likely comes from FFT/backend paths.",
        },
        {
            "metric": "load_store_to_fp512_ratio",
            "value": f"{(loads + stores) / fp512:.9f}" if fp512 else "0",
            "interpretation": "Memory instructions exceed FP512 arithmetic instructions; memory layout remains a plausible frontier.",
        },
        {
            "metric": "cache_miss_rate",
            "value": f"{cache_misses / cache_refs:.9f}" if cache_refs else "0",
            "interpretation": "High cache miss rate supports locality-focused investigation, but not a standalone optimization claim.",
        },
        {
            "metric": "branch_miss_rate",
            "value": f"{branch_misses / branches:.9f}" if branches else "0",
            "interpretation": "Branch misses are small relative to memory/FP pressure.",
        },
        {
            "metric": "perf_wrapped_speedup_vs_scalar_repeated",
            "value": f"{speedup:.9f}" if speedup else "0",
            "interpretation": "Single perf-wrapped full-SAB run; attribution evidence only, not high-stat performance claim.",
        },
        {
            "metric": "perf_wrapped_pvw_us",
            "value": f"{pvw_us:.3f}" if pvw_us else "0",
            "interpretation": "Wall-time under perf overhead for current r=6 path.",
        },
        {
            "metric": "perf_wrapped_scalar_repeated_us",
            "value": f"{scalar_us:.3f}" if scalar_us else "0",
            "interpretation": "Scalar repeated baseline in the same perf-wrapped run.",
        },
    ]
    return rows


def build_claim_policy() -> List[Dict[str, str]]:
    return [
        {
            "claim": "current r=6 exact path has native counter evidence",
            "status": "ALLOWED_ATTRIBUTION",
            "evidence": rel(STAGE167_COUNTERS),
            "limit": "Can discuss cycles/instructions/load/store/cache/FP512 counts for the recorded run.",
        },
        {
            "claim": "current r=6 exact path is theoretically optimal",
            "status": "BLOCKED",
            "evidence": f"{rel(STAGE167_COUNTERS)}; {rel(STAGE166_SUMMARY)}",
            "limit": "Counters do not prove a lower bound; generic compact exactness is blocked, but structured keygen remains an open theory route.",
        },
        {
            "claim": "row-streaming decompose/DFT should replace current tiled AVX",
            "status": "REJECTED",
            "evidence": rel(STAGE165_SUMMARY),
            "limit": "Exact but slower; keep current tiled AVX path.",
        },
        {
            "claim": "component-major from_DFT batching should be integrated",
            "status": "REJECTED_OR_NEUTRAL",
            "evidence": rel(STAGE163_SUMMARY),
            "limit": "Current backend fused-add remains useful, but batching order is not promoted.",
        },
        {
            "claim": "generic shared-output compact is drop-in for dense MAT",
            "status": "BLOCKED",
            "evidence": rel(STAGE166_SUMMARY),
            "limit": "Missing body-to-body cross terms require structured keygen/security/noise proof.",
        },
        {
            "claim": "native complete-SAB throughput is finalized",
            "status": "BLOCKED_STATS",
            "evidence": rel(STAGE167_RUN),
            "limit": "Stage167 is one perf-wrapped run. Need native no-perf repeated A/B and noise/resource gates.",
        },
    ]


def top_component_share(component: str) -> float:
    for row in read_csv(STAGE160_COMPONENT):
        if row.get("component") == component:
            return float(row.get("share_of_full", "0") or "0")
    return 0.0


def build_next_queue(derived: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "stage": "169",
            "name": "CB5 native no-perf repeated current r=6 full-SAB gate",
            "entry_condition": "Stage167 counters are attribution-only and speedup came from one perf-wrapped run.",
            "gate": "Run 3-5 paired native no-perf full-SAB A/B for current r=6 exact path; report T_bootstrap/r mean/min/max/CI plus correctness.",
            "failure_rule": "If native repeated speedup is weak or unstable, downgrade final performance wording to WSL/CB5-specific evidence.",
        },
        {
            "priority": "P1",
            "stage": "170",
            "name": "native MAT EP/from_DFT split counter microbench",
            "entry_condition": "Stage168 ratios show both FP512 and load/store/cache pressure; Stage160 top shares are MAT+subdecomp and from_DFT.",
            "gate": "Measure separate native counters for MAT EP/subdecomp and from_DFT materialization microbench kernels under the current exact path.",
            "failure_rule": "If counters cannot isolate components, keep only full-run attribution and do not claim component-level bound.",
        },
        {
            "priority": "P2",
            "stage": "171",
            "name": "structured compact keygen feasibility card",
            "entry_condition": "Only if pursuing a new algorithm/key distribution beyond generic dense MAT exactness.",
            "gate": "Define algebraic selector constraints, noise equations, security assumption delta, and finite phase/noise toy checks.",
            "failure_rule": "If keygen proof is not coherent, compact remains blocked and out of SAB implementation.",
        },
        {
            "priority": "P3",
            "stage": "172",
            "name": "frontier closeout report refresh",
            "entry_condition": "After Stage169 or Stage170 supplies stronger native evidence.",
            "gate": "Update final report with allowed claims, rejected variants, and remaining proof obligations.",
            "failure_rule": "No unsupported paper-level novelty or optimality wording.",
        },
    ]


def decide(inputs: List[Dict[str, str]], claim_rows: List[Dict[str, str]]) -> str:
    if any(row["present"] != "yes" for row in inputs):
        return "BLOCKED_STAGE168_MISSING_INPUT_EVIDENCE"
    if any(row["status"] == "BLOCKED_STATS" for row in claim_rows):
        return "PASS_STAGE168_ROUTE_TO_NATIVE_REPEATED_AND_SPLIT_COUNTERS"
    return "PASS_STAGE168_COUNTER_FRONTIER_RECORDED"


def build_summary(inputs: List[Dict[str, str]], derived: List[Dict[str, str]], decision: str) -> List[Dict[str, str]]:
    missing = [row["source"] for row in inputs if row["present"] != "yes"]
    cache_miss_rate = next((row["value"] for row in derived if row["metric"] == "cache_miss_rate"), "0")
    ls_fp = next((row["value"] for row in derived if row["metric"] == "load_store_to_fp512_ratio"), "0")
    speedup = next((row["value"] for row in derived if row["metric"] == "perf_wrapped_speedup_vs_scalar_repeated"), "0")
    return [
        {
            "gate": "stage168_inputs",
            "status": "PASS" if not missing else "BLOCKED",
            "metric": "missing_inputs",
            "value": ";".join(missing) if missing else "none",
            "evidence": rel(INPUT_CSV),
            "detail": "Stage168 consumes Stage160/163/165/166/167 evidence.",
            "next_action": "Repair missing input before routing claims.",
        },
        {
            "gate": "stage168_counter_ratios",
            "status": "PASS",
            "metric": "cache_miss_rate;load_store_to_fp512",
            "value": f"{cache_miss_rate};{ls_fp}",
            "evidence": rel(DERIVED_CSV),
            "detail": "Native counters show both memory/locality and AVX512 arithmetic pressure.",
            "next_action": "Use split counters before component-level claims.",
        },
        {
            "gate": "stage168_stats_policy",
            "status": "BLOCKED_STATS",
            "metric": "perf_wrapped_speedup",
            "value": speedup,
            "evidence": rel(CLAIM_CSV),
            "detail": "Stage167 has a single perf-wrapped full-SAB run; not enough for final native throughput wording.",
            "next_action": "Run native no-perf repeated A/B as Stage169.",
        },
        {
            "gate": "stage168_decision",
            "status": decision,
            "metric": "next_stage",
            "value": "Stage169",
            "evidence": rel(ROUTE_CSV),
            "detail": "Stage168 routes to native repeated full-SAB and split counter gates.",
            "next_action": "Do not make optimality or final throughput claims before Stage169/170.",
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
    derived: List[Dict[str, str]],
    claims: List[Dict[str, str]],
    route: List[Dict[str, str]],
) -> None:
    summary_fields = ["gate", "status", "metric", "value", "evidence", "detail", "next_action"]
    input_fields = ["source", "path", "present", "decision_or_role"]
    derived_fields = ["metric", "value", "interpretation"]
    claim_fields = ["claim", "status", "evidence", "limit"]
    route_fields = ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"]
    mat_share = top_component_share("mat_ep_plus_subdecomp")
    dft_share = top_component_share("from_dft_materialization")

    write_text_lf(OUT_MD, f"""# Stage168 Native Counter Frontier

Decision: `{decision}`.

Stage168 interprets Stage167 native counters as attribution evidence only. The
full-SAB optimization frontier remains split between:

- current exact-path throughput/statistics, because Stage167 is one perf-wrapped
  run;
- component-level native split counters, because the full run mixes MAT
  external product, decomposition, and materialization;
- structured compact keygen proof, if the research direction wants a new
  algorithm rather than a generic dense-MAT implementation.

Stage160 component shares remain material: MAT+subdecomp share
`{mat_share:.6f}`, and from_DFT materialization share `{dft_share:.6f}`.

## Gate Summary

{table(summary, summary_fields)}

## Evidence Inputs

{table(inputs, input_fields)}

## Derived Counter Ratios

{table(derived, derived_fields)}

## Claim Policy

{table(claims, claim_fields)}

## Next Queue

{table(route, route_fields)}
""")

    write_text_lf(PLAN_MD, """# Stage168 Validation Plan

Goal: convert Stage167 native counters into scoped attribution and a concrete
next queue without overclaiming theoretical optimality or final throughput.

Inputs:

- Stage160 post-fusion component shares;
- Stage163 from_DFT batching result;
- Stage165 closed full-MAT streaming result;
- Stage166 compact algebra gate;
- Stage167 native CB5 r=6 counters.

Acceptance:

- derived ratios must be reproducible from raw counter CSV;
- claim policy must block theoretical optimality and final native throughput
  until stronger evidence exists;
- next queue must contain executable gates with failure rules.
""")

    write_text_lf(THEORY_MD, """# Stage168 Counter Frontier Scope

Native counters help explain a concrete implementation on a concrete CPU. They
do not establish an algorithmic lower bound for PVW/MAT-SAB. In this project,
the lower-bound and algorithmic issues remain separate:

- the current exact dense MAT route needs `(1+r)^2` generic selector terms per
  gadget level;
- same-format materialization-count reduction is closed under the current API;
- generic compact shared-output exactness is blocked by missing cross terms;
- structured compact keygen remains a different algorithmic object, not an
  implementation detail.

Therefore Stage168 uses counters to route experiments, not to certify
optimality.
""")

    write_text_lf(VARIANT_MD, f"""# Native Counter Frontier for Current r=6 PVW/MAT-SAB

This artifact does not define a new implementation variant. It classifies the
current exact r=6 path after Stage167.

Decision:

```text
{decision}
```

Allowed next executable work:

```text
Stage169: native no-perf repeated full-SAB A/B
Stage170: native MAT EP/from_DFT split counter microbench
```

Blocked claims:

```text
theoretical optimality
final native throughput claim from a single perf-wrapped run
generic compact drop-in exactness
```
""")


def update_global_docs(decision: str) -> None:
    append_once(ROADMAP_MD, "## Stage 168: Native Counter Frontier", f"""
## Stage 168: Native Counter Frontier

Goal:

```text
Convert Stage167 native counters into scoped attribution, claim policy, and
next executable gates.
```

Status:

```text
Completed. Stage168 records {decision}. Native counters are attribution-only;
the next gates are native no-perf repeated full-SAB A/B and split native
component counters.
```
""")

    append_once(GOAL_MD, "Stage168 records native counter frontier", f"""
Stage168 records the native counter frontier after Stage167. Decision:
`{decision}`. It blocks theoretical optimality and final native throughput
claims from the single perf-wrapped run and routes next to Stage169/170.
""")

    append_once(CURRENT_GOAL_MD, "72. Treat Stage168 as the native counter frontier", f"""
72. Treat Stage168 as the native counter frontier:
    `{decision}`. Use Stage167 counters only for attribution; final native
    throughput and component-level claims require Stage169/170.
""")

    append_once(HYPOTHESIS_YAML, "id: H92_native_counter_frontier", f"""
  - id: H92_native_counter_frontier
    statement: >
      Stage167 native counters should route the next PVW/MAT-SAB work toward
      native repeated complete-SAB statistics and split component counters, not
      theoretical optimality claims.
    mechanism: >
      The full-run counters combine high AVX512 FP work with substantial
      load/store/cache pressure, while prior gates reject from_DFT batching,
      row streaming, and generic compact drop-in exactness.
    status: stage168_native_counter_frontier
    evidence: docs/stage168_native_counter_frontier.md; experiments/stage168_native_counter_frontier_plan.md; theory_checks/stage168_counter_frontier_scope.md; repro/stage168_native_counter_frontier/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - derived ratios are not reproducible from Stage167 raw counters
      - final native throughput is claimed from one perf-wrapped run
      - theoretical optimality is claimed without lower-bound proof
""")

    append_once(RUN_LOG, "stage168-native-counter-frontier-001", f"""
stage168-native-counter-frontier-001,2026-07-04,{git_head()},Stage 168,analysis,python scripts/build_stage168_native_counter_frontier.py,Stage160/163/165/166/167 evidence,none,{decision},Native counter attribution frontier and claim-policy gate.,repro/stage168_native_counter_frontier
""")

    append_once(MANIFEST, "stage168_native_counter_frontier", f"""
- stage168_native_counter_frontier: `{decision}`
  - `docs/stage168_native_counter_frontier.md`
  - `experiments/stage168_native_counter_frontier_plan.md`
  - `theory_checks/stage168_counter_frontier_scope.md`
  - `algorithm_variants/mat_rlwe_sab_native_counter_frontier.md`
  - `repro/stage168_native_counter_frontier/`
""")

    append_once(CHECKLIST, "Stage168 native counter frontier pack recorded", """
- [x] Stage168 native counter frontier pack recorded.
""")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    inputs = build_inputs()
    derived = build_derived()
    claims = build_claim_policy()
    route = build_next_queue(derived)
    decision = decide(inputs, claims)
    summary = build_summary(inputs, derived, decision)

    write_csv(INPUT_CSV, inputs, ["source", "path", "present", "decision_or_role"])
    write_csv(DERIVED_CSV, derived, ["metric", "value", "interpretation"])
    write_csv(CLAIM_CSV, claims, ["claim", "status", "evidence", "limit"])
    write_csv(ROUTE_CSV, route, ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"])
    write_csv(SUMMARY_CSV, summary, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])

    write_docs(decision, summary, inputs, derived, claims, route)
    update_global_docs(decision)
    artifact_index([
        OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, SUMMARY_CSV, INPUT_CSV,
        DERIVED_CSV, CLAIM_CSV, ROUTE_CSV, Path(__file__),
    ])

    print(decision)
    for row in derived:
        if row["metric"] in {"ipc", "cache_miss_rate", "load_store_to_fp512_ratio", "perf_wrapped_speedup_vs_scalar_repeated"}:
            print(f"{row['metric']}={row['value']}")


if __name__ == "__main__":
    main()
