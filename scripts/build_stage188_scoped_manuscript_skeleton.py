#!/usr/bin/env python3
"""Stage188: scoped manuscript skeleton from current PVW/MAT-SAB evidence."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage188_scoped_manuscript_skeleton"

SUMMARY_CSV = OUT_DIR / "summary.csv"
SECTION_CSV = OUT_DIR / "section_evidence_matrix.csv"
CLAIM_GUARD_CSV = OUT_DIR / "claim_guard.csv"
CITATION_TODO_CSV = OUT_DIR / "citation_todo.csv"
EXPERIMENT_TABLE_CSV = OUT_DIR / "experiment_table_plan.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"
MANUSCRIPT_MD = OUT_DIR / "manuscript_skeleton.md"

OUT_MD = ROOT / "docs" / "stage188_scoped_manuscript_skeleton.md"
PLAN_MD = ROOT / "experiments" / "stage188_scoped_manuscript_skeleton_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage188_manuscript_claim_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_scoped_manuscript_skeleton.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE185_CLAIMS = ROOT / "repro" / "stage185_research_repro_package_refresh" / "claim_table.csv"
STAGE185_REQ = ROOT / "repro" / "stage185_research_repro_package_refresh" / "requirement_matrix.csv"
STAGE187_THEOREMS = ROOT / "repro" / "stage187_compact_proof_obligation_draft" / "theorem_matrix.csv"
STAGE187_ENTRY = ROOT / "repro" / "stage187_compact_proof_obligation_draft" / "implementation_entry_rule.csv"
STAGE177_LITERATURE = ROOT / "repro" / "stage177_verified_literature_novelty_gate" / "literature_matrix.csv"
STAGE178_PERBIT = ROOT / "repro" / "stage178_fullmat_perbit_frontier" / "per_bit_throughput.csv"
STAGE180_DERIVED = ROOT / "repro" / "stage180_mat_ep_split_probe" / "derived_projection.csv"
STAGE181_COMPARE = ROOT / "repro" / "stage181_sub_decomp_avx512_gate" / "comparison.csv"
STAGE186_SUMMARY = ROOT / "repro" / "stage186_compact_proof_unlock_audit" / "summary.csv"

DECISION = "PASS_STAGE188_SCOPED_MANUSCRIPT_SKELETON_READY"


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


def metric_value(metric: str) -> str:
    for row in read_csv_dicts(STAGE178_PERBIT):
        if row.get("metric") == metric:
            return row.get("value", "")
    return ""


def stage181_value(variant: str, column: str) -> str:
    for row in read_csv_dicts(STAGE181_COMPARE):
        if row.get("variant") == variant:
            return row.get(column, "")
    return ""


def projection(metric: str) -> str:
    for row in read_csv_dicts(STAGE180_DERIVED):
        if row.get("metric") == metric:
            return row.get("value", "")
    return ""


def build_section_rows() -> List[Dict[str, str]]:
    return [
        {
            "section": "Introduction",
            "allowed_content": "Motivate per-lane SAB throughput and define T_bootstrap/r as the endpoint.",
            "evidence": f"{rel(STAGE185_REQ)}; {rel(STAGE178_PERBIT)}",
            "guardrail": "No broad novelty or theoretical optimum language.",
        },
        {
            "section": "Background and Related Work",
            "allowed_content": "Position against 2025/686, 2025/696, amortized/batch bootstrapping, PVW packing, TFHE/FHEW.",
            "evidence": rel(STAGE177_LITERATURE),
            "guardrail": "Every final citation sentence needs source-level verification before submission.",
        },
        {
            "section": "Algorithm Object",
            "allowed_content": "Describe exact PVW/MAT-SAB as r-body shared-mask MAT-RLWE bootstrapping.",
            "evidence": rel(STAGE185_REQ),
            "guardrail": "Do not call compact/shared-output SAB implemented.",
        },
        {
            "section": "Complexity and Boundaries",
            "allowed_content": "Report dense full-MAT same-format counts and measured Amdahl requirements.",
            "evidence": rel(STAGE180_DERIVED),
            "guardrail": "State partial lower-bound model, not formal optimality.",
        },
        {
            "section": "Implementation",
            "allowed_content": "Describe explicit sab_pvw path, MAT-aware AVX512 variants, and negative ablations.",
            "evidence": f"{rel(STAGE181_COMPARE)}; {rel(STAGE185_CLAIMS)}",
            "guardrail": "Do not claim AVX512 sub-decompose optimization.",
        },
        {
            "section": "Experiments",
            "allowed_content": "Report complete-SAB T_bootstrap/r A/B and rejected component candidates.",
            "evidence": f"{rel(STAGE178_PERBIT)}; {rel(STAGE181_COMPARE)}",
            "guardrail": "Kernel-only results cannot be reported as bootstrapping speedup.",
        },
        {
            "section": "Limitations and Future Work",
            "allowed_content": "Explain compact proof obligations and exact-route no-code boundary.",
            "evidence": f"{rel(STAGE186_SUMMARY)}; {rel(STAGE187_THEOREMS)}",
            "guardrail": "Compact remains proof-gated future work.",
        },
    ]


def build_claim_guard_rows() -> List[Dict[str, str]]:
    rows = []
    for row in read_csv_dicts(STAGE185_CLAIMS):
        rows.append(
            {
                "claim": row.get("claim", ""),
                "status": row.get("stage185_status", ""),
                "safe_text": row.get("safe_use", ""),
                "forbidden_text": row.get("must_not_say", ""),
                "evidence": row.get("evidence", ""),
            }
        )
    rows.append(
        {
            "claim": "compact_future_work",
            "status": "future_work_only",
            "safe_text": "Compact/shared-output MAT-SAB is a proof-gated future route with kernel-level motivation.",
            "forbidden_text": "Compact/shared-output MAT-SAB is implemented or has complete-SAB speedup.",
            "evidence": f"{rel(STAGE186_SUMMARY)}; {rel(STAGE187_THEOREMS)}",
        }
    )
    return rows


def build_citation_rows() -> List[Dict[str, str]]:
    rows = []
    for row in read_csv_dicts(STAGE177_LITERATURE):
        rows.append(
            {
                "id": row.get("id", ""),
                "title": row.get("title", ""),
                "role": row.get("relation_to_project", ""),
                "url": row.get("url", ""),
                "required_action": "cite_verify_before_submission",
            }
        )
    return rows


def build_experiment_rows() -> List[Dict[str, str]]:
    return [
        {
            "table": "Complete SAB amortized throughput",
            "rows": "exact PVW/MAT-SAB r=6 versus repeated scalar",
            "primary_metric": "T_bootstrap/r",
            "current_values": (
                f"mean {metric_value('speedup_vs_scalar_repeated_mean')}x; "
                f"min {metric_value('speedup_vs_scalar_repeated_min')}x; "
                f"CI-low {metric_value('speedup_vs_scalar_repeated_ci95_low')}x"
            ),
            "evidence": rel(STAGE178_PERBIT),
        },
        {
            "table": "Component projection and Amdahl requirements",
            "rows": "sub-decompose, torus-to-DFT rows, addmul",
            "primary_metric": "component share and speedup required for 3pct full-SAB gain",
            "current_values": (
                f"sub {projection('sub_decompose_full_sab_share_and_3pct_requirement')}; "
                f"dft {projection('torus_to_dft_rows_full_sab_share_and_3pct_requirement')}; "
                f"addmul {projection('addmul_from_dec_dft_full_sab_share_and_3pct_requirement')}"
            ),
            "evidence": rel(STAGE180_DERIVED),
        },
        {
            "table": "Negative AVX512 sub-decompose ablation",
            "rows": "baseline versus default-off AVX512 sub-decompose",
            "primary_metric": "combined_current speedup",
            "current_values": f"{stage181_value('combined_current', 'speedup')}x",
            "evidence": rel(STAGE181_COMPARE),
        },
        {
            "table": "Compact proof status",
            "rows": "T1-T6 proof obligations",
            "primary_metric": "implementation permission",
            "current_values": "production SAB code denied",
            "evidence": rel(STAGE187_ENTRY),
        },
    ]


def build_summary_rows() -> List[Dict[str, str]]:
    inputs = [
        STAGE185_CLAIMS,
        STAGE187_THEOREMS,
        STAGE177_LITERATURE,
        STAGE178_PERBIT,
        STAGE180_DERIVED,
    ]
    ok = all(path.exists() for path in inputs)
    forbidden = forbidden_scan()
    return [
        {
            "gate": "stage188_inputs",
            "status": "PASS" if ok else "FAIL",
            "metric": "required_inputs_present",
            "value": "1" if ok else "0",
            "evidence": f"{rel(STAGE185_CLAIMS)}; {rel(STAGE187_THEOREMS)}",
            "detail": "Stage188 consumes scoped claim ledger, compact proof obligations, literature matrix, and experiment evidence.",
            "next_action": "Repair missing inputs before manuscript use.",
        },
        {
            "gate": "stage188_manuscript_skeleton",
            "status": "PASS_DRAFTED",
            "metric": "sections",
            "value": "7",
            "evidence": rel(MANUSCRIPT_MD),
            "detail": "Manuscript skeleton is scoped to allowed current claims.",
            "next_action": "Use as outline only; final paper still needs citation verification.",
        },
        {
            "gate": "stage188_forbidden_claim_guard",
            "status": "PASS" if not forbidden else "FAIL",
            "metric": "forbidden_hits",
            "value": str(len(forbidden)),
            "evidence": rel(CLAIM_GUARD_CSV),
            "detail": "Generated skeleton avoids forbidden compact/optimality claims.",
            "next_action": "Fix skeleton before commit if nonzero.",
        },
        {
            "gate": "stage188_decision",
            "status": DECISION if not forbidden else "FAIL_STAGE188_FORBIDDEN_CLAIM",
            "metric": "route",
            "value": "scoped_manuscript_ready" if not forbidden else "repair_required",
            "evidence": rel(SUMMARY_CSV),
            "detail": "The artifact is a manuscript skeleton, not a final paper or novelty proof.",
            "next_action": "Proceed to citation verification or targeted proof probes.",
        },
    ]


def forbidden_scan() -> List[str]:
    if not MANUSCRIPT_MD.exists():
        return []
    text = read_text(MANUSCRIPT_MD).lower()
    forbidden_phrases = [
        "theoretically optimal",
        "optimal avx512",
        "implemented compact",
        "compact sab speedup",
        "novel compact",
        "prove novelty",
    ]
    return [phrase for phrase in forbidden_phrases if phrase in text]


def write_manuscript() -> None:
    write_text_lf(
        MANUSCRIPT_MD,
        f"""# Scoped Manuscript Skeleton: PVW/MAT-SAB as r-Body Amortized Bootstrapping

