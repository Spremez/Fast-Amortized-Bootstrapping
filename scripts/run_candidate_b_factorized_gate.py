#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import platform
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.mat_sab.factorized_selector_model import (
    expected_phase,
    external_product,
    factor_cost,
    full_rank_homomorphic_image,
    homomorphic_image_fits_inner_dimension,
    homomorphic_image_rank,
    low_rank_homomorphic_image_control,
    phase,
    standard_selector,
    torus_normal_from_uniform_pair,
)


OUT = Path("repro/candidate_b_factorized_gate")
ADMIT = "ADMIT_CANDIDATE_B_KEY_DISTRIBUTION_PREFLIGHT"
REJECT = "REJECT_CANDIDATE_B_EXACT_STANDARD_PVW_FACTORIZATION_ROUTE_TO_C"
PRIME = 257
TARGET_R = (2, 4, 6)
SUMMARY_FIELDS = (
    "decision",
    "source_gate",
    "literature_scope_gate",
    "sampler_parity_gate",
    "phase_identity_gate",
    "mutation_control_gate",
    "full_rank_control_gate",
    "low_rank_control_gate",
    "cost_accounting_gate",
    "exact_standard_factorization_gate",
    "noiseless_only_linear_gate",
    "concrete_alternative_gate",
    "production_code_permission",
    "route",
)
SOURCE_SPECS = (
    (
        "pvw_sampling",
        "src/mosfhet/src/pvwtmlwe.c",
        "void pvmtmlwe_sample(",
        "code",
    ),
    (
        "torus_error_coefficients",
        "src/mosfhet/src/misc.c",
        "out[i] = double2torus(generate_normal_random(sigma));",
        "code",
    ),
    (
        "torus64_scale",
        "src/mosfhet/src/misc.c",
        "#define TORUS_SCALE 18446744073709551616.0",
        "code",
    ),
    (
        "pvw_phase",
        "src/mosfhet/src/pvwtmlwe.c",
        "void pvmtmlwe_phase(",
        "code",
    ),
    (
        "mat_selector_keygen",
        "src/mosfhet/src/mattrgsw.c",
        "void mat_trgsw_monomial_sample(",
        "code",
    ),
    (
        "mat_dense_external_product",
        "src/mosfhet/src/mattrgsw.c",
        "static void mat_trgsw_mul_pvmtmlwe_DFT_from_dec(",
        "code",
    ),
    (
        "sab_pvw_cmux",
        "src/sab_pvw.c",
        "void sab_pvw_CMUX(",
        "code",
    ),
    (
        "target_default_parameters",
        "main.c",
        "static SAB_PVW_Target_Params sab_pvw_target_params(void){",
        "code",
    ),
    (
        "candidate_a_terminal_evidence",
        "repro/candidate_a_star_cycle_gate/summary.csv",
        "REJECT_CANDIDATE_A_STANDARD_PVW_RANDOMIZATION_ROUTE_TO_B",
        "evidence",
    ),
    (
        "candidate_b_contract",
        "docs/superpowers/specs/2026-07-17-candidate-b-factorized-gate-design.md",
        "C = mu h I_m + v w^T + [0 | E]",
        "design",
    ),
)
LITERATURE_SPECS = (
    (
        "FAB686_2025",
        "https://eprint.iacr.org/2025/686",
        "docs/stage102_686_source_anchor_review_log.md",
        "FAB_COMPLEXITY_MODEL",
        "FULLTEXT_ANCHORS_REVIEWED",
        "Target SAB protocol and scoped complexity anchors.",
        "Does not prove the local factorized selector.",
    ),
    (
        "SHAREMASK25",
        "https://eprint.iacr.org/2025/2112",
        "repro/stage335_source_and_compact_route/source_acquisition_audit.csv",
        "LOCAL_FULLTEXT_AUDITED",
        "LOCAL_FULLTEXT_AUDITED",
        "Common-mask multi-body TFHE is established prior art.",
        "Does not prove Candidate B Theta(r) internal work.",
    ),
    (
        "BGH2012_565",
        "https://eprint.iacr.org/2012/565",
        "repro/stage230_source_verified_literature_novelty_audit/source_verification_refresh.csv",
        "BGH2012_565",
        "PRIMARY_METADATA_BACKGROUND_ONLY",
        "PVW/LWE packing ancestry only.",
        "No low-rank selector theorem is attributed.",
    ),
    (
        "CGGI2018_421",
        "https://eprint.iacr.org/2018/421",
        "repro/stage230_source_verified_literature_novelty_audit/source_verification_refresh.csv",
        "CGGI2018_421",
        "PRIMARY_METADATA_BACKGROUND_ONLY",
        "TFHE external-product background only.",
        "No Candidate B distribution theorem is attributed.",
    ),
)
ALTERNATIVE_PROOF_FIELDS = (
    "mechanism_id",
    "phase_gate",
    "distribution_security_gate",
    "shared_mask_closure_gate",
    "neighbor_cycle_gate",
    "theta_r_complete_cost_gate",
    "no_hidden_dense_work_gate",
    "amdahl_gate",
)
ALTERNATIVE_ARTIFACT_KINDS = {
    "equations",
    "key_distribution",
    "closure",
    "cost",
    "amdahl",
}
REGISTERED_ALTERNATIVE_CHECKERS: dict[
    str,
    Callable[[Path, dict[str, str], tuple[dict[str, str], ...]], bool],
] = {}


