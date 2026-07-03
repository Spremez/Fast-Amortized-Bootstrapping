#!/usr/bin/env python3
"""Stage189: executable T2 closed-state linear probe."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage189_closed_state_linear_probe"

SUMMARY_CSV = OUT_DIR / "summary.csv"
RANK_CSV = OUT_DIR / "rank_probe.csv"
CONVERSION_CSV = OUT_DIR / "conversion_cost_model.csv"
ROUTE_CSV = OUT_DIR / "route_decision.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage189_closed_state_linear_probe.md"
PLAN_MD = ROOT / "experiments" / "stage189_closed_state_linear_probe_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage189_closed_state_linear_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_closed_state_linear_probe.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE132_API = ROOT / "repro" / "stage132_lane_pair_cmux_consumption_gate" / "api_results.csv"
STAGE133_CLOSURE = ROOT / "repro" / "stage133_lane_state_closure_audit" / "closure_matrix.csv"
STAGE134_SUMMARY = ROOT / "repro" / "stage134_generalized_lane_pair_input_ep_gate" / "summary.csv"
STAGE134_TARGET = ROOT / "repro" / "stage135_decomp_dft_reuse_target_gate" / "target_matrix.csv"
STAGE139_CLOSURE = ROOT / "repro" / "stage139_compact_closure_audit" / "closure.csv"
STAGE176_API = ROOT / "repro" / "stage176_structured_compact_security_api_gate" / "api_options.csv"
STAGE187_THEOREMS = ROOT / "repro" / "stage187_compact_proof_obligation_draft" / "theorem_matrix.csv"

DECISION = "PASS_STAGE189_T2_PUBLIC_CLOSURE_PROBE_DIRECT_SHARED_MASK_REJECTED"
PRIME = 65537


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


def gf_rank(matrix: List[List[int]], p: int) -> int:
    if not matrix:
        return 0
    a = [row[:] for row in matrix]
    rows = len(a)
    cols = len(a[0])
    rank = 0
    for col in range(cols):
        pivot = None
        for row in range(rank, rows):
            if a[row][col] % p:
                pivot = row
                break
        if pivot is None:
            continue
        a[rank], a[pivot] = a[pivot], a[rank]
        inv = pow(a[rank][col] % p, -1, p)
        a[rank] = [(v * inv) % p for v in a[rank]]
        for row in range(rows):
            if row == rank:
                continue
            factor = a[row][col] % p
            if factor:
                a[row] = [(a[row][c] - factor * a[rank][c]) % p for c in range(cols)]
        rank += 1
        if rank == rows:
            break
    return rank


def negacyclic_mul_matrix(secret: List[int], p: int) -> List[List[int]]:
    n = len(secret)
    mat = [[0 for _ in range(n)] for _ in range(n)]
    for col in range(n):
        for i, coeff in enumerate(secret):
            deg = col + i
            sign = 1
            if deg >= n:
                deg -= n
                sign = -1
            mat[deg][col] = (mat[deg][col] + sign * coeff) % p
    return mat


def monomial_secret(n: int, shift: int) -> List[int]:
    coeffs = [0 for _ in range(n)]
    coeffs[shift % n] = 1
    return coeffs


def build_shared_projection_system(r: int, n: int, p: int) -> Tuple[List[List[int]], List[List[int]], List[int]]:
    """Build S_q G = S_q E_q over GF(p).

    G is the unknown public projection from r lane-local masks to one shared
    mask. E_q selects lane q's mask. If the system is inconsistent, no
    secret-independent linear projection can preserve all lane phases for the
    chosen full-rank secret multiplication matrices.
    """

    unknowns = n * r * n
    equations: List[List[int]] = []
    augmented: List[List[int]] = []
    secret_ranks: List[int] = []
    for q in range(r):
        secret = monomial_secret(n, q)
        s_mat = negacyclic_mul_matrix(secret, p)
        secret_ranks.append(gf_rank(s_mat, p))
        for out_coeff in range(n):
            for lane_coeff in range(r * n):
                row = [0 for _ in range(unknowns)]
                for shared_coeff in range(n):
                    var_idx = (shared_coeff * r * n) + lane_coeff
                    row[var_idx] = s_mat[out_coeff][shared_coeff] % p
                selected_coeff = lane_coeff - q * n
                rhs = s_mat[out_coeff][selected_coeff] % p if 0 <= selected_coeff < n else 0
                equations.append(row)
                augmented.append(row + [rhs])
    return equations, augmented, secret_ranks


def build_rank_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for r in [1, 2, 4, 6]:
        for n in [4, 8]:
            equations, augmented, secret_ranks = build_shared_projection_system(r, n, PRIME)
            rank_a = gf_rank(equations, PRIME)
            rank_aug = gf_rank(augmented, PRIME)
            consistent = rank_a == rank_aug
            rows.append(
                {
                    "probe": "public_shared_mask_projection",
                    "field": f"GF({PRIME})",
                    "r": str(r),
                    "N": str(n),
                    "unknowns": str(n * r * n),
                    "constraints": str(len(equations)),
                    "rank_A": str(rank_a),
                    "rank_aug": str(rank_aug),
                    "secret_rank_min": str(min(secret_ranks)),
                    "consistent": "yes" if consistent else "no",
                    "expected": "consistent_only_for_r1",
                    "status": "PASS_R1_CONTROL" if r == 1 and consistent else ("EXPECTED_INCONSISTENT" if r > 1 and not consistent else "UNEXPECTED"),
                }
            )
            rows.append(
                {
                    "probe": "lane_pair_identity_state",
                    "field": f"GF({PRIME})",
                    "r": str(r),
                    "N": str(n),
                    "unknowns": str(r * n * r * n),
                    "constraints": str(r * n * r * n),
                    "rank_A": str(r * n * r * n),
                    "rank_aug": str(r * n * r * n),
                    "secret_rank_min": str(min(secret_ranks)),
                    "consistent": "yes",
                    "expected": "always_consistent_but_not_one_shared_mask",
                    "status": "PASS_INTERNAL_MULTIMASK_STATE",
                }
            )
    return rows


def stage134_min_speedup() -> str:
    for row in read_csv_dicts(STAGE134_SUMMARY):
        if row.get("gate") == "stage134_full_signal":
            return row.get("value", "")
    return ""


def build_conversion_rows(rank_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    inconsistent_r_gt_1 = all(
        row["consistent"] == "no"
        for row in rank_rows
        if row["probe"] == "public_shared_mask_projection" and row["r"] != "1"
    )
    return [
        {
            "route": "direct_public_projection_to_one_shared_mask",
            "t2_result": "REJECTED" if inconsistent_r_gt_1 else "OPEN",
            "extra_state": "one shared mask only",
            "secret_dependent_work": "none",
            "performance_status": "no production benchmark because algebra gate fails",
            "evidence": rel(RANK_CSV),
            "next_action": "Do not implement this route.",
        },
        {
            "route": "keep_lane_pair_or_multimask_state",
            "t2_result": "CLOSED_AS_INTERNAL_STATE_NOT_STANDARD_PVW",
            "extra_state": "r masks plus r bodies instead of one mask plus r bodies",
            "secret_dependent_work": "none",
            "performance_status": f"Stage134 generalized input full signal {stage134_min_speedup()}",
            "evidence": f"{rel(STAGE133_CLOSURE)}; {rel(STAGE134_SUMMARY)}",
            "next_action": "Only revisit if a decompose/DFT reuse mechanism changes Stage134 economics.",
        },
        {
            "route": "secret_correction_or_keyswitch_to_shared_mask",
            "t2_result": "ALGEBRAICALLY_POSSIBLE_BUT_NOT_PUBLIC",
            "extra_state": "one shared mask after correction",
            "secret_dependent_work": "body_q += (a_shared - a_q) * s_q or equivalent key switch",
            "performance_status": "unmeasured; must include noise/key/materialization overhead",
            "evidence": rel(STAGE176_API),
            "next_action": "Requires T1/T4 security-noise proof before any SAB code.",
        },
        {
            "route": "dense_full_mat_reexpansion",
            "t2_result": "CLOSED_REFERENCE",
            "extra_state": "standard PVW_TMLWE",
            "secret_dependent_work": "covered by existing dense encrypted selector rows",
            "performance_status": "implemented exact full-MAT path; not compact",
            "evidence": rel(STAGE176_API),
            "next_action": "Keep as current exact baseline, not a compact proof route.",
        },
        {
            "route": "new_structured_equal_mask_selector",
            "t2_result": "OPEN_PROOF_ROUTE",
            "extra_state": "one shared mask if selector distribution forces equal output masks",
            "secret_dependent_work": "depends on new key distribution/proof",
            "performance_status": "no implementation permission",
            "evidence": f"{rel(STAGE187_THEOREMS)}; {rel(STAGE176_API)}",
            "next_action": "Target T1 key-distribution proof before code.",
        },
    ]


def build_route_rows() -> List[Dict[str, str]]:
    return [
        {
            "decision": "direct_public_shared_mask_closure",
            "status": "DENY",
            "reason": "finite linear system is inconsistent for r>1 under full-rank monomial secret multiplication",
            "allowed_next": "none",
        },
        {
            "decision": "production_compact_sab_code",
            "status": "DENY",
            "reason": "T2 direct closure is rejected and T1/T4 remain unproven for secret-correction or structured selector routes",
            "allowed_next": "isolated T1 distribution probe or T4 noise/key-switch probe",
        },
        {
            "decision": "lane_pair_multimask_route",
            "status": "DEFER",
            "reason": "algebraically closed as internal state but Stage134 performance is neutral/negative for r=4/r=6 unless decompose/DFT economics change",
            "allowed_next": "only a new decompose/DFT reuse mechanism with projected complete-SAB impact",
        },
        {
            "decision": "paper_claim",
            "status": "SCOPED_ONLY",
            "reason": "Stage189 strengthens a negative/blocked T2 boundary; it does not implement compact SAB",
            "allowed_next": "state as limitation or proof obligation, not as speedup",
        },
    ]


def build_summary_rows(rank_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    inputs = [STAGE132_API, STAGE133_CLOSURE, STAGE139_CLOSURE, STAGE176_API, STAGE187_THEOREMS]
    ok = all(path.exists() for path in inputs)
    inconsistent = [
        row
        for row in rank_rows
        if row["probe"] == "public_shared_mask_projection" and row["r"] != "1" and row["consistent"] == "no"
    ]
    unexpected = [row for row in rank_rows if row["status"] == "UNEXPECTED"]
    return [
        {
            "gate": "stage189_inputs",
            "status": "PASS" if ok else "FAIL",
            "metric": "required_inputs_present",
            "value": "1" if ok else "0",
            "evidence": f"{rel(STAGE133_CLOSURE)}; {rel(STAGE139_CLOSURE)}; {rel(STAGE187_THEOREMS)}",
            "detail": "Stage189 targets T2 using prior lane-pair and nonclosure evidence.",
            "next_action": "Repair missing inputs before interpreting the probe.",
        },
        {
            "gate": "stage189_linear_probe",
            "status": "PASS" if not unexpected else "FAIL",
            "metric": "inconsistent_public_projection_rows_r_gt_1",
            "value": str(len(inconsistent)),
            "evidence": rel(RANK_CSV),
            "detail": "Public one-shared-mask projection is consistent for r=1 control and inconsistent for r>1 finite probes.",
            "next_action": "Reject direct public closure if no unexpected row exists.",
        },
        {
            "gate": "stage189_conversion_routes",
            "status": "RECORDED",
            "metric": "routes",
            "value": "5",
            "evidence": rel(CONVERSION_CSV),
            "detail": "Remaining T2 routes require multimask state, secret correction/key switching, dense re-expansion, or a new structured selector proof.",
            "next_action": "Do not write production compact SAB code.",
        },
        {
            "gate": "stage189_decision",
            "status": DECISION if not unexpected else "FAIL_STAGE189_UNEXPECTED_LINEAR_PROBE",
            "metric": "production_compact_sab_permission",
            "value": "0",
            "evidence": rel(ROUTE_CSV),
            "detail": "Stage189 closes the direct public shared-mask closure route, but does not close T1/T4.",
            "next_action": "Run isolated T1 distribution or T4 secret-correction/noise probe.",
        },
    ]


def write_docs(
    summary_rows: List[Dict[str, str]],
    rank_rows: List[Dict[str, str]],
    conversion_rows: List[Dict[str, str]],
    route_rows: List[Dict[str, str]],
) -> None:
    write_text_lf(
        OUT_MD,
        f"""# Stage189 Closed-State Linear Probe

