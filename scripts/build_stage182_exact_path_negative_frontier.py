#!/usr/bin/env python3
"""Stage182: exact full-MAT negative frontier after AVX512 sub-decompose gate."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage182_exact_path_negative_frontier"

SUMMARY_CSV = OUT_DIR / "summary.csv"
FRONTIER_CSV = OUT_DIR / "frontier_decisions.csv"
COMPONENT_CSV = OUT_DIR / "component_recheck.csv"
CLAIM_CSV = OUT_DIR / "claim_permissions.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage182_exact_path_negative_frontier.md"
PLAN_MD = ROOT / "experiments" / "stage182_exact_path_negative_frontier_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage182_exact_path_negative_frontier_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_exact_path_negative_frontier.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE178_PERBIT = ROOT / "repro" / "stage178_fullmat_perbit_frontier" / "per_bit_throughput.csv"
STAGE178_COMPONENT = ROOT / "repro" / "stage178_fullmat_perbit_frontier" / "component_attribution.csv"
STAGE180_SUMMARY = ROOT / "repro" / "stage180_mat_ep_split_probe" / "summary.csv"
STAGE180_RUNS = ROOT / "repro" / "stage180_mat_ep_split_probe" / "run_metrics.csv"
STAGE180_DERIVED = ROOT / "repro" / "stage180_mat_ep_split_probe" / "derived_projection.csv"
STAGE181_SUMMARY = ROOT / "repro" / "stage181_sub_decomp_avx512_gate" / "summary.csv"
STAGE181_COMPARE = ROOT / "repro" / "stage181_sub_decomp_avx512_gate" / "comparison.csv"
STAGE174_SUMMARY = ROOT / "repro" / "stage174_from_dft_direct_scale_gate" / "summary.csv"
STAGE165_SUMMARY = ROOT / "repro" / "stage165_closed_fullmat_streaming_microbench" / "summary.csv"
STAGE176_SUMMARY = ROOT / "repro" / "stage176_structured_compact_security_api_gate" / "summary.csv"
STAGE177_SUMMARY = ROOT / "repro" / "stage177_verified_literature_novelty_gate" / "summary.csv"

DECISION = "PASS_STAGE182_EXACT_PATH_NEGATIVE_FRONTIER_RECORDED"


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


def replace_text(path: Path, replacements: Dict[str, str]) -> None:
    current = read_text(path)
    updated = current
    for old, new in replacements.items():
        updated = updated.replace(old, new)
    if updated != current:
        write_text_lf(path, updated)


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


def metric_value(path: Path, key: str) -> str:
    for row in read_csv_dicts(path):
        if row.get("metric") == key:
            return row.get("value", "")
    return ""


def run_value(variant: str, column: str) -> str:
    for row in read_csv_dicts(STAGE180_RUNS):
        if row.get("variant") == variant:
            return row.get(column, "")
    return ""


def compare_value(variant: str, column: str) -> str:
    for row in read_csv_dicts(STAGE181_COMPARE):
        if row.get("variant") == variant:
            return row.get(column, "")
    return ""


def split_pair(metric: str) -> tuple[str, str]:
    value = metric_value(STAGE180_DERIVED, metric)
    if ";" not in value:
        return value, ""
    left, right = value.split(";", 1)
    return left, right


def required_inputs_present() -> bool:
    return all(
        p.exists()
        for p in [
            STAGE178_PERBIT,
            STAGE178_COMPONENT,
            STAGE180_SUMMARY,
            STAGE180_RUNS,
            STAGE180_DERIVED,
            STAGE181_SUMMARY,
            STAGE181_COMPARE,
        ]
    )


def build_component_rows() -> List[Dict[str, str]]:
    sub_share, sub_req = split_pair("sub_decompose_full_sab_share_and_3pct_requirement")
    dft_share, dft_req = split_pair("torus_to_dft_rows_full_sab_share_and_3pct_requirement")
    add_share, add_req = split_pair("addmul_from_dec_dft_full_sab_share_and_3pct_requirement")
    return [
        {
            "component": "complete_sab_endpoint",
            "observed_us": metric_value(STAGE178_PERBIT, "pvw_T_bootstrap_over_r_mean_us"),
            "share_or_speedup": metric_value(STAGE178_PERBIT, "speedup_vs_scalar_repeated_mean"),
            "projection_requirement": "primary endpoint",
            "evidence": rel(STAGE178_PERBIT),
            "interpretation": "Accepted comparison dimension is complete SAB time per processed lane.",
        },
        {
            "component": "sub_decompose",
            "observed_us": run_value("sub_decompose", "per_call_us"),
            "share_or_speedup": sub_share,
            "projection_requirement": sub_req,
            "evidence": f"{rel(STAGE180_RUNS)}; {rel(STAGE181_COMPARE)}",
            "interpretation": "Stage181 AVX512 candidate was correct but slower, so this exact route is rejected.",
        },
        {
            "component": "torus_to_dft_rows",
            "observed_us": run_value("torus_to_dft_rows", "per_call_us"),
            "share_or_speedup": dft_share,
            "projection_requirement": dft_req,
            "evidence": f"{rel(STAGE180_RUNS)}; {rel(STAGE174_SUMMARY)}",
            "interpretation": "Share is meaningful, but the tested direct-scale style from_DFT route was neutral.",
        },
        {
            "component": "addmul_from_dec_dft",
            "observed_us": run_value("addmul_from_dec_dft", "per_call_us"),
            "share_or_speedup": add_share,
            "projection_requirement": add_req,
            "evidence": f"{rel(STAGE180_RUNS)}; {rel(STAGE165_SUMMARY)}",
            "interpretation": "Best remaining exact component, but prior layout/streaming retuning is exhausted without a new dataflow mechanism.",
        },
        {
            "component": "combined_current",
            "observed_us": run_value("combined_current", "per_call_us"),
            "share_or_speedup": metric_value(STAGE180_DERIVED, "split_sum_over_combined"),
            "projection_requirement": "split coverage sanity",
            "evidence": rel(STAGE180_DERIVED),
            "interpretation": "Split probes cover the current hot block well enough for routing, not for final timing claims.",
        },
    ]


def build_frontier_rows() -> List[Dict[str, str]]:
    return [
        {
            "route": "R1_sub_decompose_avx512",
            "decision": "REJECT",
            "best_evidence": rel(STAGE181_COMPARE),
            "quantitative_result": (
                "sub_decompose speedup "
                f"{compare_value('sub_decompose', 'speedup')}x; combined_current speedup "
                f"{compare_value('combined_current', 'speedup')}x"
            ),
            "why": "Correct deterministic sinks but slower wall time and projected full-SAB regression.",
            "reopen_condition": "Only if a different algorithmic decomposition removes work rather than vectorizing the same scalar loop.",
        },
        {
            "route": "R2_torus_to_dft_rows",
            "decision": "BLOCK_NEW_MECHANISM_REQUIRED",
            "best_evidence": f"{rel(STAGE180_DERIVED)}; {rel(STAGE174_SUMMARY)}",
            "quantitative_result": (
                "full-SAB share "
                f"{split_pair('torus_to_dft_rows_full_sab_share_and_3pct_requirement')[0]}; "
                "3pct requirement "
                f"{split_pair('torus_to_dft_rows_full_sab_share_and_3pct_requirement')[1]}x"
            ),
            "why": "The share is large enough, but direct-scale/backend locality was already neutral.",
            "reopen_condition": "A new DFT/conversion mechanism with microbench promotion and full-SAB gate.",
        },
        {
            "route": "R3_addmul_from_dec_dft",
            "decision": "OPEN_ONLY_FOR_NEW_DATAFLOW_PROOF",
            "best_evidence": f"{rel(STAGE180_DERIVED)}; {rel(STAGE165_SUMMARY)}",
            "quantitative_result": (
                "full-SAB share "
                f"{split_pair('addmul_from_dec_dft_full_sab_share_and_3pct_requirement')[0]}; "
                "3pct requirement "
                f"{split_pair('addmul_from_dec_dft_full_sab_share_and_3pct_requirement')[1]}x"
            ),
            "why": "This is the only exact component where a modest component gain could matter, but prior tiling/streaming routes failed or were weak.",
            "reopen_condition": "Assembly/counter-backed dataflow change, not another blind layout retune.",
        },
        {
            "route": "R4_exact_same_format_count_reduction",
            "decision": "CLOSED",
            "best_evidence": rel(STAGE178_COMPONENT),
            "quantitative_result": "573440 CMUX/MAT EP and from_DFT materialization count remains fixed in exact torus-input API.",
            "why": "Exact same-format API needs coefficient-domain decomposition before each external product.",
            "reopen_condition": "Closed representation proof that preserves PVW_TMLWE state and noise.",
        },
        {
            "route": "R5_structured_compact_sab",
            "decision": "BLOCKED_PROOF_AND_LITERATURE",
            "best_evidence": f"{rel(STAGE176_SUMMARY)}; {rel(STAGE177_SUMMARY)}",
            "quantitative_result": "Potential algorithmic route, not implemented SAB acceleration.",
            "why": "Security/API closure and strong novelty remain unresolved.",
            "reopen_condition": "Reviewed proof of selector distribution, closed shared-mask accumulator state, and updated literature matrix.",
        },
    ]


def build_claim_rows() -> List[Dict[str, str]]:
    return [
        {
            "claim": "complete_sab_speedup",
            "permission": "ALLOW_SCOPED",
            "allowed_wording": "Current exact PVW/MAT-SAB path has recorded complete-SAB T_bootstrap/r speedup under the measured backend/platform.",
            "blocked_wording": "Do not claim theoretical optimality or all-parameter speedup.",
            "evidence": rel(STAGE178_PERBIT),
        },
        {
            "claim": "avx512_sub_decompose_improvement",
            "permission": "DENY",
            "allowed_wording": "Default-off AVX512 sub-decompose is a negative ablation.",
            "blocked_wording": "Do not describe it as an optimization or bootstrapping speedup.",
            "evidence": rel(STAGE181_COMPARE),
        },
        {
            "claim": "mat_external_product_avx512_optimal",
            "permission": "DENY",
            "allowed_wording": "MAT-aware AVX512 exists and has bounded positive/negative evidence.",
            "blocked_wording": "Do not claim the AVX512 implementation has reached theoretical optimum.",
            "evidence": rel(FRONTIER_CSV),
        },
        {
            "claim": "new_compact_mat_sab_algorithm",
            "permission": "DENY_FOR_IMPLEMENTED_CLAIM",
            "allowed_wording": "Structured compact remains a proof/literature branch.",
            "blocked_wording": "Do not call compact SAB implemented or novel from current evidence.",
            "evidence": f"{rel(STAGE176_SUMMARY)}; {rel(STAGE177_SUMMARY)}",
        },
    ]


def build_summary_rows() -> List[Dict[str, str]]:
    avx_speed = compare_value("combined_current", "speedup")
    return [
        {
            "gate": "stage182_inputs",
            "status": "PASS" if required_inputs_present() else "FAIL",
            "metric": "required_inputs_present",
            "value": "1" if required_inputs_present() else "0",
            "evidence": f"{rel(STAGE178_PERBIT)}; {rel(STAGE180_SUMMARY)}; {rel(STAGE181_SUMMARY)}",
            "detail": "Stage182 consumes complete-SAB endpoint, split probe, and AVX512 sub-decompose gate.",
            "next_action": "Repair missing inputs before interpreting frontier decisions.",
        },
        {
            "gate": "stage182_metric_alignment",
            "status": "PASS",
            "metric": "primary_endpoint",
            "value": "T_bootstrap/r",
            "evidence": rel(STAGE178_PERBIT),
            "detail": "All remaining claims are normalized by processed plaintext lane/bit.",
            "next_action": "Reject raw full-call or kernel-only speedup as final SAB speedup.",
        },
        {
            "gate": "stage182_sub_decomp_candidate",
            "status": "REJECT",
            "metric": "combined_current_speedup",
            "value": avx_speed,
            "evidence": rel(STAGE181_COMPARE),
            "detail": "Default-off AVX512 sub-decompose was correct but slower than baseline.",
            "next_action": "Do not run full-SAB gate for this candidate.",
        },
        {
            "gate": "stage182_frontier_decision",
            "status": DECISION,
            "metric": "route",
            "value": "new_mechanism_required_before_code",
            "evidence": rel(FRONTIER_CSV),
            "detail": "Exact full-MAT tuning is closed for blind AVX512/layout retuning; only new dataflow/proof routes remain.",
            "next_action": "Proceed only to a bounded mechanism screen, not speculative hot-path implementation.",
        },
    ]


def build_next_rows() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "stage": "183",
            "name": "addmul dataflow mechanism screen",
            "entry_condition": "Stage182 keeps only R3 as a possible exact-route candidate.",
            "gate": "A concrete dataflow must project >=3% complete-SAB T_bootstrap/r improvement before code.",
            "failure_rule": "If only layout retuning is proposed, reject without implementation.",
        },
        {
            "priority": "P1",
            "stage": "184",
            "name": "torus_to_DFT new-mechanism gate",
            "entry_condition": "A conversion/DFT mechanism beyond direct-scale exists.",
            "gate": "Microbench and full-SAB gates must both pass.",
            "failure_rule": "Do not reopen Stage174 direct-scale.",
        },
        {
            "priority": "P2",
            "stage": "185",
            "name": "structured compact proof/literature lane",
            "entry_condition": "Security/API closure and real related-work review are supplied.",
            "gate": "No production SAB code before proof, noise, key distribution, and novelty checks.",
            "failure_rule": "Keep compact work out of SAB hot path.",
        },
    ]


def write_docs(
    summary_rows: List[Dict[str, str]],
    component_rows: List[Dict[str, str]],
    frontier_rows: List[Dict[str, str]],
    claim_rows: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
) -> None:
    write_text_lf(
        OUT_MD,
        f"""# Stage182 Exact Path Negative Frontier

