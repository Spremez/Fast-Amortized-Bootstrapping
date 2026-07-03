#!/usr/bin/env python3
"""Stage194: exact DFT/conversion mechanism preflight."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage194_exact_dft_conversion_preflight"

SUMMARY_CSV = OUT_DIR / "summary.csv"
SOURCE_CSV = OUT_DIR / "source_facts.csv"
PRIOR_CSV = OUT_DIR / "prior_gate_matrix.csv"
BUDGET_CSV = OUT_DIR / "component_budget.csv"
CANDIDATE_CSV = OUT_DIR / "mechanism_candidates.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage194_exact_dft_conversion_preflight.md"
PLAN_MD = ROOT / "experiments" / "stage194_exact_dft_conversion_preflight_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage194_exact_dft_conversion_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_exact_dft_conversion_preflight.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

POLY_C = ROOT / "src" / "mosfhet" / "src" / "polynomial.c"
PVW_C = ROOT / "src" / "mosfhet" / "src" / "pvwtmlwe.c"
MATTRGSW_C = ROOT / "src" / "mosfhet" / "src" / "mattrgsw.c"
STAGE180_DERIVED = ROOT / "repro" / "stage180_mat_ep_split_probe" / "derived_projection.csv"
STAGE180_RUN = ROOT / "repro" / "stage180_mat_ep_split_probe" / "run_metrics.csv"
STAGE180_COUNTERS = ROOT / "repro" / "stage180_mat_ep_split_probe" / "counter_metrics.csv"
STAGE193_SUMMARY = ROOT / "repro" / "stage193_exact_addmul_dataflow_preflight" / "summary.csv"
STAGE174_SUMMARY = ROOT / "repro" / "stage174_from_dft_direct_scale_gate" / "summary.csv"
STAGE174_COMPARE = ROOT / "repro" / "stage174_from_dft_direct_scale_gate" / "comparison.csv"
STAGE174_AGG = ROOT / "repro" / "stage174_from_dft_direct_scale_gate" / "microbench_aggregate.csv"
STAGE163_SUMMARY = ROOT / "repro" / "stage163_from_dft_batching_microbench" / "summary.csv"
STAGE163_COMPARE = ROOT / "repro" / "stage163_from_dft_batching_microbench" / "comparison.csv"
STAGE163_AGG = ROOT / "repro" / "stage163_from_dft_batching_microbench" / "benchmark_aggregate.csv"
STAGE162_SUMMARY = ROOT / "repro" / "stage162_materialization_count_feasibility" / "summary.csv"
STAGE162_LOWER = ROOT / "repro" / "stage162_materialization_count_feasibility" / "materialization_lower_bound.csv"
STAGE156_SUMMARY = ROOT / "repro" / "stage156_lazy_dft_closure_gate" / "summary.csv"
STAGE136_SUMMARY = ROOT / "repro" / "stage136_batched_decomp_dft_gate" / "summary.csv"
STAGE136_RATIO = ROOT / "repro" / "stage136_batched_decomp_dft_gate" / "ratio_summary.csv"
STAGE137_SUMMARY = ROOT / "repro" / "stage137_decomp_dft_attribution_gate" / "summary.csv"
STAGE137_ATTR = ROOT / "repro" / "stage137_decomp_dft_attribution_gate" / "attribution.csv"
STAGE164_SUMMARY = ROOT / "repro" / "stage164_representation_closure_route" / "summary.csv"

DECISION = "PASS_STAGE194_EXACT_DFT_PREFLIGHT_NO_CODE_ROUTE_SCOPED_REFRESH"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((text.rstrip() + "\n").encode("utf-8"))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{name: row.get(name, "") for name in fields} for row in rows]
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


def f(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def find_line(pattern: str, path: Path) -> str:
    for idx, line in enumerate(read_text(path).splitlines(), start=1):
        if pattern in line:
            return str(idx)
    return ""


def derived_parts(metric: str) -> List[str]:
    for row in read_csv_dicts(STAGE180_DERIVED):
        if row.get("metric") == metric:
            return row.get("value", "").split(";")
    return []


def counter_value(variant: str, metric_name: str) -> float:
    for row in read_csv_dicts(STAGE180_COUNTERS):
        if row.get("variant") == variant and row.get("metric") == metric_name:
            return f(row.get("value", ""))
    return 0.0


def run_value(variant: str, column: str) -> float:
    for row in read_csv_dicts(STAGE180_RUN):
        if row.get("variant") == variant:
            return f(row.get(column, ""))
    return 0.0


def row_value(path: Path, key_col: str, key: str, value_col: str) -> str:
    for row in read_csv_dicts(path):
        if row.get(key_col) == key:
            return row.get(value_col, "")
    return ""


def build_source_rows() -> List[Dict[str, str]]:
    return [
        {
            "fact": "dft_to_torus_uses_backend_direct",
            "status": "yes",
            "line": find_line("void polynomial_DFT_to_torus", POLY_C),
            "evidence": rel(POLY_C),
            "implication": "Same-format materialization is delegated to backend FFT; local arithmetic changes must beat the backend primitive.",
        },
        {
            "fact": "dft_to_torus_add_uses_backend_fused_add",
            "status": "yes",
            "line": find_line("execute_direct_torus64_add", POLY_C),
            "evidence": rel(POLY_C),
            "implication": "The current add path already uses fused backend materialize+add for TORUS64.",
        },
        {
            "fact": "pvw_from_dft_add_has_backend_flag",
            "status": "yes",
            "line": find_line("SAB_PVW_BACKEND_FROM_DFT_ADD", PVW_C),
            "evidence": rel(PVW_C),
            "implication": "Stage174 tested this explicit backend/SIMD candidate and did not promote it.",
        },
        {
            "fact": "mat_sub_dft_converts_every_decomposed_row",
            "status": "yes",
            "line": find_line("polynomial_torus_to_DFT(scratch->dec_dft[i]", MATTRGSW_C),
            "evidence": rel(MATTRGSW_C),
            "implication": "Exact torus-input MAT EP still needs one torus_to_DFT per decomposed row before addmul.",
        },
        {
            "fact": "fft_processor_cached_per_thread_and_N",
            "status": "yes",
            "line": find_line("if(fft_proc[N >> 10]) return", POLY_C),
            "evidence": rel(POLY_C),
            "implication": "Processor construction is already cached; optimization must target conversion work, not init overhead.",
        },
    ]


def build_prior_rows() -> List[Dict[str, str]]:
    stage163_ratio = row_value(STAGE163_COMPARE, "metric", "component_major_batch_over_backend_current", "mean")
    stage174_ratio = row_value(STAGE174_COMPARE, "scope", "microbench", "value")
    stage136_r4 = row_value(STAGE136_RATIO, "r", "4", "speedup_current_over_batched")
    return [
        {
            "gate": "Stage162",
            "route": "same_format_materialization_count_reduction",
            "status": "CLOSED",
            "quantitative_result": "reducible_calls_without_representation_change=0",
            "evidence": rel(STAGE162_SUMMARY),
            "consequence": "Do not claim fewer from_DFT calls under current torus-input API.",
        },
        {
            "gate": "Stage163",
            "route": "component_major_from_DFT_batching",
            "status": "NEUTRAL_NOT_PROMOTED",
            "quantitative_result": f"component_major_over_backend_current_mean={stage163_ratio}",
            "evidence": rel(STAGE163_SUMMARY),
            "consequence": "Do not repeat backend batching without a new mechanism.",
        },
        {
            "gate": "Stage174",
            "route": "direct_scale_backend_from_DFT_add",
            "status": "NEUTRAL_OR_REJECT",
            "quantitative_result": f"baseline/direct_scale={stage174_ratio}",
            "evidence": rel(STAGE174_SUMMARY),
            "consequence": "Do not implement direct-scale/fused-add variants as full-SAB candidates.",
        },
        {
            "gate": "Stage136",
            "route": "batched_decompose_to_DFT",
            "status": "NEUTRAL_OR_NEGATIVE",
            "quantitative_result": f"r4 speedup_current_over_batched={stage136_r4}",
            "evidence": rel(STAGE136_SUMMARY),
            "consequence": "Do not reopen this batched decomp/DFT variant.",
        },
        {
            "gate": "Stage156",
            "route": "naive_lazy_DFT_accumulator",
            "status": "REJECTED_NONCLOSED",
            "quantitative_result": "decomposition nonlinearity counterexamples found",
            "evidence": rel(STAGE156_SUMMARY),
            "consequence": "Do not keep only DFT accumulator state without a new exact decomposition API.",
        },
        {
            "gate": "Stage164",
            "route": "representation_change",
            "status": "PROOF_OR_NEW_API_REQUIRED",
            "quantitative_result": "same-format closed; representation route must prove closure/noise",
            "evidence": rel(STAGE164_SUMMARY),
            "consequence": "Representation changes are not local DFT tuning.",
        },
    ]


def build_budget_rows() -> List[Dict[str, str]]:
    torus_parts = derived_parts("torus_to_dft_rows_full_sab_share_and_3pct_requirement")
    add_parts = derived_parts("addmul_from_dec_dft_full_sab_share_and_3pct_requirement")
    sub_parts = derived_parts("sub_decompose_full_sab_share_and_3pct_requirement")
    torus_loads = counter_value("torus_to_dft_rows", "mem_inst_retired.all_loads")
    torus_stores = counter_value("torus_to_dft_rows", "mem_inst_retired.all_stores")
    torus_cache_refs = counter_value("torus_to_dft_rows", "cache-references")
    torus_cache_misses = counter_value("torus_to_dft_rows", "cache-misses")
    torus_fp512 = counter_value("torus_to_dft_rows", "fp_arith_inst_retired.512b_packed_double")
    cache_miss_rate = torus_cache_misses / torus_cache_refs if torus_cache_refs else 0.0
    return [
        {
            "component": "torus_to_dft_rows",
            "full_sab_share": torus_parts[0] if torus_parts else "",
            "required_component_speedup_for_3pct_full_sab": torus_parts[1] if len(torus_parts) > 1 else "",
            "per_call_us": f"{run_value('torus_to_dft_rows', 'per_call_us'):.9f}",
            "loads": f"{torus_loads:.0f}",
            "stores": f"{torus_stores:.0f}",
            "fp512": f"{torus_fp512:.0f}",
            "cache_miss_rate": f"{cache_miss_rate:.6f}",
            "evidence": f"{rel(STAGE180_DERIVED)}; {rel(STAGE180_COUNTERS)}",
            "interpretation": "Large enough to matter only if a new mechanism beats about 1.208x component speedup.",
        },
        {
            "component": "sub_decompose",
            "full_sab_share": sub_parts[0] if sub_parts else "",
            "required_component_speedup_for_3pct_full_sab": sub_parts[1] if len(sub_parts) > 1 else "",
            "per_call_us": f"{run_value('sub_decompose', 'per_call_us'):.9f}",
            "loads": f"{counter_value('sub_decompose', 'mem_inst_retired.all_loads'):.0f}",
            "stores": f"{counter_value('sub_decompose', 'mem_inst_retired.all_stores'):.0f}",
            "fp512": f"{counter_value('sub_decompose', 'fp_arith_inst_retired.512b_packed_double'):.0f}",
            "cache_miss_rate": "",
            "evidence": rel(STAGE180_DERIVED),
            "interpretation": "Sub-decompose alone requires a much larger speedup and Stage181 already rejected the AVX512 variant.",
        },
        {
            "component": "addmul_from_dec_dft",
            "full_sab_share": add_parts[0] if add_parts else "",
            "required_component_speedup_for_3pct_full_sab": add_parts[1] if len(add_parts) > 1 else "",
            "per_call_us": f"{run_value('addmul_from_dec_dft', 'per_call_us'):.9f}",
            "loads": f"{counter_value('addmul_from_dec_dft', 'mem_inst_retired.all_loads'):.0f}",
            "stores": f"{counter_value('addmul_from_dec_dft', 'mem_inst_retired.all_stores'):.0f}",
            "fp512": f"{counter_value('addmul_from_dec_dft', 'fp_arith_inst_retired.512b_packed_double'):.0f}",
            "cache_miss_rate": "",
            "evidence": rel(STAGE193_SUMMARY),
            "interpretation": "Closed by Stage193 unless a new nonlocal mechanism appears.",
        },
    ]


def build_candidate_rows() -> List[Dict[str, str]]:
    torus_req = derived_parts("torus_to_dft_rows_full_sab_share_and_3pct_requirement")
    req = torus_req[1] if len(torus_req) > 1 else "1.208076492"
    return [
        {
            "candidate": "same_format_call_count_reduction",
            "mechanism_type": "algorithmic_count",
            "status": "REJECTED",
            "best_evidence": rel(STAGE162_LOWER),
            "quantitative_or_static_result": "reducible_calls_without_representation_change=0",
            "code_permission": "DENY",
            "next_action": "do not reopen without representation change",
        },
        {
            "candidate": "backend_component_major_batching",
            "mechanism_type": "backend_wall_time",
            "status": "NEUTRAL",
            "best_evidence": rel(STAGE163_COMPARE),
            "quantitative_or_static_result": "component_major_batch_over_backend_current_mean=0.972807930",
            "code_permission": "DENY",
            "next_action": "do not integrate into full SAB",
        },
        {
            "candidate": "direct_scale_or_fused_add_variant",
            "mechanism_type": "backend_wall_time",
            "status": "NEUTRAL_OR_REJECT",
            "best_evidence": rel(STAGE174_COMPARE),
            "quantitative_or_static_result": "baseline/direct_scale mean ratio=0.990754925",
            "code_permission": "DENY",
            "next_action": "do not keep tuning direct-scale",
        },
        {
            "candidate": "batched_decompose_to_DFT",
            "mechanism_type": "decomp_dft_dataflow",
            "status": "REJECTED",
            "best_evidence": rel(STAGE136_RATIO),
            "quantitative_or_static_result": "r4 speedup_current_over_batched=0.739827 at N=1024 and 0.671246 at N=512",
            "code_permission": "DENY",
            "next_action": "do not reopen this batching shape",
        },
        {
            "candidate": "new_torus_to_DFT_backend_kernel",
            "mechanism_type": "backend_primitive",
            "status": "OPEN_ONLY_EXTERNALLY",
            "best_evidence": rel(BUDGET_CSV),
            "quantitative_or_static_result": f"must beat component speedup {req}; no local MOSFHET code path identified",
            "code_permission": "DENY_LOCAL_CODE",
            "next_action": "requires backend-library kernel work or external perf evidence, not local SAB code",
        },
        {
            "candidate": "lazy_DFT_or_DFT_state_accumulator",
            "mechanism_type": "representation_change",
            "status": "REJECTED_OR_PROOF_BLOCKED",
            "best_evidence": f"{rel(STAGE156_SUMMARY)}; {rel(STAGE164_SUMMARY)}",
            "quantitative_or_static_result": "naive lazy DFT rejected; representation change needs closure/noise proof",
            "code_permission": "DENY",
            "next_action": "keep as proof route only",
        },
    ]


def build_next_rows() -> List[Dict[str, str]]:
    return [
        {
            "stage": "Stage195",
            "title": "Scoped Paper/Repro Refresh",
            "status": "NEXT",
            "goal": "freeze the current exact PVW/MAT-SAB engineering result, negative frontiers, and compact proof blockers into a clean report/repro package",
            "required_inputs": "repro/stage188_scoped_manuscript_skeleton/summary.csv; repro/stage192_compact_admission_route_selection/summary.csv; repro/stage193_exact_addmul_dataflow_preflight/summary.csv; repro/stage194_exact_dft_conversion_preflight/summary.csv",
            "correctness_gate": "claim guard forbids compact implementation, theoretical optimality, or unverified novelty",
            "performance_gate": "only Stage178/169 complete-SAB T_bootstrap/r evidence may be used as speedup",
            "failure_action": "repair claim ledger and manuscript skeleton",
        },
        {
            "stage": "Future backend route",
            "title": "External FFT Backend Primitive Work",
            "status": "OPTIONAL_EXTERNAL",
            "goal": "only if a new backend torus_to_DFT primitive is available, rerun Stage180/Stage194 budgets",
            "required_inputs": "new backend implementation; repro/stage194_exact_dft_conversion_preflight/component_budget.csv",
            "correctness_gate": "bit-exact conversion equivalence",
            "performance_gate": "component speedup above Stage180 requirement and complete-SAB A/B",
            "failure_action": "record neutral backend ablation",
        },
    ]


def build_summary_rows(candidate_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    inputs = [
        POLY_C,
        PVW_C,
        MATTRGSW_C,
        STAGE180_DERIVED,
        STAGE193_SUMMARY,
        STAGE174_SUMMARY,
        STAGE163_SUMMARY,
        STAGE162_SUMMARY,
        STAGE136_SUMMARY,
        STAGE137_SUMMARY,
    ]
    ok = all(path.exists() for path in inputs)
    promoted = [row for row in candidate_rows if row["code_permission"].startswith("ALLOW")]
    open_external = [row for row in candidate_rows if row["status"].startswith("OPEN")]
    return [
        {
            "gate": "stage194_inputs",
            "status": "PASS" if ok else "FAIL",
            "metric": "required_inputs_present",
            "value": "1" if ok else "0",
            "evidence": f"{rel(POLY_C)}; {rel(STAGE180_DERIVED)}; {rel(STAGE174_SUMMARY)}; {rel(STAGE163_SUMMARY)}",
            "detail": "Stage194 consumes DFT/conversion source, Stage180 budgets, and prior DFT/backend gates.",
            "next_action": "Repair missing inputs before interpreting preflight.",
        },
        {
            "gate": "stage194_source_prior_audit",
            "status": "PASS_RECORDED",
            "metric": "source_facts;prior_gates",
            "value": "5;6",
            "evidence": f"{rel(SOURCE_CSV)}; {rel(PRIOR_CSV)}",
            "detail": "Current path already uses backend fused add and cached FFT processors; prior backend batching/direct-scale candidates were neutral.",
            "next_action": "Screen only new mechanisms.",
        },
        {
            "gate": "stage194_component_budget",
            "status": "PASS_RECORDED",
            "metric": "torus_to_dft_required_speedup",
            "value": "1.208076492",
            "evidence": rel(BUDGET_CSV),
            "detail": "DFT conversion can matter only if a new mechanism exceeds the complete-SAB projection threshold.",
            "next_action": "Deny local code if no candidate reaches the threshold.",
        },
        {
            "gate": "stage194_code_permission",
            "status": "DENY_NO_LOCAL_DFT_CODE_CANDIDATE",
            "metric": "promoted_candidates;external_only_candidates",
            "value": f"{len(promoted)};{len(open_external)}",
            "evidence": rel(CANDIDATE_CSV),
            "detail": "All local DFT/conversion candidates are rejected, neutral, or proof-blocked; only external backend primitive work remains optional.",
            "next_action": "Route to Stage195 scoped paper/repro refresh.",
        },
        {
            "gate": "stage194_decision",
            "status": DECISION,
            "metric": "next_stage",
            "value": "Stage195",
            "evidence": rel(NEXT_CSV),
            "detail": "The local implementation frontier is exhausted under current gates; consolidate report/repro rather than speculate.",
            "next_action": "Proceed to Stage195.",
        },
    ]


def write_docs(
    summary_rows: List[Dict[str, str]],
    source_rows: List[Dict[str, str]],
    prior_rows: List[Dict[str, str]],
    budget_rows: List[Dict[str, str]],
    candidate_rows: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
) -> None:
    write_text_lf(
        OUT_MD,
        f"""# Stage194 Exact DFT/Conversion Preflight

