"""Fail-closed Candidate D D0 baseline evidence freeze."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal
import hashlib
from pathlib import Path, PurePosixPath
import re
from typing import Iterable, Mapping


D0_DECISION = "PASS_D0_CANDIDATE_D_BASELINES_FROZEN"
PRIMARY_METRIC = "T_complete_bootstrap/(r*N_active)"
REQUIRED_NOT_YET_LOCAL = "REQUIRED_NOT_YET_LOCAL"
FROZEN_HIGHSTAT = "FROZEN_HISTORICAL_HIGHSTAT"

EXPECTED_ANCHORS = {
    "repro/candidate_a_star_cycle_gate/summary.csv": (
        "c7a003c39d8e56f1cc4ca0845cffe7e68f81cd41a8979d661f8a3df525a96d09"
    ),
    "repro/candidate_b_factorized_gate/summary.csv": (
        "c758785b0ce7d4d6ef56bb44639b381780ef0d529dc17c8f2544ec67ce3b7a91"
    ),
    "repro/candidate_c_rank_bounded_gate/terminal_record.csv": (
        "7c7e60bd9a201d4ed943d411dbd40be76ece8f4942822ca31ed278d53c8863d7"
    ),
    "repro/stage331_current_head_highstat_refresh/summary.csv": (
        "23d3c2611329f189a88f6bdc645e9ed1ac237d19159e79401d2fc11b9c03ad56"
    ),
    "repro/stage345_binary_matrix_synthesis/binary_matrix.csv": (
        "97014b127ad5061dc10fbd3cb3ab53fb06d9ebc69b436011760778425208ea9b"
    ),
    "src/sab_pvw.c": (
        "6aaabf61f010e0154b826855286137afc39de9b2520ee09e2ca43d5accf5e2ac"
    ),
    "src/mosfhet/src/mattrgsw.c": (
        "5da51089a748f7f1f54b56f81c2948ced14f0be4dd431bcffb2339af97c527fa"
    ),
    "main.c": (
        "d402980a203aacbaf6b281a9f7245cf14b72c2c80468e5a05050f35373eb11f8"
    ),
}

ANCHOR_ROLES = {
    "repro/candidate_a_star_cycle_gate/summary.csv": (
        "candidate_a_terminal_decision"
    ),
    "repro/candidate_b_factorized_gate/summary.csv": (
        "candidate_b_terminal_decision"
    ),
    "repro/candidate_c_rank_bounded_gate/terminal_record.csv": (
        "candidate_c_terminal_decision"
    ),
    "repro/stage331_current_head_highstat_refresh/summary.csv": (
        "b0a_b1_highstat_metrics"
    ),
    "repro/stage345_binary_matrix_synthesis/binary_matrix.csv": (
        "b1_backend_and_metric_cross_check"
    ),
    "src/sab_pvw.c": "b1_exact_dense_pvw_sab_source",
    "src/mosfhet/src/mattrgsw.c": "b1_mat_trgsw_source",
    "main.c": "target_parameters_and_smoke_harness",
}

_PREDECESSOR_DECISIONS = {
    "repro/candidate_a_star_cycle_gate/summary.csv": (
        "REJECT_CANDIDATE_A_STANDARD_PVW_RANDOMIZATION_ROUTE_TO_B"
    ),
    "repro/candidate_b_factorized_gate/summary.csv": (
        "REJECT_CANDIDATE_B_EXACT_STANDARD_PVW_FACTORIZATION_ROUTE_TO_C"
    ),
    "repro/candidate_c_rank_bounded_gate/terminal_record.csv": (
        "REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL"
    ),
}

_EXPECTED_PARAMETERS = {
    "in_N": 2048,
    "out_N": 2048,
    "out_k": 1,
    "l": 1,
    "bg_bit": 23,
    "prec": 3,
    "h": 39,
    "r_prec": 7,
    "sigma_out": 2.0**-50,
    "H": 573440,
}

_B1_SOURCE = "repro/stage331_current_head_highstat_refresh/summary.csv"
_B1_MATRIX = "repro/stage345_binary_matrix_synthesis/binary_matrix.csv"
_B1_EXPECTED = {
    "decision": "PASS_STAGE331_CURRENT_HEAD_HIGHSTAT_REFRESH",
    "primary_metric": "complete_sab_T_bootstrap_over_r_vs_repeated_scalar",
    "samples": "10",
    "correctness": "Pass",
    "t_bootstrap_over_r_mean_us": "6117083.425",
    "scalar_t_bootstrap_over_r_mean_us": "10690503.200",
    "speedup_vs_repeated_scalar_mean": "1.747647",
    "noise_trials": "10",
    "noise_pair_failures": "0",
    "claim_level": "current_head_scoped_highstat",
}
_B1_MATRIX_EXPECTED = {
    "case": "SET_2_3_2048_r4",
    "param": "SET_2_3_2048",
    "r": "4",
    "backend": "spqlios_avx512-wsl",
    "metric": "complete_sab_T_bootstrap_over_r_vs_repeated_scalar",
    "samples": "10",
    "correctness": "Pass",
    "pvw_t_over_r_mean_us": "6117083.425",
    "scalar_t_over_r_mean_us": "10690503.200",
    "speedup_mean": "1.747647",
    "noise_trials": "10",
    "noise_pair_failures": "0",
    "evidence_stage": "Stage331",
    "source": _B1_SOURCE,
    "claim_status": "current_head_highstat",
}

_MANIFEST_FIELDS = (
    "baseline_id",
    "baseline_name",
    "status",
    "evidence_class",
    "source_path",
    "source_sha256",
    "backend",
    "r",
    "n_active",
    "t_complete_bootstrap_us",
    "t_over_r_us",
    "t_over_r_n_active_us",
    "primary_metric",
    "metric_unit",
    "speedup_vs_b0a",
    "pair_failures",
    "pair_trials",
    "performance_claim",
)


class BaselineEvidenceError(RuntimeError):
    """A required D0 source or semantic invariant did not validate."""


@dataclass(frozen=True)
class BaselineAnchor:
    path: str
    sha256: str
    role: str


def sha256_file(path: Path) -> str:
    candidate = Path(path)
    if candidate.is_symlink() or not candidate.is_file():
        raise BaselineEvidenceError(f"anchor is not a regular file: {candidate}")
    digest = hashlib.sha256()
    try:
        with candidate.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as error:
        raise BaselineEvidenceError(f"cannot hash anchor: {candidate}") from error
    return digest.hexdigest()


def _resolved_root(root: Path) -> Path:
    candidate = Path(root)
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        raise BaselineEvidenceError("repository root cannot be resolved") from error
    if not resolved.is_dir():
        raise BaselineEvidenceError("repository root is not a directory")
    return resolved


def _anchor_path(root: Path, relative: str) -> Path:
    pure = PurePosixPath(relative)
    if (
        not relative
        or pure.is_absolute()
        or ".." in pure.parts
        or "." in pure.parts
        or pure.as_posix() != relative
        or Path(relative).is_absolute()
    ):
        raise BaselineEvidenceError(
            f"manifest path outside repository root: {relative}"
        )
    unresolved = root.joinpath(*pure.parts)
    try:
        resolved = unresolved.resolve(strict=True)
    except OSError as error:
        raise BaselineEvidenceError(f"missing baseline anchor: {relative}") from error
    if not resolved.is_relative_to(root):
        raise BaselineEvidenceError(
            f"manifest path outside repository root: {relative}"
        )
    if unresolved != resolved or unresolved.is_symlink() or not resolved.is_file():
        raise BaselineEvidenceError(
            f"baseline anchor is not a repository regular file: {relative}"
        )
    return resolved


def validate_baseline_anchors(root: Path) -> tuple[BaselineAnchor, ...]:
    source_root = _resolved_root(root)
    anchors = []
    for relative, expected_hash in EXPECTED_ANCHORS.items():
        path = _anchor_path(source_root, relative)
        actual_hash = sha256_file(path)
        if actual_hash != expected_hash:
            raise BaselineEvidenceError(
                f"baseline anchor hash mismatch: {relative}"
            )
        role = ANCHOR_ROLES.get(relative)
        if role is None:
            raise BaselineEvidenceError(
                f"baseline anchor has no registered role: {relative}"
            )
        anchors.append(BaselineAnchor(relative, actual_hash, role))
    return tuple(anchors)


def _read_csv(root: Path, relative: str) -> tuple[dict[str, str], ...]:
    path = _anchor_path(root, relative)
    try:
        with path.open("r", encoding="ascii", newline="") as handle:
            reader = csv.DictReader(handle, strict=True)
            fieldnames = tuple(reader.fieldnames or ())
            if not fieldnames or len(fieldnames) != len(set(fieldnames)):
                raise BaselineEvidenceError(
                    f"invalid CSV field names: {relative}"
                )
            rows = []
            signatures = set()
            for row in reader:
                if None in row or set(row) != set(fieldnames):
                    raise BaselineEvidenceError(
                        f"malformed artifact row: {relative}"
                    )
                signature = tuple(row[field] for field in fieldnames)
                if signature in signatures:
                    raise BaselineEvidenceError(
                        f"duplicate artifact rows: {relative}"
                    )
                signatures.add(signature)
                rows.append(dict(row))
    except (OSError, UnicodeError, csv.Error) as error:
        raise BaselineEvidenceError(f"cannot parse CSV anchor: {relative}") from error
    if not rows:
        raise BaselineEvidenceError(f"artifact has no rows: {relative}")
    return tuple(rows)


def _single_row(root: Path, relative: str) -> dict[str, str]:
    rows = _read_csv(root, relative)
    if len(rows) != 1:
        raise BaselineEvidenceError(
            f"duplicate artifact rows or unexpected row count: {relative}"
        )
    return rows[0]


def _require_fields(
    row: Mapping[str, str],
    expected: Mapping[str, str],
    label: str,
) -> None:
    missing = tuple(field for field in expected if field not in row)
    if missing:
        raise BaselineEvidenceError(
            f"{label} missing fields: {', '.join(missing)}"
        )
    mismatches = tuple(
        field for field, value in expected.items() if row[field] != value
    )
    if mismatches:
        raise BaselineEvidenceError(
            f"{label} mismatch: {', '.join(mismatches)}"
        )


def validate_terminal_predecessors(root: Path) -> None:
    source_root = _resolved_root(root)
    for relative, decision in _PREDECESSOR_DECISIONS.items():
        row = _single_row(source_root, relative)
        if row.get("decision") != decision:
            raise BaselineEvidenceError(
                f"predecessor decision mismatch: {relative}"
            )
    candidate_a = _single_row(
        source_root,
        "repro/candidate_a_star_cycle_gate/summary.csv",
    )
    candidate_b = _single_row(
        source_root,
        "repro/candidate_b_factorized_gate/summary.csv",
    )
    candidate_c = _single_row(
        source_root,
        "repro/candidate_c_rank_bounded_gate/terminal_record.csv",
    )
    if (
        candidate_a.get("production_code_permission") != "no"
        or candidate_a.get("route") != "candidate_b_factorized_star_cycle"
        or candidate_b.get("production_code_permission") != "no"
        or candidate_b.get("route")
        != "candidate_c_rank_bounded_shared_mask_state"
        or candidate_c.get("classification") != "REJECT"
        or candidate_c.get("task4_status")
        != "SKIPPED_NO_REGISTERED_OPERATOR"
    ):
        raise BaselineEvidenceError("predecessor decision boundary mismatch")


def _split_c_initializer(initializer: str) -> tuple[str, ...]:
    values = []
    start = 0
    depth = 0
    for index, character in enumerate(initializer):
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth < 0:
                raise BaselineEvidenceError(
                    "target parameter initializer has unbalanced parentheses"
                )
        elif character == "," and depth == 0:
            values.append(initializer[start:index].strip())
            start = index + 1
    if depth != 0:
        raise BaselineEvidenceError(
            "target parameter initializer has unbalanced parentheses"
        )
    values.append(initializer[start:].strip())
    if any(not value for value in values):
        raise BaselineEvidenceError("target parameter initializer has an empty value")
    return tuple(values)


def parse_target_parameters(root: Path) -> dict[str, int | float]:
    source_root = _resolved_root(root)
    main_path = _anchor_path(source_root, "main.c")
    try:
        source = main_path.read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeError) as error:
        raise BaselineEvidenceError("cannot read target parameter source") from error

    declaration = re.search(
        r"typedef\s+struct\s*\{(?P<body>.*?)\}"
        r"\s*SAB_PVW_Target_Params\s*;",
        source,
        flags=re.DOTALL,
    )
    function = re.search(
        r"static\s+SAB_PVW_Target_Params\s+"
        r"sab_pvw_target_params\s*\(\s*void\s*\)\s*\{"
        r"(?P<body>.*?)#endif\s*\}",
        source,
        flags=re.DOTALL,
    )
    if declaration is None or function is None:
        raise BaselineEvidenceError("target parameter declaration not found")
    fields = tuple(
        re.findall(
            r"^\s*(?:int|double)\s+"
            r"([A-Za-z_][A-Za-z0-9_]*)\s*;\s*$",
            declaration.group("body"),
            flags=re.MULTILINE,
        )
    )
    initializer = re.search(
        r"#else\s*return\s*\(SAB_PVW_Target_Params\)\s*"
        r"\{(?P<values>.*?)\}\s*;",
        function.group("body"),
        flags=re.DOTALL,
    )
    if (
        not fields
        or len(fields) != len(set(fields))
        or initializer is None
    ):
        raise BaselineEvidenceError("target parameter fields are invalid")
    values = _split_c_initializer(initializer.group("values"))
    if len(fields) != len(values):
        raise BaselineEvidenceError(
            "target parameter field/initializer length mismatch"
        )
    tokens = dict(zip(fields, values, strict=True))
    required = (
        "in_N",
        "out_N",
        "out_k",
        "l",
        "bg_bit",
        "prec",
        "h",
        "r_prec",
        "sigma_out",
    )
    if any(field not in tokens for field in required):
        raise BaselineEvidenceError("target parameter is missing")

    parsed: dict[str, int | float] = {}
    for field in required[:-1]:
        token = tokens[field]
        if re.fullmatch(r"(?:0|[1-9][0-9]*)", token) is None:
            raise BaselineEvidenceError(
                f"target parameter is not a literal integer: {field}"
            )
        parsed[field] = int(token, 10)
    sigma_match = re.fullmatch(
        r"pow\s*\(\s*2\s*,\s*(-?[0-9]+)\s*\)",
        tokens["sigma_out"],
    )
    if sigma_match is None:
        raise BaselineEvidenceError("target parameter sigma_out is not pow(2, e)")
    parsed["sigma_out"] = 2.0 ** int(sigma_match.group(1))
    parsed["H"] = (
        (int(parsed["h"]) + 1)
        * int(parsed["r_prec"])
        * int(parsed["in_N"])
    )
    return parsed


def _validated_b1_row(root: Path) -> tuple[dict[str, str], dict[str, str]]:
    summary = _single_row(root, _B1_SOURCE)
    if summary.get("noise_pair_failures") not in (None, "0"):
        raise BaselineEvidenceError(
            "historical pair-failure count must remain zero"
        )
    _require_fields(summary, _B1_EXPECTED, "B1 numeric row")

    matrix_rows = _read_csv(root, _B1_MATRIX)
    cases = [row.get("case") for row in matrix_rows]
    if len(cases) != len(set(cases)):
        raise BaselineEvidenceError(
            f"duplicate artifact rows: {_B1_MATRIX}"
        )
    matching = [
        row for row in matrix_rows if row.get("case") == "SET_2_3_2048_r4"
    ]
    if len(matching) != 1:
        raise BaselineEvidenceError("B1 matrix row is missing or duplicated")
    matrix = matching[0]
    if matrix.get("noise_pair_failures") not in (None, "0"):
        raise BaselineEvidenceError(
            "historical pair-failure count must remain zero"
        )
    _require_fields(matrix, _B1_MATRIX_EXPECTED, "B1 numeric row")
    return summary, matrix


def _metric_rows(
    anchors: tuple[BaselineAnchor, ...],
    summary: Mapping[str, str],
    matrix: Mapping[str, str],
) -> tuple[dict[str, str], ...]:
    hashes = {anchor.path: anchor.sha256 for anchor in anchors}
    r = Decimal(matrix["r"])
    n_active = Decimal("2048")
    b1_over_r = Decimal(summary["t_bootstrap_over_r_mean_us"])
    b0a_over_r = Decimal(summary["scalar_t_bootstrap_over_r_mean_us"])
    b1_total = b1_over_r * r
    b0a_total = b0a_over_r * r
    quantum = Decimal("0.000000001")
    b1_primary = (b1_over_r / n_active).quantize(quantum)
    b0a_primary = (b0a_over_r / n_active).quantize(quantum)
    calculated_speedup = (b0a_over_r / b1_over_r).quantize(
        Decimal("0.000001")
    )
    if calculated_speedup != Decimal(
        summary["speedup_vs_repeated_scalar_mean"]
    ):
        raise BaselineEvidenceError("B1 numeric row speedup is inconsistent")

    shared = {
        "status": FROZEN_HIGHSTAT,
        "evidence_class": "HISTORICAL_CURRENT_HEAD_HIGHSTAT",
        "source_path": _B1_SOURCE,
        "source_sha256": hashes[_B1_SOURCE],
        "backend": matrix["backend"],
        "r": matrix["r"],
        "n_active": "2048",
        "primary_metric": PRIMARY_METRIC,
        "metric_unit": "us",
        "performance_claim": (
            "HISTORICAL_WSL_HIGHSTAT_NOT_FORMAL_NATIVE_PERFORMANCE"
        ),
    }
    missing = {
        "status": REQUIRED_NOT_YET_LOCAL,
        "evidence_class": "REQUIRED_CONTROL",
        "source_path": "",
        "source_sha256": "",
        "backend": "",
        "r": "",
        "n_active": "2048",
        "t_complete_bootstrap_us": "",
        "t_over_r_us": "",
        "t_over_r_n_active_us": "",
        "primary_metric": PRIMARY_METRIC,
        "metric_unit": "us",
        "speedup_vs_b0a": "",
        "pair_failures": "",
        "pair_trials": "",
        "performance_claim": "NONE_REQUIRED_NOT_YET_LOCAL",
    }
    return (
        {
            "baseline_id": "B0a",
            "baseline_name": "repeated_scalar_SAB",
            **shared,
            "t_complete_bootstrap_us": f"{b0a_total:.3f}",
            "t_over_r_us": f"{b0a_over_r:.3f}",
            "t_over_r_n_active_us": f"{b0a_primary:.9f}",
            "speedup_vs_b0a": "1.000000",
            "pair_failures": "",
            "pair_trials": "",
        },
        {
            "baseline_id": "B0b",
            "baseline_name": (
                "independent_mask_shared_output_key_scalar_control"
            ),
            **missing,
        },
        {
            "baseline_id": "B1",
            "baseline_name": "exact_dense_PVW_MAT_SAB",
            **shared,
            "t_complete_bootstrap_us": f"{b1_total:.3f}",
            "t_over_r_us": f"{b1_over_r:.3f}",
            "t_over_r_n_active_us": f"{b1_primary:.9f}",
            "speedup_vs_b0a": summary[
                "speedup_vs_repeated_scalar_mean"
            ],
            "pair_failures": summary["noise_pair_failures"],
            "pair_trials": summary["noise_trials"],
        },
        {
            "baseline_id": "B2",
            "baseline_name": "relevant_local_BatchBoot_composition",
            **missing,
        },
    )


def _write_csv(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: Iterable[Mapping[str, str]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("w", encoding="ascii", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=fieldnames,
                lineterminator="\n",
                extrasaction="raise",
            )
            writer.writeheader()
            writer.writerows(rows)
    except (OSError, UnicodeError, csv.Error) as error:
        raise BaselineEvidenceError(f"cannot write D0 CSV: {path}") from error


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(content, encoding="ascii", newline="\n")
    except (OSError, UnicodeError) as error:
        raise BaselineEvidenceError(f"cannot write D0 text: {path}") from error


def _environment_rows(params: Mapping[str, int | float]):
    return (
        {
            "key": "parameter_set",
            "value": "BINARY/include-zero SET_2_3_2048",
            "unit": "",
            "evidence_class": "SOURCE_PARSED",
            "source": "main.c",
        },
        {
            "key": "in_N",
            "value": str(params["in_N"]),
            "unit": "coefficients",
            "evidence_class": "SOURCE_PARSED",
            "source": "main.c",
        },
        {
            "key": "out_N",
            "value": str(params["out_N"]),
            "unit": "coefficients",
            "evidence_class": "SOURCE_PARSED",
            "source": "main.c",
        },
        {
            "key": "sigma_out",
            "value": "2^-50",
            "unit": "torus",
            "evidence_class": "SOURCE_PARSED",
            "source": "main.c",
        },
        {
            "key": "H",
            "value": str(params["H"]),
            "unit": "selector_events",
            "evidence_class": "DERIVED_EXACT",
            "source": "H=(h+1)*r_prec*in_N",
        },
        {
            "key": "historical_highstat_backend",
            "value": "spqlios_avx512-wsl",
            "unit": "",
            "evidence_class": "FROZEN_HISTORICAL_HIGHSTAT",
            "source": _B1_MATRIX,
        },
        {
            "key": "formal_performance_environment",
            "value": "NATIVE_LINUX_REQUIRED_NOT_YET_LOCAL",
            "unit": "",
            "evidence_class": "CLAIM_BOUNDARY",
            "source": (
                "docs/superpowers/specs/"
                "2026-07-20-lut-late-binding-operator-sab-design.md"
            ),
        },
        {
            "key": "wsl_smoke_claim_scope",
            "value": "CORRECTNESS_AND_SMOKE_ONLY_NOT_FORMAL_PERFORMANCE",
            "unit": "",
            "evidence_class": "CLAIM_BOUNDARY",
            "source": "reproduction_commands.md",
        },
        {
            "key": "wsl_smoke_disposition",
            "value": "ENVIRONMENT_BLOCKED",
            "unit": "",
            "evidence_class": "D0_EXECUTION_RECORD",
            "source": "task_2_execution",
        },
        {
            "key": "wsl_smoke_failure_reason",
            "value": (
                "ATTEMPT_INTERRUPTED_AFTER_TRACKED_STAGE33_OUTPUT_WRITE;"
                "NO_VALID_ISOLATED_SMOKE_RESULT"
            ),
            "unit": "",
            "evidence_class": "D0_EXECUTION_RECORD",
            "source": "task_2_execution",
        },
        {
            "key": "stage33_restoration",
            "value": "VERIFIED_1164B3F_GIT_BLOB_IDENTITY",
            "unit": "",
            "evidence_class": "D0_EXECUTION_RECORD",
            "source": (
                "repro/stage33_current_smoke/"
                "pvw_target_SET_2_3_2048/build.log;"
                "repro/stage33_current_smoke/"
                "scalar_binary_SET_2_3_2048/run.log"
            ),
        },
    )


def _baseline_document(
    anchors: tuple[BaselineAnchor, ...],
    params: Mapping[str, int | float],
    rows: tuple[Mapping[str, str], ...],
) -> str:
    by_id = {row["baseline_id"]: row for row in rows}
    anchor_lines = "\n".join(
        f"- `{anchor.path}` `{anchor.sha256}` ({anchor.role})"
        for anchor in anchors
    )
    return f"""# Candidate D D0 Baseline Freeze