class GateEvidenceError(RuntimeError):
    def __init__(self, failed_gates: Iterable[str]):
        self.failed_gates = tuple(failed_gates)
        super().__init__(
            "inconclusive Candidate B gate evidence: "
            + ",".join(self.failed_gates)
        )


@dataclass(frozen=True)
class GateResult:
    decision: str
    source_gate: bool
    literature_scope_gate: bool
    sampler_parity_gate: bool
    phase_identity_gate: bool
    mutation_control_gate: bool
    full_rank_control_gate: bool
    low_rank_control_gate: bool
    cost_accounting_gate: bool
    exact_standard_factorization_gate: bool
    noiseless_only_linear_gate: bool
    concrete_alternative_gate: bool
    production_code_permission: bool
    source_rows: tuple[dict[str, object], ...]
    literature_rows: tuple[dict[str, object], ...]
    sampler_rows: tuple[dict[str, object], ...]
    phase_rows: tuple[dict[str, object], ...]
    mutation_rows: tuple[dict[str, object], ...]
    rank_rows: tuple[dict[str, object], ...]
    cost_rows: tuple[dict[str, object], ...]
    mechanism_rows: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class TargetParameters:
    out_k: int
    l: int
    out_N: int
    sigma_out_exponent: int
    torus_bits: int


_TARGET_PARAMETER_FIELDS = (
    ("int", "in_N"),
    ("int", "in_k"),
    ("int", "out_N"),
    ("int", "out_k"),
    ("int", "l"),
    ("int", "bg_bit"),
    ("int", "prec"),
    ("int", "h"),
    ("int", "r_prec"),
    ("int", "h_out"),
    ("int", "h_packing"),
    ("int", "ell_packing"),
    ("int", "b_packing"),
    ("int", "t_ks"),
    ("int", "b_ks"),
    ("double", "sigma_in"),
    ("double", "sigma_out"),
    ("double", "sigma_packing"),
)


def _target_parameters(root: Path) -> TargetParameters:
    try:
        main = (root / "main.c").read_text(encoding="utf-8")
        misc = (root / "src/mosfhet/src/misc.c").read_text(encoding="utf-8")
    except OSError as error:
        raise GateEvidenceError(("target_parameters",)) from error

    declarations = re.findall(
        r"typedef\s+struct\s*\{(?P<fields>.*?)\}\s*"
        r"SAB_PVW_Target_Params\s*;",
        main,
        flags=re.DOTALL,
    )
    if len(declarations) != 1:
        raise GateEvidenceError(("target_parameters",))
    fields = tuple(
        re.findall(
            r"^\s*(int|double)\s+([A-Za-z_]\w*)\s*;\s*$",
            declarations[0],
            flags=re.MULTILINE,
        )
    )
    if fields != _TARGET_PARAMETER_FIELDS:
        raise GateEvidenceError(("target_parameters",))

    defaults = re.findall(
        r"#else\s*\n\s*return\s+\(\s*SAB_PVW_Target_Params\s*\)"
        r"\s*\{(?P<values>[^{}]+)\};\s*\n#endif",
        main,
        flags=re.MULTILINE,
    )
    if len(defaults) != 1:
        raise GateEvidenceError(("target_parameters",))
    value_pattern = r"(?:0|[1-9]\d*|pow\(\s*2\s*,\s*-\d+\s*\))"
    if re.fullmatch(
        rf"\s*{value_pattern}(?:\s*,\s*{value_pattern}){{17}}\s*",
        defaults[0],
        flags=re.DOTALL,
    ) is None:
        raise GateEvidenceError(("target_parameters",))
    values = tuple(re.findall(value_pattern, defaults[0]))
    if len(values) != len(_TARGET_PARAMETER_FIELDS):
        raise GateEvidenceError(("target_parameters",))
    if any(not re.fullmatch(r"(?:0|[1-9]\d*)", value) for value in values[:15]):
        raise GateEvidenceError(("target_parameters",))
    sigma_match = re.fullmatch(r"pow\(2,\s*(-\d+)\)", values[16])
    if sigma_match is None:
        raise GateEvidenceError(("target_parameters",))

    scales = re.findall(
        r"#ifdef\s+TORUS32\s*\n\s*#define\s+TORUS_SCALE\s+"
        r"(?P<torus32>[0-9]+\.0)\s*\n#else\s*\n\s*"
        r"#define\s+TORUS_SCALE\s+(?P<default>[0-9]+\.0)\s*\n#endif",
        misc,
        flags=re.MULTILINE,
    )
    if len(scales) != 1:
        raise GateEvidenceError(("target_parameters",))
    default_scale = int(scales[0][1].split(".", maxsplit=1)[0])
    torus_bits = default_scale.bit_length() - 1
    if (
        default_scale != 1 << torus_bits
        or torus_bits not in (32, 64)
        or int(scales[0][0].split(".", maxsplit=1)[0]) != 1 << 32
    ):
        raise GateEvidenceError(("target_parameters",))

    out_N = int(values[2])
    out_k = int(values[3])
    l = int(values[4])
    if out_N <= 0 or out_k <= 0 or l <= 0:
        raise GateEvidenceError(("target_parameters",))
    return TargetParameters(
        out_k=out_k,
        l=l,
        out_N=out_N,
        sigma_out_exponent=int(sigma_match.group(1)),
        torus_bits=torus_bits,
    )