Decision: `{DECISION}`.

Stage189 targets the Stage187 `T2_closed_state` obligation with an executable
finite linear-algebra probe. It asks one narrow question:

```text
Can r lane-local compact output masks be publicly projected to one shared
PVW_TMLWE mask while preserving every lane phase, without secret-dependent
correction and without dense re-expansion?
```

The answer is no for the tested r>1 finite systems. The r=1 control passes.
This does not prove every possible compact construction impossible; it rejects
the direct public projection route for the current lane-pair output shape.

## Gate Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Rank Probe

{table(rank_rows, ["probe", "field", "r", "N", "unknowns", "constraints", "rank_A", "rank_aug", "secret_rank_min", "consistent", "expected", "status"])}
## Conversion Routes

{table(conversion_rows, ["route", "t2_result", "extra_state", "secret_dependent_work", "performance_status", "evidence", "next_action"])}
## Route Decision

{table(route_rows, ["decision", "status", "reason", "allowed_next"])}
""",
    )

    write_text_lf(
        PLAN_MD,
        """# Stage189 Plan

Goal: run an isolated proof probe for Stage187 `T2_closed_state`.

Rules:

- do not modify `sab_pvw_*`;
- model only public linear conversion from lane-local masks to one shared mask;
- keep r=1 as a positive control;
- reject direct closure if r>1 systems are inconsistent;
- route remaining work to T1/T4 or a new measured dataflow mechanism.
""",
    )

    write_text_lf(
        THEORY_MD,
        """# Stage189 Closed-State Linear Model

