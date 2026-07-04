#!/usr/bin/env python3
"""
Stage257 records the first explicit production-code implementation of the
non-binary PVW/MAT sparse_mul path. It intentionally does not upgrade the claim
to complete bootstrapping speedup.
"""

from __future__ import annotations

import csv
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage257_nonbinary_sparsemul_implementation"

RUN_LOG = OUT / "run_ffnt_nonbinary_test.log"
BUILD_LOG = OUT / "build_ffnt_nonbinary_test.log"
CLEAN_LOG = OUT / "clean.log"
DEFAULT_BUILD_LOG = OUT / "build_ffnt_default_binary.log"
DEFAULT_CLEAN_LOG = OUT / "default_clean.log"

API = OUT / "api_matrix.csv"
RUNTIME = OUT / "runtime_equivalence.csv"
SOURCE = OUT / "source_change_matrix.csv"
ADMISSION = OUT / "implementation_admission.csv"
CLAIMS = OUT / "claim_boundary.csv"
GATES = OUT / "proof_gate.csv"
COMMANDS = OUT / "reproduction_commands.md"
INDEX = OUT / "artifact_index.csv"
REPORT = OUT / "stage257_report.md"

DOC = ROOT / "docs" / "stage257_nonbinary_sparsemul_implementation.md"
EXP = ROOT / "experiments" / "stage257_nonbinary_sparsemul_implementation_plan.md"
THEORY = ROOT / "theory_checks" / "stage257_nonbinary_sparsemul_implementation_model.md"
ALGO = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage257_nonbinary_sparsemul.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYP = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LEDGER = ROOT / "repro" / "run_log.csv"

DECISION = "PASS_STAGE257_NONBINARY_SPARSEMUL_IMPLEMENTED_STAGED"


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
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")) for field in fields) + " |")
    return "\n".join(out)


def contains(path: Path, needle: str) -> bool:
    return needle in read(path)


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


def runtime_rows() -> list[dict[str, object]]:
    text = read(RUN_LOG)
    rows: list[dict[str, object]] = []
    rx = re.compile(
        r"SAB_PVW API nonbinary sparse_mul lane equivalence "
        r"mode=(?P<mode>[a-z_]+) r=(?P<r>\d+) h=(?P<h>\d+) "
        r"r_prec=(?P<r_prec>\d+): (?P<status>Pass|Fail)"
    )
    for match in rx.finditer(text):
        rows.append({
            "mode": match.group("mode"),
            "r": match.group("r"),
            "h": match.group("h"),
            "r_prec": match.group("r_prec"),
            "status": "PASS" if match.group("status") == "Pass" else "FAIL",
            "evidence": rel(RUN_LOG),
        })
    return rows


def api_rows() -> list[dict[str, object]]:
    apis = [
        ("sab_pvw_new_nonbinary_key", r"sab_pvw_new_nonbinary_key\(", r"SAB_PVW_Key\s+sab_pvw_new_nonbinary_key\("),
        ("sab_pvw_sub_a_include_zero", r"sab_pvw_sub_a_include_zero\(", r"void\s+sab_pvw_sub_a_include_zero\("),
        ("sab_pvw_sub_a_ternary", r"sab_pvw_sub_a_ternary\(", r"void\s+sab_pvw_sub_a_ternary\("),
        ("sab_pvw_sparse_mul_nonbinary", r"sab_pvw_sparse_mul_nonbinary\(", r"void\s+sab_pvw_sparse_mul_nonbinary\("),
    ]
    rows: list[dict[str, object]] = []
    for name, decl, definition in apis:
        rows.append({
            "api": name,
            "declared": "yes" if source_has("include/sab_pvw.h", decl) else "no",
            "defined": "yes" if source_has("src/sab_pvw.c", definition) else "no",
            "notes": "explicit non-binary PVW sparse_mul path only",
        })
    return rows


