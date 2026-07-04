#!/usr/bin/env python3
"""Build Stage317 SPQLIOS ifft_batch5 skeleton feasibility artifacts."""

from __future__ import annotations

import csv
import hashlib
import math
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage317_spqlios_ifft_batch5_skeleton"
DOC = ROOT / "docs" / "stage317_spqlios_ifft_batch5_skeleton.md"
THEORY = ROOT / "theory_checks" / "stage317_ifft_batch5_static_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage317_ifft_batch5_tile32.md"
PLAN = ROOT / "experiments" / "stage317_ifft_batch5_tile32_plan.md"
BUILDER = ROOT / "scripts" / "build_stage317_spqlios_ifft_batch5_skeleton.py"

SUMMARY = OUT / "stage317_summary.csv"
REGISTER = OUT / "register_budget.csv"
MEMORY = OUT / "static_memory_model.csv"
ROUTES = OUT / "implementation_routes.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
SKELETON = OUT / "batch5_tile32_skeleton.md"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage317_report.md"
ARTIFACT = OUT / "artifact_index.csv"

STAGE316 = ROOT / "repro" / "stage316_spqlios_ifft_abi_preflight" / "stage316_summary.csv"
STAGE315_THRESHOLDS = ROOT / "repro" / "stage315_backend_ifft_admission" / "component_thresholds.csv"
IFFT_AVX512 = ROOT / "src" / "mosfhet" / "src" / "fft" / "spqlios" / "spqlios-ifft-avx512.s"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION = "PASS_STAGE317_IFFT_BATCH5_TILE32_SKELETON_STAGE318_MICRO_REQUIRED"
DECISION_FAIL = "FAIL_STAGE317_IFFT_BATCH5_SKELETON_INPUT_MISSING"


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


def max_zmm_index(text: str) -> int:
    vals = [int(match) for match in re.findall(r"%zmm(\d+)", text)]
    return max(vals) if vals else -1


def required_component_reduction() -> float:
    row = first(read_csv(STAGE315_THRESHOLDS), "component", "spqlios_ifft")
    return fnum(row.get("component_reduction_required_for_1p02_body"))