def _source_rows(root: Path) -> tuple[dict[str, object], ...]:
    rows = []
    for claim, relative, token, kind in SOURCE_SPECS:
        path = root / relative
        present = (
            path.is_file()
            and token in path.read_text(encoding="utf-8", errors="replace")
        )
        rows.append(
            {
                "claim": claim,
                "kind": kind,
                "path": relative,
                "token": token,
                "status": "PASS" if present else "FAIL",
            }
        )
    return tuple(rows)


def _literature_rows(root: Path) -> tuple[dict[str, object], ...]:
    rows = []
    for (
        source_id,
        primary_url,
        relative,
        token,
        support_level,
        allowed_claim,
        blocked_claim,
    ) in LITERATURE_SPECS:
        path = root / relative
        present = (
            path.is_file()
            and token in path.read_text(encoding="utf-8", errors="replace")
        )
        rows.append(
            {
                "source_id": source_id,
                "primary_url": primary_url,
                "local_evidence": relative,
                "local_evidence_sha256": (
                    hashlib.sha256(path.read_bytes()).hexdigest()
                    if path.is_file()
                    else ""
                ),
                "support_level": support_level,
                "allowed_claim": allowed_claim,
                "blocked_claim": blocked_claim,
                "status": "PASS" if present else "FAIL",
            }
        )
    return tuple(rows)


def _strict_single_csv(
    path: Path,
    fields: tuple[str, ...],
) -> dict[str, str]:
    try:
        with path.open(newline="", encoding="ascii") as handle:
            rows = list(csv.reader(handle, strict=True))
    except (csv.Error, OSError, UnicodeError) as error:
        raise GateEvidenceError(("registered_alternative_package",)) from error
    if (
        len(rows) != 2
        or tuple(rows[0]) != fields
        or len(rows[1]) != len(fields)
        or any(value == "" for value in rows[1])
    ):
        raise GateEvidenceError(("registered_alternative_package",))
    return dict(zip(fields, rows[1]))


def validate_registered_alternative(root: Path) -> bool:
    package = root / "repro/candidate_b_registered_alternative"
    if not package.exists():
        return False
    proof = _strict_single_csv(
        package / "proof_gate.csv",
        ALTERNATIVE_PROOF_FIELDS,
    )
    if any(
        proof[field] != "PASS"
        for field in ALTERNATIVE_PROOF_FIELDS
        if field != "mechanism_id"
    ):
        return False

    index_path = package / "artifact_index.csv"
    try:
        with index_path.open(newline="", encoding="ascii") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != ("kind", "path", "sha256"):
                raise GateEvidenceError(("registered_alternative_package",))
            rows = list(reader)
    except (csv.Error, OSError, UnicodeError) as error:
        raise GateEvidenceError(("registered_alternative_package",)) from error
    if (
        {row.get("kind") for row in rows} != ALTERNATIVE_ARTIFACT_KINDS
        or any(not row.get("path") or not row.get("sha256") for row in rows)
    ):
        raise GateEvidenceError(("registered_alternative_package",))
    resolved_root = root.resolve(strict=True)
    for row in rows:
        artifact = (root / row["path"]).resolve(strict=True)
        if not artifact.is_relative_to(resolved_root) or not artifact.is_file():
            raise GateEvidenceError(("registered_alternative_package",))
        if hashlib.sha256(artifact.read_bytes()).hexdigest() != row["sha256"]:
            raise GateEvidenceError(("registered_alternative_package",))
    checker = REGISTERED_ALTERNATIVE_CHECKERS.get(proof["mechanism_id"])
    if checker is None:
        return False
    return checker(root, proof, tuple(rows))


def _deterministic_inputs(
    r: int,
) -> tuple[
    tuple[int, ...],
    tuple[int, ...],
    tuple[int, ...],
    tuple[tuple[int, ...], ...],
]:
    size = r + 1
    secret = tuple(index + 2 for index in range(r))
    masks = tuple(2 * index + 5 for index in range(size))
    digits = tuple(3 * index + 7 for index in range(size))
    errors = tuple(
        tuple((row + 1) * (lane + 2) for lane in range(r))
        for row in range(size)
    )
    return secret, masks, digits, errors


def _serialized(values: Iterable[int]) -> str:
    return ";".join(str(value) for value in values)


