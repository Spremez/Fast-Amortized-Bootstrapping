#!/usr/bin/env python3
"""Stage195: scoped paper/repro refresh for current PVW/MAT-SAB evidence."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage195_scoped_paper_repro_refresh"

SUMMARY_CSV = OUT_DIR / "summary.csv"
CLAIM_CSV = OUT_DIR / "final_claim_ledger.csv"
EVIDENCE_CSV = OUT_DIR / "evidence_chain.csv"
FRONTIER_CSV = OUT_DIR / "negative_frontier.csv"
FORBIDDEN_CSV = OUT_DIR / "forbidden_claim_scan.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"
REPORT_MD = OUT_DIR / "scoped_report.md"
COMMANDS_MD = OUT_DIR / "reproduction_commands.md"

OUT_MD = ROOT / "docs" / "stage195_scoped_paper_repro_refresh.md"
PLAN_MD = ROOT / "experiments" / "stage195_scoped_paper_repro_refresh_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage195_scoped_claim_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_scoped_paper_repro_refresh.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE178_PERBIT = ROOT / "repro" / "stage178_fullmat_perbit_frontier" / "per_bit_throughput.csv"
STAGE180_DERIVED = ROOT / "repro" / "stage180_mat_ep_split_probe" / "derived_projection.csv"
STAGE188_SUMMARY = ROOT / "repro" / "stage188_scoped_manuscript_skeleton" / "summary.csv"
STAGE188_CLAIM = ROOT / "repro" / "stage188_scoped_manuscript_skeleton" / "claim_guard.csv"
STAGE192_SUMMARY = ROOT / "repro" / "stage192_compact_admission_route_selection" / "summary.csv"
STAGE193_SUMMARY = ROOT / "repro" / "stage193_exact_addmul_dataflow_preflight" / "summary.csv"
STAGE194_SUMMARY = ROOT / "repro" / "stage194_exact_dft_conversion_preflight" / "summary.csv"
STAGE177_LIT = ROOT / "repro" / "stage177_verified_literature_novelty_gate" / "literature_matrix.csv"
STAGE185_CLAIMS = ROOT / "repro" / "stage185_research_repro_package_refresh" / "claim_table.csv"

DECISION = "PASS_STAGE195_SCOPED_PAPER_REPRO_REFRESH_READY_GOAL_ACTIVE"


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


def metric(metric_name: str) -> str:
    for row in read_csv_dicts(STAGE178_PERBIT):
        if row.get("metric") == metric_name:
            return row.get("value", "")
    return ""


def derived(metric_name: str) -> str:
    for row in read_csv_dicts(STAGE180_DERIVED):
        if row.get("metric") == metric_name:
            return row.get("value", "")
    return ""


def build_claim_rows() -> List[Dict[str, str]]:
    return [
        {
            "claim": "complete_sab_amortized_speedup",
            "status": "ALLOW_SCOPED",
            "safe_wording": "The exact full-MAT PVW/MAT-SAB path has recorded complete-SAB T_bootstrap/r speedup over repeated scalar SAB under the recorded platform, backend, parameters, and seeds.",
            "quantitative_bound": f"mean {metric('speedup_vs_scalar_repeated_mean')}x; min {metric('speedup_vs_scalar_repeated_min')}x; CI-low {metric('speedup_vs_scalar_repeated_ci95_low')}x",
            "must_not_say": "Do not generalize to all parameters/backends, proof of optimality, or compact/shared-output speedup.",
            "evidence": rel(STAGE178_PERBIT),
        },
        {
            "claim": "compact_shared_output_sab",
            "status": "DENY_IMPLEMENTATION_CLAIM",
            "safe_wording": "Compact/shared-output MAT-SAB remains a proof-only route with explicit T1/T2/T4 blockers.",
            "quantitative_bound": "production compact permission 0",
            "must_not_say": "Do not say compact/shared-output SAB is implemented or benchmarked at complete-SAB level.",
            "evidence": rel(STAGE192_SUMMARY),
        },
        {
            "claim": "exact_addmul_new_code",
            "status": "DENY_CODE_CANDIDATE",
            "safe_wording": "Exact addmul has no promoted local code candidate after source/counter/dataflow preflight.",
            "quantitative_bound": "r6 dec-cache full-SAB bound 1.022675x below 3pct gate",
            "must_not_say": "Do not claim a new addmul acceleration without measured gates.",
            "evidence": rel(STAGE193_SUMMARY),
        },
        {
            "claim": "exact_dft_conversion_new_code",
            "status": "DENY_LOCAL_CODE_CANDIDATE",
            "safe_wording": "Exact DFT/conversion has no promoted local code candidate; only external backend primitive work remains optional.",
            "quantitative_bound": "torus_to_DFT required component speedup 1.208076492x",
            "must_not_say": "Do not reopen direct-scale or component-major batching as complete-SAB acceleration.",
            "evidence": rel(STAGE194_SUMMARY),
        },
        {
            "claim": "novelty",
            "status": "SCOPED_ONLY",
            "safe_wording": "The current package supports scoped systems/engineering wording only, with related-work comparison still required for final submission.",
            "quantitative_bound": "n/a",
            "must_not_say": "Do not assert broad novelty based only on local implementation evidence.",
            "evidence": rel(STAGE177_LIT),
        },
    ]


def build_evidence_rows() -> List[Dict[str, str]]:
    return [
        {
            "item": "primary_endpoint",
            "status": "SUPPORTED_SCOPED",
            "evidence": rel(STAGE178_PERBIT),
            "detail": f"T_bootstrap/r mean {metric('speedup_vs_scalar_repeated_mean')}x; min {metric('speedup_vs_scalar_repeated_min')}x; CI-low {metric('speedup_vs_scalar_repeated_ci95_low')}x.",
        },
        {
            "item": "component_budget",
            "status": "RECORDED",
            "evidence": rel(STAGE180_DERIVED),
            "detail": f"sub {derived('sub_decompose_full_sab_share_and_3pct_requirement')}; dft {derived('torus_to_dft_rows_full_sab_share_and_3pct_requirement')}; addmul {derived('addmul_from_dec_dft_full_sab_share_and_3pct_requirement')}.",
        },
        {
            "item": "manuscript_scope",
            "status": "DRAFT_READY_NOT_FINAL",
            "evidence": rel(STAGE188_SUMMARY),
            "detail": "A scoped skeleton exists, but final citation verification remains required.",
        },
        {
            "item": "compact_admission",
            "status": "IMPLEMENTATION_DENIED",
            "evidence": rel(STAGE192_SUMMARY),
            "detail": "T1/T2/T4 block compact/shared-output production code.",
        },
        {
            "item": "exact_addmul_frontier",
            "status": "NO_CODE_CANDIDATE",
            "evidence": rel(STAGE193_SUMMARY),
            "detail": "No addmul candidate passed the complete-SAB projection gate.",
        },
        {
            "item": "exact_dft_frontier",
            "status": "NO_LOCAL_CODE_CANDIDATE",
            "evidence": rel(STAGE194_SUMMARY),
            "detail": "No local DFT/conversion candidate passed prior gates and budget checks.",
        },
    ]


def build_frontier_rows() -> List[Dict[str, str]]:
    return [
        {
            "frontier": "compact_shared_output",
            "decision": "PROOF_ONLY",
            "reason": "implementation admission denied by T1/T2/T4 gates",
            "evidence": rel(STAGE192_SUMMARY),
            "reopen_condition": "T1/T2/T4 proof and then complete-SAB A/B.",
        },
        {
            "frontier": "exact_addmul",
            "decision": "NO_CODE",
            "reason": "new dec-cache mechanism below 3pct complete-SAB gate; prior families rejected",
            "evidence": rel(STAGE193_SUMMARY),
            "reopen_condition": "new dataflow reducing selector loads or FMA-equivalent work with counter evidence.",
        },
        {
            "frontier": "exact_dft_conversion",
            "decision": "NO_LOCAL_CODE",
            "reason": "same-format count closed; backend batching/direct-scale neutral; only external backend primitive possible",
            "evidence": rel(STAGE194_SUMMARY),
            "reopen_condition": "new backend primitive with exact equivalence and component speedup above Stage180 gate.",
        },
        {
            "frontier": "paper_package",
            "decision": "READY_SCOPED_NOT_FINAL",
            "reason": "current evidence can support a scoped engineering report but not final broad claims",
            "evidence": rel(REPORT_MD),
            "reopen_condition": "citation verification and final venue-specific writing pass.",
        },
    ]


def forbidden_scan_text() -> List[Dict[str, str]]:
    text = read_text(REPORT_MD).lower()
    phrases = [
        "theoretically optimal",
        "optimal avx512",
        "implemented compact",
        "compact sab speedup",
        "novel compact",
        "prove novelty",
    ]
    rows = []
    for phrase in phrases:
        rows.append(
            {
                "phrase": phrase,
                "hits": "1" if phrase in text else "0",
                "status": "FAIL" if phrase in text else "PASS",
                "evidence": rel(REPORT_MD),
            }
        )
    return rows


def write_report(claim_rows: List[Dict[str, str]], evidence_rows: List[Dict[str, str]], frontier_rows: List[Dict[str, str]]) -> None:
    write_text_lf(
        REPORT_MD,
        f"""# Scoped PVW/MAT-SAB Report Refresh

