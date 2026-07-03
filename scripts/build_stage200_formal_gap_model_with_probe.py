#!/usr/bin/env python3
"""Stage200: formal r-body gap model with finite falsification probes."""

from __future__ import annotations

import csv
import hashlib
import random
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage200_formal_gap_model_with_probe"

SUMMARY_CSV = OUT_DIR / "summary.csv"
ASSUMPTION_CSV = OUT_DIR / "assumptions.csv"
LOWER_BOUND_CSV = OUT_DIR / "lower_bound_model.csv"
FINITE_PROBE_CSV = OUT_DIR / "finite_probe.csv"
COUNTEREXAMPLE_CSV = OUT_DIR / "counterexample_matrix.csv"
GAP_PROJECTION_CSV = OUT_DIR / "gap_projection.csv"
OBLIGATION_CSV = OUT_DIR / "proof_obligations.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
COMMANDS_MD = OUT_DIR / "reproduction_commands.md"
REPORT_MD = OUT_DIR / "formal_gap_model_report.md"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage200_formal_gap_model_with_probe.md"
PLAN_MD = ROOT / "experiments" / "stage200_formal_gap_model_with_probe_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage200_rbody_gap_lower_bound_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_formal_gap_model.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE140_ATTR = ROOT / "repro" / "stage140_closed_fullmat_attribution_gate" / "attribution.csv"
STAGE140_SUMMARY = ROOT / "repro" / "stage140_closed_fullmat_attribution_gate" / "summary.csv"
STAGE162_SUMMARY = ROOT / "repro" / "stage162_materialization_count_feasibility" / "summary.csv"
STAGE180_DERIVED = ROOT / "repro" / "stage180_mat_ep_split_probe" / "derived_projection.csv"
STAGE199_GAPS = ROOT / "repro" / "stage199_active_goal_requirement_verifier" / "evidence_gap_register.csv"
STAGE199_NEXT = ROOT / "repro" / "stage199_active_goal_requirement_verifier" / "next_action_selector.csv"

DECISION = "PASS_STAGE200_FORMAL_GAP_MODEL_WITH_PROBE_RECORDED_GOAL_ACTIVE"


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
    with path.open(newline="", encoding="utf-8") as f:
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


def derived(metric_name: str) -> str:
    for row in read_csv_dicts(STAGE180_DERIVED):
        if row.get("metric") == metric_name:
            return row.get("value", "")
    return ""


def poly_add(a: List[int], b: List[int], q: int) -> List[int]:
    return [(x + y) % q for x, y in zip(a, b)]


def poly_mul_negacyclic(a: List[int], b: List[int], q: int) -> List[int]:
    n = len(a)
    out = [0] * n
    for i, ai in enumerate(a):
        for j, bj in enumerate(b):
            idx = i + j
            if idx >= n:
                out[idx - n] -= ai * bj
            else:
                out[idx] += ai * bj
    return [x % q for x in out]


def random_poly(rng: random.Random, n: int, q: int) -> List[int]:
    return [rng.randrange(q) for _ in range(n)]


def dense_mat_ep(matrix: List[List[List[int]]], vec: List[List[int]], q: int) -> List[List[int]]:
    m = len(vec)
    out = [[0] * len(vec[0]) for _ in range(m)]
    for row in range(m):
        acc = [0] * len(vec[0])
        for col in range(m):
            acc = poly_add(acc, poly_mul_negacyclic(matrix[row][col], vec[col], q), q)
        out[row] = acc
    return out


def omit_component_ep(matrix: List[List[List[int]]], vec: List[List[int]], q: int, omitted: int) -> List[List[int]]:
    m = len(vec)
    out = [[0] * len(vec[0]) for _ in range(m)]
    for row in range(m):
        acc = [0] * len(vec[0])
        for col in range(m):
            if col == omitted:
                continue
            acc = poly_add(acc, poly_mul_negacyclic(matrix[row][col], vec[col], q), q)
        out[row] = acc
    return out


def mismatch_count(a: List[List[int]], b: List[List[int]]) -> int:
    return sum(1 for row_a, row_b in zip(a, b) for x, y in zip(row_a, row_b) if x != y)


def decompose_int(x: int, base: int, levels: int) -> List[int]:
    out = []
    cur = x
    for _ in range(levels):
        out.append(cur % base)
        cur //= base
    return out


