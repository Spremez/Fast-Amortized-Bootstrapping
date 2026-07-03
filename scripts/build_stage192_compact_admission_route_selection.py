#!/usr/bin/env python3
"""Stage192: compact-route implementation admission and route selection."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage192_compact_admission_route_selection"

SUMMARY_CSV = OUT_DIR / "summary.csv"
ADMISSION_CSV = OUT_DIR / "gate_admission_matrix.csv"
ROUTE_CSV = OUT_DIR / "route_selection.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
CLAIM_CSV = OUT_DIR / "claim_policy.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage192_compact_admission_route_selection.md"
PLAN_MD = ROOT / "experiments" / "stage192_compact_admission_route_selection_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage192_compact_admission_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_compact_admission_route_selection.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE187_THEOREMS = ROOT / "repro" / "stage187_compact_proof_obligation_draft" / "theorem_matrix.csv"
STAGE189_SUMMARY = ROOT / "repro" / "stage189_closed_state_linear_probe" / "summary.csv"
STAGE190_SUMMARY = ROOT / "repro" / "stage190_selector_distribution_distinguisher" / "summary.csv"
STAGE191_SUMMARY = ROOT / "repro" / "stage191_secret_correction_noise_resource_gate" / "summary.csv"
STAGE178_PERBIT = ROOT / "repro" / "stage178_fullmat_perbit_frontier" / "per_bit_throughput.csv"
STAGE178_COMPONENT = ROOT / "repro" / "stage178_fullmat_perbit_frontier" / "component_attribution.csv"
STAGE182_FRONTIER = ROOT / "repro" / "stage182_exact_path_negative_frontier" / "frontier_decisions.csv"
STAGE183_MECHANISMS = ROOT / "repro" / "stage183_addmul_dataflow_screen" / "mechanism_screen.csv"
STAGE185_CLAIMS = ROOT / "repro" / "stage185_research_repro_package_refresh" / "claim_table.csv"

DECISION = "PASS_STAGE192_COMPACT_IMPLEMENTATION_DENIED_ROUTE_EXACT_ADDMUL_PREFLIGHT"


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


def metric(path: Path, key_col: str, key: str, value_col: str) -> str:
    for row in read_csv_dicts(path):
        if row.get(key_col) == key:
            return row.get(value_col, "")
    return ""


def theorem_status(theorem_id: str) -> str:
    for row in read_csv_dicts(STAGE187_THEOREMS):
        if row.get("id") == theorem_id:
            return row.get("current_status", "")
    return ""


def build_admission_rows() -> List[Dict[str, str]]:
    return [
        {
            "gate": "G1_key_distribution",
            "target_theorem": "T1_key_distribution",
            "status": "FAIL_STANDARD_SHORTCUTS_REJECTED",
            "primary_evidence": rel(STAGE190_SUMMARY),
            "blocking_fact": "row deletion, deterministic zero rows, and forced equal/shared masks have public distinguishers",
            "implementation_consequence": "no compact selector may be treated as standard dense MAT_TRGSW distribution",
        },
        {
            "gate": "G2_closed_state",
            "target_theorem": "T2_closed_state",
            "status": "FAIL_DIRECT_PUBLIC_CLOSURE",
            "primary_evidence": rel(STAGE189_SUMMARY),
            "blocking_fact": "public one-shared-mask projection is inconsistent for r>1 finite probes",
            "implementation_consequence": "do not wire lane-local compact output into PVW_TMLWE SAB state",
        },
        {
            "gate": "G3_phase_equivalence",
            "target_theorem": "T3_phase_equivalence",
            "status": "TOY_ONLY_NOT_PRODUCTION",
            "primary_evidence": rel(STAGE187_THEOREMS),
            "blocking_fact": "production polynomial/RLWE CMUX/RGSW/sparse_mul equivalence is not proven for a closed compact state",
            "implementation_consequence": "phase toy evidence cannot authorize full SAB code",
        },
        {
            "gate": "G4_noise_bound",
            "target_theorem": "T4_noise_bound",
            "status": "FAIL_NOT_PROVEN",
            "primary_evidence": rel(STAGE191_SUMMARY),
            "blocking_fact": "secret correction/key-switch closure has tight latency budget, resource risk, and no repeated noise recurrence",
            "implementation_consequence": "no correction/key-switch compact path may enter sab_pvw hot path",
        },
        {
            "gate": "G5_complete_sab_performance",
            "target_theorem": "T5_performance_survival",
            "status": "NOT_RUN_NO_IMPLEMENTATION_PERMISSION",
            "primary_evidence": rel(STAGE187_THEOREMS),
            "blocking_fact": "kernel-level compact gains cannot be lifted to complete-SAB without G1-G4 and implementation",
            "implementation_consequence": "do not claim compact complete-SAB speedup",
        },
        {
            "gate": "G6_novelty_scope",
            "target_theorem": "T6_novelty_scope",
            "status": "STRONG_CLAIM_DENIED",
            "primary_evidence": rel(STAGE187_THEOREMS),
            "blocking_fact": "no implemented compact route and no citation-supported novelty upgrade",
            "implementation_consequence": "only scoped exact-route engineering wording remains allowed",
        },
    ]


def build_route_rows() -> List[Dict[str, str]]:
    exact_speedup = metric(STAGE178_PERBIT, "metric", "speedup_vs_scalar_repeated_mean", "value")
    exact_min = metric(STAGE178_PERBIT, "metric", "speedup_vs_scalar_repeated_min", "value")
    mat_share = metric(STAGE178_COMPONENT, "component", "mat_ep_subdecomp", "share_of_pvw_full")
    dft_share = metric(STAGE178_COMPONENT, "component", "from_dft_materialize", "share_of_pvw_full")
    return [
        {
            "route": "compact_shared_output_mat_sab",
            "status": "PROOF_ONLY_IMPLEMENTATION_DENIED",
            "why": "G1/G2/G4 failed or remain unproven; G3 is toy-only and G5 cannot run",
            "primary_metric": "no valid T_bootstrap/r benchmark",
            "allowed_next": "formal structured-key proof or isolated noise proof only; no sab_pvw production code",
            "stage193_priority": "no",
        },
        {
            "route": "exact_full_mat_current_path",
            "status": "CURRENT_SCOPED_BASELINE",
            "why": "implemented PVW/MAT-SAB exact route remains the only closed r-body ciphertext SAB path",
            "primary_metric": f"T_bootstrap/r speedup mean {exact_speedup}x; min {exact_min}x",
            "allowed_next": "keep as baseline and regression reference",
            "stage193_priority": "reference",
        },
        {
            "route": "exact_addmul_from_dec_dft_new_dataflow",
            "status": "SELECT_FOR_STAGE193_PREFLIGHT",
            "why": "Stage182 keeps R3 open only for a new dataflow proof; Stage178/180 show addmul share is large enough for modest gains",
            "primary_metric": f"MAT EP/subdecomp full share {mat_share}; from_DFT share {dft_share}",
            "allowed_next": "assembly/counter/source-backed preflight; no code promotion unless projected >=3% complete-SAB gain",
            "stage193_priority": "yes",
        },
        {
            "route": "exact_torus_to_dft_new_mechanism",
            "status": "SECONDARY_AFTER_R3",
            "why": "share is meaningful but Stage174 direct-scale/backend locality was neutral",
            "primary_metric": f"from_DFT materialize share {dft_share}",
            "allowed_next": "only a genuinely new DFT/conversion mechanism",
            "stage193_priority": "defer",
        },
        {
            "route": "tail_setup_extract_ks",
            "status": "DEFER",
            "why": "residual share is too small to drive the main objective unless profiling changes",
            "primary_metric": "residual share 0.074538623",
            "allowed_next": "reopen only if new profile shows residual >15%",
            "stage193_priority": "no",
        },
    ]


def build_next_rows() -> List[Dict[str, str]]:
    return [
        {
            "stage": "Stage193",
            "title": "Exact Addmul Dataflow Preflight",
            "status": "NEXT",
            "goal": "screen a non-layout exact full-MAT addmul dataflow mechanism before code",
            "required_inputs": f"{rel(STAGE182_FRONTIER)}; {rel(STAGE183_MECHANISMS)}; src/mosfhet/src/mattrgsw.c",
            "correctness_gate": "no source changes; identify exact mathematical equivalence constraints before implementation",
            "performance_gate": "projected >=3% complete-SAB gain from measured/counter-backed component model",
            "failure_action": "record no-code result and move to secondary DFT mechanism or scoped final paper package",
        },
        {
            "stage": "Stage194",
            "title": "Exact Addmul Candidate Microbench",
            "status": "CONDITIONAL",
            "goal": "implement only if Stage193 finds a new mechanism not covered by rejected fulltile/bodymajor/streaming families",
            "required_inputs": "Stage193 promoted mechanism",
            "correctness_gate": "deterministic MAT EP equivalence r=2/4/6 and no scalar regression",
            "performance_gate": "same-backend microbench plus complete-SAB projection",
            "failure_action": "revert/keep default-off as negative ablation",
        },
        {
            "stage": "Compact proof follow-up",
            "title": "Structured-Key Formal Route",
            "status": "OPTIONAL_PROOF_ONLY",
            "goal": "study new selector distribution only as a proof object",
            "required_inputs": f"{rel(STAGE190_SUMMARY)}; {rel(STAGE191_SUMMARY)}",
            "correctness_gate": "T1/T2/T4 proof obligations pass before any code",
            "performance_gate": "none until implementation permission exists",
            "failure_action": "keep compact route as limitations/future work",
        },
    ]


def build_claim_rows() -> List[Dict[str, str]]:
    return [
        {
            "claim": "exact_full_mat_complete_sab_speedup",
            "status": "ALLOW_SCOPED",
            "safe_wording": "current exact PVW/MAT-SAB path has scoped complete-SAB T_bootstrap/r speedup under recorded conditions",
            "forbidden_wording": "theoretically optimal or general across all parameters/backends",
            "evidence": rel(STAGE178_PERBIT),
        },
        {
            "claim": "compact_shared_output_implementation",
            "status": "DENY",
            "safe_wording": "compact/shared-output remains proof-only",
            "forbidden_wording": "implemented compact SAB or compact complete-SAB speedup",
            "evidence": f"{rel(STAGE189_SUMMARY)}; {rel(STAGE190_SUMMARY)}; {rel(STAGE191_SUMMARY)}",
        },
        {
            "claim": "avx512_or_addmul_optimality",
            "status": "DENY",
            "safe_wording": "exact addmul remains open only for a new dataflow preflight",
            "forbidden_wording": "current AVX512 MAT addmul is theoretically optimal",
            "evidence": f"{rel(STAGE182_FRONTIER)}; {rel(STAGE183_MECHANISMS)}",
        },
        {
            "claim": "stage193_future_candidate",
            "status": "EXPERIMENT_PENDING",
            "safe_wording": "Stage193 may screen an exact addmul dataflow candidate",
            "forbidden_wording": "Stage193 candidate speeds up bootstrapping before measured gates",
            "evidence": rel(NEXT_CSV),
        },
    ]


def build_summary_rows(
    admission_rows: List[Dict[str, str]],
    route_rows: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    inputs = [
        STAGE187_THEOREMS,
        STAGE189_SUMMARY,
        STAGE190_SUMMARY,
        STAGE191_SUMMARY,
        STAGE178_PERBIT,
        STAGE182_FRONTIER,
        STAGE183_MECHANISMS,
    ]
    ok = all(path.exists() for path in inputs)
    denied_gates = sum(1 for row in admission_rows if row["status"].startswith("FAIL") or row["status"].startswith("STRONG"))
    next_selected = ";".join(row["stage"] for row in next_rows if row["status"] == "NEXT")
    return [
        {
            "gate": "stage192_inputs",
            "status": "PASS" if ok else "FAIL",
            "metric": "required_inputs_present",
            "value": "1" if ok else "0",
            "evidence": f"{rel(STAGE187_THEOREMS)}; {rel(STAGE189_SUMMARY)}; {rel(STAGE190_SUMMARY)}; {rel(STAGE191_SUMMARY)}",
            "detail": "Stage192 consumes the compact proof gates and exact-route frontier ledgers.",
            "next_action": "Repair missing inputs before route selection.",
        },
        {
            "gate": "stage192_compact_admission",
            "status": "DENY_PRODUCTION_COMPACT_CODE",
            "metric": "failed_or_denied_gates",
            "value": str(denied_gates),
            "evidence": rel(ADMISSION_CSV),
            "detail": "Compact/shared-output MAT-SAB fails implementation admission under T1/T2/T4 and cannot run a valid T5 full-SAB benchmark.",
            "next_action": "Keep compact proof-only.",
        },
        {
            "gate": "stage192_route_selection",
            "status": "SELECT_EXACT_ADDMUL_PREFLIGHT",
            "metric": "next_stage",
            "value": next_selected,
            "evidence": f"{rel(ROUTE_CSV)}; {rel(NEXT_CSV)}",
            "detail": "The next non-theory path is exact full-MAT addmul dataflow preflight, not compact SAB code.",
            "next_action": "Run Stage193 source/assembly/counter-backed preflight.",
        },
        {
            "gate": "stage192_decision",
            "status": DECISION,
            "metric": "production_compact_sab_permission",
            "value": "0",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Research loop is redirected from proof-blocked compact route to a bounded exact-route experiment gate.",
            "next_action": "Proceed to Stage193.",
        },
    ]


def write_docs(
    summary_rows: List[Dict[str, str]],
    admission_rows: List[Dict[str, str]],
    route_rows: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
    claim_rows: List[Dict[str, str]],
) -> None:
    write_text_lf(
        OUT_MD,
        f"""# Stage192 Compact Admission and Route Selection

