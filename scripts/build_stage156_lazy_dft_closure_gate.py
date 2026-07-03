#!/usr/bin/env python3
"""Stage156: naive lazy-DFT accumulator closure gate.

The goal is to decide whether the large Stage155 materialization component can
be attacked by simply keeping PVW/MAT-SAB accumulators in DFT form across CMUX
updates. The gate is intentionally finite:

1. scan the production API boundary;
2. reproduce MOSFHET's torus gadget decomposition formula;
3. test whether decomposition can be linearly maintained across SAB add/sub
   updates without returning to torus coefficients.
"""

from __future__ import annotations

import csv
import hashlib
import random
import re
from pathlib import Path
from typing import Dict, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage156_lazy_dft_closure_gate"

HEADER = ROOT / "src" / "mosfhet" / "include" / "mosfhet.h"
MATTRGSW = ROOT / "src" / "mosfhet" / "src" / "mattrgsw.c"
POLYNOMIAL = ROOT / "src" / "mosfhet" / "src" / "polynomial.c"
STAGE155_SUMMARY = ROOT / "repro" / "stage155_same_format_frontier_refresh" / "summary.csv"

SUMMARY_CSV = OUT_DIR / "summary.csv"
API_CSV = OUT_DIR / "source_api_scan.csv"
NONLINEAR_CSV = OUT_DIR / "decomposition_nonlinearity.csv"
CLOSURE_CSV = OUT_DIR / "closure_decision.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

DOC_STAGE = ROOT / "docs" / "stage156_lazy_dft_closure_gate.md"
DOC_PLAN = ROOT / "experiments" / "stage156_lazy_dft_closure_gate_plan.md"
DOC_THEORY = ROOT / "theory_checks" / "stage156_decomposition_closure_model.md"
DOC_VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_lazy_dft_state.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_DOC = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

MASK64 = (1 << 64) - 1


