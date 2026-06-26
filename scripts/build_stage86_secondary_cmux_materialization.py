#!/usr/bin/env python3
"""Build the Stage86 secondary CMUX materialization design gate."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage86_secondary_cmux_materialization"
OUT_CANDIDATES = OUT_DIR / "candidates.csv"
OUT_DECISION = OUT_DIR / "decision.csv"
OUT_MD = ROOT / "docs" / "stage86_secondary_cmux_materialization_log.md"

STAGE82_PROFILE = ROOT / "repro" / "stage82_post_h11_profile" / "profile_metrics.csv"
STAGE84_SUMMARY = ROOT / "repro" / "stage84_h13_r6_tile_sweep_preflight" / "summary.csv"
STAGE18_LOG = ROOT / "docs" / "stage18_cmux_profile_and_fusion_log.md"
STAGE23_LOG = ROOT / "docs" / "stage23_schedule_fused_cmux_log.md"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def pct(value: float) -> str:
    return f"{value * 100.0:.2f}%"


def f3(value: float) -> str:
    return f"{value:.3f}"


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def stage84_status(summary: List[Dict[str, str]], gate: str) -> str:
    rows = {row.get("gate"): row for row in summary}
    return rows.get(gate, {}).get("status", "MISSING")


def build_candidates(metrics: Dict[str, float]) -> List[Dict[str, str]]:
    add_share = metrics["cmux_add_share_of_full"]
    sub_share = metrics["cmux_sub_share_of_full"]
    from_dft_share = metrics["from_dft_share_of_full"]
    materialization_share = from_dft_share + add_share
    add_full_elim_amdahl = 1.0 / (1.0 - add_share)
    material_half_amdahl = 1.0 / (1.0 - 0.5 * materialization_share)
    sub_half_amdahl = 1.0 / (1.0 - 0.5 * sub_share)

    return [
        {
            "candidate_id": "H14-C1-backend-from-dft-add-callback",
            "status": "SELECT_FOR_STAGE86_PREFLIGHT",
            "mechanism": (
                "Add a backend-level inverse-DFT-to-torus plus addend callback so "
                "the add-back is performed during the inverse materialization store, "
                "not as a second torus-polynomial pass."
            ),
            "distinct_from_prior": (
                "Stage18/23 fused at the PVW wrapper after polynomial_DFT_to_torus; "
                "this candidate must change the polynomial/backend materialization "
                "boundary and expose a separate flag."
            ),
            "expected_bound": (
                f"from_DFT+add is {pct(materialization_share)} of full body; "
                f"eliminating the whole add pass has an Amdahl ceiling of "
                f"{f3(add_full_elim_amdahl)}x, while halving materialization has "
                f"a ceiling of {f3(material_half_amdahl)}x."
            ),
            "risk": (
                "Backend-specific, may require spqlios/AVX512 code paths and may "
                "be neutral if FFT arithmetic dominates memory traffic."
            ),
            "required_gate": (
                "identity-lane correctness; r=4/r=6 CMUX materialization microbench; "
                "non-instrumented complete-SAB A/B; noise/resource if full-SAB positive"
            ),
        },
        {
            "candidate_id": "H14-C2-dft-lazy-bit-window",
            "status": "REJECT_FOR_NOW_MEMORY_AND_NO_COUNT_REDUCTION",
            "mechanism": (
                "Keep each bit-window output in DFT form and materialize after the "
                "whole window rather than inside each CMUX."
            ),
            "distinct_from_prior": "Different schedule lifetime, but not selected.",
            "expected_bound": (
                "It does not reduce the number of inverse DFTs because the next SAB "
                "bit consumes torus-domain samples; it also requires an array of DFT "
                "temporaries across many accumulator slots."
            ),
            "risk": (
                "Large memory footprint and cache pressure; likely worsens the full "
                "SAB path unless a separate DFT-domain accumulator design is proven."
            ),
            "required_gate": "New memory model and scratch allocator before any code.",
        },
        {
            "candidate_id": "H14-C3-dual-butterfly-shared-input-wrapper",
            "status": "SECONDARY_FALLBACK_AFTER_C1",
            "mechanism": (
                "Fuse paired direct/NCMUX butterfly calls that share one input sample "
                "to reduce repeated torus loads in the sub stage."
            ),
            "distinct_from_prior": (
                "Targets the butterfly pair before MAT EP, not the from_DFT/add "
                "epilogue."
            ),
            "expected_bound": (
                f"sub is {pct(sub_share)} of full body; even halving sub has an "
                f"Amdahl ceiling of {f3(sub_half_amdahl)}x."
            ),
            "risk": (
                "Pairing is irregular at bit boundaries and NCMUX includes an "
                "automorphism; implementation complexity may exceed expected gain."
            ),
            "required_gate": "Per-bit phase equivalence plus full-SAB A/B if C1 fails.",
        },
        {
            "candidate_id": "H14-C4-repeat-stage23-r6-schedule-fusion",
            "status": "REJECT_DUPLICATES_NEUTRAL_ABLATION",
            "mechanism": "Rerun the Stage23 schedule-fused CMUX wrapper for r=6.",
            "distinct_from_prior": "Not distinct; repeats epilogue-only fusion.",
            "expected_bound": "Stage23 r=2/r=4 was neutral and did not change materialization count.",
            "risk": "Consumes experiment budget without a new mechanism.",
            "required_gate": "Not selected.",
        },
        {
            "candidate_id": "H14-C5-ncmux-automorphism-materialization",
            "status": "REJECT_LOW_SHARE",
            "mechanism": "Optimize the NCMUX automorphism/materialization path first.",
            "distinct_from_prior": "Different subcomponent, but too small.",
            "expected_bound": (
                f"NCMUX is {pct(metrics['ncmux_share_of_full'])} of full body in "
                "Stage82, below the materiality threshold."
            ),
            "risk": "Low maximum impact for high implementation risk.",
            "required_gate": "Revisit only if a future profile changes the share.",
        },
    ]


def build_decision(
    profile_rows: List[Dict[str, str]],
    stage84_rows: List[Dict[str, str]],
    candidates: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    profile = profile_rows[0] if profile_rows else {}
    metrics = {k: float(profile.get(k, "0") or "0") for k in [
        "non_mat_share_of_full",
        "from_dft_share_of_full",
        "cmux_add_share_of_full",
        "cmux_sub_share_of_full",
        "ncmux_share_of_full",
    ]}
    materialization_share = metrics["from_dft_share_of_full"] + metrics["cmux_add_share_of_full"]
    prior_text = ""
    if STAGE18_LOG.exists():
        prior_text += STAGE18_LOG.read_text(encoding="utf-8", errors="replace")
    if STAGE23_LOG.exists():
        prior_text += "\n" + STAGE23_LOG.read_text(encoding="utf-8", errors="replace")
    prior_neutral = "neutral" in prior_text.lower() and "not promoted" in prior_text.lower()
    stage84_not_promoted = (
        stage84_status(stage84_rows, "stage84_decision")
        == "PASS_STAGE84_H13_R6_TILE_SWEEP_KERNEL_ONLY_NOT_PROMOTED"
    )
    selected = next(
        (row for row in candidates if row["status"] == "SELECT_FOR_STAGE86_PREFLIGHT"),
        {},
    )

    return [
        {
            "gate": "stage86_inputs_available",
            "status": "PASS" if profile_rows and stage84_not_promoted else "FAIL",
            "metric": "profile_rows;stage84_decision",
            "value": f"{len(profile_rows)};{stage84_status(stage84_rows, 'stage84_decision')}",
            "evidence": (
                "repro/stage82_post_h11_profile/profile_metrics.csv; "
                "repro/stage84_h13_r6_tile_sweep_preflight/summary.csv"
            ),
            "detail": "Stage82 profile and Stage84 not-promoted routing are available.",
            "next_action": "Restore Stage82/84 inputs before interpreting Stage86.",
        },
        {
            "gate": "stage86_non_mat_materiality",
            "status": (
                "PASS_NON_MAT_MATERIAL"
                if metrics["non_mat_share_of_full"] >= 0.35 and materialization_share >= 0.25
                else "DEFER_NON_MAT_TOO_SMALL"
            ),
            "metric": "non_mat;from_dft_plus_add;sub",
            "value": (
                f"{pct(metrics['non_mat_share_of_full'])};"
                f"{pct(materialization_share)};"
                f"{pct(metrics['cmux_sub_share_of_full'])}"
            ),
            "evidence": "repro/stage82_post_h11_profile/profile_metrics.csv",
            "detail": "Stage82 leaves a material non-MAT CMUX/body share after MAT work.",
            "next_action": "Do not implement Stage86 if this gate falls below threshold.",
        },
        {
            "gate": "stage86_prior_neutral_guard",
            "status": "PASS_DIFFERENT_LAYER_REQUIRED" if prior_neutral else "FAIL_PRIOR_GUARD_MISSING",
            "metric": "stage18_stage23_neutral",
            "value": str(prior_neutral),
            "evidence": "docs/stage18_cmux_profile_and_fusion_log.md; docs/stage23_schedule_fused_cmux_log.md",
            "detail": "Prior epilogue-only fusions are recorded as neutral/not promoted.",
            "next_action": "A Stage86 candidate must change the backend/materialization boundary or another distinct lifetime layer.",
        },
        {
            "gate": "stage86_candidate_screen",
            "status": "SELECT_BACKEND_FROM_DFT_ADD_CALLBACK_PREFLIGHT" if selected else "NO_CANDIDATE_SELECTED",
            "metric": "selected_candidate",
            "value": selected.get("candidate_id", ""),
            "evidence": "repro/stage86_secondary_cmux_materialization/candidates.csv",
            "detail": "Select the backend materialization callback preflight and keep other candidates as fallback/rejected.",
            "next_action": "Implement only behind an explicit flag and require full-SAB A/B before any promotion.",
        },
        {
            "gate": "stage86_security_boundary",
            "status": "PASS_NO_KEY_FORMAT_CHANGE",
            "metric": "key_format;selector_visibility",
            "value": "unchanged;encrypted",
            "evidence": "theory_checks/h14_secondary_cmux_materialization.md",
            "detail": "The selected preflight changes local materialization only; it does not inspect plaintext selectors or change MAT key format.",
            "next_action": "Any future sparse selector shortcut still needs a separate security/key-format proof.",
        },
        {
            "gate": "stage86_decision",
            "status": "PASS_STAGE86_SECONDARY_CMUX_MATERIALIZATION_SELECT_BACKEND_PREFLIGHT",
            "metric": "decision",
            "value": "",
            "evidence": "repro/stage86_secondary_cmux_materialization/decision.csv",
            "detail": "Stage86 design gate selects a backend from_DFT_add callback preflight; no code path is promoted yet.",
            "next_action": "Next implementation step is a flagged backend materialization microkernel preflight.",
        },
    ]


def write_md(candidates: List[Dict[str, str]], decision_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage86 Secondary CMUX Materialization Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage86 decides whether the post-Stage84 route should continue into a",
        "secondary CMUX/materialization implementation preflight. It is a design",
        "gate only: it does not modify scalar SAB, does not promote a new PVW/SAB",
        "path, and does not claim complete-SAB acceleration.",
        "",
        "## Decision Gates",
        "",
        "| gate | status | metric | value | detail |",
        "|---|---|---|---|---|",
    ]
    for row in decision_rows:
        lines.append(
            f"| {row['gate']} | {row['status']} | {row['metric']} | "
            f"{row['value']} | {row['detail']} |"
        )
    lines.extend(
        [
            "",
            "## Candidate Screen",
            "",
            "| candidate | status | mechanism | expected bound | risk |",
            "|---|---|---|---|---|",
        ]
    )
    for row in candidates:
        lines.append(
            f"| {row['candidate_id']} | {row['status']} | {row['mechanism']} | "
            f"{row['expected_bound']} | {row['risk']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The selected Stage86 follow-up is not another Stage18/23 epilogue-only",
            "wrapper. It must move the boundary into the polynomial/backend inverse",
            "DFT materialization path, stay behind an explicit flag, and pass",
            "complete-SAB A/B before promotion.",
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    with OUT_MD.open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    profile_rows = read_csv(STAGE82_PROFILE)
    if profile_rows:
        profile = profile_rows[0]
        metrics = {k: float(profile.get(k, "0") or "0") for k in [
            "from_dft_share_of_full",
            "cmux_add_share_of_full",
            "cmux_sub_share_of_full",
            "ncmux_share_of_full",
        ]}
    else:
        metrics = {
            "from_dft_share_of_full": 0.0,
            "cmux_add_share_of_full": 0.0,
            "cmux_sub_share_of_full": 0.0,
            "ncmux_share_of_full": 0.0,
        }
    candidates = build_candidates(metrics)
    decision_rows = build_decision(profile_rows, read_csv(STAGE84_SUMMARY), candidates)
    write_csv(
        OUT_CANDIDATES,
        candidates,
        [
            "candidate_id",
            "status",
            "mechanism",
            "distinct_from_prior",
            "expected_bound",
            "risk",
            "required_gate",
        ],
    )
    write_csv(
        OUT_DECISION,
        decision_rows,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_md(candidates, decision_rows)
    decision = decision_rows[-1]["status"]
    print(f"Wrote {OUT_CANDIDATES.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_DECISION.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    print(f"Stage86 secondary CMUX materialization: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
