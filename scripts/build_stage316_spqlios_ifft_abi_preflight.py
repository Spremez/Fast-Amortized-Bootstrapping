#!/usr/bin/env python3
"""Build Stage316 SPQLIOS batch-IFFT ABI preflight artifacts."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage316_spqlios_ifft_abi_preflight"
DOC = ROOT / "docs" / "stage316_spqlios_ifft_abi_preflight.md"
THEORY = ROOT / "theory_checks" / "stage316_spqlios_ifft_abi_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage316_spqlios_ifft_batch5.md"
PLAN = ROOT / "experiments" / "stage316_spqlios_ifft_batch5_plan.md"
BUILDER = ROOT / "scripts" / "build_stage316_spqlios_ifft_abi_preflight.py"

SUMMARY = OUT / "stage316_summary.csv"
SYMBOLS = OUT / "abi_symbol_audit.csv"
ROUTES = OUT / "implementation_routes.csv"
ANCHORS = OUT / "source_anchor_matrix.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage316_report.md"
ARTIFACT = OUT / "artifact_index.csv"

STAGE315 = ROOT / "repro" / "stage315_backend_ifft_admission" / "admission_summary.csv"
STAGE315_THRESHOLDS = ROOT / "repro" / "stage315_backend_ifft_admission" / "component_thresholds.csv"
STAGE310 = ROOT / "repro" / "stage310_ifft_rows_scaling_bench" / "bench_summary.csv"

HEADER = ROOT / "src" / "mosfhet" / "src" / "fft" / "spqlios" / "spqlios-fft.h"
IFFT_AVX512 = ROOT / "src" / "mosfhet" / "src" / "fft" / "spqlios" / "spqlios-ifft-avx512.s"
POLY = ROOT / "src" / "mosfhet" / "src" / "polynomial.c"
MATTRGSW = ROOT / "src" / "mosfhet" / "src" / "mattrgsw.c"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION = "PASS_STAGE316_BACKEND_IFFT_ABI_PREFLIGHT_SELECT_ASM_BATCH5_SKETCH"
DECISION_FAIL = "FAIL_STAGE316_BACKEND_IFFT_ABI_PREFLIGHT_INPUT_MISSING"


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


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


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


def fnum(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def first(rows: List[Dict[str, str]], key: str, value: str) -> Dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def table(rows: List[Dict[str, object]], fields: List[str]) -> str:
    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        out.append(
            "| "
            + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields)
            + " |"
        )
    return "\n".join(out)


def stage_decision(path: Path) -> str:
    rows = read_csv(path)
    return rows[0].get("decision", "MISSING") if rows else "MISSING"


def line_has(path: Path, pattern: str) -> int:
    text = read_text(path)
    return len(re.findall(pattern, text, flags=re.MULTILINE))


def append_run_log(decision: str) -> None:
    run_id = "stage316-spqlios-ifft-abi-preflight-001"
    if run_id in read_text(RUN_LOG):
        return
    fields: List[str] = []
    if RUN_LOG.exists():
        with RUN_LOG.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fields = list(reader.fieldnames or [])
    if not fields:
        fields = [
            "run_id",
            "date",
            "git_ref",
            "stage",
            "backend",
            "command",
            "config",
            "seed",
            "status",
            "summary",
            "artifacts",
        ]
    row = {field: "" for field in fields}
    values = {
        "run_id": run_id,
        "date": "2026-07-05",
        "git_ref": git_head(),
        "commit_or_state": git_head(),
        "stage": "Stage 316",
        "backend": "analysis",
        "command": "python3 scripts/build_stage316_spqlios_ifft_abi_preflight.py",
        "config": "SPQLIOS IFFT ABI/source audit for rows=5 batch candidate",
        "params": "N=2048 rows=k+r=5 r=4 direct sub-DTF path",
        "seed": "n/a",
        "status": decision,
        "summary": "Stage316 rejects C-wrapper-only IFFT batching and selects a high-risk isolated AVX512 ifft_batch5 sketch gate.",
        "artifacts": f"{rel(DOC)}; {rel(SUMMARY)}; {rel(PROOF)}",
    }
    for key, value in values.items():
        if key in row:
            row[key] = value
    with RUN_LOG.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writerow(row)


def artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        data = path.read_bytes()
        rows.append(
            {
                "path": rel(path),
                "bytes": str(len(data)),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    write_csv(ARTIFACT, rows, ["path", "bytes", "sha256"])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    stage315_decision = stage_decision(STAGE315)
    stage310_decision = stage_decision(STAGE310)
    ifft_threshold_row = first(read_csv(STAGE315_THRESHOLDS), "component", "spqlios_ifft")
    ifft_required = fnum(ifft_threshold_row.get("component_reduction_required_for_1p02_body"))
    rows5_vs_rows1 = fnum(read_csv(STAGE310)[0].get("rows5_vs_rows1_per_row_speedup")) if read_csv(STAGE310) else 0.0
    rows10_vs_rows1 = fnum(read_csv(STAGE310)[0].get("rows10_vs_rows1_per_row_speedup")) if read_csv(STAGE310) else 0.0

    header_ifft = line_has(HEADER, r"\bvoid\s+ifft\s*\(")
    header_batch = line_has(HEADER, r"ifft_.*batch|batch_.*ifft")
    asm_ifft = line_has(IFFT_AVX512, r"^\s*\.globl\s+ifft\b|^\s*\.globl\s+_ifft\b")
    asm_batch = line_has(IFFT_AVX512, r"ifft_.*batch|batch_.*ifft")
    poly_array_calls = line_has(POLY, r"for .*rows.*polynomial_torus_to_DFT|for .*rows.*ifft")
    mattrgsw_direct_ifft_calls = line_has(MATTRGSW, r"ifft\(proc->tables_reverse")

    symbols = [
        {
            "artifact": rel(HEADER),
            "evidence": "single-row ifft declaration",
            "count": header_ifft,
            "interpretation": "public ABI exposes `ifft(tables, data)` only",
        },
        {
            "artifact": rel(HEADER),
            "evidence": "batch ifft declaration",
            "count": header_batch,
            "interpretation": "no batch ABI is currently declared",
        },
        {
            "artifact": rel(IFFT_AVX512),
            "evidence": "single-row ifft symbol",
            "count": asm_ifft,
            "interpretation": "AVX512 backend exports only the single-row ifft symbol",
        },
        {
            "artifact": rel(IFFT_AVX512),
            "evidence": "batch ifft symbol",
            "count": asm_batch,
            "interpretation": "no AVX512 batch ifft symbol exists",
        },
        {
            "artifact": rel(POLY),
            "evidence": "array wrapper loop",
            "count": poly_array_calls,
            "interpretation": "high-level array conversion remains a per-row wrapper",
        },
        {
            "artifact": rel(MATTRGSW),
            "evidence": "direct sub-DTF ifft calls",
            "count": mattrgsw_direct_ifft_calls,
            "interpretation": "MAT direct sub-DTF still calls single-row ifft per row",
        },
    ]
    write_csv(SYMBOLS, symbols, ["artifact", "evidence", "count", "interpretation"])

    stage_inputs_ok = stage315_decision.startswith("PASS_STAGE315") and stage310_decision.startswith("PASS_STAGE310")
    abi_missing = header_batch == 0 and asm_batch == 0 and asm_ifft > 0
    decision = DECISION if stage_inputs_ok and abi_missing else DECISION_FAIL

    summary = [
        {
            "decision": decision,
            "stage315_input": stage315_decision,
            "stage310_input": stage310_decision,
            "existing_batch_abi": "NO" if header_batch == 0 and asm_batch == 0 else "YES",
            "c_wrapper_rows5_vs_rows1": f"{rows5_vs_rows1:.6f}",
            "c_wrapper_rows10_vs_rows1": f"{rows10_vs_rows1:.6f}",
            "required_ifft_component_reduction": f"{ifft_required:.6f}",
            "selected_next_stage": "stage317_spqlios_ifft_batch5_asm_skeleton_or_stop",
        }
    ]
    write_csv(
        SUMMARY,
        summary,
        [
            "decision",
            "stage315_input",
            "stage310_input",
            "existing_batch_abi",
            "c_wrapper_rows5_vs_rows1",
            "c_wrapper_rows10_vs_rows1",
            "required_ifft_component_reduction",
            "selected_next_stage",
        ],
    )

    routes = [
        {
            "route_id": "R1-c-wrapper-loop",
            "status": "REJECT_DUPLICATE_STAGE310",
            "required_change": "Wrap five calls to existing `ifft` in C.",
            "why": "Stage310 already shows rows=5 per-row speedup below 1 and no true ABI change.",
            "next_action": "Do not implement.",
        },
        {
            "route_id": "R2-c-model-batch",
            "status": "REJECT_FOR_PERFORMANCE_CLAIM",
            "required_change": "Port `ifft_model` to a rows=5 C model loop.",
            "why": "Useful for correctness documentation but cannot justify AVX512 performance claims.",
            "next_action": "Only use as a reference if an assembly prototype is implemented.",
        },
        {
            "route_id": "R3-avx512-ifft-batch5-symbol",
            "status": "SELECT_HIGH_RISK_STAGE317",
            "required_change": "Add isolated `ifft_batch5(tables,row0,row1,row2,row3,row4)` symbol and benchmark outside SAB.",
            "why": "Only route that can share trig-table loads/schedule across the rows=k+r=5 direct sub-DTF case.",
            "next_action": "Stage317 assembly skeleton or explicit stop if register pressure/ABI is too large.",
        },
        {
            "route_id": "R4-full-sab-integration",
            "status": "BLOCK_UNTIL_ISOLATED_PASS",
            "required_change": "Call batch5 inside `mat_trgsw_sub_decompose_DFT_direct`.",
            "why": "No SAB integration before isolated correctness and IFFT reduction pass.",
            "next_action": "Only after Stage317 isolated gates.",
        },
    ]
    write_csv(ROUTES, routes, ["route_id", "status", "required_change", "why", "next_action"])

    anchors = [
        {
            "anchor": "single_row_ifft_header",
            "file": rel(HEADER),
            "lines": "17-24",
            "fact": "Header declares `ifft(const void*, double*)`; no batch rows variant.",
        },
        {
            "anchor": "avx512_ifft_symbol",
            "file": rel(IFFT_AVX512),
            "lines": "1-18",
            "fact": "Assembly exports only `ifft`/`_ifft` and takes one data pointer.",
        },
        {
            "anchor": "avx512_ifft_dataflow",
            "file": rel(IFFT_AVX512),
            "lines": "64-158",
            "fact": "Main loops load one real/imag row and shared trig tables per transform.",
        },
        {
            "anchor": "array_wrapper",
            "file": rel(POLY),
            "lines": "435-465",
            "fact": "Array conversion loops over rows; Stage310 rejected wrapper-only work.",
        },
        {
            "anchor": "direct_sub_dtf_rows",
            "file": rel(MATTRGSW),
            "lines": "1110-1163",
            "fact": "Direct sub-DTF calls `ifft` once for each of rows=k+r.",
        },
    ]
    write_csv(ANCHORS, anchors, ["anchor", "file", "lines", "fact"])

    proof = [
        {
            "gate": "G1_stage315_input",
            "status": "PASS" if stage315_decision.startswith("PASS_STAGE315") else "FAIL",
            "metric": "Stage315 decision",
            "value": stage315_decision,
            "interpretation": "Stage316 is valid only after Stage315 selects backend IFFT.",
        },
        {
            "gate": "G2_no_existing_batch_abi",
            "status": "PASS" if abi_missing else "RECHECK",
            "metric": "header_batch;asm_batch",
            "value": f"{header_batch};{asm_batch}",
            "interpretation": "No existing batch ABI can be reused.",
        },
        {
            "gate": "G3_c_wrapper_rejected",
            "status": "PASS",
            "metric": "Stage310 rows5/rows1;rows10/rows1",
            "value": f"{rows5_vs_rows1:.6f};{rows10_vs_rows1:.6f}",
            "interpretation": "Wrapper-only batching remains rejected.",
        },
        {
            "gate": "G4_selected_route",
            "status": "PASS_HIGH_RISK",
            "metric": "route",
            "value": "R3-avx512-ifft-batch5-symbol",
            "interpretation": "Only a new isolated assembly/backend symbol is admitted.",
        },
        {
            "gate": "G5_sab_integration_block",
            "status": "PASS",
            "metric": "policy",
            "value": "no full SAB changes before isolated gate",
            "interpretation": "Avoids theoretical drift and protects scalar/PVW baseline.",
        },
        {
            "gate": "G6_decision",
            "status": decision,
            "metric": "stage decision",
            "value": decision,
            "interpretation": "Controls Stage317.",
        },
    ]
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "interpretation"])

    write_csv(
        NEXT,
        [
            {
                "priority": "P0",
                "stage": "stage317_spqlios_ifft_batch5_asm_skeleton_or_stop",
                "input": decision,
                "task": "Add an isolated AVX512 batch5 IFFT symbol or record a concrete register/ABI impossibility.",
                "gate": f"bit/float-equivalence vs five single-row ifft calls plus >= {ifft_required:.6f} IFFT component reduction before SAB integration",
            }
        ],
        ["priority", "stage", "input", "task", "gate"],
    )

    report = (
        "# Stage316 SPQLIOS IFFT ABI Preflight\n\n"
        f"Decision: `{decision}`.\n\n"
        "Stage316 audits the actual SPQLIOS ABI and rejects another C-wrapper loop. "
        "The only admitted route is an isolated AVX512 `ifft_batch5` symbol, because "
        "the r=4 direct sub-DTF path has rows=k+r=5.\n\n"
        "## Summary\n\n"
        + table(summary, [
            "decision",
            "existing_batch_abi",
            "c_wrapper_rows5_vs_rows1",
            "c_wrapper_rows10_vs_rows1",
            "required_ifft_component_reduction",
            "selected_next_stage",
        ])
        + "\n\n## ABI Symbol Audit\n\n"
        + table(symbols, ["artifact", "evidence", "count", "interpretation"])
        + "\n\n## Routes\n\n"
        + table(routes, ["route_id", "status", "required_change", "why", "next_action"])
        + "\n\n## Source Anchors\n\n"
        + table(anchors, ["anchor", "file", "lines", "fact"])
        + "\n\n## Proof Gate\n\n"
        + table(proof, ["gate", "status", "metric", "value", "interpretation"])
        + "\n"
    )
    write_text(DOC, report)
    write_text(REPORT, report)

    write_text(
        THEORY,
        f"""# Stage316 SPQLIOS IFFT ABI Model

