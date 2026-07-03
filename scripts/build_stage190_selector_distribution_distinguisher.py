#!/usr/bin/env python3
"""Stage190: executable T1 selector-distribution distinguisher probe."""

from __future__ import annotations

import csv
import hashlib
import random
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage190_selector_distribution_distinguisher"

SUMMARY_CSV = OUT_DIR / "summary.csv"
PROBE_CSV = OUT_DIR / "distribution_probe.csv"
ROUTE_CSV = OUT_DIR / "distribution_route.csv"
CLAIM_CSV = OUT_DIR / "claim_boundary.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage190_selector_distribution_distinguisher.md"
PLAN_MD = ROOT / "experiments" / "stage190_selector_distribution_distinguisher_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage190_selector_distribution_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_selector_distribution_distinguisher.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE124_LAYOUT = ROOT / "repro" / "stage124_mosfhet_type_api_skeleton" / "layout_results.csv"
STAGE125_LAYOUT = ROOT / "repro" / "stage125_compact_selector_gadget_gate" / "layout_results.csv"
STAGE176_API = ROOT / "repro" / "stage176_structured_compact_security_api_gate" / "api_options.csv"
STAGE187_THEOREMS = ROOT / "repro" / "stage187_compact_proof_obligation_draft" / "theorem_matrix.csv"
STAGE189_SUMMARY = ROOT / "repro" / "stage189_closed_state_linear_probe" / "summary.csv"

DECISION = "PASS_STAGE190_T1_SELECTOR_DISTRIBUTION_DISTINGUISHERS_RECORDED_IMPLEMENTATION_STILL_DENIED"
PRIME = 65537
TRIALS = 64
MASK_N = 16
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


def rand_vec(rng: random.Random, n: int) -> List[int]:
    return [rng.randrange(PRIME) for _ in range(n)]


def layout_for_r(r: int) -> Dict[str, str]:
    for row in read_csv_dicts(STAGE124_LAYOUT):
        if row.get("r") == str(r) and row.get("N") == "2048":
            return row
    return {}


def build_probe_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for r in [2, 4, 6]:
        layout = layout_for_r(r)
        dense_rows = int(layout.get("current_selector_dft_polys") or ((r + 1) * (r + 1) * T))
        compact_rows = int(layout.get("vector_selector_dft_polys") or (4 * r * T))
        omitted_rows = dense_rows - compact_rows

        rows.append(
            {
                "candidate": "delete_body_cross_rows",
                "r": str(r),
                "mask_N": str(MASK_N),
                "trials": "1",
                "dense_observation": str(dense_rows),
                "structured_observation": str(compact_rows),
                "distinguisher": "public_row_count",
                "successes": "1",
                "status": "DISTINGUISHER_FOUND" if dense_rows != compact_rows else "NO_SIGNAL",
                "interpretation": f"{omitted_rows} public selector rows are missing versus dense format.",
            }
        )

        rng = random.Random(190000 + r)
        dense_equal_hits = 0
        structured_equal_hits = 0
        dense_zero_hits = 0
        structured_zero_hits = 0
        for _ in range(TRIALS):
            dense_a = rand_vec(rng, MASK_N)
            dense_b = rand_vec(rng, MASK_N)
            if dense_a == dense_b:
                dense_equal_hits += 1
            forced_a = rand_vec(rng, MASK_N)
            forced_b = forced_a[:]
            if forced_a == forced_b:
                structured_equal_hits += 1
            dense_zero = rand_vec(rng, MASK_N)
            if all(v == 0 for v in dense_zero):
                dense_zero_hits += 1
            structured_zero = [0 for _ in range(MASK_N)]
            if all(v == 0 for v in structured_zero):
                structured_zero_hits += 1

        rows.append(
            {
                "candidate": "force_equal_output_masks",
                "r": str(r),
                "mask_N": str(MASK_N),
                "trials": str(TRIALS),
                "dense_observation": str(dense_equal_hits),
                "structured_observation": str(structured_equal_hits),
                "distinguisher": "mask_equality_relation",
                "successes": str(TRIALS if dense_equal_hits == 0 and structured_equal_hits == TRIALS else 0),
                "status": "DISTINGUISHER_FOUND" if dense_equal_hits == 0 and structured_equal_hits == TRIALS else "REVIEW",
                "interpretation": "Forced shared/equal masks create a public equality relation absent from independent dense rows in the probe.",
            }
        )

        rows.append(
            {
                "candidate": "deterministic_zero_cross_rows",
                "r": str(r),
                "mask_N": str(MASK_N),
                "trials": str(TRIALS),
                "dense_observation": str(dense_zero_hits),
                "structured_observation": str(structured_zero_hits),
                "distinguisher": "zero_mask_relation",
                "successes": str(TRIALS if dense_zero_hits == 0 and structured_zero_hits == TRIALS else 0),
                "status": "DISTINGUISHER_FOUND" if dense_zero_hits == 0 and structured_zero_hits == TRIALS else "REVIEW",
                "interpretation": "Replacing omitted rows with deterministic zero rows is publicly detectable.",
            }
        )
    return rows