def append_run_log(decision: str) -> None:
    run_id = "stage317-spqlios-ifft-batch5-skeleton-001"
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
        "stage": "Stage 317",
        "backend": "analysis",
        "command": "python3 scripts/build_stage317_spqlios_ifft_batch5_skeleton.py",
        "config": "static register and memory model for AVX512 ifft_batch5",
        "params": "r=4 rows=k+r=5; tile3+tile2 skeleton; no SAB integration",
        "seed": "n/a",
        "status": decision,
        "summary": "Stage317 selects a tile3+tile2 isolated AVX512 batch5 skeleton and defines Stage318 microbench gates.",
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
    stage316_decision = stage_decision(STAGE316)
    req_reduction = required_component_reduction()
    asm_text = read_text(IFFT_AVX512)
    observed_max_zmm = max_zmm_index(asm_text)

    zmm_total = 32
    shared_trig_zmm = 2
    offloop_live_per_row = 8
    firstloop_live_per_row = 4
    full5_offloop_zmm = shared_trig_zmm + 5 * offloop_live_per_row
    tile3_offloop_zmm = shared_trig_zmm + 3 * offloop_live_per_row
    tile2_offloop_zmm = shared_trig_zmm + 2 * offloop_live_per_row
    max_rows_no_spill = (zmm_total - shared_trig_zmm) // offloop_live_per_row

    stage316_ok = stage316_decision.startswith("PASS_STAGE316")
    tile32_feasible = full5_offloop_zmm > zmm_total and tile3_offloop_zmm <= zmm_total and tile2_offloop_zmm <= zmm_total
    decision = DECISION if stage316_ok and tile32_feasible else DECISION_FAIL

    register_rows = [
        {
            "case": "current_single_row_assembly",
            "zmm_total_avx512": zmm_total,
            "observed_max_zmm_index": observed_max_zmm,
            "required_zmm": observed_max_zmm + 1 if observed_max_zmm >= 0 else "",
            "status": "BASELINE",
            "interpretation": "Current assembly uses zmm0-zmm15 even though AVX512 has zmm0-zmm31.",
        },
        {
            "case": "full5_offloop_no_spill",
            "zmm_total_avx512": zmm_total,
            "observed_max_zmm_index": observed_max_zmm,
            "required_zmm": full5_offloop_zmm,
            "status": "REJECT_SPILLS" if full5_offloop_zmm > zmm_total else "PASS",
            "interpretation": "Processing all five rows simultaneously needs too many live vectors in the offloop.",
        },
        {
            "case": "tile3_offloop",
            "zmm_total_avx512": zmm_total,
            "observed_max_zmm_index": observed_max_zmm,
            "required_zmm": tile3_offloop_zmm,
            "status": "PASS_NO_ZMM_SPILL" if tile3_offloop_zmm <= zmm_total else "REJECT",
            "interpretation": "First tile can share trig loads across three rows without zmm spills.",
        },
        {
            "case": "tile2_offloop",
            "zmm_total_avx512": zmm_total,
            "observed_max_zmm_index": observed_max_zmm,
            "required_zmm": tile2_offloop_zmm,
            "status": "PASS_NO_ZMM_SPILL" if tile2_offloop_zmm <= zmm_total else "REJECT",
            "interpretation": "Second tile handles the remaining two rows.",
        },
        {
            "case": "max_rows_per_tile_no_spill",
            "zmm_total_avx512": zmm_total,
            "observed_max_zmm_index": observed_max_zmm,
            "required_zmm": max_rows_no_spill,
            "status": "TILE3_SELECTED" if max_rows_no_spill == 3 else "REVIEW",
            "interpretation": "Static model selects tile3+tile2 for rows=5.",
        },
    ]
    write_csv(
        REGISTER,
        register_rows,
        [
            "case",
            "zmm_total_avx512",
            "observed_max_zmm_index",
            "required_zmm",
            "status",
            "interpretation",
        ],
    )

    memory_rows = [
        {
            "loop_region": "firstloop_with_trig",
            "single_row_vector_mem_ops": 6,
            "five_single_rows_vector_mem_ops": 30,
            "tile32_vector_mem_ops": 24,
            "static_memop_reduction": f"{(30 - 24) / 30:.6f}",
            "notes": "Shares trig loads once per tile; data loads/stores unchanged.",
        },
        {
            "loop_region": "nnloop_offloop_with_trig",
            "single_row_vector_mem_ops": 10,
            "five_single_rows_vector_mem_ops": 50,
            "tile32_vector_mem_ops": 44,
            "static_memop_reduction": f"{(50 - 44) / 50:.6f}",
            "notes": "Dominant butterfly region; tile3+tile2 shares trig loads twice instead of five times.",
        },
        {
            "loop_region": "size4_size2_no_trig",
            "single_row_vector_mem_ops": 4,
            "five_single_rows_vector_mem_ops": 20,
            "tile32_vector_mem_ops": 20,
            "static_memop_reduction": f"{0.0:.6f}",
            "notes": "No trig-table load sharing opportunity.",
        },
    ]
    write_csv(
        MEMORY,
        memory_rows,
        [
            "loop_region",
            "single_row_vector_mem_ops",
            "five_single_rows_vector_mem_ops",
            "tile32_vector_mem_ops",
            "static_memop_reduction",
            "notes",
        ],
    )

    routes = [
        {
            "route_id": "R317-1-full5-single-tile",
            "status": "REJECT_ZMM_SPILL_RISK",
            "mechanism": "Fuse all five rows in one AVX512 loop body.",
            "reason": f"Requires {full5_offloop_zmm} zmm registers in offloop, above {zmm_total}.",
        },
        {
            "route_id": "R317-2-tile3-plus-tile2",
            "status": "SELECT_FOR_STAGE318_ISOLATED_MICROBENCH",
            "mechanism": "Run shared-trig row tiles of 3 then 2 rows for each IFFT loop region.",
            "reason": f"Tile3 requires {tile3_offloop_zmm} zmm registers; tile2 requires {tile2_offloop_zmm}.",
        },
        {
            "route_id": "R317-3-sab-integration",
            "status": "BLOCKED_UNTIL_ISOLATED_PASS",
            "mechanism": "Wire batch5 into MAT direct sub-DTF.",
            "reason": "Needs bit/float equivalence and isolated IFFT reduction before touching SAB.",
        },
    ]
    write_csv(ROUTES, routes, ["route_id", "status", "mechanism", "reason"])

    summary = [
        {
            "decision": decision,
            "stage316_input": stage316_decision,
            "selected_tile_plan": "tile3_plus_tile2",
            "full5_required_zmm": full5_offloop_zmm,
            "tile3_required_zmm": tile3_offloop_zmm,
            "tile2_required_zmm": tile2_offloop_zmm,
            "required_ifft_component_reduction": f"{req_reduction:.6f}",
            "static_nnloop_memop_reduction": f"{(50 - 44) / 50:.6f}",
            "next_stage": "stage318_isolated_ifft_batch5_tile32_microbench_or_stop",
        }
    ]
    write_csv(
        SUMMARY,
        summary,
        [
            "decision",
            "stage316_input",
            "selected_tile_plan",
            "full5_required_zmm",
            "tile3_required_zmm",
            "tile2_required_zmm",
            "required_ifft_component_reduction",
            "static_nnloop_memop_reduction",
            "next_stage",
        ],
    )

    proof = [
        {
            "gate": "G1_stage316_input",
            "status": "PASS" if stage316_ok else "FAIL",
            "metric": "Stage316 decision",
            "value": stage316_decision,
            "interpretation": "Stage317 follows the selected isolated batch5 route.",
        },
        {
            "gate": "G2_full5_rejected",
            "status": "PASS" if full5_offloop_zmm > zmm_total else "RECHECK",
            "metric": "full5 required zmm vs available",
            "value": f"{full5_offloop_zmm};{zmm_total}",
            "interpretation": "Reject all-five-row single tile to avoid zmm spilling.",
        },
        {
            "gate": "G3_tile32_register_budget",
            "status": "PASS" if tile32_feasible else "FAIL",
            "metric": "tile3;tile2 required zmm",
            "value": f"{tile3_offloop_zmm};{tile2_offloop_zmm}",
            "interpretation": "Tile3+tile2 is the only admitted register-feasible skeleton.",
        },
        {
            "gate": "G4_static_potential",
            "status": "BORDERLINE_MEASURE",
            "metric": "nnloop static memop reduction vs required IFFT component reduction",
            "value": f"{(50 - 44) / 50:.6f};{req_reduction:.6f}",
            "interpretation": "Static opportunity is close enough to require measurement, not promotion.",
        },
        {
            "gate": "G5_no_sab_integration",
            "status": "PASS",
            "metric": "policy",
            "value": "isolated microbench first",
            "interpretation": "No full SAB code path may depend on this until Stage318 passes.",
        },
        {
            "gate": "G6_decision",
            "status": decision,
            "metric": "stage decision",
            "value": decision,
            "interpretation": "Controls Stage318.",
        },
    ]
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "interpretation"])

    write_csv(
        NEXT,
        [
            {
                "priority": "P0",
                "stage": "stage318_isolated_ifft_batch5_tile32_microbench_or_stop",
                "input": decision,
                "task": "Implement an isolated tile3+tile2 AVX512 batch5 IFFT microbench or stop with concrete assembly constraints.",
                "gate": f"row-wise equivalence against five `ifft` calls and >= {req_reduction:.6f} isolated IFFT component reduction before SAB integration",
            }
        ],
        ["priority", "stage", "input", "task", "gate"],
    )

    skeleton_md = f"""# Batch5 Tile3+Tile2 Skeleton

This is a register-level skeleton, not an implemented backend symbol.

```text
ifft_batch5_tile32(tables, row0, row1, row2, row3, row4):
  for each IFFT loop region that loads trig tables:
    for each butterfly/vector position:
      load shared trig vectors once for tile rows 0..2
      apply the single-row butterfly equations to row0, row1, row2
      load shared trig vectors once for tile rows 3..4
      apply the same equations to row3, row4
  for size4/size2 regions with no trig-table sharing:
      either keep row-tiled form or fall back to per-row code
```

Register budget:

- full five-row offloop: {full5_offloop_zmm} zmm registers, rejected;
- tile3 offloop: {tile3_offloop_zmm} zmm registers, admitted;
- tile2 offloop: {tile2_offloop_zmm} zmm registers, admitted.

Promotion requirement for Stage318: row-wise equivalence against five existing
`ifft` calls and at least {req_reduction:.6f} isolated IFFT component reduction.
"""
    write_text(SKELETON, skeleton_md)

    report = (
        "# Stage317 SPQLIOS IFFT Batch5 Skeleton\n\n"
        f"Decision: `{decision}`.\n\n"
        "Stage317 rejects a single full5 fused loop because the offloop would "
        "spill zmm registers. It selects a `tile3 + tile2` skeleton as the only "
        "admitted Stage318 isolated microbench target. This is not a SAB speed "
        "claim and does not modify the SAB hot path.\n\n"
        "## Summary\n\n"
        + table(summary, [
            "decision",
            "selected_tile_plan",
            "full5_required_zmm",
            "tile3_required_zmm",
            "tile2_required_zmm",
            "required_ifft_component_reduction",
            "static_nnloop_memop_reduction",
            "next_stage",
        ])
        + "\n\n## Register Budget\n\n"
        + table(register_rows, ["case", "required_zmm", "status", "interpretation"])
        + "\n\n## Static Memory Model\n\n"
        + table(memory_rows, [
            "loop_region",
            "five_single_rows_vector_mem_ops",
            "tile32_vector_mem_ops",
            "static_memop_reduction",
            "notes",
        ])
        + "\n\n## Routes\n\n"
        + table(routes, ["route_id", "status", "mechanism", "reason"])
        + "\n\n## Proof Gate\n\n"
        + table(proof, ["gate", "status", "metric", "value", "interpretation"])
        + "\n"
    )
    write_text(DOC, report)
    write_text(REPORT, report)

    write_text(
        THEORY,
        f"""# Stage317 IFFT Batch5 Static Model

For r=4 and k=1, MAT direct sub-DTF has rows=k+r=5.  A single tile containing
all five rows is rejected because the offloop needs

```text
2 shared trig zmm + 5 * 8 per-row zmm = {full5_offloop_zmm}
```

live vector registers, exceeding the {zmm_total} zmm registers available in
AVX512.  The admitted skeleton is `tile3 + tile2`:

```text
2 + 3 * 8 = {tile3_offloop_zmm}
2 + 2 * 8 = {tile2_offloop_zmm}
```

The static memory model is not a performance result.  It only shows why the
candidate is measurable: in the trig-loading nnloop, five single-row calls use
50 vector memory operations per abstract butterfly group, while tile3+tile2
uses 44, a {(50 - 44) / 50:.6f} static reduction.  Stage318 must measure
whether this reaches the {req_reduction:.6f} required IFFT component reduction
from Stage315.
""",
    )

    write_text(
        VARIANT,
        f"""# Stage317 Candidate: `ifft_batch5` Tile3+Tile2

## Summary

- Parent algorithm: PVW/MAT-SAB direct sub-DTF materialization.
- Focused module: SPQLIOS AVX512 inverse transform for gadget rows.
- Optimization target: isolated IFFT component time, then complete SAB `T_bootstrap/r`.
- Status labels: `[experimental gate]`, `[implementation pending]`, `[not a SAB claim]`.
- Main hypothesis: tile3+tile2 row batching can share trig-table loads enough
  to reduce the isolated IFFT component by at least {req_reduction:.6f}.

## Mathematical Definition

The transform result is unchanged:

```text
forall row in 0..4: out[row] = IFFT(row)
```

The variant changes only the backend schedule used to compute those five
independent row transforms.

## Pseudocode

```text
Input: tables, row0..row4
Output: row0..row4 after the same IFFT as five scalar calls
1. For trig-loading IFFT regions, process row0..row2 as one tile.
2. Process row3..row4 as the second tile.
3. For non-trig regions, preserve the same row-wise equations.
4. Return transformed rows.
```

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| five `ifft(tables,row)` calls | one isolated `ifft_batch5_tile32` backend routine | implements same transform schedule with shared trig loads | Stage317 static gate only |

## Required Experiments

- Baseline: five existing AVX512 `ifft` calls.
- Metric: isolated IFFT time and exact row-wise output equivalence.
- Success: at least {req_reduction:.6f} IFFT component reduction.
- Failure: any output mismatch, zmm/GPR spills that erase benefit, or reduction below gate.
""",
    )

    write_text(
        PLAN,
        f"""# Stage317 Plan For Stage318

1. Implement an isolated `ifft_batch5_tile32` candidate or record a concrete
   assembly-level impossibility.
2. Benchmark it against five existing `ifft` calls with the same buffers and
   tables.
3. Verify row-wise output equivalence for all five rows.
4. Require >= {req_reduction:.6f} isolated IFFT component reduction.
5. Do not connect the candidate to `mat_trgsw_sub_decompose_DFT_direct` until
   the isolated gate passes.
""",
    )

    write_text(
        COMMANDS,
        """# Stage317 Reproduction Commands

```bash
python3 scripts/build_stage317_spqlios_ifft_batch5_skeleton.py
```
""",
    )

    append_once(
        ROADMAP,
        "## Stage 317: SPQLIOS IFFT Batch5 Skeleton",
        "\n## Stage 317: SPQLIOS IFFT Batch5 Skeleton\n\n"
        "Goal: select or reject a concrete backend skeleton before implementation.\n\n"
        f"Status: `{decision}`.\n",
    )
    append_once(
        GOAL,
        "<!-- stage317-spqlios-ifft-batch5-skeleton -->",
        "\n<!-- stage317-spqlios-ifft-batch5-skeleton -->\n"
        "### Stage317 SPQLIOS IFFT batch5 skeleton\n\n"
        f"`{decision}` rejects full5 no-spill fusion and selects tile3+tile2 "
        "as the isolated Stage318 candidate.\n",
    )
    append_once(
        HYPOTHESES,
        "H317_spqlios_ifft_batch5_tile32:",
        "\nH317_spqlios_ifft_batch5_tile32:\n"
        f"  status: {decision}\n"
        "  primary_metric: isolated_ifft_component_reduction\n"
        "  evidence:\n"
        "    - repro/stage317_spqlios_ifft_batch5_skeleton/stage317_summary.csv\n"
        "    - repro/stage317_spqlios_ifft_batch5_skeleton/register_budget.csv\n"
        "    - repro/stage317_spqlios_ifft_batch5_skeleton/static_memory_model.csv\n"
        "    - repro/stage317_spqlios_ifft_batch5_skeleton/proof_gate.csv\n"
        "  conclusion: >\n"
        "    Stage317 admits only a tile3+tile2 isolated batch5 IFFT skeleton for\n"
        "    Stage318 measurement; it makes no complete-SAB speed claim.\n",
    )
    append_once(
        MANIFEST,
        "- stage317_spqlios_ifft_batch5_skeleton:",
        "\n- stage317_spqlios_ifft_batch5_skeleton:\n"
        "  - `docs/stage317_spqlios_ifft_batch5_skeleton.md`\n"
        "  - `theory_checks/stage317_ifft_batch5_static_model.md`\n"
        "  - `algorithm_variants/mat_rlwe_sab_stage317_ifft_batch5_tile32.md`\n"
        "  - `experiments/stage317_ifft_batch5_tile32_plan.md`\n"
        "  - `scripts/build_stage317_spqlios_ifft_batch5_skeleton.py`\n"
        "  - `repro/stage317_spqlios_ifft_batch5_skeleton/`\n",
    )
    append_once(
        CHECKLIST,
        "<!-- stage317-spqlios-ifft-batch5-skeleton-checklist -->",
        "\n<!-- stage317-spqlios-ifft-batch5-skeleton-checklist -->\n"
        f"- [x] Stage317 records `{decision}` and the Stage318 isolated gate.\n",
    )
    append_run_log(decision)

    artifacts = [
        DOC,
        THEORY,
        VARIANT,
        PLAN,
        BUILDER,
        SUMMARY,
        REGISTER,
        MEMORY,
        ROUTES,
        PROOF,
        NEXT,
        SKELETON,
        COMMANDS,
        REPORT,
    ]
    artifact_index(artifacts)
    print(decision)


if __name__ == "__main__":
    main()
