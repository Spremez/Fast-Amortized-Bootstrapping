#!/usr/bin/env python3
"""Stage191: T4 secret-correction noise/resource lower-bound gate."""

from __future__ import annotations

import csv
import hashlib
import math
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage191_secret_correction_noise_resource_gate"

SUMMARY_CSV = OUT_DIR / "summary.csv"
LATENCY_CSV = OUT_DIR / "latency_budget.csv"
RESOURCE_CSV = OUT_DIR / "resource_budget.csv"
NOISE_CSV = OUT_DIR / "noise_sensitivity.csv"
ROUTE_CSV = OUT_DIR / "route_decision.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage191_secret_correction_noise_resource_gate.md"
PLAN_MD = ROOT / "experiments" / "stage191_secret_correction_noise_resource_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage191_secret_correction_noise_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_secret_correction_closure.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE134_RATIO = ROOT / "repro" / "stage134_generalized_lane_pair_input_ep_gate" / "ratio_summary.csv"
STAGE138_RATIO = ROOT / "repro" / "stage138_shared_mask_compact_gate" / "ratio_summary.csv"
STAGE176_API = ROOT / "repro" / "stage176_structured_compact_security_api_gate" / "api_options.csv"
STAGE178_PERBIT = ROOT / "repro" / "stage178_fullmat_perbit_frontier" / "per_bit_throughput.csv"
STAGE178_COMPONENT = ROOT / "repro" / "stage178_fullmat_perbit_frontier" / "component_attribution.csv"
STAGE189_CONVERSION = ROOT / "repro" / "stage189_closed_state_linear_probe" / "conversion_cost_model.csv"
STAGE190_ROUTE = ROOT / "repro" / "stage190_selector_distribution_distinguisher" / "distribution_route.csv"
STAGE124_LAYOUT = ROOT / "repro" / "stage124_mosfhet_type_api_skeleton" / "layout_results.csv"
STAGE187_THEOREMS = ROOT / "repro" / "stage187_compact_proof_obligation_draft" / "theorem_matrix.csv"

DECISION = "PASS_STAGE191_T4_SECRET_CORRECTION_LOWER_BOUND_RECORDED_IMPLEMENTATION_DENIED"
TARGET_N = 2048
T = 7


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


def layout_by_r(r: int) -> Dict[str, str]:
    rows = read_csv_dicts(STAGE124_LAYOUT)
    for row in rows:
        if row.get("r") == str(r) and row.get("N") == str(TARGET_N):
            return row
    for row in rows:
        if row.get("r") == str(r):
            return row
    return {}


def stage134_by_r_n(r: int, n: int) -> Dict[str, str]:
    for row in read_csv_dicts(STAGE134_RATIO):
        if row.get("r") == str(r) and row.get("N") == str(n):
            return row
    return {}


def perbit(metric: str) -> str:
    for row in read_csv_dicts(STAGE178_PERBIT):
        if row.get("metric") == metric:
            return row.get("value", "")
    return ""


def component_value(component: str, column: str) -> str:
    for row in read_csv_dicts(STAGE178_COMPONENT):
        if row.get("component") == component:
            return row.get(column, "")
    return ""