## Abstract Draft

We study an implementation-level PVW/MAT r-body path for 2025/686-style sparse
amortized bootstrapping. The evaluation endpoint is complete bootstrapping time
per processed lane, `T_bootstrap/r`. Under the recorded platform and backend,
the exact full-MAT path has scoped complete-SAB amortized speedup over repeated
scalar SAB. The current evidence does not support theoretical optimality,
strong novelty, or a production compact/shared-output SAB implementation.

## 1. Introduction

State the original problem: scalar SAB processes independent look-up lanes with
repeated bootstrapping cost, while PVW/MAT-SAB carries one shared mask and r
body lanes. Define `T_bootstrap/r` as the primary metric.

## 2. Background and Related Work

Use the Stage177 literature matrix to cover 2025/686, 2025/696, amortized and
batch bootstrapping, PVW packing, and TFHE/FHEW external products. Every final
sentence in this section needs citation verification before submission.

## 3. Algorithm Object

Describe the implemented exact full-MAT PVW/MAT-SAB path as an r-body
shared-mask accumulator. State that scalar/default SAB remains a baseline and
that experimental paths are explicit.

## 4. Complexity and Boundary Model

Report dense full-MAT costs and the measured split projection:

- `sub_decompose`: `{projection('sub_decompose_full_sab_share_and_3pct_requirement')}`
- `torus_to_dft_rows`: `{projection('torus_to_dft_rows_full_sab_share_and_3pct_requirement')}`
- `addmul_from_dec_dft`: `{projection('addmul_from_dec_dft_full_sab_share_and_3pct_requirement')}`

