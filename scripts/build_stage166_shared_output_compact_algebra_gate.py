#!/usr/bin/env python3
"""Stage166: shared-output compact algebra/keygen proof gate."""

from __future__ import annotations

import csv
import hashlib
import random
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage166_shared_output_compact_algebra_gate"

SUMMARY_CSV = OUT_DIR / "summary.csv"
TERM_CSV = OUT_DIR / "term_model.csv"
COUNTEREXAMPLE_CSV = OUT_DIR / "finite_field_counterexamples.csv"
NEXT_QUEUE_CSV = OUT_DIR / "next_stage_queue.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage166_shared_output_compact_algebra_gate.md"
PLAN_MD = ROOT / "experiments" / "stage166_shared_output_compact_algebra_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage166_shared_output_compact_algebra_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_shared_output_compact_algebra.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

PRIME = 65537
SEED = 166
TRIALS = 16
R_VALUES = (2, 4, 6, 8)


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(row.get(field, "") for field in fields) + " |")
    return "\n".join(out)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def append_once(path: Path, marker: str, block: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(path, text + block.strip("\n") + "\n")


def build_term_model() -> List[Dict[str, str]]:
    rows = []
    for r in R_VALUES:
        m = 1 + r
        dense = m * m
        shared_output_lane_local = m + 2 * r
        missing_cross_body = r * (r - 1)
        rows.append({
            "r": str(r),
            "state_polys": str(m),
            "dense_terms_per_level": str(dense),
            "shared_output_lane_local_terms": str(shared_output_lane_local),
            "missing_cross_body_terms": str(missing_cross_body),
            "dense_over_compact": f"{dense / shared_output_lane_local:.6f}",
            "interpretation": "Generic exact dense MAT needs all body-to-body cross terms unless keygen constrains them.",
        })
    return rows


def random_dense_matrix(rng: random.Random, m: int) -> List[List[int]]:
    return [[rng.randrange(1, PRIME) for _ in range(m)] for _ in range(m)]


def shared_output_lane_local_projection(matrix: List[List[int]]) -> List[List[int]]:
    m = len(matrix)
    out = [[0 for _ in range(m)] for _ in range(m)]
    for col in range(m):
        out[0][col] = matrix[0][col]
    for row in range(1, m):
        out[row][0] = matrix[row][0]
        out[row][row] = matrix[row][row]
    return out


def matrix_mismatches(a: List[List[int]], b: List[List[int]]) -> int:
    return sum(1 for i in range(len(a)) for j in range(len(a)) if a[i][j] != b[i][j])


def build_counterexamples() -> List[Dict[str, str]]:
    rng = random.Random(SEED)
    rows = []
    for r in R_VALUES:
        m = 1 + r
        for trial in range(TRIALS):
            dense = random_dense_matrix(rng, m)
            projected = shared_output_lane_local_projection(dense)
            mismatches = matrix_mismatches(dense, projected)
            rows.append({
                "r": str(r),
                "trial": str(trial),
                "field_prime": str(PRIME),
                "matrix_size": f"{m}x{m}",
                "mismatches": str(mismatches),
                "expected_missing_cross_body_terms": str(r * (r - 1)),
                "status": "COUNTEREXAMPLE_GENERIC_DENSE_NOT_REPRESENTABLE" if mismatches else "UNEXPECTED_EXACT",
            })
    return rows


def build_next_queue() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "stage": "167",
            "name": "native current r=6 counter refresh",
            "entry_condition": "Local WSL proxy cannot establish theoretical optimality; current tiled AVX remains the fastest tested exact route.",
            "gate": "Collect native Linux cycles/instructions/load/store/FMA/cache counters for current post-fusion r=6 path.",
            "failure_rule": "If native counters unavailable, keep FMA-vs-memory optimality claims blocked.",
        },
        {
            "priority": "P1",
            "stage": "168",
            "name": "structured compact keygen/noise design",
            "entry_condition": "Only if the research direction accepts a new selector distribution and proof obligation.",
            "gate": "Define keygen constraints that remove cross-body terms while preserving security/noise; then finite/toy phase gate.",
            "failure_rule": "Without a proof, no compact shared-output SAB integration.",
        },
        {
            "priority": "P2",
            "stage": "169",
            "name": "frontier closeout and paper-claim boundary refresh",
            "entry_condition": "After native counters or structured-keygen proof status is known.",
            "gate": "Update final contribution wording: engineering optimization versus new algorithm/keygen claim.",
            "failure_rule": "No unsupported novelty or theoretical optimality wording.",
        },
    ]


def decide(counterexamples: List[Dict[str, str]]) -> str:
    if any(row["status"] == "UNEXPECTED_EXACT" for row in counterexamples):
        return "FAIL_STAGE166_COUNTEREXAMPLE_MODEL_UNEXPECTED_EXACT"
    return "PASS_STAGE166_GENERIC_COMPACT_EXACTNESS_BLOCKED_KEYGEN_PROOF_REQUIRED"


