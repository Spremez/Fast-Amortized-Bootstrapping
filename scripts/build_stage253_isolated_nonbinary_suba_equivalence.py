"""Stage253: isolated non-binary PVW sub_a equivalence.

This stage validates the Stage252 selector/key skeleton at the equation level.
It uses a finite negacyclic ring model with independent body lanes and checks
that include-zero and ternary selector updates match scalar-lane references.
It also records binary-naive negative controls.
"""

from __future__ import annotations

import csv
import hashlib
import subprocess
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage253_isolated_nonbinary_suba_equivalence"

INPUTS = {
    "stage251_semantic_equations": ROOT / "repro" / "stage251_nonbinary_selector_semantics" / "semantic_equation_matrix.csv",
    "stage252_proof_gate": ROOT / "repro" / "stage252_nonbinary_mat_selector_key_skeleton" / "proof_gate.csv",
    "stage252_skeleton_design": ROOT / "repro" / "stage252_nonbinary_mat_selector_key_skeleton" / "skeleton_design_matrix.csv",
    "stage252_key_probe": ROOT / "repro" / "stage252_nonbinary_mat_selector_key_skeleton" / "toy_key_object_probe.csv",
    "sab_header": ROOT / "include" / "sab.h",
    "sab_pvw_header": ROOT / "include" / "sab_pvw.h",
    "scalar_sab_source": ROOT / "src" / "sparse_amortized_bootstrap.c",
    "pvw_sab_source": ROOT / "src" / "sab_pvw.c",
}

DOC = ROOT / "docs" / "stage253_isolated_nonbinary_suba_equivalence.md"
PLAN = ROOT / "experiments" / "stage253_isolated_nonbinary_suba_equivalence_plan.md"
THEORY = ROOT / "theory_checks" / "stage253_isolated_nonbinary_suba_equivalence_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage253_isolated_nonbinary_suba_equivalence.md"

INPUT_STATUS = OUT / "input_status.csv"
EQUATIONS = OUT / "equation_model.csv"
PROBE = OUT / "lane_equivalence_probe.csv"
NEGATIVE = OUT / "negative_control_matrix.csv"
TRACE = OUT / "trace_sample.csv"
SOURCE_ISOLATION = OUT / "source_isolation.csv"
ADMISSION = OUT / "admission_decision.csv"
CLAIM = OUT / "claim_boundary.csv"
GATES = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage253_report.md"
REPRO_CMDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION = "PASS_STAGE253_ISOLATED_NONBINARY_SUBA_EQUIVALENCE_READY_KEYGEN_NOISE_PREFLIGHT"
MODULUS = 257


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def run_git(args: list[str]) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return proc.stdout.strip()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text.rstrip() + "\n")


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        if current and not current.endswith("\n"):
            f.write("\n")
        f.write(text.lstrip("\n").rstrip() + "\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def table(rows: list[dict[str, object]], fields: list[str]) -> str:
    if not rows:
        return "_No rows._\n"
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("\n", " ") for field in fields) + " |")
    return "\n".join(lines) + "\n"


def input_rows() -> list[dict[str, object]]:
    return [
        {
            "input_id": key,
            "path": rel(path),
            "status": "present" if path.exists() else "missing",
            "bytes": path.stat().st_size if path.exists() else 0,
        }
        for key, path in INPUTS.items()
    ]


def stage252_passes() -> bool:
    rows = read_csv(INPUTS["stage252_proof_gate"])
    return bool(rows) and rows[-1].get("status") == "PASS_STAGE252_NONBINARY_MAT_SELECTOR_KEY_SKELETON_READY_ISOLATED_EQUIVALENCE"


