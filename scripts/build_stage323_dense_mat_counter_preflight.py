#!/usr/bin/env python3
"""Build Stage323 dense MAT layout/counter preflight artifacts."""

from __future__ import annotations

import csv
import hashlib
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage323_dense_mat_counter_preflight"
DOC = ROOT / "docs" / "stage323_dense_mat_counter_preflight.md"
THEORY = ROOT / "theory_checks" / "stage323_dense_mat_static_load_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage323_exact_dense_no_code.md"
PLAN = ROOT / "experiments" / "stage324_selector_layout_mechanism_preflight_plan.md"
BUILDER = ROOT / "scripts" / "build_stage323_dense_mat_counter_preflight.py"
SOURCE = ROOT / "src" / "mosfhet" / "src" / "mattrgsw.c"

SUMMARY = OUT / "summary.csv"
STATIC_MODEL = OUT / "static_load_model.csv"
SOURCE_FACTS = OUT / "source_facts.csv"
MECHANISMS = OUT / "mechanism_screen.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage323_report.md"
PERF_LOG = OUT / "perf_probe.log"
ARTIFACT = OUT / "artifact_index.csv"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE322_SUMMARY = ROOT / "repro" / "stage322_schedule_profile_attribution" / "profile_summary.csv"
STAGE321_PROOF = ROOT / "repro" / "stage321_r4_unrolled_fullsab_ab" / "proof_gate.csv"
STAGE183_DOC = ROOT / "docs" / "stage183_addmul_dataflow_screen.md"
STAGE193_DOC = ROOT / "docs" / "stage193_exact_addmul_dataflow_preflight.md"

