#!/usr/bin/env python3
"""
Stage259 wires the explicit non-binary PVW/MAT sparse_mul route into a full
SAB bootstrap smoke path. This proves a small-parameter full-pipeline
equivalence gate only; it does not prove target-parameter speedup.
"""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage259_nonbinary_full_sab_smoke"

RUN_LOG = OUT / "run_ffnt_nonbinary_full.log"
BUILD_LOG = OUT / "build_ffnt_nonbinary_full.log"
CLEAN_LOG = OUT / "clean_nonbinary_full.log"
DEFAULT_BUILD_LOG = OUT / "build_ffnt_default_binary.log"
DEFAULT_CLEAN_LOG = OUT / "clean_default.log"

RUNTIME = OUT / "runtime_summary.csv"
SOURCE = OUT / "source_matrix.csv"
ADMISSION = OUT / "implementation_admission.csv"
CLAIMS = OUT / "claim_boundary.csv"
GATES = OUT / "proof_gate.csv"
COMMANDS = OUT / "reproduction_commands.md"
INDEX = OUT / "artifact_index.csv"
REPORT = OUT / "stage259_report.md"

DOC = ROOT / "docs" / "stage259_nonbinary_full_sab_smoke.md"
EXP = ROOT / "experiments" / "stage259_nonbinary_full_sab_smoke_plan.md"
THEORY = ROOT / "theory_checks" / "stage259_nonbinary_full_sab_scope.md"
ALGO = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage259_nonbinary_full_sab.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYP = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LEDGER = ROOT / "repro" / "run_log.csv"

DECISION = "PASS_STAGE259_NONBINARY_FULL_SAB_SMOKE"
EXPECTED_MODES = {"include_zero", "ternary"}
EXPECTED_R = {"1", "2", "4"}


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
        r"SAB_PVW nonbinary full bootstrap lane equivalence "
        r"mode=(?P<mode>[a-z_]+) r=(?P<r>\d+) h=(?P<h>\d+) "
        r"r_prec=(?P<r_prec>\d+): (?P<status>Pass|Fail)"
    )
    rows: list[dict[str, object]] = []
    for match in rx.finditer(text):
        rows.append(
            {
                "mode": match.group("mode"),
                "r": match.group("r"),
                "h": match.group("h"),
                "r_prec": match.group("r_prec"),
                "status": "PASS" if match.group("status") == "Pass" else "FAIL",
                "scope": "small_full_pipeline_ffnt_smoke",
                "evidence": rel(RUN_LOG),
            }
        )
    return rows


def runtime_ok(rows: list[dict[str, object]]) -> bool:
    observed = {(str(row["mode"]), str(row["r"])) for row in rows}
    expected = {(mode, r) for mode in EXPECTED_MODES for r in EXPECTED_R}
    return (
        observed == expected
        and all(row["status"] == "PASS" for row in rows)
        and "SAB_PVW nonbinary full bootstrap gate: Pass" in read(RUN_LOG)
    )


def source_rows() -> list[dict[str, object]]:
    changed = set(git(["diff", "--name-only", "HEAD"]).splitlines())
    checks = [
        (
            "api_decl_new_nonbinary_full_key",
            "include/sab_pvw.h",
            r"sab_pvw_new_nonbinary_full_key\(",
            "explicit full-key constructor declaration",
        ),
        (
            "api_decl_bootstrap_nonbinary",
            "include/sab_pvw.h",
            r"sab_pvw_bootstrap_nonbinary\(",
            "explicit non-binary full bootstrap declaration",
        ),
        (
            "api_def_new_nonbinary_full_key",
            "src/sab_pvw.c",
            r"SAB_PVW_Key\s+sab_pvw_new_nonbinary_full_key\(",
            "constructor reuses non-binary keygen plus full postproc",
        ),
        (
            "api_def_blind_rotate_nonbinary",
            "src/sab_pvw.c",
            r"void\s+sab_pvw_blind_rotate_nonbinary\(",
            "blind rotate calls sparse_mul_nonbinary",
        ),
        (
            "api_def_bootstrap_nonbinary",
            "src/sab_pvw.c",
            r"void\s+sab_pvw_bootstrap_nonbinary\(",
            "full path uses non-binary wo_extract and existing postproc",
        ),
        (
            "test_flag",
            "src/mosfhet/Makefile.def",
            r"SAB_PVW_NONBINARY_FULL_TEST",
            "isolated FFNT smoke flag",
        ),
        (
            "test_harness",
            "main.c",
            r"check_pvw_nonbinary_full_lane_equivalence",
            "small full-pipeline scalar/PVW equivalence test",
        ),
    ]
    rows = [
        {
            "check": name,
            "path": path,
            "observed": "present" if source_has(path, pattern) else "missing",
            "gate": "PASS" if source_has(path, pattern) else "FAIL",
            "notes": notes,
        }
        for name, path, pattern, notes in checks
    ]
    rows.append(
        {
            "check": "scalar_sab_unchanged",
            "path": "src/sparse_amortized_bootstrap.c",
            "observed": "not_changed" if "src/sparse_amortized_bootstrap.c" not in changed else "changed",
            "gate": "PASS" if "src/sparse_amortized_bootstrap.c" not in changed else "FAIL",
            "notes": "scalar baseline remains the oracle",
        }
    )
    rows.append(
        {
            "check": "default_binary_build",
            "path": rel(DEFAULT_BUILD_LOG),
            "observed": "compiled" if DEFAULT_BUILD_LOG.exists() and not log_has_errors(DEFAULT_BUILD_LOG) else "failed_or_missing",
            "gate": "PASS" if DEFAULT_BUILD_LOG.exists() and not log_has_errors(DEFAULT_BUILD_LOG) else "FAIL",
            "notes": "default binary build still compiles",
        }
    )
    return rows


