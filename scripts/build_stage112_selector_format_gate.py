#!/usr/bin/env python3
"""Build Stage112 body-linear selector/key-format design gate."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage112_selector_format_gate"
SUMMARY_CSV = OUT_DIR / "summary.csv"
COUNTEREXAMPLE_CSV = OUT_DIR / "shared_mask_counterexample.csv"
CANDIDATE_CSV = OUT_DIR / "candidate_format_matrix.csv"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage112_selector_format_gate.md"
PLAN_MD = ROOT / "experiments" / "stage112_selector_format_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage112_shared_mask_body_linear_counterexample.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_body_linear_selector_format.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    rows = [{field: row.get(field, "") for field in fields} for row in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def build_counterexample() -> List[Dict[str, str]]:
    # Algebra over integers, not torus arithmetic, is enough to show the phase
    # cancellation invariant. A row whose mask contributes to the shared output
    # mask also contributes to every body phase.
    d = 2
    mask = 7
    s0 = 3
    s1 = 5
    m0 = 11
    m1 = 0
    b0 = mask * s0 + m0
    b1 = mask * s1 + m1
    dense_phase0 = d * (b0 - mask * s0)
    dense_phase1 = d * (b1 - mask * s1)
    drop_phase1 = d * (0 - mask * s1)
    return [
        {
            "case": "dense_shared_mask_row",
            "d": str(d),
            "mask": str(mask),
            "s0": str(s0),
            "s1": str(s1),
            "b0": str(b0),
            "b1": str(b1),
            "phase0": str(dense_phase0),
            "phase1": str(dense_phase1),
            "expected_phase0": str(d * m0),
            "expected_phase1": str(d * m1),
            "result": "PASS",
            "interpretation": "Dense row-output terms preserve both lane phases.",
        },
        {
            "case": "drop_offlane_body_keep_shared_mask",
            "d": str(d),
            "mask": str(mask),
            "s0": str(s0),
            "s1": str(s1),
            "b0": str(b0),
            "b1": "0",
            "phase0": str(dense_phase0),
            "phase1": str(drop_phase1),
            "expected_phase0": str(d * m0),
            "expected_phase1": str(d * m1),
            "result": "FAIL_COUNTEREXAMPLE",
            "interpretation": "Dropping the off-lane body term leaves an uncancelled shared-mask contribution.",
        },
    ]


def build_candidates() -> List[Dict[str, str]]:
    return [
        {
            "candidate": "S112-A-current-shared-mask-dense",
            "definition": "Keep current PVW_TMLWE/MAT_TRGSW_DFT format and dense row-output external product.",
            "status": "VALID_BASELINE_NOT_OPTIMAL",
            "complexity_shape": "O((k+r)^2) products for k=1,l=1",
            "next_gate": "Use as correctness baseline for any new selector format.",
        },
        {
            "candidate": "S112-B-loop-only-drop-offlane",
            "definition": "Skip off-lane body products while keeping the current shared output mask.",
            "status": "REJECTED_BY_COUNTEREXAMPLE",
            "complexity_shape": "Would be O(r), but incorrect under shared-mask phase cancellation.",
            "next_gate": "Do not implement in current MAT_TRGSW_DFT.",
        },
        {
            "candidate": "S112-C-trivial-offdiag-current-mask",
            "definition": "Make off-diagonal selector bodies trivial zero while keeping shared row masks.",
            "status": "BLOCKED_PHASE_OR_LEAKAGE",
            "complexity_shape": "Unclear; shared mask still affects all lanes.",
            "next_gate": "Requires proof that row masks do not leak selectors and all lane phases cancel.",
        },
        {
            "candidate": "S112-D-lane-local-multimask",
            "definition": "Give each output lane its own mask accumulation so off-lane body cancellation is not needed.",
            "status": "THEORY_FEASIBLE_NEW_CIPHERTEXT_TYPE",
            "complexity_shape": "Body-linear external product, but may lose shared-mask resource benefits.",
            "next_gate": "Build an r=2 algebraic simulator and key-size/resource model before C implementation.",
        },
        {
            "candidate": "S112-E-proof-carrying-mask-partition",
            "definition": "Attach selector metadata that proves which mask contributions are lane-local and skippable.",
            "status": "DESIGN_OPEN",
            "complexity_shape": "Potentially body-linear if proof rules are enforceable.",
            "next_gate": "Define metadata semantics and a deterministic r=2 equivalence harness.",
        },
    ]


def build_summary(counterexample: List[Dict[str, str]]) -> List[Dict[str, str]]:
    has_counterexample = any(row["result"] == "FAIL_COUNTEREXAMPLE" for row in counterexample)
    decision = (
        "PASS_STAGE112_SELECTOR_FORMAT_GATE_NEW_FORMAT_REQUIRED"
        if has_counterexample
        else "FAIL_STAGE112_COUNTEREXAMPLE_MISSING"
    )
    return [
        {
            "gate": "stage112_shared_mask_counterexample",
            "status": "PASS" if has_counterexample else "FAIL",
            "metric": "drop_offlane_phase_failure",
            "value": "present" if has_counterexample else "missing",
            "evidence": rel(COUNTEREXAMPLE_CSV),
            "detail": "Loop-only off-lane skipping fails when a shared mask contribution remains.",
            "next_action": "Do not implement body-linear skipping in current MAT_TRGSW_DFT.",
        },
        {
            "gate": "stage112_candidate_format_matrix",
            "status": "PASS",
            "metric": "candidate_count",
            "value": "5",
            "evidence": rel(CANDIDATE_CSV),
            "detail": "Candidate selector/key-format routes are classified.",
            "next_action": "Route only new-format candidates to finite r=2 gates.",
        },
        {
            "gate": "stage112_decision",
            "status": decision,
            "metric": "body_linear_policy",
            "value": "",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Body-linear MAT-SAB requires a new selector/key or ciphertext format, not loop-only tuning.",
            "next_action": "Open Stage113 r=2 algebraic simulator for lane-local or proof-carrying format candidates.",
        },
    ]


def write_plan() -> None:
    lines = [
        "# Stage112 Selector/Key-Format Gate Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Convert the Stage109 source-level blocker into a finite selector/key-format",
        "design gate for body-linear MAT external product.",
        "",
        "## Command",
        "",
        "```bash",
        "python scripts/build_stage112_selector_format_gate.py",
        "```",
        "",
        "## Gate",
        "",
        "- Provide a concrete shared-mask phase counterexample for loop-only",
        "  off-lane skipping.",
        "- Classify candidate new formats.",
        "- Select a finite r=2 simulator gate instead of continuing theory-only",
        "  discussion.",
    ]
    PLAN_MD.write_bytes("\n".join(lines).encode("utf-8"))


def write_theory(counterexample: List[Dict[str, str]]) -> None:
    fail = next(row for row in counterexample if row["result"] == "FAIL_COUNTEREXAMPLE")
    lines = [
        "# Stage112 Shared-Mask Body-Linear Counterexample",
        "",
        "Date: 2026-07-03",
        "",
        "## Phase Invariant",
        "",
        "For a single shared-mask row with decomposition digit `d`, mask `A`, body",
        "`B_q = A*s_q + m_q`, and lane secret `s_q`, the dense contribution to",
        "lane `q` is:",
        "",
        "```text",
        "d * (B_q - A*s_q) = d*m_q",
        "```",
        "",
        "If the row is needed for one lane but the off-lane body term is dropped",
        "while the shared mask contribution remains, the off-lane phase becomes:",
        "",
        "```text",
        "d * (0 - A*s_q)",
        "```",
        "",
        "which is not a zero encryption in general.",
        "",
        "## Concrete Counterexample",
        "",
        f"With `d={fail['d']}`, `A={fail['mask']}`, `s1={fail['s1']}`, and expected",
        f"off-lane message `0`, dropping the off-lane body gives phase",
        f"`{fail['phase1']}` instead of `0`.",
        "",
        "Therefore body-linear external product is not safe as a loop-only change",
        "under the current shared-mask `MAT_TRGSW_DFT` format.",
    ]
    THEORY_MD.write_bytes("\n".join(lines).encode("utf-8"))


def write_variant() -> None:
    lines = [
        "# MAT-RLWE SAB Body-Linear Selector Format Candidate",
        "",
        "## Status",
        "",
        "`DESIGN_OPEN_NEW_FORMAT_REQUIRED`",
        "",
        "## Mathematical Definition",
        "",
        "The desired body-linear external product must avoid the current",
        "`(k+r)^2` row-output product shape while preserving each lane phase:",
        "",
        "```text",
        "phase(body_q(out)) = phase(body_q(reference_dense_out))",
        "```",
        "",
        "for every checked lane `q`.",
        "",
        "## Required Format Change",
        "",
        "A valid candidate must ensure that any mask contribution used for one lane",
        "is either cancelled in every other lane or is not shared with those lanes.",
        "This requires one of:",
        "",
        "- lane-local mask accumulations;",
        "- proof-carrying mask partitions;",
        "- another selector/key format with an equivalent phase proof.",
        "",
        "## Next Experiment",
        "",
        "Before C implementation, build a deterministic r=2 algebraic simulator for",
        "candidate lane-local or proof-carrying formats and compare every lane",
        "against the dense MAT external-product phase.",
    ]
    VARIANT_MD.write_bytes("\n".join(lines).encode("utf-8"))


def write_md(summary: List[Dict[str, str]], counterexample: List[Dict[str, str]], candidates: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage112 Selector/Key-Format Gate",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{summary[-1]['status']}`",
        "",
        "Stage112 shows why body-linear MAT external product is not a local loop",
        "rewrite under the current shared-mask selector format. A shared mask row",
        "that contributes to the output mask must be cancelled in every body lane.",
        "Dropping off-lane body ciphertext terms leaves an uncancelled mask term.",
        "",
        "## Gates",
        "",
        "| gate | status | metric | value | detail |",
        "|---|---|---|---|---|",
    ]
    for row in summary:
        lines.append(f"| {row['gate']} | {row['status']} | {row['metric']} | {row['value']} | {row['detail']} |")
    lines += [
        "",
        "## Counterexample",
        "",
        "| case | result | phase0 | expected0 | phase1 | expected1 | interpretation |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in counterexample:
        lines.append(
            f"| {row['case']} | {row['result']} | {row['phase0']} | "
            f"{row['expected_phase0']} | {row['phase1']} | {row['expected_phase1']} | "
            f"{row['interpretation']} |"
        )
    lines += [
        "",
        "## Candidate Formats",
        "",
        "| candidate | status | complexity shape | next gate |",
        "|---|---|---|---|",
    ]
    for row in candidates:
        lines.append(
            f"| {row['candidate']} | {row['status']} | {row['complexity_shape']} | {row['next_gate']} |"
        )
    OUT_MD.write_bytes("\n".join(lines).encode("utf-8"))


def artifact_index(paths: Iterable[Path]) -> List[Dict[str, str]]:
    rows = []
    for path in paths:
        rows.append(
            {
                "artifact": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256_file(path) if path.exists() else "",
                "size_bytes": str(path.stat().st_size) if path.exists() else "",
            }
        )
    return rows


def upsert_run_log(status: str) -> None:
    fields = [
        "run_id",
        "date",
        "commit_or_state",
        "stage",
        "backend",
        "command",
        "params",
        "seed",
        "status",
        "summary",
        "artifacts",
    ]
    rows = [
        row for row in read_csv(RUN_LOG)
        if row.get("run_id") != "stage112-selector-format-gate-001"
    ]
    artifacts = [
        rel(OUT_MD),
        rel(PLAN_MD),
        rel(THEORY_MD),
        rel(VARIANT_MD),
        rel(SUMMARY_CSV),
        rel(COUNTEREXAMPLE_CSV),
        rel(CANDIDATE_CSV),
        rel(ARTIFACT_INDEX),
        rel(ROOT / "scripts" / "build_stage112_selector_format_gate.py"),
    ]
    rows.append(
        {
            "run_id": "stage112-selector-format-gate-001",
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 112",
            "backend": "n/a",
            "command": "python scripts/build_stage112_selector_format_gate.py",
            "params": "shared-mask body-linear counterexample; candidate selector/key-format matrix",
            "seed": "n/a",
            "status": status,
            "summary": "Stage112 proves loop-only off-lane skipping is invalid under shared-mask MAT_TRGSW_DFT and routes body-linear work to new-format r=2 gates.",
            "artifacts": "; ".join(artifacts),
        }
    )
    write_csv(RUN_LOG, rows, fields)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_plan()
    counterexample = build_counterexample()
    candidates = build_candidates()
    summary = build_summary(counterexample)
    write_csv(
        COUNTEREXAMPLE_CSV,
        counterexample,
        [
            "case",
            "d",
            "mask",
            "s0",
            "s1",
            "b0",
            "b1",
            "phase0",
            "phase1",
            "expected_phase0",
            "expected_phase1",
            "result",
            "interpretation",
        ],
    )
    write_csv(
        CANDIDATE_CSV,
        candidates,
        ["candidate", "definition", "status", "complexity_shape", "next_gate"],
    )
    write_csv(
        SUMMARY_CSV,
        summary,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_theory(counterexample)
    write_variant()
    write_md(summary, counterexample, candidates)
    write_csv(
        ARTIFACT_INDEX,
        artifact_index(
            [
                OUT_MD,
                PLAN_MD,
                THEORY_MD,
                VARIANT_MD,
                SUMMARY_CSV,
                COUNTEREXAMPLE_CSV,
                CANDIDATE_CSV,
                ROOT / "scripts" / "build_stage112_selector_format_gate.py",
            ]
        ),
        ["artifact", "exists", "sha256", "size_bytes"],
    )
    status = summary[-1]["status"]
    upsert_run_log(status)
    print(f"Stage112 selector-format gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 1 if status.startswith("FAIL") else 0


if __name__ == "__main__":
    raise SystemExit(main())