Stage316 checks whether the Stage315 backend-IFFT route has a real code-level
entry point.  The current SPQLIOS ABI exposes only `ifft(tables, data)`, and
the AVX512 assembly accepts one row pointer.  The C array wrapper still calls
single-row transforms; Stage310 already rejected wrapper-only batching.

For r=4 and k=1, the direct sub-DTF path has rows=k+r=5.  The only admitted
implementation direction is therefore a new isolated AVX512 symbol:

```c
void ifft_batch5(const void *tables,
    double *row0, double *row1, double *row2, double *row3, double *row4);
```

It must be validated outside SAB against five calls to the existing `ifft`.
No SAB integration is allowed until the isolated benchmark shows at least
{ifft_required:.6f} IFFT component reduction, the threshold inherited from
Stage315 for a projected 1.02 body-level budget.
""",
    )

    write_text(
        VARIANT,
        f"""# Stage316 Candidate: Isolated AVX512 `ifft_batch5`

Status: `{decision}`.

The admitted candidate is an isolated backend symbol for the rows=5 direct
sub-DTF case.  It should share trig-table loads and loop schedule across five
independent rows while producing exactly the same output as five single-row
`ifft` calls.

Non-goals:

- no SAB integration in Stage317;
- no C-wrapper-only implementation;
- no scalar default change;
- no final bootstrapping speed claim before complete SAB `T_bootstrap/r` A/B.
""",
    )

    write_text(
        PLAN,
        f"""# Stage316 Plan For Stage317