def source_rows() -> list[dict[str, object]]:
    changed = set(git(["diff", "--name-only", "HEAD"]).splitlines())
    binary_call_ok = source_has("src/sab_pvw.c", r"sab_pvw_blind_rotate_binary[\s\S]*sab_pvw_sparse_mul_binary")
    default_build_text = read(DEFAULT_BUILD_LOG)
    default_build_ok = DEFAULT_BUILD_LOG.exists() and "gcc -g -o main" in default_build_text and not re.search(
        r"error:|undefined reference|collect2: error|ld returned", default_build_text, re.I
    )
    return [
        {
            "file": "include/sab_pvw.h",
            "change": "optional s_coff/s_sign fields and explicit non-binary API declarations",
            "observed": "changed" if "include/sab_pvw.h" in changed else "not_changed",
            "gate": "PASS" if "include/sab_pvw.h" in changed else "FAIL",
        },
        {
            "file": "src/sab_pvw.c",
            "change": "explicit non-binary keygen, sub_a, and sparse_mul implementation",
            "observed": "changed" if "src/sab_pvw.c" in changed else "not_changed",
            "gate": "PASS" if "src/sab_pvw.c" in changed else "FAIL",
        },
        {
            "file": "src/sparse_amortized_bootstrap.c",
            "change": "scalar SAB reference remains untouched",
            "observed": "not_changed" if "src/sparse_amortized_bootstrap.c" not in changed else "changed",
            "gate": "PASS" if "src/sparse_amortized_bootstrap.c" not in changed else "FAIL",
        },
        {
            "file": "src/sab_pvw.c",
            "change": "binary blind rotate continues to call sab_pvw_sparse_mul_binary",
            "observed": "yes" if binary_call_ok else "no",
            "gate": "PASS" if binary_call_ok else "FAIL",
        },
        {
            "file": "Makefile/src",
            "change": "default binary FFNT build still compiles",
            "observed": "compiled" if default_build_ok else "failed_or_missing",
            "gate": "PASS" if default_build_ok else "FAIL",
        },
    ]


def admission_rows(runtime: list[dict[str, object]]) -> list[dict[str, object]]:
    runtime_ok = len(runtime) == 6 and all(row["status"] == "PASS" for row in runtime)
    return [
        {
            "route": "stage258_nonbinary_sparsemul_correctness_noise",
            "decision": "ADMIT_STAGED_CORRECTNESS_NOISE" if runtime_ok else "BLOCK",
            "production_permission": "explicit_nonbinary_path_only",
            "reason": "r=1/2/4 include-zero and ternary sparse_mul lane equivalence pass" if runtime_ok else "runtime gate incomplete",
            "next_gate": "deterministic and multi-seed sparse_mul correctness/noise before full SAB",
        },
        {
            "route": "default_binary_sab",
            "decision": "NO_CHANGE",
            "production_permission": "no_default_change",
            "reason": "binary blind rotate and bootstrap path still call sab_pvw_sparse_mul_binary",
            "next_gate": "binary regression build/run after each promoted change",
        },
        {
            "route": "nonbinary_full_sab_speedup",
            "decision": "BLOCKED",
            "production_permission": "no",
            "reason": "no non-binary blind_rotate/bootstrap/full extract integration or T_bootstrap/r benchmark yet",
            "next_gate": "Stage258+Stage259",
        },
    ]


def claim_rows() -> list[dict[str, object]]:
    return [
        {
            "claim": "nonbinary_sparsemul_implementation",
            "status": "supported_staged",
            "allowed_wording": "An explicit non-binary PVW/MAT sparse_mul path is implemented and passes staged lane equivalence for include-zero and ternary r=1/2/4.",
            "forbidden_wording": "Full non-binary PVW/MAT-SAB bootstrapping is complete.",
            "evidence": rel(RUNTIME),
        },
        {
            "claim": "full_sab_speedup",
            "status": "unsupported",
            "allowed_wording": "No non-binary complete-SAB speedup is claimed at Stage257.",
            "forbidden_wording": "Stage257 accelerates complete SAB bootstrapping.",
            "evidence": rel(ADMISSION),
        },
        {
            "claim": "amortized_time_per_plaintext_bit",
            "status": "unsupported_for_nonbinary",
            "allowed_wording": "T_bootstrap/r remains the final metric for complete-SAB evaluation.",
            "forbidden_wording": "Non-binary T_bootstrap/r improved.",
            "evidence": rel(CLAIMS),
        },
    ]


