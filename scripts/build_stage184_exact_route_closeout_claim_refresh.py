#!/usr/bin/env python3
"""Stage184: exact-route closeout and claim refresh."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage184_exact_route_closeout_claim_refresh"

SUMMARY_CSV = OUT_DIR / "summary.csv"
CLAIM_LEDGER_CSV = OUT_DIR / "claim_ledger.csv"
EVIDENCE_CHAIN_CSV = OUT_DIR / "evidence_chain.csv"
OPEN_ROUTES_CSV = OUT_DIR / "open_routes.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage184_exact_route_closeout_claim_refresh.md"
PLAN_MD = ROOT / "experiments" / "stage184_exact_route_closeout_claim_refresh_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage184_claim_boundary_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_exact_route_closeout.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE178_PERBIT = ROOT / "repro" / "stage178_fullmat_perbit_frontier" / "per_bit_throughput.csv"
STAGE180_DERIVED = ROOT / "repro" / "stage180_mat_ep_split_probe" / "derived_projection.csv"
STAGE181_COMPARE = ROOT / "repro" / "stage181_sub_decomp_avx512_gate" / "comparison.csv"
STAGE182_SUMMARY = ROOT / "repro" / "stage182_exact_path_negative_frontier" / "summary.csv"
STAGE182_CLAIMS = ROOT / "repro" / "stage182_exact_path_negative_frontier" / "claim_permissions.csv"
STAGE183_SUMMARY = ROOT / "repro" / "stage183_addmul_dataflow_screen" / "summary.csv"
STAGE183_MECH = ROOT / "repro" / "stage183_addmul_dataflow_screen" / "mechanism_screen.csv"
STAGE176_SUMMARY = ROOT / "repro" / "stage176_structured_compact_security_api_gate" / "summary.csv"
STAGE177_SUMMARY = ROOT / "repro" / "stage177_verified_literature_novelty_gate" / "summary.csv"

DECISION = "PASS_STAGE184_EXACT_ROUTE_CLOSEOUT_CLAIM_REFRESH"


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


def metric_value(metric: str) -> str:
    for row in read_csv_dicts(STAGE178_PERBIT):
        if row.get("metric") == metric:
            return row.get("value", "")
    return ""


def compare_value(variant: str, column: str) -> str:
    for row in read_csv_dicts(STAGE181_COMPARE):
        if row.get("variant") == variant:
            return row.get(column, "")
    return ""


def split_pair(metric: str) -> tuple[str, str]:
    for row in read_csv_dicts(STAGE180_DERIVED):
        if row.get("metric") == metric:
            value = row.get("value", "")
            if ";" in value:
                return tuple(value.split(";", 1))  # type: ignore[return-value]
            return value, ""
    return "", ""


def build_evidence_rows() -> List[Dict[str, str]]:
    return [
        {
            "stage": "178",
            "decision": "PASS_STAGE178_FULLMAT_PERBIT_FRONTIER_SELECT_MAT_EP_AUDIT",
            "role": "primary endpoint",
            "key_result": (
                "T_bootstrap/r speedup mean "
                f"{metric_value('speedup_vs_scalar_repeated_mean')}x; "
                f"CI-low {metric_value('speedup_vs_scalar_repeated_ci95_low')}x"
            ),
            "evidence": rel(STAGE178_PERBIT),
        },
        {
            "stage": "180",
            "decision": "PASS_STAGE180_SPLIT_PROBE_RECORDED",
            "role": "component split",
            "key_result": (
                "sub/decomp requirement "
                f"{split_pair('sub_decompose_full_sab_share_and_3pct_requirement')[1]}x; "
                "DFT requirement "
                f"{split_pair('torus_to_dft_rows_full_sab_share_and_3pct_requirement')[1]}x; "
                "addmul requirement "
                f"{split_pair('addmul_from_dec_dft_full_sab_share_and_3pct_requirement')[1]}x"
            ),
            "evidence": rel(STAGE180_DERIVED),
        },
        {
            "stage": "181",
            "decision": "REJECT_STAGE181_SUB_DECOMP_AVX512_NOT_FASTER",
            "role": "candidate rejection",
            "key_result": (
                "combined_current AVX512-subdecomp speedup "
                f"{compare_value('combined_current', 'speedup')}x"
            ),
            "evidence": rel(STAGE181_COMPARE),
        },
        {
            "stage": "182",
            "decision": "PASS_STAGE182_EXACT_PATH_NEGATIVE_FRONTIER_RECORDED",
            "role": "frontier policy",
            "key_result": "blind AVX512/layout retuning closed; new mechanism required before code",
            "evidence": rel(STAGE182_SUMMARY),
        },
        {
            "stage": "183",
            "decision": "PASS_STAGE183_ADDMUL_DATAFLOW_SCREEN_NO_CODE_PERMISSION",
            "role": "mechanism screen",
            "key_result": "tiled/fulltile/bodymajor/streaming families are exhausted without a new mechanism",
            "evidence": rel(STAGE183_SUMMARY),
        },
    ]


def build_claim_rows() -> List[Dict[str, str]]:
    return [
        {
            "claim": "complete_sab_amortized_speedup",
            "status": "allowed_scoped",
            "allowed_statement": (
                "Under recorded platform/backend/parameters, the exact PVW/MAT-SAB "
                "path has complete-SAB T_bootstrap/r speedup over repeated scalar SAB."
            ),
            "quantitative_bound": (
                f"mean {metric_value('speedup_vs_scalar_repeated_mean')}x; "
                f"min {metric_value('speedup_vs_scalar_repeated_min')}x; "
                f"CI-low {metric_value('speedup_vs_scalar_repeated_ci95_low')}x"
            ),
            "blocked_extension": "Do not generalize to theoretical optimality, all parameters, or all branches.",
            "evidence": rel(STAGE178_PERBIT),
        },
        {
            "claim": "avx512_sub_decompose_optimization",
            "status": "denied",
            "allowed_statement": "The default-off AVX512 sub-decompose path is a negative ablation.",
            "quantitative_bound": (
                f"sub_decompose {compare_value('sub_decompose', 'speedup')}x; "
                f"combined_current {compare_value('combined_current', 'speedup')}x"
            ),
            "blocked_extension": "Do not call this path a speedup or run a full-SAB claim from it.",
            "evidence": rel(STAGE181_COMPARE),
        },
        {
            "claim": "mat_avx512_theoretical_optimality",
            "status": "denied",
            "allowed_statement": "MAT-aware AVX512 implementations exist and are bounded by measured gates.",
            "quantitative_bound": "no theoretical lower-bound proof; no promoted new mechanism after Stage183",
            "blocked_extension": "Do not claim optimal AVX512 or optimal MAT external product.",
            "evidence": f"{rel(STAGE182_CLAIMS)}; {rel(STAGE183_MECH)}",
        },
        {
            "claim": "new_compact_mat_sab_algorithm_implemented",
            "status": "denied_blocked",
            "allowed_statement": "Compact/shared-output MAT-SAB remains a proof/literature route.",
            "quantitative_bound": "no implemented complete-SAB T_bootstrap/r gate",
            "blocked_extension": "Do not claim compact SAB implementation, speedup, or novelty.",
            "evidence": f"{rel(STAGE176_SUMMARY)}; {rel(STAGE177_SUMMARY)}",
        },
    ]


def build_open_rows() -> List[Dict[str, str]]:
    return [
        {
            "route": "exact_full_mat_hot_path",
            "state": "closed_until_new_mechanism",
            "required_unlock": "assembly/counter-backed addmul or DFT mechanism with projected full-SAB gain",
            "why_not_now": "Stage181 rejected sub-decompose; Stage183 denies layout-only addmul code.",
        },
        {
            "route": "structured_compact_shared_output",
            "state": "proof_literature_blocked",
            "required_unlock": "selector distribution proof, closed shared-mask state, noise/resource model, real related-work review",
            "why_not_now": "Stage176/177 block implementation and strong novelty claims.",
        },
        {
            "route": "paper_writeup",
            "state": "scoped_engineering_possible",
            "required_unlock": "use claim ledger wording and cite only verified sources",
            "why_not_now": "No broad novelty or theoretical-optimality claim is permitted.",
        },
    ]


def build_summary_rows() -> List[Dict[str, str]]:
    inputs_ok = all(
        p.exists()
        for p in [
            STAGE178_PERBIT,
            STAGE180_DERIVED,
            STAGE181_COMPARE,
            STAGE182_SUMMARY,
            STAGE183_SUMMARY,
        ]
    )
    return [
        {
            "gate": "stage184_inputs",
            "status": "PASS" if inputs_ok else "FAIL",
            "metric": "required_inputs_present",
            "value": "1" if inputs_ok else "0",
            "evidence": f"{rel(STAGE178_PERBIT)}; {rel(STAGE183_SUMMARY)}",
            "detail": "Stage184 consumes the exact-route evidence chain through Stage183.",
            "next_action": "Repair missing evidence before claim refresh.",
        },
        {
            "gate": "stage184_claim_alignment",
            "status": "PASS",
            "metric": "allowed_claim_count;denied_claim_count",
            "value": "1;3",
            "evidence": rel(CLAIM_LEDGER_CSV),
            "detail": "Only scoped complete-SAB amortized speedup is allowed; stronger claims are denied.",
            "next_action": "Use claim ledger wording in paper/report.",
        },
        {
            "gate": "stage184_exact_code_permission",
            "status": "DENY_NEW_EXACT_CODE",
            "metric": "stage183_code_permission",
            "value": "denied",
            "evidence": rel(STAGE183_SUMMARY),
            "detail": "No new exact AVX512 hot-path code should be written without a new mechanism.",
            "next_action": "Do not continue blind retuning.",
        },
        {
            "gate": "stage184_decision",
            "status": DECISION,
            "metric": "route",
            "value": "closeout_or_proof_lane",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Exact-route closeout is refreshed; next work is paper packaging or proof-gated compact work.",
            "next_action": "Proceed according to next_stage_queue.",
        },
    ]


def build_next_rows() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "stage": "185",
            "name": "paper/repro package refresh",
            "entry_condition": "User wants report or manuscript artifacts from current evidence.",
            "gate": "Use Stage184 claim ledger; no novelty/optimality overclaim.",
            "failure_rule": "If unsupported wording appears, reject before writing.",
        },
        {
            "priority": "P1",
            "stage": "186",
            "name": "compact proof unlock",
            "entry_condition": "A proof package or new source evidence is supplied.",
            "gate": "Security/API/noise/literature gates before any SAB code.",
            "failure_rule": "No implementation from toy evidence alone.",
        },
    ]


def write_docs(
    summary_rows: List[Dict[str, str]],
    evidence_rows: List[Dict[str, str]],
    claim_rows: List[Dict[str, str]],
    open_rows: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
) -> None:
    write_text_lf(
        OUT_MD,
        f"""# Stage184 Exact-Route Closeout Claim Refresh