def build_latency_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for row in read_csv_dicts(STAGE138_RATIO):
        r = int(row["r"])
        n = int(row["N"])
        repeated_us = f(row["repeated_us"])
        shared_us = f(row["shared_us"])
        saved_us = max(0.0, repeated_us - shared_us)
        corrections = max(1, r - 1)
        budget_per_correction = saved_us / corrections
        proxy = stage134_by_r_n(r, n)
        addmul_lane = f(proxy.get("dense_addmul_mean_us", "")) / r if proxy else 0.0
        dft_add_lane = (
            f(proxy.get("dense_decomp_dft_mean_us", "")) + f(proxy.get("dense_addmul_mean_us", ""))
        ) / r if proxy else 0.0
        addmul_ratio = addmul_lane / budget_per_correction if budget_per_correction else math.inf
        dft_add_ratio = dft_add_lane / budget_per_correction if budget_per_correction else math.inf
        if dft_add_ratio > 1.0:
            status = "FAIL_IF_CORRECTION_NEEDS_DECOMP_DFT_PLUS_ADDMUL"
        elif addmul_ratio > 1.0:
            status = "FAIL_EVEN_ADDMUL_ONLY_PROXY"
        else:
            status = "LATENCY_BUDGET_ONLY_FOR_ADDMUL_LIKE_CORRECTION"
        rows.append(
            {
                "backend": row["backend"],
                "r": str(r),
                "N": str(n),
                "kernel_repeated_us": f"{repeated_us:.6f}",
                "kernel_shared_us": f"{shared_us:.6f}",
                "available_saved_us": f"{saved_us:.6f}",
                "min_corrections_per_cmux": str(corrections),
                "budget_us_per_correction": f"{budget_per_correction:.6f}",
                "proxy_addmul_us_per_lane": f"{addmul_lane:.6f}",
                "proxy_decomp_dft_addmul_us_per_lane": f"{dft_add_lane:.6f}",
                "addmul_proxy_over_budget": f"{addmul_ratio:.6f}",
                "decomp_dft_addmul_proxy_over_budget": f"{dft_add_ratio:.6f}",
                "status": status,
            }
        )
    return rows


def build_resource_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for r in [2, 4, 6]:
        layout = layout_by_r(r)
        dense = int(layout.get("current_selector_dft_polys") or ((r + 1) * (r + 1) * T))
        compact = int(layout.get("vector_selector_dft_polys") or (4 * r * T))
        max_extra = dense - compact
        min_extra = (r - 1) * T
        ks_like_extra = (r - 1) * T * T
        min_total = compact + min_extra
        ks_total = compact + ks_like_extra
        rows.append(
            {
                "r": str(r),
                "N": str(layout.get("N") or TARGET_N),
                "T": str(T),
                "dense_selector_rows": str(dense),
                "compact_selector_rows": str(compact),
                "max_extra_rows_before_losing_count_gain": str(max_extra),
                "minimal_one_gadget_correction_rows": str(min_extra),
                "ks_like_T_gadget_correction_rows": str(ks_like_extra),
                "dense_over_compact_plus_minimal": f"{dense / min_total:.6f}",
                "dense_over_compact_plus_ks_like": f"{dense / ks_total:.6f}",
                "minimal_status": "COUNT_POSITIVE" if min_total <= dense else "COUNT_NEGATIVE",
                "ks_like_status": "COUNT_POSITIVE" if ks_total <= dense else "COUNT_NEGATIVE",
            }
        )
    return rows


def build_noise_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    steps = 40 * 7 * 2048
    for r in [2, 4, 6]:
        corrections = r - 1
        for rho in [0.0, 0.1, 0.25, 0.5, 1.0]:
            multiplier = math.sqrt(1.0 + corrections * rho * rho)
            rows.append(
                {
                    "r": str(r),
                    "cmux_steps_binary_set_2_3_2048": str(steps),
                    "min_corrections_per_cmux": str(corrections),
                    "rho_sigma_correction_over_baseline_step": f"{rho:.2f}",
                    "per_step_sigma_multiplier": f"{multiplier:.6f}",
                    "variance_multiplier": f"{multiplier * multiplier:.6f}",
                    "status": "ZERO_EXTRA_NOISE_ONLY" if rho == 0.0 else "T4_NEEDS_REAL_NOISE_BOUND",
                    "interpretation": "Normalized sensitivity; not a measured noise proof.",
                }
            )
    return rows


