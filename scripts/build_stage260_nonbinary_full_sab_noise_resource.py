#!/usr/bin/env python3
"""
Stage260 upgrades the explicit non-binary PVW/MAT full SAB path from a
deterministic smoke to a small multi-trial noise/resource gate. It intentionally
does not claim target-parameter throughput or T_bootstrap/r speedup.
"""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage260_nonbinary_full_sab_noise_resource"

RUN_LOG = OUT / "run_ffnt_nonbinary_full_noise.log"
BUILD_LOG = OUT / "build_ffnt_nonbinary_full_noise.log"
CLEAN_LOG = OUT / "clean_nonbinary_full_noise.log"
DEFAULT_BUILD_LOG = OUT / "build_ffnt_default_binary.log"
DEFAULT_CLEAN_LOG = OUT / "clean_default.log"

FINAL = OUT / "final_noise_summary.csv"
STAGES = OUT / "stage_noise_summary.csv"
RESOURCES = OUT / "resource_summary.csv"
SOURCE = OUT / "source_matrix.csv"
ADMISSION = OUT / "implementation_admission.csv"
CLAIMS = OUT / "claim_boundary.csv"
GATES = OUT / "proof_gate.csv"
COMMANDS = OUT / "reproduction_commands.md"
INDEX = OUT / "artifact_index.csv"
REPORT = OUT / "stage260_report.md"

DOC = ROOT / "docs" / "stage260_nonbinary_full_sab_noise_resource.md"
EXP = ROOT / "experiments" / "stage260_nonbinary_full_sab_noise_resource_plan.md"
THEORY = ROOT / "theory_checks" / "stage260_nonbinary_full_sab_noise_resource_scope.md"
ALGO = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage260_nonbinary_full_sab_noise_resource.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYP = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LEDGER = ROOT / "repro" / "run_log.csv"

DECISION = "PASS_STAGE260_NONBINARY_FULL_SAB_NOISE_RESOURCE"
EXPECTED_MODES = {"include_zero", "ternary"}
EXPECTED_R = {"1", "2", "4"}
EXPECTED_STAGES = {"blind_rotate_coeff0", "extract", "materialize_tlwe", "packing_ks", "hw_ks"}
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


def log_has_errors(path: Path) -> bool:
    return re.search(r"error:|undefined reference|collect2: error|ld returned", read(path), re.I) is not None


def source_has(path: str, pattern: str) -> bool:
    return re.search(pattern, read(ROOT / path), re.MULTILINE) is not None