def write_csv(path: Path, rows: List[Dict[str, object]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def append_once(path: Path, marker: str, text: str) -> None:
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in current:
        return
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        if current and not current.endswith("\n"):
            handle.write("\n")
        handle.write(text)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def decomp_digit(x: int, bg_bit: int, l: int, digit_index: int) -> int:
    """Match polynomial_decompose_i for one 64-bit torus coefficient."""
    bit_size = 64
    half_bg = 1 << (bg_bit - 1)
    h_mask = (1 << bg_bit) - 1
    h_bit = bit_size - (digit_index + 1) * bg_bit
    offset = 1 << (bit_size - l * bg_bit - 1)
    for j in range(l):
        offset += 1 << (bit_size - j * bg_bit - 1)
    coeff_off = (x + offset) & MASK64
    return int(((coeff_off >> h_bit) & h_mask) - half_bg)


def decomp_vec(poly: List[int], bg_bit: int, l: int) -> List[List[int]]:
    return [[decomp_digit(x, bg_bit, l, t) for x in poly] for t in range(l)]


def add_poly(a: List[int], b: List[int]) -> List[int]:
    return [(x + y) & MASK64 for x, y in zip(a, b)]


def neg_poly(a: List[int]) -> List[int]:
    return [(-x) & MASK64 for x in a]


def negacyclic_rotate(poly: List[int], shift: int) -> List[int]:
    n = len(poly)
    out = [0] * n
    for i, coeff in enumerate(poly):
        dst = i + shift
        sign = 1
        while dst >= n:
            dst -= n
            sign *= -1
        out[dst] = coeff if sign > 0 else ((-coeff) & MASK64)
    return out


def count_mismatch(lhs: List[List[int]], rhs: List[List[int]]) -> Tuple[int, str]:
    mismatches = 0
    example = ""
    for t, (row_l, row_r) in enumerate(zip(lhs, rhs)):
        for c, (x, y) in enumerate(zip(row_l, row_r)):
            if x != y:
                mismatches += 1
                if not example:
                    example = f"t={t},coeff={c},lhs={x},rhs={y}"
    return mismatches, example


def scan_api() -> List[Dict[str, object]]:
    header = read_text(HEADER)
    mattrgsw = read_text(MATTRGSW)
    combined = header + "\n" + mattrgsw

    dense_sig = "void mat_trgsw_mul_pvmtmlwe_DFT(PVW_TMLWE_DFT out, PVW_TMLWE in"
    compact_sig = "void mat_trgsw_compact_mul_pvmtmlwe_DFT(MAT_TRGSW_COMPACT_OUTPUT_DFT out, PVW_TMLWE in"
    dft_input_re = re.compile(r"mat_trgsw(?:_compact)?_mul_[A-Za-z0-9_]*DFT\s*\([^;{)]*PVW_TMLWE_DFT\s+in")
    decomp_call_present = "pvmtmlwe_decompose(scratch->dec, in" in mattrgsw
    compact_decomp_present = "polynomial_decompose_i(scratch->dec_shared, in->a[0]" in mattrgsw

    return [
        {
            "check": "dense_external_product_signature",
            "status": "PASS" if dense_sig in header or dense_sig in mattrgsw else "FAIL",
            "evidence": "mat_trgsw_mul_pvmtmlwe_DFT takes PVW_TMLWE torus input",
            "detail": rel(HEADER) + "; " + rel(MATTRGSW),
        },
        {
            "check": "compact_external_product_signature",
            "status": "PASS" if compact_sig in header or compact_sig in mattrgsw else "FAIL",
            "evidence": "mat_trgsw_compact_mul_pvmtmlwe_DFT also takes PVW_TMLWE torus input",
            "detail": rel(HEADER) + "; " + rel(MATTRGSW),
        },
        {
            "check": "no_dft_input_external_product_api",
            "status": "PASS" if dft_input_re.search(combined) is None else "FAIL",
            "evidence": "No MAT external-product entry point accepts PVW_TMLWE_DFT as the decomposed input state.",
            "detail": "regex_scan=mat_trgsw*_mul*DFT(... PVW_TMLWE_DFT in)",
        },
        {
            "check": "dense_decomposition_inside_ep",
            "status": "PASS" if decomp_call_present else "FAIL",
            "evidence": "Dense MAT EP calls pvmtmlwe_decompose before converting digits to DFT.",
            "detail": rel(MATTRGSW) + ":673",
        },
        {
            "check": "compact_decomposition_inside_ep",
            "status": "PASS" if compact_decomp_present else "FAIL",
            "evidence": "Compact MAT EP calls polynomial_decompose_i on shared/body torus components.",
            "detail": rel(MATTRGSW) + ":853-860",
        },
    ]


def run_nonlinearity_trials() -> List[Dict[str, object]]:
    rng = random.Random(20260703)
    configs = [
        {"bg_bit": 7, "l": 1, "n": 8, "trials": 256},
        {"bg_bit": 7, "l": 2, "n": 8, "trials": 256},
        {"bg_bit": 8, "l": 2, "n": 16, "trials": 256},
    ]
    rows: List[Dict[str, object]] = []
    for cfg in configs:
        bg_bit = int(cfg["bg_bit"])
        l = int(cfg["l"])
        n = int(cfg["n"])
        trials = int(cfg["trials"])
        add_bad = neg_bad = rot_bad = 0
        add_ex = neg_ex = rot_ex = ""
        for _ in range(trials):
            a = [rng.getrandbits(64) for _ in range(n)]
            b = [rng.getrandbits(64) for _ in range(n)]

            d_a = decomp_vec(a, bg_bit, l)
            d_b = decomp_vec(b, bg_bit, l)
            d_add = decomp_vec(add_poly(a, b), bg_bit, l)
            d_add_linear = [[x + y for x, y in zip(row_a, row_b)] for row_a, row_b in zip(d_a, d_b)]
            mismatches, example = count_mismatch(d_add, d_add_linear)
            if mismatches:
                add_bad += 1
                add_ex = add_ex or example

            d_neg = decomp_vec(neg_poly(a), bg_bit, l)
            d_neg_linear = [[-x for x in row] for row in d_a]
            mismatches, example = count_mismatch(d_neg, d_neg_linear)
            if mismatches:
                neg_bad += 1
                neg_ex = neg_ex or example

            shift = rng.randrange(1, n)
            d_rot = decomp_vec(negacyclic_rotate(a, shift), bg_bit, l)
            d_rot_linear = negacyclic_rotate_decomp(d_a, shift)
            mismatches, example = count_mismatch(d_rot, d_rot_linear)
            if mismatches:
                rot_bad += 1
                rot_ex = rot_ex or example

        rows.append(
            {
                "config": f"Bg_bit={bg_bit};l={l};N={n}",
                "trials": trials,
                "addition_nonlinear_trials": add_bad,
                "addition_example": add_ex,
                "negation_nonlinear_trials": neg_bad,
                "negation_example": neg_ex,
                "negacyclic_rotation_nonlinear_trials": rot_bad,
                "negacyclic_rotation_example": rot_ex,
                "status": "PASS_NEGATIVE_CONTROL" if add_bad and neg_bad and rot_bad else "FAIL",
            }
        )
    return rows


def negacyclic_rotate_decomp(digits: List[List[int]], shift: int) -> List[List[int]]:
    n = len(digits[0])
    out: List[List[int]] = []
    for row in digits:
        dst = [0] * n
        for i, coeff in enumerate(row):
            j = i + shift
            sign = 1
            while j >= n:
                j -= n
                sign *= -1
            dst[j] = coeff if sign > 0 else -coeff
        out.append(dst)
    return out


def build() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    api_rows = scan_api()
    nonlinear_rows = run_nonlinearity_trials()

    api_pass = all(row["status"] == "PASS" for row in api_rows)
    nonlinear_pass = all(row["status"] == "PASS_NEGATIVE_CONTROL" for row in nonlinear_rows)
    stage155_exists = STAGE155_SUMMARY.exists()

    if not stage155_exists:
        decision = "FAIL_STAGE156_MISSING_STAGE155_PRECONDITION"
        selected_next = "restore Stage155 before Stage156"
    elif api_pass and nonlinear_pass:
        decision = "REJECT_STAGE156_NAIVE_LAZY_DFT_STATE_NOT_CLOSED"
        selected_next = "Stage157 compact/shared-source production microbench or decomposed-cache feasibility"
    else:
        decision = "FAIL_STAGE156_GATE_INCONCLUSIVE"
        selected_next = "repair API scan or decomposition model before routing"

    closure_rows = [
        {
            "gate": "stage156_precondition",
            "status": "PASS" if stage155_exists else "FAIL",
            "metric": "stage155_summary_exists",
            "value": rel(STAGE155_SUMMARY) if stage155_exists else "MISSING",
            "evidence": rel(STAGE155_SUMMARY),
            "detail": "Stage156 is valid only after Stage155 routes to representation feasibility.",
            "next_action": "Restore or rerun Stage155 if missing.",
        },
        {
            "gate": "stage156_api_boundary",
            "status": "PASS" if api_pass else "FAIL",
            "metric": "torus_input_ep;no_dft_input_ep;decomp_inside_ep",
            "value": "PASS" if api_pass else "FAIL",
            "evidence": rel(API_CSV),
            "detail": "Production MAT EP boundaries require torus input and decompose internally.",
            "next_action": "Do not plan lazy DFT insertion without a new EP API.",
        },
        {
            "gate": "stage156_decomposition_closure",
            "status": "PASS_NEGATIVE_CONTROL" if nonlinear_pass else "FAIL",
            "metric": "add;neg;negacyclic_rotation",
            "value": "nonlinear_counterexamples_found" if nonlinear_pass else "missing_counterexample",
            "evidence": rel(NONLINEAR_CSV),
            "detail": "MOSFHET-style gadget decomposition is not linearly maintainable under SAB updates.",
            "next_action": "Reject naive lazy DFT state; use exact torus/decomp cache or compact-state redesign.",
        },
        {
            "gate": "stage156_decision",
            "status": decision,
            "metric": "lazy_dft_state_route",
            "value": "naive_lazy_dft_rejected",
            "evidence": rel(CLOSURE_CSV),
            "detail": "A DFT accumulator alone cannot feed the next external product because decomposition is coefficient-domain and nonlinear.",
            "next_action": selected_next,
        },
    ]

    next_rows = [
        {
            "stage": "157",
            "priority": "P0",
            "name": "decomposed-cache or compact-state feasibility",
            "goal": "Test a representation that stores enough exact coefficient/decomposition state to reduce materialization/decomposition cost without relying on linear DFT-only updates.",
            "correctness_gate": "phase/decomposition equality against production dense MAT EP for r=4/r=6 and N=2048.",
            "performance_gate": "T_kernel/r must beat current dense MAT EP after cache update overhead.",
            "failure_handling": "Reject if cache invalidation or update cost cancels the saved materialization/decomposition work.",
        },
        {
            "stage": "158",
            "priority": "P1",
            "name": "native perf/counter attribution refresh",
            "goal": "Measure current H14 r=6 path on native Linux to separate memory traffic, FMA throughput, and spills.",
            "correctness_gate": "full-SAB correctness logs pass under same parameters.",
            "performance_gate": "Counters explain whether current AVX512 is FMA-bound or memory-bound.",
            "failure_handling": "If unavailable, keep theoretical AVX optimality unclaimed.",
        },
    ]

    write_csv(API_CSV, api_rows, ["check", "status", "evidence", "detail"])
    write_csv(NONLINEAR_CSV, nonlinear_rows, [
        "config", "trials", "addition_nonlinear_trials", "addition_example",
        "negation_nonlinear_trials", "negation_example",
        "negacyclic_rotation_nonlinear_trials", "negacyclic_rotation_example",
        "status",
    ])
    write_csv(CLOSURE_CSV, closure_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    write_csv(NEXT_CSV, next_rows, ["stage", "priority", "name", "goal", "correctness_gate", "performance_gate", "failure_handling"])
    write_csv(SUMMARY_CSV, closure_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])

    write_docs(api_rows, nonlinear_rows, closure_rows, next_rows, decision)
    update_global_docs(decision)

    artifacts = [
        SUMMARY_CSV, API_CSV, NONLINEAR_CSV, CLOSURE_CSV, NEXT_CSV,
        DOC_STAGE, DOC_PLAN, DOC_THEORY, DOC_VARIANT,
    ]
    artifact_rows = [
        {"path": rel(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
        for path in artifacts
    ]
    write_csv(ARTIFACT_CSV, artifact_rows, ["path", "sha256", "bytes"])

    print(f"Stage156 lazy-DFT closure gate: {decision}")
    print(f"Wrote {rel(SUMMARY_CSV)}")


def write_docs(
    api_rows: List[Dict[str, object]],
    nonlinear_rows: List[Dict[str, object]],
    closure_rows: List[Dict[str, object]],
    next_rows: List[Dict[str, object]],
    decision: str,
) -> None:
    api_table = md_table(api_rows, ["check", "status", "evidence", "detail"])
    nonlinear_table = md_table(nonlinear_rows, [
        "config", "trials", "addition_nonlinear_trials",
        "negation_nonlinear_trials", "negacyclic_rotation_nonlinear_trials",
        "status",
    ])
    closure_table = md_table(closure_rows, ["gate", "status", "metric", "value", "next_action"])
    next_table = md_table(next_rows, ["stage", "priority", "name", "goal", "performance_gate"])

    DOC_STAGE.write_text(f"""# Stage156 Lazy-DFT Closure Gate

Decision: `{decision}`

Stage156 tests the most direct representation-changing idea after Stage155:
keep the PVW/MAT-SAB accumulator in DFT form and avoid materializing every
CMUX output. The gate rejects only the naive DFT-only state, not all future
representation changes.

## API Scan

{api_table}

## Decomposition Nonlinearity

{nonlinear_table}

The toy model exactly mirrors the 64-bit coefficient formula in
`polynomial_decompose_i`: offset, high-bit extraction, mask, and centered
digit subtraction. The negative-control pass means counterexamples were found:
`decompose(x+y) != decompose(x)+decompose(y)`,
`decompose(-x) != -decompose(x)`, and negacyclic sign rotations are not
linearly maintainable on decomposed digits.

## Gate Result

{closure_table}

## Next Queue

{next_table}

Interpretation: a DFT accumulator can represent the polynomial value, but the
next MAT external product needs coefficient-domain gadget digits. Because the
digits are nonlinear under the SAB updates, a DFT-only lazy state is not a
closed iterative representation. Future work must store enough exact torus or
decomposed state, or use a compact/shared-source representation with its own
correctness and performance gates.
""", encoding="utf-8", newline="\n")

    DOC_PLAN.write_text(f"""# Stage156 Experiment Plan

Goal: decide whether the Stage155 `from_DFT` frontier can be attacked by a
naive lazy-DFT accumulator.

Inputs:

- `{rel(HEADER)}` public API signatures.
- `{rel(MATTRGSW)}` production MAT external product implementation.
- `{rel(POLYNOMIAL)}` production gadget decomposition formula.
- `{rel(STAGE155_SUMMARY)}` route precondition.

Correctness gate:

- production scan must show the real EP boundary being evaluated.
- finite decomposition tests must find or fail to find counterexamples under
  MOSFHET-style decomposition.

Performance gate:

- no timing claim is made here; this gate only permits a later implementation
  if the representation is algebraically closed.

Failure handling:

- if naive DFT is not closed, do not implement it in `sab_pvw_*`.
- route to exact decomposed-cache or compact-state feasibility instead.
""", encoding="utf-8", newline="\n")

    DOC_THEORY.write_text("""# Stage156 Decomposition Closure Model

The production MAT external product does not multiply a DFT ciphertext by a
selector directly. It first decomposes the torus coefficients into gadget
digits and converts those digits to DFT:

```text
PVW_TMLWE torus input
  -> gadget decomposition
  -> DFT(digits)
  -> selector addmul
```

The SAB update is linear in torus polynomial space, but gadget decomposition is
piecewise and includes centered digit extraction. Carries make it nonlinear:

```text
D(x + y) != D(x) + D(y)
D(-x)    != -D(x)
```

Since DFT is linear, it cannot repair a mismatch already present in the
coefficient-domain digits. Therefore, a DFT-only accumulator does not provide
the information needed by the next external product.

This rejects only the naive lazy-DFT state. A richer representation that keeps
exact torus coefficients, invalidates/rebuilds decomposition caches, or changes
the selector/ciphertext format remains a valid future hypothesis.
""", encoding="utf-8", newline="\n")

    DOC_VARIANT.write_text("""# MAT-RLWE SAB Lazy DFT State Variant

Variant tested:

```text
Keep each PVW/MAT-SAB accumulator in DFT form across CMUX/RGSW steps, hoping to
avoid per-update materialization.
```

Stage156 decision:

```text
REJECT naive DFT-only state.
```

Reason:

- production MAT EP requires torus input and decomposes inside the EP;
- no current EP API accepts a DFT/decomposed accumulator input;
- gadget decomposition is not linear under addition, subtraction, negation, or
  negacyclic sign rotations.

Allowed successor variants:

- exact torus plus decomposition cache;
- compact/shared-source representation with proven closure;
- native-counter analysis to decide whether implementation work should target
  materialization, decomposition, or dense addmul.
""", encoding="utf-8", newline="\n")


def md_table(rows: List[Dict[str, object]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("\n", " ") for field in fields) + " |")
    return "\n".join(out)


def update_global_docs(decision: str) -> None:
    append_once(
        ROADMAP,
        "## Stage 156: Lazy-DFT Closure Gate",
        f"""## Stage 156: Lazy-DFT Closure Gate

Goal:

```text
Test whether the Stage155 materialization frontier can be attacked by a naive
DFT-only accumulator state across SAB CMUX/RGSW updates.
```

Status:

```text
Completed. Stage156 records {decision}. The production API requires torus
input for MAT EP, and finite MOSFHET-style decomposition tests show
nonlinearity under addition, negation, and negacyclic sign rotations.
```
""",
    )
    append_once(
        GOAL_DOC,
        "Stage156 rejects naive lazy-DFT state",
        f"""Stage156 rejects naive lazy-DFT state after Stage155. Decision:
`{decision}`. It confirms that materialization cannot be removed by keeping
only DFT accumulator values, because the next MAT external product needs
coefficient-domain gadget decomposition. Future representation work must keep
exact torus/decomposition state or use a compact/shared-source format with
separate gates.
""",
    )
    append_once(
        CURRENT_GOAL,
        "60. Treat Stage156 as the lazy-DFT closure gate",
        f"""60. Treat Stage156 as the lazy-DFT closure gate:
    `{decision}`. It rejects the naive DFT-only accumulator route and routes
    next to exact decomposed-cache or compact/shared-source feasibility, not to
    direct `sab_pvw_*` integration.
""",
    )
    append_once(
        HYPOTHESES,
        "H80_lazy_dft_state_closure",
        f"""  - id: H80_lazy_dft_state_closure
    statement: >
      A naive DFT-only accumulator state is not closed for iterative
      MAT-RLWE SAB because the next external product requires nonlinear
      coefficient-domain gadget decomposition.
    mechanism: >
      Production MAT EP takes PVW_TMLWE torus input and calls decomposition
      internally; finite tests show decomposition is nonlinear under SAB
      addition, negation, and negacyclic sign rotations.
    status: stage156_lazy_dft_closure_gate
    evidence: docs/stage156_lazy_dft_closure_gate.md; experiments/stage156_lazy_dft_closure_gate_plan.md; theory_checks/stage156_decomposition_closure_model.md; algorithm_variants/mat_rlwe_sab_lazy_dft_state.md; repro/stage156_lazy_dft_closure_gate/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - a MAT external-product API accepting DFT/decomposed accumulator input already exists
      - decomposition is linearly maintainable under addition, negation, and negacyclic rotations
""",
    )
    append_once(
        RUN_LOG,
        "stage156-lazy-dft-closure-gate-001",
        f"2026-07-03,stage156-lazy-dft-closure-gate-001,analysis,none,SET_2_3_2048,BINARY,{decision},docs/stage156_lazy_dft_closure_gate.md;repro/stage156_lazy_dft_closure_gate/summary.csv\n",
    )
    append_once(
        MANIFEST,
        "stage156_lazy_dft_closure_gate",
        "- `repro/stage156_lazy_dft_closure_gate/`: Stage156 lazy-DFT closure gate outputs.\n",
    )
    append_once(
        CHECKLIST,
        "Stage156 lazy-DFT closure gate",
        "- [x] Stage156 lazy-DFT closure gate generated from source API scan and finite decomposition tests.\n",
    )


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


if __name__ == "__main__":
    build()