Decision: `{DECISION}`.

Stage194 executes the DFT/conversion route selected by Stage193. It performs a
source/prior-gate/budget audit before any implementation.

Result: no local DFT/conversion code candidate is authorized. Same-format call
count reduction is closed, backend batching and direct-scale candidates were
neutral, batched decompose-to-DFT missed its target, and lazy DFT state is not
closed. Only an external backend primitive route remains possible, and it must
restart with equivalence and complete-SAB gates.

## Gate Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Source Facts

{table(source_rows, ["fact", "status", "line", "evidence", "implication"])}
## Prior Gate Matrix

{table(prior_rows, ["gate", "route", "status", "quantitative_result", "evidence", "consequence"])}
## Component Budget

{table(budget_rows, ["component", "full_sab_share", "required_component_speedup_for_3pct_full_sab", "per_call_us", "loads", "stores", "fp512", "cache_miss_rate", "evidence", "interpretation"])}
## Mechanism Candidates

{table(candidate_rows, ["candidate", "mechanism_type", "status", "best_evidence", "quantitative_or_static_result", "code_permission", "next_action"])}
## Next Stage Queue

{table(next_rows, ["stage", "title", "status", "goal", "required_inputs", "correctness_gate", "performance_gate", "failure_action"])}
""",
    )

    write_text_lf(
        PLAN_MD,
        """# Stage194 Plan

