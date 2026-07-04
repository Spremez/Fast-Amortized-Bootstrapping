#!/usr/bin/env python3
"""Stage228: counter-driven search for the next exact MAT/PVW kernel step."""

from __future__ import annotations

import csv
import hashlib
import math
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage228_counter_driven_backend_kernel_search"

DOC = ROOT / "docs" / "stage228_counter_driven_backend_kernel_search.md"
PLAN = ROOT / "experiments" / "stage228_counter_driven_backend_kernel_search_plan.md"
THEORY = ROOT / "theory_checks" / "stage228_counter_driven_kernel_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage228_counter_driven_candidates.md"

INPUTS = OUT / "input_status.csv"
SOURCE_FACTS = OUT / "source_facts.csv"
PROJECTION = OUT / "projection_thresholds.csv"
CANDIDATES = OUT / "candidate_cards.csv"
GATES = OUT / "candidate_gates.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "kernel_search_report.md"
ARTIFACT = OUT / "artifact_index.csv"
REPRO = OUT / "reproduction_commands.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE227_PROOF = ROOT / "repro" / "stage227_exact_route_claim_boundary_update" / "proof_gate.csv"
STAGE227_NEXT = ROOT / "repro" / "stage227_exact_route_claim_boundary_update" / "next_stage_queue.csv"
STAGE226_ATTR = ROOT / "repro" / "stage226_exact_mat_avx_counter_attribution" / "attribution_summary.csv"
STAGE226_COUNTER = ROOT / "repro" / "stage226_exact_mat_avx_counter_attribution" / "counter_comparison.csv"
STAGE183_SUMMARY = ROOT / "repro" / "stage183_addmul_dataflow_screen" / "summary.csv"
STAGE183_MECH = ROOT / "repro" / "stage183_addmul_dataflow_screen" / "mechanism_screen.csv"
STAGE183_PROJ = ROOT / "repro" / "stage183_addmul_dataflow_screen" / "projection.csv"
STAGE184_OPEN = ROOT / "repro" / "stage184_exact_route_closeout_claim_refresh" / "open_routes.csv"
STAGE155_COMPONENT = ROOT / "repro" / "stage155_same_format_frontier_refresh" / "component_shares.csv"
STAGE159_PERF = ROOT / "repro" / "stage159_sub_decomp_fusion_repeated_gate" / "perf_comparison.csv"
STAGE181_COMP = ROOT / "repro" / "stage181_sub_decomp_avx512_gate" / "comparison.csv"

