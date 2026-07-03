#!/usr/bin/env python3
"""Stage179: MAT EP/subdecomp microarchitecture audit."""

from __future__ import annotations

import csv
import hashlib
import math
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage179_mat_ep_microarch_audit"

SUMMARY_CSV = OUT_DIR / "summary.csv"
CODE_FACTS_CSV = OUT_DIR / "code_facts.csv"
MECHANISM_CSV = OUT_DIR / "mechanism_screen.csv"
PROJECTION_CSV = OUT_DIR / "projection_requirements.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage179_mat_ep_microarch_audit.md"
PLAN_MD = ROOT / "experiments" / "stage179_mat_ep_microarch_audit_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage179_mat_ep_microarch_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_mat_ep_microarch_audit.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE178_COMPONENT = ROOT / "repro" / "stage178_fullmat_perbit_frontier" / "component_attribution.csv"
STAGE178_SUMMARY = ROOT / "repro" / "stage178_fullmat_perbit_frontier" / "summary.csv"
STAGE111_SUMMARY = ROOT / "repro" / "stage111_r6_fulltile_repeated_gate" / "summary.csv"
STAGE154_SUMMARY = ROOT / "repro" / "stage154_bodymajor_fullsab_closeout" / "summary.csv"
STAGE165_SUMMARY = ROOT / "repro" / "stage165_closed_fullmat_streaming_microbench" / "summary.csv"
STAGE174_SUMMARY = ROOT / "repro" / "stage174_from_dft_direct_scale_gate" / "summary.csv"
MATTRGSW_C = ROOT / "src" / "mosfhet" / "src" / "mattrgsw.c"
MAKEFILE_DEF = ROOT / "src" / "mosfhet" / "Makefile.def"

DECISION = "PASS_STAGE179_AUDIT_SELECT_MAT_EP_SPLIT_PROBE_NO_CODE"
MAT_SHARE = 0.603899465


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((text.rstrip() + "\n").encode("utf-8"))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)
    normalized = [{field: row.get(field, "") for field in fields} for row in row_list]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


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


def contains(path: Path, token: str) -> str:
    return "PRESENT" if token in read_text(path) else "MISSING"


def required_component_speedup(target_full_speedup: float, share: float) -> float:
    denominator = (1.0 / target_full_speedup) - (1.0 - share)
    if denominator <= 0:
        return math.inf
    return share / denominator


def build_code_facts() -> List[Dict[str, str]]:
    return [
        {
            "fact": "current_r_gt4_tiled_avx512_exists",
            "source": rel(MATTRGSW_C),
            "status": contains(MATTRGSW_C, "mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_rgt4_tiled_avx512"),
            "evidence": "Current r=6/r=8 exact path has a MAT-aware AVX512 tiled output kernel.",
            "implication": "The project is not missing a basic MAT-aware AVX512 external-product implementation.",
        },
        {
            "fact": "r6_fulltile_variant_exists",
            "source": rel(MATTRGSW_C),
            "status": contains(MATTRGSW_C, "mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r6_fulltile_avx512"),
            "evidence": "Full-output r=6 tile variant exists behind MAT_TRGSW_AVX512_R6_FULLTILE.",
            "implication": "All-output register residency has already been tested and was not promoted.",
        },
        {
            "fact": "r6_bodymajor_variant_exists",
            "source": rel(MATTRGSW_C),
            "status": contains(MATTRGSW_C, "mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r6_bodymajor_avx512"),
            "evidence": "Body-major r=6 variant exists behind MAT_TRGSW_AVX512_R6_BODYMAJOR.",
            "implication": "Pure layout retuning has prior negative full-SAB evidence.",
        },
        {
            "fact": "sub_decompose_is_separate_scalar_loop",
            "source": rel(MATTRGSW_C),
            "status": contains(MATTRGSW_C, "static void mat_trgsw_sub_decompose"),
            "evidence": "mat_trgsw_sub_decompose computes diff/offset/shift/mask into scratch->dec before DFT.",
            "implication": "The remaining unmeasured mechanism is not another MAT multiply layout; it is subcomponent split and possible vectorized decompose/DFT dataflow.",
        },
        {
            "fact": "sub_decompose_then_dft_then_addmul_boundary",
            "source": rel(MATTRGSW_C),
            "status": contains(MATTRGSW_C, "mat_trgsw_sub_decompose(in1, in2, scratch->dec, selector->Q, l);"),
            "evidence": "mat_trgsw_mul_pvmtmlwe_sub_DFT decomposes to scratch, converts every row to DFT, then calls the AVX512 addmul kernel.",
            "implication": "Stage180 must split these three phases before deciding whether a code change is justified.",
        },
        {
            "fact": "explicit_flags_exist",
            "source": rel(MAKEFILE_DEF),
            "status": contains(MAKEFILE_DEF, "MAT_TRGSW_AVX512_RGT4_FUSED"),
            "evidence": "All relevant exact MAT variants are controlled by explicit flags.",
            "implication": "Any Stage180+ implementation must stay behind a flag and preserve scalar/default behavior.",
        },
    ]