Goal: decide whether exact DFT/conversion has a local implementation candidate
before writing code.

Rules:

- no source changes;
- do not repeat Stage163 component-major batching or Stage174 direct-scale;
- do not claim same-format materialization-count reduction after Stage162;
- require a component mechanism above the Stage180 3% complete-SAB threshold;
- if no candidate is promoted, route to scoped paper/repro refresh.
""",
    )

    write_text_lf(
        THEORY_MD,
        """# Stage194 Exact DFT/Conversion Model

Current exact MAT-RLWE SAB has a torus-input MAT external product:

```text
torus accumulator -> gadget decomposition -> torus_to_DFT rows -> DFT addmul -> DFT_to_torus materialization
```

Stage162 proves that same-format materialization count is tight: observed
`from_DFT` calls equal the MAT EP calls under the current API. Stage156 rejects
the naive lazy-DFT accumulator because the next gadget decomposition is
coefficient-domain and nonlinear.

Therefore a valid Stage194 implementation candidate must either:

1. make the backend DFT/conversion primitive faster enough to exceed the
   Stage180 complete-SAB projection threshold; or
2. change the representation/API and then satisfy closure, phase, noise, and
   resource gates.

No current local candidate satisfies these conditions.
""",
    )

    write_text_lf(
        VARIANT_MD,
        """# Exact DFT/Conversion Preflight Candidate

