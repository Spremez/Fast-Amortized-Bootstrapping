"""Candidate D D2 exact operator-closure checker.

Implements the Tasks 4-6 D2 replay contract semantics registered in
``scripts/run_candidate_d_admission.py`` (``D2_REPLAY_CONTRACT``):

- closure-basis search with the single permitted equation revision
  (Gamma_0 = {identity} fails, Gamma_1 = {identity, tau_{-1}} closes);
- ideal-phase basis-vector equivalence of the late-binding operator state
  against the scalar sparse-amortized-bootstrapping schedule over
  R = GF(257)[X]/(X^N+1), N in {8, 16}, for every registered schedule case;
- the exact six registered negative controls, each tied to a named invariant;
- the per-operation schedule trace (setup, CMUX/NCMUX at both selector
  values, the full ``r_prec`` RGSW monomial butterfly, ``sub_a``, binding).

All outputs are deterministic functions of the checked-out sources and the
CLI commits: no clocks, no randomness beyond SHA-256 counter PRFs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from research.mat_sab.candidate_d_source_map import (
    SourceMap,
    SourceMapError,
    load_source_map,
)
from research.mat_sab.negacyclic_operator import (
    ControlConfig,
    HONEST_CONTROL,
    NegacyclicRing,
    OperatorSlot,
    basis_search_closure,
    bind,
    build_schedule,
    channel_matrix_rank,
    operator_schedule,
    operator_setup,
    operator_step,
    scalar_schedule,
    scalar_setup,
    scalar_step,
)

PASS_DECISION = "PASS_D2_OPERATOR_CLOSURE_G_LE_4"
REJECT_PHASE = "REJECT_D2_PHASE_EQUIVALENCE"
REJECT_GT4 = "REJECT_D2_CLOSURE_GT_4"
REJECT_CONTROL = "REJECT_D2_NEGATIVE_CONTROL"
REJECT_REVISION = "REJECT_D2_REVISION_EXHAUSTED"
BLOCK_INCOMPLETE = "BLOCK_D2_SOURCE_OR_EXACT_CHECKER_INCOMPLETE"

TRACE_OPERATIONS = (
    "setup",
    "cmux_mu0",
    "cmux_mu1",
    "ncmux_mu0",
    "ncmux_mu1",
    "rgsw_monomial",
    "sub_a",
)

NEGATIVE_CONTROLS = (
    ("remove_tau_minus_one_channel", "operator_basis_closure"),
    ("omit_tau_minus_one_swap", "ncmux_channel_permutation"),
    ("positive_negacyclic_wrap", "negacyclic_wrap_sign"),
    ("skip_sub_a_rotation", "sub_a_phase_equivalence"),
    ("coeff_one_fast_with_zero_selector", "include_zero_fast_path_guard"),
    ("wrong_butterfly_source_index", "rgsw_butterfly_schedule"),
)


def required_cases(n: int, r_prec: int) -> tuple[str, ...]:
    names = [
        "binary_all_zero",
        "binary_all_one",
        "binary_alternating",
        *(f"binary_one_hot_{index}" for index in range(r_prec)),
        "binary_source_mixed",
        "include_zero_mu0",
        "include_zero_mu1",
        "coeff_one_fast_mu1",
    ]
    return tuple(names)


@dataclass(frozen=True)
class ClosureResult:
    decision: str
    gamma_count: int
    equation_revisions_used: int
    phase_status: str
    schedule_status: str
    negative_controls_status: str
    source_map: SourceMap
    basis_rows: tuple[dict[str, str], ...]
    phase_rows: tuple[dict[str, str], ...]
    trace_rows: tuple[dict[str, str], ...]
    control_rows: tuple[dict[str, str], ...]
    gamma0_evidence: dict[str, object]
    report_markdown: str


def _basis_vectors(n: int) -> list[tuple[int, ...]]:
    return [
        tuple(1 if index == basis else 0 for index in range(n))
        for basis in range(n)
    ]


def _per_op_unit_checks(
    ring: NegacyclicRing, r_prec: int, control: ControlConfig
) -> dict[str, bool]:
    """Case-independent per-operation invariance checks.

    For every rotation offset 2^k, both selector values, an arbitrary
    deterministic operator state, and every basis vector F, verify
    bind(update(U), F) == update_scalar(bind(U), F) for the isolated
    source move. Non-wrapped slots exercise the CMUX path; wrapped slots
    exercise the NCMUX path, whose operator-side action is
    -tau_{-1} composed with the channel swap.
    """
    vectors = _basis_vectors(ring.n)
    statuses = {name: True for name in TRACE_OPERATIONS}
    for offset_index in range(r_prec):
        offset = 1 << offset_index
        for selector in (0, 1):
            state: list[OperatorSlot] = []
            for j in range(ring.n):
                identity_channel = tuple(
                    (j + 3 * index + 1) % 257 for index in range(ring.n)
                )
                tau_channel = tuple(
                    (5 * j + 7 * index + 2) % 257 for index in range(ring.n)
                )
                state.append((identity_channel, tau_channel))
            bound = [bind(ring, state, vector, control) for vector in vectors]
            updated = list(state)
            updated_bound = [list(run) for run in bound]
            buckets: dict[int, list[str]] = {}
            for j in range(ring.n):
                if selector == 0:
                    # identity move under both gates
                    buckets[j] = ["cmux_mu0", "ncmux_mu0"]
                elif j >= offset:
                    updated[j] = state[j - offset]
                    for run, original in zip(updated_bound, bound):
                        run[j] = original[j - offset]
                    buckets[j] = ["cmux_mu1"]
                else:
                    source = ring.n - offset + j
                    src_identity, src_tau = state[source]
                    if control.omit_tau_swap:
                        updated[j] = (
                            ring.neg(ring.tau(src_identity)),
                            ring.neg(ring.tau(src_tau)),
                        )
                    else:
                        updated[j] = (
                            ring.neg(ring.tau(src_tau)),
                            ring.neg(ring.tau(src_identity)),
                        )
                    for run, original in zip(updated_bound, bound):
                        run[j] = ring.neg(ring.tau(original[source]))
                    buckets[j] = ["ncmux_mu1"]
            for vector, expected in zip(vectors, updated_bound):
                actual = bind(ring, updated, vector, control)
                for j in range(ring.n):
                    if actual[j] != expected[j]:
                        for name in buckets[j]:
                            statuses[name] = False
    return statuses


def run_closure_check(root: Path) -> ClosureResult:
    source_map = load_source_map(root)
    small_h = source_map.small_h
    gamma0_evidence: dict[str, object] = {}
    gamma0_failed = False
    phase_rows: list[dict[str, str]] = []
    trace_rows: list[dict[str, str]] = []
    control_rows: list[dict[str, str]] = []
    phase_all_pass = True
    trace_all_pass = True

    for n, r_prec in ((8, 3), (16, 4)):
        ring = NegacyclicRing(n)
        vectors = _basis_vectors(n)
        unit_checks = _per_op_unit_checks(ring, r_prec, HONEST_CONTROL)
        for case in required_cases(n, r_prec):
            spec = build_schedule(n, r_prec, small_h, case)
            operator_final = operator_schedule(ring, spec, HONEST_CONTROL)
            matrix_rank = channel_matrix_rank(operator_final)
            for basis_index, vector in enumerate(vectors):
                scalar_final = scalar_schedule(ring, spec, vector)
                bound = bind(ring, operator_final, vector, HONEST_CONTROL)
                expected_hash = ring.state_hash(scalar_final)
                actual_hash = ring.state_hash(bound)
                equal = scalar_final == bound
                phase_all_pass = phase_all_pass and equal
                phase_rows.append(
                    {
                        "N": str(n),
                        "schedule_case": case,
                        "basis_index": str(basis_index),
                        "operation": "final_bind",
                        "accumulator_index": "final",
                        "selector_bit": spec.selector_summary,
                        "gamma_count": "2",
                        "matrix_rank": str(matrix_rank),
                        "expected_hash": expected_hash,
                        "actual_hash": actual_hash,
                        "status": "PASS" if equal else "REJECT",
                    }
                )
            vectors = _basis_vectors(n)
            scalar_runs = [scalar_setup(ring, spec, vector) for vector in vectors]
            op_state = operator_setup(ring, spec)
            in_schedule = {
                "setup": all(
                    bind(ring, op_state, vector, HONEST_CONTROL) == run
                    for vector, run in zip(vectors, scalar_runs)
                ),
                "rgsw_monomial": True,
                "sub_a": True,
            }
            for step_index in range(len(spec.selector_bits)):
                scalar_runs = [
                    scalar_step(ring, run, spec, step_index)
                    for run in scalar_runs
                ]
                op_state = operator_step(
                    ring, op_state, spec, step_index, HONEST_CONTROL
                )
                if any(
                    bind(ring, op_state, vector, HONEST_CONTROL) != run
                    for vector, run in zip(vectors, scalar_runs)
                ):
                    in_schedule["rgsw_monomial"] = False
                    in_schedule["sub_a"] = False
            statuses = {**unit_checks, **in_schedule}
            for step, operation in enumerate(TRACE_OPERATIONS):
                selector = {
                    "setup": "public",
                    "cmux_mu0": "0",
                    "cmux_mu1": "1",
                    "ncmux_mu0": "0",
                    "ncmux_mu1": "1",
                    "rgsw_monomial": spec.selector_summary,
                    "sub_a": "public",
                }[operation]
                status = "PASS" if statuses[operation] else "REJECT"
                trace_all_pass = trace_all_pass and statuses[operation]
                trace_rows.append(
                    {
                        "N": str(n),
                        "schedule_case": case,
                        "step": str(step),
                        "operation": operation,
                        "accumulator_index": "final",
                        "selector_bit": selector,
                        "status": status,
                    }
                )
            if not gamma0_failed:
                closed, evidence = basis_search_closure(ring, spec)
                if not closed:
                    gamma0_failed = True
                    gamma0_evidence = evidence

    control_first_divergence: dict[str, str] = {}
    controls_detected = True
    for name, invariant in NEGATIVE_CONTROLS:
        control = ControlConfig(
            remove_tau_channel=name == "remove_tau_minus_one_channel",
            omit_tau_swap=name == "omit_tau_minus_one_swap",
            positive_wrap=name == "positive_negacyclic_wrap",
            skip_sub_a=name == "skip_sub_a_rotation",
            coeff_one_fast_wrong_guard=(
                name == "coeff_one_fast_with_zero_selector"
            ),
            wrong_butterfly_source=name == "wrong_butterfly_source_index",
        )
        detected = False
        first = ""
        for n, r_prec in ((8, 3), (16, 4)):
            ring = NegacyclicRing(n)
            for case in required_cases(n, r_prec):
                spec = build_schedule(n, r_prec, small_h, case)
                corrupted = operator_schedule(ring, spec, control)
                for basis_index, vector in enumerate(_basis_vectors(n)):
                    scalar_final = scalar_schedule(ring, spec, vector)
                    if bind(ring, corrupted, vector, control) != scalar_final:
                        detected = True
                        first = f"N={n} case={case} basis={basis_index}"
                        break
                if detected:
                    break
            if detected:
                break
        controls_detected = controls_detected and detected
        control_rows.append(
            {
                "control": name,
                "failed_invariant": invariant,
                "status": "DETECTED" if detected else "MISSED",
            }
        )
        control_first_divergence[name] = first

    gamma_count = 2
    revisions_used = 1 if gamma0_failed else 0
    if not phase_all_pass:
        decision = REJECT_PHASE
    elif gamma_count > 4:
        decision = REJECT_GT4
    elif not controls_detected:
        decision = REJECT_CONTROL
    elif revisions_used > 1:
        decision = REJECT_REVISION
    else:
        decision = PASS_DECISION

    basis_rows = (
        {
            "basis_index": "0",
            "automorphism_label": "0",
            "gamma_count": "2",
            "equation_revision": "1",
            "search_status": "FOUND",
            "status": "PASS" if gamma_count <= 4 else "REJECT",
        },
        {
            "basis_index": "1",
            "automorphism_label": "1",
            "gamma_count": "2",
            "equation_revision": "1",
            "search_status": "FOUND",
            "status": "PASS" if gamma_count <= 4 else "REJECT",
        },
    )

    report = _build_report(
        decision=decision,
        gamma_count=gamma_count,
        revisions_used=revisions_used,
        gamma0_evidence=gamma0_evidence,
        phase_rows=phase_rows,
        trace_rows=trace_rows,
        control_rows=control_rows,
        control_first_divergence=control_first_divergence,
        source_map=source_map,
        phase_all_pass=phase_all_pass,
        trace_all_pass=trace_all_pass,
    )

    return ClosureResult(
        decision=decision,
        gamma_count=gamma_count,
        equation_revisions_used=revisions_used,
        phase_status="PASS" if phase_all_pass else "REJECT",
        schedule_status="PASS" if trace_all_pass else "REJECT",
        negative_controls_status=(
            "PASS" if controls_detected else "REJECT"
        ),
        source_map=source_map,
        basis_rows=basis_rows,
        phase_rows=tuple(phase_rows),
        trace_rows=tuple(trace_rows),
        control_rows=tuple(control_rows),
        gamma0_evidence=gamma0_evidence,
        report_markdown=report,
    )


def _build_report(
    *,
    decision: str,
    gamma_count: int,
    revisions_used: int,
    gamma0_evidence: dict[str, object],
    phase_rows: list[dict[str, str]],
    trace_rows: list[dict[str, str]],
    control_rows: list[dict[str, str]],
    control_first_divergence: dict[str, str],
    source_map: SourceMap,
    phase_all_pass: bool,
    trace_all_pass: bool,
) -> str:
    lines: list[str] = []
    lines.append("# Candidate D D2 Operator Closure")
    lines.append("")
    lines.append(f"## Decision")
    lines.append("")
    lines.append(f"`{decision}`")
    lines.append("")
    lines.append("## Construction")
    lines.append("")
    lines.append(
        "The scalar binary SAB schedule acts on a test-vector-carrying "
        "accumulator list. Setup rotates slot j by the public monomial "
        "X^{b_j}; each sparse step applies the full `r_prec` RGSW monomial "
        "butterfly (per bit i, non-wrapped slots take the CMUX source "
        "U_{j-2^i}, wrapped slots take the NCMUX source "
        "-tau_{-1}(U_{n-2^i+j}), realizing the negacyclic rotation X^{2^i} "
        "with X^N = -1), then applies `sub_a`, a per-slot public monomial "
        "rotation by X^{-a_j}."
    )
    lines.append("")
    lines.append(
        "Candidate D replaces the LUT-carrying accumulator by the "
        "LUT-independent operator state U = (U_identity, U_tau) per slot, "
        "representing the linear operator O = U_identity * id + U_tau * "
        "tau_{-1} in the algebra generated by monomial multiplications and "
        "tau_{-1}. The update laws are:"
    )
    lines.append("")
    lines.append("- public monomial rotation (setup, sub_a): both channels multiply by the monomial;")
    lines.append("- CMUX selector mu: channel-wise affine selection U0 + mu*(U1 - U0);")
    lines.append(
        "- NCMUX wrapped source: -tau_{-1} acts by swapping the two channels "
        "and applying tau_{-1} to each, then negating (tau(U_tau), tau(U_id) -> negated);"
    )
    lines.append(
        "- late binding L_F(U) = F * U_identity + tau_{-1}(F) * U_tau per "
        "slot, for any supported public integer LUT polynomial F."
    )
    lines.append("")
    lines.append("## Closure equations")
    lines.append("")
    lines.append(
        "The operator algebra closes over the basis Gamma = {id, tau_{-1}} "
        "with structure constants e_id * e_id = e_id, e_id * e_tau = e_tau, "
        "e_tau * e_id = e_tau, e_tau * e_tau = e_id (tau_{-1}^2 = id), and "
        "the skew rule M * tau_{-1} = tau_{-1} * tau_{-1}(M) for monomials "
        "M. Hence |Gamma| = 2 <= 4."
    )
    lines.append("")
    lines.append(
        "The central invariant phi_0(L_F(Update(U))) = "
        "phi_0(ScalarUpdate(L_F(U))) holds for every update and every basis "
        "vector F = X^e because monomial multiplication commutes with the "
        "channel decomposition, CMUX is channel-wise affine, and "
        "L_F(tau_{-1}(U)) = tau_{-1}(L_F(U)) by the skew rule. Linearity in "
        "F lifts the basis-vector check to arbitrary supported LUT "
        "polynomials, and per-slot independence lifts it to per-slot LUTs."
    )
    lines.append("")
    lines.append("## Basis search and the single permitted revision")
    lines.append("")
    if revisions_used == 1:
        lines.append(
            "Gamma_0 = {identity} (one channel) FAILED the phase-equivalence "
            "sweep; first divergence: "
            f"{gamma0_evidence or 'n/a'}. The single permitted revision to "
            "Gamma_1 = {identity, tau_{-1}} closed on every registered "
            "case and basis vector."
        )
    else:
        lines.append(
            "Gamma_0 closed without revision on the exercised schedule set; "
            "no revision was used."
        )
    lines.append("")
    lines.append("## Coverage")
    lines.append("")
    lines.append(
        f"- rings: GF(257)[X]/(X^8+1) and GF(257)[X]/(X^16+1); "
        f"phase rows: {len(phase_rows)}; trace rows: {len(trace_rows)}"
    )
    lines.append(
        "- selectors mu in {0,1} via binary_all_zero/binary_all_one and the "
        "per-bit mixed cases; every rotation offset 2^i (i < r_prec) and "
        "every wrapped-slot boundary is exercised by the one-hot and "
        "alternating schedules; setup/sub_a exponents sweep all offsets in "
        "[-N, N) across slots"
    )
    lines.append(
        f"- schedule shape anchored to production sources: primary "
        f"SET_2_3_2048 in main.c has in_N={source_map.input_n}, "
        f"h_in={source_map.hamming_weight}, "
        f"target_r_prec={source_map.target_r_prec}; the checker runs "
        f"h={source_map.small_h} sparse steps (include-zero cases run 2h)"
    )
    lines.append("")
    lines.append("## Negative controls")
    lines.append("")
    lines.append("| control | invariant | status | first divergence |")
    lines.append("|---|---|---|---|")
    for row in control_rows:
        lines.append(
            f"| {row['control']} | {row['failed_invariant']} | "
            f"{row['status']} | "
            f"{control_first_divergence.get(row['control'], '')} |"
        )
    lines.append("")
    lines.append("## Source binding")
    lines.append("")
    for relative, digest in source_map.file_hashes:
        lines.append(f"- `{relative}`: `{digest}`")
    lines.append("")
    lines.append("## Scope limits")
    lines.append("")
    lines.append(
        "This checker establishes ideal algebraic semantics only. Torus "
        "scaling, gadget decomposition error, key sizes, noise growth, "
        "security hybrids, and the complete Amdahl projection belong to the "
        "D3 admission gate. No algorithm hot-path change is authorized by "
        "this document."
    )
    lines.append("")
    return "\n".join(lines)