Decision: `{D0_DECISION}`.

## Primary Metric

The primary metric is exactly `T_complete_bootstrap/(r*N_active)` in `us`.
For this frozen row, `N_active={params["in_N"]}`. Historical WSL high-stat
values remain frozen source evidence, but they are not formal native-Linux
performance. Newly executed WSL commands are correctness/smoke evidence only.

## Target Parameters

`in_N={params["in_N"]}`, `out_N={params["out_N"]}`,
`out_k={params["out_k"]}`, `l={params["l"]}`,
`bg_bit={params["bg_bit"]}`, `prec={params["prec"]}`, `h={params["h"]}`,
`r_prec={params["r_prec"]}`, `sigma_out=2^-50`, and
`H=(h+1)*r_prec*in_N={params["H"]}`.

## Frozen Baselines

| baseline | status | T_complete_bootstrap (us) | T/r (us) | T/(r*N_active) (us) |
| --- | --- | ---: | ---: | ---: |
| B0a repeated scalar | {by_id["B0a"]["status"]} | {by_id["B0a"]["t_complete_bootstrap_us"]} | {by_id["B0a"]["t_over_r_us"]} | {by_id["B0a"]["t_over_r_n_active_us"]} |
| B0b independent-mask shared-output-key control | {by_id["B0b"]["status"]} |  |  |  |
| B1 exact-dense PVW/MAT-SAB | {by_id["B1"]["status"]} | {by_id["B1"]["t_complete_bootstrap_us"]} | {by_id["B1"]["t_over_r_us"]} | {by_id["B1"]["t_over_r_n_active_us"]} |
| B2 relevant local BatchBoot composition | {by_id["B2"]["status"]} |  |  |  |