Decision: `{DECISION}`.

## Scope

This package reports the current exact full-MAT PVW/MAT-SAB engineering result
using the primary endpoint `T_bootstrap/r`. It does not close the broader
research objective. It also does not authorize compact/shared-output SAB code,
does not claim optimality, and does not upgrade local implementation evidence
into broad novelty.

## Primary Result

Current exact full-MAT PVW/MAT-SAB, under recorded conditions:

- mean `T_bootstrap/r` speedup over repeated scalar SAB:
  `{metric('speedup_vs_scalar_repeated_mean')}x`;
- minimum repeated-run speedup: `{metric('speedup_vs_scalar_repeated_min')}x`;
- CI lower bound: `{metric('speedup_vs_scalar_repeated_ci95_low')}x`.

## Current Frontiers

{table(frontier_rows, ["frontier", "decision", "reason", "evidence", "reopen_condition"])}
## Claim Ledger

{table(claim_rows, ["claim", "status", "safe_wording", "quantitative_bound", "must_not_say", "evidence"])}
## Evidence Chain

{table(evidence_rows, ["item", "status", "evidence", "detail"])}
## Reproduction Entry Points

Use `repro/stage195_scoped_paper_repro_refresh/reproduction_commands.md` for
the current scoped report entry points. Every stronger claim still needs a
new gate with correctness, noise/resource, complete-SAB timing, and citation
verification.
""",
    )


def write_commands() -> None:
    write_text_lf(
        COMMANDS_MD,
        """# Stage195 Reproduction Commands