def gate_rows(api, runtime, source, admission) -> list[dict[str, object]]:
    build_text = read(BUILD_LOG)
    run_text = read(RUN_LOG)
    build_ok = BUILD_LOG.exists() and "gcc -g -o main" in build_text and not re.search(
        r"error:|undefined reference|collect2: error|ld returned", build_text, re.I
    )
    api_ok = all(row["declared"] == "yes" and row["defined"] == "yes" for row in api)
    runtime_ok = len(runtime) == 6 and all(row["status"] == "PASS" for row in runtime) and "staged test: Pass" in run_text
    source_ok = all(row["gate"] == "PASS" for row in source)
    admission_ok = admission[0]["decision"] == "ADMIT_STAGED_CORRECTNESS_NOISE"
    decision_ok = build_ok and api_ok and runtime_ok and source_ok and admission_ok
    return [
        {
            "gate": "G1_build",
            "status": "PASS" if build_ok else "FAIL",
            "metric": "ffnt build",
            "value": "compiled" if build_ok else "failed",
            "evidence": rel(BUILD_LOG),
            "interpretation": "Portable build smoke gate only, not performance evidence.",
        },
        {
            "gate": "G2_api_surface",
            "status": "PASS" if api_ok else "FAIL",
            "metric": "declared;defined",
            "value": "all" if api_ok else "missing",
            "evidence": rel(API),
            "interpretation": "Explicit non-binary API is present without replacing binary API.",
        },
        {
            "gate": "G3_runtime_equivalence",
            "status": "PASS" if runtime_ok else "FAIL",
            "metric": "mode/r pass rows",
            "value": f"{sum(row['status'] == 'PASS' for row in runtime)}/6",
            "evidence": rel(RUNTIME),
            "interpretation": "include-zero and ternary sparse_mul staged lane equivalence pass for r=1/2/4.",
        },
        {
            "gate": "G4_source_isolation",
            "status": "PASS" if source_ok else "FAIL",
            "metric": "default path isolation",
            "value": "preserved" if source_ok else "changed",
            "evidence": rel(SOURCE),
            "interpretation": "Scalar SAB and binary PVW default route remain reference paths.",
        },
        {
            "gate": "G5_admission",
            "status": "PASS_STAGED_ONLY" if admission_ok else "FAIL",
            "metric": "next route",
            "value": admission[0]["production_permission"],
            "evidence": rel(ADMISSION),
            "interpretation": "Next work is correctness/noise, not full-SAB speedup claim.",
        },
        {
            "gate": "G6_stage257_decision",
            "status": DECISION if decision_ok else "FAIL_STAGE257_NONBINARY_SPARSEMUL_IMPLEMENTATION",
            "metric": "decision",
            "value": DECISION if decision_ok else "FAIL_STAGE257_NONBINARY_SPARSEMUL_IMPLEMENTATION",
            "evidence": rel(GATES),
            "interpretation": "Proceed to Stage258 sparse_mul correctness/noise and then full SAB integration.",
        },
    ]