Decision: `{DECISION}`.

Stage192 is the implementation-admission audit after Stage189/190/191. It
does not stop the active research goal. It closes one branch:
compact/shared-output MAT-SAB remains proof-only and is not allowed to enter
the `sab_pvw_*` production hot path.

The next bounded non-theory work is Stage193: exact full-MAT addmul dataflow
preflight. This keeps the primary endpoint as complete-SAB `T_bootstrap/r`
and requires a new mechanism before code.

## Gate Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Admission Matrix

{table(admission_rows, ["gate", "target_theorem", "status", "primary_evidence", "blocking_fact", "implementation_consequence"])}
## Route Selection

{table(route_rows, ["route", "status", "why", "primary_metric", "allowed_next", "stage193_priority"])}
## Next Stage Queue

{table(next_rows, ["stage", "title", "status", "goal", "required_inputs", "correctness_gate", "performance_gate", "failure_action"])}
## Claim Policy

{table(claim_rows, ["claim", "status", "safe_wording", "forbidden_wording", "evidence"])}
""",
    )

    write_text_lf(
        PLAN_MD,
        """# Stage192 Plan

Goal: decide whether compact/shared-output MAT-SAB has implementation
permission after T1/T2/T4 gates and select the next non-theory research step.

Rules:

- do not modify `sab_pvw_*`;
- deny compact production code unless G1-G4 pass;
- preserve exact full-MAT PVW/MAT-SAB as the scoped baseline;
- select only a bounded experiment route with a projected complete-SAB impact.
""",
    )

    write_text_lf(
        THEORY_MD,
        """# Stage192 Compact Admission Model