B1 uses `r=4`, has speedup `1.747647` versus B0a, and has pair failures
`0/10`. B0b and B2 are required but not yet local; neither is measured here.

## WSL Smoke Disposition

The D0 WSL smoke attempt is `ENVIRONMENT_BLOCKED`. It was interrupted after
writing tracked Stage 33 output, so it produced
`NO_VALID_ISOLATED_SMOKE_RESULT`. The two affected Stage 33 files were
restored and verified against their exact `1164b3f` Git blob identities.
No smoke timing is used as performance evidence.

## Immutable Anchors

{anchor_lines}
"""


def _reproduction_commands() -> str:
    return """# Candidate D D0 Reproduction Commands

These commands are executable correctness and smoke checks. WSL smoke timing
is not formal performance evidence. If WSL cannot execute, record
`ENVIRONMENT_BLOCKED`; do not alter the frozen high-stat rows.

The required Stage 33 command is recorded verbatim below. It writes to
`repro/stage33_current_smoke` by default; do not run it with the tracked Stage 33 output directory
in a source checkout. Use a disposable exact snapshot or override the output
directory:

```text
STAGE33_OUT_DIR=/tmp/candidate-d-stage33-smoke bash scripts/run_stage33_current_smoke.sh
```

The D0 attempt was interrupted after a tracked Stage 33 output write and is
recorded as `ENVIRONMENT_BLOCKED` with
`NO_VALID_ISOLATED_SMOKE_RESULT`. The affected frozen files were restored to
their exact `1164b3f` Git blobs.