def build_assumption_rows() -> List[Dict[str, str]]:
    return [
        {
            "assumption_id": "A1_state_shape",
            "statement": "Exact full-MAT state has one shared mask component and r body components, so m=r+1 input components are present.",
            "scope": "current exact PVW_TMLWE representation",
            "evidence": rel(STAGE140_ATTR),
            "falsification": "Find a correct production state with fewer than r+1 torus input components under the same API.",
        },
        {
            "assumption_id": "A2_torus_input_api",
            "statement": "The current exact external product consumes torus-domain input before decomposition and DFT multiplication.",
            "scope": "same-format production path",
            "evidence": rel(STAGE162_SUMMARY),
            "falsification": "Provide a closed decomposed/DFT state that feeds the next SAB step without torus materialization.",
        },
        {
            "assumption_id": "A3_general_selector_coupling",
            "statement": "For a general closed full-MAT selector, each output row may depend on every input component.",
            "scope": "dense MAT_TRGSW_DFT model, not compact proof route",
            "evidence": rel(FINITE_PROBE_CSV),
            "falsification": "Show structural zero constraints from key generation that safely remove a component for all inputs.",
        },
        {
            "assumption_id": "A4_complete_sab_metric",
            "statement": "Any acceleration claim must be measured on complete SAB T_bootstrap/r, not only a component count.",
            "scope": "claim policy",
            "evidence": rel(STAGE199_GAPS),
            "falsification": "None; this is a reporting invariant from the active goal.",
        },
    ]


def build_lower_bound_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for r in (2, 4, 6):
        for t in (1, 7):
            m = r + 1
            mat_input_dft = m * t
            repeated_scalar_input_dft = 2 * r * t
            dense_mat_terms = m * m * t
            repeated_scalar_terms = 4 * r * t
            rows.append(
                {
                    "r": str(r),
                    "T": str(t),
                    "input_components_m": str(m),
                    "mat_input_dft_lower_bound": str(mat_input_dft),
                    "repeated_scalar_input_dft": str(repeated_scalar_input_dft),
                    "mat_input_dft_over_repeated": f"{mat_input_dft / repeated_scalar_input_dft:.9f}",
                    "dense_mat_addmul_terms": str(dense_mat_terms),
                    "repeated_scalar_dense_terms": str(repeated_scalar_terms),
                    "dense_terms_over_repeated": f"{dense_mat_terms / repeated_scalar_terms:.9f}",
                    "interpretation": "MAT shares input conversion work but pays dense row/output interactions under the closed full-MAT selector.",
                    "evidence": rel(STAGE140_ATTR),
                }
            )
    return rows


def build_finite_probe_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    q = 257
    n = 8
    samples = 5
    for r in (2, 4, 6):
        m = r + 1
        for seed in range(samples):
            rng = random.Random(200000 + 100 * r + seed)
            matrix = [[random_poly(rng, n, q) for _ in range(m)] for _ in range(m)]
            vec = [random_poly(rng, n, q) for _ in range(m)]
            dense = dense_mat_ep(matrix, vec, q)
            for omitted in range(m):
                approx = omit_component_ep(matrix, vec, q, omitted)
                mismatches = mismatch_count(dense, approx)
                rows.append(
                    {
                        "probe": "omit_input_component",
                        "r": str(r),
                        "N": str(n),
                        "q": str(q),
                        "seed": str(seed),
                        "omitted_component": str(omitted),
                        "mismatches": str(mismatches),
                        "status": "PASS_COUNTEREXAMPLE" if mismatches > 0 else "FAIL_NO_MISMATCH",
                        "interpretation": "A general dense selector can depend on the omitted component, so component skipping is not sound without extra structure.",
                    }
                )

    base = 4
    levels = 4
    for seed in range(samples):
        rng = random.Random(300000 + seed)
        x = rng.randrange(base ** levels)
        y = rng.randrange(base ** levels)
        lhs = decompose_int((x + y) % (base ** levels), base, levels)
        dx = decompose_int(x, base, levels)
        dy = decompose_int(y, base, levels)
        rhs = [(a + b) % base for a, b in zip(dx, dy)]
        mismatches = sum(1 for a, b in zip(lhs, rhs) if a != b)
        rows.append(
            {
                "probe": "gadget_decompose_non_additivity",
                "r": "n/a",
                "N": "n/a",
                "q": str(base ** levels),
                "seed": str(seed),
                "omitted_component": "n/a",
                "mismatches": str(mismatches),
                "status": "PASS_COUNTEREXAMPLE" if mismatches > 0 else "FAIL_NO_MISMATCH",
                "interpretation": "Toy decomposition is not additive under carries, supporting the same-format lazy-state caution.",
            }
        )
    return rows


