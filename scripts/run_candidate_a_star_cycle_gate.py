#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.mat_sab.star_cycle_model import (
    analyze_support,
    dense_support,
    phase_residual,
    selector_from_kernel,
    star_cycle_support,
    support_from_stage203,
)


OUT = Path("repro/candidate_a_star_cycle_gate")
ADMIT = "ADMIT_CANDIDATE_A_REVISION_OR_KEYGEN_PREFLIGHT"
REJECT = "REJECT_CANDIDATE_A_STANDARD_PVW_RANDOMIZATION_ROUTE_TO_B"
PRIME = 257
SECRETS = {
    2: (2, 3),
    4: (2, 3, 5, 7),
    6: (2, 3, 5, 7, 11, 13),
}


@dataclass(frozen=True)
class GateResult:
    decision: str
    support_gate: bool
    phase_gate: bool
    dense_control_gate: bool
    negative_control_gate: bool
    randomization_gate: bool
    production_code_permission: bool
    phase_rows: tuple[dict[str, object], ...]
    randomization_rows: tuple[dict[str, object], ...]
    negative_rows: tuple[dict[str, object], ...]
    source_rows: tuple[dict[str, object], ...]


def _zero_count(matrix: Iterable[Iterable[int]]) -> int:
    return sum(value != 0 for row in matrix for value in row)


def evaluate_candidate_a(root: Path = ROOT) -> GateResult:
    stage203 = root / "repro/stage203_production_selector_equation_probe/equation_map.csv"
    phase_rows: list[dict[str, object]] = []
    randomization_rows: list[dict[str, object]] = []
    negative_rows: list[dict[str, object]] = []
    support_gate = True
    phase_gate = True
    dense_control_gate = True
    randomization_gate = True
    removal_outcomes: dict[int, set[str]] = {r: set() for r in SECRETS}

    for r, secret in SECRETS.items():
        star = star_cycle_support(r)
        declared = support_from_stage203(stage203, r)
        support_match = star == declared and len(star) == 4 * r
        support_gate &= support_match
        for mu in (0, 1):
            analysis = analyze_support(secret, mu, star, PRIME)
            residual_count = (
                _zero_count(
                    phase_residual(
                        secret,
                        analysis.particular_matrix,
                        mu,
                        PRIME,
                    )
                )
                if analysis.consistent
                else -1
            )
            passed = analysis.consistent and residual_count == 0
            phase_gate &= passed
            phase_rows.append(
                {
                    "r": r,
                    "mu": mu,
                    "prime": PRIME,
                    "support_terms": len(star),
                    "stage203_match": "PASS" if support_match else "FAIL",
                    "consistent": "PASS" if analysis.consistent else "FAIL",
                    "affine_dimension": analysis.affine_dimension,
                    "residual_nonzero": residual_count,
                    "phase_status": "PASS" if passed else "FAIL",
                }
            )

        star_analysis = analyze_support(secret, 1, star, PRIME)
        dense_analysis = analyze_support(secret, 1, dense_support(r), PRIME)
        randomization_gate &= star_analysis.full_pvw_randomization
        dense_control_gate &= dense_analysis.full_pvw_randomization
        for name, analysis in (
            ("star_cycle", star_analysis),
            ("dense", dense_analysis),
        ):
            randomization_rows.append(
                {
                    "r": r,
                    "support": name,
                    "support_terms": analysis.support_size,
                    "affine_dimension": analysis.affine_dimension,
                    "column_dimensions": ";".join(
                        str(value) for value in analysis.column_dimensions
                    ),
                    "full_pvw_randomization": (
                        "PASS" if analysis.full_pvw_randomization else "FAIL"
                    ),
                }
            )

        generic = selector_from_kernel(
            secret,
            1,
            tuple(range(1, r + 2)),
            PRIME,
        )
        outside_nonzero = sum(
            generic[row][column] != 0
            for row in range(r + 1)
            for column in range(r + 1)
            if (row, column) not in star
        )
        negative_rows.append(
            {
                "r": r,
                "control": "generic_dense_randomizer_outside_star",
                "observed": outside_nonzero,
                "expected": ">0",
                "status": "PASS" if outside_nonzero > 0 else "FAIL",
            }
        )
        for removed in sorted(star):
            reduced = analyze_support(
                secret,
                1,
                frozenset(star - {removed}),
                PRIME,
            )
            observed = "consistent" if reduced.consistent else "inconsistent"
            removal_outcomes[r].add(observed)
            negative_rows.append(
                {
                    "r": r,
                    "control": f"remove_{removed[0]}_{removed[1]}",
                    "observed": observed,
                    "expected": "coverage_contains_consistent_and_inconsistent",
                    "status": "PASS",
                }
            )

    source_specs = (
        ("phase_map", "src/mosfhet/src/pvwtmlwe.c", "void pvmtmlwe_phase("),
        (
            "pvw_randomization",
            "src/mosfhet/src/pvwtmlwe.c",
            "void pvmtmlwe_sample(",
        ),
        (
            "dense_keygen",
            "src/mosfhet/src/mattrgsw.c",
            "void mat_trgsw_monomial_sample(",
        ),
        (
            "dense_evaluator",
            "src/mosfhet/src/mattrgsw.c",
            "static void mat_trgsw_mul_pvmtmlwe_DFT_from_dec(",
        ),
        (
            "star_support",
            "repro/stage203_production_selector_equation_probe/equation_map.csv",
            "lane_neighbor_body_interaction",
        ),
    )
    source_rows = []
    for claim, relative, token in source_specs:
        path = root / relative
        present = (
            path.is_file()
            and token in path.read_text(encoding="utf-8", errors="replace")
        )
        source_rows.append(
            {
                "claim": claim,
                "path": relative,
                "token": token,
                "status": "PASS" if present else "FAIL",
            }
        )
    source_gate = all(row["status"] == "PASS" for row in source_rows)
    support_gate &= source_gate
    generic_rows = [
        row
        for row in negative_rows
        if row["control"] == "generic_dense_randomizer_outside_star"
    ]
    generic_gate = len(generic_rows) == len(SECRETS) and all(
        row["status"] == "PASS" for row in generic_rows
    )
    negative_gate = generic_gate and all(
        outcomes == {"consistent", "inconsistent"}
        for outcomes in removal_outcomes.values()
    )
    admitted = support_gate and phase_gate and dense_control_gate and negative_gate and randomization_gate
    return GateResult(
        decision=ADMIT if admitted else REJECT,
        support_gate=support_gate,
        phase_gate=phase_gate,
        dense_control_gate=dense_control_gate,
        negative_control_gate=negative_gate,
        randomization_gate=randomization_gate,
        production_code_permission=False,
        phase_rows=tuple(phase_rows),
        randomization_rows=tuple(randomization_rows),
        negative_rows=tuple(negative_rows),
        source_rows=tuple(source_rows),
    )