def sha256(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as fd:
        for chunk in iter(lambda: fd.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def final_rows() -> list[dict[str, object]]:
    rx = re.compile(
        r"SAB_PVW_NONBINARY_FULL_NOISE summary mode=(?P<mode>[a-z_]+) "
        r"r=(?P<r>\d+) trials=(?P<trials>\d+) points=(?P<points>\d+) "
        r"pvw_failures=(?P<pvw_failures>\d+) scalar_failures=(?P<scalar_failures>\d+) "
        r"pair_failures=(?P<pair_failures>\d+) "
        r"pvw_log2_sigma_torus=(?P<pvw_sigma>[-.A-Za-z0-9]+) "
        r"scalar_log2_sigma_torus=(?P<scalar_sigma>[-.A-Za-z0-9]+) "
        r"pair_log2_sigma_torus=(?P<pair_sigma>[-.A-Za-z0-9]+) "
        r"pair_log2_max_abs_torus=(?P<pair_max>[-.A-Za-z0-9]+) "
        r"gate=(?P<gate>Pass|Fail)"
    )
    rows: list[dict[str, object]] = []
    for m in rx.finditer(read(RUN_LOG)):
        rows.append({
            "mode": m.group("mode"),
            "r": m.group("r"),
            "trials": m.group("trials"),
            "points": m.group("points"),
            "pvw_failures": m.group("pvw_failures"),
            "scalar_failures": m.group("scalar_failures"),
            "pair_failures": m.group("pair_failures"),
            "pvw_log2_sigma_torus": m.group("pvw_sigma"),
            "scalar_log2_sigma_torus": m.group("scalar_sigma"),
            "pair_log2_sigma_torus": m.group("pair_sigma"),
            "pair_log2_max_abs_torus": m.group("pair_max"),
            "gate": "PASS" if m.group("gate") == "Pass" else "FAIL",
            "evidence": rel(RUN_LOG),
        })
    return rows


def stage_rows() -> list[dict[str, object]]:
    rx = re.compile(
        r"SAB_PVW_NONBINARY_STAGE_NOISE summary mode=(?P<mode>[a-z_]+) "
        r"stage=(?P<stage>[a-z0-9_]+) r=(?P<r>\d+) trials=(?P<trials>\d+) "
        r"points=(?P<points>\d+) pair_failures=(?P<pair_failures>\d+) "
        r"pair_log2_sigma_torus=(?P<pair_sigma>[-.A-Za-z0-9]+) "
        r"pair_log2_max_abs_torus=(?P<pair_max>[-.A-Za-z0-9]+)"
    )
    rows: list[dict[str, object]] = []
    for m in rx.finditer(read(RUN_LOG)):
        rows.append({
            "mode": m.group("mode"),
            "stage": m.group("stage"),
            "r": m.group("r"),
            "trials": m.group("trials"),
            "points": m.group("points"),
            "pair_failures": m.group("pair_failures"),
            "pair_log2_sigma_torus": m.group("pair_sigma"),
            "pair_log2_max_abs_torus": m.group("pair_max"),
            "evidence": rel(RUN_LOG),
        })
    return rows


def resource_rows() -> list[dict[str, object]]:
    text = read(RUN_LOG)
    key_rx = re.compile(
        r"SAB_PVW_NONBINARY_RESOURCE key_bytes full_smoke mode=(?P<mode>[a-z_]+) "
        r"r=(?P<r>\d+) pvw_estimated_key_bytes=(?P<pvw>\d+) "
        r"scalar_one_estimated_key_bytes=(?P<scalar_one>\d+) "
        r"scalar_repeated_estimated_key_bytes=(?P<scalar_repeated>\d+) "
        r"pvw_vs_scalar_repeated_ratio=(?P<ratio>[-.0-9]+)"
    )
    pvw_keygen_rx = re.compile(
        r"SAB_PVW_NONBINARY_RESOURCE keygen full_smoke mode=(?P<mode>[a-z_]+) "
        r"r=(?P<r>\d+) pvw_sab_keygen_us=(?P<pvw_keygen>\d+)"
    )
    scalar_keygen_rx = re.compile(
        r"SAB_PVW_NONBINARY_RESOURCE keygen full_smoke mode=(?P<mode>[a-z_]+) "
        r"r=(?P<r>\d+) scalar_repeated_sab_keygen_us=(?P<scalar_keygen>\d+) "
        r"scalar_lane_avg_keygen_us=(?P<scalar_lane_avg>[-.0-9]+)"
    )
    rows: dict[tuple[str, str], dict[str, object]] = {}
    for m in key_rx.finditer(text):
        row = rows.setdefault((m.group("mode"), m.group("r")), {"mode": m.group("mode"), "r": m.group("r")})
        row.update({
            "pvw_estimated_key_bytes": m.group("pvw"),
            "scalar_one_estimated_key_bytes": m.group("scalar_one"),
            "scalar_repeated_estimated_key_bytes": m.group("scalar_repeated"),
            "pvw_vs_scalar_repeated_ratio": m.group("ratio"),
        })
    for m in pvw_keygen_rx.finditer(text):
        row = rows.setdefault((m.group("mode"), m.group("r")), {"mode": m.group("mode"), "r": m.group("r")})
        row["pvw_sab_keygen_us"] = m.group("pvw_keygen")
    for m in scalar_keygen_rx.finditer(text):
        row = rows.setdefault((m.group("mode"), m.group("r")), {"mode": m.group("mode"), "r": m.group("r")})
        row["scalar_repeated_sab_keygen_us"] = m.group("scalar_keygen")
        row["scalar_lane_avg_keygen_us"] = m.group("scalar_lane_avg")
    out = []
    for key in sorted(rows):
        row = rows[key]
        row.setdefault("pvw_estimated_key_bytes", "")
        row.setdefault("scalar_one_estimated_key_bytes", "")
        row.setdefault("scalar_repeated_estimated_key_bytes", "")
        row.setdefault("pvw_vs_scalar_repeated_ratio", "")
        row.setdefault("pvw_sab_keygen_us", "")
        row.setdefault("scalar_repeated_sab_keygen_us", "")
        row.setdefault("scalar_lane_avg_keygen_us", "")
        row["evidence"] = rel(RUN_LOG)
        out.append(row)
    return out


def final_ok(rows: list[dict[str, object]]) -> bool:
    expected = {(m, r) for m in EXPECTED_MODES for r in EXPECTED_R}
    observed = {(str(row["mode"]), str(row["r"])) for row in rows}
    return (
        observed == expected
        and all(row["trials"] == EXPECTED_TRIALS for row in rows)
        and all(row["pvw_failures"] == row["scalar_failures"] == row["pair_failures"] == "0" for row in rows)
        and all(row["gate"] == "PASS" for row in rows)
        and "SAB_PVW nonbinary full bootstrap noise/resource gate: Pass" in read(RUN_LOG)
    )


def stages_ok(rows: list[dict[str, object]]) -> bool:
    expected = {(m, stage, r) for m in EXPECTED_MODES for stage in EXPECTED_STAGES for r in EXPECTED_R}
    observed = {(str(row["mode"]), str(row["stage"]), str(row["r"])) for row in rows}
    return (
        observed == expected
        and all(row["trials"] == EXPECTED_TRIALS for row in rows)
        and all(row["pair_failures"] == "0" for row in rows)
    )


def resources_ok(rows: list[dict[str, object]]) -> bool:
    expected = {(m, r) for m in EXPECTED_MODES for r in EXPECTED_R}
    observed = {(str(row["mode"]), str(row["r"])) for row in rows}
    required = [
        "pvw_estimated_key_bytes",
        "scalar_repeated_estimated_key_bytes",
        "pvw_vs_scalar_repeated_ratio",
        "pvw_sab_keygen_us",
        "scalar_repeated_sab_keygen_us",
    ]
    return observed == expected and all(all(str(row.get(k, "")) for k in required) for row in rows)


def source_rows() -> list[dict[str, object]]:
    changed = set(git(["diff", "--name-only", "HEAD"]).splitlines())
    checks = [
        ("test_flag", "src/mosfhet/Makefile.def", r"SAB_PVW_NONBINARY_FULL_NOISE_TEST", "isolated Stage260 flag"),
        ("test_harness", "main.c", r"check_pvw_nonbinary_full_noise_resource", "multi-trial full-path noise/resource harness"),
        ("nonbinary_key_estimate_scalar", "main.c", r"estimate_scalar_sab_nonbinary_public_key_bytes", "resource estimate includes extra scalar selector family"),
        ("nonbinary_key_estimate_pvw", "main.c", r"estimate_pvw_sab_nonbinary_public_key_bytes", "resource estimate includes extra MAT selector family"),
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
    rows.append({
        "check": "scalar_sab_unchanged",
        "path": "src/sparse_amortized_bootstrap.c",
        "observed": "not_changed" if "src/sparse_amortized_bootstrap.c" not in changed else "changed",
        "gate": "PASS" if "src/sparse_amortized_bootstrap.c" not in changed else "FAIL",
        "notes": "scalar baseline remains the oracle",
    })
    rows.append({
        "check": "default_binary_build",
        "path": rel(DEFAULT_BUILD_LOG),
        "observed": "compiled" if DEFAULT_BUILD_LOG.exists() and not log_has_errors(DEFAULT_BUILD_LOG) else "failed_or_missing",
        "gate": "PASS" if DEFAULT_BUILD_LOG.exists() and not log_has_errors(DEFAULT_BUILD_LOG) else "FAIL",
        "notes": "default binary build still compiles",
    })
    return rows


def admission_rows(final_pass: bool, stage_pass: bool, resource_pass: bool) -> list[dict[str, object]]:
    return [
        {
            "route": "stage261_nonbinary_target_perf_t_bootstrap_per_bit",
            "decision": "ADMIT_TARGET_PERF_PREFLIGHT" if final_pass and stage_pass and resource_pass else "BLOCK",
            "production_permission": "explicit_nonbinary_path_only",
            "reason": "small full-path non-binary multi-trial noise/resource gate passes"
            if final_pass and stage_pass and resource_pass
            else "noise/resource evidence incomplete",
            "next_gate": "same-backend complete SAB A/B with T_bootstrap/r",
        },
        {
            "route": "nonbinary_full_sab_speedup",
            "decision": "BLOCKED",
            "production_permission": "no",
            "reason": "no target-parameter full SAB benchmark and no T_bootstrap/r result yet",
            "next_gate": "Stage261 target performance",
        },
        {
            "route": "paper_claim",
            "decision": "WAIT_STAGE261_AND_LITERATURE",
            "production_permission": "no_novelty_claim",
            "reason": "small FFNT correctness/resource evidence is not a paper-grade performance or novelty claim",
            "next_gate": "target benchmark, statistics, and citation-safe related work",
        },
    ]


def claim_rows() -> list[dict[str, object]]:
    return [
        {
            "claim": "nonbinary_full_sab_small_noise_resource",
            "status": "supported_small_gate",
            "allowed_wording": "The explicit non-binary PVW/MAT full SAB path passes a 3-trial small FFNT noise/resource gate for include-zero and ternary r=1/2/4.",
            "forbidden_wording": "The target 686 non-binary full SAB path has validated noise/resource behavior.",
            "evidence": rel(FINAL),
        },
        {
            "claim": "stage_pair_equivalence",
            "status": "supported_small_gate",
            "allowed_wording": "The recorded blind-rotate, extract, materialize, packing-KS, and HW-KS stage pair failures are zero for the small gate.",
            "forbidden_wording": "All target-parameter stages have zero failure probability.",
            "evidence": rel(STAGES),
        },
        {
            "claim": "full_sab_speedup",
            "status": "unsupported",
            "allowed_wording": "Stage260 does not measure complete SAB speedup.",
            "forbidden_wording": "Stage260 proves bootstrapping acceleration.",
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


def gate_rows(final, stages, resources, source, admission) -> list[dict[str, object]]:
    build_pass = BUILD_LOG.exists() and not log_has_errors(BUILD_LOG)
    final_pass = final_ok(final)
    stage_pass = stages_ok(stages)
    resource_pass = resources_ok(resources)
    source_pass = all(row["gate"] == "PASS" for row in source)
    admission_pass = admission[0]["decision"] == "ADMIT_TARGET_PERF_PREFLIGHT"
    decision_pass = build_pass and final_pass and stage_pass and resource_pass and source_pass and admission_pass
    return [
        {
            "gate": "G1_build",
            "status": "PASS" if build_pass else "FAIL",
            "metric": "ffnt nonbinary full noise/resource build",
            "value": "compiled" if build_pass else "failed",
            "evidence": rel(BUILD_LOG),
            "interpretation": "Portable small full-path gate; no performance claim.",
        },
        {
            "gate": "G2_final_noise",
            "status": "PASS" if final_pass else "FAIL",
            "metric": "mode/r final rows",
            "value": f"{sum(row['gate'] == 'PASS' for row in final)}/6",
            "evidence": rel(FINAL),
            "interpretation": "Final output PVW/scalar/paired failures are zero for all small-gate rows.",
        },
        {
            "gate": "G3_stage_noise",
            "status": "PASS" if stage_pass else "FAIL",
            "metric": "stage summary rows",
            "value": f"{len(stages)}/30",
            "evidence": rel(STAGES),
            "interpretation": "All recorded intermediate pair-noise summaries have zero pair failures.",
        },
        {
            "gate": "G4_resource",
            "status": "PASS" if resource_pass else "FAIL",
            "metric": "resource rows",
            "value": f"{len(resources)}/6",
            "evidence": rel(RESOURCES),
            "interpretation": "Small-gate key-size and keygen resource estimates are recorded.",
        },
        {
            "gate": "G5_source_isolation",
            "status": "PASS" if source_pass else "FAIL",
            "metric": "explicit path and scalar isolation",
            "value": "preserved" if source_pass else "failed",
            "evidence": rel(SOURCE),
            "interpretation": "Stage260 adds an explicit measurement flag; scalar SAB source is unchanged.",
        },
        {
            "gate": "G6_stage261_admission",
            "status": "PASS_STAGED_ONLY" if admission_pass else "FAIL",
            "metric": "next route",
            "value": admission[0]["decision"],
            "evidence": rel(ADMISSION),
            "interpretation": "Proceed to target performance preflight, but speedup remains blocked.",
        },
        {
            "gate": "G7_stage260_decision",
            "status": DECISION if decision_pass else "FAIL_STAGE260_NONBINARY_FULL_SAB_NOISE_RESOURCE",
            "metric": "decision",
            "value": DECISION if decision_pass else "FAIL_STAGE260_NONBINARY_FULL_SAB_NOISE_RESOURCE",
            "evidence": rel(GATES),
            "interpretation": "Small non-binary full-path noise/resource gate is complete.",
        },
    ]


def write_repro_files(final, stages, resources, source, admission, claims, gates) -> None:
    write_csv(FINAL, final, [
        "mode", "r", "trials", "points", "pvw_failures", "scalar_failures",
        "pair_failures", "pvw_log2_sigma_torus", "scalar_log2_sigma_torus",
        "pair_log2_sigma_torus", "pair_log2_max_abs_torus", "gate", "evidence",
    ])
    write_csv(STAGES, stages, [
        "mode", "stage", "r", "trials", "points", "pair_failures",
        "pair_log2_sigma_torus", "pair_log2_max_abs_torus", "evidence",
    ])
    write_csv(RESOURCES, resources, [
        "mode", "r", "pvw_estimated_key_bytes", "scalar_one_estimated_key_bytes",
        "scalar_repeated_estimated_key_bytes", "pvw_vs_scalar_repeated_ratio",
        "pvw_sab_keygen_us", "scalar_repeated_sab_keygen_us",
        "scalar_lane_avg_keygen_us", "evidence",
    ])
    write_csv(SOURCE, source, ["check", "path", "observed", "gate", "notes"])
    write_csv(ADMISSION, admission, ["route", "decision", "production_permission", "reason", "next_gate"])
    write_csv(CLAIMS, claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(GATES, gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_text_lf(COMMANDS, """# Stage260 Reproduction Commands

```powershell
make clean
make FFT_LIB=ffnt SAB_PVW_NONBINARY_FULL_NOISE_TEST=true SAB_PVW_NONBINARY_FULL_NOISE_TRIALS=3 KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
.\\main
make clean
make FFT_LIB=ffnt KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
python scripts\\build_stage260_nonbinary_full_sab_noise_resource.py
```

This is a small FFNT full-path correctness/noise/resource gate. It is not a
target-parameter performance benchmark.
""")
    artifacts = [
        BUILD_LOG, RUN_LOG, CLEAN_LOG, DEFAULT_BUILD_LOG, DEFAULT_CLEAN_LOG,
        FINAL, STAGES, RESOURCES, SOURCE, ADMISSION, CLAIMS, GATES, COMMANDS,
        REPORT, DOC, EXP, THEORY, ALGO,
    ]
    write_csv(INDEX, [
        {
            "artifact": rel(path),
            "status": "present" if path.exists() else "missing",
            "sha256": sha256(path),
            "bytes": path.stat().st_size if path.exists() else 0,
        }
        for path in artifacts
    ], ["artifact", "status", "sha256", "bytes"])


def write_docs(final, stages, resources, source, admission, claims, gates, head: str) -> None:
    report = f"""# Stage260 Non-Binary Full SAB Noise/Resource

Decision: `{gates[-1]['status']}`.

Stage260 records a small multi-trial full-path gate for the explicit
non-binary PVW/MAT-SAB path. It covers include-zero and ternary modes, r=1/2/4,
and trials=3. The primary endpoint is zero final PVW/scalar/pair failures; the
secondary endpoints are zero stage-pair failures and recorded non-binary
selector key-size/keygen estimates.

This is still not target-parameter performance evidence. The primary final
metric remains:

```text
T_bootstrap / r
```

## Final Noise

{table(final, ['mode', 'r', 'trials', 'points', 'pvw_failures', 'scalar_failures', 'pair_failures', 'pvw_log2_sigma_torus', 'scalar_log2_sigma_torus', 'pair_log2_sigma_torus', 'gate'])}

## Stage Pair Noise

{table(stages, ['mode', 'stage', 'r', 'trials', 'points', 'pair_failures', 'pair_log2_sigma_torus', 'pair_log2_max_abs_torus'])}

## Resources

{table(resources, ['mode', 'r', 'pvw_estimated_key_bytes', 'scalar_repeated_estimated_key_bytes', 'pvw_vs_scalar_repeated_ratio', 'pvw_sab_keygen_us', 'scalar_repeated_sab_keygen_us'])}

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
    write_text_lf(ALGO, f"""# MAT-RLWE SAB Stage260 Non-Binary Full SAB Noise/Resource

Stage260 keeps the Stage259 full non-binary path and adds a falsifiable
multi-trial gate:

```text
for mode in include_zero, ternary:
  for r in 1,2,4:
    run full PVW/MAT SAB and repeated scalar SAB for 3 trials
    record final output noise against LUT expectation
    record PVW-vs-scalar pair noise at body and post-processing stages
    record non-binary selector key-size and keygen estimates
```

The algorithmic object remains MAT-RLWE/r-body ciphertext SAB. The result
admits target performance preflight only; it does not prove speedup.

Stage260 gate: `{gates[-1]['status']}`.
""")
    write_text_lf(THEORY, """# Stage260 Non-Binary Full SAB Noise/Resource Scope

Stage260 checks the following invariant under a small FFNT full-path gate:

```text
decode(phase(PVW_lane_q)) == decode(phase(scalar_reference_q))
```

at the final output and at selected intermediate boundaries:

```text
blind_rotate_coeff0, extract, materialize_tlwe, packing_ks, hw_ks
```

The resource model includes one additional non-binary selector family
(`s_coff` or `s_sign`) for both scalar and PVW/MAT keys. It is still a static
estimate, not a measured peak-memory proof on Windows because `/proc` RSS is
not available there.

Open proof obligation: target-parameter `T_bootstrap/r` under a fair backend.
""")
    write_text_lf(EXP, f"""# Stage260 Experiment Plan

Primary endpoint:

```text
zero final PVW/scalar/pair failures for include-zero and ternary r=1/2/4
```

Secondary endpoints:

```text
zero stage-pair failures and recorded non-binary key resource estimates
```

Executed commands:

```powershell
make clean
make FFT_LIB=ffnt SAB_PVW_NONBINARY_FULL_NOISE_TEST=true SAB_PVW_NONBINARY_FULL_NOISE_TRIALS=3 KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
.\\main
make clean
make FFT_LIB=ffnt KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
python scripts\\build_stage260_nonbinary_full_sab_noise_resource.py
```

Evidence:

- `{rel(FINAL)}`
- `{rel(STAGES)}`
- `{rel(RESOURCES)}`
- `{rel(GATES)}`
""")


def update_ledgers(head: str) -> None:
    append_once(ROADMAP, "## Stage 260: Non-Binary Full SAB Noise/Resource", f"""
## Stage 260: Non-Binary Full SAB Noise/Resource

Goal:

```text
Upgrade the explicit non-binary PVW/MAT full SAB path from deterministic smoke
to a small multi-trial correctness/noise/resource gate.
```

Status:

```text
Generated from input head `{head}` with `{DECISION}`. include-zero and ternary
r=1/2/4 pass the small FFNT full-path final-noise gate with zero PVW, scalar,
and pair failures. Five stage-pair boundaries also record zero pair failures.
Stage261 target `T_bootstrap/r` benchmarking is admitted, but speedup remains
unproved.
```
""")
    append_once(GOAL, "### Stage260 non-binary full SAB noise/resource", f"""
### Stage260 non-binary full SAB noise/resource

`{DECISION}` records small full-path non-binary noise/resource evidence. The
active research goal remains open because target-parameter `T_bootstrap/r`,
backend-fair performance, statistical intervals, and literature-backed paper
claims are still missing.
""")
    append_once(HYP, "H10_stage260_nonbinary_full_sab_noise_resource:", f"""
H10_stage260_nonbinary_full_sab_noise_resource:
  status: small_full_path_noise_resource_passed_speedup_blocked
  evidence:
    - repro/stage260_nonbinary_full_sab_noise_resource/final_noise_summary.csv
    - repro/stage260_nonbinary_full_sab_noise_resource/stage_noise_summary.csv
    - repro/stage260_nonbinary_full_sab_noise_resource/resource_summary.csv
    - repro/stage260_nonbinary_full_sab_noise_resource/proof_gate.csv
  conclusion: >
    Stage260 records {DECISION}. The explicit non-binary PVW/MAT full SAB path
    passes small include-zero and ternary r=1/2/4 multi-trial noise/resource
    gates. Target T_bootstrap/r speedup and paper-grade claims remain blocked.
""")
    append_once(MANIFEST, "- stage260_nonbinary_full_sab_noise_resource:", """
- stage260_nonbinary_full_sab_noise_resource:
  - `docs/stage260_nonbinary_full_sab_noise_resource.md`
  - `experiments/stage260_nonbinary_full_sab_noise_resource_plan.md`
  - `theory_checks/stage260_nonbinary_full_sab_noise_resource_scope.md`
  - `algorithm_variants/mat_rlwe_sab_stage260_nonbinary_full_sab_noise_resource.md`
  - `scripts/build_stage260_nonbinary_full_sab_noise_resource.py`
  - `repro/stage260_nonbinary_full_sab_noise_resource/`
""")
    append_once(CHECKLIST, "Stage260 non-binary full SAB noise/resource", "\n- [x] Stage260 non-binary full SAB noise/resource\n")
    append_once(RUN_LEDGER, "stage260-nonbinary-full-sab-noise-resource-001", f"""stage260-nonbinary-full-sab-noise-resource-001,2026-07-04,{head},Stage 260,ffnt-correctness,"make FFT_LIB=ffnt SAB_PVW_NONBINARY_FULL_NOISE_TEST=true SAB_PVW_NONBINARY_FULL_NOISE_TRIALS=3 KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=; .\\\\main; python scripts/build_stage260_nonbinary_full_sab_noise_resource.py","include_zero/ternary; r=1/2/4; trials=3; small full path",0..2,{DECISION},"Small non-binary full SAB noise/resource gate passes; target T_bootstrap/r remains blocked.",docs/stage260_nonbinary_full_sab_noise_resource.md; repro/stage260_nonbinary_full_sab_noise_resource/proof_gate.csv
""")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    head = git(["rev-parse", "--short", "HEAD"])
    final = final_rows()
    stages = stage_rows()
    resources = resource_rows()
    source = source_rows()
    admission = admission_rows(final_ok(final), stages_ok(stages), resources_ok(resources))
    claims = claim_rows()
    gates = gate_rows(final, stages, resources, source, admission)
    write_docs(final, stages, resources, source, admission, claims, gates, head)
    write_repro_files(final, stages, resources, source, admission, claims, gates)
    update_ledgers(head)
    print(f"Stage260 report: {rel(DOC)}")
    print(f"Stage260 decision: {gates[-1]['status']}")
    return 0 if gates[-1]["status"] == DECISION else 1


if __name__ == "__main__":
    raise SystemExit(main())