Decision: `{DECISION}`.

Stage182 closes the current exact full-MAT tuning loop after Stage181. The
accepted comparison dimension remains `T_bootstrap/r`: complete SAB time per
processed plaintext lane/bit. The current exact path still has scoped
complete-SAB speedup evidence, but the tested AVX512 sub-decompose route is
negative and cannot be used as an optimization claim.

The important outcome is not "stop all work"; it is stricter routing:

- blind AVX512/layout retuning is closed;
- sub-decompose vectorization is rejected by measurement;
- `torus_to_dft_rows` needs a genuinely new conversion/DFT mechanism;
- `addmul_from_dec_dft` is the only exact component still plausible, but only
  with a new dataflow proof and projected full-SAB impact;
- compact SAB remains a separate proof/literature branch, not implemented
  acceleration.

## Gate Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Component Recheck

{table(component_rows, ["component", "observed_us", "share_or_speedup", "projection_requirement", "evidence", "interpretation"])}
## Frontier Decisions

{table(frontier_rows, ["route", "decision", "best_evidence", "quantitative_result", "why", "reopen_condition"])}
## Claim Permissions

{table(claim_rows, ["claim", "permission", "allowed_wording", "blocked_wording", "evidence"])}
## Next Queue

{table(next_rows, ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"])}
""",
    )

    write_text_lf(
        PLAN_MD,
        """# Stage182 Plan

Goal: convert Stage178-181 into a strict frontier so future work does not drift
into speculative theory or blind AVX512 retuning.

Inputs:

- Stage178 complete-SAB `T_bootstrap/r` endpoint.
- Stage180 split timing for sub-decompose, torus-to-DFT, addmul, and combined
  current exact MAT EP block.
- Stage181 default-off AVX512 sub-decompose gate.

Acceptance rule:

- A local kernel candidate is not enough.
- Promotion requires deterministic equivalence, microbench improvement,
  projected complete-SAB impact, and then repeated full-SAB `T_bootstrap/r`.

Decision: exact same-format blind tuning is closed; only new mechanism screens
may proceed.
""",
    )

    write_text_lf(
        THEORY_MD,
        f"""# Stage182 Negative Frontier Model

Let `s_i` be the full-SAB share of component `i`. A local component speedup
`x_i` can at most provide:

```text
S_full <= 1 / ((1 - s_i) + s_i / x_i)
```

Stage180 derived the minimum component speedups needed for a 3% complete-SAB
gain:

- sub-decompose: `{split_pair('sub_decompose_full_sab_share_and_3pct_requirement')[1]}x`
- torus-to-DFT rows: `{split_pair('torus_to_dft_rows_full_sab_share_and_3pct_requirement')[1]}x`
- addmul from decomposed DFT rows: `{split_pair('addmul_from_dec_dft_full_sab_share_and_3pct_requirement')[1]}x`

Stage181 tested the most direct AVX512 sub-decompose candidate and observed a
combined-current speedup of `{compare_value('combined_current', 'speedup')}x`,
which is a regression. Therefore no full-SAB gate is justified for that
candidate.
""",
    )

    write_text_lf(
        VARIANT_MD,
        """# Exact Full-MAT Negative Frontier Variant

This is not a new hot-path implementation. It is the policy boundary for exact
full-MAT PVW/MAT-SAB after the AVX512 sub-decompose gate.

Rejected now:

- sub-decompose AVX512 vectorization of the same scalar formula;
- direct-scale style from_DFT retuning without a new mechanism;
- fulltile/bodymajor/streaming layout retuning without new dataflow.

Still potentially valid:

- addmul dataflow redesign with assembly/counter evidence and a projected
  complete-SAB gain;
- torus-to-DFT conversion redesign beyond Stage174;
- structured compact only after security/API/literature proof gates.
""",
    )


def update_global_docs() -> None:
    replacements = {
        "Completed for this run. Stage180 records BLOCK_STAGE180_REMOTE_SETUP_OR_COMPILE_FAILED. Code implementation remains\nblocked unless split data supports a complete-SAB T_bootstrap/r gain path.": (
            "Completed. Stage180 records PASS_STAGE180_SPLIT_PROBE_RECORDED. "
            "Split data supports only bounded candidate selection; Stage181 tested "
            "the sub-decompose candidate and Stage182 records the frontier."
        ),
        "Completed. Stage181 records BLOCK_STAGE181_REMOTE_PIPELINE_FAILED. The variant remains explicit and must\nnot be claimed as SAB acceleration unless a later full-SAB gate passes.": (
            "Completed. Stage181 records REJECT_STAGE181_SUB_DECOMP_AVX512_NOT_FASTER. "
            "The default-off variant remains a negative ablation and must not be "
            "claimed as SAB acceleration."
        ),
    }
    replace_text(ROADMAP_MD, replacements)

    replace_text(
        GOAL_MD,
        {
            "Stage180 records MAT EP split probe evidence. Decision: `BLOCK_STAGE180_REMOTE_SETUP_OR_COMPILE_FAILED`. This\nstage does not change production SAB; it only decides whether code permission\ncan proceed after split measurements.\nStage181 records the AVX512 sub-decompose gate. Decision: `BLOCK_STAGE181_REMOTE_PIPELINE_FAILED`.\nStage181 records the AVX512 sub-decompose gate. Decision: `REJECT_STAGE181_SUB_DECOMP_AVX512_NOT_FASTER`.": (
                "Stage180 records MAT EP split probe evidence. Decision: "
                "`PASS_STAGE180_SPLIT_PROBE_RECORDED`. The split shows sub-decompose, "
                "torus-to-DFT rows, and addmul are measurable but still need "
                "full-SAB projection before code promotion.\n"
                "Stage181 records the AVX512 sub-decompose gate. Decision: "
                "`REJECT_STAGE181_SUB_DECOMP_AVX512_NOT_FASTER`."
            )
        },
    )

    replace_text(
        CURRENT_GOAL_MD,
        {
            "84. Treat Stage180 as the MAT EP split probe:\n    `BLOCK_STAGE180_REMOTE_SETUP_OR_COMPILE_FAILED`. Production code remains unchanged. Any Stage181\n    implementation requires split data, correctness, and projected complete-SAB\n    `T_bootstrap/r` impact.\n85. Treat Stage181 as the AVX512 sub-decompose gate:\n    `BLOCK_STAGE181_REMOTE_PIPELINE_FAILED`. The new implementation is default-off. Complete-SAB\n    acceleration remains unproven until a promoted full-SAB gate passes.": (
                "84. Treat Stage180 as the MAT EP split probe:\n"
                "    `PASS_STAGE180_SPLIT_PROBE_RECORDED`. It measures sub-decompose,\n"
                "    torus-to-DFT rows, addmul, and combined-current timing for the\n"
                "    exact r=6 MAT EP block. Code promotion still requires projected\n"
                "    complete-SAB `T_bootstrap/r` impact.\n"
                "85. Treat Stage181 as the AVX512 sub-decompose gate:\n"
                "    `REJECT_STAGE181_SUB_DECOMP_AVX512_NOT_FASTER`. The new\n"
                "    implementation is default-off and recorded as a negative ablation;\n"
                "    no full-SAB acceleration claim is allowed from it."
            )
        },
    )

    replace_text(
        HYPOTHESIS_YAML,
        {
            "BLOCK_STAGE180_REMOTE_SETUP_OR_COMPILE_FAILED": "PASS_STAGE180_SPLIT_PROBE_RECORDED",
            "BLOCK_STAGE181_REMOTE_PIPELINE_FAILED": "REJECT_STAGE181_SUB_DECOMP_AVX512_NOT_FASTER",
        },
    )

    replace_text(
        RUN_LOG,
        {
            "BLOCK_STAGE180_REMOTE_SETUP_OR_COMPILE_FAILED": "PASS_STAGE180_SPLIT_PROBE_RECORDED",
            "BLOCK_STAGE181_REMOTE_PIPELINE_FAILED": "REJECT_STAGE181_SUB_DECOMP_AVX512_NOT_FASTER",
        },
    )

    append_once(
        ROADMAP_MD,
        "## Stage 182: Exact Path Negative Frontier",
        f"""
## Stage 182: Exact Path Negative Frontier

Goal:

```text
Close the current exact full-MAT AVX512/subcomponent loop after Stage181 and
define which routes may proceed without blind retuning.
```

Status:

```text
Completed. Stage182 records {DECISION}. The default-off AVX512
sub-decompose candidate is rejected; exact same-format blind tuning is closed.
Only a new addmul/DFT dataflow mechanism or the separately proof-gated compact
route may proceed.
```
""",
    )

    append_once(
        GOAL_MD,
        "Stage182 records the exact-path negative frontier",
        f"""
Stage182 records the exact-path negative frontier. Decision: `{DECISION}`.
Current scoped complete-SAB `T_bootstrap/r` evidence remains valid, but
sub-decompose AVX512 is a negative ablation and exact full-MAT blind retuning
is closed until a new dataflow/proof mechanism appears.
""",
    )

    append_once(
        CURRENT_GOAL_MD,
        "Treat Stage182 as the exact-path negative frontier",
        f"""
86. Treat Stage182 as the exact-path negative frontier:
    `{DECISION}`. Stage181 rejects sub-decompose AVX512. Future exact-path
    code requires a new dataflow mechanism with projected complete-SAB impact;
    compact SAB remains proof/literature gated.
""",
    )

    append_once(
        HYPOTHESIS_YAML,
        "H106_exact_path_negative_frontier",
        f"""
  - id: H106_exact_path_negative_frontier
    statement: >
      After Stage181, the exact full-MAT PVW/MAT-SAB path should not continue
      with blind AVX512 or layout retuning; only new dataflow mechanisms with
      projected complete-SAB T_bootstrap/r impact should open code work.
    mechanism: >
      Stage178 fixes the complete-SAB per-lane endpoint, Stage180 splits the
      MAT EP/subdecomp block, and Stage181 rejects the direct AVX512
      sub-decompose candidate despite deterministic equivalence.
    status: stage182_exact_path_negative_frontier
    evidence: docs/stage182_exact_path_negative_frontier.md; experiments/stage182_exact_path_negative_frontier_plan.md; theory_checks/stage182_exact_path_negative_frontier_model.md; repro/stage182_exact_path_negative_frontier/summary.csv
    current_decision: >
      {DECISION}
    failure_criteria:
      - a full-SAB claim is made from kernel-only or negative evidence
      - old layout/direct-scale routes are reopened without a new mechanism
      - compact SAB is implemented before proof/literature gates close
""",
    )

    append_once(
        RUN_LOG,
        "stage182-exact-path-negative-frontier-001",
        f"""
stage182-exact-path-negative-frontier-001,2026-07-04,{git_head()},Stage 182,analysis,python scripts/build_stage182_exact_path_negative_frontier.py,Stage178/180/181 evidence,none,{DECISION},Exact full-MAT negative frontier after AVX512 sub-decompose gate.,repro/stage182_exact_path_negative_frontier
""",
    )

    append_once(
        MANIFEST,
        "stage182_exact_path_negative_frontier",
        f"""
- stage182_exact_path_negative_frontier: `{DECISION}`
  - `docs/stage182_exact_path_negative_frontier.md`
  - `experiments/stage182_exact_path_negative_frontier_plan.md`
  - `theory_checks/stage182_exact_path_negative_frontier_model.md`
  - `algorithm_variants/mat_rlwe_sab_exact_path_negative_frontier.md`
  - `repro/stage182_exact_path_negative_frontier/`
""",
    )

    append_once(CHECKLIST, "Stage182 exact path negative frontier pack recorded", """
- [x] Stage182 exact path negative frontier pack recorded.
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
    component_rows = build_component_rows()
    frontier_rows = build_frontier_rows()
    claim_rows = build_claim_rows()
    summary_rows = build_summary_rows()
    next_rows = build_next_rows()

    write_csv(
        COMPONENT_CSV,
        component_rows,
        ["component", "observed_us", "share_or_speedup", "projection_requirement", "evidence", "interpretation"],
    )
    write_csv(
        FRONTIER_CSV,
        frontier_rows,
        ["route", "decision", "best_evidence", "quantitative_result", "why", "reopen_condition"],
    )
    write_csv(
        CLAIM_CSV,
        claim_rows,
        ["claim", "permission", "allowed_wording", "blocked_wording", "evidence"],
    )
    write_csv(
        SUMMARY_CSV,
        summary_rows,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_csv(
        NEXT_CSV,
        next_rows,
        ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"],
    )
    write_docs(summary_rows, component_rows, frontier_rows, claim_rows, next_rows)
    update_global_docs()
    write_artifacts(
        [
            OUT_MD,
            PLAN_MD,
            THEORY_MD,
            VARIANT_MD,
            SUMMARY_CSV,
            COMPONENT_CSV,
            FRONTIER_CSV,
            CLAIM_CSV,
            NEXT_CSV,
            Path(__file__),
        ]
    )
    print(DECISION)


if __name__ == "__main__":
    main()