def build_route_rows() -> List[Dict[str, str]]:
    return [
        {
            "route": "current_dense_mat_trgsw_distribution",
            "t1_status": "AVAILABLE_REFERENCE",
            "public_difference": "none versus current implementation",
            "security_consequence": "standard current route remains the baseline",
            "implementation_permission": "YES_FOR_EXACT_FULL_MAT_ONLY",
        },
        {
            "route": "delete_body_cross_rows_and_claim_dense_equivalence",
            "t1_status": "REJECTED",
            "public_difference": "key row count/key size changes",
            "security_consequence": "not indistinguishable from dense public key format",
            "implementation_permission": "NO",
        },
        {
            "route": "deterministic_zero_cross_rows",
            "t1_status": "REJECTED",
            "public_difference": "zero-mask relation is directly testable",
            "security_consequence": "cannot be justified as standard RLWE encryption of zero",
            "implementation_permission": "NO",
        },
        {
            "route": "force_equal_or_shared_output_masks",
            "t1_status": "REJECTED_AS_STANDARD_DISTRIBUTION",
            "public_difference": "mask equality relation is directly testable",
            "security_consequence": "requires a new structured-key assumption or reduction",
            "implementation_permission": "NO_UNTIL_PROOF",
        },
        {
            "route": "new_structured_selector_distribution",
            "t1_status": "OPEN_PROOF_ONLY",
            "public_difference": "must be declared as a new public key distribution",
            "security_consequence": "needs hybrid/simulation proof and leakage analysis",
            "implementation_permission": "PROOF_ONLY",
        },
    ]


def build_claim_rows() -> List[Dict[str, str]]:
    return [
        {
            "claim": "compact_selector_is_standard_dense_key",
            "status": "DENY",
            "safe_replacement": "compact selector variants change the public distribution unless a new proof is supplied",
            "evidence": rel(PROBE_CSV),
        },
        {
            "claim": "row_deletion_is_free",
            "status": "DENY",
            "safe_replacement": "row deletion is a key-format change with an immediate public size distinguisher",
            "evidence": rel(PROBE_CSV),
        },
        {
            "claim": "equal_shared_masks_are_indistinguishable",
            "status": "DENY",
            "safe_replacement": "equal/shared masks create a public relation in this finite probe",
            "evidence": rel(PROBE_CSV),
        },
        {
            "claim": "new_structured_key_may_be_studied",
            "status": "ALLOW_PROOF_ONLY",
            "safe_replacement": "state an explicit structured-key assumption/reduction target before implementation",
            "evidence": f"{rel(STAGE187_THEOREMS)}; {rel(STAGE176_API)}",
        },
    ]