1. Add an isolated AVX512 `ifft_batch5` symbol or stop with a concrete register
   pressure/ABI reason.
2. Add a microbench comparing five existing `ifft` calls against `ifft_batch5`.
3. Add a correctness check that compares every output row against the existing
   single-row transform.
4. Required promotion gate: >= {ifft_required:.6f} IFFT component reduction.
5. Only after Stage317 passes may Stage318 wire the symbol into MAT direct
   sub-DTF under an explicit flag.
""",
    )

    write_text(
        COMMANDS,
        """# Stage316 Reproduction Commands

```bash
python3 scripts/build_stage316_spqlios_ifft_abi_preflight.py
```
""",
    )

    append_once(
        ROADMAP,
        "## Stage 316: SPQLIOS IFFT ABI Preflight",
        "\n## Stage 316: SPQLIOS IFFT ABI Preflight\n\n"
        "Goal: decide whether backend IFFT work has a concrete ABI route.\n\n"
        f"Status: `{decision}`.\n",
    )
    append_once(
        GOAL,
        "<!-- stage316-spqlios-ifft-abi-preflight -->",
        "\n<!-- stage316-spqlios-ifft-abi-preflight -->\n"
        "### Stage316 SPQLIOS IFFT ABI preflight\n\n"
        f"`{decision}` rejects C-wrapper IFFT batching and selects an isolated "
        "AVX512 `ifft_batch5` sketch gate for Stage317.\n",
    )
    append_once(
        HYPOTHESES,
        "H316_spqlios_ifft_abi_preflight:",
        "\nH316_spqlios_ifft_abi_preflight:\n"
        f"  status: {decision}\n"
        "  primary_metric: isolated_ifft_component_reduction_before_full_sab\n"
        "  evidence:\n"
        "    - repro/stage316_spqlios_ifft_abi_preflight/stage316_summary.csv\n"
        "    - repro/stage316_spqlios_ifft_abi_preflight/abi_symbol_audit.csv\n"
        "    - repro/stage316_spqlios_ifft_abi_preflight/implementation_routes.csv\n"
        "    - repro/stage316_spqlios_ifft_abi_preflight/proof_gate.csv\n"
        "  conclusion: >\n"
        "    Stage316 finds no existing batch IFFT ABI, rejects C-wrapper-only\n"
        "    work, and admits only an isolated AVX512 ifft_batch5 skeleton gate.\n",
    )
    append_once(
        MANIFEST,
        "- stage316_spqlios_ifft_abi_preflight:",
        "\n- stage316_spqlios_ifft_abi_preflight:\n"
        "  - `docs/stage316_spqlios_ifft_abi_preflight.md`\n"
        "  - `theory_checks/stage316_spqlios_ifft_abi_model.md`\n"
        "  - `algorithm_variants/mat_rlwe_sab_stage316_spqlios_ifft_batch5.md`\n"
        "  - `experiments/stage316_spqlios_ifft_batch5_plan.md`\n"
        "  - `scripts/build_stage316_spqlios_ifft_abi_preflight.py`\n"
        "  - `repro/stage316_spqlios_ifft_abi_preflight/`\n",
    )
    append_once(
        CHECKLIST,
        "<!-- stage316-spqlios-ifft-abi-preflight-checklist -->",
        "\n<!-- stage316-spqlios-ifft-abi-preflight-checklist -->\n"
        f"- [x] Stage316 records `{decision}` and Stage317 isolated batch5 gate.\n",
    )
    append_run_log(decision)

    artifacts = [
        DOC,
        THEORY,
        VARIANT,
        PLAN,
        BUILDER,
        SUMMARY,
        SYMBOLS,
        ROUTES,
        ANCHORS,
        PROOF,
        NEXT,
        COMMANDS,
        REPORT,
    ]
    artifact_index(artifacts)
    print(decision)


if __name__ == "__main__":
    main()