def _write_csv(
    path: Path,
    rows: Iterable[dict[str, object]],
    fields: list[str],
) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="ascii") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(
            {field: row.get(field, "") for field in fields}
            for row in rows
        )


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        content.rstrip() + "\n",
        encoding="ascii",
        newline="\n",
    )


def write_gate_artifacts(
    root: Path,
    result: GateResult,
) -> tuple[Path, ...]:
    out = root / OUT
    out.mkdir(parents=True, exist_ok=True)
    summary = out / "summary.csv"
    phase = out / "phase_constraints.csv"
    randomization = out / "randomization_dimension.csv"
    negative = out / "negative_controls.csv"
    source = out / "source_mapping.csv"
    proof = out / "proof_gate.csv"
    commands = out / "reproduction_commands.md"
    report = root / "docs/candidate_a_star_cycle_mechanism_gate.md"
    variant = root / "algorithm_variants/candidate_a_star_cycle_sparse_mat_ggsw.md"
    experiment = root / "experiments/candidate_a_star_cycle_gate_plan.md"
    index = out / "artifact_index.csv"

    _write_csv(
        summary,
        [
            {
                "decision": result.decision,
                "support_gate": "PASS" if result.support_gate else "FAIL",
                "phase_gate": "PASS" if result.phase_gate else "FAIL",
                "dense_control_gate": (
                    "PASS" if result.dense_control_gate else "FAIL"
                ),
                "negative_control_gate": (
                    "PASS" if result.negative_control_gate else "FAIL"
                ),
                "standard_pvw_randomization_gate": (
                    "PASS" if result.randomization_gate else "FAIL"
                ),
                "production_code_permission": (
                    "yes" if result.production_code_permission else "no"
                ),
                "route": (
                    "candidate_a_keygen_preflight"
                    if result.decision == ADMIT
                    else "candidate_b_factorized_star_cycle"
                ),
            }
        ],
        [
            "decision",
            "support_gate",
            "phase_gate",
            "dense_control_gate",
            "negative_control_gate",
            "standard_pvw_randomization_gate",
            "production_code_permission",
            "route",
        ],
    )
    _write_csv(
        phase,
        result.phase_rows,
        [
            "r",
            "mu",
            "prime",
            "support_terms",
            "stage203_match",
            "consistent",
            "affine_dimension",
            "residual_nonzero",
            "phase_status",
        ],
    )
    _write_csv(
        randomization,
        result.randomization_rows,
        [
            "r",
            "support",
            "support_terms",
            "affine_dimension",
            "column_dimensions",
            "full_pvw_randomization",
        ],
    )
    _write_csv(
        negative,
        result.negative_rows,
        [
            "r",
            "control",
            "observed",
            "expected",
            "status",
        ],
    )
    _write_csv(
        source,
        result.source_rows,
        ["claim", "path", "token", "status"],
    )
    gates = (
        (
            "source_and_support",
            result.support_gate,
            "Stage203 equals the 4r star-cycle support",
        ),
        (
            "phase_zero_one",
            result.phase_gate,
            "P M = mu P for r=2/4/6 and mu=0/1",
        ),
        (
            "dense_control",
            result.dense_control_gate,
            "dense support retains one PVW kernel degree per column",
        ),
        (
            "negative_controls",
            result.negative_control_gate,
            "generic dense and omitted-term controls cover expected failure modes",
        ),
        (
            "standard_pvw_randomization",
            result.randomization_gate,
            "star support fails to retain one PVW kernel degree per column",
        ),
        (
            "production_code",
            result.production_code_permission,
            "later security/noise/Amdahl gates are required",
        ),
    )
    _write_csv(
        proof,
        (
            {
                "gate": name,
                "status": "PASS" if passed else "FAIL",
                "interpretation": interpretation,
            }
            for name, passed, interpretation in gates
        ),
        ["gate", "status", "interpretation"],
    )
    _write_text(
        commands,
        """# Candidate A Star-Cycle Gate Reproduction

```powershell
python -m unittest discover -s tests/research -p "test_*.py" -v
python scripts/run_candidate_a_star_cycle_gate.py
```

This command performs no SAB hot-path modification and makes no security or
complete-SAB performance claim.
""",
    )
    body = f"""# Candidate A Star-Cycle Mechanism Gate

Decision: `{result.decision}`.

The Stage203 `4r` support satisfies sampled zero/one phase equations, while
the standard PVW randomization gate is `{'PASS' if result.randomization_gate else 'FAIL'}`.
Dense support is the positive control. Production code permission remains
`false`; finite-field linear algebra is not an RLWE security proof.

Failure of the direct sparse standard-PVW representation routes the finite
campaign to Candidate B, Factorized Star-Cycle. Existing scalar and exact-dense
SAB paths are unchanged.
"""
    _write_text(report, body)
    _write_text(
        variant,
        f"""# Candidate A: Star-Cycle Sparse MAT-GGSW

- Decision: `{result.decision}`
- Semantic target: `P M = mu P`
- Declared work: `4r` selector-output terms
- Dense baseline work: `(r+1)^2` terms
- Production code permission: `false`
- Security scope: no claim from the finite checker
- Next route: `{'Candidate A key/security/noise preflight' if result.decision == ADMIT else 'Candidate B factorized realization'}`
""",
    )
    _write_text(
        experiment,
        """# Candidate A Star-Cycle Gate Registration

- Field: prime 257
- Lane counts: r=2, r=4, r=6
- Selector semantics: mu=0 and mu=1
- Secrets: deterministic nonzero vectors registered in the gate source
- Positive control: unrestricted dense support
- Negative control: generic dense kernel randomizer outside star support
- Primary gate: at least one kernel-randomization degree per input column
- Failure action: reject the direct sparse standard-PVW route and activate B
- C hot-path changes: prohibited
""",
    )

    indexed = [
        summary,
        phase,
        randomization,
        negative,
        source,
        proof,
        commands,
        report,
        variant,
        experiment,
    ]
    index_rows = []
    for path in indexed:
        data = path.read_bytes()
        index_rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    _write_csv(
        index,
        index_rows,
        ["path", "bytes", "sha256"],
    )
    return tuple(indexed + [index])


def main() -> int:
    result = evaluate_candidate_a(ROOT)
    write_gate_artifacts(ROOT, result)
    print(result.decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