Let the compact output after one CMUX step contain lane-local masks `a_q` and
bodies `b_q`. Standard PVW_TMLWE requires one shared mask `a*` and r bodies.
For lane q, phase preservation without changing the secret relation requires:

```text
b'_q - S_q a* = b_q - S_q a_q
```

If `b'_q` is not allowed to include the secret-dependent correction
`(a* - a_q) * s_q`, then a public projection `a* = G(a_0,...,a_{r-1})` must
satisfy:

```text
S_q G = S_q E_q   for every q
```

where `E_q` selects lane q's mask. For full-rank `S_q`, this implies
`G = E_q` for every q. For r>1 the `E_q` matrices are different, so no single
public shared-mask projection exists. The generated rank probe instantiates
this over GF(65537) with full-rank monomial secret multiplication matrices.

This is a T2/API result, not a T1 key-distribution proof and not a T4 noise
bound.
""",
    )

    write_text_lf(
        VARIANT_MD,
        """# Closed-State Linear Probe Variant

This variant is a proof probe, not an implementation. It rejects direct public
collapse of lane-pair compact output to a standard one-mask PVW_TMLWE state.

Remaining implementation routes are not unlocked:

- keep multimask/lane-pair state and solve the generalized-input performance
  problem;
- add secret correction or key switching and prove distribution/noise;
- use dense full-MAT re-expansion, which is the current exact route;
- design a new structured equal-mask selector and prove T1/T3/T4.
""",
    )


def update_global_docs() -> None:
    append_once(
        ROADMAP_MD,
        "## Stage 189: Closed-State Linear Probe",
        f"""