This is a preflight card, not an implementation.

Rejected local candidates:

- same-format materialization-count reduction;
- component-major from_DFT batching;
- direct-scale/fused-add variants;
- batched decompose-to-DFT;
- naive lazy-DFT accumulator.

Open only externally:

- a new backend torus_to_DFT/from_DFT primitive with exact equivalence and
  measured component speedup above the Stage180 threshold.

Next route: scoped paper/repro refresh.
""",
    )


def update_global_docs() -> None:
    append_once(
        ROADMAP_MD,
        "## Stage 194: Exact DFT/Conversion Preflight",
        f"""
## Stage 194: Exact DFT/Conversion Preflight

Goal:

```text
Screen exact DFT/conversion mechanisms before implementation.
```

Status:

```text
Completed. Stage194 records {DECISION}. No local DFT/conversion code candidate
is promoted; route next to Stage195 scoped paper/repro refresh.
```
""",
    )

    append_once(
        GOAL_MD,
        "Stage194 records exact DFT/conversion preflight",
        f"""
Stage194 records exact DFT/conversion preflight. Decision: `{DECISION}`.
No local DFT/conversion implementation is authorized; the loop routes to
scoped paper/repro refresh unless an external backend primitive is supplied.
""",
    )

    append_once(
        CURRENT_GOAL_MD,
        "Treat Stage194 as exact DFT/conversion preflight",
        f"""