def evaluate_candidate_b(root: Path = ROOT) -> GateResult:
    source_rows = _source_rows(root)
    source_gate = all(row["status"] == "PASS" for row in source_rows)
    if not source_gate:
        raise GateEvidenceError(("source_anchors",))
    target = _target_parameters(root)
    literature_rows = _literature_rows(root)
    literature_gate = all(
        row["status"] == "PASS"
        for row in literature_rows
    )
    if not literature_gate:
        raise GateEvidenceError(("literature_scope_anchors",))

    sigma = 2 ** target.sigma_out_exponent
    sampler_specs = (
        (
            "even",
            0x9E3779B97F4A7C15,
            0xA36A9465A325DA06,
            -11446,
        ),
        (
            "odd",
            0x3C6EF372FE94F82A,
            0x751FDE9874B8C709,
            1791,
        ),
    )
    sampler_rows = []
    sampler_gate = True
    for parity, rnd0, rnd1, expected_value in sampler_specs:
        try:
            value = torus_normal_from_uniform_pair(
                rnd0,
                rnd1,
                sigma,
                torus_bits=target.torus_bits,
            )
        except ValueError as error:
            raise GateEvidenceError(("sampler_parity_support",)) from error
        passed = (
            value == expected_value
            and value % 2 == (0 if parity == "even" else 1)
        )
        sampler_gate &= passed
        sampler_rows.append(
            {
                "parity": parity,
                "rnd0": f"0x{rnd0:016x}",
                "rnd1": f"0x{rnd1:016x}",
                "sigma": f"2^{target.sigma_out_exponent}",
                "torus_bits": target.torus_bits,
                "out_k": target.out_k,
                "T": target.l,
                "N": target.out_N,
                "image_pattern": (
                    "odd diagonal coefficient-sum; even off-diagonal sum"
                ),
                "value": value,
                "expected_value": expected_value,
                "status": "PASS" if passed else "FAIL",
            }
        )

    phase_rows: list[dict[str, object]] = []
    mutation_rows: list[dict[str, object]] = []
    rank_rows: list[dict[str, object]] = []
    cost_rows: list[dict[str, object]] = []
    phase_gate = True
    mutation_gate = True
    full_rank_gate = True
    low_rank_gate = True

    for r in TARGET_R:
        secret, masks, digits, errors = _deterministic_inputs(r)
        for mu in (0, 1):
            selector = standard_selector(
                secret,
                mu,
                masks,
                errors,
                PRIME,
                gadget=3,
            )
            output = external_product(digits, selector, PRIME)
            actual = phase(output, secret, PRIME)
            expected = expected_phase(
                digits,
                errors,
                secret,
                mu,
                PRIME,
                gadget=3,
            )
            hand_oracle = True
            oracle = "algebraic_identity"
            if r == 2 and mu == 1:
                oracle = "hand_derived_r2"
                hand_oracle = (
                    selector
                    == (
                        (8, 12, 18),
                        (7, 21, 27),
                        (9, 24, 39),
                    )
                    and output == (243, 92, 132)
                    and actual == (120, 174)
                    and expected == (120, 174)
                )
            passed = actual == expected and hand_oracle
            phase_gate &= passed
            phase_rows.append(
                {
                    "r": r,
                    "mu": mu,
                    "prime": PRIME,
                    "oracle": oracle,
                    "actual": _serialized(actual),
                    "expected": _serialized(expected),
                    "status": "PASS" if passed else "FAIL",
                }
            )

        base = expected_phase(
            digits,
            errors,
            secret,
            1,
            PRIME,
            gadget=3,
        )
        changed_errors = [list(row) for row in errors]
        lane = r - 1
        changed_errors[0][lane] = (changed_errors[0][lane] + 1) % PRIME
        changed_selector = standard_selector(
            secret,
            1,
            masks,
            changed_errors,
            PRIME,
            gadget=3,
        )
        changed_actual = phase(
            external_product(digits, changed_selector, PRIME),
            secret,
            PRIME,
        )
        changed_expected = expected_phase(
            digits,
            changed_errors,
            secret,
            1,
            PRIME,
            gadget=3,
        )
        delta = tuple(
            (after - before) % PRIME
            for before, after in zip(base, changed_expected)
        )
        expected_delta = tuple(
            digits[0] % PRIME if current == lane else 0
            for current in range(r)
        )
        mutation_passed = (
            changed_actual == changed_expected and delta == expected_delta
        )
        mutation_gate &= mutation_passed
        mutation_rows.append(
            {
                "r": r,
                "control": "increment_error_row0_last_lane",
                "observed_delta": _serialized(delta),
                "expected_delta": _serialized(expected_delta),
                "status": "PASS" if mutation_passed else "FAIL",
            }
        )

        full = full_rank_homomorphic_image(r)
        full_rank = homomorphic_image_rank(full)
        full_rank_gate &= full_rank == r
        for q in range(1, r):
            possible = homomorphic_image_fits_inner_dimension(full, q)
            passed = full_rank == r and not possible
            full_rank_gate &= passed
            rank_rows.append(
                {
                    "r": r,
                    "q": q,
                    "control": "standard_support_full_rank_image",
                    "image_map": "phi(f)=f(1)_mod_2",
                    "witness_pattern": "phi(E)=[I_r;0]",
                    "observed_rank": full_rank,
                    "expected_rank": r,
                    "observed_possible": "yes" if possible else "no",
                    "expected_possible": "no",
                    "status": "PASS" if passed else "FAIL",
                }
            )

            low = low_rank_homomorphic_image_control(r, q)
            low_rank = homomorphic_image_rank(low)
            possible = homomorphic_image_fits_inner_dimension(low, q)
            passed = low_rank == q and possible
            low_rank_gate &= passed
            rank_rows.append(
                {
                    "r": r,
                    "q": q,
                    "control": "constructed_low_rank_image",
                    "image_map": "phi(f)=f(1)_mod_2",
                    "witness_pattern": "rank_q_control",
                    "observed_rank": low_rank,
                    "expected_rank": q,
                    "observed_possible": "yes" if possible else "no",
                    "expected_possible": "yes",
                    "status": "PASS" if passed else "FAIL",
                }
            )

        for q in range(1, r + 1):
            cost = factor_cost(r, q)
            cost_rows.append(
                {
                    "r": r,
                    "q": q,
                    "dense_products": cost.dense_products,
                    "generic_left_products": cost.generic_left_products,
                    "generic_right_products": cost.generic_right_products,
                    "separate_diagonal_products": (
                        cost.separate_diagonal_products
                    ),
                    "generic_dense_factor_products": (
                        cost.generic_dense_factor_products
                    ),
                    "generic_dense_factor_beats_dense": (
                        "yes"
                        if cost.generic_dense_factor_beats_dense
                        else "no"
                    ),
                    "retained_dense_error_products": (
                        cost.retained_dense_error_products
                    ),
                    "retained_dense_error_order": "Theta(r^2)",
                }
            )

    cost_gate = all(
        row["dense_products"] == (row["r"] + 1) ** 2
        and row["retained_dense_error_products"]
        == (row["r"] + 1) * row["r"]
        for row in cost_rows
    ) and all(
        row["generic_dense_factor_beats_dense"] == "no"
        for row in cost_rows
        if row["q"] == row["r"]
    )

    failed_prerequisites = [
        name
        for name, passed in (
            ("sampler_parity_support", sampler_gate),
            ("phase_identity", phase_gate),
            ("mutation_controls", mutation_gate),
            ("full_rank_controls", full_rank_gate),
            ("low_rank_controls", low_rank_gate),
            ("cost_accounting", cost_gate),
        )
        if not passed
    ]
    if failed_prerequisites:
        raise GateEvidenceError(failed_prerequisites)

    # Once the supported rank-r image and rank controls pass, exact q<r
    # representation is rejected by the multiplicative image argument.
    exact_standard_gate = False
    noiseless_only_gate = all(
        not factor_cost(r, 1).retained_dense_error_is_quadratic
        for r in TARGET_R
    )
    concrete_alternative_gate = validate_registered_alternative(root)
    decision = ADMIT if concrete_alternative_gate else REJECT
    mechanism_rows = (
        {
            "variant": "B0",
            "mechanism": "exact_standard_distribution_q_lt_r",
            "distribution": "current_standard_PVW",
            "complete_work": "Theta(r)_required",
            "disposition": (
                "ADMIT" if exact_standard_gate else "REJECT_RANK_SUPPORT"
            ),
        },
        {
            "variant": "B1",
            "mechanism": "factor_noiseless_term_keep_dense_error",
            "distribution": "current_standard_PVW",
            "complete_work": "Theta(r^2)",
            "disposition": "REJECT_DENSE_ERROR_REMAINS",
        },
        {
            "variant": "B2",
            "mechanism": "correlated_or_low_rank_error",
            "distribution": "changed",
            "complete_work": "potentially_Theta(r)",
            "disposition": "ROUTE_C_SECURITY_NOISE_REQUIRED",
        },
        {
            "variant": "B3",
            "mechanism": "encrypted_factors_and_relinearization",
            "distribution": "new_evaluation_key",
            "complete_work": (
                "Theta(r)_registered"
                if concrete_alternative_gate
                else "unaccounted"
            ),
            "disposition": (
                "ADMIT_REGISTERED_ALTERNATIVE"
                if concrete_alternative_gate
                else "UNREGISTERED_NO_COMPLETE_CONSTRUCTION"
            ),
        },
        {
            "variant": "B4",
            "mechanism": "lane_pair_then_shared_mask_conversion",
            "distribution": "new_intermediate_state",
            "complete_work": "unaccounted",
            "disposition": "UNREGISTERED_NO_CLOSED_CONVERSION",
        },
    )
    return GateResult(
        decision=decision,
        source_gate=source_gate,
        literature_scope_gate=literature_gate,
        sampler_parity_gate=sampler_gate,
        phase_identity_gate=phase_gate,
        mutation_control_gate=mutation_gate,
        full_rank_control_gate=full_rank_gate,
        low_rank_control_gate=low_rank_gate,
        cost_accounting_gate=cost_gate,
        exact_standard_factorization_gate=exact_standard_gate,
        noiseless_only_linear_gate=noiseless_only_gate,
        concrete_alternative_gate=concrete_alternative_gate,
        production_code_permission=False,
        source_rows=source_rows,
        literature_rows=literature_rows,
        sampler_rows=tuple(sampler_rows),
        phase_rows=tuple(phase_rows),
        mutation_rows=tuple(mutation_rows),
        rank_rows=tuple(rank_rows),
        cost_rows=tuple(cost_rows),
        mechanism_rows=mechanism_rows,
    )