This file records entry points for the current scoped report package.

```powershell
# Rebuild this package
python scripts\\build_stage195_scoped_paper_repro_refresh.py

# Inspect primary result
Get-Content -Raw repro\\stage178_fullmat_perbit_frontier\\per_bit_throughput.csv

# Inspect compact admission blockers
Get-Content -Raw repro\\stage192_compact_admission_route_selection\\gate_admission_matrix.csv

# Inspect local implementation frontiers
Get-Content -Raw repro\\stage193_exact_addmul_dataflow_preflight\\summary.csv
Get-Content -Raw repro\\stage194_exact_dft_conversion_preflight\\summary.csv

# Validate generated claim guard
Get-Content -Raw repro\\stage195_scoped_paper_repro_refresh\\forbidden_claim_scan.csv
```
""",
    )


def build_summary_rows(forbidden_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    inputs = [
        STAGE178_PERBIT,
        STAGE188_SUMMARY,
        STAGE192_SUMMARY,
        STAGE193_SUMMARY,
        STAGE194_SUMMARY,
        STAGE177_LIT,
        STAGE185_CLAIMS,
    ]
    ok = all(path.exists() for path in inputs)
    forbidden_hits = sum(1 for row in forbidden_rows if row["hits"] != "0")
    return [
        {
            "gate": "stage195_inputs",
            "status": "PASS" if ok else "FAIL",
            "metric": "required_inputs_present",
            "value": "1" if ok else "0",
            "evidence": f"{rel(STAGE178_PERBIT)}; {rel(STAGE188_SUMMARY)}; {rel(STAGE192_SUMMARY)}; {rel(STAGE194_SUMMARY)}",
            "detail": "Stage195 consumes primary endpoint, manuscript skeleton, compact admission, and local frontier audits.",
            "next_action": "Repair missing inputs before report use.",
        },
        {
            "gate": "stage195_claim_ledger",
            "status": "PASS_SCOPED",
            "metric": "claims",
            "value": "5",
            "evidence": rel(CLAIM_CSV),
            "detail": "Allowed and denied claims are explicitly separated.",
            "next_action": "Use only ALLOW_SCOPED wording in reports.",
        },
        {
            "gate": "stage195_forbidden_claim_scan",
            "status": "PASS" if forbidden_hits == 0 else "FAIL",
            "metric": "forbidden_hits",
            "value": str(forbidden_hits),
            "evidence": rel(FORBIDDEN_CSV),
            "detail": "Generated report avoids forbidden compact/optimality/novelty phrases.",
            "next_action": "Fix report before use if nonzero.",
        },
        {
            "gate": "stage195_decision",
            "status": DECISION if forbidden_hits == 0 else "FAIL_STAGE195_FORBIDDEN_CLAIM",
            "metric": "goal_status",
            "value": "active",
            "evidence": rel(SUMMARY_CSV),
            "detail": "The scoped package is refreshed; the broader research objective remains active.",
            "next_action": "Proceed only with new external backend/proof evidence or final citation verification.",
        },
    ]


def write_docs(
    summary_rows: List[Dict[str, str]],
    claim_rows: List[Dict[str, str]],
    evidence_rows: List[Dict[str, str]],
    frontier_rows: List[Dict[str, str]],
    forbidden_rows: List[Dict[str, str]],
) -> None:
    write_text_lf(
        OUT_MD,
        f"""# Stage195 Scoped Paper/Repro Refresh