Implementation admission requires all of:

1. T1: a permitted selector/key distribution.
2. T2: closed one-mask/r-body PVW_TMLWE state.
3. T3: production phase equivalence.
4. T4: noise and resource bound.

Stage189 rejects direct public shared-mask closure for r>1. Stage190 rejects
standard-distribution shortcuts. Stage191 records that secret correction or
key-switch closure lacks latency/resource/noise proof. Therefore compact SAB
cannot run a valid complete-SAB `T_bootstrap/r` benchmark yet.

To avoid a theory loop, the next executable route is not another compact
implementation attempt. It is an exact full-MAT addmul dataflow preflight tied
to the current hot component and strict promotion thresholds.
""",
    )

    write_text_lf(
        VARIANT_MD,
        """# Compact Admission Route Selection

This is a route-selection artifact, not an implementation.

Current route decisions:

- exact full-MAT PVW/MAT-SAB: current scoped baseline;
- compact/shared-output MAT-SAB: proof-only, implementation denied;
- exact addmul dataflow: selected for Stage193 preflight;
- exact from-DFT mechanism: secondary if addmul preflight fails;
- tail setup/extract/KS: deferred.

Stage193 must not reopen rejected fulltile/bodymajor/streaming retuning unless
it identifies a genuinely new dataflow mechanism.
""",
    )


def update_global_docs() -> None:
    append_once(
        ROADMAP_MD,
        "## Stage 192: Compact Admission and Route Selection",
        f"""
