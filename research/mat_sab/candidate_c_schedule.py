"""Source-derived finite schedule replay metadata for Candidate C.

This module records finite-field mechanism evidence only. It does not claim
polynomial-module correctness, security, noise, performance, or a production
bootstrapping construction.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, replace
from pathlib import Path

from .rank_bounded_state_model import (
    append_mask_directions,
    compress_state,
    excess_rank,
    lane_difference_matrix,
    linear_combine_states,
    phase_vector,
    rotate_state,
    shared_state,
)


class ScheduleInconclusiveError(ValueError):
    """Raised when the audited C source no longer has the required shape."""


@dataclass(frozen=True)
class BinaryTargetSchedule:
    target: str
    h: int
    r_prec: int
    in_N: int
    monomial_calls: int
    butterfly_steps: int
    selector_applications: int
    source_anchors: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class ScheduleTrace:
    variant: str
    r: int
    modulus: int
    rho_bound: int
    max_rho: int
    first_rank_overflow: int | None
    first_missing_edge: str | None
    steps_before_compression: int | None
    compressions: int
    completed_butterflies: int
    selector_applications: int
    selector_boundaries_checked: int
    monomial_boundaries_checked: int
    sub_a_boundaries_checked: int
    phase_gate: str
    closure_gate: str
    boundary_gate: str
    provenance_gate: str


@dataclass(frozen=True)
class _CycleEdge:
    row: int
    column: int

    @property
    def label(self) -> str:
        return (
            "lane_neighbor_body_interaction:"
            f"row={self.row},col={self.column}"
        )


_SOURCE_ANCHORS = (
    ("main.c", "sab_pvw_target_params"),
    ("src/sparse_amortized_bootstrap.c", "RGSW_monomial_mul"),
    ("src/sparse_amortized_bootstrap.c", "sparse_mul"),
    ("src/sab_pvw.c", "sab_pvw_RGSW_monomial_mul_state"),
    ("src/sab_pvw.c", "sab_pvw_sparse_mul_binary"),
    ("src/sab_pvw.c", "sab_pvw_sub_a_binary_to"),
)


def _read_source(root: Path, relative_path: str) -> str:
    path = root / relative_path
    try:
        return path.read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeError) as error:
        raise ScheduleInconclusiveError(
            f"cannot read required source {relative_path}: {error}"
        ) from error


def _split_initializer(initializer: str) -> tuple[str, ...]:
    values: list[str] = []
    start = 0
    depth = 0
    for index, character in enumerate(initializer):
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth < 0:
                raise ScheduleInconclusiveError(
                    "unbalanced target initializer parentheses"
                )
        elif character == "," and depth == 0:
            values.append(initializer[start:index].strip())
            start = index + 1
    if depth != 0:
        raise ScheduleInconclusiveError(
            "unbalanced target initializer parentheses"
        )
    values.append(initializer[start:].strip())
    if any(not value for value in values):
        raise ScheduleInconclusiveError("empty target initializer value")
    return tuple(values)


def _parse_default_target(source: str) -> dict[str, str]:
    declaration = re.search(
        r"typedef\s+struct\s*\{(?P<body>.*?)\}"
        r"\s*SAB_PVW_Target_Params\s*;",
        source,
        flags=re.DOTALL,
    )
    if declaration is None:
        raise ScheduleInconclusiveError(
            "SAB_PVW_Target_Params declaration not found"
        )
    fields = re.findall(
        r"^\s*(?:int|double)\s+([A-Za-z_][A-Za-z0-9_]*)\s*;\s*$",
        declaration.group("body"),
        flags=re.MULTILINE,
    )
    if not fields or len(fields) != len(set(fields)):
        raise ScheduleInconclusiveError(
            "SAB_PVW_Target_Params fields are missing or duplicated"
        )

    function = _extract_function(
        source,
        "static SAB_PVW_Target_Params sab_pvw_target_params(void)",
    )
    initializer = re.search(
        r"#else\s*return\s*\(SAB_PVW_Target_Params\)\s*"
        r"\{(?P<values>.*?)\}\s*;\s*#endif",
        function,
        flags=re.DOTALL,
    )
    if initializer is None:
        raise ScheduleInconclusiveError(
            "default SAB_PVW_Target_Params initializer not found"
        )
    values = _split_initializer(initializer.group("values"))
    if len(fields) != len(values):
        raise ScheduleInconclusiveError(
            "SAB_PVW_Target_Params field/initializer length mismatch"
        )
    return dict(zip(fields, values, strict=True))


def _extract_function(source: str, signature: str) -> str:
    start = source.find(signature)
    if start < 0:
        raise ScheduleInconclusiveError(
            f"required source function {signature.split('(')[0]} not found"
        )
    opening = source.find("{", start + len(signature))
    if opening < 0:
        raise ScheduleInconclusiveError(
            f"required source function {signature.split('(')[0]} has no body"
        )
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise ScheduleInconclusiveError(
        f"required source function {signature.split('(')[0]} is unbalanced"
    )


def _require_tokens(body: str, label: str, tokens: tuple[str, ...]) -> None:
    missing = tuple(token for token in tokens if token not in body)
    if missing:
        raise ScheduleInconclusiveError(
            f"{label} source shape changed; missing {missing[0]!r}"
        )


def _validate_scalar_schedule(source: str) -> None:
    monomial = _extract_function(
        source,
        "void RGSW_monomial_mul(",
    )
    _require_tokens(
        monomial,
        "RGSW_monomial_mul",
        (
            "const uint32_t r_prec = sab->r_prec, in_N = sab->in_N;",
            "for (size_t i = 0; i < r_prec; i++){",
            "const uint64_t power = 1ULL << i;",
            "for (size_t j = 0; j < power; j++){",
            "NCMUX(",
            "for (size_t j = 0; j < in_N - power; j++){",
            "CMUX(",
        ),
    )
    sparse = _extract_function(source, "void sparse_mul(")
    _require_tokens(
        sparse,
        "sparse_mul",
        (
            "for (size_t i = 0; i < sab->h; i++){",
            "RGSW_monomial_mul(p, sab->s[a_idx][i], sab);",
            "sub_a(p, a, i, sab);",
            "RGSW_monomial_mul(p, sab->s[a_idx][sab->h], sab);",
        ),
    )


def _validate_pvw_schedule(source: str) -> None:
    monomial = _extract_function(
        source,
        "static uint64_t sab_pvw_RGSW_monomial_mul_state(",
    )
    _require_tokens(
        monomial,
        "sab_pvw_RGSW_monomial_mul_state",
        (
            "const uint32_t r_prec = sab->r_prec, in_N = sab->in_N;",
            "for (size_t bit = 0; bit < r_prec; bit++){",
            "const uint64_t power = 1ULL << bit;",
            "if(2 * power <= in_N){",
            "sab_pvw_schedule_dual_sub_pair(",
            "direct_start = power;",
            "for (size_t j = 0; j < power; j++){",
            "sab_pvw_schedule_NCMUX(",
            "sab_pvw_NCMUX(",
            "for (size_t j = direct_start; j < in_N - power; j++){",
            "sab_pvw_schedule_CMUX(",
            "sab_pvw_CMUX(",
        ),
    )
    dual_pair = _extract_function(
        source,
        "static void sab_pvw_schedule_dual_sub_pair(",
    )
    if dual_pair.count("sab_pvw_CMUX_from_sub_internal(") != 2:
        raise ScheduleInconclusiveError(
            "sab_pvw_schedule_dual_sub_pair source shape changed; "
            "expected two selector applications"
        )
    sparse = _extract_function(source, "void sab_pvw_sparse_mul_binary(")
    _require_tokens(
        sparse,
        "sab_pvw_sparse_mul_binary",
        (
            "for (size_t step = 0; step < sab->h; step++){",
            "sab_pvw_RGSW_monomial_mul_state(",
            "sab_pvw_sub_a_binary_to(",
            "sab_pvw_sub_a_binary(",
            "sab->s[a_idx][sab->h]",
        ),
    )
    sub_a = _extract_function(
        source,
        "static void sab_pvw_sub_a_binary_to(",
    )
    _require_tokens(
        sub_a,
        "sab_pvw_sub_a_binary_to",
        (
            "for (size_t idx = 0; idx < sab->in_N; idx++){",
            "pvmtmlwe_mul_by_xai(out[idx], in[idx], a[idx]);",
        ),
    )


def _parse_int(target: dict[str, str], field: str) -> int:
    value = target.get(field)
    if value is None or re.fullmatch(r"(?:0[xX][0-9a-fA-F]+|\d+)", value) is None:
        raise ScheduleInconclusiveError(
            f"default target field {field} is not an integer literal"
        )
    return int(value, 0)


def load_binary_target_schedule(root: Path | str) -> BinaryTargetSchedule:
    """Parse the default target and exact binary SAB schedule source shape."""

    root_path = Path(root)
    main_source = _read_source(root_path, "main.c")
    scalar_source = _read_source(
        root_path,
        "src/sparse_amortized_bootstrap.c",
    )
    pvw_source = _read_source(root_path, "src/sab_pvw.c")

    target = _parse_default_target(main_source)
    _validate_scalar_schedule(scalar_source)
    _validate_pvw_schedule(pvw_source)

    h = _parse_int(target, "h")
    r_prec = _parse_int(target, "r_prec")
    in_N = _parse_int(target, "in_N")
    if min(h, r_prec, in_N) <= 0:
        raise ScheduleInconclusiveError(
            "default binary target dimensions must be positive"
        )

    monomial_calls = h + 1
    butterfly_steps = monomial_calls * r_prec
    selector_applications = butterfly_steps * in_N
    return BinaryTargetSchedule(
        target="SET_2_3_2048",
        h=h,
        r_prec=r_prec,
        in_N=in_N,
        monomial_calls=monomial_calls,
        butterfly_steps=butterfly_steps,
        selector_applications=selector_applications,
        source_anchors=_SOURCE_ANCHORS,
    )


def _default_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_cycle_edges(root: Path, r: int) -> tuple[_CycleEdge, ...]:
    relative_path = (
        "repro/stage203_production_selector_equation_probe/"
        "equation_map.csv"
    )
    source = _read_source(root, relative_path)
    reader = csv.DictReader(source.splitlines())
    expected_fields = [
        "r",
        "row",
        "col",
        "equation_class",
        "semantic_role",
        "is_public_row",
        "may_skip_after_proof",
    ]
    if reader.fieldnames != expected_fields:
        raise ScheduleInconclusiveError(
            "Stage203 equation map header changed"
        )
    try:
        selected = [
            row
            for row in reader
            if int(row["r"]) == r
        ]
    except (KeyError, TypeError, ValueError) as error:
        raise ScheduleInconclusiveError(
            "Stage203 equation map contains malformed rows"
        ) from error
    if len(selected) != (r + 1) ** 2:
        raise ScheduleInconclusiveError(
            f"Stage203 r={r} equation map shape changed"
        )

    neighbors = [
        row
        for row in selected
        if row["equation_class"] == "lane_neighbor_body_interaction"
    ]
    edges: list[_CycleEdge] = []
    for row in neighbors:
        try:
            source_lane = int(row["row"])
            target_lane = int(row["col"])
        except (TypeError, ValueError) as error:
            raise ScheduleInconclusiveError(
                "Stage203 neighbor edge is malformed"
            ) from error
        if (
            not 1 <= source_lane <= r
            or target_lane != 1 + (source_lane % r)
            or row["semantic_role"] != "active"
            or row["is_public_row"] != "1"
            or row["may_skip_after_proof"] != "0"
        ):
            raise ScheduleInconclusiveError(
                f"Stage203 r={r} cycle edge shape changed"
            )
        edges.append(_CycleEdge(source_lane, target_lane))
    if len(edges) != r or [edge.row for edge in edges] != list(
        range(1, r + 1)
    ):
        raise ScheduleInconclusiveError(
            f"Stage203 r={r} cycle is incomplete"
        )
    return tuple(edges)


def _cycle_direction_matrix(
    edges: tuple[_CycleEdge, ...],
    r: int,
    modulus: int,
) -> tuple[tuple[int, ...], ...]:
    columns: list[tuple[int, ...]] = []
    for edge in edges:
        raw = [
            (
                (1 if lane == edge.row - 1 else 0)
                - (1 if lane == edge.column - 1 else 0)
            )
            % modulus
            for lane in range(r)
        ]
        reference = raw[0]
        columns.append(
            tuple((value - reference) % modulus for value in raw)
        )
    return tuple(
        tuple(columns[column][lane] for column in range(len(columns)))
        for lane in range(r)
    )


def _cycle_rank(
    edges: tuple[_CycleEdge, ...],
    r: int,
    modulus: int,
) -> int:
    state = append_mask_directions(
        shared_state(r, modulus),
        _cycle_direction_matrix(edges, r, modulus),
    )
    return excess_rank(state)


def _replay_c1(
    r: int,
    modulus: int,
    root: Path,
    schedule: BinaryTargetSchedule,
) -> ScheduleTrace:
    edges = _load_cycle_edges(root, r)
    observed_rho = _cycle_rank(edges, r, modulus)
    rho_bound = min(2, r - 1)
    missing_edge = None
    for length in range(1, len(edges) + 1):
        if _cycle_rank(edges[:length], r, modulus) > rho_bound:
            missing_edge = edges[length - 1]
            break

    closure_gate = (
        "PASS_FINITE_CLOSURE"
        if missing_edge is None
        else "FAIL_MINIMUM_CYCLE_RANK"
    )
    if missing_edge is None:
        state = append_mask_directions(
            shared_state(r, modulus),
            _cycle_direction_matrix(edges, r, modulus),
        )
        for exponent in range(1, schedule.h + 1):
            rotated = rotate_state(state, exponent)
            if excess_rank(rotated) != observed_rho:
                raise AssertionError("public sub_a rotation changed rho")
            state = rotated
    return ScheduleTrace(
        variant="C1",
        r=r,
        modulus=modulus,
        rho_bound=rho_bound,
        max_rho=observed_rho,
        first_rank_overflow=None if missing_edge is None else 1,
        first_missing_edge=(
            None
            if missing_edge is None
            else (
                f"{missing_edge.label};"
                "butterfly=NCMUX:bit=0,j=0"
            )
        ),
        steps_before_compression=None,
        compressions=0,
        completed_butterflies=(
            schedule.selector_applications
            if missing_edge is None
            else 0
        ),
        selector_applications=schedule.selector_applications,
        selector_boundaries_checked=(
            schedule.selector_applications
            if missing_edge is None
            else 1
        ),
        monomial_boundaries_checked=(
            schedule.monomial_calls if missing_edge is None else 0
        ),
        sub_a_boundaries_checked=(
            schedule.h if missing_edge is None else 0
        ),
        phase_gate="INCONCLUSIVE_MISSING_OPERATOR_MAPPING",
        closure_gate=closure_gate,
        boundary_gate="NOT_APPLICABLE",
        provenance_gate="PASS",
    )


_C2_BLOCK_LENGTHS = frozenset((1, 2, 4, 8, 16, 32, 64))


def _replay_c2(
    r: int,
    modulus: int,
    root: Path,
    schedule: BinaryTargetSchedule,
    block_length: int | None,
) -> ScheduleTrace:
    if (
        type(block_length) is not int
        or block_length not in _C2_BLOCK_LENGTHS
    ):
        raise ValueError(
            "C2 block length must be one of 1, 2, 4, 8, 16, 32, 64"
        )

    edges = _load_cycle_edges(root, r)
    directions = _cycle_direction_matrix(edges, r, modulus)
    state = shared_state(r, modulus)
    for _ in range(block_length):
        state = append_mask_directions(state, directions)

    observed_rho = excess_rank(state)
    rho_bound = min(2, r - 1)
    first_overflow = 1 if observed_rho > rho_bound else None
    missing_edge = None
    if first_overflow is not None:
        for length in range(1, len(edges) + 1):
            if _cycle_rank(edges[:length], r, modulus) > rho_bound:
                missing_edge = edges[length - 1]
                break

    differences = lane_difference_matrix(state)
    projection = tuple(differences[:rho_bound])
    compression_preserved = False
    try:
        before = phase_vector(
            state,
            tuple(range(2, r + 2)),
            modulus,
        )
        result = compress_state(state, projection)
        after = phase_vector(
            result.compressed_state,
            tuple(range(2, r + 2)),
            modulus,
        )
        compression_preserved = result.phase_preserved and before == after
        if compression_preserved:
            rotated = result.compressed_state
            for exponent in range(1, schedule.h + 1):
                rotated = rotate_state(rotated, exponent)
                if excess_rank(rotated) != observed_rho:
                    raise AssertionError(
                        "public sub_a rotation changed compressed rho"
                    )
    except ValueError as error:
        if "phase-active direction" not in str(error):
            raise

    if block_length == 1:
        boundary_gate = "REJECT_PER_CMUX_CONTROL"
        closure_gate = "REJECT_FORBIDDEN_BOUNDARY"
        compressions = 1
        completed = 1
    elif observed_rho <= rho_bound and compression_preserved:
        boundary_gate = "PASS"
        closure_gate = "PASS_FINITE_CLOSURE"
        compressions = (
            schedule.selector_applications + block_length - 1
        ) // block_length
        completed = schedule.selector_applications
    else:
        boundary_gate = "PASS"
        closure_gate = "FAIL_MINIMUM_CYCLE_RANK"
        compressions = 1
        completed = block_length

    return ScheduleTrace(
        variant="C2",
        r=r,
        modulus=modulus,
        rho_bound=rho_bound,
        max_rho=observed_rho,
        first_rank_overflow=first_overflow,
        first_missing_edge=(
            None
            if missing_edge is None
            else (
                f"{missing_edge.label};"
                "butterfly=NCMUX:bit=0,j=0"
            )
        ),
        steps_before_compression=block_length,
        compressions=compressions,
        completed_butterflies=completed,
        selector_applications=schedule.selector_applications,
        selector_boundaries_checked=completed,
        monomial_boundaries_checked=(
            schedule.monomial_calls
            if completed == schedule.selector_applications
            else 0
        ),
        sub_a_boundaries_checked=(
            schedule.h
            if completed == schedule.selector_applications
            else 0
        ),
        phase_gate="INCONCLUSIVE_MISSING_OPERATOR_MAPPING",
        closure_gate=closure_gate,
        boundary_gate=boundary_gate,
        provenance_gate="PASS",
    )


def _cycle_coefficient_mutation_detected(
    root: Path,
    r: int,
    modulus: int,
) -> bool:
    edges = _load_cycle_edges(root, r)
    expected = _cycle_direction_matrix(edges, r, modulus)
    mutated = [list(row) for row in expected]
    mutated[1][0] = (mutated[1][0] + 1) % modulus
    return tuple(tuple(row) for row in mutated) != expected


def _provenance_mutation_rejected(
    root: Path,
    r: int,
    modulus: int,
) -> bool:
    edge = _load_cycle_edges(root, r)[:1]
    directions = _cycle_direction_matrix(edge, r, modulus)
    lhs = append_mask_directions(shared_state(r, modulus), directions)
    rhs = append_mask_directions(shared_state(r, modulus), directions)
    mutated_rhs = replace(rhs, provenance=lhs.provenance)
    try:
        linear_combine_states(lhs, mutated_rhs, 1, 1)
    except ValueError as error:
        return "independent provenance" in str(error)
    return False


def _apply_mutation(
    trace: ScheduleTrace,
    mutation: str | None,
    root: Path,
    block_length: int | None,
) -> ScheduleTrace:
    if mutation is None:
        return trace
    if mutation == "cycle_coefficient":
        if not _cycle_coefficient_mutation_detected(
            root,
            trace.r,
            trace.modulus,
        ):
            raise AssertionError("cycle coefficient mutation was ineffective")
        first_edge = _load_cycle_edges(root, trace.r)[0]
        return replace(
            trace,
            first_missing_edge=(
                f"{first_edge.label};mutation=cycle_coefficient"
            ),
            completed_butterflies=0,
            closure_gate="FAIL_CYCLE_COEFFICIENT",
        )
    if mutation == "compression_boundary":
        if trace.variant != "C2" or block_length is None:
            raise ValueError(
                "compression boundary mutation requires C2 block length"
            )
        mutated_boundary = (
            block_length - 1 if block_length > 1 else block_length + 1
        )
        if mutated_boundary == block_length:
            raise AssertionError("compression boundary mutation was ineffective")
        return replace(
            trace,
            steps_before_compression=mutated_boundary,
            compressions=0,
            completed_butterflies=mutated_boundary,
            selector_boundaries_checked=mutated_boundary,
            monomial_boundaries_checked=0,
            sub_a_boundaries_checked=0,
            closure_gate="INCONCLUSIVE_AFTER_BOUNDARY_FAILURE",
            boundary_gate="FAIL_MUTATED_COMPRESSION_BOUNDARY",
        )
    if mutation == "provenance_identifier":
        if not _provenance_mutation_rejected(
            root,
            trace.r,
            trace.modulus,
        ):
            raise AssertionError("provenance mutation was not rejected")
        return replace(
            trace,
            phase_gate="FAIL_PROVENANCE_IDENTITY",
            closure_gate="INCONCLUSIVE_AFTER_PROVENANCE_FAILURE",
            provenance_gate="FAIL_MUTATED_PROVENANCE",
        )
    raise ValueError(f"unknown schedule mutation: {mutation!r}")


def replay_variant_schedule(
    variant: str,
    r: int,
    modulus: int,
    *,
    root: Path | str | None = None,
    block_length: int | None = None,
    mutation: str | None = None,
) -> ScheduleTrace:
    """Replay one registered finite variant over the source-derived schedule."""

    root_path = _default_root() if root is None else Path(root)
    schedule = load_binary_target_schedule(root_path)
    if variant == "C1":
        return _apply_mutation(
            _replay_c1(r, modulus, root_path, schedule),
            mutation,
            root_path,
            block_length,
        )
    if variant == "C2":
        return _apply_mutation(
            _replay_c2(
                r,
                modulus,
                root_path,
                schedule,
                block_length,
            ),
            mutation,
            root_path,
            block_length,
        )
    if variant != "C0":
        raise ValueError(f"unknown Candidate C schedule variant: {variant!r}")

    state = shared_state(r, modulus)
    independent = tuple(
        tuple(
            1 if lane == column + 1 else 0
            for column in range(r - 1)
        )
        for lane in range(r)
    )
    state = append_mask_directions(state, independent)
    observed_rho = excess_rank(state)
    rho_bound = min(2, r - 1)
    trace = ScheduleTrace(
        variant=variant,
        r=r,
        modulus=modulus,
        rho_bound=rho_bound,
        max_rho=observed_rho,
        first_rank_overflow=1 if observed_rho > rho_bound else None,
        first_missing_edge=None,
        steps_before_compression=None,
        compressions=0,
        completed_butterflies=1,
        selector_applications=schedule.selector_applications,
        selector_boundaries_checked=1,
        monomial_boundaries_checked=0,
        sub_a_boundaries_checked=0,
        phase_gate="NOT_APPLICABLE_NEGATIVE_CONTROL",
        closure_gate="REJECT_EXPECTED",
        boundary_gate="NOT_APPLICABLE",
        provenance_gate="PASS",
    )
    return _apply_mutation(
        trace,
        mutation,
        root_path,
        block_length,
    )
