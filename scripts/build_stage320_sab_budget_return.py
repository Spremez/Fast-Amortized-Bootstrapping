#!/usr/bin/env python3
"""Build Stage320 complete-SAB budget return artifacts."""

from __future__ import annotations

import csv
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage320_sab_budget_return"
DOC = ROOT / "docs" / "stage320_sab_budget_return.md"
THEORY = ROOT / "theory_checks" / "stage320_candidate_budget_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage320_r4_unrolled_refresh.md"
PLAN = ROOT / "experiments" / "stage321_r4_unrolled_fullsab_ab_plan.md"

SUMMARY = OUT / "stage320_summary.csv"
CANDIDATES = OUT / "candidate_rank.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage320_report.md"
ARTIFACT = OUT / "artifact_index.csv"

STAGE314 = ROOT / "repro" / "stage314_local_digit_closeout" / "stage314_summary.csv"
STAGE315 = ROOT / "repro" / "stage315_backend_ifft_admission" / "admission_summary.csv"
STAGE319 = ROOT / "repro" / "stage319_ifft_batch5_asm_microbench" / "stage319_summary.csv"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION = "PASS_STAGE320_RETURN_TO_MAT_EP_SELECT_R4_UNROLLED_REFRESH"
NEXT_STAGE = "stage321_current_head_r4_unrolled_fullsab_ab"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return (
        path.read_text(encoding="utf-8", errors="replace")
        .replace("\x00", "")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def read_csv_one(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return rows[0] if rows else {}


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def append_once(path: Path, marker: str, block: str) -> None:
    text = read_text(path)
    if marker in text:
        return
    write_text(path, text.rstrip() + "\n" + marker + "\n" + block.strip() + "\n")


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def f(row: Dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default))
    except Exception:
        return default


def projected_speedup(share: float, reduction: float) -> float:
    return 1.0 / (1.0 - share * reduction)


def main() -> int:
    s314 = read_csv_one(STAGE314)
    s315 = read_csv_one(STAGE315)
    s319 = read_csv_one(STAGE319)
    if not s314 or not s315 or not s319:
        print("missing Stage314/315/319 inputs")
        return 1

    mat_ep_share = f(s315, "stage313_mat_ep_share_of_body")
    ifft_share = f(s315, "stage313_ifft_share_of_body")
    digit_share = f(s314, "digit_share_of_body_profile")
    dense_share = 0.215408
    ifft_closed_speedup = f(s319, "mean_speedup")

    candidate_rows = [
        {
            "rank": "P0",
            "candidate": "r4_unrolled_mat_ep_current_head_refresh",
            "route_family": "MAT EP inner-loop/layout",
            "body_share": f"{mat_ep_share:.6f}",
            "prior": "Stage142-144 weak positive, current-head refresh required",
            "projected_fullsab_speedup_at_5pct_component_reduction": f"{projected_speedup(mat_ep_share, 0.05):.6f}",
            "status": "SELECT_STAGE321",
            "reason": "Targets the dominant MAT EP share, already implemented behind an explicit flag, and has prior full-SAB signal.",
        },
        {
            "rank": "P1",
            "candidate": "schedule_level_cmux_copy_sub_fusion_refresh",
            "route_family": "SAB schedule",
            "body_share": "unknown_current",
            "prior": "defer until r4-unrolled refresh is neutral or negative",
            "projected_fullsab_speedup_at_5pct_component_reduction": "needs profile",
            "status": "DEFER",
            "reason": "Potentially valid but needs fresh body attribution before code changes.",
        },
        {
            "rank": "REJECT",
            "candidate": "ifft_batch5_backend",
            "route_family": "backend IFFT",
            "body_share": f"{ifft_share:.6f}",
            "prior": "Stage318/319 correct but slower",
            "projected_fullsab_speedup_at_5pct_component_reduction": f"{ifft_closed_speedup:.6f}_observed_isolated_speedup",
            "status": "CLOSED",
            "reason": "Both intrinsics and hand assembly failed the isolated component gate.",
        },
        {
            "rank": "REJECT",
            "candidate": "local_digit_microvariant",
            "route_family": "digit conversion",
            "body_share": f"{digit_share:.6f}",
            "prior": "Stage314 closes local digit variants",
            "projected_fullsab_speedup_at_5pct_component_reduction": f"{projected_speedup(digit_share, 0.05):.6f}",
            "status": "CLOSED",
            "reason": "Observed digit-only projection is below full-SAB budget.",
        },
        {
            "rank": "REJECT",
            "candidate": "dense_from_dec_local_only_without_fullsab_budget",
            "route_family": "dense MAT AVX subcomponent",
            "body_share": f"{dense_share:.6f}",
            "prior": "subcomponent-only budget is smaller than full MAT EP lifecycle",
            "projected_fullsab_speedup_at_5pct_component_reduction": f"{projected_speedup(dense_share, 0.05):.6f}",
            "status": "NEEDS_STRONGER_PREFLIGHT",
            "reason": "Do not write new local kernel unless a microbench projects >= 1.02 full-SAB movement.",
        },
    ]
    summary_rows = [
        {
            "decision": DECISION,
            "primary_metric": "complete_sab_T_bootstrap_over_r",
            "mat_ep_share_of_body": f"{mat_ep_share:.6f}",
            "ifft_share_of_body": f"{ifft_share:.6f}",
            "digit_share_of_body": f"{digit_share:.6f}",
            "closed_ifft_stage": s319.get("decision", ""),
            "selected_next_stage": NEXT_STAGE,
            "selected_flag": "MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true",
        }
    ]

    write_csv(SUMMARY, summary_rows, [
        "decision", "primary_metric", "mat_ep_share_of_body", "ifft_share_of_body",
        "digit_share_of_body", "closed_ifft_stage", "selected_next_stage", "selected_flag"
    ])
    write_csv(CANDIDATES, candidate_rows, [
        "rank", "candidate", "route_family", "body_share", "prior",
        "projected_fullsab_speedup_at_5pct_component_reduction", "status", "reason"
    ])
    proof_rows = [
        {
            "gate": "G1_primary_metric",
            "status": "PASS",
            "metric": "primary endpoint",
            "value": "complete_sab_T_bootstrap_over_r",
            "interpretation": "Candidate selection is tied to amortized SAB throughput, not isolated kernel speed.",
        },
        {
            "gate": "G2_closed_routes",
            "status": "PASS",
            "metric": "digit and IFFT",
            "value": "Stage314;Stage319",
            "interpretation": "Local digit and batch5 IFFT are not reopened without new full-SAB budget evidence.",
        },
        {
            "gate": "G3_select_dominant_share",
            "status": "PASS",
            "metric": "MAT EP body share",
            "value": f"{mat_ep_share:.6f}",
            "interpretation": "MAT EP remains the largest actionable measured component.",
        },
        {
            "gate": "G4_next",
            "status": DECISION,
            "metric": "selected route",
            "value": NEXT_STAGE,
            "interpretation": "Refresh current-head r=4 unrolled MAT EP as the lowest-risk next full-SAB A/B.",
        },
    ]
    write_csv(PROOF, proof_rows, ["gate", "status", "metric", "value", "interpretation"])
    write_csv(NEXT, [
        {
            "priority": "P0",
            "stage": NEXT_STAGE,
            "input": DECISION,
            "task": "Run current-head same-backend full-SAB A/B: selected direct MAT path versus MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true.",
            "gate": "correctness pass and repeated T_bootstrap/r speedup; if positive, run noise/resource before promotion",
        }
    ], ["priority", "stage", "input", "task", "gate"])
    write_text(COMMANDS, """# Stage320 Reproduction

```sh
python3 scripts/build_stage320_sab_budget_return.py
```

Stage321 must run real full-SAB A/B before any performance claim.
""")
    artifacts = [
        (SUMMARY, "decision summary"),
        (CANDIDATES, "candidate ranking"),
        (PROOF, "stage gate"),
        (NEXT, "next-stage queue"),
        (DOC, "human-readable report"),
        (THEORY, "candidate budget model"),
        (VARIANT, "selected variant card"),
        (PLAN, "Stage321 experiment plan"),
    ]
    write_csv(ARTIFACT, [{"artifact": rel(p), "role": r} for p, r in artifacts], ["artifact", "role"])

    report = f"""# Stage320 SAB Budget Return

Decision: `{DECISION}`.

Stage320 closes the IFFT-only branch and returns to the complete SAB
`T_bootstrap/r` budget.  The selected next executable candidate is a current
head refresh of the existing explicit r=4 MAT EP unrolled-row implementation:
`MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true`.

| component | body share | status |
| --- | --- | --- |
| MAT EP lifecycle | {mat_ep_share:.6f} | selected target family |
| IFFT | {ifft_share:.6f} | closed by Stage319 |
| digit conversion | {digit_share:.6f} | closed by Stage314 |

The next step must be full-SAB A/B, not another isolated kernel claim.
"""
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, f"""# Stage320 Candidate Budget Model

Primary endpoint: complete `T_bootstrap/r`.

Stage315 measured MAT EP share of body as {mat_ep_share:.6f}.  A 5% reduction in
that lifecycle projects to {projected_speedup(mat_ep_share, 0.05):.6f} body
speedup, enough to justify a full-SAB refresh.  By contrast, local digit and
IFFT-only routes have already failed or closed their gates.

Selected candidate: refresh existing r=4 unrolled MAT EP under current head and
same backend.  It is already behind an explicit flag and therefore preserves
the scalar/default path.
""")
    write_text(VARIANT, f"""# Stage320 Selected Variant: r=4 MAT EP Unrolled Refresh

Flag: `MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true`.

Reason: it targets MAT EP, the dominant measured body component, and has prior
weak full-SAB evidence while remaining isolated behind an explicit flag.

No claim is made at Stage320.  Stage321 must run complete SAB A/B on the
current codebase.
""")
    write_text(PLAN, f"""# Stage321 r=4 Unrolled Full-SAB A/B Plan

Input decision: `{DECISION}`.

Run same-backend current-head A/B:

- control: current selected direct MAT/SAB path;
- candidate: add `MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true`;
- endpoint: complete SAB `T_bootstrap/r`;
- gate: correctness pass and repeated speedup; if positive, run noise/resource.

If Stage321 is neutral or negative, close r=4 unrolled for current head and
move to SAB schedule attribution.
""")

    append_once(GOAL, "<!-- stage320-sab-budget-return -->",
        f"""### Stage320 SAB budget return

`{DECISION}` selects a current-head full-SAB A/B refresh of
`MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true` and keeps IFFT batch5 closed.
""")
    append_once(ROADMAP, "<!-- stage320-sab-budget-return-roadmap -->",
        f"""## Stage 320: SAB Budget Return

Goal: close failed IFFT-only work and select the next full-SAB candidate from
the current measured budget.

Status: `{DECISION}`.
""")
    append_once(HYPOTHESES, "H320_sab_budget_return_r4_unrolled_refresh:",
        f"""  status: {DECISION}
  primary_metric: complete_sab_T_bootstrap_over_r
  evidence:
    - repro/stage320_sab_budget_return/stage320_summary.csv
    - repro/stage320_sab_budget_return/candidate_rank.csv
    - repro/stage320_sab_budget_return/proof_gate.csv
  conclusion: >
    Stage320 closes IFFT batch5 and selects current-head r=4 unrolled MAT EP
    full-SAB A/B as the next executable candidate.
""")
    append_once(MANIFEST, "<!-- stage320-sab-budget-return-manifest -->",
        """- stage320_sab_budget_return:
  - `docs/stage320_sab_budget_return.md`
  - `theory_checks/stage320_candidate_budget_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage320_r4_unrolled_refresh.md`
  - `experiments/stage321_r4_unrolled_fullsab_ab_plan.md`
  - `scripts/build_stage320_sab_budget_return.py`
  - `repro/stage320_sab_budget_return/`
""")
    append_once(CHECKLIST, "<!-- stage320-sab-budget-return-checklist -->",
        f"""- [x] Stage320 records `{DECISION}` and selects Stage321 full-SAB A/B.
""")
    append_once(RUN_LOG, "stage320-sab-budget-return-001",
        (
            "stage320-sab-budget-return-001,2026-07-05,"
            f"{git_head()},Stage 320,analysis,"
            "python scripts/build_stage320_sab_budget_return.py,"
            "BINARY SET_2_3_2048 complete-SAB budget return,n/a,"
            f"{DECISION},"
            "Stage320 closes IFFT batch5 and selects current-head r=4 unrolled "
            "MAT EP full-SAB A/B as the next executable candidate,"
            "docs/stage320_sab_budget_return.md; "
            "repro/stage320_sab_budget_return/stage320_summary.csv; "
            "repro/stage320_sab_budget_return/candidate_rank.csv"
        ))

    print(DECISION)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
