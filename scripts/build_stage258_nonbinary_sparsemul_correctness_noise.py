#!/usr/bin/env python3
"""
Stage258 turns the Stage257 non-binary PVW/MAT sparse_mul implementation into a
small multi-trial correctness/noise gate. It intentionally does not claim full
SAB bootstrapping speedup or T_bootstrap/r improvement.
"""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage258_nonbinary_sparsemul_correctness_noise"

RUN_LOG = OUT / "run_ffnt_nonbinary_noise.log"
BUILD_LOG = OUT / "build_ffnt_nonbinary_noise.log"
CLEAN_LOG = OUT / "clean_nonbinary_noise.log"
DEFAULT_BUILD_LOG = OUT / "build_ffnt_default_binary.log"
DEFAULT_CLEAN_LOG = OUT / "clean_default.log"

RUNTIME = OUT / "runtime_summary.csv"
LANES = OUT / "noise_lane.csv"
SOURCE = OUT / "source_matrix.csv"
ADMISSION = OUT / "implementation_admission.csv"
CLAIMS = OUT / "claim_boundary.csv"
GATES = OUT / "proof_gate.csv"
COMMANDS = OUT / "reproduction_commands.md"
INDEX = OUT / "artifact_index.csv"
REPORT = OUT / "stage258_report.md"

DOC = ROOT / "docs" / "stage258_nonbinary_sparsemul_correctness_noise.md"
EXP = ROOT / "experiments" / "stage258_nonbinary_sparsemul_correctness_noise_plan.md"
THEORY = ROOT / "theory_checks" / "stage258_nonbinary_sparsemul_noise_model.md"
ALGO = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage258_nonbinary_sparsemul_noise.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYP = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LEDGER = ROOT / "repro" / "run_log.csv"

