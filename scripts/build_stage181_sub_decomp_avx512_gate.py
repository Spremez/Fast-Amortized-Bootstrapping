#!/usr/bin/env python3
"""Stage181: benchmark the default-off AVX512 sub-decompose candidate."""

from __future__ import annotations

import csv
import hashlib
import os
import re
import shlex
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage181_sub_decomp_avx512_gate"

C_SOURCE = OUT_DIR / "stage181_sub_decomp_avx512_probe.c"
SUMMARY_CSV = OUT_DIR / "summary.csv"
RUN_CSV = OUT_DIR / "run_metrics.csv"
COUNTER_CSV = OUT_DIR / "counter_metrics.csv"
COMPARISON_CSV = OUT_DIR / "comparison.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage181_sub_decomp_avx512_gate.md"
PLAN_MD = ROOT / "experiments" / "stage181_sub_decomp_avx512_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage181_sub_decomp_avx512_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_sub_decomp_avx512.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE180_PROBE = ROOT / "repro" / "stage180_mat_ep_split_probe" / "stage180_mat_ep_split_probe.c"
STAGE180_DERIVED = ROOT / "repro" / "stage180_mat_ep_split_probe" / "derived_projection.csv"
MATTRGSW_C = ROOT / "src" / "mosfhet" / "src" / "mattrgsw.c"
MAKEFILE_DEF = ROOT / "src" / "mosfhet" / "Makefile.def"

REMOTE_USER = os.environ.get("STAGE181_REMOTE_USER", "delld")
REMOTE_HOST = os.environ.get("STAGE181_REMOTE_HOST", "192.168.107.220")
REMOTE_BASE = os.environ.get("STAGE181_REMOTE_BASE", "/home/delld/spz")
REMOTE_PASSWORD = os.environ.get("STAGE181_SSHPASS") or os.environ.get("STAGE180_SSHPASS") or ""
MAKE_JOBS = os.environ.get("STAGE181_JOBS", "$(nproc)")
R_VALUE = int(os.environ.get("STAGE181_R", "6"))
N_VALUE = int(os.environ.get("STAGE181_N", "2048"))
ITEMS = int(os.environ.get("STAGE181_ITEMS", "128"))
REPS = int(os.environ.get("STAGE181_REPS", "8"))
WARMUPS = int(os.environ.get("STAGE181_WARMUPS", "2"))
BG_BIT = int(os.environ.get("STAGE181_BG_BIT", "23"))
SUB_FULL_SHARE = float(os.environ.get("STAGE181_SUB_FULL_SHARE", "0.103963271"))
MAT_EP_FULL_SHARE = float(os.environ.get("STAGE181_MAT_EP_FULL_SHARE", "0.603899465"))

HEAD = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
REMOTE_DIR_NAME = f"Fast-Amortized-Bootstrapping-stage181-{HEAD}"
REMOTE_DIR = f"{REMOTE_BASE}/{REMOTE_DIR_NAME}"
REMOTE_STAGE_DIR = f"{REMOTE_DIR}/repro/stage181_sub_decomp_avx512_gate"
REMOTE_PROBE_SOURCE = f"{REMOTE_STAGE_DIR}/stage181_sub_decomp_avx512_probe.c"
REMOTE_BASELINE_BINARY = f"{REMOTE_STAGE_DIR}/stage181_probe_baseline"
REMOTE_AVX_BINARY = f"{REMOTE_STAGE_DIR}/stage181_probe_avx512"