def build_route_rows() -> List[Dict[str, str]]:
    return [
        {
            "route": "public_projection_to_shared_mask",
            "t4_status": "NOT_APPLICABLE_REJECTED_BY_T2",
            "latency_status": "no correction benchmark because algebra gate failed",
            "noise_status": "not evaluated",
            "implementation_permission": "NO",
            "next_action": "closed by Stage189 unless a new algebraic invariant appears",
        },
        {
            "route": "secret_correction_each_cmux",
            "t4_status": "OPEN_BLOCKED_BY_NO_NOISE_PROOF",
            "latency_status": "budget is tight and fails if correction requires decompose/DFT plus addmul in proxy rows",
            "noise_status": "any nonzero correction noise increases per-step variance; no multi-seed bound exists",
            "implementation_permission": "NO",
            "next_action": "only an isolated noise/key-size proof probe, not sab_pvw hot-path code",
        },
        {
            "route": "keyswitch_or_reshare_each_cmux",
            "t4_status": "OPEN_HIGH_RISK",
            "latency_status": "must fit within per-correction saved-us budget and include key/materialization overhead",
            "noise_status": "requires KS noise recurrence over all CMUX steps",
            "implementation_permission": "NO",
            "next_action": "derive explicit KS parameters and compare against budget before code",
        },
        {
            "route": "dense_full_mat_reexpansion",
            "t4_status": "CURRENT_REFERENCE",
            "latency_status": "implemented exact path; no compact claim",
            "noise_status": "covered by current exact PVW/MAT-SAB gates",
            "implementation_permission": "YES_FOR_EXACT_FULL_MAT_ONLY",
            "next_action": "keep as baseline/reference",
        },
        {
            "route": "new_structured_selector_distribution",
            "t4_status": "PROOF_ONLY_AFTER_T1",
            "latency_status": "unmeasured",
            "noise_status": "must prove selector and repeated SAB noise recurrence",
            "implementation_permission": "NO",
            "next_action": "first supply a T1 structured-key assumption/reduction",
        },
    ]