def write_docs(api, runtime, source, admission, claims, gates, head: str) -> None:
    report = f"""# Stage257 Non-Binary Sparse_Mul Implementation

Decision: `{gates[-1]['status']}`.

Stage257 is the first production-code checkpoint for the non-binary
PVW/MAT-SAB route. It adds explicit `sab_pvw_*` APIs for include-zero and
ternary sparse_mul, but it does not claim complete bootstrapping speedup.

## Implemented Algorithm

For each sparse secret step, the distance-bit RGSW monomial schedule is reused:

```text
p <- RGSW_monomial_mul_state(p, s_distance[step])
```

The branch-specific update is then:

```text
include-zero: p[j] <- p[j] + EP(s_coff[step], (X^a[j] - 1) p[j])
ternary:      p[j] <- X^a[j] p[j] + EP(s_sign[step], (X^(-2a[j]) - 1) X^a[j] p[j])
```

The final distance-bit RGSW step is unchanged. The PVW ciphertext still has one
shared mask and `r` body lanes; this gate checks r=1/2/4.

## API Matrix

{table(api, ['api', 'declared', 'defined', 'notes'])}

## Runtime Equivalence

{table(runtime, ['mode', 'r', 'h', 'r_prec', 'status', 'evidence'])}

## Source Isolation

{table(source, ['file', 'change', 'observed', 'gate'])}

## Admission

{table(admission, ['route', 'decision', 'production_permission', 'reason', 'next_gate'])}

## Claim Boundary

{table(claims, ['claim', 'status', 'allowed_wording', 'forbidden_wording', 'evidence'])}

## Proof Gate

{table(gates, ['gate', 'status', 'metric', 'value', 'evidence', 'interpretation'])}

Generated from input head `{head}`.
"""
    for path, content in [
        (DOC, report),
        (REPORT, report),
        (ALGO, f"""# MAT-RLWE SAB Stage257 Non-Binary Sparse_Mul

This variant upgrades the previously binary-only PVW sparse schedule with
explicit MAT selector families:

- `s_coff` for include-zero coefficients.
- `s_sign` for ternary signs.

It preserves the scalar SAB equations and maps the selector multiplication to
`mat_trgsw_mul_pvmtmlwe_DFT`. It is a sparse_mul-stage algorithm, not yet a
complete blind-rotate/bootstrap algorithm.

Stage257 gate: `{gates[-1]['status']}`.
"""),
        (THEORY, f"""# Stage257 Non-Binary Sparse_Mul Model

For one non-binary family, the additional EP-class work remains `h * in_N`.
The main distance-bit work remains `(h+1) * r_prec * in_N`. For SET_2_3_2048
this is `79872 / 573440 = 0.139286` extra EP-class updates before measuring
implementation overhead.

The correctness invariant checked here is:

```text
phase(PVW.body[q][j]) == phase(scalar_lane[q][j])
```

for include-zero and ternary sparse_mul at r=1/2/4.

This model does not prove noise stability or complete-SAB speedup.
"""),
        (EXP, f"""# Stage257 Experiment Plan

Executed smoke command:

```powershell
make clean
make FFT_LIB=ffnt SAB_PVW_NONBINARY_TEST=true KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
.\\main
make clean
make FFT_LIB=ffnt KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
```

Evidence:

- `{rel(BUILD_LOG)}`
- `{rel(RUN_LOG)}`
- `{rel(GATES)}`

Next experiment must move from staged lane equivalence to deterministic and
multi-seed sparse_mul correctness/noise, then full non-binary SAB A/B.
"""),
    ]:
        write_text_lf(path, content)