MAKE_FLAGS = (
    "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false "
    "ENABLE_PVW_TMLWE=true MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true "
    "MAT_TRGSW_AVX512_RGT4_FUSED=true "
    "SAB_PVW_BACKEND_FROM_DFT_ADD=true "
    "SAB_PVW_SUB_DECOMP_FUSION=true"
)
COMPILE_FLAGS = (
    "-O3 -march=native -Wall -Wextra "
    "-DUSE_SPQLIOS -DAVX512_OPT "
    "-DMAT_TRGSW_AVX512_SMALLR_SPECIALIZED "
    "-DMAT_TRGSW_AVX512_RGT4_FUSED "
)
COMMON_DEFS = (
    f"-DSTAGE180_R={R_VALUE} -DSTAGE180_N={N_VALUE} "
    f"-DSTAGE180_ITEMS={ITEMS} -DSTAGE180_REPS={REPS} "
    f"-DSTAGE180_WARMUPS={WARMUPS} -DSTAGE180_BG_BIT={BG_BIT}"
)
PERF_EVENTS = (
    "cycles,instructions,cache-references,cache-misses,"
    "mem_inst_retired.all_loads,mem_inst_retired.all_stores,"
    "fp_arith_inst_retired.512b_packed_double"
)

BUILDS = ["baseline", "avx512_sub_decomp"]
VARIANTS = ["sub_decompose", "combined_current"]

RESULT_RE = re.compile(
    r"RESULT180,(?P<variant>[^,]+),(?P<r>\d+),(?P<N>\d+),"
    r"(?P<items>\d+),(?P<reps>\d+),(?P<calls>\d+),"
    r"(?P<total_ns>\d+),(?P<per_call_us>[0-9.]+),(?P<sink>\d+),"
    r"(?P<status>[^,\s]+)"
)
PERF_LINE_RE = re.compile(r"^\s*([\d,]+)\s+([A-Za-z0-9_.-]+)\b")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((text.rstrip() + "\n").encode("utf-8"))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)
    normalized = [{field: row.get(field, "") for field in fields} for row in row_list]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    def cell(value: str) -> str:
        return str(value).replace("|", "\\|").replace("\n", "<br>")

    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(cell(row.get(field, "")) for field in fields) + " |")
    return "\n".join(out) + "\n"


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    if current and not current.endswith("\n"):
        current += "\n"
    write_text_lf(path, current + text.lstrip("\n"))