## Stage 192: Compact Admission and Route Selection

Goal:

```text
Audit compact/shared-output implementation permission after Stage189-191 and
select the next bounded non-theory experiment route.
```

Status:

```text
Completed. Stage192 records {DECISION}. Compact/shared-output SAB production
code remains denied. The next executable route is Stage193 exact full-MAT
addmul dataflow preflight.
```
""",
    )

    append_once(
        GOAL_MD,
        "Stage192 records compact admission and route selection",
        f"""
Stage192 records compact admission and route selection. Decision:
`{DECISION}`. It keeps compact/shared-output MAT-SAB proof-only and routes the
active research loop to exact full-MAT addmul dataflow preflight.
""",
    )

    append_once(
        CURRENT_GOAL_MD,
        "Treat Stage192 as compact admission and route selection",
        f"""
96. Treat Stage192 as compact admission and route selection:
    `{DECISION}`. Compact/shared-output SAB implementation is denied after
    T1/T2/T4 gates. The next non-theory executable route is Stage193 exact
    full-MAT addmul dataflow preflight.
""",
    )

    append_once(
        HYPOTHESIS_YAML,
        "H116_compact_admission_route_selection",
        f"""
  - id: H116_compact_admission_route_selection
    statement: >
      After T1/T2/T4 gates, compact/shared-output MAT-SAB should remain
      proof-only and the active implementation loop should move to exact
      full-MAT addmul dataflow preflight.
    mechanism: >
      Stage192 aggregates Stage189 closed-state, Stage190 distribution, and
      Stage191 noise/resource results with the exact-route frontier ledger.
    status: stage192_compact_admission_route_selection
    evidence: docs/stage192_compact_admission_route_selection.md; experiments/stage192_compact_admission_route_selection_plan.md; theory_checks/stage192_compact_admission_model.md; repro/stage192_compact_admission_route_selection/summary.csv
    current_decision: >
      {DECISION}
    failure_criteria:
      - compact production SAB code is written despite denied admission gates
      - exact addmul preflight reopens rejected layout-only retuning
      - kernel-only compact timing is reported as complete-SAB speedup
