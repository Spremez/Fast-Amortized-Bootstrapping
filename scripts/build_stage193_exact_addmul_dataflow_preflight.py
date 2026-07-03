#!/usr/bin/env python3
"""Stage193: exact full-MAT addmul dataflow preflight."""

from __future__ import annotations

import csv
import hashlib
import math
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage193_exact_addmul_dataflow_preflight"

SUMMARY_CSV = OUT_DIR / "summary.csv"
SOURCE_CSV = OUT_DIR / "source_facts.csv"
COUNTER_CSV = OUT_DIR / "counter_summary.csv"
DATAFLOW_CSV = OUT_DIR / "dataflow_candidates.csv"
PROJECTION_CSV = OUT_DIR / "projection_bounds.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage193_exact_addmul_dataflow_preflight.md"
PLAN_MD = ROOT / "experiments" / "stage193_exact_addmul_dataflow_preflight_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage193_exact_addmul_dataflow_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_exact_addmul_dataflow_preflight.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

MATTRGSW_C = ROOT / "src" / "mosfhet" / "src" / "mattrgsw.c"
MAKEFILE_DEF = ROOT / "src" / "mosfhet" / "Makefile.def"
STAGE180_DERIVED = ROOT / "repro" / "stage180_mat_ep_split_probe" / "derived_projection.csv"
STAGE180_COUNTERS = ROOT / "repro" / "stage180_mat_ep_split_probe" / "counter_metrics.csv"
STAGE180_RUN = ROOT / "repro" / "stage180_mat_ep_split_probe" / "run_metrics.csv"
STAGE182_FRONTIER = ROOT / "repro" / "stage182_exact_path_negative_frontier" / "frontier_decisions.csv"
STAGE183_MECHANISMS = ROOT / "repro" / "stage183_addmul_dataflow_screen" / "mechanism_screen.csv"
STAGE192_ROUTE = ROOT / "repro" / "stage192_compact_admission_route_selection" / "route_selection.csv"

DECISION = "PASS_STAGE193_EXACT_ADDMUL_PREFLIGHT_NO_CODE_ROUTE_DFT_MECHANISM"


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


def find_line(pattern: str, path: Path = MATTRGSW_C) -> str:
    for idx, line in enumerate(read_text(path).splitlines(), start=1):
        if pattern in line:
            return str(idx)
    return ""


def derived_value(metric: str) -> str:
    for row in read_csv_dicts(STAGE180_DERIVED):
        if row.get("metric") == metric:
            return row.get("value", "")
    return ""


def addmul_required_speedup() -> float:
    raw = derived_value("addmul_from_dec_dft_full_sab_share_and_3pct_requirement")
    parts = raw.split(";")
    return f(parts[1]) if len(parts) > 1 else 1.151228774


def addmul_full_sab_share() -> float:
    raw = derived_value("addmul_from_dec_dft_full_sab_share_and_3pct_requirement")
    parts = raw.split(";")
    return f(parts[0]) if parts else 0.221723249


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


def full_sab_speedup_bound(component_share: float, component_speedup: float) -> float:
    if component_speedup <= 0:
        return 1.0
    return 1.0 / ((1.0 - component_share) + component_share / component_speedup)


def build_source_rows() -> List[Dict[str, str]]:
    makefile = read_text(MAKEFILE_DEF)
    return [
        {
            "fact": "complex_addmul_uses_avx512_fma",
            "status": "yes",
            "line": find_line("mat_avx512_complex_addmul"),
            "evidence": rel(MATTRGSW_C),
            "implication": "The exact addmul hot loop is already vectorized; Stage193 must find dataflow savings, not basic AVX512 enablement.",
        },
        {
            "fact": "rgt4_tiled_kernel_reuses_dec_per_output_tile",
            "status": "yes",
            "line": find_line("mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_rgt4_tiled_avx512"),
            "evidence": rel(MATTRGSW_C),
            "implication": "For r=6, dec rows are loaded once per output tile; this is the only local duplicate-load opportunity.",
        },
        {
            "fact": "r6_fulltile_exists",
            "status": "yes",
            "line": find_line("mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r6_fulltile_avx512"),
            "evidence": rel(MATTRGSW_C),
            "implication": "All-output register-resident accumulation was already implemented and rejected by prior gates.",
        },
        {
            "fact": "r6_bodymajor_exists",
            "status": "yes",
            "line": find_line("mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r6_bodymajor_avx512"),
            "evidence": rel(MATTRGSW_C),
            "implication": "Output-major dataflow was already implemented and rejected by prior gates.",
        },
        {
            "fact": "sub_decomp_avx512_exists_default_off",
            "status": "yes" if "MAT_TRGSW_AVX512_SUB_DECOMP ?= false" in makefile else "unknown",
            "line": find_line("MAT_TRGSW_AVX512_SUB_DECOMP ?= false", MAKEFILE_DEF),
            "evidence": rel(MAKEFILE_DEF),
            "implication": "Sub-decompose vectorization remains an explicit negative ablation, not a promoted path.",
        },
    ]