State this as a practical boundary model, not as a formal lower-bound theorem.

## 5. Implementation

Describe the exact `sab_pvw_*` path, MAT-aware AVX512 variants, and the explicit
negative ablations. The AVX512 sub-decompose candidate is a negative ablation:
combined-current speedup `{stage181_value('combined_current', 'speedup')}x`.

## 6. Experiments

Primary table: complete SAB `T_bootstrap/r` against repeated scalar SAB.
Current scoped values: mean `{metric_value('speedup_vs_scalar_repeated_mean')}x`,
min `{metric_value('speedup_vs_scalar_repeated_min')}x`, CI-low
`{metric_value('speedup_vs_scalar_repeated_ci95_low')}x`.

Secondary tables: component projection, negative ablations, resource/noise
evidence, and compact proof status.

## 7. Limitations

The compact/shared-output route is proof-gated. Stage187 lists open obligations
for key distribution, closed shared-mask state, production phase/noise proof,
complete-SAB performance, and citation-supported novelty scope.

## 8. Future Work

Allowed future work: isolated proof probes targeting Stage187 theorem gates,
or new non-layout dataflow preflights with complete-SAB projection. Production
compact SAB code remains denied until the proof gates pass.
""",
    )


def write_docs(
    summary_rows: List[Dict[str, str]],
    section_rows: List[Dict[str, str]],
    claim_rows: List[Dict[str, str]],
    citation_rows: List[Dict[str, str]],
    experiment_rows: List[Dict[str, str]],
) -> None:
    write_text_lf(
        OUT_MD,
        f"""# Stage188 Scoped Manuscript Skeleton

