"""Exact source-derived SAB schedule events for the Candidate C gate.

Candidate C has no registered numeric compact-operator or public-lambda
mapping. The replay can therefore decide source structure, schedule counts,
explicit controls, and public boundary policy only. Candidate rank, closure,
phase, and compression admissibility remain inconclusive.
"""

from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterator

from .rank_bounded_state_model import (
    append_mask_directions,
    excess_rank,
    linear_combine_states,
    shared_state,
)


INCONCLUSIVE_OPERATOR = (
    "INCONCLUSIVE_MISSING_NUMERIC_OPERATOR_MAPPING"
)
_C2_BLOCK_LENGTHS = frozenset((1, 2, 4, 8, 16, 32, 64))
_SELECTOR_KINDS = frozenset(("ncmux", "cmux"))
_STAGE203_SUPPORT_FIELDS = (
    "r",
    "row",
    "col",
    "equation_class",
    "semantic_role",
    "is_public_row",
    "may_skip_after_proof",
)
_UNREGISTERED_NUMERIC_EVIDENCE = (
    "REJECT_UNREGISTERED_NUMERIC_EVIDENCE_SCHEMA"
)


class ScheduleInconclusiveError(ValueError):
    """Raised when audited source no longer has the required structure."""


@dataclass(frozen=True)
class BinaryTargetSchedule:
    target: str
    h: int
    r_prec: int
    in_N: int
    monomial_calls: int
    butterfly_steps: int
    selector_applications: int
    dual_sub_enabled: bool
    source_anchors: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class ScheduleEvent:
    kind: str
    monomial: int
    bit: int | None = None
    index: int | None = None
    branch: str = "schedule"


@dataclass(frozen=True)
class ScheduleTrace:
    variant: str
    r: int
    modulus: int
    rho_bound: int
    max_rho: int | None
    first_rank_overflow: int | None
    first_missing_edge: str | None
    steps_before_compression: int | None
    compressions: int
    compression_boundaries_checked: int
    first_boundary_mismatch: int | None
    completed_butterflies: int
    selector_applications: int
    selector_boundaries_checked: int
    ncmux_events_checked: int
    cmux_events_checked: int
    butterfly_boundaries_checked: int
    monomial_boundaries_checked: int
    sub_a_boundaries_checked: int
    events_traversed: int
    phase_gate: str
    closure_gate: str
    boundary_gate: str
    provenance_gate: str
    operator_mapping_gate: str


@dataclass(frozen=True)
class _CBlock:
    start: int
    opening: int
    end: int
    body: str


@dataclass(frozen=True)
class _Stage203Evidence:
    fields: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


@dataclass
class _ReplayCounts:
    events: int = 0
    selectors: int = 0
    ncmux: int = 0
    cmux: int = 0
    butterflies: int = 0
    monomials: int = 0
    sub_a: int = 0
    compression_boundaries: int = 0
    first_boundary_mismatch: int | None = None
    first_actual_boundary: int | None = None
    provenance_gate: str = INCONCLUSIVE_OPERATOR


_SOURCE_ANCHORS = (
    ("main.c", "sab_pvw_target_params"),
    ("src/sparse_amortized_bootstrap.c", "RGSW_monomial_mul"),
    ("src/sparse_amortized_bootstrap.c", "sparse_mul"),
    ("src/sab_pvw.c", "sab_pvw_RGSW_monomial_mul_state"),
    ("src/sab_pvw.c", "sab_pvw_sparse_mul_binary"),
    ("src/sab_pvw.c", "sab_pvw_sub_a_binary_to"),
    ("src/mosfhet/Makefile.def", "SAB_PVW_DUAL_SUB_CMUX"),
)