98. Treat Stage194 as exact DFT/conversion preflight:
    `{DECISION}`. DFT/conversion code remains denied: same-format count
    reduction is closed, backend batching/direct-scale candidates were neutral,
    and representation routes need closure/noise proof. Next route: Stage195
    scoped paper/repro refresh.
""",
    )

    append_once(
        HYPOTHESIS_YAML,
        "H118_exact_dft_conversion_preflight",
        f"""
  - id: H118_exact_dft_conversion_preflight
    statement: >
      Exact DFT/conversion should not receive local code unless a mechanism
      exceeds the Stage180 complete-SAB projection threshold and preserves
      exact-state closure.
    mechanism: >
      Stage194 combines source facts, prior DFT/backend gates, Stage180 budget
      requirements, and representation-closure blockers.
    status: stage194_exact_dft_preflight_no_code
    evidence: docs/stage194_exact_dft_conversion_preflight.md; experiments/stage194_exact_dft_conversion_preflight_plan.md; theory_checks/stage194_exact_dft_conversion_model.md; repro/stage194_exact_dft_conversion_preflight/summary.csv
    current_decision: >
      {DECISION}
    failure_criteria:
      - local DFT/conversion code is written despite no promoted mechanism
      - Stage163/174 neutral candidates are reopened without new mechanism
      - backend timing is reported as algorithmic count reduction