Decision: `{DECISION}`.

Stage188 creates a manuscript skeleton that is constrained by the current
claim ledger. It is not a final paper. It exists to prevent claim drift while
making the current implemented result and open proof obligations readable.

## Gate Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Section Evidence Matrix

{table(section_rows, ["section", "allowed_content", "evidence", "guardrail"])}
## Claim Guard

{table(claim_rows, ["claim", "status", "safe_text", "forbidden_text", "evidence"])}
## Citation TODO

{table(citation_rows, ["id", "title", "role", "url", "required_action"])}
## Experiment Table Plan

{table(experiment_rows, ["table", "rows", "primary_metric", "current_values", "evidence"])}
""",
    )

    write_text_lf(
        PLAN_MD,
        """# Stage188 Plan

Goal: generate a scoped manuscript skeleton from current evidence.

Rules:

- use only Stage185 allowed claims;
- keep compact/shared-output as future work;
- use `T_bootstrap/r` as the performance endpoint;
- final paper requires separate citation verification.
""",
    )

    write_text_lf(
        THEORY_MD,
        """# Stage188 Manuscript Claim Model

Allowed claim class:

- scoped complete-SAB amortized speedup for exact PVW/MAT-SAB under recorded
  conditions.

Denied claim classes:

- theoretical optimality;
- compact/shared-output production implementation;
- compact complete-SAB speedup;
- strong novelty.

The manuscript skeleton is valid only if it stays inside these boundaries.
""",
    )

    write_text_lf(
        VARIANT_MD,
        """# Scoped Manuscript Skeleton Variant

This is a writing artifact, not a code or proof artifact. It packages the
implemented exact PVW/MAT-SAB result, negative ablations, and compact proof
obligations into a paper skeleton with explicit claim guards.
""",
    )


def update_global_docs() -> None:
    append_once(
        ROADMAP_MD,
        "## Stage 188: Scoped Manuscript Skeleton",
        f"""
## Stage 188: Scoped Manuscript Skeleton

Goal:

```text
Create a manuscript skeleton from the scoped exact PVW/MAT-SAB evidence while
preserving forbidden-claim guardrails.
```

Status:

```text
Completed. Stage188 records {DECISION}. The skeleton reports the implemented
exact-route `T_bootstrap/r` evidence and treats compact/shared-output MAT-SAB
as proof-gated future work.
```
""",
    )

    append_once(
        GOAL_MD,
        "Stage188 records the scoped manuscript skeleton",
        f"""