def _status(value: bool) -> str:
    return "PASS" if value else "FAIL"


def validate_gate_result(result: GateResult) -> None:
    prerequisites = (
        result.source_gate,
        result.literature_scope_gate,
        result.sampler_parity_gate,
        result.phase_identity_gate,
        result.mutation_control_gate,
        result.full_rank_control_gate,
        result.low_rank_control_gate,
        result.cost_accounting_gate,
    )
    if not all(prerequisites):
        raise ValueError("gate result contains failed evidence prerequisites")
    if result.exact_standard_factorization_gate:
        raise ValueError("exact standard factorization contradicts rank evidence")
    if result.noiseless_only_linear_gate:
        raise ValueError("noiseless-only route contradicts retained dense errors")
    expected = ADMIT if result.concrete_alternative_gate else REJECT
    if result.decision != expected:
        raise ValueError("decision does not match mechanism gates")
    if result.production_code_permission:
        raise ValueError("mechanism gate cannot grant production permission")


def canonical_summary_record(result: GateResult) -> dict[str, str]:
    validate_gate_result(result)
    return {
        "decision": result.decision,
        "source_gate": _status(result.source_gate),
        "literature_scope_gate": _status(result.literature_scope_gate),
        "sampler_parity_gate": _status(result.sampler_parity_gate),
        "phase_identity_gate": _status(result.phase_identity_gate),
        "mutation_control_gate": _status(result.mutation_control_gate),
        "full_rank_control_gate": _status(result.full_rank_control_gate),
        "low_rank_control_gate": _status(result.low_rank_control_gate),
        "cost_accounting_gate": _status(result.cost_accounting_gate),
        "exact_standard_factorization_gate": _status(
            result.exact_standard_factorization_gate
        ),
        "noiseless_only_linear_gate": _status(
            result.noiseless_only_linear_gate
        ),
        "concrete_alternative_gate": _status(
            result.concrete_alternative_gate
        ),
        "production_code_permission": (
            "yes" if result.production_code_permission else "no"
        ),
        "route": (
            "candidate_b_key_distribution_preflight"
            if result.decision == ADMIT
            else "candidate_c_rank_bounded_shared_mask_state"
        ),
    }