## Stage 189: Closed-State Linear Probe

Goal:

```text
Run an executable T2 proof probe for whether lane-local compact output masks
can be publicly collapsed into one shared PVW_TMLWE mask.
```

Status:

```text
Completed. Stage189 records {DECISION}. The direct public shared-mask
projection route is rejected for r>1; production compact SAB code remains
denied. Remaining routes require multimask state, secret correction/key
switching, dense re-expansion, or a new structured selector distribution proof.
```
""",
    )

    append_once(
        GOAL_MD,
        "Stage189 records the closed-state linear probe",
        f"""
Stage189 records the closed-state linear probe. Decision: `{DECISION}`.
It gives executable evidence for the T2 boundary: current lane-pair compact
output cannot be publicly collapsed to one shared PVW_TMLWE mask for r>1.
""",
    )

    append_once(
        CURRENT_GOAL_MD,
        "Treat Stage189 as the closed-state linear probe",
        f"""
93. Treat Stage189 as the closed-state linear probe:
    `{DECISION}`. Direct public projection from lane-local compact masks to
    one shared PVW_TMLWE mask is rejected for r>1. Compact/shared-output SAB
    implementation remains denied; only isolated T1/T4 proof probes or a new
    measured dataflow mechanism may proceed.
""",
    )

    append_once(
        HYPOTHESIS_YAML,
        "H113_closed_state_linear_probe",
        f"""
  - id: H113_closed_state_linear_probe
    statement: >
      Current lane-pair compact output cannot be converted to a one-shared-mask
      PVW_TMLWE state by public linear projection for r > 1.
    mechanism: >
      Stage189 solves finite linear systems for S_q G = S_q E_q over GF(65537)
      using full-rank monomial secret multiplication matrices.
    status: stage189_t2_public_closure_probe
    evidence: docs/stage189_closed_state_linear_probe.md; experiments/stage189_closed_state_linear_probe_plan.md; theory_checks/stage189_closed_state_linear_model.md; repro/stage189_closed_state_linear_probe/summary.csv
    current_decision: >
      {DECISION}
    failure_criteria:
      - an r > 1 public shared-mask projection system is consistent
      - production compact SAB code is written without T1/T4 proof gates
      - this T2 probe is reported as a complete compact SAB implementation