_EXPECTED_FUNCTION_TOKEN_DIGESTS = {
    (
        "src/sparse_amortized_bootstrap.c",
        "void RGSW_monomial_mul(",
    ): "e0cd91bf3d7d790e6b8ce1477f4f144d46039d3fe8a94a28e9324b68e5263aa3",
    (
        "src/sparse_amortized_bootstrap.c",
        "void sparse_mul(",
    ): "8e80845ce907cb0be7c1e7a7d60ce0fee1237005417c32ec9bdf7454e8b65a8e",
    (
        "src/sab_pvw.c",
        "static void sab_pvw_schedule_dual_sub_pair(",
    ): "40eee548c273a88518fef1becfa5fa9e36061fe141f4824f7610825c42900d8b",
    (
        "src/sab_pvw.c",
        "static uint64_t sab_pvw_RGSW_monomial_mul_state(",
    ): "a8b68aaee69c0f5043b32ea3b3c537dc511c4b19196494dfa3f0bfb3c2e93b3b",
    (
        "src/sab_pvw.c",
        "void sab_pvw_RGSW_monomial_mul(",
    ): "8c12dab0f90946776fac7380343f1ee0a41fbb83eab5603dd3ece174941fbc45",
    (
        "src/sab_pvw.c",
        "void sab_pvw_sub_a_binary(",
    ): "dea8fe9e6e74ead9f09a22a8612d7773b26dbdd944e95e0443397e43a5aadf90",
    (
        "src/sab_pvw.c",
        "static void sab_pvw_sub_a_binary_to(",
    ): "cb0adcf1e250b908ac7b58a4679ffb5edfb14bd281aecf83b04c7f19e176305a",
    (
        "src/sab_pvw.c",
        "void sab_pvw_sparse_mul_binary(",
    ): "f389252c3ea05c01f689fac1db1939b0ba83b66d7d08c9b23f470984e99408b3",
}