def build_counter_rows() -> List[Dict[str, str]]:
    loads = counter_value("addmul_from_dec_dft", "mem_inst_retired.all_loads")
    stores = counter_value("addmul_from_dec_dft", "mem_inst_retired.all_stores")
    cache_refs = counter_value("addmul_from_dec_dft", "cache-references")
    cache_misses = counter_value("addmul_from_dec_dft", "cache-misses")
    fp512 = counter_value("addmul_from_dec_dft", "fp_arith_inst_retired.512b_packed_double")
    cycles = counter_value("addmul_from_dec_dft", "cycles")
    instructions = counter_value("addmul_from_dec_dft", "instructions")
    per_call = run_value("addmul_from_dec_dft", "per_call_us")
    miss_rate = cache_misses / cache_refs if cache_refs else 0.0
    ipc = instructions / cycles if cycles else 0.0
    return [
        {
            "variant": "addmul_from_dec_dft",
            "per_call_us": f"{per_call:.9f}",
            "loads": f"{loads:.0f}",
            "stores": f"{stores:.0f}",
            "fp512": f"{fp512:.0f}",
            "cache_miss_rate": f"{miss_rate:.6f}",
            "ipc": f"{ipc:.6f}",
            "evidence": rel(STAGE180_COUNTERS),
            "interpretation": "Low cache-miss rate and heavy FP512 mean prefetch-only is weak; only real load/store reduction or fewer FMA-equivalent ops can matter.",
        }
    ]


def mem_model(r: int, tile_outputs: int) -> Dict[str, float]:
    outputs = r + 1
    rows = r + 1
    tiles = math.ceil(outputs / tile_outputs)
    selector_loads = rows * outputs * 2
    dec_loads_current = rows * tiles * 2
    dec_loads_cached = rows * 2
    output_stores = outputs * 2
    current_mem_ops = selector_loads + dec_loads_current + output_stores
    cached_mem_ops = selector_loads + dec_loads_cached + output_stores
    duplicate_dec_loads = dec_loads_current - dec_loads_cached
    upper_speedup = current_mem_ops / cached_mem_ops if cached_mem_ops else 1.0
    return {
        "r": r,
        "outputs": outputs,
        "rows": rows,
        "tiles": tiles,
        "selector_loads": selector_loads,
        "dec_loads_current": dec_loads_current,
        "dec_loads_cached": dec_loads_cached,
        "output_stores": output_stores,
        "current_mem_ops": current_mem_ops,
        "cached_mem_ops": cached_mem_ops,
        "duplicate_dec_loads": duplicate_dec_loads,
        "duplicate_fraction": duplicate_dec_loads / current_mem_ops if current_mem_ops else 0.0,
        "upper_component_speedup": upper_speedup,
    }


def build_projection_rows() -> List[Dict[str, str]]:
    share = addmul_full_sab_share()
    required = addmul_required_speedup()
    rows: List[Dict[str, str]] = []
    for r, tile in [(6, 4), (8, 4)]:
        model = mem_model(r, tile)
        full_bound = full_sab_speedup_bound(share, model["upper_component_speedup"])
        rows.append(
            {
                "candidate": "dec_register_cache_across_tiles",
                "r": str(r),
                "tile_outputs": str(tile),
                "selector_loads_per_coeff": f"{model['selector_loads']:.0f}",
                "dec_loads_current_per_coeff": f"{model['dec_loads_current']:.0f}",
                "dec_loads_cached_per_coeff": f"{model['dec_loads_cached']:.0f}",
                "duplicate_dec_load_fraction": f"{model['duplicate_fraction']:.6f}",
                "upper_component_speedup": f"{model['upper_component_speedup']:.6f}",
                "required_component_speedup_for_3pct_full_sab": f"{required:.9f}",
                "full_sab_speedup_bound": f"{full_bound:.6f}",
                "decision": "REJECT_TARGET_R6_BELOW_3PCT_GATE" if r == 6 and model["upper_component_speedup"] < required else "NON_TARGET_R8_REQUIRES_FULL_SAB_CONTEXT",
            }
        )
    return rows