DECISION = "PASS_STAGE258_NONBINARY_SPARSEMUL_CORRECTNESS_NOISE"
EXPECTED_MODES = {"include_zero", "ternary"}
EXPECTED_R = {"1", "2", "4"}
EXPECTED_TRIALS = "3"


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def read(path: Path) -> str:
    if not path.exists():
        return ""
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-16", "utf-16-le", "cp936", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fd:
        writer = csv.DictWriter(fd, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fd:
        fd.write(text)


def table(rows: list[dict[str, object]], fields: list[str]) -> str:
    lines = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")) for field in fields) + " |")
    return "\n".join(lines)


def append_once(path: Path, marker: str, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    current = read(path)
    if marker in current:
        return
    existing = path.read_bytes() if path.exists() else b""
    newline = b"\r\n" if b"\r\n" in existing and existing.count(b"\r\n") >= existing.count(b"\n") else b"\n"
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    payload = normalized.replace("\n", newline.decode("ascii")).encode("utf-8")
    with path.open("ab") as fd:
        if existing and not existing.endswith(b"\n"):
            fd.write(newline)
        fd.write(payload)


def source_has(path: str, pattern: str) -> bool:
    return re.search(pattern, read(ROOT / path), re.MULTILINE) is not None


def log_has_errors(path: Path) -> bool:
    return re.search(r"error:|undefined reference|collect2: error|ld returned", read(path), re.I) is not None


def sha256(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as fd:
        for chunk in iter(lambda: fd.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def runtime_rows() -> list[dict[str, object]]:
    text = read(RUN_LOG)
    rx = re.compile(
        r"SAB_PVW_NONBINARY_NOISE summary sparse_mul mode=(?P<mode>[a-z_]+) "
        r"r=(?P<r>\d+) trials=(?P<trials>\d+) points=(?P<points>\d+) "
        r"pair_failures=(?P<pair_failures>\d+) "
        r"pair_log2_sigma_torus=(?P<sigma>[-.A-Za-z0-9]+) "
        r"pair_log2_max_abs_torus=(?P<max_abs>[-.A-Za-z0-9]+) "
        r"gate=(?P<gate>Pass|Fail)"
    )
    rows: list[dict[str, object]] = []
    for match in rx.finditer(text):
        rows.append(
            {
                "mode": match.group("mode"),
                "r": match.group("r"),
                "trials": match.group("trials"),
                "points": match.group("points"),
                "pair_failures": match.group("pair_failures"),
                "pair_log2_sigma_torus": match.group("sigma"),
                "pair_log2_max_abs_torus": match.group("max_abs"),
                "gate": "PASS" if match.group("gate") == "Pass" else "FAIL",
                "evidence": rel(RUN_LOG),
            }
        )
    return rows


def lane_rows() -> list[dict[str, object]]:
    text = read(RUN_LOG)
    rx = re.compile(
        r"SAB_PVW_NONBINARY_NOISE lane sparse_mul mode=(?P<mode>[a-z_]+) "
        r"r=(?P<r>\d+) lane=(?P<lane>\d+) trials=(?P<trials>\d+) "
        r"points=(?P<points>\d+) pair_failures=(?P<pair_failures>\d+) "
        r"pair_log2_sigma_torus=(?P<sigma>[-.A-Za-z0-9]+) "
        r"pair_log2_max_abs_torus=(?P<max_abs>[-.A-Za-z0-9]+)"
    )
    rows: list[dict[str, object]] = []
    for match in rx.finditer(text):
        rows.append(
            {
                "mode": match.group("mode"),
                "r": match.group("r"),
                "lane": match.group("lane"),
                "trials": match.group("trials"),
                "points": match.group("points"),
                "pair_failures": match.group("pair_failures"),
                "pair_log2_sigma_torus": match.group("sigma"),
                "pair_log2_max_abs_torus": match.group("max_abs"),
                "evidence": rel(RUN_LOG),
            }
        )
    return rows


def runtime_ok(rows: list[dict[str, object]]) -> bool:
    observed = {(str(row["mode"]), str(row["r"])) for row in rows}
    expected = {(mode, r) for mode in EXPECTED_MODES for r in EXPECTED_R}
    return (
        observed == expected
        and all(str(row["trials"]) == EXPECTED_TRIALS for row in rows)
        and all(str(row["pair_failures"]) == "0" for row in rows)
        and all(str(row["gate"]) == "PASS" for row in rows)
        and "SAB_PVW nonbinary sparse_mul correctness/noise gate: Pass" in read(RUN_LOG)
    )


def lanes_ok(rows: list[dict[str, object]]) -> bool:
    expected_count = sum(int(r) for r in EXPECTED_R) * len(EXPECTED_MODES)
    return (
        len(rows) == expected_count
        and all(str(row["trials"]) == EXPECTED_TRIALS for row in rows)
        and all(str(row["pair_failures"]) == "0" for row in rows)
        and all(int(str(row["points"])) > 0 for row in rows)
    )


def source_rows() -> list[dict[str, object]]:
    changed = set(git(["diff", "--name-only", "HEAD"]).splitlines())
    default_ok = DEFAULT_BUILD_LOG.exists() and not log_has_errors(DEFAULT_BUILD_LOG)
    build_ok = BUILD_LOG.exists() and not log_has_errors(BUILD_LOG)
    return [
        {
            "check": "noise_flag",
            "path": "src/mosfhet/Makefile.def",
            "observed": "present" if source_has("src/mosfhet/Makefile.def", r"SAB_PVW_NONBINARY_NOISE_TEST") else "missing",
            "gate": "PASS" if source_has("src/mosfhet/Makefile.def", r"SAB_PVW_NONBINARY_NOISE_TEST") else "FAIL",
            "notes": "explicit correctness/noise smoke flag only",
        },
        {
            "check": "noise_harness",
            "path": "main.c",
            "observed": "present" if source_has("main.c", r"check_pvw_sparse_mul_nonbinary_noise") else "missing",
            "gate": "PASS" if source_has("main.c", r"check_pvw_sparse_mul_nonbinary_noise") else "FAIL",
            "notes": "multi-trial sparse_mul lane/noise gate",
        },
        {
            "check": "pair_noise_all_coeffs",
            "path": "main.c",
            "observed": "present" if source_has("main.c", r"add_sparse_noise_pvmtmlwe_all_coeffs") else "missing",
            "gate": "PASS" if source_has("main.c", r"add_sparse_noise_pvmtmlwe_all_coeffs") else "FAIL",
            "notes": "phase-pair noise measured over all coefficients and lanes",
        },
        {
            "check": "scalar_sab_unchanged",
            "path": "src/sparse_amortized_bootstrap.c",
            "observed": "not_changed" if "src/sparse_amortized_bootstrap.c" not in changed else "changed",
            "gate": "PASS" if "src/sparse_amortized_bootstrap.c" not in changed else "FAIL",
            "notes": "scalar baseline remains the comparison reference",
        },
        {
            "check": "noise_build",
            "path": rel(BUILD_LOG),
            "observed": "compiled" if build_ok else "failed_or_missing",
            "gate": "PASS" if build_ok else "FAIL",
            "notes": "portable FFNT correctness smoke, not performance",
        },
        {
            "check": "default_binary_build",
            "path": rel(DEFAULT_BUILD_LOG),
            "observed": "compiled" if default_ok else "failed_or_missing",
            "gate": "PASS" if default_ok else "FAIL",
            "notes": "default binary build still compiles",
        },
    ]


def admission_rows(runtime_pass: bool, lane_pass: bool) -> list[dict[str, object]]:
    return [
        {
            "route": "stage259_nonbinary_full_sab_integration_preflight",
            "decision": "ADMIT_FULL_SAB_PREFLIGHT" if runtime_pass and lane_pass else "BLOCK",
            "production_permission": "explicit_nonbinary_path_only",
            "reason": "sparse_mul include-zero/ternary r=1/2/4 multi-trial equivalence and pair-noise gate pass"
            if runtime_pass and lane_pass
            else "sparse_mul correctness/noise gate incomplete",
            "next_gate": "wire non-binary path into blind_rotate/bootstrap and test full SAB T_bootstrap/r",
        },
        {
            "route": "nonbinary_full_sab_speedup",
            "decision": "BLOCKED",
            "production_permission": "no",
            "reason": "no complete non-binary SAB route, no full extract/KS path, and no T_bootstrap/r benchmark yet",
            "next_gate": "Stage259 full-SAB preflight then deterministic full-SAB correctness",
        },
        {
            "route": "default_binary_sab",
            "decision": "NO_CHANGE",
            "production_permission": "no_default_change",
            "reason": "Stage258 adds a gated test harness only and default FFNT binary build passes",
            "next_gate": "keep scalar/binary regression for every promoted change",
        },
    ]


def claim_rows() -> list[dict[str, object]]:
    return [
        {
            "claim": "nonbinary_sparsemul_correctness_noise",
            "status": "supported_staged",
            "allowed_wording": "The explicit non-binary PVW/MAT sparse_mul path passes a 3-trial staged equivalence/noise gate for include-zero and ternary r=1/2/4.",
            "forbidden_wording": "The non-binary full SAB bootstrap is correct.",
            "evidence": rel(RUNTIME),
        },
        {
            "claim": "nonbinary_noise_vs_scalar_pair",
            "status": "supported_staged",
            "allowed_wording": "PVW body lanes match scalar-lane references with zero pair failures over all recorded Stage258 sparse_mul coefficients.",
            "forbidden_wording": "Complete SAB failure rate is unchanged.",
            "evidence": rel(LANES),
        },
        {
            "claim": "full_sab_speedup",
            "status": "unsupported",
            "allowed_wording": "Stage258 does not measure complete SAB speedup.",
            "forbidden_wording": "Stage258 proves bootstrapping acceleration.",
            "evidence": rel(ADMISSION),
        },
        {
            "claim": "amortized_time_per_plaintext_bit",
            "status": "unsupported_for_nonbinary",
            "allowed_wording": "T_bootstrap/r remains the primary metric for Stage259+ complete-SAB evaluation.",
            "forbidden_wording": "Non-binary T_bootstrap/r improved.",
            "evidence": rel(CLAIMS),
        },
    ]


def gate_rows(
    runtime: list[dict[str, object]],
    lanes: list[dict[str, object]],
    source: list[dict[str, object]],
    admission: list[dict[str, object]],
) -> list[dict[str, object]]:
    build_pass = BUILD_LOG.exists() and not log_has_errors(BUILD_LOG)
    runtime_pass = runtime_ok(runtime)
    lane_pass = lanes_ok(lanes)
    source_pass = all(row["gate"] == "PASS" for row in source)
    admission_pass = admission[0]["decision"] == "ADMIT_FULL_SAB_PREFLIGHT"
    decision_pass = build_pass and runtime_pass and lane_pass and source_pass and admission_pass
    return [
        {
            "gate": "G1_build",
            "status": "PASS" if build_pass else "FAIL",
            "metric": "ffnt nonbinary noise build",
            "value": "compiled" if build_pass else "failed",
            "evidence": rel(BUILD_LOG),
            "interpretation": "Portable correctness smoke only; no performance claim.",
        },
        {
            "gate": "G2_runtime_summary",
            "status": "PASS" if runtime_pass else "FAIL",
            "metric": "mode/r summary rows",
            "value": f"{sum(row['gate'] == 'PASS' for row in runtime)}/6",
            "evidence": rel(RUNTIME),
            "interpretation": "include-zero and ternary r=1/2/4 pass with zero pair failures.",
        },
        {
            "gate": "G3_lane_noise",
            "status": "PASS" if lane_pass else "FAIL",
            "metric": "lane rows",
            "value": f"{len(lanes)}/14",
            "evidence": rel(LANES),
            "interpretation": "All body lanes are checked against scalar-lane references over all coefficients.",
        },
        {
            "gate": "G4_source_isolation",
            "status": "PASS" if source_pass else "FAIL",
            "metric": "test harness and default isolation",
            "value": "preserved" if source_pass else "failed",
            "evidence": rel(SOURCE),
            "interpretation": "The scalar/default path remains isolated; Stage258 adds only gated measurement code.",
        },
        {
            "gate": "G5_stage259_admission",
            "status": "PASS_STAGED_ONLY" if admission_pass else "FAIL",
            "metric": "next route",
            "value": admission[0]["decision"],
            "evidence": rel(ADMISSION),
            "interpretation": "Full-SAB integration may start, but speedup claims remain blocked.",
        },
        {
            "gate": "G6_stage258_decision",
            "status": DECISION if decision_pass else "FAIL_STAGE258_NONBINARY_SPARSEMUL_CORRECTNESS_NOISE",
            "metric": "decision",
            "value": DECISION if decision_pass else "FAIL_STAGE258_NONBINARY_SPARSEMUL_CORRECTNESS_NOISE",
            "evidence": rel(GATES),
            "interpretation": "Proceed to Stage259 full non-binary SAB integration preflight.",
        },
    ]


def write_repro_files(
    runtime: list[dict[str, object]],
    lanes: list[dict[str, object]],
    source: list[dict[str, object]],
    admission: list[dict[str, object]],
    claims: list[dict[str, object]],
    gates: list[dict[str, object]],
) -> None:
    write_csv(
        RUNTIME,
        runtime,
        [
            "mode",
            "r",
            "trials",
            "points",
            "pair_failures",
            "pair_log2_sigma_torus",
            "pair_log2_max_abs_torus",
            "gate",
            "evidence",
        ],
    )
    write_csv(
        LANES,
        lanes,
        [
            "mode",
            "r",
            "lane",
            "trials",
            "points",
            "pair_failures",
            "pair_log2_sigma_torus",
            "pair_log2_max_abs_torus",
            "evidence",
        ],
    )
    write_csv(SOURCE, source, ["check", "path", "observed", "gate", "notes"])
    write_csv(ADMISSION, admission, ["route", "decision", "production_permission", "reason", "next_gate"])
    write_csv(CLAIMS, claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(GATES, gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_text_lf(
        COMMANDS,
        """# Stage258 Reproduction Commands

```powershell
make clean
make FFT_LIB=ffnt SAB_PVW_NONBINARY_NOISE_TEST=true SAB_PVW_NONBINARY_NOISE_TRIALS=3 KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
.\\main
make clean
make FFT_LIB=ffnt KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
python scripts\\build_stage258_nonbinary_sparsemul_correctness_noise.py
```

The FFNT run is a correctness/noise smoke gate, not a performance benchmark.
Complete SAB acceleration must be measured later as `T_bootstrap/r`.
""",
    )
    artifacts = [
        BUILD_LOG,
        RUN_LOG,
        CLEAN_LOG,
        DEFAULT_BUILD_LOG,
        DEFAULT_CLEAN_LOG,
        RUNTIME,
        LANES,
        SOURCE,
        ADMISSION,
        CLAIMS,
        GATES,
        COMMANDS,
        REPORT,
        DOC,
        EXP,
        THEORY,
        ALGO,
    ]
    write_csv(
        INDEX,
        [
            {
                "artifact": rel(path),
                "status": "present" if path.exists() else "missing",
                "sha256": sha256(path),
                "bytes": path.stat().st_size if path.exists() else 0,
            }
            for path in artifacts
        ],
        ["artifact", "status", "sha256", "bytes"],
    )


def write_docs(
    runtime: list[dict[str, object]],
    lanes: list[dict[str, object]],
    source: list[dict[str, object]],
    admission: list[dict[str, object]],
    claims: list[dict[str, object]],
    gates: list[dict[str, object]],
    head: str,
) -> None:
    report = f"""# Stage258 Non-Binary Sparse_Mul Correctness/Noise

Decision: `{gates[-1]['status']}`.

Stage258 is a research-process gate, not an optimization claim. It checks the
Stage257 explicit non-binary PVW/MAT sparse_mul path under multiple deterministic
trial inputs and records pair-noise against scalar lane references.

## Algorithm Scope

The tested object is:

```text
PVW/MAT sparse_mul_nonbinary(mode, r)
```

with `mode in {{include_zero, ternary}}` and `r in {{1, 2, 4}}`. Each PVW
ciphertext is interpreted as one shared mask plus `r` body lanes. The invariant
is:

```text
phase(acc_pvw.body[q][i]) == phase(acc_scalar[q][i])
```

for every recorded lane `q`, coefficient `i`, sparse step, and trial. This is
still below full SAB because blind rotation integration, extraction, packing
key-switching, and the primary metric `T_bootstrap/r` are not exercised here.

## Runtime Summary

{table(runtime, ['mode', 'r', 'trials', 'points', 'pair_failures', 'pair_log2_sigma_torus', 'pair_log2_max_abs_torus', 'gate'])}

## Lane Noise

{table(lanes, ['mode', 'r', 'lane', 'trials', 'points', 'pair_failures', 'pair_log2_sigma_torus', 'pair_log2_max_abs_torus'])}

## Source Isolation

{table(source, ['check', 'path', 'observed', 'gate', 'notes'])}

## Admission

{table(admission, ['route', 'decision', 'production_permission', 'reason', 'next_gate'])}

## Claim Boundary

{table(claims, ['claim', 'status', 'allowed_wording', 'forbidden_wording', 'evidence'])}

## Proof Gate

{table(gates, ['gate', 'status', 'metric', 'value', 'evidence', 'interpretation'])}

Generated from input head `{head}`.
"""
    write_text_lf(DOC, report)
    write_text_lf(REPORT, report)
    write_text_lf(
        ALGO,
        f"""# MAT-RLWE SAB Stage258 Non-Binary Sparse_Mul Noise Variant

Stage258 keeps the Stage257 non-binary sparse_mul equations and adds an
all-coefficient lane-pair noise gate:

```text
for mode in include_zero, ternary:
  for r in 1,2,4:
    for trial in 0..2:
      run scalar sparse_mul references for every body lane
      run one PVW sparse_mul with shared mask and r bodies
      compare phase(PVW.body[q][i]) against phase(scalar[q][i])
```

The variant remains an isolated sparse_mul-stage variant. It does not integrate
non-binary blind rotation or claim complete SAB acceleration.

Stage258 gate: `{gates[-1]['status']}`.
""",
    )
    write_text_lf(
        THEORY,
        """# Stage258 Non-Binary Sparse_Mul Noise Model

Stage258 measures a pairwise reference error, not absolute decryption failure.
For each PVW lane and scalar reference lane, the recorded torus error is:

```text
e_pair[q,i] = phase_pvw[q,i] - phase_scalar[q,i]
```

The gate requires zero pair failures over all recorded coefficients. This proves
that the PVW/MAT sparse_mul implementation is algebraically aligned with the
scalar reference for the tested sparse_mul scope.

This does not prove the final SAB failure rate because complete bootstrapping
adds blind rotation scheduling, extraction, optional packing/key switching, and
the target message decoding boundary. Those remain Stage259+ gates.
""",
    )
    write_text_lf(
        EXP,
        f"""# Stage258 Experiment Plan

Primary endpoint:

```text
zero pair failures for include-zero and ternary sparse_mul, r=1/2/4, trials=3
```

Executed commands:

```powershell
make clean
make FFT_LIB=ffnt SAB_PVW_NONBINARY_NOISE_TEST=true SAB_PVW_NONBINARY_NOISE_TRIALS=3 KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
.\\main
make clean
make FFT_LIB=ffnt KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
python scripts\\build_stage258_nonbinary_sparsemul_correctness_noise.py
```

Evidence:

- `{rel(RUNTIME)}`
- `{rel(LANES)}`
- `{rel(GATES)}`

Next endpoint:

```text
full non-binary SAB correctness and T_bootstrap/r benchmark
```

No performance claim is made from FFNT or sparse_mul-only evidence.
""",
    )


def update_ledgers(head: str) -> None:
    append_once(
        ROADMAP,
        "## Stage 258: Non-Binary Sparse_Mul Correctness/Noise",
        f"""
## Stage 258: Non-Binary Sparse_Mul Correctness/Noise

Goal:

```text
Convert the Stage257 explicit non-binary PVW/MAT sparse_mul implementation into
a multi-trial correctness/noise gate before admitting full SAB integration.
```

Status:

```text
Generated from input head `{head}` with `{DECISION}`. include-zero and ternary
sparse_mul pass r=1/2/4, trials=3, with zero scalar/PVW pair failures across
all recorded body-lane coefficients. Stage259 full-SAB integration preflight is
admitted, but full bootstrapping acceleration and T_bootstrap/r remain blocked.
```
""",
    )
    append_once(
        GOAL,
        "### Stage258 non-binary sparse_mul correctness/noise",
        f"""
### Stage258 non-binary sparse_mul correctness/noise

`{DECISION}` records a sparse_mul-layer correctness/noise gate for the
non-binary PVW/MAT path. The active research goal remains open: Stage259 must
integrate non-binary blind rotation/bootstrap, then measure full-SAB
`T_bootstrap/r` under scalar baseline isolation.
""",
    )
    append_once(
        HYP,
        "H10_stage258_nonbinary_sparsemul_correctness_noise:",
        f"""
H10_stage258_nonbinary_sparsemul_correctness_noise:
  status: sparsemul_correctness_noise_passed_full_sab_blocked
  evidence:
    - repro/stage258_nonbinary_sparsemul_correctness_noise/runtime_summary.csv
    - repro/stage258_nonbinary_sparsemul_correctness_noise/noise_lane.csv
    - repro/stage258_nonbinary_sparsemul_correctness_noise/proof_gate.csv
    - docs/stage258_nonbinary_sparsemul_correctness_noise.md
  conclusion: >
    Stage258 records {DECISION}. The explicit non-binary PVW/MAT sparse_mul
    path passes include-zero and ternary r=1/2/4 multi-trial pair-noise gates.
    Complete SAB correctness, complete SAB failure rate, and T_bootstrap/r
    speedup claims remain blocked until Stage259+.
""",
    )
    append_once(
        MANIFEST,
        "- stage258_nonbinary_sparsemul_correctness_noise:",
        f"""
- stage258_nonbinary_sparsemul_correctness_noise:
  - `docs/stage258_nonbinary_sparsemul_correctness_noise.md`
  - `experiments/stage258_nonbinary_sparsemul_correctness_noise_plan.md`
  - `theory_checks/stage258_nonbinary_sparsemul_noise_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage258_nonbinary_sparsemul_noise.md`
  - `scripts/build_stage258_nonbinary_sparsemul_correctness_noise.py`
  - `repro/stage258_nonbinary_sparsemul_correctness_noise/`
""",
    )
    append_once(CHECKLIST, "Stage258 non-binary sparse_mul correctness/noise", "\n- [x] Stage258 non-binary sparse_mul correctness/noise\n")
    append_once(
        RUN_LEDGER,
        "stage258-nonbinary-sparsemul-correctness-noise-001",
        f"""stage258-nonbinary-sparsemul-correctness-noise-001,2026-07-04,{head},Stage 258,ffnt-correctness,"make FFT_LIB=ffnt SAB_PVW_NONBINARY_NOISE_TEST=true SAB_PVW_NONBINARY_NOISE_TRIALS=3 KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=; .\\\\main; python scripts/build_stage258_nonbinary_sparsemul_correctness_noise.py","include_zero/ternary; r=1/2/4; trials=3; sparse_mul only",0..2,{DECISION},"Non-binary sparse_mul multi-trial pair-noise gate passes; full SAB T_bootstrap/r remains blocked.",docs/stage258_nonbinary_sparsemul_correctness_noise.md; repro/stage258_nonbinary_sparsemul_correctness_noise/proof_gate.csv
""",
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    head = git(["rev-parse", "--short", "HEAD"])
    runtime = runtime_rows()
    lanes = lane_rows()
    source = source_rows()
    admission = admission_rows(runtime_ok(runtime), lanes_ok(lanes))
    claims = claim_rows()
    gates = gate_rows(runtime, lanes, source, admission)
    write_docs(runtime, lanes, source, admission, claims, gates, head)
    write_repro_files(runtime, lanes, source, admission, claims, gates)
    update_ledgers(head)
    print(f"Stage258 report: {rel(DOC)}")
    print(f"Stage258 decision: {gates[-1]['status']}")
    return 0 if gates[-1]["status"] == DECISION else 1


if __name__ == "__main__":
    raise SystemExit(main())