def build_summary(decision: str, counterexamples: List[Dict[str, str]]) -> List[Dict[str, str]]:
    min_mismatch = min(int(row["mismatches"]) for row in counterexamples)
    return [
        {
            "gate": "stage166_term_model",
            "status": "PASS",
            "metric": "generic_dense_terms",
            "value": "(1+r)^2",
            "evidence": rel(TERM_CSV),
            "detail": "Generic MAT selector is a full linear map from 1+r input rows to 1+r outputs.",
            "next_action": "Compact exactness needs keygen constraints, not only a smaller data layout.",
        },
        {
            "gate": "stage166_finite_field_counterexamples",
            "status": "PASS" if min_mismatch > 0 else "FAIL",
            "metric": "min_mismatches",
            "value": str(min_mismatch),
            "evidence": rel(COUNTEREXAMPLE_CSV),
            "detail": "Random dense selectors over a finite field are not representable by the lane-local shared-output compact structure.",
            "next_action": "Do not integrate compact SAB without a structured keygen/noise proof.",
        },
        {
            "gate": "stage166_decision",
            "status": decision,
            "metric": "compact_route_status",
            "value": "keygen_proof_required",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Stage166 blocks generic compact exactness claims while preserving a proof-driven structured-keygen research route.",
            "next_action": "Run native counters for the current exact route or start formal structured-keygen design.",
        },
    ]


def artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        rows.append({
            "path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path) if path.exists() and path.is_file() else "",
            "bytes": str(path.stat().st_size) if path.exists() and path.is_file() else "",
        })
    write_csv(ARTIFACT_CSV, rows, ["path", "exists", "sha256", "bytes"])


def write_docs(
    decision: str,
    summary: List[Dict[str, str]],
    term_rows: List[Dict[str, str]],
    counter_rows: List[Dict[str, str]],
    next_queue: List[Dict[str, str]],
) -> None:
    summary_fields = ["gate", "status", "metric", "value", "evidence", "detail", "next_action"]
    term_fields = [
        "r", "state_polys", "dense_terms_per_level",
        "shared_output_lane_local_terms", "missing_cross_body_terms",
        "dense_over_compact", "interpretation",
    ]
    counter_fields = [
        "r", "trial", "field_prime", "matrix_size", "mismatches",
        "expected_missing_cross_body_terms", "status",
    ]
    next_fields = ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"]

    sample_counter = counter_rows[:8]
    write_text_lf(OUT_MD, f"""# Stage166 Shared-Output Compact Algebra Gate

Decision: `{decision}`.

Stage166 tests whether a lane-local shared-output compact structure can
represent a generic dense MAT selector. It cannot: random dense finite-field
selectors require cross-body terms that the compact structure omits. Therefore
compact SAB is not an implementation-ready route unless a new structured
keygen/security/noise proof intentionally removes those terms.

## Gate Summary

{table(summary, summary_fields)}

## Term Model

{table(term_rows, term_fields)}

## Counterexample Sample

{table(sample_counter, counter_fields)}

Full counterexamples are in `{rel(COUNTEREXAMPLE_CSV)}`.

## Next Queue

{table(next_queue, next_fields)}
""")

    write_text_lf(PLAN_MD, """# Stage166 Validation Plan

Goal: decide whether shared-output compact SAB can be treated as a generic
implementation optimization, or whether it requires a new keygen/proof route.

Model:

- Dense MAT selector: arbitrary `(1+r) x (1+r)` matrix over a finite field.
- Compact shared-output lane-local selector: shared mask output can depend on
  all inputs, but body lane q depends only on shared input and body q.

Gate:

- random dense finite-field matrices must produce nonzero mismatches under the
  compact projection;
- if mismatches exist for all tested r/trials, generic compact exactness is
  blocked and structured keygen proof is required.
""")

    write_text_lf(THEORY_MD, """# Stage166 Algebra Model

Let `m = 1 + r`. A generic dense MAT external product is a linear map:

```text
y = M x,  M in F^{m x m}
```

where `x` contains the shared-mask decomposed row and the `r` body rows, and
`y` contains the shared mask output plus `r` body outputs.

The lane-local shared-output compact projection keeps:

- the full shared output row `M[0,*]`;
- each body output's shared-input term `M[q,0]`;
- each body output's diagonal body term `M[q,q]`.

It drops body-to-body cross terms `M[q,j]` for `q != j`, `q,j > 0`. There are
`r(r-1)` such terms. For a generic encrypted dense selector, these terms are
not guaranteed to be zero, so the compact structure is not exact without a new
structured key distribution and proof.
""")

    write_text_lf(VARIANT_MD, f"""# Shared-Output Compact Algebra Route

Stage166 does not implement production SAB. It classifies the compact route.

Result:

```text
{decision}
```

Allowed next compact claim:

```text
Only a structured keygen/noise/security proof can reopen compact shared-output
SAB integration.
```

Disallowed claim:

```text
Compact shared-output is a drop-in implementation optimization for the generic
dense MAT selector.
```
""")