def sha256_file(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def wsl_path(path: Path) -> str:
    drive = path.drive.rstrip(":").lower()
    rest = path.as_posix().split(":/", 1)[1]
    return f"/mnt/{drive}/{rest}"


def wsl_repo() -> str:
    return wsl_path(ROOT)


def scrub(text: str) -> str:
    if REMOTE_PASSWORD:
        text = text.replace(REMOTE_PASSWORD, "***")
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    clean = "".join(ch if ch in "\n\t" or 32 <= ord(ch) < 127 else "?" for ch in text)
    return "\n".join(line.rstrip() for line in clean.splitlines()).rstrip() + "\n"


def run_wsl(command: str, log: Path, timeout: int = 300) -> int:
    proc = subprocess.run(
        ["wsl", "bash", "-lc", command],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    write_text_lf(log, "\n".join([
        f"command: {scrub(command).strip()}",
        f"returncode: {proc.returncode}",
        "--- stdout ---",
        scrub(proc.stdout),
        "--- stderr ---",
        scrub(proc.stderr),
    ]))
    return proc.returncode


def ssh_prefix() -> str:
    return (
        f"sshpass -p {shlex.quote(REMOTE_PASSWORD)} ssh "
        "-o StrictHostKeyChecking=no "
        "-o UserKnownHostsFile=/tmp/codex_stage181_known_hosts "
        "-o ConnectTimeout=12 "
        f"{shlex.quote(REMOTE_USER + '@' + REMOTE_HOST)}"
    )


def scp_prefix() -> str:
    return (
        f"sshpass -p {shlex.quote(REMOTE_PASSWORD)} scp "
        "-o StrictHostKeyChecking=no "
        "-o UserKnownHostsFile=/tmp/codex_stage181_known_hosts "
        "-o ConnectTimeout=12 "
    )


def remote_command(command: str) -> str:
    return f"{ssh_prefix()} {shlex.quote(command)}"


def prepare_source() -> None:
    if STAGE180_PROBE.exists():
        text = read_text(STAGE180_PROBE)
    else:
        raise FileNotFoundError(STAGE180_PROBE)
    write_text_lf(C_SOURCE, text)


def sync_repo() -> int:
    remote_extract = (
        f"rm -rf {shlex.quote(REMOTE_DIR)} && "
        f"mkdir -p {shlex.quote(REMOTE_DIR)} && "
        f"tar -xf - -C {shlex.quote(REMOTE_DIR)}"
    )
    cmd = (
        f"cd {shlex.quote(wsl_repo())} && "
        f"git archive --format=tar HEAD | {ssh_prefix()} {shlex.quote(remote_extract)}"
    )
    return run_wsl(cmd, OUT_DIR / "sync.log", timeout=300)


def upload_file(local: Path, remote: str, log_name: str) -> int:
    remote_parent = remote.rsplit("/", 1)[0]
    mkdir_rc = run_wsl(remote_command(f"mkdir -p {shlex.quote(remote_parent)}"), OUT_DIR / f"{log_name}_mkdir.log", timeout=60)
    if mkdir_rc != 0:
        return mkdir_rc
    target = f"{REMOTE_USER}@{REMOTE_HOST}:{remote}"
    cmd = f"{scp_prefix()} {shlex.quote(wsl_path(local))} {shlex.quote(target)}"
    return run_wsl(cmd, OUT_DIR / f"{log_name}.log", timeout=120)


def upload_sources() -> int:
    steps = [
        (C_SOURCE, REMOTE_PROBE_SOURCE, "upload_probe"),
        (MATTRGSW_C, f"{REMOTE_DIR}/src/mosfhet/src/mattrgsw.c", "upload_mattrgsw"),
        (MAKEFILE_DEF, f"{REMOTE_DIR}/src/mosfhet/Makefile.def", "upload_makefile_def"),
    ]
    for local, remote, log in steps:
        rc = upload_file(local, remote, log)
        if rc != 0:
            return rc
    return 0


def build_remote_static() -> int:
    cmd = (
        f"cd {shlex.quote(REMOTE_DIR)}/src/mosfhet && "
        "(make clean >/dev/null 2>&1 || true) && "
        f"make static {MAKE_FLAGS} -j{MAKE_JOBS}"
    )
    return run_wsl(remote_command(cmd), OUT_DIR / "build_static.log", timeout=1800)


def compile_remote_probe(build: str) -> int:
    binary = REMOTE_BASELINE_BINARY if build == "baseline" else REMOTE_AVX_BINARY
    extra = "" if build == "baseline" else "-DMAT_TRGSW_AVX512_SUB_DECOMP"
    cmd = (
        f"cd {shlex.quote(REMOTE_DIR)} && "
        f"gcc {COMPILE_FLAGS} {extra} {COMMON_DEFS} "
        "-I . -I src/mosfhet/include "
        f"-o {shlex.quote(binary)} "
        f"{shlex.quote(REMOTE_PROBE_SOURCE)} src/mosfhet/lib/libmosfhet.a -lm"
    )
    return run_wsl(remote_command(cmd), OUT_DIR / f"compile_{build}.log", timeout=600)


def perf_remote(build: str, variant: str) -> int:
    binary = REMOTE_BASELINE_BINARY if build == "baseline" else REMOTE_AVX_BINARY
    sudo_prefix = f"printf %s {shlex.quote(REMOTE_PASSWORD)} | sudo -S -p ''"
    cmd = (
        f"cd {shlex.quote(REMOTE_DIR)} && "
        "orig=$(cat /proc/sys/kernel/perf_event_paranoid); "
        "restore_perf_paranoid(){ "
        f"{sudo_prefix} sysctl -w kernel.perf_event_paranoid=$orig >/dev/null; "
        "}; "
        "trap restore_perf_paranoid EXIT; "
        f"{sudo_prefix} sysctl -w kernel.perf_event_paranoid=1 >/dev/null && "
        f"perf stat -e {shlex.quote(PERF_EVENTS)} -- "
        f"stdbuf -o0 {shlex.quote(binary)} {shlex.quote(variant)}"
    )
    return run_wsl(remote_command(cmd), OUT_DIR / f"run_{build}_{variant}.log", timeout=1800)


def cleanup_remote() -> int:
    cmd = f"cd {shlex.quote(REMOTE_DIR)}/src/mosfhet && (make clean >/dev/null 2>&1 || true)"
    return run_wsl(remote_command(cmd), OUT_DIR / "cleanup.log", timeout=300)


def run_remote_pipeline() -> Dict[str, int]:
    rcs: Dict[str, int] = {}
    rcs["sync"] = sync_repo()
    rcs["upload"] = upload_sources() if rcs["sync"] == 0 else 1
    rcs["build"] = build_remote_static() if rcs["upload"] == 0 else 1
    for build in BUILDS:
        rcs[f"compile_{build}"] = compile_remote_probe(build) if rcs["build"] == 0 else 1
    for build in BUILDS:
        for variant in VARIANTS:
            rcs[f"run_{build}_{variant}"] = (
                perf_remote(build, variant) if rcs.get(f"compile_{build}", 1) == 0 else 1
            )
    rcs["cleanup"] = cleanup_remote() if rcs["sync"] == 0 else 1
    return rcs


def parse_log(build: str, variant: str) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    path = OUT_DIR / f"run_{build}_{variant}.log"
    text = read_text(path)
    rc_match = re.search(r"^returncode:\s+(\d+)$", text, re.MULTILINE)
    run_rc = rc_match.group(1) if rc_match else ""
    run_rows: List[Dict[str, str]] = []
    counter_rows: List[Dict[str, str]] = []
    for raw in text.splitlines():
        m = PERF_LINE_RE.match(raw)
        if m:
            counter_rows.append({
                "build": build,
                "variant": variant,
                "metric": m.group(2),
                "value": m.group(1).replace(",", ""),
                "unit": "count",
                "evidence": rel(path),
            })
        r = RESULT_RE.search(raw)
        if r:
            run_rows.append({
                "build": build,
                "variant": variant,
                "run_rc": run_rc,
                "r": r.group("r"),
                "N": r.group("N"),
                "items": r.group("items"),
                "reps": r.group("reps"),
                "calls": r.group("calls"),
                "total_ns": r.group("total_ns"),
                "per_call_us": r.group("per_call_us"),
                "sink": r.group("sink"),
                "status": r.group("status"),
                "evidence": rel(path),
            })
    if not run_rows:
        run_rows.append({
            "build": build,
            "variant": variant,
            "run_rc": run_rc,
            "r": str(R_VALUE),
            "N": str(N_VALUE),
            "items": str(ITEMS),
            "reps": str(REPS),
            "calls": "0",
            "total_ns": "0",
            "per_call_us": "",
            "sink": "",
            "status": "NO_RESULT",
            "evidence": rel(path),
        })
    return run_rows, counter_rows


def build_comparison(run_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    by_key = {(r["build"], r["variant"]): r for r in run_rows if r.get("per_call_us")}
    rows: List[Dict[str, str]] = []
    for variant in VARIANTS:
        base = by_key.get(("baseline", variant))
        avx = by_key.get(("avx512_sub_decomp", variant))
        if not base or not avx:
            rows.append({
                "variant": variant,
                "baseline_us": "",
                "avx512_us": "",
                "speedup": "",
                "sink_equal": "no",
                "projected_full_sab_speedup": "",
                "status": "MISSING",
            })
            continue
        baseline_us = float(base["per_call_us"])
        avx_us = float(avx["per_call_us"])
        speedup = baseline_us / avx_us if avx_us else 0.0
        if variant == "sub_decompose":
            share = SUB_FULL_SHARE
        else:
            share = MAT_EP_FULL_SHARE
        projected = 1.0 / ((1.0 - share) + share / speedup) if speedup > 0 else 0.0
        rows.append({
            "variant": variant,
            "baseline_us": f"{baseline_us:.9f}",
            "avx512_us": f"{avx_us:.9f}",
            "speedup": f"{speedup:.9f}",
            "sink_equal": "yes" if base["sink"] == avx["sink"] else "no",
            "projected_full_sab_speedup": f"{projected:.9f}",
            "status": "PASS" if base["sink"] == avx["sink"] and speedup > 1.0 else "NEUTRAL_OR_FAIL",
        })
    return rows


def decide(rcs: Dict[str, int], run_rows: List[Dict[str, str]], comparison_rows: List[Dict[str, str]]) -> str:
    if not REMOTE_PASSWORD:
        return "SKIP_STAGE181_REMOTE_SECRET_MISSING"
    if any(v != 0 for k, v in rcs.items() if k != "cleanup"):
        return "BLOCK_STAGE181_REMOTE_PIPELINE_FAILED"
    if any(row["status"] != "PASS" for row in run_rows):
        return "BLOCK_STAGE181_PROBE_RESULT_FAILED"
    if any(row["sink_equal"] != "yes" for row in comparison_rows if row["variant"] in VARIANTS):
        return "BLOCK_STAGE181_SINK_MISMATCH"
    combined = next((r for r in comparison_rows if r["variant"] == "combined_current"), None)
    sub = next((r for r in comparison_rows if r["variant"] == "sub_decompose"), None)
    if combined and float(combined["projected_full_sab_speedup"]) >= 1.03:
        return "PASS_STAGE181_SUB_DECOMP_AVX512_PROMOTE_FULLSAB_GATE"
    if sub and float(sub["speedup"]) > 1.0:
        return "NEUTRAL_STAGE181_SUB_DECOMP_AVX512_MICRO_ONLY"
    return "REJECT_STAGE181_SUB_DECOMP_AVX512_NOT_FASTER"


def build_next_rows(decision: str) -> List[Dict[str, str]]:
    if decision == "PASS_STAGE181_SUB_DECOMP_AVX512_PROMOTE_FULLSAB_GATE":
        return [{
            "priority": "P0",
            "stage": "182",
            "name": "full-SAB AVX512 sub-decompose gate",
            "entry_condition": "Stage181 combined current projection reaches >=3% complete-SAB gain.",
            "gate": "Run correctness and repeated full-SAB T_bootstrap/r A/B with MAT_TRGSW_AVX512_SUB_DECOMP=true.",
            "failure_rule": "Reject if complete-SAB speedup is not stable.",
        }]
    return [{
        "priority": "P0",
        "stage": "182",
        "name": "negative frontier or new mechanism",
        "entry_condition": "Stage181 does not promote AVX512 sub-decompose to full-SAB gate.",
        "gate": "Record exact-path headroom and avoid blind AVX512 retuning.",
        "failure_rule": "No full-SAB run without a promoted microbench candidate.",
    }]


def summary_rows(decision: str, rcs: Dict[str, int], comparison_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [
        {
            "gate": "stage181_inputs",
            "status": "PASS" if STAGE180_PROBE.exists() and MATTRGSW_C.exists() else "FAIL",
            "metric": "probe_and_source_present",
            "value": "1" if STAGE180_PROBE.exists() and MATTRGSW_C.exists() else "0",
            "evidence": f"{rel(STAGE180_PROBE)}; {rel(MATTRGSW_C)}",
            "detail": "Stage181 compares baseline and default-off AVX512 sub-decompose candidate.",
            "next_action": "Repair missing source before running.",
        },
        {
            "gate": "stage181_remote_pipeline",
            "status": "PASS" if rcs and all(v == 0 for k, v in rcs.items() if k != "cleanup") else ("SKIPPED" if not REMOTE_PASSWORD else "FAIL"),
            "metric": "rcs",
            "value": ";".join(f"{k}={v}" for k, v in sorted(rcs.items())) if rcs else "not_run",
            "evidence": rel(OUT_DIR),
            "detail": "Remote CB5 builds baseline and AVX512-subdecomp probes from the same uploaded source.",
            "next_action": "Fix first nonzero rc before interpreting results.",
        },
        {
            "gate": "stage181_equivalence",
            "status": "PASS" if comparison_rows and all(r["sink_equal"] == "yes" for r in comparison_rows) else ("SKIPPED" if not comparison_rows else "FAIL"),
            "metric": "sink_equal",
            "value": ";".join(f"{r['variant']}={r['sink_equal']}" for r in comparison_rows) if comparison_rows else "none",
            "evidence": rel(COMPARISON_CSV),
            "detail": "Baseline and AVX512-subdecomp deterministic sinks must match.",
            "next_action": "Do not interpret timing if sinks differ.",
        },
        {
            "gate": "stage181_decision",
            "status": decision,
            "metric": "route",
            "value": "stage182",
            "evidence": rel(COMPARISON_CSV),
            "detail": "Promotion requires projected complete-SAB gain, not just a local kernel improvement.",
            "next_action": "Proceed according to next_stage_queue.",
        },
    ]


def write_docs(decision: str, rows: List[Dict[str, str]], comparisons: List[Dict[str, str]], next_rows: List[Dict[str, str]]) -> None:
    write_text_lf(OUT_MD, f"""# Stage181 AVX512 Sub-Decompose Gate

Decision: `{decision}`.

Stage181 benchmarks the default-off `MAT_TRGSW_AVX512_SUB_DECOMP` candidate
against the baseline split probe on CB5. The candidate is allowed to proceed to
a full-SAB gate only if the combined-current projection reaches the complete
SAB `T_bootstrap/r` threshold.

## Gate Summary

{table(rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Comparison

{table(comparisons, ["variant", "baseline_us", "avx512_us", "speedup", "sink_equal", "projected_full_sab_speedup", "status"])}
## Next Queue

{table(next_rows, ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"])}
""")
    write_text_lf(PLAN_MD, """# Stage181 Plan

Goal: test the default-off AVX512 integer sub-decompose candidate without
changing scalar/default behavior.

Gates:

- baseline and AVX512 sinks must match;
- sub-decompose and combined-current timings must be recorded;
- full-SAB promotion requires projected complete-SAB gain, not local speedup
  alone.
""")
    write_text_lf(THEORY_MD, f"""# Stage181 AVX512 Sub-Decompose Model

The Stage180 split estimates sub-decompose at full-SAB share
`{SUB_FULL_SHARE:.9f}`. A pure sub-decompose improvement must therefore be very
large to move complete SAB. Stage181 also measures the combined current block;
promotion to full-SAB is allowed only if the combined block projection reaches
at least 3% complete-SAB speedup.
""")
    write_text_lf(VARIANT_MD, """# AVX512 Sub-Decompose Variant

Production flag: `MAT_TRGSW_AVX512_SUB_DECOMP=true`.

The variant replaces the scalar coefficient loop in `mat_trgsw_sub_decompose`
with AVX512 integer subtract/add/variable-shift/mask/subtract/store operations.
It is default-off and leaves scalar/default SAB unchanged.
""")


def write_global_updates(decision: str) -> None:
    append_once(ROADMAP_MD, "## Stage 181: AVX512 Sub-Decompose Gate", f"""
## Stage 181: AVX512 Sub-Decompose Gate

Goal:

```text
Benchmark the default-off AVX512 sub-decompose implementation candidate and
decide whether it deserves a complete-SAB gate.
```

Status:

```text
Completed. Stage181 records {decision}. The variant remains explicit and must
not be claimed as SAB acceleration unless a later full-SAB gate passes.
```
""")
    append_once(GOAL_MD, "Stage181 records AVX512 sub-decompose gate", f"""
Stage181 records the AVX512 sub-decompose gate. Decision: `{decision}`.
""")
    append_once(CURRENT_GOAL_MD, "Treat Stage181 as the AVX512 sub-decompose gate", f"""
85. Treat Stage181 as the AVX512 sub-decompose gate:
    `{decision}`. The new implementation is default-off. Complete-SAB
    acceleration remains unproven until a promoted full-SAB gate passes.
""")
    append_once(HYPOTHESIS_YAML, "H105_sub_decomp_avx512_gate", f"""
  - id: H105_sub_decomp_avx512_gate
    statement: >
      A default-off AVX512 integer sub-decompose path may improve the exact
      full-MAT hot block, but it should promote only if the combined-current
      projection can affect complete SAB T_bootstrap/r.
    mechanism: >
      Replace scalar coefficient decomposition with AVX512 subtract/add/shift/
      mask/store operations and compare deterministic sinks and timings against
      baseline on CB5.
    status: stage181_sub_decomp_avx512_gate
    evidence: docs/stage181_sub_decomp_avx512_gate.md; experiments/stage181_sub_decomp_avx512_gate_plan.md; theory_checks/stage181_sub_decomp_avx512_model.md; repro/stage181_sub_decomp_avx512_gate/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - baseline and AVX512 sinks differ
      - microbench does not project to complete-SAB gain
      - local speedup is reported as bootstrapping acceleration
""")
    append_once(RUN_LOG, "stage181-sub-decomp-avx512-gate-001", f"""
stage181-sub-decomp-avx512-gate-001,2026-07-04,{HEAD},Stage 181,spqlios_avx512,python scripts/build_stage181_sub_decomp_avx512_gate.py,r={R_VALUE}; N={N_VALUE}; items={ITEMS}; reps={REPS},deterministic-probe,{decision},Default-off AVX512 sub-decompose microbench gate.,repro/stage181_sub_decomp_avx512_gate
""")
    append_once(MANIFEST, "stage181_sub_decomp_avx512_gate", f"""
- stage181_sub_decomp_avx512_gate: `{decision}`
  - `docs/stage181_sub_decomp_avx512_gate.md`
  - `experiments/stage181_sub_decomp_avx512_gate_plan.md`
  - `theory_checks/stage181_sub_decomp_avx512_model.md`
  - `algorithm_variants/mat_rlwe_sab_sub_decomp_avx512.md`
  - `repro/stage181_sub_decomp_avx512_gate/`
""")
    append_once(CHECKLIST, "Stage181 AVX512 sub-decompose gate pack recorded", """
- [x] Stage181 AVX512 sub-decompose gate pack recorded.
""")


def write_artifacts(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        rows.append({
            "path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path),
            "bytes": str(path.stat().st_size) if path.exists() else "0",
        })
    write_csv(ARTIFACT_CSV, rows, ["path", "exists", "sha256", "bytes"])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prepare_source()
    rcs: Dict[str, int] = {}
    if REMOTE_PASSWORD:
        rcs = run_remote_pipeline()
    all_runs: List[Dict[str, str]] = []
    all_counters: List[Dict[str, str]] = []
    for build in BUILDS:
        for variant in VARIANTS:
            runs, counters = parse_log(build, variant)
            all_runs.extend(runs)
            all_counters.extend(counters)
    write_csv(RUN_CSV, all_runs, ["build", "variant", "run_rc", "r", "N", "items", "reps", "calls", "total_ns", "per_call_us", "sink", "status", "evidence"])
    write_csv(COUNTER_CSV, all_counters, ["build", "variant", "metric", "value", "unit", "evidence"])
    comparisons = build_comparison(all_runs)
    write_csv(COMPARISON_CSV, comparisons, ["variant", "baseline_us", "avx512_us", "speedup", "sink_equal", "projected_full_sab_speedup", "status"])
    decision = decide(rcs, all_runs, comparisons)
    rows = summary_rows(decision, rcs, comparisons)
    next_rows = build_next_rows(decision)
    write_csv(SUMMARY_CSV, rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    write_csv(NEXT_CSV, next_rows, ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"])
    write_docs(decision, rows, comparisons, next_rows)
    write_global_updates(decision)
    write_artifacts([
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        SUMMARY_CSV,
        RUN_CSV,
        COUNTER_CSV,
        COMPARISON_CSV,
        NEXT_CSV,
        C_SOURCE,
        Path(__file__),
        MATTRGSW_C,
        MAKEFILE_DEF,
    ])
    print(decision)


if __name__ == "__main__":
    main()