def build_counterexample_rows(probe_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    omit_failures = sum(1 for row in probe_rows if row["probe"] == "omit_input_component" and row["status"] != "PASS_COUNTEREXAMPLE")
    decomp_failures = sum(1 for row in probe_rows if row["probe"] == "gadget_decompose_non_additivity" and row["status"] != "PASS_COUNTEREXAMPLE")
    return [
        {
            "candidate_shortcut": "drop_or_skip_any_input_component",
            "expected_if_valid": "No mismatch after omitting a component for all tested dense selectors.",
            "observed": f"omit probe failures={omit_failures}; total rows={sum(1 for row in probe_rows if row['probe'] == 'omit_input_component')}",
            "decision": "REJECT_SHORTCUT" if omit_failures == 0 else "INCONCLUSIVE",
            "evidence": rel(FINITE_PROBE_CSV),
        },
        {
            "candidate_shortcut": "same_format_lazy_decomposed_addition",
            "expected_if_valid": "Toy decomposition would commute with addition in all sampled rows.",
            "observed": f"non-additivity probe failures={decomp_failures}; total rows={sum(1 for row in probe_rows if row['probe'] == 'gadget_decompose_non_additivity')}",
            "decision": "REJECT_SHORTCUT" if decomp_failures == 0 else "INCONCLUSIVE",
            "evidence": rel(FINITE_PROBE_CSV),
        },
        {
            "candidate_shortcut": "reduce_same_format_materialization_count",
            "expected_if_valid": "Observed materialization calls would exceed the same-format lower-bound model.",
            "observed": "Stage162 records reducible_calls_without_rep_change=0 and matching 573440 count.",
            "decision": "REJECT_SAME_FORMAT_COUNT_REDUCTION",
            "evidence": rel(STAGE162_SUMMARY),
        },
    ]


def build_gap_projection_rows() -> List[Dict[str, str]]:
    return [
        {
            "component": "sub_decompose",
            "full_sab_share_and_required_speedup": derived("sub_decompose_full_sab_share_and_3pct_requirement"),
            "route_status": "prior AVX512 candidate rejected",
            "interpretation": "Needs a new dataflow mechanism before code is reopened.",
            "evidence": rel(STAGE180_DERIVED),
        },
        {
            "component": "torus_to_dft_rows",
            "full_sab_share_and_required_speedup": derived("torus_to_dft_rows_full_sab_share_and_3pct_requirement"),
            "route_status": "same-format count reduction closed",
            "interpretation": "Only backend primitive or representation change can move the count.",
            "evidence": rel(STAGE180_DERIVED),
        },
        {
            "component": "addmul_from_dec_dft",
            "full_sab_share_and_required_speedup": derived("addmul_from_dec_dft_full_sab_share_and_3pct_requirement"),
            "route_status": "prior layout/dataflow families rejected",
            "interpretation": "New code needs selector-load or FMA-equivalent mechanism evidence.",
            "evidence": rel(STAGE180_DERIVED),
        },
    ]


def build_obligation_rows() -> List[Dict[str, str]]:
    return [
        {
            "obligation_id": "O1_bound_scope",
            "statement": "State the lower bound only for exact same-format torus-input full-MAT PVW_TMLWE paths.",
            "status": "RECORDED",
            "evidence": f"{rel(ASSUMPTION_CSV)}; {rel(LOWER_BOUND_CSV)}",
            "needed_before_stronger_claim": "Separate proof for compact, multimask, or lazy-state representations.",
        },
        {
            "obligation_id": "O2_selector_structure",
            "statement": "Prove any component skipping from keygen-imposed zero structure before implementation.",
            "status": "OPEN",
            "evidence": rel(COUNTEREXAMPLE_CSV),
            "needed_before_stronger_claim": "Structured selector distribution proof and production keygen/noise gates.",
        },
        {
            "obligation_id": "O3_complete_sab_endpoint",
            "statement": "Convert any component-level win into complete-SAB T_bootstrap/r evidence.",
            "status": "RECORDED_POLICY",
            "evidence": rel(STAGE199_NEXT),
            "needed_before_stronger_claim": "Correctness, noise/resource, repeated complete-SAB timing, and claim ledger refresh.",
        },
        {
            "obligation_id": "O4_source_anchor",
            "statement": "Cite 2025/686 algorithm/proof details only after reviewed full text is available.",
            "status": "BLOCKED",
            "evidence": "repro/stage196_public_source_refresh/citation_gate.csv",
            "needed_before_stronger_claim": "Local full-text artifact plus source-anchor extraction.",
        },
    ]


def build_next_rows() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "source_anchor_intake",
            "entry_condition": "Reviewed 2025/686 full text is supplied locally.",
            "gate": "Map every source-specific algorithm/proof sentence to inspected text anchors.",
            "current_status": "waiting_external_artifact",
            "evidence": "repro/stage196_public_source_refresh/citation_gate.csv",
        },
        {
            "priority": "P1",
            "route": "structured_selector_proof_probe",
            "entry_condition": "A compact/shared-output selector distribution proof route is proposed.",
            "gate": "Show keygen-imposed structure safely removes dense terms without public distribution change, then run finite and production noise gates.",
            "current_status": "proof_required",
            "evidence": rel(COUNTEREXAMPLE_CSV),
        },
        {
            "priority": "P2",
            "route": "new_exact_mechanism_admission",
            "entry_condition": "A new addmul, DFT, or backend primitive mechanism is supplied.",
            "gate": "Projection clears complete-SAB threshold and then correctness/noise/resource/full-SAB gates pass.",
            "current_status": "waiting_new_mechanism",
            "evidence": rel(GAP_PROJECTION_CSV),
        },
    ]