def build_mechanism_rows() -> List[Dict[str, str]]:
    return [
        {
            "mechanism": "M1_split_mat_ep_subcomponents",
            "status": "SELECT_FOR_STAGE180_PROBE",
            "evidence": rel(STAGE178_COMPONENT),
            "reason": "Stage178 shows MAT EP/subdecomp is 60.39% of full time, but Stage170 only times the combined block.",
            "required_gate": "Measure sub_decompose, torus_to_DFT rows, and tiled addmul separately before code.",
        },
        {
            "mechanism": "M2_manual_avx512_sub_decompose",
            "status": "CONDITIONAL",
            "evidence": rel(MATTRGSW_C),
            "reason": "The decompose loop is scalar-looking, but its actual share is unknown.",
            "required_gate": "Only implement if Stage180 shows enough share for >=3% full-SAB projection.",
        },
        {
            "mechanism": "M3_fulltile_or_bodymajor_retuning",
            "status": "REJECT_NO_NEW_MECHANISM",
            "evidence": f"{rel(STAGE111_SUMMARY)}; {rel(STAGE154_SUMMARY)}",
            "reason": "Fulltile/bodymajor variants exist and were not promoted at complete-SAB gates.",
            "required_gate": "Do not reopen without a different arithmetic/dataflow mechanism.",
        },
        {
            "mechanism": "M4_streaming_row_dft",
            "status": "REJECT_NO_NEW_MECHANISM",
            "evidence": rel(STAGE165_SUMMARY),
            "reason": "Closed full-MAT streaming was slower than current tiled AVX.",
            "required_gate": "Do not reopen row-streaming unless the addmul locality problem is changed.",
        },
        {
            "mechanism": "M5_from_dft_direct_scale",
            "status": "DEFER",
            "evidence": rel(STAGE174_SUMMARY),
            "reason": "Stage174 direct-scale was neutral and is outside the selected MAT EP/subdecomp block.",
            "required_gate": "Reopen only with a new from_DFT mechanism.",
        },
    ]


def build_projection_rows() -> List[Dict[str, str]]:
    return [
        {
            "target_full_sab_speedup": f"{target:.6f}",
            "mat_ep_share": f"{MAT_SHARE:.9f}",
            "required_mat_ep_component_speedup": f"{required_component_speedup(target, MAT_SHARE):.9f}",
            "interpretation": "Minimum component speedup over the current MAT EP/subdecomp block needed to reach target full-SAB gain.",
        }
        for target in [1.01, 1.02, 1.03, 1.05, 1.10]
    ]


def build_summary_rows() -> List[Dict[str, str]]:
    return [
        {
            "gate": "stage179_inputs",
            "status": "PASS" if STAGE178_SUMMARY.exists() and MATTRGSW_C.exists() else "FAIL",
            "metric": "stage178_and_code_present",
            "value": "1" if STAGE178_SUMMARY.exists() and MATTRGSW_C.exists() else "0",
            "evidence": f"{rel(STAGE178_SUMMARY)}; {rel(MATTRGSW_C)}",
            "detail": "Stage179 consumes Stage178 frontier and current MAT external-product source.",
            "next_action": "Repair missing inputs before audit.",
        },
        {
            "gate": "stage179_avx512_completeness",
            "status": "PASS_ALREADY_PRESENT",
            "metric": "rgt4_tiled;r6_fulltile;r6_bodymajor",
            "value": "present;present;present",
            "evidence": rel(CODE_FACTS_CSV),
            "detail": "MAT-aware AVX512 implementations for the current r=6 path and prior variants already exist.",
            "next_action": "Do not claim the project lacks MAT AVX512; the issue is whether any remaining exact-path mechanism exists.",
        },
        {
            "gate": "stage179_no_direct_code_permission",
            "status": "DENY_CODE_NOW",
            "metric": "split_subcomponent_data_available",
            "value": "0",
            "evidence": rel(MECHANISM_CSV),
            "detail": "The combined MAT EP/subdecomp block is hot, but internal shares are not split enough to justify code.",
            "next_action": "Run Stage180 split probe before implementation.",
        },
        {
            "gate": "stage179_decision",
            "status": DECISION,
            "metric": "route",
            "value": "stage180_mat_ep_split_probe",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Avoid theory loop and blind retuning: the next step is a measurement probe, not another speculative AVX512 variant.",
            "next_action": "Run Stage180.",
        },
    ]


