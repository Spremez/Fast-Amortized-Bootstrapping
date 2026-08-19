"""Source-anchored parameters for the Candidate D D2 closure checker.

The D2 gate must not invent its own schedule parameters: the small-ring test
dimensions are fixed by the admission contract, while the sparse-schedule
shape (input ring dimension, secret Hamming weight, and the RGSW monomial
precision) is derived from the production sources themselves. This module
parses those anchors out of ``main.c`` and hashes every required input file
so the D2 report binds the checker to an exact source tree.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from pathlib import Path

REQUIRED_INPUTS = (
    "src/sparse_amortized_bootstrap.c",
    "src/sab_pvw.c",
    "include/sab.h",
    "include/sab_pvw.h",
    "main.c",
)

_PRIMARY_SET = "SET_2_3_2048"


class SourceMapError(ValueError):
    """Raised when the production source anchors cannot be parsed."""


@dataclass(frozen=True)
class SourceMap:
    input_n: int
    hamming_weight: int
    target_r_prec: int
    small_h: int
    file_hashes: tuple[tuple[str, str], ...]


def _parse_block(source: str, parameter_set: str) -> dict[str, int]:
    pattern = re.compile(
        rf"#if defined\({parameter_set}\)(.*?)#elif",
        re.DOTALL,
    )
    match = pattern.search(source)
    if match is None:
        raise SourceMapError(f"{parameter_set} block not found in main.c")
    block = match.group(1)
    values: dict[str, int] = {}
    for name in ("in_N", "h_in", "target_r_prec"):
        found = re.search(rf"\b{name}\s*=\s*(\d+)", block)
        if found is None:
            raise SourceMapError(f"{name} missing from {parameter_set}")
        values[name] = int(found.group(1))
    return values


def load_source_map(root: Path) -> SourceMap:
    main_c = root / "main.c"
    if not main_c.is_file():
        raise SourceMapError("main.c is missing from the checkout")
    values = _parse_block(main_c.read_text(encoding="utf-8"), _PRIMARY_SET)
    file_hashes: list[tuple[str, str]] = []
    for relative in REQUIRED_INPUTS:
        path = root / relative
        if not path.is_file():
            raise SourceMapError(f"required input {relative} is missing")
        file_hashes.append(
            (relative, hashlib.sha256(path.read_bytes()).hexdigest())
        )
    small_h = max(2, min(values["h_in"], 4))
    return SourceMap(
        input_n=values["in_N"],
        hamming_weight=values["h_in"],
        target_r_prec=values["target_r_prec"],
        small_h=small_h,
        file_hashes=tuple(file_hashes),
    )