""",
    )

    append_once(
        RUN_LOG,
        "stage194-exact-dft-conversion-preflight-001",
        f"""
stage194-exact-dft-conversion-preflight-001,2026-07-04,{git_head()},Stage 194,analysis,python scripts/build_stage194_exact_dft_conversion_preflight.py,Stage193 route and DFT prior gates,none,{DECISION},Exact DFT/conversion preflight denies local code and routes to scoped refresh.,repro/stage194_exact_dft_conversion_preflight
""",
    )

    append_once(
        MANIFEST,
        "stage194_exact_dft_conversion_preflight",
        f"""
- stage194_exact_dft_conversion_preflight: `{DECISION}`
  - `docs/stage194_exact_dft_conversion_preflight.md`
  - `experiments/stage194_exact_dft_conversion_preflight_plan.md`
  - `theory_checks/stage194_exact_dft_conversion_model.md`
  - `algorithm_variants/mat_rlwe_sab_exact_dft_conversion_preflight.md`
  - `repro/stage194_exact_dft_conversion_preflight/`
""",
    )

    append_once(CHECKLIST, "Stage194 exact DFT/conversion preflight recorded", """
- [x] Stage194 exact DFT/conversion preflight recorded.
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
    source_rows = build_source_rows()
    prior_rows = build_prior_rows()
    budget_rows = build_budget_rows()
    candidate_rows = build_candidate_rows()
    next_rows = build_next_rows()
    summary_rows = build_summary_rows(candidate_rows)

    write_csv(SOURCE_CSV, source_rows, ["fact", "status", "line", "evidence", "implication"])
    write_csv(PRIOR_CSV, prior_rows, ["gate", "route", "status", "quantitative_result", "evidence", "consequence"])
    write_csv(
        BUDGET_CSV,
        budget_rows,
        [
            "component",
            "full_sab_share",
            "required_component_speedup_for_3pct_full_sab",
            "per_call_us",
            "loads",
            "stores",
            "fp512",
            "cache_miss_rate",
            "evidence",
            "interpretation",
        ],
    )
    write_csv(CANDIDATE_CSV, candidate_rows, ["candidate", "mechanism_type", "status", "best_evidence", "quantitative_or_static_result", "code_permission", "next_action"])
    write_csv(NEXT_CSV, next_rows, ["stage", "title", "status", "goal", "required_inputs", "correctness_gate", "performance_gate", "failure_action"])
    write_csv(SUMMARY_CSV, summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    write_docs(summary_rows, source_rows, prior_rows, budget_rows, candidate_rows, next_rows)
    update_global_docs()
    write_artifacts(
        [
            OUT_MD,
            PLAN_MD,
            THEORY_MD,
            VARIANT_MD,
            SUMMARY_CSV,
            SOURCE_CSV,
            PRIOR_CSV,
            BUDGET_CSV,
            CANDIDATE_CSV,
            NEXT_CSV,
            Path(__file__),
        ]
    )
    print(DECISION)


if __name__ == "__main__":
    main()