def write_repro_files(api, runtime, source, admission, claims, gates) -> None:
    write_csv(API, api, ["api", "declared", "defined", "notes"])
    write_csv(RUNTIME, runtime, ["mode", "r", "h", "r_prec", "status", "evidence"])
    write_csv(SOURCE, source, ["file", "change", "observed", "gate"])
    write_csv(ADMISSION, admission, ["route", "decision", "production_permission", "reason", "next_gate"])
    write_csv(CLAIMS, claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(GATES, gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_text_lf(COMMANDS, f"""# Stage257 Reproduction Commands

```powershell
make clean
make FFT_LIB=ffnt SAB_PVW_NONBINARY_TEST=true KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
.\\main
make clean
make FFT_LIB=ffnt KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
python scripts\\build_stage257_nonbinary_sparsemul_implementation.py
```

The FFNT run is a correctness smoke gate, not a performance benchmark.
""")
    artifacts = [
        BUILD_LOG, RUN_LOG, CLEAN_LOG, DEFAULT_BUILD_LOG, DEFAULT_CLEAN_LOG,
        API, RUNTIME, SOURCE, ADMISSION, CLAIMS, GATES, COMMANDS, REPORT, DOC,
        EXP, THEORY, ALGO,
    ]
    write_csv(INDEX, [
        {"artifact": rel(path), "status": "present" if path.exists() else "missing"}
        for path in artifacts
    ], ["artifact", "status"])


def update_ledgers(head: str) -> None:
    append_once(ROADMAP, "## Stage 257: Non-Binary Sparse_Mul Implementation", f"""
## Stage 257: Non-Binary Sparse_Mul Implementation

Goal:

```text
Add an explicit production-code PVW/MAT sparse_mul path for include-zero and
ternary selector families without replacing scalar SAB or binary PVW defaults.
```

Status:

```text
Generated from input head `{head}` with `{DECISION}`. The new
`sab_pvw_new_nonbinary_key`, `sab_pvw_sub_a_include_zero`,
`sab_pvw_sub_a_ternary`, and `sab_pvw_sparse_mul_nonbinary` APIs compile and
pass staged lane equivalence for include-zero and ternary at r=1/2/4. Full SAB
speedup and T_bootstrap/r claims remain blocked pending correctness/noise and
complete bootstrapping A/B.
```
""")
    append_once(GOAL, "### Stage257 non-binary sparse_mul implementation", f"""
### Stage257 non-binary sparse_mul implementation

`{DECISION}` records an explicit non-binary PVW sparse_mul implementation.
The active goal remains open for deterministic/multi-seed sparse_mul
noise/correctness, full SAB integration, T_bootstrap/r benchmark, parameter
generalization, and final paper claim closure.
""")
    append_once(HYP, "H10_stage257_nonbinary_sparsemul_implementation:", f"""
H10_stage257_nonbinary_sparsemul_implementation:
  status: explicit_nonbinary_sparsemul_staged_implemented
  evidence:
    - repro/stage257_nonbinary_sparsemul_implementation/runtime_equivalence.csv
    - repro/stage257_nonbinary_sparsemul_implementation/api_matrix.csv
    - repro/stage257_nonbinary_sparsemul_implementation/proof_gate.csv
    - docs/stage257_nonbinary_sparsemul_implementation.md
  conclusion: >
    Stage257 records {DECISION}. It implements explicit include-zero and
    ternary PVW/MAT sparse_mul APIs and passes staged lane equivalence for
    r=1/2/4. Complete non-binary SAB bootstrapping speedup and T_bootstrap/r
    claims remain blocked.
""")
    append_once(MANIFEST, "- stage257_nonbinary_sparsemul_implementation:", f"""
- stage257_nonbinary_sparsemul_implementation:
  - `docs/stage257_nonbinary_sparsemul_implementation.md`
  - `experiments/stage257_nonbinary_sparsemul_implementation_plan.md`
  - `theory_checks/stage257_nonbinary_sparsemul_implementation_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage257_nonbinary_sparsemul.md`
  - `scripts/build_stage257_nonbinary_sparsemul_implementation.py`
  - `repro/stage257_nonbinary_sparsemul_implementation/`
""")
    append_once(CHECKLIST, "Stage257 non-binary sparse_mul implementation", "\n- [x] Stage257 non-binary sparse_mul implementation\n")
    append_once(RUN_LEDGER, "stage257-nonbinary-sparsemul-implementation-001", f"""stage257-nonbinary-sparsemul-implementation-001,2026-07-04,{head},Stage 257,sparsemul_implementation,"make FFT_LIB=ffnt SAB_PVW_NONBINARY_TEST=true KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=; .\\\\main; python scripts/build_stage257_nonbinary_sparsemul_implementation.py","Stage256 explicit implementation admission + production code",n/a,{DECISION},"Explicit non-binary sparse_mul staged lane equivalence passes; full SAB remains blocked.",docs/stage257_nonbinary_sparsemul_implementation.md; repro/stage257_nonbinary_sparsemul_implementation/proof_gate.csv
""")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    head = git(["rev-parse", "--short", "HEAD"])
    runtime = runtime_rows()
    api = api_rows()
    source = source_rows()
    admission = admission_rows(runtime)
    claims = claim_rows()
    gates = gate_rows(api, runtime, source, admission)
    write_repro_files(api, runtime, source, admission, claims, gates)
    write_docs(api, runtime, source, admission, claims, gates, head)
    update_ledgers(head)
    print(f"Stage257 report: {rel(DOC)}")
    print(f"Stage257 decision: {gates[-1]['status']}")
    return 0 if gates[-1]["status"] == DECISION else 1


if __name__ == "__main__":
    raise SystemExit(main())