Stage188 records the scoped manuscript skeleton. Decision: `{DECISION}`.
It packages the current implemented exact PVW/MAT-SAB result into a paper
outline while preserving claim guards against optimality, compact
implementation, and broad novelty claims.
""",
    )

    append_once(
        CURRENT_GOAL_MD,
        "Treat Stage188 as the scoped manuscript skeleton",
        f"""
92. Treat Stage188 as the scoped manuscript skeleton:
    `{DECISION}`. It is a writing artifact constrained by Stage185/187 claim
    guards, not a final paper or proof. Final citation verification remains
    required before submission-level claims.
""",
    )

    append_once(
        HYPOTHESIS_YAML,
        "H112_scoped_manuscript_skeleton",
        f"""
  - id: H112_scoped_manuscript_skeleton
    statement: >
      The current PVW/MAT-SAB evidence can support a scoped manuscript
      skeleton only if the text stays within Stage185/187 claim guards.
    mechanism: >
      Stage188 maps sections, claims, citations, and experiment tables to
      authoritative artifacts and runs a forbidden-claim guard over the
      generated skeleton.
    status: stage188_scoped_manuscript_skeleton
    evidence: docs/stage188_scoped_manuscript_skeleton.md; experiments/stage188_scoped_manuscript_skeleton_plan.md; theory_checks/stage188_manuscript_claim_model.md; repro/stage188_scoped_manuscript_skeleton/summary.csv
    current_decision: >
      {DECISION}
    failure_criteria:
      - skeleton claims theoretical optimality
      - skeleton claims implemented compact SAB or compact complete-SAB speedup
      - final paper uses unverified citations
""",
    )

    append_once(
        RUN_LOG,
        "stage188-scoped-manuscript-skeleton-001",
        f"""
stage188-scoped-manuscript-skeleton-001,2026-07-04,{git_head()},Stage 188,analysis,python scripts/build_stage188_scoped_manuscript_skeleton.py,Stage185/187 claim guards,none,{DECISION},Scoped manuscript skeleton from current PVW/MAT-SAB evidence.,repro/stage188_scoped_manuscript_skeleton
""",
    )

    append_once(
        MANIFEST,
        "stage188_scoped_manuscript_skeleton",
        f"""
- stage188_scoped_manuscript_skeleton: `{DECISION}`
  - `docs/stage188_scoped_manuscript_skeleton.md`
  - `experiments/stage188_scoped_manuscript_skeleton_plan.md`
  - `theory_checks/stage188_manuscript_claim_model.md`
  - `algorithm_variants/mat_rlwe_sab_scoped_manuscript_skeleton.md`
  - `repro/stage188_scoped_manuscript_skeleton/`
""",
    )

    append_once(CHECKLIST, "Stage188 scoped manuscript skeleton recorded", """
- [x] Stage188 scoped manuscript skeleton recorded.
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
    write_manuscript()
    section_rows = build_section_rows()
    claim_rows = build_claim_guard_rows()
    citation_rows = build_citation_rows()
    experiment_rows = build_experiment_rows()
    summary_rows = build_summary_rows()

    write_csv(SECTION_CSV, section_rows, ["section", "allowed_content", "evidence", "guardrail"])
    write_csv(CLAIM_GUARD_CSV, claim_rows, ["claim", "status", "safe_text", "forbidden_text", "evidence"])
    write_csv(CITATION_TODO_CSV, citation_rows, ["id", "title", "role", "url", "required_action"])
    write_csv(EXPERIMENT_TABLE_CSV, experiment_rows, ["table", "rows", "primary_metric", "current_values", "evidence"])
    write_csv(SUMMARY_CSV, summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    write_docs(summary_rows, section_rows, claim_rows, citation_rows, experiment_rows)
    update_global_docs()
    write_artifacts(
        [
            OUT_MD,
            PLAN_MD,
            THEORY_MD,
            VARIANT_MD,
            MANUSCRIPT_MD,
            SUMMARY_CSV,
            SECTION_CSV,
            CLAIM_GUARD_CSV,
            CITATION_TODO_CSV,
            EXPERIMENT_TABLE_CSV,
            Path(__file__),
        ]
    )
    print(DECISION)


if __name__ == "__main__":
    main()