```text
python -m unittest discover -s tests/research -v

bash scripts/run_stage33_current_smoke.sh

make FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false \\
  KEY=BINARY PARAM=SET_2_3_2048 \\
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \\
  MAT_TRGSW_AVX512_SUB_DECOMP=true \\
  MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true \\
  SAB_PVW_BACKEND_FROM_DFT_ADD=true \\
  SAB_PVW_SUB_DECOMP_FUSION=true \\
  SAB_PVW_DUAL_SUB_CMUX=true \\
  SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true \\
  SAB_PVW_TARGET_TEST=true -j$(nproc)
./main
```

Expected target smoke token:

```text
SAB_PVW target full bootstrap binary lane equivalence ... Pass
```
"""


def build_d0_artifacts(root: Path, out: Path) -> str:
    source_root = _resolved_root(root)
    anchors = validate_baseline_anchors(source_root)
    validate_terminal_predecessors(source_root)
    params = parse_target_parameters(source_root)
    if params != _EXPECTED_PARAMETERS:
        raise BaselineEvidenceError("target parameter values changed")
    summary, matrix = _validated_b1_row(source_root)
    rows = _metric_rows(anchors, summary, matrix)

    destination = Path(out)
    destination.mkdir(parents=True, exist_ok=True)
    _write_csv(
        destination
        / "repro/candidate_d_admission/baseline_manifest.csv",
        _MANIFEST_FIELDS,
        rows,
    )
    _write_csv(
        destination / "repro/candidate_d_admission/environment.csv",
        ("key", "value", "unit", "evidence_class", "source"),
        _environment_rows(params),
    )
    _write_text(
        destination
        / "repro/candidate_d_admission/reproduction_commands.md",
        _reproduction_commands(),
    )
    _write_text(
        destination / "docs/candidate_d_d0_baseline.md",
        _baseline_document(anchors, params, rows),
    )
    return D0_DECISION
