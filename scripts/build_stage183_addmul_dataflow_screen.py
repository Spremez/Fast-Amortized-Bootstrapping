#!/usr/bin/env python3
"""Stage183: addmul dataflow mechanism screen."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage183_addmul_dataflow_screen"

SUMMARY_CSV = OUT_DIR / "summary.csv"
SOURCE_FACTS_CSV = OUT_DIR / "source_facts.csv"
MECHANISM_CSV = OUT_DIR / "mechanism_screen.csv"
PROJECTION_CSV = OUT_DIR / "projection.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage183_addmul_dataflow_screen.md"
PLAN_MD = ROOT / "experiments" / "stage183_addmul_dataflow_screen_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage183_addmul_dataflow_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_addmul_dataflow_screen.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

MATTRGSW_C = ROOT / "src" / "mosfhet" / "src" / "mattrgsw.c"
MAKEFILE_DEF = ROOT / "src" / "mosfhet" / "Makefile.def"
STAGE182_SUMMARY = ROOT / "repro" / "stage182_exact_path_negative_frontier" / "summary.csv"
STAGE182_FRONTIER = ROOT / "repro" / "stage182_exact_path_negative_frontier" / "frontier_decisions.csv"
STAGE180_DERIVED = ROOT / "repro" / "stage180_mat_ep_split_probe" / "derived_projection.csv"
STAGE180_RUNS = ROOT / "repro" / "stage180_mat_ep_split_probe" / "run_metrics.csv"
STAGE154_SUMMARY = ROOT / "repro" / "stage154_bodymajor_fullsab_closeout" / "summary.csv"
STAGE165_SUMMARY = ROOT / "repro" / "stage165_closed_fullmat_streaming_microbench" / "summary.csv"
STAGE111_SUMMARY = ROOT / "repro" / "stage111_r6_fulltile_repeated_gate" / "summary.csv"
STAGE112_SUMMARY = ROOT / "repro" / "stage112_selector_format_gate" / "summary.csv"
STAGE176_SUMMARY = ROOT / "repro" / "stage176_structured_compact_security_api_gate" / "summary.csv"

DECISION = "PASS_STAGE183_ADDMUL_DATAFLOW_SCREEN_NO_CODE_PERMISSION"
R = 6
ROWS = R + 1
OUTPUTS = R + 1


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((text.rstrip() + "\n").encode("utf-8"))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
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


def line_of(token: str) -> str:
    for lineno, line in enumerate(read_text(MATTRGSW_C).splitlines(), 1):
        if token in line:
            return str(lineno)
    return ""


def contains(path: Path, token: str) -> str:
    return "yes" if token in read_text(path) else "no"


def metric_value(metric: str) -> str:
    for row in read_csv_dicts(STAGE180_DERIVED):
        if row.get("metric") == metric:
            return row.get("value", "")
    return ""


def split_pair(metric: str) -> tuple[str, str]:
    value = metric_value(metric)
    if ";" not in value:
        return value, ""
    left, right = value.split(";", 1)
    return left, right


def run_value(variant: str, column: str) -> str:
    for row in read_csv_dicts(STAGE180_RUNS):
        if row.get("variant") == variant:
            return row.get(column, "")
    return ""


def build_source_rows() -> List[Dict[str, str]]:
    return [
        {
            "fact": "complex_addmul_uses_avx512_fma",
            "status": contains(MATTRGSW_C, "static inline void mat_avx512_complex_addmul"),
            "line": line_of("static inline void mat_avx512_complex_addmul"),
            "evidence": rel(MATTRGSW_C),
            "implication": "The addmul hot loop is already vectorized with AVX512 FMA helpers.",
        },
        {
            "fact": "rgt4_tiled_kernel_exists",
            "status": contains(MATTRGSW_C, "mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_rgt4_tiled_avx512"),
            "line": line_of("mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_rgt4_tiled_avx512"),
            "evidence": rel(MATTRGSW_C),
            "implication": "Current r=6/r=8 path already reuses each decomposed row across output tiles.",
        },
        {
            "fact": "r6_fulltile_kernel_exists",
            "status": contains(MATTRGSW_C, "mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r6_fulltile_avx512"),
            "line": line_of("mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r6_fulltile_avx512"),
            "evidence": rel(MATTRGSW_C),
            "implication": "Register-resident all-output accumulation was implemented as an explicit variant.",
        },
        {
            "fact": "r6_bodymajor_kernel_exists",
            "status": contains(MATTRGSW_C, "mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r6_bodymajor_avx512"),
            "line": line_of("mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r6_bodymajor_avx512"),
            "evidence": rel(MATTRGSW_C),
            "implication": "Output-major dataflow was implemented as an explicit variant.",
        },
        {
            "fact": "rgt4_dispatch_is_flagged",
            "status": contains(MAKEFILE_DEF, "MAT_TRGSW_AVX512_RGT4_FUSED"),
            "line": "",
            "evidence": rel(MAKEFILE_DEF),
            "implication": "All r>4 MAT variants remain explicit and default-controllable.",
        },
    ]


def build_projection_rows() -> List[Dict[str, str]]:
    add_share, add_req = split_pair("addmul_from_dec_dft_full_sab_share_and_3pct_requirement")
    return [
        {
            "metric": "r",
            "value": str(R),
            "unit": "lanes",
            "interpretation": "Stage183 screens the current exact r=6 path.",
        },
        {
            "metric": "dense_complex_products_per_coeff",
            "value": str(ROWS * OUTPUTS),
            "unit": "complex_vector_products",
            "interpretation": "Closed full-MAT shape has (r+1)^2 products per coefficient block.",
        },
        {
            "metric": "stage180_addmul_per_call_us",
            "value": run_value("addmul_from_dec_dft", "per_call_us"),
            "unit": "us",
            "interpretation": "Measured isolated addmul-from-decomposed-DFT time.",
        },
        {
            "metric": "addmul_full_sab_share",
            "value": add_share,
            "unit": "share",
            "interpretation": "Estimated full-SAB share from Stage180 projection.",
        },
        {
            "metric": "required_addmul_speedup_for_3pct_full_sab",
            "value": add_req,
            "unit": "x",
            "interpretation": "Minimum local speedup needed before a code branch is worthwhile.",
        },
    ]


def build_mechanism_rows() -> List[Dict[str, str]]:
    return [
        {
            "mechanism": "D1_current_tile4_reuse",
            "decision": "CURRENT_BASELINE",
            "evidence": rel(MATTRGSW_C),
            "reason": "The tiled r>4 kernel already loads one decomposed row and updates output tiles for each coefficient.",
            "code_permission": "no_new_code",
        },
        {
            "mechanism": "D2_fulltile_register_resident_outputs",
            "decision": "REJECT_PRIOR_GATE",
            "evidence": rel(STAGE111_SUMMARY),
            "reason": "A full-output r=6 path exists; repeated complete-SAB evidence did not promote it.",
            "code_permission": "do_not_reopen_without_new_mechanism",
        },
        {
            "mechanism": "D3_bodymajor_output_major",
            "decision": "REJECT_PRIOR_GATE",
            "evidence": rel(STAGE154_SUMMARY),
            "reason": "Complete-SAB `T_bootstrap/r` bodymajor/tile4 result was 0.977892.",
            "code_permission": "do_not_reopen_without_new_mechanism",
        },
        {
            "mechanism": "D4_row_streaming_decompose_dft_addmul",
            "decision": "REJECT_PRIOR_GATE",
            "evidence": rel(STAGE165_SUMMARY),
            "reason": "Streaming reduced scratch lifetime but lost to current all-row tiled AVX in exact-output microbench.",
            "code_permission": "do_not_reopen_without_changed_locality_model",
        },
        {
            "mechanism": "D5_more_coefficient_unrolling",
            "decision": "DENY_NO_EVIDENCE",
            "evidence": rel(SOURCE_FACTS_CSV),
            "reason": "Unrolling coefficients duplicates many accumulator registers on top of dec/selector registers; no measured mechanism suggests it beats current tile/fulltile tradeoff.",
            "code_permission": "requires_assembly_counter_preflight_first",
        },
        {
            "mechanism": "D6_selector_transposed_key_layout",
            "decision": "BLOCK_KEY_FORMAT_CHANGE",
            "evidence": rel(STAGE112_SUMMARY),
            "reason": "Better selector locality likely requires key/selector layout changes, not a loop-only exact-path change.",
            "code_permission": "requires_keygen_resource_noise_gate",
        },
        {
            "mechanism": "D7_sparse_selector_skip",
            "decision": "BLOCK_SECURITY_FORMAT",
            "evidence": rel(STAGE176_SUMMARY),
            "reason": "Encrypted selector rows cannot be skipped as plaintext zeros under the current key format.",
            "code_permission": "proof_branch_only",
        },
    ]


def build_summary_rows() -> List[Dict[str, str]]:
    source_ok = all(row["status"] == "yes" for row in build_source_rows())
    return [
        {
            "gate": "stage183_inputs",
            "status": "PASS" if STAGE182_SUMMARY.exists() and MATTRGSW_C.exists() else "FAIL",
            "metric": "required_inputs_present",
            "value": "1" if STAGE182_SUMMARY.exists() and MATTRGSW_C.exists() else "0",
            "evidence": f"{rel(STAGE182_SUMMARY)}; {rel(MATTRGSW_C)}",
            "detail": "Stage183 consumes Stage182 frontier and current MAT addmul source.",
            "next_action": "Repair missing inputs before mechanism screening.",
        },
        {
            "gate": "stage183_source_fact_check",
            "status": "PASS" if source_ok else "FAIL",
            "metric": "mat_aware_avx512_variants_present",
            "value": "1" if source_ok else "0",
            "evidence": rel(SOURCE_FACTS_CSV),
            "detail": "Current source already contains tiled, fulltile, and bodymajor MAT-aware AVX512 variants.",
            "next_action": "Do not describe the project as lacking MAT AVX512 addmul.",
        },
        {
            "gate": "stage183_projection_check",
            "status": "PASS",
            "metric": "required_addmul_speedup_for_3pct_full_sab",
            "value": split_pair("addmul_from_dec_dft_full_sab_share_and_3pct_requirement")[1],
            "evidence": rel(PROJECTION_CSV),
            "detail": "The addmul component is large enough only if a real dataflow gain exists.",
            "next_action": "Reject layout-only retuning without a new proof or counter preflight.",
        },
        {
            "gate": "stage183_decision",
            "status": DECISION,
            "metric": "code_permission",
            "value": "denied",
            "evidence": rel(MECHANISM_CSV),
            "detail": "No untested exact addmul dataflow mechanism currently meets the code-entry rule.",
            "next_action": "Route to final exact-frontier closeout or proof-gated compact work.",
        },
    ]


def build_next_rows() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "stage": "184",
            "name": "exact-route closeout and paper claim refresh",
            "entry_condition": "Stage183 denies new exact addmul code permission.",
            "gate": "Update final claim ledger: scoped complete-SAB speedup allowed, theoretical optimality denied.",
            "failure_rule": "Do not invent another exact AVX512 variant without new measured mechanism.",
        },
        {
            "priority": "P1",
            "stage": "185",
            "name": "structured compact proof unlock",
            "entry_condition": "A proof/literature package for compact shared-mask closure is supplied.",
            "gate": "Selector distribution, closed state, noise, resource, and novelty gates must pass before SAB code.",
            "failure_rule": "If proof is incomplete, keep compact out of hot path.",
        },
    ]


def write_docs(
    summary_rows: List[Dict[str, str]],
    source_rows: List[Dict[str, str]],
    projection_rows: List[Dict[str, str]],
    mechanism_rows: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
) -> None:
    write_text_lf(
        OUT_MD,
        f"""# Stage183 Addmul Dataflow Screen