Decision: `{DECISION}`.

Stage195 refreshes the current scoped report package. It is not a completion
claim for the active research goal. It records exactly what can be reported
now, what remains blocked, and how to reproduce the current evidence.

## Gate Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Final Claim Ledger

{table(claim_rows, ["claim", "status", "safe_wording", "quantitative_bound", "must_not_say", "evidence"])}
## Evidence Chain

{table(evidence_rows, ["item", "status", "evidence", "detail"])}
## Negative Frontier

{table(frontier_rows, ["frontier", "decision", "reason", "evidence", "reopen_condition"])}
## Forbidden Claim Scan

{table(forbidden_rows, ["phrase", "hits", "status", "evidence"])}
""",
    )

    write_text_lf(
        PLAN_MD,
        """# Stage195 Plan

Goal: refresh the scoped paper/repro package after compact, exact addmul, and
exact DFT/conversion frontiers were audited.

Rules:

- only complete-SAB `T_bootstrap/r` evidence may support speedup wording;
- compact/shared-output remains proof-only;
- no optimality or broad novelty wording;
- preserve negative and neutral ablations.
""",
    )

    write_text_lf(
        THEORY_MD,
        """# Stage195 Scoped Claim Model

Allowed:

- scoped exact full-MAT PVW/MAT-SAB complete-SAB `T_bootstrap/r` result under
  recorded conditions.

Denied:

- compact/shared-output implementation claims;
- compact complete-SAB speedup;
- optimality or broad novelty claims;
- new addmul or DFT/conversion speedup claims without measured gates.

The active research goal remains open because stronger theory, proof, and
implementation evidence is not complete.
""",
    )

    write_text_lf(
        VARIANT_MD,
        """# Scoped Paper/Repro Refresh Artifact

This artifact packages the current exact PVW/MAT-SAB evidence and negative
frontiers. It does not define a new algorithm variant.

Use it as the current report baseline until a new proof or external backend
mechanism changes the evidence chain.
""",
    )


def update_global_docs() -> None:
    append_once(
        ROADMAP_MD,
        "## Stage 195: Scoped Paper/Repro Refresh",
        f"""
## Stage 195: Scoped Paper/Repro Refresh

Goal:

```text
Refresh the scoped paper/repro package after compact and exact local
implementation frontiers were audited.
```

Status:

```text
Completed. Stage195 records {DECISION}. The package is ready for scoped
reporting, while the broader research goal remains active.
```
""",
    )

    append_once(
        GOAL_MD,
        "Stage195 records scoped paper/repro refresh",
        f"""