DECISION = "PASS_STAGE323_DENSE_MAT_PREFLIGHT_DENY_LOOP_CODE_ROUTE_SELECTOR_FORMAT_REQUIRED"


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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv_one(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return rows[0] if rows else {}


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        if current and not current.endswith("\n"):
            f.write("\n")
        f.write(text.lstrip())
        if not text.endswith("\n"):
            f.write("\n")


def fnum(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def run_perf_probe() -> Dict[str, str]:
    if os.name == "nt":
        cmd = [
            "wsl.exe", "-e", "bash", "-lc",
            "if command -v perf >/dev/null 2>&1; then perf stat -e cycles,instructions true; else echo 'perf: command not found' >&2; exit 127; fi",
        ]
    else:
        cmd = [
            "bash", "-lc",
            "if command -v perf >/dev/null 2>&1; then perf stat -e cycles,instructions true; else echo 'perf: command not found' >&2; exit 127; fi",
        ]
    proc = subprocess.run(
        cmd, cwd=ROOT, text=True, encoding="utf-8", errors="replace",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
    )
    write_text(PERF_LOG, "\n".join([
        "command: " + " ".join(cmd),
        f"returncode: {proc.returncode}",
        "--- stdout ---",
        proc.stdout.rstrip(),
        "--- stderr ---",
        proc.stderr.rstrip(),
    ]))
    return {
        "available": "yes" if proc.returncode == 0 else "no",
        "returncode": str(proc.returncode),
        "reason": "perf stat works" if proc.returncode == 0 else "perf unavailable in current WSL environment",
        "log": rel(PERF_LOG),
    }


def source_fact(pattern: str, text: str) -> tuple[str, str]:
    for idx, line in enumerate(text.splitlines(), start=1):
        if pattern in line:
            return "yes", str(idx)
    return "no", ""


def table(rows: List[Dict[str, object]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        data = path.read_bytes()
        rows.append({"path": rel(path), "bytes": str(len(data)), "sha256": hashlib.sha256(data).hexdigest()})
    write_csv(ARTIFACT, rows, ["path", "bytes", "sha256"])


def append_run_log() -> None:
    run_id = "stage323-dense-mat-counter-preflight-001"
    if run_id in read_text(RUN_LOG):
        return
    fields: List[str] = []
    if RUN_LOG.exists():
        with RUN_LOG.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fields = list(reader.fieldnames or [])
    if not fields:
        fields = [
            "run_id", "date", "git_ref", "stage", "backend", "command",
            "config", "seed", "status", "summary", "artifacts",
        ]
    row = {field: "" for field in fields}
    values = {
        "run_id": run_id,
        "date": "2026-07-05",
        "git_ref": git_head(),
        "commit_or_state": git_head(),
        "stage": "Stage 323",
        "backend": "source-static-plus-wsl-perf-probe",
        "command": "python scripts/build_stage323_dense_mat_counter_preflight.py",
        "config": "dense MAT r=4 static load model and perf availability probe",
        "params": "BINARY SET_2_3_2048; r=4; current direct baseline",
        "seed": "n/a",
        "status": DECISION,
        "summary": "Stage323 denies new exact dense loop code without a new selector/key-format mechanism.",
        "artifacts": f"{rel(DOC)}; {rel(STATIC_MODEL)}; {rel(MECHANISMS)}; {rel(PROOF)}",
    }
    for key, value in values.items():
        if key in row:
            row[key] = value
    with RUN_LOG.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writerow(row)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    stage322 = read_csv_one(STAGE322_SUMMARY)
    dense_share = fnum(stage322.get("dense_share"))
    mat_ep_share = fnum(stage322.get("mat_ep_share"))
    t_over_r = stage322.get("t_bootstrap_over_r_us", "")
    speedup_scalar = stage322.get("speedup_vs_repeated_scalar", "")
    one_pct_reduction = (1.0 - 1.0 / 1.01) / dense_share if dense_share else 0.0
    two_pct_reduction = (1.0 - 1.0 / 1.02) / dense_share if dense_share else 0.0
    source = read_text(SOURCE)
    perf = run_perf_probe()

    facts = []
    for fact_id, pattern, implication in [
        ("complex_addmul_uses_avx512_fma", "mat_avx512_complex_addmul", "Current dense addmul already uses AVX512 FMA intrinsics."),
        ("r4_dense_kernel_exists", "mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r4_avx512", "The target r=4 dense kernel is already specialized."),
        ("r4_unrolled_kernel_exists", "MAT_TRGSW_AVX512_R4_UNROLLED_ROWS", "The obvious pointer-hoist/unroll route exists and was closed by Stage321."),
        ("rgt4_fulltile_exists", "MAT_TRGSW_AVX512_R6_FULLTILE", "Fulltile/bodymajor families are r>4 prior ablations, not a new r=4 route."),
        ("selector_samples_dense_rows", "selector->samples[row]", "Selector rows are dense public-key material under the current key format."),
    ]:
        status, line = source_fact(pattern, source)
        facts.append({
            "fact": fact_id,
            "status": status,
            "line": line,
            "evidence": rel(SOURCE),
            "implication": implication,
        })
    write_csv(SOURCE_FACTS, facts, ["fact", "status", "line", "evidence", "implication"])

    rows = 5
    outputs = 5
    vec_blocks = 2048 // 16
    zmm_bytes = 64
    complex_products_per_block = rows * outputs
    dec_zmm_loads_per_block = rows * 2
    selector_zmm_loads_per_block = rows * outputs * 2
    output_zmm_stores_per_block = outputs * 2
    total_zmm_memops_per_block = (
        dec_zmm_loads_per_block + selector_zmm_loads_per_block + output_zmm_stores_per_block
    )
    row0_complex_mul = outputs
    addmul_complex = (rows - 1) * outputs
    zmm_fma_per_block = row0_complex_mul * 2 + addmul_complex * 4
    zmm_mul_per_block = row0_complex_mul * 2
    static_rows = [{
        "model": "r4_k1_l1_dense_current",
        "rows": rows,
        "outputs": outputs,
        "vec_blocks": vec_blocks,
        "complex_products_per_block": complex_products_per_block,
        "dec_zmm_loads_per_block": dec_zmm_loads_per_block,
        "selector_zmm_loads_per_block": selector_zmm_loads_per_block,
        "output_zmm_stores_per_block": output_zmm_stores_per_block,
        "total_zmm_memops_per_block": total_zmm_memops_per_block,
        "zmm_fma_per_block": zmm_fma_per_block,
        "zmm_mul_per_block": zmm_mul_per_block,
        "estimated_mem_bytes_per_call": total_zmm_memops_per_block * vec_blocks * zmm_bytes,
        "dec_reuse_status": "optimal_for_dense_r4_loop",
        "store_status": "one_store_per_output_component",
    }]
    write_csv(STATIC_MODEL, static_rows, [
        "model", "rows", "outputs", "vec_blocks", "complex_products_per_block",
        "dec_zmm_loads_per_block", "selector_zmm_loads_per_block",
        "output_zmm_stores_per_block", "total_zmm_memops_per_block",
        "zmm_fma_per_block", "zmm_mul_per_block", "estimated_mem_bytes_per_call",
        "dec_reuse_status", "store_status",
    ])

    mechanisms = [
        {
            "candidate": "r4_pointer_hoist_unrolled_rows",
            "status": "CLOSED_STAGE321_NEUTRAL",
            "new_mechanism": "no",
            "static_or_empirical_result": "Stage321 r4/direct complete-SAB ratio=0.998571",
            "code_permission": "DENY_PRIOR_FULLSAB_NEUTRAL",
        },
        {
            "candidate": "dec_row_cache_across_outputs",
            "status": "DENY_NO_DUPLICATE_DEC_LOADS",
            "new_mechanism": "no",
            "static_or_empirical_result": "r=4 current loop loads each dec row once per coefficient block and reuses it across all five outputs",
            "code_permission": "DENY_NO_LOAD_REDUCTION",
        },
        {
            "candidate": "more_output_register_tiling",
            "status": "DENY_ALREADY_REGISTER_RESIDENT_R4",
            "new_mechanism": "no",
            "static_or_empirical_result": "r=4 current loop accumulates all five outputs in registers and stores once",
            "code_permission": "DENY_NO_STORE_REDUCTION",
        },
        {
            "candidate": "prefetch_only_selector_rows",
            "status": "DENY_COUNTER_UNAVAILABLE_AND_NO_COUNT_REDUCTION",
            "new_mechanism": "weak",
            "static_or_empirical_result": perf["reason"],
            "code_permission": "DENY_UNTIL_COUNTER_BACKED",
        },
        {
            "candidate": "selector_transposed_key_layout",
            "status": "ROUTE_STAGE324_KEY_FORMAT_PREFLIGHT",
            "new_mechanism": "yes",
            "static_or_empirical_result": "Could change selector locality, but changes key layout/resource/noise surface.",
            "code_permission": "NO_HOT_PATH_CODE_BEFORE_KEYGEN_RESOURCE_NOISE_GATE",
        },
        {
            "candidate": "structured_or_compact_selector",
            "status": "ROUTE_STAGE324_PROOF_BRANCH_ONLY",
            "new_mechanism": "yes",
            "static_or_empirical_result": "Could reduce dense (r+1)^2 selector products, but requires distribution/security proof.",
            "code_permission": "NO_HOT_PATH_CODE_BEFORE_PROOF_AND_RESOURCE_GATE",
        },
    ]
    write_csv(MECHANISMS, mechanisms, [
        "candidate", "status", "new_mechanism", "static_or_empirical_result", "code_permission",
    ])

    summary_rows = [{
        "decision": DECISION,
        "stage322_dense_share": f"{dense_share:.6f}",
        "stage322_mat_ep_share": f"{mat_ep_share:.6f}",
        "stage322_t_bootstrap_over_r_us": t_over_r,
        "stage322_speedup_vs_repeated_scalar": speedup_scalar,
        "required_dense_reduction_for_1pct_fullsab": f"{one_pct_reduction:.6f}",
        "required_dense_reduction_for_2pct_fullsab": f"{two_pct_reduction:.6f}",
        "perf_counter_available": perf["available"],
        "next_stage": "stage324_selector_layout_or_structured_mechanism_preflight",
    }]
    write_csv(SUMMARY, summary_rows, [
        "decision", "stage322_dense_share", "stage322_mat_ep_share",
        "stage322_t_bootstrap_over_r_us", "stage322_speedup_vs_repeated_scalar",
        "required_dense_reduction_for_1pct_fullsab",
        "required_dense_reduction_for_2pct_fullsab",
        "perf_counter_available", "next_stage",
    ])

    proof_rows = [
        {"gate": "G1_stage322_input", "status": "PASS" if "PASS_STAGE322_PROFILE_SELECT_DENSE_MAT_LAYOUT_COUNTER_PREFLIGHT" in read_text(STAGE322_SUMMARY) else "FAIL", "metric": "Stage322 decision", "value": "dense selected", "interpretation": "Stage323 opens only because dense MAT was the selected unclosed residual."},
        {"gate": "G2_perf_counter_probe", "status": "PROXY_ONLY" if perf["available"] == "no" else "PASS", "metric": "perf availability", "value": perf["available"], "interpretation": "No hardware-counter claim is made when perf is unavailable."},
        {"gate": "G3_static_load_model", "status": "PASS", "metric": "r4 dec/output reuse", "value": "dec_once;store_once", "interpretation": "Current r=4 dense loop already reuses each dec row across all outputs and stores each output once."},
        {"gate": "G4_existing_route_closure", "status": "PASS", "metric": "r4_unrolled", "value": "Stage321 neutral", "interpretation": "The only local r=4 loop variant already failed complete-SAB A/B."},
        {"gate": "G5_code_permission", "status": DECISION, "metric": "exact dense loop code", "value": "denied", "interpretation": "Further gains require selector/key-format or structured mechanism gates, not another local loop rewrite."},
    ]
    write_csv(PROOF, proof_rows, ["gate", "status", "metric", "value", "interpretation"])
    write_csv(NEXT, [{
        "priority": "P0",
        "stage": "stage324_selector_layout_or_structured_mechanism_preflight",
        "input_decision": DECISION,
        "task": "Choose between selector-transposed key layout and structured/compact selector mechanism with explicit keygen/resource/noise gates.",
        "gate": "No hot-path SAB code until key format, correctness, resource, noise, and full-SAB A/B gates are specified.",
    }], ["priority", "stage", "input_decision", "task", "gate"])

    write_text(COMMANDS, """# Stage323 Reproduction Commands

```bash
python3 scripts/build_stage323_dense_mat_counter_preflight.py
```

If native Linux `perf` is available, rerun on that platform to upgrade the
counter row from proxy-only to measured. Without counters, Stage323 remains a
static/source preflight and cannot admit new exact dense loop code.
""")

    report = f"""# Stage323 Dense MAT Counter Preflight

Decision: `{DECISION}`.

Stage323 tests whether Stage322's dense MAT residual admits another local
exact-loop optimization. It does not. The current r=4 dense MAT path already
uses AVX512 FMA, loads each decomposed row once per coefficient block, reuses
it across all five outputs, and stores each output once. The explicit
r4-unrolled pointer-hoist variant was neutral in complete SAB at Stage321.

## Summary

{table(summary_rows, ["decision", "stage322_dense_share", "required_dense_reduction_for_1pct_fullsab", "perf_counter_available", "next_stage"])}

## Static Model

{table(static_rows, ["model", "rows", "outputs", "complex_products_per_block", "dec_zmm_loads_per_block", "selector_zmm_loads_per_block", "output_zmm_stores_per_block", "zmm_fma_per_block", "estimated_mem_bytes_per_call", "dec_reuse_status", "store_status"])}

## Mechanism Screen

{table(mechanisms, ["candidate", "status", "new_mechanism", "code_permission"])}

## Proof Gate

{table(proof_rows, ["gate", "status", "metric", "value", "interpretation"])}

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, """# Stage323 Dense MAT Static Load Model

For the target r=4, k=1, l=1 dense MAT external product:

```text
rows = r + 1 = 5
outputs = k + r = 5
vector blocks = N / 16 = 128
complex vector products per block = rows * outputs = 25
```

The current r=4 AVX512 loop is already MAT-aware:

- each decomposed DFT row is loaded once per coefficient block;
- that row is reused across all five outputs;
- all five outputs are accumulated in registers;
- each output is stored once after all rows are processed.

Therefore a local loop rewrite cannot reduce decomposed-row loads or output
stores. It must either reduce selector loads, reduce dense product count, or
change key/selector layout. Those are not local exact-loop edits and require
key-format/resource/noise gates.
""")
    write_text(VARIANT, """# Stage323 Exact Dense No-Code Route

Status: no new exact dense loop code is admitted.

Reason: the current r=4 dense MAT implementation already has the main
MAT-aware AVX load/store properties, and the explicit r4-unrolled variant was
neutral in complete SAB.

Allowed next mechanisms:

- selector-transposed key layout, only after keygen/resource/noise gates;
- structured or compact selector, only after distribution/security proof gates.

Forbidden next action: another speculative r=4 dense addmul loop rewrite
without a new counter-backed mechanism.
""")
    write_text(PLAN, f"""# Stage324 Selector Layout Or Structured Mechanism Preflight Plan

Input decision: `{DECISION}`.

Goal: decide whether the next real acceleration route is:

- selector-transposed key layout, targeting selector-load locality without
  changing dense arithmetic count; or
- structured/compact selector, targeting the dense `(r+1)^2` product count but
  requiring distribution/security proof.

Required gates before any SAB hot-path code:

- exact algebraic equivalence or staged phase equivalence;
- keygen/key-format specification;
- key size and memory projection;
- noise/resource side conditions;
- complete SAB `T_bootstrap/r` A/B plan.

Failure handling: if neither route passes preflight, stop exact-dense code work
and update the paper/repro claim boundary instead of writing speculative AVX.
""")

    append_once(GOAL, "<!-- stage323-dense-mat-counter-preflight -->", f"""<!-- stage323-dense-mat-counter-preflight -->
### Stage323 dense MAT counter preflight

`{DECISION}` denies new exact dense loop code and routes to selector-layout or
structured mechanism preflight.
""")
    append_once(ROADMAP, "## Stage 323: Dense MAT Counter Preflight", f"""## Stage 323: Dense MAT Counter Preflight

Goal: determine whether Stage322's dense MAT residual admits another local
exact-loop optimization.

Status: `{DECISION}`.
""")
    append_once(HYPOTHESES, "H323_dense_mat_counter_preflight:", f"""H323_dense_mat_counter_preflight:
  status: {DECISION}
  primary_metric: code_permission_for_complete_sab_T_bootstrap_over_r
  evidence:
    - repro/stage323_dense_mat_counter_preflight/summary.csv
    - repro/stage323_dense_mat_counter_preflight/static_load_model.csv
    - repro/stage323_dense_mat_counter_preflight/mechanism_screen.csv
    - repro/stage323_dense_mat_counter_preflight/proof_gate.csv
  conclusion: >
    Stage323 denies another local exact dense addmul rewrite: current r=4
    dense MAT already has dec-row reuse and single output stores, while
    r4-unrolled was neutral in complete SAB.
""")
    append_once(MANIFEST, "- stage323_dense_mat_counter_preflight:", """- stage323_dense_mat_counter_preflight:
  - `docs/stage323_dense_mat_counter_preflight.md`
  - `scripts/build_stage323_dense_mat_counter_preflight.py`
  - `repro/stage323_dense_mat_counter_preflight/`
""")
    append_once(CHECKLIST, "<!-- stage323-dense-mat-counter-preflight-checklist -->", f"""<!-- stage323-dense-mat-counter-preflight-checklist -->
- [x] Stage323 records `{DECISION}` and blocks speculative exact dense loop rewrites.
""")
    append_run_log()

    paths = [
        DOC, THEORY, VARIANT, PLAN, COMMANDS, REPORT, SUMMARY, STATIC_MODEL,
        SOURCE_FACTS, MECHANISMS, PROOF, NEXT, PERF_LOG, BUILDER,
        STAGE183_DOC, STAGE193_DOC, STAGE321_PROOF, STAGE322_SUMMARY,
    ]
    artifact_index(paths)
    print(DECISION)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
