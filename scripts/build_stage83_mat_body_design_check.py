#!/usr/bin/env python3
"""Build the Stage83 MAT-body reduction theory/design check.

Stage83 is a non-hot-path design gate. It converts the Stage82 post-H11
profile into a falsifiable next-step plan without changing scalar SAB,
default sab_pvw_* behavior, or MAT_TRGSW key format.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage83_mat_body_design_check"
STAGE82_DECISION = ROOT / "repro" / "stage82_post_h11_profile" / "decision.csv"
STAGE82_PROFILE = ROOT / "repro" / "stage82_post_h11_profile" / "profile_metrics.csv"
STAGE81 = ROOT / "repro" / "stage81_next_variant_triage.csv"
H11_THEORY = ROOT / "theory_checks" / "h11_rgt4_fused_mat_kernel.md"
H13_THEORY = ROOT / "theory_checks" / "h13_mat_body_reduction_design.md"
H13_VARIANT = ROOT / "algorithm_variants" / "pvw_sab_h13_mat_body_design.md"
OUT_CANDIDATES = OUT_DIR / "candidates.csv"
OUT_DECISION = OUT_DIR / "decision.csv"
OUT_MD = ROOT / "docs" / "stage83_mat_body_design_check_log.md"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def by_key(path: Path, key: str) -> Dict[str, Dict[str, str]]:
    return {row.get(key, ""): row for row in read_csv(path)}


def fnum(row: Dict[str, str], key: str) -> float:
    try:
        return float(row.get(key, "") or 0.0)
    except ValueError:
        return 0.0


def passfail(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def row(
    gate: str,
    status: str,
    metric: str,
    value: str,
    evidence: str,
    detail: str,
    next_action: str,
) -> Dict[str, str]:
    return {
        "gate": gate,
        "status": status,
        "metric": metric,
        "value": value,
        "evidence": evidence,
        "detail": detail,
        "next_action": next_action,
    }


def candidate(
    candidate_id: str,
    status: str,
    mechanism: str,
    expected_effect: str,
    risk: str,
    required_gate: str,
    next_stage: str,
) -> Dict[str, str]:
    return {
        "candidate_id": candidate_id,
        "status": status,
        "mechanism": mechanism,
        "expected_effect": expected_effect,
        "risk": risk,
        "required_gate": required_gate,
        "next_stage": next_stage,
    }


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def amdahl(local_share: float, local_speedup: float) -> float:
    if local_share <= 0 or local_speedup <= 0:
        return 1.0
    return 1.0 / ((1.0 - local_share) + local_share / local_speedup)


def build_candidates(profile: Dict[str, str]) -> List[Dict[str, str]]:
    r = int(float(profile.get("r", "6") or 6))
    outputs = r + 1
    rows = outputs
    current_tile = 4
    current_tiles = math.ceil(outputs / current_tile)
    current_dec_load_units = 2 * rows * current_tiles
    full_tile_dec_load_units = 2 * rows
    dec_load_reduction = (
        1.0 - (full_tile_dec_load_units / current_dec_load_units)
        if current_dec_load_units
        else 0.0
    )
    return [
        candidate(
            "H13-C1-r6-full-output-tile-sweep",
            "SELECT_FOR_STAGE84_PREFLIGHT",
            (
                "For k=1,l=1,r=6, test a dedicated output tile that updates all "
                "7 MAT outputs for one coefficient block before advancing rows."
            ),
            (
                f"Dec-row vector load units per coefficient can drop from "
                f"{current_dec_load_units} to {full_tile_dec_load_units} "
                f"({dec_load_reduction:.1%}) for r={r}; dense m^2 selector "
                "loads/FMA count remains unchanged."
            ),
            (
                "Higher accumulator register pressure may spill; must stay behind "
                "an explicit flag and be rejected if objdump/perf or microbench "
                "shows spill-driven regression."
            ),
            (
                "identity-lane correctness; DFT-output and full-output MAT "
                "microbench; objdump/native-counter spill/load audit when "
                "available; non-instrumented full-SAB A/B only if kernel positive"
            ),
            "Stage84",
        ),
        candidate(
            "H13-C2-row-streamed-decompose-dft",
            "DEFER_AFTER_C1",
            (
                "Stream one decomposed row through DFT and MAT accumulation to "
                "reduce dec_dft materialization lifetime."
            ),
            (
                "May reduce scratch traffic, but it does not reduce dense m^2 "
                "selector loads or FMA count."
            ),
            (
                "Touches the external-product scratch/API lifetime and may disturb "
                "small-r paths; lower priority unless C1 is neutral and profiles "
                "still show dec/materialization cost."
            ),
            "isolated MAT equivalence for r=1/2/4/6; full-SAB A/B if positive",
            "Stage86 candidate",
        ),
        candidate(
            "H13-C3-body-major-or-coeff-blocked-key-layout",
            "EXPERIMENT_ONLY_LAYOUT_RISK",
            (
                "Change MAT_TRGSW_DFT storage order so selector rows/outputs are "
                "loaded in the order consumed by fused body kernels."
            ),
            (
                "Could improve cache locality, especially for r>=6, but does not "
                "change dense arithmetic."
            ),
            (
                "Key-format change or conversion layer risk; cannot replace "
                "default key layout without a separate compatibility/resource gate."
            ),
            "new-key-format compatibility test; keygen/resource matrix; full-SAB A/B",
            "external or later experimental branch",
        ),
        candidate(
            "H13-C4-sparse-selector-skip",
            "BLOCKED_SECURITY_KEY_FORMAT",
            (
                "Skip dense MAT row-output products using SAB selector structure."
            ),
            (
                "Only candidate with possible arithmetic-count reduction below m^2, "
                "but encrypted selector zeros are still dense ciphertext objects."
            ),
            (
                "Requires plaintext/secret-dependent metadata or a new key format; "
                "blocked until a leakage and security argument exists."
            ),
            "formal key/security design before code",
            "blocked",
        ),
        candidate(
            "H13-C5-cmux-materialization-second-pass",
            "SECONDARY_AFTER_MAT_PREFLIGHT",
            (
                "Revisit from_DFT/add/sub lifecycle only after the MAT body "
                "preflight, using Stage82 non-MAT shares as a secondary target."
            ),
            (
                "Stage82 non-MAT body share is material, but Stage18/23 local "
                "epilogue fusion was neutral."
            ),
            (
                "Risk of repeating a previously neutral direction unless the new "
                "design reduces lifetime across a larger schedule window."
            ),
            "per-CMUX phase equivalence; non-instrumented full-SAB A/B",
            "Stage86 fallback",
        ),
        candidate(
            "H13-C6-native-counter-optimality-check",
            "EXTERNAL_BLOCKED_NATIVE_PERF",
            (
                "Use native perf counters to decide whether MAT-aware AVX512 is "
                "load/store, FMA, cache, or spill limited."
            ),
            "Upgrades attribution confidence, not algorithmic speed by itself.",
            "Current WSL2 environment lacks perf; cannot be used as local gate now.",
            "native Linux or perf-enabled WSL with hardware counters",
            "external unlock",
        ),
    ]


def build_rows() -> List[Dict[str, str]]:
    stage81 = by_key(STAGE81, "gate")
    stage82 = by_key(STAGE82_DECISION, "gate")
    profile_rows = read_csv(STAGE82_PROFILE)
    profile = profile_rows[0] if profile_rows else {}
    candidates = build_candidates(profile)
    write_csv(
        OUT_CANDIDATES,
        candidates,
        [
            "candidate_id",
            "status",
            "mechanism",
            "expected_effect",
            "risk",
            "required_gate",
            "next_stage",
        ],
    )

    required = [STAGE81, STAGE82_DECISION, STAGE82_PROFILE, H11_THEORY, H13_THEORY, H13_VARIANT]
    missing = [p.relative_to(ROOT).as_posix() for p in required if not p.exists()]
    stage81_ok = (
        stage81.get("stage81_decision", {}).get("status")
        == "PASS_STAGE81_NEXT_VARIANT_TRIAGE_PROFILE_FIRST_NO_CODE_PROMOTION"
    )
    stage82_ok = (
        stage82.get("stage82_decision", {}).get("status")
        == "PASS_STAGE82_POST_H11_PROFILE_MAT_BODY_PRIMARY"
    )
    mat_share = fnum(profile, "mat_ep_share_of_full")
    non_mat_share = fnum(profile, "non_mat_share_of_full")
    from_dft_share = fnum(profile, "from_dft_share_of_full")
    add_share = fnum(profile, "cmux_add_share_of_full")
    sub_share = fnum(profile, "cmux_sub_share_of_full")
    r = profile.get("r", "6")
    selected = next(c for c in candidates if c["candidate_id"] == "H13-C1-r6-full-output-tile-sweep")
    selected_ok = selected["status"] == "SELECT_FOR_STAGE84_PREFLIGHT"

    amdahl_110 = amdahl(mat_share, 1.10)
    amdahl_120 = amdahl(mat_share, 1.20)
    amdahl_150 = amdahl(mat_share, 1.50)

    rows = [
        row(
            "stage83_inputs_available",
            passfail(not missing and stage81_ok and stage82_ok and bool(profile_rows)),
            "stage81;stage82;profile;theory_docs",
            f"missing={missing}; stage81={stage81_ok}; stage82={stage82_ok}; profile_rows={len(profile_rows)}",
            "; ".join(p.relative_to(ROOT).as_posix() for p in required),
            "Stage83 has the Stage81 profile-first and Stage82 MAT-body-primary preconditions."
            if not missing and stage81_ok and stage82_ok and bool(profile_rows)
            else "Restore Stage81/Stage82/H13 inputs before selecting a new local candidate.",
            "Do not implement a MAT body variant until all inputs are present.",
        ),
        row(
            "stage83_profile_bound",
            "PASS_MAT_BODY_PRIMARY_BUT_NOT_EXCLUSIVE" if mat_share >= 0.45 and non_mat_share > 0 else "FAIL_PROFILE_BOUND",
            "r;mat_ep_share;from_dft_share;add_share;sub_share;non_mat_share",
            f"{r};{mat_share:.6f};{from_dft_share:.6f};{add_share:.6f};{sub_share:.6f};{non_mat_share:.6f}",
            STAGE82_PROFILE.relative_to(ROOT).as_posix(),
            "MAT EP is the largest single Stage82 component, while non-MAT body work still caps overall gains.",
            "Use Amdahl bounds when judging any kernel-only improvement.",
        ),
        row(
            "stage83_amdahl_bound",
            "PASS_RECORDED",
            "mat_body_local_speedup_to_full_body_multiplier",
            f"1.10->{amdahl_110:.6f};1.20->{amdahl_120:.6f};1.50->{amdahl_150:.6f}",
            STAGE82_PROFILE.relative_to(ROOT).as_posix(),
            "A MAT-body-only win has a bounded complete-body effect because Stage82 non-MAT share is above half.",
            "Require full SAB A/B before claiming bootstrapping speedup.",
        ),
        row(
            "stage83_security_boundary",
            "PASS_BLOCK_SPARSE_SKIP_WITHOUT_KEY_SECURITY_DESIGN",
            "blocked_candidate",
            "H13-C4-sparse-selector-skip",
            f"{H13_THEORY.relative_to(ROOT).as_posix()}; {H13_VARIANT.relative_to(ROOT).as_posix()}",
            "Arithmetic-count reduction below dense m^2 is not locally authorized because encrypted selectors remain ciphertexts.",
            "Do not implement selector skipping without a new key-format/security proof.",
        ),
        row(
            "stage83_candidate_screen",
            "SELECT_STAGE84_R6_TILE_SWEEP_PREFLIGHT" if selected_ok else "FAIL_NO_SELECTED_CANDIDATE",
            "selected_candidate",
            selected["candidate_id"],
            OUT_CANDIDATES.relative_to(ROOT).as_posix(),
            "The selected next local candidate is low key-format risk and tests a concrete MAT-body load/reuse hypothesis.",
            "Stage84 should implement only an explicit preflight flag or microbench path, then stop at promote/neutral/reject gates.",
        ),
    ]
    failures = [item["gate"] for item in rows if item["status"].startswith("FAIL")]
    rows.append(
        row(
            "stage83_decision",
            "PASS_STAGE83_MAT_BODY_DESIGN_CHECK_SELECT_R6_TILE_SWEEP_PREFLIGHT"
            if not failures
            else "FAIL_STAGE83_MAT_BODY_DESIGN_CHECK",
            "decision",
            "",
            f"{OUT_DECISION.relative_to(ROOT).as_posix()}; {OUT_CANDIDATES.relative_to(ROOT).as_posix()}",
            "Stage83 completes the MAT body theory/design check and selects Stage84 preflight only."
            if not failures
            else f"failed_gates={failures}",
            "Proceed to Stage84 only with explicit flags and no scalar/default behavior change."
            if not failures
            else "Fix failed gates and rerun Stage83.",
        )
    )
    return rows


def write_md(rows: List[Dict[str, str]]) -> None:
    candidates = read_csv(OUT_CANDIDATES)
    decision = rows[-1]["status"] if rows else "MISSING"
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stage83 MAT Body Design Check Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage83 answers whether the post-Stage82 local continuation has a complete",
        "route to the final SAB optimization goal. It is a theory/design and",
        "candidate-screening stage only; it does not change scalar SAB, default",
        "`sab_pvw_*`, key format, or hot-path code.",
        "",
        "## Gates",
        "",
        "| gate | status | metric | value | evidence | detail | next_action |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in rows:
        lines.append(
            "| {gate} | {status} | {metric} | {value} | {evidence} | {detail} | {next_action} |".format(
                **{k: item[k].replace("|", "\\|") for k in item}
            )
        )
    lines.extend(
        [
            "",
            "## Candidate Matrix",
            "",
            "| candidate | status | mechanism | expected effect | risk | gate | next stage |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for item in candidates:
        lines.append(
            "| {candidate_id} | {status} | {mechanism} | {expected_effect} | {risk} | {required_gate} | {next_stage} |".format(
                **{k: item[k].replace("|", "\\|") for k in item}
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"`{decision}`",
            "",
            "The Stage84 entry is deliberately narrow: test the r=6 full-output tile",
            "preflight behind an explicit flag or isolated harness. A positive kernel",
            "result is not a SAB claim unless non-instrumented complete-SAB A/B,",
            "correctness, noise, resource, and closure gates pass.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> int:
    rows = build_rows()
    write_csv(
        OUT_DECISION,
        rows,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_md(rows)
    decision = rows[-1]["status"]
    print(f"Wrote {OUT_CANDIDATES.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_DECISION.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    print(f"Stage83 MAT body design check: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