def build_summary_rows(
    latency_rows: List[Dict[str, str]],
    resource_rows: List[Dict[str, str]],
    noise_rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    inputs = [
        STAGE134_RATIO,
        STAGE138_RATIO,
        STAGE176_API,
        STAGE178_PERBIT,
        STAGE189_CONVERSION,
        STAGE190_ROUTE,
        STAGE187_THEOREMS,
    ]
    ok = all(path.exists() for path in inputs)
    latency_fail_count = sum(
        1 for row in latency_rows if row["status"] == "FAIL_IF_CORRECTION_NEEDS_DECOMP_DFT_PLUS_ADDMUL"
    )
    ks_resource_negative = sum(1 for row in resource_rows if row["ks_like_status"] == "COUNT_NEGATIVE")
    noisy_rows = sum(1 for row in noise_rows if row["status"] == "T4_NEEDS_REAL_NOISE_BOUND")
    return [
        {
            "gate": "stage191_inputs",
            "status": "PASS" if ok else "FAIL",
            "metric": "required_inputs_present",
            "value": "1" if ok else "0",
            "evidence": f"{rel(STAGE189_CONVERSION)}; {rel(STAGE190_ROUTE)}; {rel(STAGE138_RATIO)}",
            "detail": "Stage191 targets T4 after T2 public closure and T1 standard-distribution shortcuts were rejected.",
            "next_action": "Repair missing inputs before interpreting the lower-bound gate.",
        },
        {
            "gate": "stage191_latency_budget",
            "status": "RECORDED_TIGHT_BUDGET",
            "metric": "proxy_rows_failing_decomp_dft_addmul_budget",
            "value": str(latency_fail_count),
            "evidence": rel(LATENCY_CSV),
            "detail": "Secret correction must fit inside saved compact-kernel time; proxy rows fail when correction needs decompose/DFT plus addmul.",
            "next_action": "No implementation unless an isolated correction kernel is measured below budget.",
        },
        {
            "gate": "stage191_resource_budget",
            "status": "RECORDED",
            "metric": "ks_like_count_negative_rows",
            "value": str(ks_resource_negative),
            "evidence": rel(RESOURCE_CSV),
            "detail": "Minimal one-gadget correction can preserve row-count gain, but KS-like T-gadget correction can erase it for some r.",
            "next_action": "Require explicit key format before code.",
        },
        {
            "gate": "stage191_noise_sensitivity",
            "status": "T4_NOT_PROVEN",
            "metric": "nonzero_noise_rows_require_bound",
            "value": str(noisy_rows),
            "evidence": rel(NOISE_CSV),
            "detail": "Any nonzero correction noise increases normalized per-step variance; no measured recurrence or multi-seed bound exists.",
            "next_action": "Run only isolated noise recurrence proof/probe if this route is continued.",
        },
        {
            "gate": "stage191_decision",
            "status": DECISION,
            "metric": "production_compact_sab_permission",
            "value": "0",
            "evidence": rel(ROUTE_CSV),
            "detail": "Secret-correction/key-switch closure remains proof-only and implementation-denied.",
            "next_action": "Proceed to a structured-key proof draft or keep compact route as limitation.",
        },
    ]


def write_docs(
    summary_rows: List[Dict[str, str]],
    latency_rows: List[Dict[str, str]],
    resource_rows: List[Dict[str, str]],
    noise_rows: List[Dict[str, str]],
    route_rows: List[Dict[str, str]],
) -> None:
    write_text_lf(
        OUT_MD,
        f"""# Stage191 Secret-Correction Noise/Resource Gate

Decision: `{DECISION}`.

Stage191 targets the Stage187 `T4_noise_bound` obligation for the only
remaining closure family after Stage189/190: use secret-dependent correction,
key switching, or re-sharing to turn lane-local compact masks into a one-mask
PVW_TMLWE state.

This is a lower-bound gate, not a production implementation. It records the
latency budget, key/materialization budget, and normalized noise sensitivity
that any future correction route must beat before touching `sab_pvw_*`.

Current exact full-MAT complete-SAB evidence remains scoped:

- `T_bootstrap/r` mean speedup versus repeated scalar:
  `{perbit('speedup_vs_scalar_repeated_mean')}x`;
- conservative min: `{perbit('speedup_vs_scalar_repeated_min')}x`;
- CI-low: `{perbit('speedup_vs_scalar_repeated_ci95_low')}x`.

## Gate Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Latency Budget

{table(latency_rows, ["backend", "r", "N", "kernel_repeated_us", "kernel_shared_us", "available_saved_us", "min_corrections_per_cmux", "budget_us_per_correction", "proxy_addmul_us_per_lane", "proxy_decomp_dft_addmul_us_per_lane", "addmul_proxy_over_budget", "decomp_dft_addmul_proxy_over_budget", "status"])}
## Resource Budget

{table(resource_rows, ["r", "N", "T", "dense_selector_rows", "compact_selector_rows", "max_extra_rows_before_losing_count_gain", "minimal_one_gadget_correction_rows", "ks_like_T_gadget_correction_rows", "dense_over_compact_plus_minimal", "dense_over_compact_plus_ks_like", "minimal_status", "ks_like_status"])}
## Noise Sensitivity

{table(noise_rows, ["r", "cmux_steps_binary_set_2_3_2048", "min_corrections_per_cmux", "rho_sigma_correction_over_baseline_step", "per_step_sigma_multiplier", "variance_multiplier", "status", "interpretation"])}
## Route Decision

{table(route_rows, ["route", "t4_status", "latency_status", "noise_status", "implementation_permission", "next_action"])}
""",
    )

    write_text_lf(
        PLAN_MD,
        """# Stage191 Plan

Goal: evaluate whether secret correction/key-switch closure can pass the T4
noise/resource precondition before any compact SAB implementation.

Rules:

- no `sab_pvw_*` hot-path changes;
- use Stage138 compact-kernel savings as the available latency budget;
- use Stage124 selector row counts as the public resource budget;
- report normalized noise sensitivity only, not a measured noise proof;
- deny implementation unless latency, resource, and noise gates all pass.
""",
    )

    write_text_lf(
        THEORY_MD,
        """# Stage191 Secret-Correction Noise Model

After Stage189, direct public collapse from lane-local masks `a_q` to one
shared mask `a*` is rejected. The algebraically possible repair is:

```text
b'_q = b_q + (a* - a_q) * s_q
```

or an equivalent key-switch/re-share. This changes the T4 problem:

1. The correction is secret-dependent and cannot be a public arithmetic update.
2. An evaluation/key-switch mechanism must contribute latency, key material,
   and noise.
3. Repeating this after every CMUX/NCMUX in the SAB schedule adds a new noise
   recurrence.

With normalized baseline step standard deviation `sigma_0` and correction
standard deviation `sigma_c = rho * sigma_0`, the per-step standard deviation
multiplier is bounded below by:

```text
sqrt(1 + (r - 1) * rho^2)
```

for the minimal choice of one existing lane mask as `a*` and correcting the
remaining `r-1` lanes. This model is a sensitivity screen; a real T4 proof
would need concrete key-switch parameters and multi-seed failure/noise
measurements.
""",
    )

    write_text_lf(
        VARIANT_MD,
        """# Secret-Correction Closure Candidate

## Summary

- Parent algorithm: compact/shared-output PVW/MAT-SAB proof route.
- Focused module: closed-state repair after compact CMUX/NCMUX.
- Optimization target: complete-SAB `T_bootstrap/r`.
- Status labels: [theory open], [experiment pending], implementation denied.
- Main hypothesis: secret correction or key switching can restore one shared
  PVW_TMLWE mask without erasing compact kernel savings.

## Mathematical Definition

For lane-local compact output `(a_q, b_q)`, choose one shared mask `a*` and set
`b'_q = b_q + (a* - a_q) * s_q`. The evaluator needs an approved mechanism for
the secret-dependent term.

## Pseudocode

```text
Input: lane-local masks a_q, bodies b_q, correction key material
Output: one shared mask a*, corrected bodies b'_q
1. Select public a* from one lane or a structured rule.
2. For every q with a_q != a*, derive an encrypted/key-switched correction for
   (a* - a_q) * s_q.
3. Add the correction to b_q.
4. Continue SAB only if the noise recurrence and key distribution proof pass.
```

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| Standard PVW_TMLWE state | Lane-local compact output plus correction | changes representation | Stage189/191 |
| Dense selector rows | Compact selector plus correction keys | changes key distribution | Stage190/191 |
| Existing noise recurrence | Correction noise recurrence | new proof obligation | Stage191 |

## Complexity Change

- Time: at least `r-1` corrections per CMUX/NCMUX.
- Memory: compact rows plus correction key rows.
- What must be measured: isolated correction latency, key size, noise, and
  full-SAB `T_bootstrap/r`.

## Theory Dependencies

- T1 structured-key proof or standard-distribution replacement.
- T2 closed-state proof after correction.
- T4 noise recurrence and failure-rate bound.

## Required Experiments

- Isolated correction kernel benchmark against the Stage191 per-correction
  budget.
- Multi-seed noise/failure probe over the full SAB schedule.
- Resource/key-size measurement for the correction key format.

## Paper Contribution Candidate

Only safe wording: secret-correction closure is a proof-only candidate with
recorded lower-bound budgets. It is not an implemented compact SAB speedup.
""",
    )


def update_global_docs() -> None:
    append_once(
        ROADMAP_MD,
        "## Stage 191: Secret-Correction Noise/Resource Gate",
        f"""
## Stage 191: Secret-Correction Noise/Resource Gate

Goal:

```text
Evaluate the remaining T4 route: secret correction/key-switch closure after
lane-local compact output.
```

Status:

```text
Completed. Stage191 records {DECISION}. The route remains proof-only:
correction must fit a tight saved-time budget, preserve key/materialization
gains, and prove a repeated SAB noise recurrence. Production compact SAB code
remains denied.
```
""",
    )

    append_once(
        GOAL_MD,
        "Stage191 records the secret-correction noise/resource gate",
        f"""
Stage191 records the secret-correction noise/resource gate. Decision:
`{DECISION}`. It quantifies the latency, resource, and normalized noise
barriers for key-switch/re-share closure and keeps compact SAB implementation
denied.
""",
    )

    append_once(
        CURRENT_GOAL_MD,
        "Treat Stage191 as the secret-correction noise/resource gate",
        f"""
95. Treat Stage191 as the secret-correction noise/resource gate:
    `{DECISION}`. Secret-correction or key-switch closure remains proof-only:
    it needs explicit key-format, latency, resource, and noise recurrence
    evidence before any `sab_pvw_*` production implementation.
""",
    )

    append_once(
        HYPOTHESIS_YAML,
        "H115_secret_correction_noise_resource_gate",
        f"""
  - id: H115_secret_correction_noise_resource_gate
    statement: >
      Secret-correction/key-switch closure for compact MAT-SAB cannot enter
      production SAB code until it fits the compact-kernel latency budget and
      proves key/resource and repeated-noise bounds.
    mechanism: >
      Stage191 converts Stage189/190 blockers into latency, resource, and
      normalized noise lower-bound tables.
    status: stage191_t4_secret_correction_gate
    evidence: docs/stage191_secret_correction_noise_resource_gate.md; experiments/stage191_secret_correction_noise_resource_gate_plan.md; theory_checks/stage191_secret_correction_noise_model.md; repro/stage191_secret_correction_noise_resource_gate/summary.csv
    current_decision: >
      {DECISION}
    failure_criteria:
      - correction path is implemented in sab_pvw before latency/resource/noise
        gates pass
      - normalized sensitivity is reported as a measured noise proof
      - compact kernel savings are reported as complete-SAB speedup after adding
        unmeasured correction overhead
""",
    )

    append_once(
        RUN_LOG,
        "stage191-secret-correction-noise-resource-gate-001",
        f"""
stage191-secret-correction-noise-resource-gate-001,2026-07-04,{git_head()},Stage 191,analysis,python scripts/build_stage191_secret_correction_noise_resource_gate.py,Stage187 T4 noise gate,none,{DECISION},Lower-bound latency/resource/noise gate for secret-correction compact closure.,repro/stage191_secret_correction_noise_resource_gate
""",
    )

    append_once(
        MANIFEST,
        "stage191_secret_correction_noise_resource_gate",
        f"""
- stage191_secret_correction_noise_resource_gate: `{DECISION}`
  - `docs/stage191_secret_correction_noise_resource_gate.md`
  - `experiments/stage191_secret_correction_noise_resource_gate_plan.md`
  - `theory_checks/stage191_secret_correction_noise_model.md`
  - `algorithm_variants/mat_rlwe_sab_secret_correction_closure.md`
  - `repro/stage191_secret_correction_noise_resource_gate/`
""",
    )

    append_once(CHECKLIST, "Stage191 secret-correction noise/resource gate recorded", """
- [x] Stage191 secret-correction noise/resource gate recorded.
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
    latency_rows = build_latency_rows()
    resource_rows = build_resource_rows()
    noise_rows = build_noise_rows()
    route_rows = build_route_rows()
    summary_rows = build_summary_rows(latency_rows, resource_rows, noise_rows)

    write_csv(
        LATENCY_CSV,
        latency_rows,
        [
            "backend",
            "r",
            "N",
            "kernel_repeated_us",
            "kernel_shared_us",
            "available_saved_us",
            "min_corrections_per_cmux",
            "budget_us_per_correction",
            "proxy_addmul_us_per_lane",
            "proxy_decomp_dft_addmul_us_per_lane",
            "addmul_proxy_over_budget",
            "decomp_dft_addmul_proxy_over_budget",
            "status",
        ],
    )
    write_csv(
        RESOURCE_CSV,
        resource_rows,
        [
            "r",
            "N",
            "T",
            "dense_selector_rows",
            "compact_selector_rows",
            "max_extra_rows_before_losing_count_gain",
            "minimal_one_gadget_correction_rows",
            "ks_like_T_gadget_correction_rows",
            "dense_over_compact_plus_minimal",
            "dense_over_compact_plus_ks_like",
            "minimal_status",
            "ks_like_status",
        ],
    )
    write_csv(
        NOISE_CSV,
        noise_rows,
        [
            "r",
            "cmux_steps_binary_set_2_3_2048",
            "min_corrections_per_cmux",
            "rho_sigma_correction_over_baseline_step",
            "per_step_sigma_multiplier",
            "variance_multiplier",
            "status",
            "interpretation",
        ],
    )
    write_csv(ROUTE_CSV, route_rows, ["route", "t4_status", "latency_status", "noise_status", "implementation_permission", "next_action"])
    write_csv(SUMMARY_CSV, summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    write_docs(summary_rows, latency_rows, resource_rows, noise_rows, route_rows)
    update_global_docs()
    write_artifacts(
        [
            OUT_MD,
            PLAN_MD,
            THEORY_MD,
            VARIANT_MD,
            SUMMARY_CSV,
            LATENCY_CSV,
            RESOURCE_CSV,
            NOISE_CSV,
            ROUTE_CSV,
            Path(__file__),
        ]
    )
    print(DECISION)


if __name__ == "__main__":
    main()