def _write_csv(
    path: Path,
    rows: Iterable[dict[str, object]],
    fields: Iterable[str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="ascii") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(fields),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(
            {field: row.get(field, "") for field in writer.fieldnames}
            for row in rows
        )


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        content.rstrip() + "\n",
        encoding="ascii",
        newline="\n",
    )


def _literature_boundary() -> str:
    return """## Primary-Source Boundary

- 2025/686 target SAB, locally reviewed full-text anchors:
  https://eprint.iacr.org/2025/686
- Common-mask ciphertext and CM-GGSW prior art:
  https://eprint.iacr.org/2025/2112
- Packed/PVW and standard TFHE sources are metadata/background scoped:
  https://eprint.iacr.org/2012/565 and
  https://eprint.iacr.org/2018/421

The local Stage102 and Stage335 logs contain the reviewed full-text claim
anchors. The PVW and TFHE rows are used only for background positioning. The
standard common-mask GGSW realization retains a quadratic `(k+r)^2` lane
factor. No checked source supplies the complete Candidate B conjunction.
This is not a general impossibility theorem and is not a novelty proof."""


def _report(result: GateResult) -> str:
    route = (
        """No concrete encrypted-factor/relinearization or closed lane-pair
conversion satisfying the complete cost gate is registered.

Production hot-path permission remains `false`. Candidate C is the next
finite route. Existing scalar and exact-dense PVW/MAT-SAB implementations are
unchanged."""
        if result.decision == REJECT
        else """A hash-bound alternative mechanism package satisfies the
registered mechanism gates. Candidate B advances only to key, security, and
noise preflight. Production hot-path permission remains `false`; no
complete-SAB acceleration claim is authorized."""
    )
    return f"""# Candidate B Factorized Mechanism Gate

Decision: `{result.decision}`.

The exact current standard-PVW selector is

```text
C = mu h I + v w^T + [0 | E].
```

The phase identity passes for r=2/4/6 and mu=0/1, including a hand-derived
r=2 orientation oracle. Explicit 128-bit inputs to the current normal-sampler
formula produce both even and odd Torus outputs. The map
`phi(f)=f(1) mod 2` is a ring homomorphism from the finite ring
`(Z/2^64Z)[X]/(X^N + 1)` to GF(2). Independent coefficient sampling therefore supports a parity-pattern
error witness whose image has rank r, while every q<r ring factorization has
image rank at most q. The constructed rank-q image controls pass, so the
rejection is not caused by a checker that rejects all factorizations.

Factoring only the noiseless rank-one term leaves `(r+1)r` dense error
products. The recorded q=r count is for generic dense two-sided factors, not
a universal arithmetic lower bound.

{route}

{_literature_boundary()}

## Claim Boundary

This result rejects the tested exact factorization of the current independent
PVW row distribution. It is not a general impossibility theorem for every
structured key, correlated-error assumption, or redesigned accumulator."""


def _variant(result: GateResult) -> str:
    alternative = (
        "B3/B4 have no registered complete construction, so B routes to C."
        if result.decision == REJECT
        else "A hash-bound B3/B4 package is registered for the next preflight."
    )
    return f"""# Candidate B: Factorized Star-Cycle

Status: `{result.decision}`.

Candidate B tests whether the Stage203 four-family star-cycle semantics can
be realized as a complete Theta(r)-work standard-PVW encrypted operator.
The multiplicative parity-evaluation image rejects exact q<r representation
of a supported full-rank independent-error witness. Generic dense q=r and
noiseless-only variants do not supply the required complete cost reduction.
B2 changes the distribution and requires Candidate C-level analysis.
{alternative}

{_literature_boundary()}

This disposition is not a general impossibility theorem. It changes no
production implementation and makes no complete-SAB performance claim."""