def build_dataflow_rows(projection_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    r6_row = next(row for row in projection_rows if row["r"] == "6")
    return [
        {
            "candidate": "dec_register_cache_across_tiles",
            "new_mechanism": "yes",
            "prior_status": "not directly tested; adjacent fulltile exists",
            "static_or_counter_result": f"r6 upper component speedup {r6_row['upper_component_speedup']} below required {r6_row['required_component_speedup_for_3pct_full_sab']}",
            "risk": "requires keeping 14 dec registers plus tile accumulators; may spill and lose the static upper bound",
            "code_permission": "DENY_BELOW_FULL_SAB_GATE",
        },
        {
            "candidate": "all_outputs_fulltile",
            "new_mechanism": "no",
            "prior_status": "rejected",
            "static_or_counter_result": "Stage111/151 did not promote fulltile under complete-SAB gates",
            "risk": "register pressure and variance already observed",
            "code_permission": "DENY_PRIOR_REJECTED",
        },
        {
            "candidate": "bodymajor_output_major",
            "new_mechanism": "no",
            "prior_status": "rejected",
            "static_or_counter_result": "Stage154 bodymajor/tile4 complete-SAB result was slower",
            "risk": "worse complete-SAB T_bootstrap/r",
            "code_permission": "DENY_PRIOR_REJECTED",
        },
        {
            "candidate": "row_streaming_decompose_dft_addmul",
            "new_mechanism": "no",
            "prior_status": "rejected",
            "static_or_counter_result": "Stage165 streaming lost to current tiled AVX",
            "risk": "decomposition/DFT locality did not translate to speed",
            "code_permission": "DENY_PRIOR_REJECTED",
        },
        {
            "candidate": "selector_transposed_key_layout",
            "new_mechanism": "yes",
            "prior_status": "blocked",
            "static_or_counter_result": "could improve selector locality but changes key format",
            "risk": "requires keygen/resource/noise gates, not a local addmul edit",
            "code_permission": "DENY_KEY_FORMAT_GATE_REQUIRED",
        },
        {
            "candidate": "prefetch_only_selector_rows",
            "new_mechanism": "weak",
            "prior_status": "not promoted",
            "static_or_counter_result": "Stage180 addmul cache miss rate is low; no arithmetic/load-count reduction",
            "risk": "implementation-only tweak unlikely to reach complete-SAB threshold",
            "code_permission": "DENY_NO_PROJECTED_3PCT",
        },
    ]


def build_next_rows() -> List[Dict[str, str]]:
    return [
        {
            "stage": "Stage194",
            "title": "Exact DFT Conversion Mechanism Preflight",
            "status": "NEXT",
            "goal": "screen a genuinely new torus_to_DFT/from_DFT mechanism after addmul preflight found no code candidate",
            "required_inputs": f"{rel(STAGE180_DERIVED)}; repro/stage174_from_dft_direct_scale_gate/summary.csv; src/mosfhet/src/polynomial.c",
            "correctness_gate": "no source changes; specify exact DFT/conversion equivalence first",
            "performance_gate": "component speedup must exceed Stage180 3pct full-SAB requirement",
            "failure_action": "route to scoped paper/repro package rather than speculative implementation",
        },
        {
            "stage": "Stage195",
            "title": "Scoped Paper/Repro Refresh",
            "status": "CONDITIONAL",
            "goal": "if Stage194 finds no code candidate, freeze engineering result and limitations",
            "required_inputs": "repro/stage188_scoped_manuscript_skeleton/summary.csv; repro/stage192_compact_admission_route_selection/summary.csv; repro/stage193_exact_addmul_dataflow_preflight/summary.csv",
            "correctness_gate": "claim guard forbids compact/optimality overclaim",
            "performance_gate": "no new speedup claim without complete-SAB benchmark",
            "failure_action": "repair claim ledger",
        },
    ]


def build_summary_rows(
    projection_rows: List[Dict[str, str]],
    dataflow_rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    inputs = [MATTRGSW_C, MAKEFILE_DEF, STAGE180_DERIVED, STAGE180_COUNTERS, STAGE182_FRONTIER, STAGE183_MECHANISMS, STAGE192_ROUTE]
    ok = all(path.exists() for path in inputs)
    promoted = [row for row in dataflow_rows if row["code_permission"].startswith("ALLOW")]
    r6_bound = next(row["full_sab_speedup_bound"] for row in projection_rows if row["r"] == "6")
    return [
        {
            "gate": "stage193_inputs",
            "status": "PASS" if ok else "FAIL",
            "metric": "required_inputs_present",
            "value": "1" if ok else "0",
            "evidence": f"{rel(MATTRGSW_C)}; {rel(STAGE180_DERIVED)}; {rel(STAGE183_MECHANISMS)}",
            "detail": "Stage193 consumes source facts, Stage180 counters, and prior rejected mechanism ledgers.",
            "next_action": "Repair missing inputs before interpreting preflight.",
        },
        {
            "gate": "stage193_source_counter_audit",
            "status": "PASS_RECORDED",
            "metric": "source_facts;counter_rows",
            "value": "5;1",
            "evidence": f"{rel(SOURCE_CSV)}; {rel(COUNTER_CSV)}",
            "detail": "Current exact addmul is already AVX512 FMA and prior r6 dataflow families exist as explicit flags.",
            "next_action": "Screen only genuinely new mechanisms.",
        },
        {
            "gate": "stage193_dec_cache_projection",
            "status": "REJECT_BELOW_COMPLETE_SAB_GATE",
            "metric": "r6_full_sab_speedup_bound",
            "value": r6_bound,
            "evidence": rel(PROJECTION_CSV),
            "detail": "The only local duplicate-load mechanism has an optimistic r=6 bound below the 3pct complete-SAB promotion threshold.",
            "next_action": "Do not implement dec-cache tile variant.",
        },
        {
            "gate": "stage193_code_permission",
            "status": "DENY_NO_ADDMUL_CODE_CANDIDATE",
            "metric": "promoted_candidates",
            "value": str(len(promoted)),
            "evidence": rel(DATAFLOW_CSV),
            "detail": "All addmul candidates are prior-rejected, key-format-blocked, or below the projected complete-SAB gate.",
            "next_action": "Route to Stage194 DFT conversion mechanism preflight.",
        },
        {
            "gate": "stage193_decision",
            "status": DECISION,
            "metric": "next_stage",
            "value": "Stage194",
            "evidence": rel(NEXT_CSV),
            "detail": "Exact addmul preflight avoids speculative implementation and routes to the secondary DFT mechanism.",
            "next_action": "Proceed to Stage194.",
        },
    ]


def write_docs(
    summary_rows: List[Dict[str, str]],
    source_rows: List[Dict[str, str]],
    counter_rows: List[Dict[str, str]],
    projection_rows: List[Dict[str, str]],
    dataflow_rows: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
) -> None:
    write_text_lf(
        OUT_MD,
        f"""# Stage193 Exact Addmul Dataflow Preflight

Decision: `{DECISION}`.

Stage193 executes the non-theory route selected by Stage192. It audits the
exact full-MAT addmul path before code. The result is no-code: every candidate
is already rejected, requires a key-format gate, or fails the projected
complete-SAB `T_bootstrap/r` promotion threshold.

The only new local mechanism identified is caching decomposed DFT rows across
the r=6 output tiles. Its optimistic memory-op upper bound is below the
Stage180 component speedup required for a 3% complete-SAB gain.

## Gate Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Source Facts

{table(source_rows, ["fact", "status", "line", "evidence", "implication"])}
## Counter Summary

{table(counter_rows, ["variant", "per_call_us", "loads", "stores", "fp512", "cache_miss_rate", "ipc", "evidence", "interpretation"])}
## Projection Bounds

{table(projection_rows, ["candidate", "r", "tile_outputs", "selector_loads_per_coeff", "dec_loads_current_per_coeff", "dec_loads_cached_per_coeff", "duplicate_dec_load_fraction", "upper_component_speedup", "required_component_speedup_for_3pct_full_sab", "full_sab_speedup_bound", "decision"])}
## Dataflow Candidates

{table(dataflow_rows, ["candidate", "new_mechanism", "prior_status", "static_or_counter_result", "risk", "code_permission"])}
## Next Stage Queue

{table(next_rows, ["stage", "title", "status", "goal", "required_inputs", "correctness_gate", "performance_gate", "failure_action"])}
""",
    )

    write_text_lf(
        PLAN_MD,
        """# Stage193 Plan

Goal: decide whether exact full-MAT addmul has a new implementation candidate
before writing code.

Rules:

- no source changes;
- reject prior fulltile/bodymajor/streaming families unless a changed dataflow
  mechanism is identified;
- require projected >=3% complete-SAB gain before code;
- separate source/static/counter evidence from real benchmarks.
""",
    )

    write_text_lf(
        THEORY_MD,
        """# Stage193 Addmul Dataflow Model

For r=6, k=1, l=1 exact full-MAT addmul has seven input rows and seven output
polynomials. The current tile4 kernel updates four outputs at a time, so it
loads each decomposed DFT row once per output tile.

Candidate: cache the decomposed row registers across output tiles. Static
memory-op model:

```text
selector vector loads = rows * outputs * 2
current dec loads     = rows * tiles * 2
cached dec loads      = rows * 2
output stores         = outputs * 2
```

For r=6 and tile size 4, this removes only 14 vector dec loads per coefficient
out of 140 modeled load/store ops. The optimistic component speedup is
`1.111111`, below the Stage180 addmul component speedup required for a 3%
complete-SAB gain. This is an upper bound because it ignores register spills
from holding 14 dec vectors plus accumulators.
""",
    )

    write_text_lf(
        VARIANT_MD,
        """# Exact Addmul Dataflow Preflight Candidate

This is a preflight card, not an implementation.

## Candidate: dec-register cache across output tiles

- Parent algorithm: exact full-MAT PVW/MAT-SAB.
- Focused module: `mat_trgsw_mul_pvmtmlwe_DFT_from_dec` r>4 AVX512 addmul.
- Optimization target: complete-SAB `T_bootstrap/r`.
- Status: rejected before code.

## Reason

The candidate reduces duplicate dec-row loads in the current r=6 tile4 kernel,
but its optimistic upper bound does not reach the component speedup needed for
a 3% complete-SAB gain. It also risks register spills.

## Required Future Evidence To Reopen

- measured native counter evidence showing a larger-than-modeled load-store
  bottleneck;
- a new dataflow that reduces selector loads or FMA-equivalent operations, not
  only duplicate dec loads;
- deterministic equivalence and complete-SAB projection before implementation.
""",
    )


def update_global_docs() -> None:
    append_once(
        ROADMAP_MD,
        "## Stage 193: Exact Addmul Dataflow Preflight",
        f"""
## Stage 193: Exact Addmul Dataflow Preflight

Goal:

```text
Screen exact full-MAT addmul dataflow candidates before implementation.
```

Status:

```text
Completed. Stage193 records {DECISION}. No addmul code candidate is promoted:
dec-register caching is below the complete-SAB projection gate, and prior
fulltile/bodymajor/streaming families remain rejected.
```
""",
    )

    append_once(
        GOAL_MD,
        "Stage193 records exact addmul dataflow preflight",
        f"""
Stage193 records exact addmul dataflow preflight. Decision: `{DECISION}`.
No exact addmul implementation is authorized; the research loop routes next to
a DFT/conversion mechanism preflight.
""",
    )

    append_once(
        CURRENT_GOAL_MD,
        "Treat Stage193 as exact addmul dataflow preflight",
        f"""
97. Treat Stage193 as exact addmul dataflow preflight:
    `{DECISION}`. Addmul code remains denied: the only new local dec-cache
    mechanism has an optimistic r=6 bound below the 3% complete-SAB gate, and
    prior fulltile/bodymajor/streaming families remain rejected. Next route:
    Stage194 DFT/conversion mechanism preflight.
""",
    )

    append_once(
        HYPOTHESIS_YAML,
        "H117_exact_addmul_dataflow_preflight",
        f"""
  - id: H117_exact_addmul_dataflow_preflight
    statement: >
      Exact full-MAT addmul should not receive new code unless a dataflow
      mechanism projects at least a 3% complete-SAB T_bootstrap/r gain.
    mechanism: >
      Stage193 combines source facts, Stage180 counters, prior mechanism
      rejections, and a static memory-op model for dec-register caching.
    status: stage193_exact_addmul_preflight_no_code
    evidence: docs/stage193_exact_addmul_dataflow_preflight.md; experiments/stage193_exact_addmul_dataflow_preflight_plan.md; theory_checks/stage193_exact_addmul_dataflow_model.md; repro/stage193_exact_addmul_dataflow_preflight/summary.csv
    current_decision: >
      {DECISION}
    failure_criteria:
      - addmul code is written without a projected >=3% complete-SAB gain
      - a prior rejected layout family is reopened under a new name
      - static projection is reported as measured performance
""",
    )

    append_once(
        RUN_LOG,
        "stage193-exact-addmul-dataflow-preflight-001",
        f"""
stage193-exact-addmul-dataflow-preflight-001,2026-07-04,{git_head()},Stage 193,analysis,python scripts/build_stage193_exact_addmul_dataflow_preflight.py,Stage192 route selection and Stage180 counters,none,{DECISION},Exact addmul source/counter preflight denies new code and routes to DFT mechanism.,repro/stage193_exact_addmul_dataflow_preflight
""",
    )

    append_once(
        MANIFEST,
        "stage193_exact_addmul_dataflow_preflight",
        f"""
- stage193_exact_addmul_dataflow_preflight: `{DECISION}`
  - `docs/stage193_exact_addmul_dataflow_preflight.md`
  - `experiments/stage193_exact_addmul_dataflow_preflight_plan.md`
  - `theory_checks/stage193_exact_addmul_dataflow_model.md`
  - `algorithm_variants/mat_rlwe_sab_exact_addmul_dataflow_preflight.md`
  - `repro/stage193_exact_addmul_dataflow_preflight/`
""",
    )

    append_once(CHECKLIST, "Stage193 exact addmul dataflow preflight recorded", """
- [x] Stage193 exact addmul dataflow preflight recorded.
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
    counter_rows = build_counter_rows()
    projection_rows = build_projection_rows()
    dataflow_rows = build_dataflow_rows(projection_rows)
    next_rows = build_next_rows()
    summary_rows = build_summary_rows(projection_rows, dataflow_rows)

    write_csv(SOURCE_CSV, source_rows, ["fact", "status", "line", "evidence", "implication"])
    write_csv(COUNTER_CSV, counter_rows, ["variant", "per_call_us", "loads", "stores", "fp512", "cache_miss_rate", "ipc", "evidence", "interpretation"])
    write_csv(
        PROJECTION_CSV,
        projection_rows,
        [
            "candidate",
            "r",
            "tile_outputs",
            "selector_loads_per_coeff",
            "dec_loads_current_per_coeff",
            "dec_loads_cached_per_coeff",
            "duplicate_dec_load_fraction",
            "upper_component_speedup",
            "required_component_speedup_for_3pct_full_sab",
            "full_sab_speedup_bound",
            "decision",
        ],
    )
    write_csv(DATAFLOW_CSV, dataflow_rows, ["candidate", "new_mechanism", "prior_status", "static_or_counter_result", "risk", "code_permission"])
    write_csv(NEXT_CSV, next_rows, ["stage", "title", "status", "goal", "required_inputs", "correctness_gate", "performance_gate", "failure_action"])
    write_csv(SUMMARY_CSV, summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    write_docs(summary_rows, source_rows, counter_rows, projection_rows, dataflow_rows, next_rows)
    update_global_docs()
    write_artifacts(
        [
            OUT_MD,
            PLAN_MD,
            THEORY_MD,
            VARIANT_MD,
            SUMMARY_CSV,
            SOURCE_CSV,
            COUNTER_CSV,
            DATAFLOW_CSV,
            PROJECTION_CSV,
            NEXT_CSV,
            Path(__file__),
        ]
    )
    print(DECISION)


if __name__ == "__main__":
    main()