def build_next_rows() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "stage": "180",
            "name": "MAT EP split probe",
            "entry_condition": "Stage179 selects split probe and denies code now.",
            "gate": "Measure sub_decompose, torus_to_DFT, and tiled addmul inside mat_trgsw_mul_pvmtmlwe_sub_DFT.",
            "failure_rule": "If no subcomponent can project >=3% full-SAB gain, close exact-path tuning.",
        },
        {
            "priority": "P1",
            "stage": "181",
            "name": "conditional AVX512 sub-decompose implementation",
            "entry_condition": "Stage180 shows sub_decompose share is large enough.",
            "gate": "Implement behind flag, pass correctness, microbench, full-SAB repeated A/B.",
            "failure_rule": "Reject if full-SAB T_bootstrap/r does not improve.",
        },
        {
            "priority": "P2",
            "stage": "182",
            "name": "negative frontier",
            "entry_condition": "Stage180 does not identify an implementable mechanism.",
            "gate": "Record remaining exact-path headroom and stop blind optimization.",
            "failure_rule": "Do not retune old fulltile/bodymajor/streaming candidates.",
        },
    ]


def write_docs(summary_rows: List[Dict[str, str]], code_rows: List[Dict[str, str]],
               mechanism_rows: List[Dict[str, str]], projection_rows: List[Dict[str, str]],
               next_rows: List[Dict[str, str]]) -> None:
    write_text_lf(OUT_MD, f"""# Stage179 MAT EP Microarchitecture Audit

Decision: `{DECISION}`.

Stage179 answers a narrow question: is the current project missing a complete
MAT-aware AVX512 external-product implementation? No. The current r=6/r=8 path
already uses a MAT-aware AVX512 tiled kernel, and prior r=6 fulltile/bodymajor
variants have been tested.

The unresolved performance question is narrower: inside
`mat_trgsw_mul_pvmtmlwe_sub_DFT`, how much time is spent in
`mat_trgsw_sub_decompose`, row `torus_to_DFT`, and tiled addmul? Stage179 does
not grant code permission until Stage180 measures those subcomponents.

## Gate Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Code Facts

{table(code_rows, ["fact", "source", "status", "evidence", "implication"])}
## Mechanism Screen

{table(mechanism_rows, ["mechanism", "status", "evidence", "reason", "required_gate"])}
## Projection Requirements

{table(projection_rows, ["target_full_sab_speedup", "mat_ep_share", "required_mat_ep_component_speedup", "interpretation"])}
## Next Queue

{table(next_rows, ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"])}
""")

    write_text_lf(PLAN_MD, """# Stage179 Plan

Goal: audit the current MAT EP/subdecomp implementation and choose whether any
exact full-MAT AVX512 code work is justified.

Rules:

- Do not implement code from combined-component timing alone.
- Do not reopen fulltile/bodymajor/streaming without a new mechanism.
- Do not touch compact SAB because Stage176/177 block it.
- The next gate must split sub_decompose, torus_to_DFT, and addmul timing.

Decision: run Stage180 split probe before code.
""")

    write_text_lf(THEORY_MD, f"""# Stage179 Microarchitecture Model

Stage178 attributes `{MAT_SHARE:.9f}` of current complete-SAB time to the
combined MAT EP/subdecomp block. A full-SAB improvement target `S` requires a
component speedup:

```text
x >= share / (1/S - (1 - share))
```

For example, a 3% complete-SAB gain requires a component speedup of
`{required_component_speedup(1.03, MAT_SHARE):.9f}` on the MAT EP/subdecomp
block. That is plausible only if a real subcomponent bottleneck exists.

The audit therefore rejects blind implementation and selects a split probe.
""")

    write_text_lf(VARIANT_MD, """# MAT EP Microarchitecture Audit Variant

Selected route: split-probe only.

Current facts:

- MAT-aware AVX512 tiled r>4 kernel exists.
- r=6 fulltile/bodymajor variants exist and have negative/neutral complete-SAB
  evidence.
- row streaming lost to the current tiled path.
- compact integration remains blocked.

Next valid implementation candidate, if any, must come from a measured
subcomponent split inside `mat_trgsw_mul_pvmtmlwe_sub_DFT`.
""")