def equation_rows() -> list[dict[str, object]]:
    return [
        {
            "branch": "include_zero",
            "selector_family": "s_coff",
            "scalar_equation": "p' = p + c((X^a - 1)p)",
            "lane_equation": "body[q]' = body[q] + c((X^a - 1)body[q])",
            "selector_values": "c=0 identity; c=1 X^a",
            "negative_control": "binary X^a must fail on c=0 nonfixed states",
        },
        {
            "branch": "ternary",
            "selector_family": "s_sign",
            "scalar_equation": "p1=X^a p; p'=p1 + s((X^{-2a}-1)p1)",
            "lane_equation": "body[q]' equals X^a body[q] when s=0 and X^-a body[q] when s=1",
            "selector_values": "s=0 positive; s=1 negative",
            "negative_control": "binary X^a must fail on s=1 nonfixed states",
        },
    ]


def negacyclic_mul_x(poly: list[int], exp: int) -> list[int]:
    n = len(poly)
    e = exp % (2 * n)
    outer_sign = 1
    if e >= n:
        e -= n
        outer_sign = -1
    out = [0] * n
    for i, coeff in enumerate(poly):
        j = i + e
        sign = outer_sign
        if j >= n:
            j -= n
            sign = -sign
        out[j] = (out[j] + sign * coeff) % MODULUS
    return out


def poly(seed: int, lane: int, n: int) -> list[int]:
    return [((seed + 11) * (lane + 3) * (i + 5) + i * i + 17 * lane + 19) % MODULUS for i in range(n)]


def choose_a(seed: int, step: int, lane: int, n: int, state: list[int]) -> int:
    a = ((seed * 13 + step * 7 + lane * 5 + 3) % (2 * n - 1)) + 1
    for _ in range(2 * n):
        if a % n != 0 and negacyclic_mul_x(state, a) != negacyclic_mul_x(state, -a):
            return a
        a = (a + 1) % (2 * n)
        if a == 0:
            a = 1
    return 1


def include_zero_update(state: list[int], a: int, c: int) -> list[int]:
    rotated = negacyclic_mul_x(state, a)
    if c == 0:
        return state[:]
    return rotated


def include_zero_formula_update(state: list[int], a: int, c: int) -> list[int]:
    rotated = negacyclic_mul_x(state, a)
    return [(x + c * (y - x)) % MODULUS for x, y in zip(state, rotated)]


def ternary_update(state: list[int], a: int, sign: int) -> list[int]:
    first = negacyclic_mul_x(state, a)
    if sign == 0:
        return first
    correction = negacyclic_mul_x(first, -2 * a)
    return correction


def ternary_formula_update(state: list[int], a: int, sign: int) -> list[int]:
    first = negacyclic_mul_x(state, a)
    correction = negacyclic_mul_x(first, -2 * a)
    return [(x + sign * (y - x)) % MODULUS for x, y in zip(first, correction)]