""",
    )

    append_once(
        RUN_LOG,
        "stage192-compact-admission-route-selection-001",
        f"""
stage192-compact-admission-route-selection-001,2026-07-04,{git_head()},Stage 192,analysis,python scripts/build_stage192_compact_admission_route_selection.py,Stage189-191 gates and Stage182/183 frontier,none,{DECISION},Compact implementation admission denied; route selected to exact addmul preflight.,repro/stage192_compact_admission_route_selection
""",
    )

    append_once(
        MANIFEST,
        "stage192_compact_admission_route_selection",
        f"""
- stage192_compact_admission_route_selection: `{DECISION}`
  - `docs/stage192_compact_admission_route_selection.md`
  - `experiments/stage192_compact_admission_route_selection_plan.md`
  - `theory_checks/stage192_compact_admission_model.md`
  - `algorithm_variants/mat_rlwe_sab_compact_admission_route_selection.md`
  - `repro/stage192_compact_admission_route_selection/`
""",
    )

    append_once(CHECKLIST, "Stage192 compact admission and route selection recorded", """
- [x] Stage192 compact admission and route selection recorded.
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
    admission_rows = build_admission_rows()
    route_rows = build_route_rows()
    next_rows = build_next_rows()
    claim_rows = build_claim_rows()
    summary_rows = build_summary_rows(admission_rows, route_rows, next_rows)

    write_csv(
        ADMISSION_CSV,
        admission_rows,
        ["gate", "target_theorem", "status", "primary_evidence", "blocking_fact", "implementation_consequence"],
    )
    write_csv(ROUTE_CSV, route_rows, ["route", "status", "why", "primary_metric", "allowed_next", "stage193_priority"])
    write_csv(
        NEXT_CSV,
        next_rows,
        ["stage", "title", "status", "goal", "required_inputs", "correctness_gate", "performance_gate", "failure_action"],
    )
    write_csv(CLAIM_CSV, claim_rows, ["claim", "status", "safe_wording", "forbidden_wording", "evidence"])
    write_csv(SUMMARY_CSV, summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    write_docs(summary_rows, admission_rows, route_rows, next_rows, claim_rows)
    update_global_docs()
    write_artifacts(
        [
            OUT_MD,
            PLAN_MD,
            THEORY_MD,
            VARIANT_MD,
            SUMMARY_CSV,
            ADMISSION_CSV,
            ROUTE_CSV,
            NEXT_CSV,
            CLAIM_CSV,
            Path(__file__),
        ]
    )
    print(DECISION)


if __name__ == "__main__":
    main()