def _experiment(result: GateResult) -> str:
    return f"""# Candidate B Factorized Gate Experiment

Decision: `{result.decision}`.

## Fixed Inputs

- finite field: GF(257)
- body counts: r=2,4,6
- selector bits: mu=0,1
- factor ranks: q=1,...,r
- deterministic masks, digits, errors, and mutations

## Gates

1. Source anchors and scoped local literature-review evidence must be present.
2. Exact selector phase identities must pass.
3. Error mutation controls must change the predicted lane.
4. Explicit current-sampler inputs must witness even and odd Torus outputs.
5. A multiplicative GF(2) image of a supported rank-r ring witness must
   reject every q<r.
6. Constructed rank-q image controls must be admitted at exactly q.
7. Generic dense-factor and retained-error costs must be recorded without
   calling them universal lower bounds.
8. Failed evidence is inconclusive; only failed mechanisms route B to C.

## Reproduction

```text
python scripts/run_candidate_b_factorized_gate.py
python -m unittest tests.research.test_candidate_b_gate -v
```

No benchmark or production-code claim is made."""


def _input_manifest_rows(root: Path) -> tuple[dict[str, str], ...]:
    paths = {
        relative
        for _, relative, _, _ in SOURCE_SPECS
    }
    paths.update(
        relative
        for _, _, relative, _, _, _, _ in LITERATURE_SPECS
    )
    paths.update(
        {
            "main.c",
            "research/mat_sab/factorized_selector_model.py",
            "scripts/run_candidate_b_factorized_gate.py",
            "paper_techgraphs/candidate_b_factorized_selector.yaml",
            "theory_checks/candidate_b_factorized_standard_pvw_model.md",
            "repro/stage335_source_and_compact_route/sharing_mask_anchor_hits.csv",
        }
    )
    rows = []
    for relative in sorted(paths):
        path = root / relative
        if not path.is_file():
            raise GateEvidenceError(("input_manifest",))
        rows.append(
            {
                "path": relative,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    return tuple(rows)


def _git_head(root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _environment_rows(root: Path) -> tuple[dict[str, str], ...]:
    target = _target_parameters(root)
    return (
        {"key": "date", "value": "2026-07-17"},
        {"key": "input_head", "value": _git_head(root)},
        {"key": "python_version", "value": platform.python_version()},
        {"key": "platform", "value": platform.platform()},
        {"key": "target_out_k", "value": str(target.out_k)},
        {"key": "target_T", "value": str(target.l)},
        {"key": "target_N", "value": str(target.out_N)},
        {"key": "target_sigma", "value": f"2^{target.sigma_out_exponent}"},
        {"key": "torus_bits", "value": str(target.torus_bits)},
        {"key": "phase_field", "value": "GF(257)"},
        {"key": "rank_image", "value": "GF(2), phi(f)=f(1) mod 2"},
    )


def write_gate_artifacts(
    root: Path,
    result: GateResult,
) -> tuple[Path, ...]:
    out = root / OUT
    summary = out / "summary.csv"
    source = out / "source_mapping.csv"
    literature_path = out / "literature_claims.csv"
    sampler_path = out / "sampler_support.csv"
    phase_path = out / "phase_identity.csv"
    rank_path = out / "rank_controls.csv"
    cost_path = out / "factor_cost.csv"
    mechanism_path = out / "mechanism_matrix.csv"
    proof_path = out / "proof_gate.csv"
    commands_path = out / "reproduction_commands.md"
    input_manifest_path = out / "input_manifest.csv"
    environment_path = out / "environment.csv"
    report_path = root / "docs/candidate_b_factorized_mechanism_gate.md"
    variant_path = (
        root / "algorithm_variants/candidate_b_factorized_star_cycle.md"
    )
    experiment_path = (
        root / "experiments/candidate_b_factorized_gate_plan.md"
    )
    index_path = out / "artifact_index.csv"

    _write_csv(
        summary,
        [canonical_summary_record(result)],
        SUMMARY_FIELDS,
    )
    _write_csv(
        source,
        result.source_rows,
        ("claim", "kind", "path", "token", "status"),
    )
    _write_csv(
        literature_path,
        result.literature_rows,
        (
            "source_id",
            "primary_url",
            "local_evidence",
            "local_evidence_sha256",
            "support_level",
            "allowed_claim",
            "blocked_claim",
            "status",
        ),
    )
    _write_csv(
        sampler_path,
        result.sampler_rows,
        (
            "parity",
            "rnd0",
            "rnd1",
            "sigma",
            "torus_bits",
            "out_k",
            "T",
            "N",
            "image_pattern",
            "value",
            "expected_value",
            "status",
        ),
    )
    phase_rows = list(result.phase_rows) + [
        {
            "r": row["r"],
            "mu": "mutation",
            "prime": PRIME,
            "oracle": row["control"],
            "actual": row["observed_delta"],
            "expected": row["expected_delta"],
            "status": row["status"],
        }
        for row in result.mutation_rows
    ]
    _write_csv(
        phase_path,
        phase_rows,
        ("r", "mu", "prime", "oracle", "actual", "expected", "status"),
    )
    _write_csv(
        rank_path,
        result.rank_rows,
        (
            "r",
            "q",
            "control",
            "image_map",
            "witness_pattern",
            "observed_rank",
            "expected_rank",
            "observed_possible",
            "expected_possible",
            "status",
        ),
    )
    _write_csv(
        cost_path,
        result.cost_rows,
        (
            "r",
            "q",
            "dense_products",
            "generic_left_products",
            "generic_right_products",
            "separate_diagonal_products",
            "generic_dense_factor_products",
            "generic_dense_factor_beats_dense",
            "retained_dense_error_products",
            "retained_dense_error_order",
        ),
    )
    _write_csv(
        mechanism_path,
        result.mechanism_rows,
        (
            "variant",
            "mechanism",
            "distribution",
            "complete_work",
            "disposition",
        ),
    )
    proof_rows = (
        {
            "gate": "source_anchors",
            "status": _status(result.source_gate),
            "classification": "evidence_prerequisite",
            "interpretation": "code, predecessor evidence, and design anchored",
        },
        {
            "gate": "literature_scope",
            "status": _status(result.literature_scope_gate),
            "classification": "evidence_prerequisite",
            "interpretation": (
                "full-text and metadata-only support levels are separated"
            ),
        },
        {
            "gate": "phase_identity",
            "status": _status(result.phase_identity_gate),
            "classification": "evidence_prerequisite",
            "interpretation": "exact current selector phase equation holds",
        },
        {
            "gate": "sampler_parity_support",
            "status": _status(result.sampler_parity_gate),
            "classification": "evidence_prerequisite",
            "interpretation": (
                "explicit uniform-word pairs produce even and odd errors"
            ),
        },
        {
            "gate": "mutation_control",
            "status": _status(result.mutation_control_gate),
            "classification": "evidence_prerequisite",
            "interpretation": "one error mutation changes one predicted lane",
        },
        {
            "gate": "full_rank_control",
            "status": _status(result.full_rank_control_gate),
            "classification": "evidence_prerequisite",
            "interpretation": (
                "a supported parity-pattern witness maps to rank r "
                "under phi(f)=f(1) mod 2"
            ),
        },
        {
            "gate": "low_rank_control",
            "status": _status(result.low_rank_control_gate),
            "classification": "evidence_prerequisite",
            "interpretation": "constructed rank-q images are admitted",
        },
        {
            "gate": "cost_accounting",
            "status": _status(result.cost_accounting_gate),
            "classification": "evidence_prerequisite",
            "interpretation": (
                "generic factor products and retained dense errors are counted"
            ),
        },
        {
            "gate": "exact_standard_q_lt_r_factorization",
            "status": _status(result.exact_standard_factorization_gate),
            "classification": "mechanism_rejection",
            "interpretation": (
                "full-rank homomorphic image cannot fit q below r"
            ),
        },
        {
            "gate": "noiseless_only_linear",
            "status": _status(result.noiseless_only_linear_gate),
            "classification": "mechanism_rejection",
            "interpretation": "retained dense error work is Theta(r^2)",
        },
        {
            "gate": "concrete_alternative",
            "status": _status(result.concrete_alternative_gate),
            "classification": "mechanism_gate",
            "interpretation": (
                "hash-bound artifacts and a registered semantic checker "
                "are both required"
            ),
        },
        {
            "gate": "production_hot_path_permission",
            "status": "YES" if result.production_code_permission else "NO",
            "classification": "permission",
            "interpretation": "mechanism gate cannot authorize production code",
        },
    )
    _write_csv(
        proof_path,
        proof_rows,
        ("gate", "status", "classification", "interpretation"),
    )
    _write_text(
        commands_path,
        """# Candidate B Reproduction Commands

```text
python scripts/run_candidate_b_factorized_gate.py
python -m unittest tests.research.test_factorized_selector_model -v
python -m unittest tests.research.test_candidate_b_gate -v
python -m unittest discover -s tests/research -p "test_*.py" -v
python scripts/mat_sab_research_state.py validate
```""",
    )
    _write_text(report_path, _report(result))
    _write_text(variant_path, _variant(result))
    _write_text(experiment_path, _experiment(result))
    _write_csv(
        input_manifest_path,
        _input_manifest_rows(root),
        ("path", "sha256"),
    )
    _write_csv(
        environment_path,
        _environment_rows(root),
        ("key", "value"),
    )

    artifacts = (
        summary,
        source,
        literature_path,
        sampler_path,
        phase_path,
        rank_path,
        cost_path,
        mechanism_path,
        proof_path,
        commands_path,
        input_manifest_path,
        environment_path,
        report_path,
        variant_path,
        experiment_path,
    )
    index_rows = [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in artifacts
    ]
    _write_csv(index_path, index_rows, ("path", "sha256"))
    return artifacts + (index_path,)


def main() -> int:
    result = evaluate_candidate_b(ROOT)
    write_gate_artifacts(ROOT, result)
    print(result.decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