def run_branch(branch: str, lanes: int, seed: int, n: int, steps: int) -> tuple[dict[str, object], list[dict[str, object]], dict[str, object]]:
    scalar = [poly(seed, lane, n) for lane in range(lanes)]
    pvw = [row[:] for row in scalar]
    positive_mismatches = 0
    formula_mismatches = 0
    neg_checked = 0
    neg_unexpected_matches = 0
    trace: list[dict[str, object]] = []
    for step in range(steps):
        for lane in range(lanes):
            a = choose_a(seed, step, lane, n, scalar[lane])
            before = scalar[lane][:]
            if branch == "include_zero":
                selector = (seed + step + lane) % 2
                scalar_next = include_zero_update(before, a, selector)
                pvw_next = include_zero_formula_update(pvw[lane], a, selector)
                formula_next = include_zero_formula_update(before, a, selector)
                naive = negacyclic_mul_x(before, a)
                if selector == 0:
                    neg_checked += 1
                    if naive == scalar_next:
                        neg_unexpected_matches += 1
            elif branch == "ternary":
                selector = (seed + step + lane + 1) % 2
                scalar_next = ternary_update(before, a, selector)
                pvw_next = ternary_formula_update(pvw[lane], a, selector)
                formula_next = ternary_formula_update(before, a, selector)
                naive = negacyclic_mul_x(before, a)
                if selector == 1:
                    neg_checked += 1
                    if naive == scalar_next:
                        neg_unexpected_matches += 1
            else:
                raise ValueError(branch)
            if scalar_next != pvw_next:
                positive_mismatches += sum(1 for x, y in zip(scalar_next, pvw_next) if x != y)
            if scalar_next != formula_next:
                formula_mismatches += sum(1 for x, y in zip(scalar_next, formula_next) if x != y)
            scalar[lane] = scalar_next
            pvw[lane] = pvw_next
            if len(trace) < 24:
                trace.append({
                    "branch": branch,
                    "r": lanes,
                    "seed": seed,
                    "step": step,
                    "lane": lane,
                    "a": a,
                    "selector": selector,
                    "before_head": " ".join(str(x) for x in before[:4]),
                    "after_head": " ".join(str(x) for x in scalar_next[:4]),
                    "status": "PASS" if scalar_next == pvw_next else "FAIL",
                })
    status = "PASS_LANE_EQUIVALENCE" if positive_mismatches == 0 and formula_mismatches == 0 and neg_checked > 0 and neg_unexpected_matches == 0 else "FAIL"
    row = {
        "branch": branch,
        "r": lanes,
        "seed": seed,
        "N": n,
        "steps": steps,
        "positive_mismatches": positive_mismatches,
        "formula_mismatches": formula_mismatches,
        "negative_controls_checked": neg_checked,
        "negative_control_unexpected_matches": neg_unexpected_matches,
        "status": status,
    }
    neg = {
        "branch": branch,
        "r": lanes,
        "seed": seed,
        "negative_controls_checked": neg_checked,
        "unexpected_matches": neg_unexpected_matches,
        "status": "PASS_NEGATIVE_CONTROL" if neg_checked > 0 and neg_unexpected_matches == 0 else "FAIL",
    }
    return row, trace, neg


def probe_rows() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    traces: list[dict[str, object]] = []
    negs: list[dict[str, object]] = []
    for branch in ["include_zero", "ternary"]:
        for lanes in [1, 2, 4]:
            for seed in range(10):
                row, trace, neg = run_branch(branch, lanes, seed, 64, 16)
                rows.append(row)
                traces.extend(trace[: max(0, 24 - len(traces))])
                negs.append(neg)
    return rows, traces[:24], negs