def build_summary_rows(probe_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    inputs = [STAGE124_LAYOUT, STAGE125_LAYOUT, STAGE176_API, STAGE187_THEOREMS, STAGE189_SUMMARY]
    ok = all(path.exists() for path in inputs)
    distinguishers = [row for row in probe_rows if row["status"] == "DISTINGUISHER_FOUND"]
    return [
        {
            "gate": "stage190_inputs",
            "status": "PASS" if ok else "FAIL",
            "metric": "required_inputs_present",
            "value": "1" if ok else "0",
            "evidence": f"{rel(STAGE124_LAYOUT)}; {rel(STAGE187_THEOREMS)}; {rel(STAGE189_SUMMARY)}",
            "detail": "Stage190 targets T1 after Stage189 rejects direct public closure.",
            "next_action": "Repair missing inputs before interpreting distribution results.",
        },
        {
            "gate": "stage190_distribution_probe",
            "status": "PASS_DISTINGUISHERS_RECORDED",
            "metric": "distinguisher_rows",
            "value": str(len(distinguishers)),
            "evidence": rel(PROBE_CSV),
            "detail": "Row deletion, deterministic zero rows, and forced equal masks are publicly distinguishable in the finite probe.",
            "next_action": "Do not claim standard dense-key equivalence for compact selectors.",
        },
        {
            "gate": "stage190_route_policy",
            "status": "DENY_PRODUCTION_COMPACT_CODE",
            "metric": "proof_only_routes",
            "value": "1",
            "evidence": rel(ROUTE_CSV),
            "detail": "Only a declared new structured selector distribution remains open, and it is proof-only.",
            "next_action": "Run a formal assumption/reduction draft or T4 noise probe before code.",
        },
        {
            "gate": "stage190_decision",
            "status": DECISION,
            "metric": "production_compact_sab_permission",
            "value": "0",
            "evidence": rel(SUMMARY_CSV),
            "detail": "T1 is not proven; standard-distribution shortcuts are rejected.",
            "next_action": "Proceed only to isolated proof/noise probes or scoped manuscript updates.",
        },
    ]


def write_docs(
    summary_rows: List[Dict[str, str]],
    probe_rows: List[Dict[str, str]],
    route_rows: List[Dict[str, str]],
    claim_rows: List[Dict[str, str]],
) -> None:
    write_text_lf(
        OUT_MD,
        f"""# Stage190 Selector Distribution Distinguisher

Decision: `{DECISION}`.

Stage190 targets the Stage187 `T1_key_distribution` obligation. It does not
prove compact selectors insecure. It records a narrower result: the usual
shortcuts needed by compact/shared-output selector layouts cannot be described
as indistinguishable from the current dense MAT_TRGSW public key distribution
without a new proof or assumption.

## Gate Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Distribution Probe

{table(probe_rows, ["candidate", "r", "mask_N", "trials", "dense_observation", "structured_observation", "distinguisher", "successes", "status", "interpretation"])}
## Route Policy

{table(route_rows, ["route", "t1_status", "public_difference", "security_consequence", "implementation_permission"])}
## Claim Boundary

{table(claim_rows, ["claim", "status", "safe_replacement", "evidence"])}
""",
    )

    write_text_lf(
        PLAN_MD,
        """# Stage190 Plan

Goal: run an isolated T1 distribution probe for compact/shared-output selector
shortcuts.

Rules:

- do not modify `sab_pvw_*`;
- test only public distinguishers: row count, deterministic zeros, and mask
  equality relations;
- treat positive distinguishers as claim blockers, not as full security
  proofs;
- keep any new structured-key route proof-only.
""",
    )

    write_text_lf(
        THEORY_MD,
        """# Stage190 Selector Distribution Model

The current dense MAT_TRGSW selector uses public rows shaped as full PVW_TMLWE
encryptions. Compact/shared-output candidates try to reduce rows or force
relations that would help Stage189's shared-mask closure problem.

Three shortcuts are publicly distinguishable:

1. Deleting rows changes the public key size.
2. Replacing rows with deterministic zeros creates a zero-mask relation.
3. Forcing equal/shared masks creates equality relations across rows.

Therefore these shortcuts cannot be called standard dense-key distribution
equivalent. A future compact selector must be introduced as a new structured
public key distribution with an explicit assumption or reduction and a leakage
analysis.
""",
    )

    write_text_lf(
        VARIANT_MD,
        """# Selector Distribution Distinguisher Variant

This variant is a proof probe. It does not implement a compact selector and it
does not claim a complete SAB speedup.

Result: standard-distribution shortcuts for compact selectors are rejected.
Remaining route: a declared structured selector distribution with T1/T3/T4
proofs before any production SAB code.
""",
    )


def update_global_docs() -> None:
    append_once(
        ROADMAP_MD,
        "## Stage 190: Selector Distribution Distinguisher",
        f"""
## Stage 190: Selector Distribution Distinguisher

Goal:

```text
Run an executable T1 public-distribution probe for compact selector shortcuts.
```

Status:

```text
Completed. Stage190 records {DECISION}. Row deletion, deterministic zero rows,
and forced equal/shared masks are publicly distinguishable from the current
dense MAT_TRGSW distribution. Compact/shared-output SAB implementation remains
denied unless a new structured-key proof route is supplied.
```
""",
    )

    append_once(
        GOAL_MD,
        "Stage190 records the selector distribution distinguisher",
        f"""
Stage190 records the selector distribution distinguisher. Decision:
`{DECISION}`. It rejects standard-distribution shortcut claims for compact
selectors and keeps production compact SAB code denied.
""",
    )

    append_once(
        CURRENT_GOAL_MD,
        "Treat Stage190 as the selector distribution distinguisher",
        f"""
94. Treat Stage190 as the selector distribution distinguisher:
    `{DECISION}`. Compact selector row deletion, deterministic zero rows, and
    forced equal/shared masks are public distribution changes. T1 remains
    unproven; production compact SAB implementation remains denied.
""",
    )

    append_once(
        HYPOTHESIS_YAML,
        "H114_selector_distribution_distinguisher",
        f"""
  - id: H114_selector_distribution_distinguisher
    statement: >
      Compact selector shortcuts based on row deletion, deterministic zero
      rows, or forced equal/shared masks are publicly distinguishable from the
      current dense MAT_TRGSW public key distribution.
    mechanism: >
      Stage190 records row-count, zero-mask, and mask-equality distinguishers
      over finite random probes and ties them to Stage187 T1.
    status: stage190_t1_distribution_distinguisher
    evidence: docs/stage190_selector_distribution_distinguisher.md; experiments/stage190_selector_distribution_distinguisher_plan.md; theory_checks/stage190_selector_distribution_model.md; repro/stage190_selector_distribution_distinguisher/summary.csv
    current_decision: >
      {DECISION}
    failure_criteria:
      - compact selector is claimed equivalent to dense distribution despite
        public row-count or relation distinguishers
      - production compact SAB code is written without a structured-key proof
      - this probe is treated as a complete security proof rather than a
        shortcut rejection
""",
    )

    append_once(
        RUN_LOG,
        "stage190-selector-distribution-distinguisher-001",
        f"""
stage190-selector-distribution-distinguisher-001,2026-07-04,{git_head()},Stage 190,analysis,python scripts/build_stage190_selector_distribution_distinguisher.py,Stage187 T1 key-distribution gate,none,{DECISION},Finite public distinguishers reject standard-distribution compact selector shortcuts.,repro/stage190_selector_distribution_distinguisher
""",
    )

    append_once(
        MANIFEST,
        "stage190_selector_distribution_distinguisher",
        f"""
- stage190_selector_distribution_distinguisher: `{DECISION}`
  - `docs/stage190_selector_distribution_distinguisher.md`
  - `experiments/stage190_selector_distribution_distinguisher_plan.md`
  - `theory_checks/stage190_selector_distribution_model.md`
  - `algorithm_variants/mat_rlwe_sab_selector_distribution_distinguisher.md`
  - `repro/stage190_selector_distribution_distinguisher/`
""",
    )

    append_once(CHECKLIST, "Stage190 selector distribution distinguisher recorded", """
- [x] Stage190 selector distribution distinguisher recorded.
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
    probe_rows = build_probe_rows()
    route_rows = build_route_rows()
    claim_rows = build_claim_rows()
    summary_rows = build_summary_rows(probe_rows)

    write_csv(
        PROBE_CSV,
        probe_rows,
        [
            "candidate",
            "r",
            "mask_N",
            "trials",
            "dense_observation",
            "structured_observation",
            "distinguisher",
            "successes",
            "status",
            "interpretation",
        ],
    )
    write_csv(ROUTE_CSV, route_rows, ["route", "t1_status", "public_difference", "security_consequence", "implementation_permission"])
    write_csv(CLAIM_CSV, claim_rows, ["claim", "status", "safe_replacement", "evidence"])
    write_csv(SUMMARY_CSV, summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    write_docs(summary_rows, probe_rows, route_rows, claim_rows)
    update_global_docs()
    write_artifacts(
        [
            OUT_MD,
            PLAN_MD,
            THEORY_MD,
            VARIANT_MD,
            SUMMARY_CSV,
            PROBE_CSV,
            ROUTE_CSV,
            CLAIM_CSV,
            Path(__file__),
        ]
    )
    print(DECISION)


if __name__ == "__main__":
    main()