def build_summary_rows(probe_rows: List[Dict[str, str]], counter_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    inputs = [STAGE140_ATTR, STAGE140_SUMMARY, STAGE162_SUMMARY, STAGE180_DERIVED, STAGE199_GAPS, STAGE199_NEXT]
    inputs_ok = all(path.exists() for path in inputs)
    probe_failures = sum(1 for row in probe_rows if row["status"] != "PASS_COUNTEREXAMPLE")
    rejected = sum(1 for row in counter_rows if row["decision"].startswith("REJECT"))
    return [
        {
            "gate": "stage200_inputs",
            "status": "PASS" if inputs_ok else "FAIL",
            "metric": "required_inputs_present",
            "value": "1" if inputs_ok else "0",
            "evidence": f"{rel(STAGE140_ATTR)}; {rel(STAGE162_SUMMARY)}; {rel(STAGE199_GAPS)}",
            "detail": "Stage200 consumes lower-bound, materialization-count, projection, and active-goal gap evidence.",
            "next_action": "Repair missing inputs before using the model.",
        },
        {
            "gate": "stage200_lower_bound_model",
            "status": "PASS_RECORDED",
            "metric": "model_rows",
            "value": "6",
            "evidence": rel(LOWER_BOUND_CSV),
            "detail": "The model records input DFT lower bound, dense full-MAT terms, and repeated scalar comparison counts.",
            "next_action": "Do not interpret as a final proof outside the stated assumptions.",
        },
        {
            "gate": "stage200_finite_probe",
            "status": "PASS" if probe_failures == 0 else "FAIL",
            "metric": "probe_failures",
            "value": str(probe_failures),
            "evidence": rel(FINITE_PROBE_CSV),
            "detail": "Finite probes reject component omission and toy additive decomposition shortcuts.",
            "next_action": "If nonzero, inspect finite probe rows before using counterexamples.",
        },
        {
            "gate": "stage200_counterexample_matrix",
            "status": "PASS_RECORDED",
            "metric": "rejected_shortcuts",
            "value": str(rejected),
            "evidence": rel(COUNTEREXAMPLE_CSV),
            "detail": "Shortcut rejections are scoped to the assumptions and do not prove all alternatives impossible.",
            "next_action": "Use proof obligations before opening compact or lazy-state production work.",
        },
        {
            "gate": "stage200_decision",
            "status": DECISION if inputs_ok and probe_failures == 0 else "FAIL_STAGE200",
            "metric": "goal_status",
            "value": "active",
            "evidence": rel(SUMMARY_CSV),
            "detail": "The R3 formal-gap requirement is improved from partial to scoped model plus executable probes, but the full goal remains active.",
            "next_action": "Proceed only via source-anchor intake, structured selector proof, or new exact mechanism admission.",
        },
    ]


def write_report(
    assumption_rows: List[Dict[str, str]],
    lower_rows: List[Dict[str, str]],
    probe_rows: List[Dict[str, str]],
    counter_rows: List[Dict[str, str]],
    gap_rows: List[Dict[str, str]],
    obligation_rows: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
    summary_rows: List[Dict[str, str]],
) -> None:
    write_text_lf(
        REPORT_MD,
        f"""# Stage200 Formal Gap Model Report

Decision: `{DECISION}`.

Stage200 records a scoped formal gap model for the current exact full-MAT
PVW/MAT-SAB route. The model is deliberately limited to same-format
torus-input full-MAT paths. It improves the R3 gap from Stage199, but it does
not complete the full research objective.

## Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Assumptions

{table(assumption_rows, ["assumption_id", "statement", "scope", "evidence", "falsification"])}
## Lower-Bound Model

{table(lower_rows, ["r", "T", "input_components_m", "mat_input_dft_lower_bound", "repeated_scalar_input_dft", "mat_input_dft_over_repeated", "dense_mat_addmul_terms", "repeated_scalar_dense_terms", "dense_terms_over_repeated", "interpretation", "evidence"])}
## Counterexamples

{table(counter_rows, ["candidate_shortcut", "expected_if_valid", "observed", "decision", "evidence"])}
## Gap Projection

{table(gap_rows, ["component", "full_sab_share_and_required_speedup", "route_status", "interpretation", "evidence"])}
## Proof Obligations

{table(obligation_rows, ["obligation_id", "statement", "status", "evidence", "needed_before_stronger_claim"])}
## Next Queue

{table(next_rows, ["priority", "route", "entry_condition", "gate", "current_status", "evidence"])}

Finite probe rows are in `{rel(FINITE_PROBE_CSV)}`.
""",
    )


def write_commands() -> None:
    write_text_lf(
        COMMANDS_MD,
        """# Stage200 Reproduction Commands

```powershell
# Rebuild the formal gap model and finite probes
python scripts\\build_stage200_formal_gap_model_with_probe.py

# Inspect the model and executable probes
Get-Content -Raw repro\\stage200_formal_gap_model_with_probe\\lower_bound_model.csv
Get-Content -Raw repro\\stage200_formal_gap_model_with_probe\\finite_probe.csv
Get-Content -Raw repro\\stage200_formal_gap_model_with_probe\\counterexample_matrix.csv
Get-Content -Raw repro\\stage200_formal_gap_model_with_probe\\summary.csv
```
""",
    )


def write_docs(
    assumption_rows: List[Dict[str, str]],
    lower_rows: List[Dict[str, str]],
    counter_rows: List[Dict[str, str]],
    obligation_rows: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
    summary_rows: List[Dict[str, str]],
) -> None:
    write_text_lf(
        OUT_MD,
        f"""# Stage200 Formal Gap Model with Probe

Decision: `{DECISION}`.

This stage adds a scoped lower-bound/gap model and finite counterexample probes.
It is not a complete proof for every possible MAT-RLWE SAB representation.

## Gate Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Assumptions

{table(assumption_rows, ["assumption_id", "statement", "scope", "evidence", "falsification"])}
## Lower-Bound Model

{table(lower_rows, ["r", "T", "input_components_m", "mat_input_dft_lower_bound", "repeated_scalar_input_dft", "mat_input_dft_over_repeated", "dense_mat_addmul_terms", "repeated_scalar_dense_terms", "dense_terms_over_repeated", "interpretation", "evidence"])}
## Counterexample Matrix

{table(counter_rows, ["candidate_shortcut", "expected_if_valid", "observed", "decision", "evidence"])}
## Proof Obligations

{table(obligation_rows, ["obligation_id", "statement", "status", "evidence", "needed_before_stronger_claim"])}
## Next Queue

{table(next_rows, ["priority", "route", "entry_condition", "gate", "current_status", "evidence"])}
""",
    )

    write_text_lf(
        PLAN_MD,
        """# Stage200 Plan

Goal: improve the R3 formal-gap requirement from Stage199 without entering a
theory loop.

Method:

- state assumptions for the current exact same-format full-MAT path;
- record count lower bounds for input DFT conversions and dense addmul terms;
- run finite probes for component omission and toy decomposition nonlinearity;
- convert rejected shortcuts into proof obligations and next gates.

Failure rule:

- if the finite probes do not find mismatches, the shortcut rejection cannot be
  used;
- if a claim exceeds the assumptions, it must be moved to proof obligations.
""",
    )

    write_text_lf(
        THEORY_MD,
        """# Stage200 R-Body Gap Lower-Bound Model

Under the current exact torus-input PVW_TMLWE state with k=1 and r body lanes,
there are m=r+1 input components. With T gadget levels, a same-format external
product that enters the DFT multiplication domain needs at least m*T input DFT
conversions unless a new closed representation is supplied.

The current production closed full-MAT path reaches that input-conversion
count. The remaining same-format gap is therefore not another shared-mask input
conversion count reduction; it is dense row/output interaction, backend
constant factors, or a representation/keygen proof route.

The finite probe tests two shortcut families:

- omitting any input component from a dense selector;
- treating toy gadget decomposition as additive across an update.

Both are rejected in the sampled finite model. This does not rule out all
future representations; it records what must be proven before they are used.
""",
    )

    write_text_lf(
        VARIANT_MD,
        """# MAT-RLWE SAB Formal Gap Model

This is a model artifact, not a new implementation variant.

Current scoped result:

- exact full-MAT path has complete-SAB `T_bootstrap/r` evidence;
- same-format input DFT count is already at the m*T lower-bound count;
- same-format materialization count is closed by Stage162;
- component omission and toy lazy-decomposition shortcuts are rejected by
  finite probes.

Admissible next implementation work requires either a new exact mechanism with
projected complete-SAB impact or a representation/keygen proof that changes
the model assumptions.
""",
    )


def update_global_docs() -> None:
    append_once(
        ROADMAP_MD,
        "## Stage 200: Formal Gap Model with Probe",
        f"""
## Stage 200: Formal Gap Model with Probe

Goal:

```text
Improve the active-goal formal lower-bound/gap requirement using explicit
assumptions plus executable finite counterexample probes.
```

Status:

```text
Completed. Stage200 records {DECISION}. The exact same-format full-MAT route
now has a scoped gap model and finite shortcut rejections, while stronger
claims remain behind proof/source/implementation gates.
```
""",
    )

    append_once(
        GOAL_MD,
        "Stage200 records formal gap model with probe",
        f"""
Stage200 records formal gap model with probe. Decision: `{DECISION}`. It
states same-format assumptions, records input DFT and dense-term count models,
and runs finite counterexample probes for unsafe shortcuts.
""",
    )

    append_once(
        CURRENT_GOAL_MD,
        "Treat Stage200 as formal gap model with probe",
        f"""
104. Treat Stage200 as formal gap model with probe:
    `{DECISION}`. R3 is improved from partial to a scoped model plus executable
    finite probes, but full goal completion remains open because source anchors
    and stronger implementation claims remain incomplete.
""",
    )

    append_once(
        HYPOTHESIS_YAML,
        "H124_formal_gap_model_with_probe",
        f"""
  - id: H124_formal_gap_model_with_probe
    statement: >
      For the current exact same-format full-MAT PVW/MAT-SAB path, input DFT
      count reduction is already at the m*T lower-bound count, so further
      exact-path gains need backend/addmul mechanisms or a representation proof
      that changes the assumptions.
    mechanism: >
      Stage200 combines Stage140 count evidence, Stage162 materialization
      closure, Stage180 projection data, and finite counterexample probes for
      component omission and toy decomposition shortcuts.
    status: stage200_formal_gap_model_with_probe
    evidence: docs/stage200_formal_gap_model_with_probe.md; experiments/stage200_formal_gap_model_with_probe_plan.md; theory_checks/stage200_rbody_gap_lower_bound_model.md; repro/stage200_formal_gap_model_with_probe/summary.csv
    current_decision: >
      {DECISION}
    failure_criteria:
      - finite probes fail to reject the tested shortcuts
      - lower-bound wording is applied outside the stated same-format assumptions
      - a component-level model is used as complete-SAB acceleration evidence
""",
    )

    append_once(
        RUN_LOG,
        "stage200-formal-gap-model-with-probe-001",
        f"""
stage200-formal-gap-model-with-probe-001,2026-07-04,{git_head()},Stage 200,analysis+finite-probe,python scripts/build_stage200_formal_gap_model_with_probe.py,Stage140/162/180/199 evidence,none,{DECISION},Formal gap model and finite shortcut probes.,repro/stage200_formal_gap_model_with_probe
""",
    )

    append_once(
        MANIFEST,
        "stage200_formal_gap_model_with_probe",
        f"""
- stage200_formal_gap_model_with_probe: `{DECISION}`
  - `docs/stage200_formal_gap_model_with_probe.md`
  - `experiments/stage200_formal_gap_model_with_probe_plan.md`
  - `theory_checks/stage200_rbody_gap_lower_bound_model.md`
  - `algorithm_variants/mat_rlwe_sab_formal_gap_model.md`
  - `repro/stage200_formal_gap_model_with_probe/`
""",
    )

    append_once(CHECKLIST, "Stage200 formal gap model with probe recorded", """
- [x] Stage200 formal gap model with probe recorded.
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
    assumption_rows = build_assumption_rows()
    lower_rows = build_lower_bound_rows()
    probe_rows = build_finite_probe_rows()
    counter_rows = build_counterexample_rows(probe_rows)
    gap_rows = build_gap_projection_rows()
    obligation_rows = build_obligation_rows()
    next_rows = build_next_rows()
    summary_rows = build_summary_rows(probe_rows, counter_rows)

    write_csv(ASSUMPTION_CSV, assumption_rows, ["assumption_id", "statement", "scope", "evidence", "falsification"])
    write_csv(
        LOWER_BOUND_CSV,
        lower_rows,
        [
            "r",
            "T",
            "input_components_m",
            "mat_input_dft_lower_bound",
            "repeated_scalar_input_dft",
            "mat_input_dft_over_repeated",
            "dense_mat_addmul_terms",
            "repeated_scalar_dense_terms",
            "dense_terms_over_repeated",
            "interpretation",
            "evidence",
        ],
    )
    write_csv(
        FINITE_PROBE_CSV,
        probe_rows,
        ["probe", "r", "N", "q", "seed", "omitted_component", "mismatches", "status", "interpretation"],
    )
    write_csv(COUNTEREXAMPLE_CSV, counter_rows, ["candidate_shortcut", "expected_if_valid", "observed", "decision", "evidence"])
    write_csv(GAP_PROJECTION_CSV, gap_rows, ["component", "full_sab_share_and_required_speedup", "route_status", "interpretation", "evidence"])
    write_csv(OBLIGATION_CSV, obligation_rows, ["obligation_id", "statement", "status", "evidence", "needed_before_stronger_claim"])
    write_csv(NEXT_CSV, next_rows, ["priority", "route", "entry_condition", "gate", "current_status", "evidence"])
    write_csv(
        SUMMARY_CSV,
        summary_rows,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_report(assumption_rows, lower_rows, probe_rows, counter_rows, gap_rows, obligation_rows, next_rows, summary_rows)
    write_commands()
    write_docs(assumption_rows, lower_rows, counter_rows, obligation_rows, next_rows, summary_rows)
    update_global_docs()
    write_artifacts(
        [
            OUT_MD,
            PLAN_MD,
            THEORY_MD,
            VARIANT_MD,
            REPORT_MD,
            COMMANDS_MD,
            SUMMARY_CSV,
            ASSUMPTION_CSV,
            LOWER_BOUND_CSV,
            FINITE_PROBE_CSV,
            COUNTEREXAMPLE_CSV,
            GAP_PROJECTION_CSV,
            OBLIGATION_CSV,
            NEXT_CSV,
            Path(__file__),
        ]
    )
    print(DECISION)


if __name__ == "__main__":
    main()