def update_global_docs(decision: str) -> None:
    append_once(ROADMAP_MD, "## Stage 166: Shared-Output Compact Algebra Gate", f"""
## Stage 166: Shared-Output Compact Algebra Gate

Goal:

```text
Test whether shared-output compact SAB is a generic exact implementation route
or requires a new structured keygen/noise proof.
```

Status:

```text
Completed. Stage166 records {decision}. Generic compact exactness is blocked
by missing body-to-body cross terms; compact SAB remains proof-driven, not an
implementation-ready optimization.
```
""")

    append_once(GOAL_MD, "Stage166 blocks generic compact exactness", f"""
Stage166 blocks generic compact exactness after Stage165. Decision:
`{decision}`. It preserves compact SAB only as a structured-keygen research
route and directs immediate engineering evidence toward native counters for
the current exact tiled-AVX path.
""")

    append_once(CURRENT_GOAL_MD, "70. Treat Stage166 as the shared-output compact algebra gate", f"""
70. Treat Stage166 as the shared-output compact algebra gate:
    `{decision}`. Generic compact shared-output is not a drop-in optimization;
    it needs structured keygen/security/noise proof before SAB integration.
""")

    append_once(HYPOTHESIS_YAML, "id: H90_shared_output_compact_algebra", f"""
  - id: H90_shared_output_compact_algebra
    statement: >
      A lane-local shared-output compact selector cannot represent a generic
      dense MAT selector exactly because it omits body-to-body cross terms.
    mechanism: >
      Dense MAT is an arbitrary `(1+r)x(1+r)` linear map, while lane-local
      compact keeps only the shared row, body shared-input terms, and diagonal
      body terms.
    status: stage166_shared_output_compact_algebra_gate
    evidence: docs/stage166_shared_output_compact_algebra_gate.md; experiments/stage166_shared_output_compact_algebra_gate_plan.md; theory_checks/stage166_shared_output_compact_algebra_model.md; repro/stage166_shared_output_compact_algebra_gate/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - random dense finite-field selectors are representable with zero mismatches
      - compact SAB is integrated without a structured keygen/security/noise proof
      - generic dense exactness is claimed from lane-local compact evidence
""")

    append_once(RUN_LOG, "stage166-shared-output-compact-algebra-gate-001", f"""
stage166-shared-output-compact-algebra-gate-001,2026-07-03,{git_head()},Stage 166,analysis,python scripts/build_stage166_shared_output_compact_algebra_gate.py,r=2/4/6/8; finite_field_prime={PRIME}; trials={TRIALS},seed-{SEED},{decision},Shared-output compact algebra/keygen proof gate.,repro/stage166_shared_output_compact_algebra_gate
""")

    append_once(MANIFEST, "stage166_shared_output_compact_algebra_gate", f"""
- stage166_shared_output_compact_algebra_gate: `{decision}`
  - `docs/stage166_shared_output_compact_algebra_gate.md`
  - `experiments/stage166_shared_output_compact_algebra_gate_plan.md`
  - `theory_checks/stage166_shared_output_compact_algebra_model.md`
  - `algorithm_variants/mat_rlwe_sab_shared_output_compact_algebra.md`
  - `repro/stage166_shared_output_compact_algebra_gate/`
""")

    append_once(CHECKLIST, "Stage166 shared-output compact algebra gate pack recorded", """
- [x] Stage166 shared-output compact algebra gate pack recorded.
""")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    term_rows = build_term_model()
    counter_rows = build_counterexamples()
    next_queue = build_next_queue()
    decision = decide(counter_rows)
    summary = build_summary(decision, counter_rows)

    write_csv(TERM_CSV, term_rows, [
        "r", "state_polys", "dense_terms_per_level",
        "shared_output_lane_local_terms", "missing_cross_body_terms",
        "dense_over_compact", "interpretation",
    ])
    write_csv(COUNTEREXAMPLE_CSV, counter_rows, [
        "r", "trial", "field_prime", "matrix_size", "mismatches",
        "expected_missing_cross_body_terms", "status",
    ])
    write_csv(NEXT_QUEUE_CSV, next_queue, [
        "priority", "stage", "name", "entry_condition", "gate", "failure_rule",
    ])
    write_csv(SUMMARY_CSV, summary, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])

    write_docs(decision, summary, term_rows, counter_rows, next_queue)
    update_global_docs(decision)
    artifact_index([
        OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, SUMMARY_CSV, TERM_CSV,
        COUNTEREXAMPLE_CSV, NEXT_QUEUE_CSV, Path(__file__),
    ])

    print(decision)
    print(f"min_mismatches={min(int(row['mismatches']) for row in counter_rows)}")


if __name__ == "__main__":
    main()