Stage195 records scoped paper/repro refresh. Decision: `{DECISION}`. It
packages the current exact full-MAT result and blocked frontiers without
claiming compact implementation, optimality, or broad novelty.
""",
    )

    append_once(
        CURRENT_GOAL_MD,
        "Treat Stage195 as scoped paper/repro refresh",
        f"""
99. Treat Stage195 as scoped paper/repro refresh:
    `{DECISION}`. The current exact full-MAT `T_bootstrap/r` evidence is ready
    for scoped reporting, but the broader research goal remains active and
    stronger claims remain blocked.
""",
    )

    append_once(
        HYPOTHESIS_YAML,
        "H119_scoped_paper_repro_refresh",
        f"""
  - id: H119_scoped_paper_repro_refresh
    statement: >
      After compact and exact local implementation frontiers are audited, the
      current package can support only scoped exact full-MAT reporting while
      keeping stronger claims blocked.
    mechanism: >
      Stage195 aggregates Stage178, Stage188, Stage192, Stage193, and Stage194
      into a claim ledger, evidence chain, negative frontier, and report guard.
    status: stage195_scoped_paper_repro_refresh
    evidence: docs/stage195_scoped_paper_repro_refresh.md; experiments/stage195_scoped_paper_repro_refresh_plan.md; theory_checks/stage195_scoped_claim_model.md; repro/stage195_scoped_paper_repro_refresh/summary.csv
    current_decision: >
      {DECISION}
    failure_criteria:
      - report claims compact/shared-output implementation or complete-SAB speedup
      - report claims optimality or broad novelty
      - speedup wording uses kernel-only evidence instead of complete-SAB T_bootstrap/r
""",
    )

    append_once(
        RUN_LOG,
        "stage195-scoped-paper-repro-refresh-001",
        f"""
stage195-scoped-paper-repro-refresh-001,2026-07-04,{git_head()},Stage 195,analysis,python scripts/build_stage195_scoped_paper_repro_refresh.py,Stage178/188/192/193/194 evidence,none,{DECISION},Scoped paper/repro refresh with claim guard.,repro/stage195_scoped_paper_repro_refresh
""",
    )

    append_once(
        MANIFEST,
        "stage195_scoped_paper_repro_refresh",
        f"""
- stage195_scoped_paper_repro_refresh: `{DECISION}`
  - `docs/stage195_scoped_paper_repro_refresh.md`
  - `experiments/stage195_scoped_paper_repro_refresh_plan.md`
  - `theory_checks/stage195_scoped_claim_model.md`
  - `algorithm_variants/mat_rlwe_sab_scoped_paper_repro_refresh.md`
  - `repro/stage195_scoped_paper_repro_refresh/`
""",
    )

    append_once(CHECKLIST, "Stage195 scoped paper/repro refresh recorded", """
- [x] Stage195 scoped paper/repro refresh recorded.
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
    claim_rows = build_claim_rows()
    evidence_rows = build_evidence_rows()
    frontier_rows = build_frontier_rows()
    write_report(claim_rows, evidence_rows, frontier_rows)
    write_commands()
    forbidden_rows = forbidden_scan_text()
    summary_rows = build_summary_rows(forbidden_rows)

    write_csv(CLAIM_CSV, claim_rows, ["claim", "status", "safe_wording", "quantitative_bound", "must_not_say", "evidence"])
    write_csv(EVIDENCE_CSV, evidence_rows, ["item", "status", "evidence", "detail"])
    write_csv(FRONTIER_CSV, frontier_rows, ["frontier", "decision", "reason", "evidence", "reopen_condition"])
    write_csv(FORBIDDEN_CSV, forbidden_rows, ["phrase", "hits", "status", "evidence"])
    write_csv(SUMMARY_CSV, summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    write_docs(summary_rows, claim_rows, evidence_rows, frontier_rows, forbidden_rows)
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
            CLAIM_CSV,
            EVIDENCE_CSV,
            FRONTIER_CSV,
            FORBIDDEN_CSV,
            Path(__file__),
        ]
    )
    print(DECISION)


if __name__ == "__main__":
    main()