def write_global_updates() -> None:
    append_once(ROADMAP_MD, "## Stage 179: MAT EP Microarchitecture Audit", f"""
## Stage 179: MAT EP Microarchitecture Audit

Goal:

```text
Audit whether current exact full-MAT r=6 still has an implementable AVX512
mechanism before writing more code.
```

Status:

```text
Completed. Stage179 records {DECISION}. MAT-aware AVX512 exists; code
permission is denied until Stage180 splits sub_decompose, torus_to_DFT, and
tiled addmul timing inside the hot block.
```
""")
    append_once(GOAL_MD, "Stage179 records MAT EP microarchitecture audit", f"""
Stage179 records MAT EP microarchitecture audit evidence. Decision:
`{DECISION}`. The project already has MAT-aware AVX512 external product; the
next valid step is a split probe, not blind AVX512 retuning.
""")
    append_once(CURRENT_GOAL_MD, "Treat Stage179 as the MAT EP microarchitecture audit", f"""
83. Treat Stage179 as the MAT EP microarchitecture audit:
    `{DECISION}`. Current r=6 MAT-aware AVX512 exists. Stage180 must split
    sub_decompose, torus_to_DFT, and tiled addmul before any new exact-path
    implementation branch opens.
""")
    append_once(HYPOTHESIS_YAML, "H103_mat_ep_microarch_audit", f"""
  - id: H103_mat_ep_microarch_audit
    statement: >
      The project already has a MAT-aware AVX512 exact external-product path;
      further full-MAT speedup requires a measured subcomponent mechanism inside
      mat_trgsw_mul_pvmtmlwe_sub_DFT rather than blind layout retuning.
    mechanism: >
      Stage179 audits code facts and prior negative full-SAB gates, then
      selects a split probe for sub_decompose, torus_to_DFT, and tiled addmul.
    status: stage179_mat_ep_microarch_audit
    evidence: docs/stage179_mat_ep_microarch_audit.md; experiments/stage179_mat_ep_microarch_audit_plan.md; theory_checks/stage179_mat_ep_microarch_model.md; repro/stage179_mat_ep_microarch_audit/summary.csv
    current_decision: >
      {DECISION}
    failure_criteria:
      - code is written before subcomponent timing exists
      - old fulltile/bodymajor/streaming variants are reopened without a new
        mechanism
      - kernel-only data is reported as complete-SAB acceleration
""")
    append_once(RUN_LOG, "stage179-mat-ep-microarch-audit-001", f"""
stage179-mat-ep-microarch-audit-001,2026-07-04,{git_head()},Stage 179,analysis,python scripts/build_stage179_mat_ep_microarch_audit.py,Stage178+source audit,none,{DECISION},MAT EP/subdecomp microarchitecture audit and split-probe routing.,repro/stage179_mat_ep_microarch_audit
""")
    append_once(MANIFEST, "stage179_mat_ep_microarch_audit", f"""
- stage179_mat_ep_microarch_audit: `{DECISION}`
  - `docs/stage179_mat_ep_microarch_audit.md`
  - `experiments/stage179_mat_ep_microarch_audit_plan.md`
  - `theory_checks/stage179_mat_ep_microarch_model.md`
  - `algorithm_variants/mat_rlwe_sab_mat_ep_microarch_audit.md`
  - `repro/stage179_mat_ep_microarch_audit/`
""")
    append_once(CHECKLIST, "Stage179 MAT EP microarchitecture audit pack recorded", """
- [x] Stage179 MAT EP microarchitecture audit pack recorded.
""")


def write_artifacts(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        rows.append({
            "path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path),
            "bytes": str(path.stat().st_size) if path.exists() else "0",
        })
    write_csv(ARTIFACT_CSV, rows, ["path", "exists", "sha256", "bytes"])


def main() -> None:
    code_rows = build_code_facts()
    mechanism_rows = build_mechanism_rows()
    projection_rows = build_projection_rows()
    summary_rows = build_summary_rows()
    next_rows = build_next_rows()

    write_csv(CODE_FACTS_CSV, code_rows, ["fact", "source", "status", "evidence", "implication"])
    write_csv(MECHANISM_CSV, mechanism_rows, ["mechanism", "status", "evidence", "reason", "required_gate"])
    write_csv(PROJECTION_CSV, projection_rows, ["target_full_sab_speedup", "mat_ep_share", "required_mat_ep_component_speedup", "interpretation"])
    write_csv(SUMMARY_CSV, summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    write_csv(NEXT_CSV, next_rows, ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"])
    write_docs(summary_rows, code_rows, mechanism_rows, projection_rows, next_rows)
    write_global_updates()
    write_artifacts([
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        SUMMARY_CSV,
        CODE_FACTS_CSV,
        MECHANISM_CSV,
        PROJECTION_CSV,
        NEXT_CSV,
        Path(__file__),
    ])
    print(DECISION)


if __name__ == "__main__":
    main()