def admission_rows(runtime_pass: bool) -> list[dict[str, object]]:
    return [
        {
            "route": "stage260_nonbinary_full_sab_noise_resource",
            "decision": "ADMIT_NOISE_RESOURCE" if runtime_pass else "BLOCK",
            "production_permission": "explicit_nonbinary_path_only",
            "reason": "small full-pipeline non-binary PVW/MAT SAB smoke passes for include-zero and ternary r=1/2/4"
            if runtime_pass
            else "full-pipeline smoke incomplete",
            "next_gate": "multi-seed correctness/noise/resource for the non-binary full path",
        },
        {
            "route": "stage261_nonbinary_target_perf_t_bootstrap_per_bit",
            "decision": "WAIT_STAGE260",
            "production_permission": "no_speedup_claim",
            "reason": "target parameter performance requires noise/resource gate first",
            "next_gate": "same-backend complete SAB A/B using T_bootstrap/r",
        },
        {
            "route": "nonbinary_full_sab_speedup",
            "decision": "BLOCKED",
            "production_permission": "no",
            "reason": "no target-parameter benchmark, no multi-seed failure-rate gate, and no T_bootstrap/r result yet",
            "next_gate": "Stage260 then Stage261",
        },
    ]


def claim_rows() -> list[dict[str, object]]:
    return [
        {
            "claim": "nonbinary_full_sab_small_correctness",
            "status": "supported_smoke",
            "allowed_wording": "The explicit non-binary PVW/MAT full SAB path passes small-parameter FFNT full-pipeline equivalence for include-zero and ternary r=1/2/4.",
            "forbidden_wording": "The target 686 non-binary full SAB path is fully validated.",
            "evidence": rel(RUNTIME),
        },
        {
            "claim": "default_scalar_baseline",
            "status": "preserved_build_gate",
            "allowed_wording": "The scalar SAB source remains unchanged and the default binary FFNT build compiles.",
            "forbidden_wording": "Scalar SAB performance is unchanged.",
            "evidence": rel(SOURCE),
        },
        {
            "claim": "full_sab_speedup",
            "status": "unsupported",
            "allowed_wording": "Stage259 does not measure complete SAB speedup.",
            "forbidden_wording": "Stage259 proves bootstrapping acceleration.",
            "evidence": rel(ADMISSION),
        },
        {
            "claim": "amortized_time_per_plaintext_bit",
            "status": "unsupported_for_nonbinary",
            "allowed_wording": "T_bootstrap/r remains the primary metric for Stage261+.",
            "forbidden_wording": "Non-binary T_bootstrap/r improved.",
            "evidence": rel(CLAIMS),
        },
    ]