_C_MULTI_CHARACTER_TOKENS = (
    ">>=",
    "<<=",
    "...",
    "->",
    "++",
    "--",
    "<<",
    ">>",
    "<=",
    ">=",
    "==",
    "!=",
    "&&",
    "||",
    "+=",
    "-=",
    "*=",
    "/=",
    "%=",
    "&=",
    "|=",
    "^=",
    "##",
)
_C_NUMBER = re.compile(
    r"(?:0[xX][0-9A-Fa-f]+|"
    r"(?:[0-9]+\.[0-9]*|\.[0-9]+|[0-9]+)"
    r"(?:[eEpP][+-]?[0-9]+)?)[fFlLuU]*"
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


def _sanitize_c(source: str) -> str:
    """Remove comments and literals while preserving offsets and braces."""

    output = list(source)
    state = "code"
    index = 0
    while index < len(source):
        current = source[index]
        following = source[index + 1] if index + 1 < len(source) else ""
        if state == "code":
            if current == "/" and following == "/":
                output[index] = output[index + 1] = " "
                state = "line_comment"
                index += 2
                continue
            if current == "/" and following == "*":
                output[index] = output[index + 1] = " "
                state = "block_comment"
                index += 2
                continue
            if current == '"':
                output[index] = " "
                state = "string"
            elif current == "'":
                output[index] = " "
                state = "character"
        elif state == "line_comment":
            if current == "\n":
                state = "code"
            else:
                output[index] = " "
        elif state == "block_comment":
            if current == "*" and following == "/":
                output[index] = output[index + 1] = " "
                state = "code"
                index += 2
                continue
            if current != "\n":
                output[index] = " "
        elif state in {"string", "character"}:
            quote = '"' if state == "string" else "'"
            if current == "\\" and following:
                output[index] = " "
                if following != "\n":
                    output[index + 1] = " "
                index += 2
                continue
            if current == quote:
                output[index] = " "
                state = "code"
            elif current != "\n":
                output[index] = " "
        index += 1
    if state in {"block_comment", "string", "character"}:
        raise ScheduleInconclusiveError(
            "unterminated C comment or literal in required source"
        )
    return "".join(output)


def _balanced_end(source: str, opening: int, label: str) -> int:
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return index
    raise ScheduleInconclusiveError(f"{label} has unbalanced braces")


def _c_tokens(source: str) -> tuple[str, ...]:
    tokens: list[str] = []
    index = 0
    while index < len(source):
        current = source[index]
        following = source[index + 1] if index + 1 < len(source) else ""
        if current.isspace():
            index += 1
            continue
        if current == "/" and following == "/":
            newline = source.find("\n", index + 2)
            index = len(source) if newline < 0 else newline + 1
            continue
        if current == "/" and following == "*":
            closing = source.find("*/", index + 2)
            if closing < 0:
                raise ScheduleInconclusiveError(
                    "unterminated C comment in required source"
                )
            index = closing + 2
            continue
        if current in {'"', "'"}:
            quote = current
            start = index
            index += 1
            while index < len(source):
                if source[index] == "\\":
                    index += 2
                    continue
                if source[index] == quote:
                    index += 1
                    tokens.append(source[start:index])
                    break
                index += 1
            else:
                raise ScheduleInconclusiveError(
                    "unterminated C literal in required source"
                )
            continue
        identifier = re.match(
            r"[A-Za-z_][A-Za-z0-9_]*",
            source[index:],
        )
        if identifier is not None:
            token = identifier.group(0)
            tokens.append(token)
            index += len(token)
            continue
        number = _C_NUMBER.match(source, index)
        if number is not None:
            tokens.append(number.group(0))
            index = number.end()
            continue
        operator = next(
            (
                candidate
                for candidate in _C_MULTI_CHARACTER_TOKENS
                if source.startswith(candidate, index)
            ),
            None,
        )
        if operator is not None:
            tokens.append(operator)
            index += len(operator)
            continue
        tokens.append(current)
        index += 1
    return tuple(tokens)


def _function_bounds(source: str, signature: str) -> tuple[int, int]:
    sanitized = _sanitize_c(source)
    signature_tokens = _c_tokens(signature)
    pattern = (
        r"(?<![A-Za-z0-9_])"
        + r"\s*".join(
            re.escape(token) for token in signature_tokens
        )
    )
    match = re.search(pattern, sanitized)
    if match is None:
        name = signature.split("(")[0]
        raise ScheduleInconclusiveError(
            f"required source function {name} not found"
        )
    opening = sanitized.find("{", match.end())
    if opening < 0:
        raise ScheduleInconclusiveError(
            f"required source function {signature!r} has no body"
        )
    end = _balanced_end(sanitized, opening, signature)
    return match.start(), end


def _extract_function(source: str, signature: str) -> str:
    sanitized = _sanitize_c(source)
    start, end = _function_bounds(source, signature)
    return sanitized[start : end + 1]


def _extract_raw_function(source: str, signature: str) -> str:
    start, end = _function_bounds(source, signature)
    return source[start : end + 1]


def _function_token_digest(source: str, signature: str) -> str:
    function = _extract_raw_function(source, signature)
    normalized = "\0".join(_c_tokens(function)).encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def _validate_exact_function_bindings(
    sources: dict[str, str],
) -> None:
    for (
        relative_path,
        signature,
    ), expected in _EXPECTED_FUNCTION_TOKEN_DIGESTS.items():
        actual = _function_token_digest(
            sources[relative_path],
            signature,
        )
        if actual != expected:
            function = signature.split("(")[0].split()[-1]
            raise ScheduleInconclusiveError(
                f"{relative_path}:{function} token digest mismatch"
            )


def _find_blocks(
    source: str,
    pattern: str,
    label: str,
) -> tuple[_CBlock, ...]:
    blocks: list[_CBlock] = []
    for match in re.finditer(pattern, source, flags=re.DOTALL):
        opening = source.find("{", match.start(), match.end())
        if opening < 0:
            continue
        end = _balanced_end(source, opening, label)
        blocks.append(
            _CBlock(
                start=match.start(),
                opening=opening,
                end=end,
                body=source[opening + 1 : end],
            )
        )
    return tuple(blocks)


def _one_block(source: str, pattern: str, label: str) -> _CBlock:
    blocks = _find_blocks(source, pattern, label)
    if len(blocks) != 1:
        raise ScheduleInconclusiveError(
            f"{label} source shape changed; expected one nested block"
        )
    return blocks[0]


def _brace_depth_at(source: str, position: int) -> int:
    return source[:position].count("{") - source[:position].count("}")


def _top_level_calls(
    source: str,
    names: tuple[str, ...],
) -> tuple[tuple[int, str], ...]:
    alternatives = "|".join(re.escape(name) for name in names)
    calls: list[tuple[int, str]] = []
    for match in re.finditer(
        rf"\b(?P<name>{alternatives})\s*\(",
        source,
    ):
        if _brace_depth_at(source, match.start()) == 0:
            calls.append((match.start(), match.group("name")))
    return tuple(calls)


def _require_top_level_call(
    block: _CBlock,
    names: tuple[str, ...],
    label: str,
) -> None:
    if not _top_level_calls(block.body, names):
        raise ScheduleInconclusiveError(
            f"{label} source shape changed; call is not nested in loop"
        )


def _require_ordered_calls(
    block: _CBlock,
    first: tuple[str, ...],
    second: tuple[str, ...],
    label: str,
) -> None:
    first_calls = _top_level_calls(block.body, first)
    second_calls = _top_level_calls(block.body, second)
    if (
        not first_calls
        or not second_calls
        or first_calls[0][0] >= second_calls[0][0]
    ):
        raise ScheduleInconclusiveError(
            f"{label} must contain ordered monomial/sub_a calls"
        )


def _require_call_after(
    source: str,
    block: _CBlock,
    names: tuple[str, ...],
    limit: int | None,
    label: str,
) -> None:
    tail = source[block.end + 1 : limit]
    if not _top_level_calls(tail, names):
        raise ScheduleInconclusiveError(
            f"{label} final monomial call is not associated with its loop"
        )


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


def _parse_int(target: dict[str, str], field: str) -> int:
    value = target.get(field)
    if (
        value is None
        or re.fullmatch(r"(?:0[xX][0-9a-fA-F]+|\d+)", value) is None
    ):
        raise ScheduleInconclusiveError(
            f"default target field {field} is not an integer literal"
        )
    return int(value, 0)


def _parse_make_default(source: str, name: str) -> bool:
    match = re.search(
        rf"^{re.escape(name)}\s*\?=\s*(true|false)\s*$",
        source,
        flags=re.MULTILINE,
    )
    if match is None:
        raise ScheduleInconclusiveError(
            f"default build flag {name} not found"
        )
    return match.group(1) == "true"


def _validate_scalar_schedule(source: str) -> None:
    monomial = _extract_function(source, "void RGSW_monomial_mul(")
    bit_loop = _one_block(
        monomial,
        r"for\s*\(\s*size_t\s+i\s*=\s*0\s*;\s*"
        r"i\s*<\s*r_prec\s*;\s*i\+\+\s*\)\s*\{",
        "scalar monomial bit loop",
    )
    wrap_loop = _one_block(
        bit_loop.body,
        r"for\s*\(\s*size_t\s+j\s*=\s*0\s*;\s*"
        r"j\s*<\s*power\s*;\s*j\+\+\s*\)\s*\{",
        "scalar wrap loop",
    )
    _require_top_level_call(
        wrap_loop,
        ("NCMUX",),
        "scalar wrap loop",
    )
    direct_loop = _one_block(
        bit_loop.body,
        r"for\s*\(\s*size_t\s+j\s*=\s*0\s*;\s*"
        r"j\s*<\s*in_N\s*-\s*power\s*;\s*j\+\+\s*\)\s*\{",
        "scalar direct loop",
    )
    _require_top_level_call(
        direct_loop,
        ("CMUX",),
        "scalar direct loop",
    )

    sparse = _extract_function(source, "void sparse_mul(")
    round_loop = _one_block(
        sparse,
        r"for\s*\(\s*size_t\s+i\s*=\s*0\s*;\s*"
        r"i\s*<\s*sab->h\s*;\s*i\+\+\s*\)\s*\{",
        "scalar sparse round loop",
    )
    _require_ordered_calls(
        round_loop,
        ("RGSW_monomial_mul",),
        ("sub_a",),
        "scalar sparse round loop",
    )
    _require_call_after(
        sparse,
        round_loop,
        ("RGSW_monomial_mul",),
        None,
        "scalar sparse round loop",
    )


def _validate_pvw_monomial(source: str) -> None:
    monomial = _extract_function(
        source,
        "static uint64_t sab_pvw_RGSW_monomial_mul_state(",
    )
    bit_loop = _one_block(
        monomial,
        r"for\s*\(\s*size_t\s+bit\s*=\s*0\s*;\s*"
        r"bit\s*<\s*r_prec\s*;\s*bit\+\+\s*\)\s*\{",
        "PVW monomial bit loop",
    )
    wrap_loops = _find_blocks(
        bit_loop.body,
        r"for\s*\(\s*size_t\s+j\s*=\s*0\s*;\s*"
        r"j\s*<\s*power\s*;\s*j\+\+\s*\)\s*\{",
        "PVW wrap loop",
    )
    if len(wrap_loops) != 2:
        raise ScheduleInconclusiveError(
            "PVW wrap loop source shape changed"
        )
    _require_top_level_call(
        wrap_loops[0],
        ("sab_pvw_schedule_dual_sub_pair",),
        "PVW dual-sub wrap loop",
    )
    _require_top_level_call(
        wrap_loops[1],
        ("sab_pvw_schedule_NCMUX",),
        "PVW normal wrap loop",
    )
    _require_top_level_call(
        wrap_loops[1],
        ("sab_pvw_NCMUX",),
        "PVW normal wrap loop",
    )
    direct_loop = _one_block(
        bit_loop.body,
        r"for\s*\(\s*size_t\s+j\s*=\s*direct_start\s*;\s*"
        r"j\s*<\s*in_N\s*-\s*power\s*;\s*j\+\+\s*\)\s*\{",
        "PVW direct loop",
    )
    _require_top_level_call(
        direct_loop,
        ("sab_pvw_schedule_CMUX",),
        "PVW direct loop",
    )
    _require_top_level_call(
        direct_loop,
        ("sab_pvw_CMUX",),
        "PVW direct loop",
    )
    dual_if = _one_block(
        bit_loop.body,
        r"if\s*\(\s*2\s*\*\s*power\s*<=\s*in_N\s*\)\s*\{",
        "PVW dual-sub branch",
    )
    dual_nested = _find_blocks(
        dual_if.body,
        r"for\s*\(\s*size_t\s+j\s*=\s*0\s*;\s*"
        r"j\s*<\s*power\s*;\s*j\+\+\s*\)\s*\{",
        "PVW dual-sub wrap loop",
    )
    if len(dual_nested) != 1:
        raise ScheduleInconclusiveError(
            "PVW dual-sub call changed loop association"
        )
    assignment = re.search(
        r"\bdirect_start\s*=\s*power\s*;",
        dual_if.body,
    )
    if (
        assignment is None
        or _brace_depth_at(dual_if.body, assignment.start()) != 0
        or assignment.start() <= dual_nested[0].end
    ):
        raise ScheduleInconclusiveError(
            "PVW dual-sub direct_start changed association"
        )

    dual_pair = _extract_function(
        source,
        "static void sab_pvw_schedule_dual_sub_pair(",
    )
    pair_calls = _top_level_calls(
        dual_pair[
            dual_pair.find("{") + 1 : dual_pair.rfind("}")
        ],
        ("sab_pvw_CMUX_from_sub_internal",),
    )
    if len(pair_calls) != 2:
        raise ScheduleInconclusiveError(
            "PVW dual-sub pair must contain two selector calls"
        )


def _validate_pvw_sparse(source: str) -> None:
    sparse = _extract_function(source, "void sab_pvw_sparse_mul_binary(")
    round_loops = _find_blocks(
        sparse,
        r"for\s*\(\s*size_t\s+step\s*=\s*0\s*;\s*"
        r"step\s*<\s*sab->h\s*;\s*step\+\+\s*\)\s*\{",
        "PVW sparse round loop",
    )
    if len(round_loops) != 2:
        raise ScheduleInconclusiveError(
            "PVW sparse source must contain both binary round branches"
        )
    active_loop, fallback_loop = round_loops
    _require_ordered_calls(
        active_loop,
        ("sab_pvw_RGSW_monomial_mul_state",),
        ("sab_pvw_sub_a_binary_to", "sab_pvw_sub_a_binary"),
        "PVW active sparse round loop",
    )
    _require_ordered_calls(
        fallback_loop,
        ("sab_pvw_RGSW_monomial_mul",),
        ("sab_pvw_sub_a_binary",),
        "PVW fallback sparse round loop",
    )
    _require_call_after(
        sparse,
        active_loop,
        ("sab_pvw_RGSW_monomial_mul_state",),
        fallback_loop.start,
        "PVW active sparse round loop",
    )
    _require_call_after(
        sparse,
        fallback_loop,
        ("sab_pvw_RGSW_monomial_mul",),
        None,
        "PVW fallback sparse round loop",
    )

    sub_a_to = _extract_function(
        source,
        "static void sab_pvw_sub_a_binary_to(",
    )
    to_loop = _one_block(
        sub_a_to,
        r"for\s*\(\s*size_t\s+idx\s*=\s*0\s*;\s*"
        r"idx\s*<\s*sab->in_N\s*;\s*idx\+\+\s*\)\s*\{",
        "PVW sub_a output loop",
    )
    _require_top_level_call(
        to_loop,
        ("pvmtmlwe_mul_by_xai",),
        "PVW sub_a output loop",
    )
    sub_a = _extract_function(source, "void sab_pvw_sub_a_binary(")
    loop = _one_block(
        sub_a,
        r"for\s*\(\s*size_t\s+idx\s*=\s*0\s*;\s*"
        r"idx\s*<\s*sab->in_N\s*;\s*idx\+\+\s*\)\s*\{",
        "PVW sub_a loop",
    )
    _require_top_level_call(
        loop,
        ("pvmtmlwe_mul_by_xai",),
        "PVW sub_a loop",
    )


def _validate_pvw_schedule(source: str) -> None:
    _validate_pvw_monomial(source)
    _validate_pvw_sparse(source)


def _load_stage203_support(root: Path) -> _Stage203Evidence:
    relative_path = (
        "repro/stage203_production_selector_equation_probe/"
        "equation_map.csv"
    )
    source = _read_source(root, relative_path)
    table = tuple(csv.reader(source.splitlines()))
    if not table:
        raise ScheduleInconclusiveError(
            "Stage203 support-only equation map is empty"
        )
    fields = tuple(table[0])
    rows = tuple(tuple(row) for row in table[1:])
    if any(len(row) != len(fields) for row in rows):
        raise ScheduleInconclusiveError(
            "Stage203 equation map contains malformed rows"
        )
    return _Stage203Evidence(fields=fields, rows=rows)


def _with_cycle_coefficient(
    evidence: _Stage203Evidence,
    r: int,
) -> _Stage203Evidence:
    if not {"r", "equation_class"}.issubset(evidence.fields):
        raise ScheduleInconclusiveError(
            "Stage203 support-only equation map header changed"
        )
    fields = evidence.fields + ("coefficient",)
    equation_index = evidence.fields.index("equation_class")
    r_index = evidence.fields.index("r")
    rows = tuple(
        row
        + (
            "1"
            if (
                row[r_index] == str(r)
                and row[equation_index]
                == "lane_neighbor_body_interaction"
            )
            else "",
        )
        for row in evidence.rows
    )
    return _Stage203Evidence(fields=fields, rows=rows)


def _validate_stage203_support(
    evidence: _Stage203Evidence,
    r: int,
) -> str:
    if evidence.fields != _STAGE203_SUPPORT_FIELDS:
        if "coefficient" in evidence.fields:
            return _UNREGISTERED_NUMERIC_EVIDENCE
        raise ScheduleInconclusiveError(
            "Stage203 support-only equation map header changed"
        )
    records = tuple(
        dict(zip(evidence.fields, row, strict=True))
        for row in evidence.rows
    )
    try:
        selected = [row for row in records if int(row["r"]) == r]
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
    if len(neighbors) != r:
        raise ScheduleInconclusiveError(
            f"Stage203 r={r} cycle support is incomplete"
        )
    for lane, row in enumerate(neighbors, start=1):
        if (
            int(row["row"]) != lane
            or int(row["col"]) != 1 + (lane % r)
            or row["semantic_role"] != "active"
            or row["is_public_row"] != "1"
            or row["may_skip_after_proof"] != "0"
        ):
            raise ScheduleInconclusiveError(
                f"Stage203 r={r} cycle support changed"
            )
    return INCONCLUSIVE_OPERATOR


def load_binary_target_schedule(
    root: Path | str,
) -> BinaryTargetSchedule:
    """Parse default parameters and validate exact binary control flow."""

    root_path = Path(root)
    main_source = _read_source(root_path, "main.c")
    scalar_source = _read_source(
        root_path,
        "src/sparse_amortized_bootstrap.c",
    )
    pvw_source = _read_source(root_path, "src/sab_pvw.c")
    make_source = _read_source(
        root_path,
        "src/mosfhet/Makefile.def",
    )
    target = _parse_default_target(main_source)
    _validate_scalar_schedule(scalar_source)
    _validate_pvw_schedule(pvw_source)
    _validate_exact_function_bindings(
        {
            "src/sparse_amortized_bootstrap.c": scalar_source,
            "src/sab_pvw.c": pvw_source,
        }
    )

    h = _parse_int(target, "h")
    r_prec = _parse_int(target, "r_prec")
    in_N = _parse_int(target, "in_N")
    if min(h, r_prec, in_N) <= 0:
        raise ScheduleInconclusiveError(
            "default binary target dimensions must be positive"
        )
    monomial_calls = h + 1
    butterfly_steps = monomial_calls * r_prec
    selectors_per_monomial = sum(
        (1 << bit) + (in_N - (1 << bit))
        for bit in range(r_prec)
    )
    if selectors_per_monomial != r_prec * in_N:
        raise ScheduleInconclusiveError(
            "binary butterfly loops no longer cover in_N selectors per bit"
        )
    return BinaryTargetSchedule(
        target="SET_2_3_2048",
        h=h,
        r_prec=r_prec,
        in_N=in_N,
        monomial_calls=monomial_calls,
        butterfly_steps=butterfly_steps,
        selector_applications=(
            monomial_calls * selectors_per_monomial
        ),
        dual_sub_enabled=_parse_make_default(
            make_source,
            "SAB_PVW_DUAL_SUB_CMUX",
        ),
        source_anchors=_SOURCE_ANCHORS,
    )


def iter_binary_schedule_events(
    schedule: BinaryTargetSchedule,
    *,
    dual_sub_enabled: bool | None = None,
) -> Iterator[ScheduleEvent]:
    """Yield the exact binary schedule without retaining its event history."""

    dual_sub = (
        schedule.dual_sub_enabled
        if dual_sub_enabled is None
        else dual_sub_enabled
    )
    if type(dual_sub) is not bool:
        raise ValueError("dual_sub_enabled must be boolean")
    for monomial in range(schedule.monomial_calls):
        for bit in range(schedule.r_prec):
            power = 1 << bit
            if dual_sub and 2 * power <= schedule.in_N:
                for index in range(power):
                    yield ScheduleEvent(
                        "ncmux",
                        monomial,
                        bit,
                        index,
                        "dual_sub_pair",
                    )
                    yield ScheduleEvent(
                        "cmux",
                        monomial,
                        bit,
                        index + power,
                        "dual_sub_pair",
                    )
                direct_start = power
            else:
                for index in range(power):
                    yield ScheduleEvent(
                        "ncmux",
                        monomial,
                        bit,
                        index,
                        "wrap",
                    )
                direct_start = 0
            for index in range(
                direct_start,
                schedule.in_N - power,
            ):
                yield ScheduleEvent(
                    "cmux",
                    monomial,
                    bit,
                    index + power,
                    "direct",
                )
            yield ScheduleEvent(
                "butterfly_boundary",
                monomial,
                bit,
            )
        yield ScheduleEvent("monomial_boundary", monomial)
        if monomial < schedule.h:
            yield ScheduleEvent("sub_a_boundary", monomial)


def _default_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _independent_control_state(r: int, modulus: int):
    directions = tuple(
        tuple(
            1 if lane == column + 1 else 0
            for column in range(r - 1)
        )
        for lane in range(r)
    )
    return append_mask_directions(
        shared_state(r, modulus),
        directions,
    )


def _exercise_live_provenance_mutation(
    r: int,
    modulus: int,
    selector_index: int,
) -> str:
    lhs = append_mask_directions(
        shared_state(r, modulus),
        tuple((0,) if lane == 0 else (1,) for lane in range(r)),
    )
    rhs = append_mask_directions(
        shared_state(r, modulus),
        tuple((0,) if lane == 0 else (1,) for lane in range(r)),
    )
    mutated_rhs = replace(rhs, provenance=lhs.provenance)
    try:
        linear_combine_states(lhs, mutated_rhs, 1, 1)
    except ValueError as error:
        if "independent provenance" in str(error):
            return (
                "FAIL_MUTATED_PROVENANCE_AT_SELECTOR_"
                f"{selector_index}"
            )
        return "FAIL_UNEXPECTED_PROVENANCE_VALIDATION_ERROR"
    return "FAIL_PROVENANCE_MUTATION_NOT_REJECTED"


def _actual_boundary(
    selector_index: int,
    block_length: int,
    mutated: bool,
) -> bool:
    if not mutated:
        return selector_index % block_length == 0
    if selector_index == block_length:
        return False
    if selector_index == block_length + 1:
        return True
    return selector_index % block_length == 0


def _stream_replay(
    schedule: BinaryTargetSchedule,
    r: int,
    modulus: int,
    *,
    block_length: int | None,
    boundary_mutated: bool,
    provenance_mutated: bool,
) -> _ReplayCounts:
    counts = _ReplayCounts()
    for event in iter_binary_schedule_events(schedule):
        counts.events += 1
        if event.kind == "ncmux":
            counts.ncmux += 1
        elif event.kind == "cmux":
            counts.cmux += 1
        elif event.kind == "butterfly_boundary":
            counts.butterflies += 1
        elif event.kind == "monomial_boundary":
            counts.monomials += 1
        elif event.kind == "sub_a_boundary":
            counts.sub_a += 1
        if event.kind not in _SELECTOR_KINDS:
            continue

        counts.selectors += 1
        if provenance_mutated and counts.selectors == 1:
            counts.provenance_gate = (
                _exercise_live_provenance_mutation(
                    r,
                    modulus,
                    counts.selectors,
                )
            )
        if block_length is None:
            continue
        expected = counts.selectors % block_length == 0
        actual = _actual_boundary(
            counts.selectors,
            block_length,
            boundary_mutated,
        )
        if actual:
            counts.compression_boundaries += 1
            if counts.first_actual_boundary is None:
                counts.first_actual_boundary = counts.selectors
        if (
            expected != actual
            and counts.first_boundary_mismatch is None
        ):
            counts.first_boundary_mismatch = counts.selectors
    return counts


def replay_variant_schedule(
    variant: str,
    r: int,
    modulus: int,
    *,
    root: Path | str | None = None,
    block_length: int | None = None,
    mutation: str | None = None,
) -> ScheduleTrace:
    """Stream one exact schedule and evaluate only registered gate facts."""

    root_path = _default_root() if root is None else Path(root)
    schedule = load_binary_target_schedule(root_path)
    if variant not in {"C0", "C1", "C2"}:
        raise ValueError(
            f"unknown Candidate C schedule variant: {variant!r}"
        )
    if type(r) is not int or r not in {2, 4, 6}:
        raise ValueError("r must be one of 2, 4, 6")
    if variant == "C2":
        if (
            type(block_length) is not int
            or block_length not in _C2_BLOCK_LENGTHS
        ):
            raise ValueError(
                "C2 block length must be one of "
                "1, 2, 4, 8, 16, 32, 64"
            )
    elif block_length is not None:
        raise ValueError("block length is registered only for C2")
    if mutation not in {
        None,
        "cycle_coefficient",
        "compression_boundary",
        "provenance_identifier",
    }:
        raise ValueError(f"unknown schedule mutation: {mutation!r}")
    if mutation == "compression_boundary" and variant != "C2":
        raise ValueError(
            "compression boundary mutation requires C2"
        )
    if mutation == "cycle_coefficient" and variant == "C0":
        raise ValueError(
            "cycle coefficient mutation requires C1 or C2"
        )

    if variant == "C0":
        operator_gate = "PASS_EXPLICIT_NEGATIVE_CONTROL"
    else:
        support_evidence = _load_stage203_support(root_path)
        if mutation == "cycle_coefficient":
            support_evidence = _with_cycle_coefficient(
                support_evidence,
                r,
            )
        operator_gate = _validate_stage203_support(
            support_evidence,
            r,
        )

    counts = _stream_replay(
        schedule,
        r,
        modulus,
        block_length=block_length,
        boundary_mutated=mutation == "compression_boundary",
        provenance_mutated=mutation == "provenance_identifier",
    )
    if counts.selectors != schedule.selector_applications:
        raise ScheduleInconclusiveError(
            "streamed selector count does not match parsed schedule"
        )
    if counts.monomials != schedule.monomial_calls:
        raise ScheduleInconclusiveError(
            "streamed monomial boundary count is incomplete"
        )
    if counts.sub_a != schedule.h:
        raise ScheduleInconclusiveError(
            "streamed sub_a boundary count is incomplete"
        )

    if variant == "C0":
        control_state = _independent_control_state(r, modulus)
        max_rho = excess_rank(control_state)
        first_rank_overflow = (
            1 if max_rho > min(2, r - 1) else None
        )
        phase_gate = "NOT_APPLICABLE_NEGATIVE_CONTROL"
        closure_gate = "REJECT_EXPECTED"
        boundary_gate = "PASS_STRUCTURAL_SCHEDULE"
        provenance_gate = (
            counts.provenance_gate
            if mutation == "provenance_identifier"
            else "PASS_EXPLICIT_CONTROL"
        )
    else:
        max_rho = None
        first_rank_overflow = None
        phase_gate = INCONCLUSIVE_OPERATOR
        closure_gate = INCONCLUSIVE_OPERATOR
        provenance_gate = (
            counts.provenance_gate
            if mutation == "provenance_identifier"
            else INCONCLUSIVE_OPERATOR
        )
        if variant == "C1":
            boundary_gate = "PASS_STRUCTURAL_SCHEDULE"
        elif counts.first_boundary_mismatch is not None:
            boundary_gate = "FAIL_MUTATED_COMPRESSION_BOUNDARY"
        elif block_length == 1:
            boundary_gate = "REJECT_PER_CMUX_CONTROL"
        else:
            boundary_gate = "PASS_STRUCTURAL_BOUNDARIES"

    return ScheduleTrace(
        variant=variant,
        r=r,
        modulus=modulus,
        rho_bound=min(2, r - 1),
        max_rho=max_rho,
        first_rank_overflow=first_rank_overflow,
        first_missing_edge=None,
        steps_before_compression=counts.first_actual_boundary,
        compressions=0,
        compression_boundaries_checked=(
            counts.compression_boundaries
        ),
        first_boundary_mismatch=counts.first_boundary_mismatch,
        completed_butterflies=counts.selectors,
        selector_applications=schedule.selector_applications,
        selector_boundaries_checked=counts.selectors,
        ncmux_events_checked=counts.ncmux,
        cmux_events_checked=counts.cmux,
        butterfly_boundaries_checked=counts.butterflies,
        monomial_boundaries_checked=counts.monomials,
        sub_a_boundaries_checked=counts.sub_a,
        events_traversed=counts.events,
        phase_gate=phase_gate,
        closure_gate=closure_gate,
        boundary_gate=boundary_gate,
        provenance_gate=provenance_gate,
        operator_mapping_gate=operator_gate,
    )