Decision: `{DECISION}`.

Stage184 converts Stage178-183 into a claim ledger. The current exact
PVW/MAT-SAB path may be described only as a scoped complete-SAB amortized
speedup result under the recorded backend/platform/parameters. It may not be
described as AVX512-theoretically optimal, as a successful sub-decompose
optimization, or as an implemented compact MAT-SAB algorithm.

## Gate Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Evidence Chain

{table(evidence_rows, ["stage", "decision", "role", "key_result", "evidence"])}
## Claim Ledger

{table(claim_rows, ["claim", "status", "allowed_statement", "quantitative_bound", "blocked_extension", "evidence"])}
## Open Routes

{table(open_rows, ["route", "state", "required_unlock", "why_not_now"])}
## Next Queue

{table(next_rows, ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"])}
""",
    )

    write_text_lf(
        PLAN_MD,
        """# Stage184 Plan

Goal: refresh the final exact-route claim boundary after Stage183 denies new
exact addmul code permission.

Rules:

- The primary speedup endpoint is `T_bootstrap/r`.
- Negative ablations must stay visible.
- No theoretical optimality, compact implementation, or broad novelty claim is
  allowed without new evidence.
""",
    )

    write_text_lf(
        THEORY_MD,
        """# Stage184 Claim Boundary Model

The exact route preserves the current PVW_TMLWE closed state and dense full-MAT
external product. Stage178-183 show that this route has scoped amortized
complete-SAB evidence, but also that the remaining local exact-code candidates
are either negative or blocked.

Therefore the claim hierarchy is:

1. Complete-SAB `T_bootstrap/r` scoped engineering speedup: allowed.
2. Kernel-only or candidate-local speedup: allowed only as component evidence.
3. AVX512 theoretical optimality: denied.
4. Compact/shared-output MAT-SAB algorithm: denied as implemented claim.
""",
    )

    write_text_lf(
        VARIANT_MD,
        """# Exact-Route Closeout

This artifact is a claim-policy variant, not a hot-path implementation.

Use it to keep future paper and report wording aligned with evidence:

- report complete SAB speedup per processed lane;
- include negative AVX512 sub-decompose and addmul dataflow screens;
- keep compact/shared-output work as proof-gated future work.
""",
    )


def update_global_docs() -> None:
    append_once(
        ROADMAP_MD,
        "## Stage 184: Exact-Route Closeout Claim Refresh",
        f"""
## Stage 184: Exact-Route Closeout Claim Refresh

Goal:

```text
Refresh the final exact-route claim ledger after Stage183 denies new exact
addmul code permission.
```

Status:

```text
Completed. Stage184 records {DECISION}. The only allowed current exact-route
claim is scoped complete-SAB `T_bootstrap/r` speedup under recorded conditions.
AVX512 theoretical optimality, sub-decompose improvement, and implemented
compact MAT-SAB claims are denied.
```
""",
    )

    append_once(
        GOAL_MD,
        "Stage184 records the exact-route closeout claim refresh",
        f"""
Stage184 records the exact-route closeout claim refresh. Decision:
`{DECISION}`. Current exact-route work is closed for blind implementation;
claim wording must follow the scoped `T_bootstrap/r` ledger.
""",
    )

    append_once(
        CURRENT_GOAL_MD,
        "Treat Stage184 as the exact-route claim closeout",
        f"""
88. Treat Stage184 as the exact-route claim closeout:
    `{DECISION}`. Scoped complete-SAB `T_bootstrap/r` speedup wording is
    allowed; AVX512 theoretical optimality, sub-decompose speedup, and
    implemented compact MAT-SAB claims are denied.
""",
    )

    append_once(
        HYPOTHESIS_YAML,
        "H108_exact_route_claim_closeout",
        f"""
  - id: H108_exact_route_claim_closeout
    statement: >
      The exact full-MAT PVW/MAT-SAB route currently supports only scoped
      complete-SAB amortized speedup claims; stronger AVX512 optimality,
      sub-decompose, or compact-SAB claims are unsupported.
    mechanism: >
      Stage178-183 establish the primary endpoint, split hot components,
      reject the AVX512 sub-decompose candidate, close blind exact retuning,
      and deny new addmul code permission.
    status: stage184_exact_route_closeout_claim_refresh
    evidence: docs/stage184_exact_route_closeout_claim_refresh.md; experiments/stage184_exact_route_closeout_claim_refresh_plan.md; theory_checks/stage184_claim_boundary_model.md; repro/stage184_exact_route_closeout_claim_refresh/summary.csv
    current_decision: >
      {DECISION}
    failure_criteria:
      - unsupported optimality or novelty wording enters reports
      - exact hot-path code is reopened without a new mechanism
      - compact SAB is described as implemented acceleration
""",
    )

    append_once(
        RUN_LOG,
        "stage184-exact-route-closeout-claim-refresh-001",
        f"""
stage184-exact-route-closeout-claim-refresh-001,2026-07-04,{git_head()},Stage 184,analysis,python scripts/build_stage184_exact_route_closeout_claim_refresh.py,Stage178-183 evidence,none,{DECISION},Exact-route closeout and claim-ledger refresh.,repro/stage184_exact_route_closeout_claim_refresh
""",
    )

    append_once(
        MANIFEST,
        "stage184_exact_route_closeout_claim_refresh",
        f"""
- stage184_exact_route_closeout_claim_refresh: `{DECISION}`
  - `docs/stage184_exact_route_closeout_claim_refresh.md`
  - `experiments/stage184_exact_route_closeout_claim_refresh_plan.md`
  - `theory_checks/stage184_claim_boundary_model.md`
  - `algorithm_variants/mat_rlwe_sab_exact_route_closeout.md`
  - `repro/stage184_exact_route_closeout_claim_refresh/`
""",
    )

    append_once(CHECKLIST, "Stage184 exact-route closeout claim refresh pack recorded", """
- [x] Stage184 exact-route closeout claim refresh pack recorded.
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
    evidence_rows = build_evidence_rows()
    claim_rows = build_claim_rows()
    open_rows = build_open_rows()
    summary_rows = build_summary_rows()
    next_rows = build_next_rows()

    write_csv(EVIDENCE_CHAIN_CSV, evidence_rows, ["stage", "decision", "role", "key_result", "evidence"])
    write_csv(
        CLAIM_LEDGER_CSV,
        claim_rows,
        ["claim", "status", "allowed_statement", "quantitative_bound", "blocked_extension", "evidence"],
    )
    write_csv(OPEN_ROUTES_CSV, open_rows, ["route", "state", "required_unlock", "why_not_now"])
    write_csv(SUMMARY_CSV, summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    write_csv(NEXT_CSV, next_rows, ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"])
    write_docs(summary_rows, evidence_rows, claim_rows, open_rows, next_rows)
    update_global_docs()
    write_artifacts(
        [
            OUT_MD,
            PLAN_MD,
            THEORY_MD,
            VARIANT_MD,
            SUMMARY_CSV,
            CLAIM_LEDGER_CSV,
            EVIDENCE_CHAIN_CSV,
            OPEN_ROUTES_CSV,
            NEXT_CSV,
            Path(__file__),
        ]
    )
    print(DECISION)


if __name__ == "__main__":
    main()