def source_isolation_rows() -> list[dict[str, object]]:
    rows = []
    for path in [INPUTS["sab_pvw_header"], INPUTS["pvw_sab_source"], INPUTS["sab_header"], INPUTS["scalar_sab_source"]]:
        relpath = rel(path)
        proc = subprocess.run(["git", "diff", "--name-only", "--", relpath], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        rows.append({
            "path": relpath,
            "modified_in_stage253": "yes" if proc.stdout.strip() else "no",
            "status": "PASS_UNCHANGED" if not proc.stdout.strip() else "FAIL_MODIFIED",
            "interpretation": "Stage253 must remain an isolated equivalence model.",
        })
    return rows


def admission_rows() -> list[dict[str, object]]:
    return [
        {
            "route": "isolated_suba_equivalence",
            "decision": "PASSED_FINITE_MODEL",
            "production_permission": "no",
            "allowed_next_step": "Stage254 encrypted selector keygen/noise/resource preflight",
            "blocked_before": "production keygen; full sparse_mul; full SAB; speed claim",
        },
        {
            "route": "include_zero_pvw",
            "decision": "EQUIVALENCE_MODEL_ONLY",
            "production_permission": "no",
            "allowed_next_step": "MAT s_coff keygen/noise design",
            "blocked_before": "MOSFHET encrypted keygen and complete SAB",
        },
        {
            "route": "ternary_pvw",
            "decision": "EQUIVALENCE_MODEL_ONLY",
            "production_permission": "no",
            "allowed_next_step": "MAT s_sign keygen/noise design",
            "blocked_before": "MOSFHET encrypted keygen and complete SAB",
        },
    ]


def claim_rows() -> list[dict[str, object]]:
    return [
        {
            "claim": "isolated_sub_a_equivalence",
            "status": "supported_finite_model",
            "allowed_wording": "Finite negacyclic lane model matches scalar include-zero and ternary sub_a equations for r=1/2/4.",
            "forbidden_wording": "Full non-binary PVW-SAB correctness is proven.",
            "evidence": rel(PROBE),
        },
        {
            "claim": "binary_negative_control",
            "status": "supported",
            "allowed_wording": "Naive binary X^a update fails on required c=0/sign=1 controls.",
            "forbidden_wording": "Binary sab_pvw_sub_a can be reused unchanged for non-binary branches.",
            "evidence": rel(NEGATIVE),
        },
        {
            "claim": "nonbinary_speedup",
            "status": "unsupported",
            "allowed_wording": "No non-binary speedup is claimed.",
            "forbidden_wording": "Non-binary PVW/MAT-SAB accelerates complete bootstrapping.",
            "evidence": rel(ADMISSION),
        },
    ]


def gate_rows(
    inputs: list[dict[str, object]],
    probe: list[dict[str, object]],
    neg: list[dict[str, object]],
    source_rows: list[dict[str, object]],
    admission: list[dict[str, object]],
) -> list[dict[str, object]]:
    inputs_ok = all(row["status"] == "present" for row in inputs)
    stage252_ok = stage252_passes()
    probe_ok = bool(probe) and all(row["status"] == "PASS_LANE_EQUIVALENCE" for row in probe)
    neg_ok = bool(neg) and all(row["status"] == "PASS_NEGATIVE_CONTROL" for row in neg)
    source_ok = all(row["status"] == "PASS_UNCHANGED" for row in source_rows)
    admission_ok = all(row["production_permission"] == "no" for row in admission)
    decision_ok = inputs_ok and stage252_ok and probe_ok and neg_ok and source_ok and admission_ok
    return [
        {
            "gate": "G1_inputs_and_stage252",
            "status": "PASS" if inputs_ok and stage252_ok else "FAIL",
            "metric": "inputs;stage252",
            "value": f"{str(inputs_ok).lower()};{str(stage252_ok).lower()}",
            "evidence": f"{rel(INPUT_STATUS)}; {rel(INPUTS['stage252_proof_gate'])}",
            "interpretation": "Stage253 is valid only after Stage252 selector/key skeleton passes.",
        },
        {
            "gate": "G2_lane_equivalence",
            "status": "PASS" if probe_ok else "FAIL",
            "metric": "probe_rows",
            "value": len(probe),
            "evidence": rel(PROBE),
            "interpretation": "Every include-zero/ternary lane-state row matches scalar reference.",
        },
        {
            "gate": "G3_negative_controls",
            "status": "PASS" if neg_ok else "FAIL",
            "metric": "negative_rows",
            "value": len(neg),
            "evidence": rel(NEGATIVE),
            "interpretation": "Naive binary update fails where non-binary selectors require identity or inverse rotation.",
        },
        {
            "gate": "G4_source_isolation",
            "status": "PASS" if source_ok else "FAIL",
            "metric": "production_source_modified",
            "value": "no" if source_ok else "yes",
            "evidence": rel(SOURCE_ISOLATION),
            "interpretation": "No production SAB/PVW source changes are made.",
        },
        {
            "gate": "G5_admission_boundary",
            "status": "PASS_NO_PRODUCTION",
            "metric": "production_permission",
            "value": "no",
            "evidence": rel(ADMISSION),
            "interpretation": "Equivalence model admits keygen/noise preflight only.",
        },
        {
            "gate": "G6_stage253_decision",
            "status": DECISION if decision_ok else "FAIL_STAGE253_ISOLATED_NONBINARY_SUBA_EQUIVALENCE",
            "metric": "decision",
            "value": DECISION if decision_ok else "FAIL_STAGE253_ISOLATED_NONBINARY_SUBA_EQUIVALENCE",
            "evidence": rel(GATES),
            "interpretation": "Proceed to encrypted selector keygen/noise preflight, not full SAB implementation.",
        },
    ]


def next_rows() -> list[dict[str, object]]:
    return [
        {
            "priority": "P0",
            "route": "stage254_nonbinary_selector_keygen_noise_preflight",
            "entry_condition": "Stage253 finite lane equivalence and negative controls pass.",
            "gate": "define encrypted MAT s_coff/s_sign keygen, noise/resource model, and source admission policy",
            "status": "selected_next",
            "failure_action": "keep non-binary PVW unsupported",
            "evidence": rel(PROBE),
        },
        {
            "priority": "P1",
            "route": "stage255_nonbinary_mosfhet_isolated_suba",
            "entry_condition": "Stage254 keygen/noise preflight admits production-adjacent code",
            "gate": "MOSFHET-adjacent isolated sub_a with actual MAT_TRGSW selectors",
            "status": "conditional",
            "failure_action": "no full SAB integration",
            "evidence": rel(ADMISSION),
        },
        {
            "priority": "P2",
            "route": "stage256_nonbinary_full_sab",
            "entry_condition": "actual selector keygen and isolated MOSFHET equivalence pass",
            "gate": "complete-SAB T_bootstrap/r, multi-seed correctness/noise, resource",
            "status": "future_gated",
            "failure_action": "no non-binary speedup claim",
            "evidence": rel(CLAIM),
        },
    ]


def artifact_rows(paths: list[Path]) -> list[dict[str, object]]:
    return [
        {
            "artifact": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256(path) if path.exists() and path.is_file() else "",
            "bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
        }
        for path in paths
    ]


def write_docs(
    inputs: list[dict[str, object]],
    equations: list[dict[str, object]],
    probe: list[dict[str, object]],
    neg: list[dict[str, object]],
    trace: list[dict[str, object]],
    source_rows: list[dict[str, object]],
    admission: list[dict[str, object]],
    claims: list[dict[str, object]],
    gates: list[dict[str, object]],
    nextq: list[dict[str, object]],
    head: str,
) -> None:
    write_text(DOC, f"""# Stage253 Isolated Non-Binary Sub_A Equivalence

Decision: `{gates[-1]["status"]}`.

Stage253 validates the Stage252 selector/key skeleton in a finite negacyclic
multi-lane model. It checks include-zero and ternary `sub_a` equations for
r=1/2/4 independent body lanes and records binary-naive negative controls.

## Equation Model

{table(equations, ["branch", "selector_family", "scalar_equation", "lane_equation", "selector_values", "negative_control"])}

## Lane Equivalence Probe

{table(probe, ["branch", "r", "seed", "N", "steps", "positive_mismatches", "formula_mismatches", "negative_controls_checked", "negative_control_unexpected_matches", "status"])}

## Negative Controls

{table(neg, ["branch", "r", "seed", "negative_controls_checked", "unexpected_matches", "status"])}

## Trace Sample

{table(trace, ["branch", "r", "seed", "step", "lane", "a", "selector", "before_head", "after_head", "status"])}

## Source Isolation

{table(source_rows, ["path", "modified_in_stage253", "status", "interpretation"])}

## Admission

{table(admission, ["route", "decision", "production_permission", "allowed_next_step", "blocked_before"])}

## Claim Boundary

{table(claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])}

## Proof Gates

{table(gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])}

## Next Queue

{table(nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}

Generated from head `{head}`.
""")
    write_text(REPORT, f"""# Stage253 Report

Decision: `{gates[-1]["status"]}`.

The finite negacyclic lane model confirms that the Stage252 `s_coff` and
`s_sign` selector families can express the scalar include-zero and ternary
`sub_a` equations per independent PVW body lane. The binary `X^a` update fails
on the negative controls, so non-binary support cannot reuse
`sab_pvw_sub_a_binary` unchanged.

This remains isolated equation evidence only. It does not include encrypted
MAT selector keygen, noise recurrence, resource accounting, sparse schedule
integration, or complete-SAB speedup.
""")
    write_text(PLAN, """# Stage253 Isolated Non-Binary Sub_A Equivalence Plan

## Objective

Validate the Stage252 selector skeleton against scalar include-zero and
ternary `sub_a` equations using an executable finite lane model.

## Gates

- Stage252 skeleton must pass.
- r=1/2/4 lane equivalence must have zero mismatches.
- Binary-naive negative controls must fail where expected.
- Production SAB/PVW source files must remain unchanged.
- Next work is encrypted selector keygen/noise preflight only.
""")
    write_text(THEORY, """# Stage253 Isolated Non-Binary Sub_A Equivalence Model

The model works over a finite negacyclic ring modulo `X^N + 1` with modulus
257. Each PVW body lane is an independent polynomial state.

Include-zero:

```text
p' = p + c((X^a - 1)p)
```

Ternary:

```text
p1 = X^a p
p' = p1 + s((X^{-2a} - 1)p1)
```

For `s=1`, this gives `X^{-a}p`. The model checks these equations lane by
lane and keeps binary `X^a` as a negative control.
""")
    write_text(VARIANT, """# MAT-RLWE SAB Stage253 Isolated Non-Binary Sub_A Equivalence

## Variant Delta

Use the Stage252 `s_coff` and `s_sign` selector families to express scalar
non-binary `sub_a` updates on each PVW body lane.

## Status

Finite isolated equivalence only. No encrypted keygen, noise model, production
code, sparse schedule integration, or complete-SAB speedup claim is included.
""")
    write_text(REPRO_CMDS, f"""# Stage253 Reproduction Commands

```text
python scripts/build_stage253_isolated_nonbinary_suba_equivalence.py
python -m py_compile scripts/build_stage253_isolated_nonbinary_suba_equivalence.py
```

Decision: `{gates[-1]["status"]}`.
""")


def update_project_files(head: str, decision: str) -> None:
    append_once(ROADMAP, "## Stage 253: Isolated Non-Binary Sub_A Equivalence", f"""
## Stage 253: Isolated Non-Binary Sub_A Equivalence

Goal:

```text
Validate include-zero and ternary sub_a equations per PVW body lane using the
Stage252 selector-key skeleton.
```

Status:

```text
Generated from input head `{head}` with `{decision}`. The finite negacyclic
lane model passes for include-zero and ternary branches at r=1/2/4, while the
binary naive update fails the negative controls. Production SAB/PVW source
files remain unchanged. Next selected route: encrypted selector keygen/noise
preflight.
```
""")
    append_once(GOAL, "Stage253 isolated non-binary sub_a equivalence", f"""
- Stage253 isolated non-binary sub_a equivalence records `{decision}`: finite
  lane equivalence for include-zero and ternary selector equations passes, but
  production non-binary PVW/MAT-SAB remains unimplemented.
""")
    append_once(CURRENT_GOAL, "### Stage253 isolated non-binary sub_a equivalence", f"""
### Stage253 isolated non-binary sub_a equivalence

`{decision}` moves non-binary support from skeleton topology to isolated
equation evidence. The active goal remains open for encrypted selector keygen,
noise/resource, MOSFHET-adjacent equivalence, full SAB A/B, and paper claim
closure.
""")
    append_once(HYPOTHESES, "H10_stage253_isolated_nonbinary_suba_equivalence:", f"""
H10_stage253_isolated_nonbinary_suba_equivalence:
  status: isolated_finite_lane_equivalence_ready_keygen_noise_preflight
  evidence:
    - repro/stage253_isolated_nonbinary_suba_equivalence/lane_equivalence_probe.csv
    - repro/stage253_isolated_nonbinary_suba_equivalence/negative_control_matrix.csv
    - repro/stage253_isolated_nonbinary_suba_equivalence/proof_gate.csv
    - docs/stage253_isolated_nonbinary_suba_equivalence.md
  conclusion: >
    Stage253 records {decision}. Include-zero and ternary sub_a equations pass
    finite negacyclic lane equivalence for r=1/2/4, and binary naive controls
    fail as expected. This is not production keygen, noise, full SAB, or
    speedup evidence.
""")
    append_once(RUN_LOG, "stage253-isolated-nonbinary-suba-equivalence-001", f"""stage253-isolated-nonbinary-suba-equivalence-001,{date.today().isoformat()},{head},Stage 253,isolated_suba_equivalence,"python scripts/build_stage253_isolated_nonbinary_suba_equivalence.py","Stage251 equations + Stage252 selector skeleton",n/a,{decision},"Finite include-zero/ternary lane equivalence passes; production still blocked.",docs/stage253_isolated_nonbinary_suba_equivalence.md; repro/stage253_isolated_nonbinary_suba_equivalence/proof_gate.csv
""")
    append_once(MANIFEST, "- stage253_isolated_nonbinary_suba_equivalence:", """
- stage253_isolated_nonbinary_suba_equivalence:
  - `docs/stage253_isolated_nonbinary_suba_equivalence.md`
  - `experiments/stage253_isolated_nonbinary_suba_equivalence_plan.md`
  - `theory_checks/stage253_isolated_nonbinary_suba_equivalence_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage253_isolated_nonbinary_suba_equivalence.md`
  - `scripts/build_stage253_isolated_nonbinary_suba_equivalence.py`
  - `repro/stage253_isolated_nonbinary_suba_equivalence/`
""")
    append_once(CHECKLIST, "Stage253 isolated non-binary sub_a equivalence ready for keygen/noise preflight", f"""
- [x] Stage253 isolated non-binary sub_a equivalence ready for keygen/noise preflight `{decision}`.
""")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    head = run_git(["rev-parse", "--short", "HEAD"])
    inputs = input_rows()
    equations = equation_rows()
    probe, trace, neg = probe_rows()
    source_rows = source_isolation_rows()
    admission = admission_rows()
    claims = claim_rows()
    gates = gate_rows(inputs, probe, neg, source_rows, admission)
    nextq = next_rows()

    write_csv(INPUT_STATUS, inputs, ["input_id", "path", "status", "bytes"])
    write_csv(EQUATIONS, equations, ["branch", "selector_family", "scalar_equation", "lane_equation", "selector_values", "negative_control"])
    write_csv(PROBE, probe, ["branch", "r", "seed", "N", "steps", "positive_mismatches", "formula_mismatches", "negative_controls_checked", "negative_control_unexpected_matches", "status"])
    write_csv(NEGATIVE, neg, ["branch", "r", "seed", "negative_controls_checked", "unexpected_matches", "status"])
    write_csv(TRACE, trace, ["branch", "r", "seed", "step", "lane", "a", "selector", "before_head", "after_head", "status"])
    write_csv(SOURCE_ISOLATION, source_rows, ["path", "modified_in_stage253", "status", "interpretation"])
    write_csv(ADMISSION, admission, ["route", "decision", "production_permission", "allowed_next_step", "blocked_before"])
    write_csv(CLAIM, claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(GATES, gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])

    write_docs(inputs, equations, probe, neg, trace, source_rows, admission, claims, gates, nextq, head)
    artifacts = [DOC, PLAN, THEORY, VARIANT, INPUT_STATUS, EQUATIONS, PROBE, NEGATIVE, TRACE, SOURCE_ISOLATION, ADMISSION, CLAIM, GATES, NEXT, REPORT, REPRO_CMDS]
    write_csv(ARTIFACT, artifact_rows(artifacts), ["artifact", "exists", "sha256", "bytes"])
    if gates[-1]["status"] == DECISION:
        update_project_files(head, gates[-1]["status"])
    print(f"Stage253 report: {rel(DOC)}")
    print(f"Stage253 decision: {gates[-1]['status']}")
    return 0 if gates[-1]["status"] == DECISION else 1


if __name__ == "__main__":
    raise SystemExit(main())