Decision: `{DECISION}`.

Stage183 checks whether the remaining exact `addmul_from_dec_dft` component
contains a concrete untested dataflow mechanism. It does not. The project
already has MAT-aware AVX512 addmul helpers and r=6 tiled/fulltile/bodymajor
variants. Prior complete-SAB or exact-output gates reject the obvious dataflow
alternatives.

Therefore no new hot-path code is allowed from Stage183. Future work must
either:

- present an assembly/counter-backed addmul mechanism that is not one of the
  rejected layout variants; or
- move to the proof-gated compact/shared-output route; or
- refresh the final scoped claim package without claiming theoretical
  optimality.

## Gate Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Source Facts

{table(source_rows, ["fact", "status", "line", "evidence", "implication"])}
## Projection

{table(projection_rows, ["metric", "value", "unit", "interpretation"])}
## Mechanism Screen

{table(mechanism_rows, ["mechanism", "decision", "evidence", "reason", "code_permission"])}
## Next Queue

{table(next_rows, ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"])}
""",
    )

    write_text_lf(
        PLAN_MD,
        """# Stage183 Plan

Goal: screen addmul dataflow candidates before implementation.

Rules:

- Existing MAT-aware AVX512 code counts as implemented baseline, not future
  work.
- A new branch must be a new mechanism, not a renamed tile/fulltile/bodymajor
  variant.
- Kernel-only or source-only arguments cannot become complete-SAB claims.

Decision: no code permission; route to exact-route closeout or proof-gated
compact work.
""",
    )

    write_text_lf(
        THEORY_MD,
        f"""# Stage183 Addmul Dataflow Model

For the current exact r=6 full-MAT path, the closed dense map has:

```text
rows = r + 1 = {ROWS}
outputs = r + 1 = {OUTPUTS}
complex vector products per coefficient block = rows * outputs = {ROWS * OUTPUTS}
```

The current tiled AVX512 implementation already shares each decomposed row
across output tiles. A full-output register-resident variant and an output-
major variant have already been tested. Row streaming was also tested and
lost to current all-row tiled AVX.

Thus an exact addmul improvement cannot be justified from theory alone. It
needs a new measured dataflow such as a changed selector layout with keygen/
resource gates, or a new assembly/counter preflight that demonstrates fewer
loads/stores/FMA pressure without breaking the dense closed map.
""",
    )

    write_text_lf(
        VARIANT_MD,
        """# Addmul Dataflow Screen Variant

This variant is a no-code screen.

Rejected or blocked routes:

- r=6 fulltile: already implemented and not promoted.
- r=6 bodymajor: complete-SAB negative.
- row streaming: exact-output microbench negative.
- more coefficient unrolling: no mechanism yet and likely register-pressure
  limited.
- selector transpose or sparse skip: key-format/security/resource gates first.

No new `mattrgsw.c` hot-path code is authorized by this stage.
""",
    )


def update_global_docs() -> None:
    append_once(
        ROADMAP_MD,
        "## Stage 183: Addmul Dataflow Screen",
        f"""
## Stage 183: Addmul Dataflow Screen

Goal:

```text
Decide whether the remaining exact addmul component has a concrete untested
dataflow mechanism before writing code.
```

Status:

```text
Completed. Stage183 records {DECISION}. The current project already has
MAT-aware AVX512 tiled/fulltile/bodymajor addmul variants, and prior gates
reject the obvious alternatives. No new exact addmul hot-path code is allowed
without a new assembly/counter-backed mechanism.
```
""",
    )

    append_once(
        GOAL_MD,
        "Stage183 records the addmul dataflow mechanism screen",
        f"""
Stage183 records the addmul dataflow mechanism screen. Decision:
`{DECISION}`. Exact addmul remains a large component, but no currently
untested loop/layout mechanism passes the code-entry rule.
""",
    )

    append_once(
        CURRENT_GOAL_MD,
        "Treat Stage183 as the addmul dataflow screen",
        f"""
87. Treat Stage183 as the addmul dataflow screen:
    `{DECISION}`. The code already contains MAT-aware AVX512 tiled,
    fulltile, and bodymajor addmul variants. Prior gates reject those dataflow
    families, so no new exact addmul code is allowed without a new mechanism.
""",
    )

    append_once(
        HYPOTHESIS_YAML,
        "H107_addmul_dataflow_screen",
        f"""
  - id: H107_addmul_dataflow_screen
    statement: >
      The remaining exact addmul component is large, but current evidence does
      not justify another AVX512/layout implementation unless it introduces a
      new dataflow beyond tiled, fulltile, bodymajor, or streaming variants.
    mechanism: >
      Source audit shows existing MAT-aware AVX512 helpers and r=6 variants;
      prior complete-SAB and exact-output gates reject the obvious alternatives.
    status: stage183_addmul_dataflow_screen
    evidence: docs/stage183_addmul_dataflow_screen.md; experiments/stage183_addmul_dataflow_screen_plan.md; theory_checks/stage183_addmul_dataflow_model.md; repro/stage183_addmul_dataflow_screen/summary.csv
    current_decision: >
      {DECISION}
    failure_criteria:
      - new addmul code is written without a new measured mechanism
      - prior rejected layout variants are reopened under new names
      - source-level AVX512 presence is reported as theoretical optimality
""",
    )

    append_once(
        RUN_LOG,
        "stage183-addmul-dataflow-screen-001",
        f"""
stage183-addmul-dataflow-screen-001,2026-07-04,{git_head()},Stage 183,analysis,python scripts/build_stage183_addmul_dataflow_screen.py,Stage182+source+prior gates,none,{DECISION},Addmul dataflow mechanism screen denies new exact hot-path code.,repro/stage183_addmul_dataflow_screen
""",
    )

    append_once(
        MANIFEST,
        "stage183_addmul_dataflow_screen",
        f"""
- stage183_addmul_dataflow_screen: `{DECISION}`
  - `docs/stage183_addmul_dataflow_screen.md`
  - `experiments/stage183_addmul_dataflow_screen_plan.md`
  - `theory_checks/stage183_addmul_dataflow_model.md`
  - `algorithm_variants/mat_rlwe_sab_addmul_dataflow_screen.md`
  - `repro/stage183_addmul_dataflow_screen/`
""",
    )

    append_once(CHECKLIST, "Stage183 addmul dataflow screen pack recorded", """
- [x] Stage183 addmul dataflow screen pack recorded.
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
    projection_rows = build_projection_rows()
    mechanism_rows = build_mechanism_rows()
    summary_rows = build_summary_rows()
    next_rows = build_next_rows()

    write_csv(SOURCE_FACTS_CSV, source_rows, ["fact", "status", "line", "evidence", "implication"])
    write_csv(PROJECTION_CSV, projection_rows, ["metric", "value", "unit", "interpretation"])
    write_csv(MECHANISM_CSV, mechanism_rows, ["mechanism", "decision", "evidence", "reason", "code_permission"])
    write_csv(SUMMARY_CSV, summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    write_csv(NEXT_CSV, next_rows, ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"])
    write_docs(summary_rows, source_rows, projection_rows, mechanism_rows, next_rows)
    update_global_docs()
    write_artifacts(
        [
            OUT_MD,
            PLAN_MD,
            THEORY_MD,
            VARIANT_MD,
            SUMMARY_CSV,
            SOURCE_FACTS_CSV,
            PROJECTION_CSV,
            MECHANISM_CSV,
            NEXT_CSV,
            Path(__file__),
        ]
    )
    print(DECISION)


if __name__ == "__main__":
    main()