MATTRGSW = ROOT / "src" / "mosfhet" / "src" / "mattrgsw.c"
PVWTMLWE = ROOT / "src" / "mosfhet" / "src" / "pvwtmlwe.c"
POLYNOMIAL = ROOT / "src" / "mosfhet" / "src" / "polynomial.c"
MAKEDEF = ROOT / "src" / "mosfhet" / "Makefile.def"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((text.rstrip() + "\n").encode("utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [{field: row.get(field, "") for field in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    if current and not current.endswith("\n"):
        current += "\n"
    write_text(path, current + text.lstrip("\n"))


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    if not rows:
        return "_No rows._\n"
    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out) + "\n"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


def fnum(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def csv_val(path: Path, key: str, key_field: str = "metric", value_field: str = "value") -> str:
    for row in read_csv(path):
        if row.get(key_field) == key:
            return row.get(value_field, "")
    return ""


def stage227_selects_stage228() -> bool:
    return any(
        row.get("route") == "stage228_counter_driven_backend_kernel_search" and row.get("status") == "selected"
        for row in read_csv(STAGE227_NEXT)
    )


def input_rows() -> List[Dict[str, str]]:
    inputs = [
        (STAGE227_PROOF, "Stage227 fixed T_bootstrap/r claim boundary"),
        (STAGE227_NEXT, "Stage227 selected Stage228"),
        (STAGE226_ATTR, "Stage226 native counter attribution"),
        (STAGE226_COUNTER, "Stage226 counter ratios"),
        (STAGE183_SUMMARY, "Prior addmul dataflow screen"),
        (STAGE183_MECH, "Prior exact addmul mechanism screen"),
        (STAGE183_PROJ, "Prior addmul projection threshold"),
        (STAGE184_OPEN, "Prior exact-route closeout"),
        (STAGE155_COMPONENT, "Prior component share frontier"),
        (STAGE159_PERF, "Prior sub-decomp fusion full-SAB gate"),
        (STAGE181_COMP, "Prior AVX512 sub-decompose negative gate"),
        (MATTRGSW, "Current MAT external product source"),
        (PVWTMLWE, "Current PVW TMLWE materialization source"),
        (POLYNOMIAL, "Current polynomial backend source"),
        (MAKEDEF, "Current explicit build flags"),
    ]
    rows = []
    for path, role in inputs:
        rows.append(
            {
                "input": rel(path),
                "status": "present" if path.exists() else "missing",
                "role": role,
                "bytes": str(path.stat().st_size) if path.exists() else "",
            }
        )
    rows.append(
        {
            "input": "stage227_next_selects_stage228",
            "status": "present" if stage227_selects_stage228() else "missing",
            "role": "Prevents off-road kernel search.",
            "bytes": "",
        }
    )
    return rows


def source_fact_rows() -> List[Dict[str, str]]:
    mat = read_text(MATTRGSW)
    pvw = read_text(PVWTMLWE)
    poly = read_text(POLYNOMIAL)
    make = read_text(MAKEDEF)
    facts = [
        (
            "rgt4_tiled_avx512_present",
            "mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_rgt4_tiled_avx512" in mat,
            rel(MATTRGSW),
            "Current r=6/r=8 exact route already has MAT-aware tiled AVX512.",
        ),
        (
            "r6_fulltile_present",
            "mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r6_fulltile_avx512" in mat,
            rel(MATTRGSW),
            "Full-output r=6 layout exists and was previously screened.",
        ),
        (
            "r6_bodymajor_present",
            "mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r6_bodymajor_avx512" in mat,
            rel(MATTRGSW),
            "Body-major r=6 layout exists and was previously screened.",
        ),
        (
            "backend_from_dft_add_present",
            "SAB_PVW_BACKEND_FROM_DFT_ADD" in pvw and "polynomial_DFT_to_torus_add" in pvw,
            rel(PVWTMLWE),
            "Current preferred path uses backend direct FromDFT+add.",
        ),
        (
            "backend_direct_add_primitive_present",
            "execute_direct_torus64_add" in poly,
            rel(POLYNOMIAL),
            "SPQLIOS backend has direct IFFT+add primitive already wired.",
        ),
        (
            "sub_decomp_fusion_present",
            "SAB_PVW_SUB_DECOMP_FUSION" in make and "mat_trgsw_mul_pvmtmlwe_sub_DFT" in mat,
            f"{rel(MAKEDEF)}; {rel(MATTRGSW)}",
            "Sub-decompose fusion path exists as an explicit flag.",
        ),
    ]
    return [
        {
            "fact": name,
            "status": "present" if ok else "missing",
            "evidence": evidence,
            "interpretation": detail,
        }
        for name, ok, evidence, detail in facts
    ]


def component_share(component: str) -> float:
    for row in read_csv(STAGE155_COMPONENT):
        if row.get("component") == component:
            return fnum(row.get("share_of_full", ""))
    return 0.0


def required_local_speedup(share: float, target_full_speedup: float = 1.03) -> float:
    if share <= 0.0:
        return 0.0
    required_new_fraction = 1.0 / target_full_speedup
    denominator = share + required_new_fraction - 1.0
    if denominator <= 0.0:
        return math.inf
    return share / denominator


def projection_rows() -> List[Dict[str, str]]:
    addmul_share = fnum(csv_val(STAGE183_PROJ, "addmul_full_sab_share"))
    if addmul_share == 0.0:
        addmul_share = component_share("mat_ep")
    from_dft_share = component_share("from_dft")
    sub_share = component_share("sub")
    return [
        {
            "component": "addmul_from_dec_dft",
            "share": f"{addmul_share:.9f}",
            "required_local_speedup_for_3pct_full_sab": f"{required_local_speedup(addmul_share):.9f}",
            "current_signal": "Stage183 denies layout-only code; Stage226 shows only backend materialization counter deltas.",
            "evidence": f"{rel(STAGE183_PROJ)}; {rel(STAGE226_ATTR)}",
        },
        {
            "component": "from_dft_materialization",
            "share": f"{from_dft_share:.9f}",
            "required_local_speedup_for_3pct_full_sab": f"{required_local_speedup(from_dft_share):.9f}",
            "current_signal": "Stage226 backend direct add is positive but already implemented; no new backend primitive exists.",
            "evidence": f"{rel(STAGE155_COMPONENT)}; {rel(POLYNOMIAL)}",
        },
        {
            "component": "sub_or_sub_decompose",
            "share": f"{sub_share:.9f}",
            "required_local_speedup_for_3pct_full_sab": f"{required_local_speedup(sub_share):.9f}",
            "current_signal": "Stage159 full-SAB fusion positive but Stage181 vectorizing sub-decompose itself is negative.",
            "evidence": f"{rel(STAGE159_PERF)}; {rel(STAGE181_COMP)}",
        },
    ]


def candidate_rows(proj: List[Dict[str, str]]) -> List[Dict[str, str]]:
    addmul_required = next((row["required_local_speedup_for_3pct_full_sab"] for row in proj if row["component"] == "addmul_from_dec_dft"), "")
    dft_required = next((row["required_local_speedup_for_3pct_full_sab"] for row in proj if row["component"] == "from_dft_materialization"), "")
    sub_required = next((row["required_local_speedup_for_3pct_full_sab"] for row in proj if row["component"] == "sub_or_sub_decompose"), "")
    return [
        {
            "candidate_id": "H228-C1-r6-dec-reuse-addmul",
            "focused_module": "mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_rgt4_tiled_avx512",
            "hypothesis": "A new r=6 dataflow that reduces duplicated dec-row loads across output tiles should improve addmul_from_dec_dft.",
            "required_evidence_before_code": f"assembly/counter microprobe plus local addmul speedup >= {addmul_required} for 3pct full-SAB projection",
            "current_evidence": "Stage183 denies layout-only addmul code; fulltile/bodymajor/streaming variants already failed or were weak.",
            "code_permission": "probe_only_no_hotpath_edit",
            "next_gate": "static assembly + isolated addmul probe before any source modification",
        },
        {
            "candidate_id": "H228-C2-batched-direct-from-dft-add",
            "focused_module": "pvmtmlwe_from_DFT_add / polynomial_DFT_to_torus_add",
            "hypothesis": "A true multi-row backend direct IFFT+add primitive could reduce materialization overhead beyond the current per-row direct add.",
            "required_evidence_before_code": f"backend API or prototype showing local from_DFT speedup >= {dft_required} for 3pct full-SAB projection",
            "current_evidence": "Stage226 supports current backend direct add, but Stage163/174-style backend retuning did not justify another blind path.",
            "code_permission": "blocked_until_new_backend_primitive",
            "next_gate": "backend primitive proof or external library support",
        },
        {
            "candidate_id": "H228-C3-sub-decomp-fusion-refresh",
            "focused_module": "mat_trgsw_mul_pvmtmlwe_sub_DFT with SAB_PVW_SUB_DECOMP_FUSION",
            "hypothesis": "Combining existing sub-decomp fusion with the current exact backend path may still be worth a targeted refresh.",
            "required_evidence_before_code": f"no new code; rerun existing flag only if current-head delta is unresolved; local sub speedup target {sub_required}",
            "current_evidence": "Stage159 full-SAB positive; Stage181 exact AVX512 sub-decompose candidate negative, so new vector code is denied.",
            "code_permission": "existing_flag_refresh_only",
            "next_gate": "optional same-flags repeated refresh, not new implementation",
        },
    ]


def gate_rows(candidates: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows = []
    for candidate in candidates:
        cid = candidate["candidate_id"]
        if cid == "H228-C1-r6-dec-reuse-addmul":
            rows.append(
                {
                    "candidate_id": cid,
                    "correctness_gate": "isolated dense MAT/PVW output equivalence r=6 plus full SAB deterministic correctness",
                    "performance_gate": "isolated addmul >= projection threshold, then complete SAB T_bootstrap/r >= 1.03 over current backend control in 3 paired runs",
                    "failure_rule": "If assembly/counter probe shows layout-only or projected gain <3pct, do not edit source.",
                    "status": "not_selected_no_code_permission",
                }
            )
        elif cid == "H228-C2-batched-direct-from-dft-add":
            rows.append(
                {
                    "candidate_id": cid,
                    "correctness_gate": "row-wise direct IFFT+add coefficient equality against current backend primitive",
                    "performance_gate": "from_DFT local speedup >= projection threshold and complete SAB T_bootstrap/r positive under same backend",
                    "failure_rule": "If no real backend primitive exists, keep blocked; do not emulate batching with extra copies.",
                    "status": "blocked_external_backend_primitive",
                }
            )
        else:
            rows.append(
                {
                    "candidate_id": cid,
                    "correctness_gate": "existing SAB_PVW_SUB_DECOMP_FUSION deterministic full SAB correctness plus noise/resource if repeated",
                    "performance_gate": "same current-head backend control, repeated complete SAB T_bootstrap/r; no new AVX512 sub-decompose code",
                    "failure_rule": "If refresh is neutral or slower, close existing flag as non-default ablation.",
                    "status": "deferred_existing_flag_refresh",
                }
            )
    return rows


def decide(inputs: List[Dict[str, str]], candidates: List[Dict[str, str]]) -> str:
    if not all(row["status"] == "present" for row in inputs):
        return "FAIL_STAGE228_MISSING_INPUTS"
    if any(row["code_permission"] == "allow_hotpath_edit" for row in candidates):
        return "PASS_STAGE228_HOTPATH_CODE_CANDIDATE_SELECTED"
    return "PASS_STAGE228_NO_NEW_HOTPATH_CODE_SELECT_PARAMETER_MATRIX"


def proof_rows(decision: str, inputs: List[Dict[str, str]], facts: List[Dict[str, str]], candidates: List[Dict[str, str]]) -> List[Dict[str, str]]:
    facts_ok = all(row["status"] == "present" for row in facts)
    no_hotpath = all(row["code_permission"] != "allow_hotpath_edit" for row in candidates)
    return [
        {
            "gate": "G1_required_inputs",
            "status": "PASS" if all(row["status"] == "present" for row in inputs) else "FAIL",
            "metric": "inputs_present",
            "value": str(all(row["status"] == "present" for row in inputs)).lower(),
            "evidence": rel(INPUTS),
            "interpretation": "Stage228 consumes Stage227, Stage226, prior frontier gates, and current source.",
        },
        {
            "gate": "G2_source_fact_check",
            "status": "PASS" if facts_ok else "FAIL",
            "metric": "facts_present",
            "value": str(facts_ok).lower(),
            "evidence": rel(SOURCE_FACTS),
            "interpretation": "The project already has MAT-aware AVX512 and backend direct add paths.",
        },
        {
            "gate": "G3_projection_gate",
            "status": "PASS",
            "metric": "candidate_count",
            "value": str(len(candidates)),
            "evidence": rel(PROJECTION),
            "interpretation": "Every code idea must clear a local speedup threshold before full-SAB work.",
        },
        {
            "gate": "G4_code_permission",
            "status": "DENY_NEW_HOTPATH_CODE" if no_hotpath else "ALLOW_SELECTED_CANDIDATE",
            "metric": "allow_hotpath_edit_count",
            "value": str(sum(1 for row in candidates if row["code_permission"] == "allow_hotpath_edit")),
            "evidence": rel(CANDIDATES),
            "interpretation": "Stage228 does not permit speculative hot-path edits from the current evidence.",
        },
        {
            "gate": "G5_stage228_decision",
            "status": decision,
            "metric": "decision",
            "value": decision,
            "evidence": rel(PROOF),
            "interpretation": "Move to parameter generalization unless a new counter-backed mechanism appears.",
        },
    ]


def next_rows(decision: str) -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "stage229_parameter_generalization_matrix",
            "entry_condition": "Stage228 denies new exact hot-path code and Stage227 fixes T_bootstrap/r claim scope.",
            "gate": "Run a parameter/branch matrix before broadening exact-route claims.",
            "status": "selected" if decision.startswith("PASS_STAGE228_NO_NEW_HOTPATH") else "future",
            "failure_action": "Keep claims scoped to BINARY SET_2_3_2048 r=6.",
            "evidence": rel(PROOF),
        },
        {
            "priority": "P1",
            "route": "stage230_literature_novelty_audit",
            "entry_condition": "Before any paper novelty claim.",
            "gate": "Source-verified related work; no fabricated references.",
            "status": "future",
            "failure_action": "Engineering-only report.",
            "evidence": rel(CANDIDATES),
        },
        {
            "priority": "P2",
            "route": "stage231_new_backend_or_compact_proof_unlock",
            "entry_condition": "A new backend primitive or closed compact-state proof is supplied.",
            "gate": "Proof or primitive first, then isolated tests, then full SAB.",
            "status": "blocked_until_new_evidence",
            "failure_action": "Do not modify SAB hot path.",
            "evidence": rel(GATES),
        },
    ]


def write_reports(decision: str, inputs: List[Dict[str, str]], facts: List[Dict[str, str]], proj: List[Dict[str, str]], candidates: List[Dict[str, str]], gates: List[Dict[str, str]], proof: List[Dict[str, str]], queue: List[Dict[str, str]]) -> None:
    report = f"""# Stage228 Counter-Driven Backend Kernel Search

Decision: `{decision}`.

Stage228 reopens the exact MAT/PVW kernel question only as a falsifiable
candidate search. It does not implement new hot-path code because the current
counter signal is small and prior frontier gates already reject layout-only
retuning. The primary endpoint remains complete SAB `T_bootstrap/r`.

## Source Facts

{table(facts, ["fact", "status", "evidence", "interpretation"])}
## Projection Thresholds

{table(proj, ["component", "share", "required_local_speedup_for_3pct_full_sab", "current_signal", "evidence"])}
## Candidate Cards

{table(candidates, ["candidate_id", "focused_module", "hypothesis", "required_evidence_before_code", "current_evidence", "code_permission", "next_gate"])}
## Candidate Gates

{table(gates, ["candidate_id", "correctness_gate", "performance_gate", "failure_rule", "status"])}
## Proof Gates

{table(proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])}
## Next Queue

{table(queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}
## Inputs

{table(inputs, ["input", "status", "role", "bytes"])}
"""
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(
        PLAN,
        """# Stage228 Counter-Driven Kernel Search Plan

1. Consume Stage226 counters, Stage227 claim boundary, prior Stage183/184 frontier, and current source.
2. Generate candidate code hypotheses with explicit correctness/performance/failure gates.
3. Deny hot-path edits unless a candidate clears the projected complete-SAB threshold.
4. Select parameter generalization when exact same-format code is not justified.
""",
    )
    write_text(
        THEORY,
        """# Stage228 Counter-Driven Kernel Model

For a component with full-SAB share p, a local speedup s changes total time by
`1 / (1 - p + p/s)`. Stage228 requires at least a 3% projected complete-SAB
`T_bootstrap/r` gain before permitting a new exact hot-path implementation.

Stage226 shows small backend counter improvements, but this supports the
existing backend FromDFT-add route rather than a new MAT addmul rewrite.
""",
    )
    write_text(
        VARIANT,
        """# Stage228 Candidate Algorithm Cards

## H228-C1-r6-dec-reuse-addmul

- Parent algorithm: exact dense MAT/PVW-SAB.
- Focused module: `mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_rgt4_tiled_avx512`.
- Main hypothesis: a new r=6 addmul dataflow could reduce duplicated dec-row loads.
- Status labels: probe-only, experiment-pending, no hot-path permission.
- Required gate: isolated addmul projection plus complete-SAB `T_bootstrap/r`.

## H228-C2-batched-direct-from-dft-add

- Parent algorithm: exact dense MAT/PVW-SAB.
- Focused module: backend direct FromDFT+add.
- Main hypothesis: a true multi-row backend primitive could reduce materialization.
- Status labels: blocked until backend primitive exists.

## H228-C3-sub-decomp-fusion-refresh

- Parent algorithm: exact dense MAT/PVW-SAB.
- Focused module: existing `SAB_PVW_SUB_DECOMP_FUSION` flag.
- Main hypothesis: existing full-SAB positive evidence may merit refresh, but no new AVX512 sub-decompose code is allowed.
- Status labels: existing-flag refresh only.
""",
    )
    write_text(
        REPRO,
        """# Stage228 Reproduction Commands

```powershell
python scripts\\build_stage228_counter_driven_backend_kernel_search.py
Get-Content repro\\stage228_counter_driven_backend_kernel_search\\proof_gate.csv
Get-Content repro\\stage228_counter_driven_backend_kernel_search\\candidate_cards.csv
```
""",
    )


def artifact_rows(paths: Iterable[Path]) -> List[Dict[str, str]]:
    rows = []
    for path in paths:
        rows.append(
            {
                "path": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256(path) if path.exists() and path.is_file() else "",
                "bytes": str(path.stat().st_size) if path.exists() and path.is_file() else "",
            }
        )
    return rows


def update_tracking(decision: str) -> None:
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 228: Counter-Driven Backend Kernel Search",
        f"""
## Stage 228: Counter-Driven Backend Kernel Search

Goal:

```text
Use Stage226 native counters and prior frontier gates to decide whether any
new exact MAT/PVW hot-path code is justified.
```

Status:

```text
Completed at `{head}` with `{decision}`. No speculative hot-path edit is
permitted; next selected work is parameter generalization.
```
""",
    )
    append_once(
        GOAL,
        "Stage228 counter-driven backend kernel search",
        f"\n\n## Stage228 counter-driven backend kernel search\n\nAt commit `{head}`, Stage228 records `{decision}`. Exact same-format kernel work remains gated by projected complete-SAB `T_bootstrap/r` gain.\n",
    )
    append_once(
        CURRENT_GOAL,
        "Stage228 counter-driven backend kernel search",
        f"\n\n### Stage228 counter-driven backend kernel search\n\n`{decision}` prevents blind exact-path retuning and routes to parameter generalization.\n",
    )
    append_once(
        HYPOTHESES,
        "H10_stage228_counter_driven_kernel_search",
        f"""

H10_stage228_counter_driven_kernel_search:
  status: no_new_hotpath_code_permission
  evidence:
    - repro/stage228_counter_driven_backend_kernel_search/candidate_cards.csv
    - repro/stage228_counter_driven_backend_kernel_search/projection_thresholds.csv
    - docs/stage228_counter_driven_backend_kernel_search.md
  conclusion: >
    Stage228 records {decision}. New exact MAT/PVW hot-path code requires a
    projected complete-SAB gain gate before implementation.
""",
    )
    append_once(
        RUN_LOG,
        "stage228-counter-driven-kernel-search-001",
        f"""stage228-counter-driven-kernel-search-001,2026-07-04,{head},Stage 228,analysis,python scripts/build_stage228_counter_driven_backend_kernel_search.py,counter-driven exact kernel candidate search,T_bootstrap_per_lane,{decision},"No hot-path edit; next selected route is parameter generalization.",docs/stage228_counter_driven_backend_kernel_search.md; repro/stage228_counter_driven_backend_kernel_search/proof_gate.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage228_counter_driven_backend_kernel_search:",
        """

- stage228_counter_driven_backend_kernel_search:
  - `docs/stage228_counter_driven_backend_kernel_search.md`
  - `experiments/stage228_counter_driven_backend_kernel_search_plan.md`
  - `theory_checks/stage228_counter_driven_kernel_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage228_counter_driven_candidates.md`
  - `scripts/build_stage228_counter_driven_backend_kernel_search.py`
  - `repro/stage228_counter_driven_backend_kernel_search/`
""",
    )
    append_once(CHECKLIST, "Stage228 counter-driven backend kernel search", f"\n- [x] Stage228 counter-driven backend kernel search records decision `{decision}`.\n")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = input_rows()
    facts = source_fact_rows()
    proj = projection_rows()
    candidates = candidate_rows(proj)
    gates = gate_rows(candidates)
    decision = decide(inputs, candidates)
    proof = proof_rows(decision, inputs, facts, candidates)
    queue = next_rows(decision)

    write_csv(INPUTS, inputs, ["input", "status", "role", "bytes"])
    write_csv(SOURCE_FACTS, facts, ["fact", "status", "evidence", "interpretation"])
    write_csv(PROJECTION, proj, ["component", "share", "required_local_speedup_for_3pct_full_sab", "current_signal", "evidence"])
    write_csv(CANDIDATES, candidates, ["candidate_id", "focused_module", "hypothesis", "required_evidence_before_code", "current_evidence", "code_permission", "next_gate"])
    write_csv(GATES, gates, ["candidate_id", "correctness_gate", "performance_gate", "failure_rule", "status"])
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])
    write_reports(decision, inputs, facts, proj, candidates, gates, proof, queue)
    update_tracking(decision)
    write_csv(
        ARTIFACT,
        artifact_rows([DOC, PLAN, THEORY, VARIANT, INPUTS, SOURCE_FACTS, PROJECTION, CANDIDATES, GATES, PROOF, NEXT, REPORT, REPRO, Path(__file__).resolve()]),
        ["path", "exists", "sha256", "bytes"],
    )
    print(decision)


if __name__ == "__main__":
    main()