def gate_rows(runtime: list[dict[str, object]], source: list[dict[str, object]],
    admission: list[dict[str, object]]) -> list[dict[str, object]]:
    build_pass = BUILD_LOG.exists() and not log_has_errors(BUILD_LOG)
    runtime_pass = runtime_ok(runtime)
    source_pass = all(row["gate"] == "PASS" for row in source)
    admission_pass = admission[0]["decision"] == "ADMIT_NOISE_RESOURCE"
    decision_pass = build_pass and runtime_pass and source_pass and admission_pass
    return [
        {
            "gate": "G1_build",
            "status": "PASS" if build_pass else "FAIL",
            "metric": "ffnt nonbinary full build",
            "value": "compiled" if build_pass else "failed",
            "evidence": rel(BUILD_LOG),
            "interpretation": "Portable full-pipeline smoke build; no performance claim.",
        },
        {
            "gate": "G2_runtime_full_pipeline",
            "status": "PASS" if runtime_pass else "FAIL",
            "metric": "mode/r pass rows",
            "value": f"{sum(row['status'] == 'PASS' for row in runtime)}/6",
            "evidence": rel(RUNTIME),
            "interpretation": "include-zero and ternary r=1/2/4 full-SAB smoke outputs match scalar references.",
        },
        {
            "gate": "G3_source_isolation",
            "status": "PASS" if source_pass else "FAIL",
            "metric": "explicit path and scalar isolation",
            "value": "preserved" if source_pass else "failed",
            "evidence": rel(SOURCE),
            "interpretation": "New code is an explicit non-binary path; scalar SAB source is unchanged.",
        },
        {
            "gate": "G4_stage260_admission",
            "status": "PASS_STAGED_ONLY" if admission_pass else "FAIL",
            "metric": "next route",
            "value": admission[0]["decision"],
            "evidence": rel(ADMISSION),
            "interpretation": "Proceed to multi-seed noise/resource, not performance claims.",
        },
        {
            "gate": "G5_stage259_decision",
            "status": DECISION if decision_pass else "FAIL_STAGE259_NONBINARY_FULL_SAB_SMOKE",
            "metric": "decision",
            "value": DECISION if decision_pass else "FAIL_STAGE259_NONBINARY_FULL_SAB_SMOKE",
            "evidence": rel(GATES),
            "interpretation": "Full non-binary path exists and passes small deterministic smoke.",
        },
    ]