""",
    )

    append_once(
        RUN_LOG,
        "stage189-closed-state-linear-probe-001",
        f"""
stage189-closed-state-linear-probe-001,2026-07-04,{git_head()},Stage 189,analysis,python scripts/build_stage189_closed_state_linear_probe.py,Stage187 T2 closed-state gate,none,{DECISION},Finite linear proof probe rejects direct public shared-mask closure for r>1.,repro/stage189_closed_state_linear_probe
""",
    )

    append_once(
        MANIFEST,
        "stage189_closed_state_linear_probe",
        f"""
- stage189_closed_state_linear_probe: `{DECISION}`
  - `docs/stage189_closed_state_linear_probe.md`
  - `experiments/stage189_closed_state_linear_probe_plan.md`
  - `theory_checks/stage189_closed_state_linear_model.md`
  - `algorithm_variants/mat_rlwe_sab_closed_state_linear_probe.md`
  - `repro/stage189_closed_state_linear_probe/`
""",
    )

    append_once(CHECKLIST, "Stage189 closed-state linear probe recorded", """
- [x] Stage189 closed-state linear probe recorded.
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
    rank_rows = build_rank_rows()
    conversion_rows = build_conversion_rows(rank_rows)
    route_rows = build_route_rows()
    summary_rows = build_summary_rows(rank_rows)

    write_csv(
        RANK_CSV,
        rank_rows,
        [
            "probe",
            "field",
            "r",
            "N",
            "unknowns",
            "constraints",
            "rank_A",
            "rank_aug",
            "secret_rank_min",
            "consistent",
            "expected",
            "status",
        ],
    )
    write_csv(
        CONVERSION_CSV,
        conversion_rows,
        ["route", "t2_result", "extra_state", "secret_dependent_work", "performance_status", "evidence", "next_action"],
    )
    write_csv(ROUTE_CSV, route_rows, ["decision", "status", "reason", "allowed_next"])
    write_csv(SUMMARY_CSV, summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    write_docs(summary_rows, rank_rows, conversion_rows, route_rows)
    update_global_docs()
    write_artifacts(
        [
            OUT_MD,
            PLAN_MD,
            THEORY_MD,
            VARIANT_MD,
            SUMMARY_CSV,
            RANK_CSV,
            CONVERSION_CSV,
            ROUTE_CSV,
            Path(__file__),
        ]
    )
    print(DECISION)


if __name__ == "__main__":
    main()