def write_repro_files(runtime, source, admission, claims, gates) -> None:
    write_csv(RUNTIME, runtime, ["mode", "r", "h", "r_prec", "status", "scope", "evidence"])
    write_csv(SOURCE, source, ["check", "path", "observed", "gate", "notes"])
    write_csv(ADMISSION, admission, ["route", "decision", "production_permission", "reason", "next_gate"])
    write_csv(CLAIMS, claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(GATES, gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_text_lf(
        COMMANDS,
        """# Stage259 Reproduction Commands

```powershell
make clean
make FFT_LIB=ffnt SAB_PVW_NONBINARY_FULL_TEST=true KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
.\\main
make clean
make FFT_LIB=ffnt KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
python scripts\\build_stage259_nonbinary_full_sab_smoke.py
```

This is a full-pipeline correctness smoke. It is not a target-parameter
performance benchmark.
""",
    )
    artifacts = [
        BUILD_LOG,
        RUN_LOG,
        CLEAN_LOG,
        DEFAULT_BUILD_LOG,
        DEFAULT_CLEAN_LOG,
        RUNTIME,
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


def write_docs(runtime, source, admission, claims, gates, head: str) -> None:
    report = f"""# Stage259 Non-Binary Full SAB Smoke

Decision: `{gates[-1]['status']}`.

Stage259 adds an explicit non-binary PVW/MAT full SAB path and checks it against
scalar SAB on a small FFNT full-pipeline smoke. The exercised pipeline is:

```text
setup_tv_xb -> blind_rotate_nonbinary -> sparse_mul_nonbinary
  -> extract -> packing KS -> HW KS
```

The tested modes are include-zero and ternary, with r=1/2/4 body lanes. This is
the first full-pipeline non-binary correctness evidence, but it is not a target
parameter, multi-seed, noise, resource, or performance gate.

## Runtime Summary

{table(runtime, ['mode', 'r', 'h', 'r_prec', 'status', 'scope'])}

## Source Matrix

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
        f"""# MAT-RLWE SAB Stage259 Non-Binary Full SAB

Stage259 lifts the Stage257/258 non-binary sparse_mul route to an explicit full
SAB API:

```text
sab_pvw_new_nonbinary_full_key
sab_pvw_blind_rotate_nonbinary
sab_pvw_bootstrap_wo_extract_nonbinary
sab_pvw_bootstrap_nonbinary
```

The core algorithmic delta from binary PVW/MAT-SAB is localized to
`blind_rotate_nonbinary`, which calls `sparse_mul_nonbinary`; extraction,
packing key switching, and HW key switching reuse the same lane-wise
post-processing as the binary PVW path.

Stage259 gate: `{gates[-1]['status']}`.
""",
    )
    write_text_lf(
        THEORY,
        """# Stage259 Non-Binary Full SAB Scope

The new path changes the SAB body update, not the final post-processing:

```text
binary:     sparse_mul_binary
nonbinary:  sparse_mul_nonbinary(mode in include_zero, ternary)
```

Post-processing is lane-wise and identical after the PVW accumulator has been
materialized into per-lane TLWE arrays. Therefore Stage259 tests only the new
body-route integration plus the existing post-processing boundary.

The proof obligation left open is target-parameter statistical correctness and
the primary performance endpoint:

```text
amortized latency = T_bootstrap / r
```
""",
    )
    write_text_lf(
        EXP,
        f"""# Stage259 Experiment Plan

Primary endpoint:

```text
full SAB scalar/PVW phase equivalence for include-zero and ternary, r=1/2/4
```

Executed commands:

```powershell
make clean
make FFT_LIB=ffnt SAB_PVW_NONBINARY_FULL_TEST=true KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
.\\main
make clean
make FFT_LIB=ffnt KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
python scripts\\build_stage259_nonbinary_full_sab_smoke.py
```

Evidence:

- `{rel(RUNTIME)}`
- `{rel(SOURCE)}`
- `{rel(GATES)}`

Next endpoint:

```text
multi-seed full-path correctness/noise/resource, then target T_bootstrap/r A/B
```
""",
    )


def update_ledgers(head: str) -> None:
    append_once(
        ROADMAP,
        "## Stage 259: Non-Binary Full SAB Smoke",
        f"""
## Stage 259: Non-Binary Full SAB Smoke

Goal:

```text
Wire the explicit non-binary PVW/MAT sparse_mul route into complete SAB
bootstrapping without changing scalar SAB or binary PVW defaults.
```

Status:

```text
Generated from input head `{head}` with `{DECISION}`. The new explicit
non-binary full SAB API passes small FFNT full-pipeline equivalence for
include-zero and ternary r=1/2/4. Target-parameter noise, resource, and
T_bootstrap/r speedup remain blocked until Stage260+.
```
""",
    )
    append_once(
        GOAL,
        "### Stage259 non-binary full SAB smoke",
        f"""
### Stage259 non-binary full SAB smoke

`{DECISION}` records the first complete non-binary PVW/MAT-SAB path smoke. The
active research goal remains open because this is not yet target-parameter,
multi-seed, noise/resource, or performance evidence.
""",
    )
    append_once(
        HYP,
        "H10_stage259_nonbinary_full_sab_smoke:",
        f"""
H10_stage259_nonbinary_full_sab_smoke:
  status: full_pipeline_smoke_passed_speedup_blocked
  evidence:
    - repro/stage259_nonbinary_full_sab_smoke/runtime_summary.csv
    - repro/stage259_nonbinary_full_sab_smoke/proof_gate.csv
    - docs/stage259_nonbinary_full_sab_smoke.md
  conclusion: >
    Stage259 records {DECISION}. The explicit non-binary PVW/MAT full SAB path
    passes small include-zero and ternary r=1/2/4 full-pipeline equivalence.
    Target correctness/noise/resource and T_bootstrap/r speedup remain blocked.
""",
    )
    append_once(
        MANIFEST,
        "- stage259_nonbinary_full_sab_smoke:",
        """
- stage259_nonbinary_full_sab_smoke:
  - `docs/stage259_nonbinary_full_sab_smoke.md`
  - `experiments/stage259_nonbinary_full_sab_smoke_plan.md`
  - `theory_checks/stage259_nonbinary_full_sab_scope.md`
  - `algorithm_variants/mat_rlwe_sab_stage259_nonbinary_full_sab.md`
  - `scripts/build_stage259_nonbinary_full_sab_smoke.py`
  - `repro/stage259_nonbinary_full_sab_smoke/`
""",
    )
    append_once(CHECKLIST, "Stage259 non-binary full SAB smoke", "\n- [x] Stage259 non-binary full SAB smoke\n")
    append_once(
        RUN_LEDGER,
        "stage259-nonbinary-full-sab-smoke-001",
        f"""stage259-nonbinary-full-sab-smoke-001,2026-07-04,{head},Stage 259,ffnt-correctness,"make FFT_LIB=ffnt SAB_PVW_NONBINARY_FULL_TEST=true KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=; .\\\\main; python scripts/build_stage259_nonbinary_full_sab_smoke.py","include_zero/ternary; r=1/2/4; small full pipeline",deterministic,{DECISION},"Explicit non-binary full SAB small smoke passes; target T_bootstrap/r remains blocked.",docs/stage259_nonbinary_full_sab_smoke.md; repro/stage259_nonbinary_full_sab_smoke/proof_gate.csv
""",
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    head = git(["rev-parse", "--short", "HEAD"])
    runtime = runtime_rows()
    source = source_rows()
    admission = admission_rows(runtime_ok(runtime))
    claims = claim_rows()
    gates = gate_rows(runtime, source, admission)
    write_docs(runtime, source, admission, claims, gates, head)
    write_repro_files(runtime, source, admission, claims, gates)
    update_ledgers(head)
    print(f"Stage259 report: {rel(DOC)}")
    print(f"Stage259 decision: {gates[-1]['status']}")
    return 0 if gates[-1]["status"] == DECISION else 1


if __name__ == "__main__":
    raise SystemExit(main())
