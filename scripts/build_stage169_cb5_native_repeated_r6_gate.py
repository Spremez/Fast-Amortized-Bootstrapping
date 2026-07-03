#!/usr/bin/env python3
"""Stage169: CB5 native no-perf repeated r=6 full-SAB gate."""

from __future__ import annotations

import csv
import hashlib
import math
import os
import re
import shlex
import statistics
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage169_cb5_native_repeated_r6_gate"

SUMMARY_CSV = OUT_DIR / "summary.csv"
RUNS_CSV = OUT_DIR / "run_results.csv"
AGG_CSV = OUT_DIR / "aggregate.csv"
REMOTE_CSV = OUT_DIR / "remote_environment.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage169_cb5_native_repeated_r6_gate.md"
PLAN_MD = ROOT / "experiments" / "stage169_cb5_native_repeated_r6_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage169_native_repeated_stats_scope.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_native_repeated_r6.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

REMOTE_USER = os.environ.get("STAGE169_REMOTE_USER", "delld")
REMOTE_HOST = os.environ.get("STAGE169_REMOTE_HOST", "192.168.107.220")
REMOTE_BASE = os.environ.get("STAGE169_REMOTE_BASE", "/home/delld/spz")
REMOTE_PASSWORD = os.environ.get("STAGE169_SSHPASS", "")
RUNS = int(os.environ.get("STAGE169_RUNS", "3"))
MAKE_JOBS = os.environ.get("STAGE169_JOBS", "$(nproc)")
HEAD = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
REMOTE_DIR_NAME = f"Fast-Amortized-Bootstrapping-stage169-{HEAD}"
REMOTE_DIR = f"{REMOTE_BASE}/{REMOTE_DIR_NAME}"

BASE_FLAGS = (
    "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false "
    "PARAM=SET_2_3_2048 KEY=BINARY "
    "MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true "
    "MAT_TRGSW_AVX512_RGT4_FUSED=true "
    "SAB_PVW_ACTIVE_BUFFER_FUSION=true "
    "SAB_PVW_BACKEND_FROM_DFT_ADD=true "
    "SAB_PVW_SUB_DECOMP_FUSION=true "
    "SAB_PVW_BENCH=true SAB_PVW_BENCH_R=6 SAB_PVW_BENCH_REPS=1"
)

SUMMARY_RE = re.compile(
    r"SAB_PVW_BENCH summary target_full r=(?P<r>\d+) reps=(?P<reps>\d+) "
    r"pvw_avg_us=(?P<pvw>[0-9.]+).*?pvw_lane_avg_us=(?P<pvw_lane>[0-9.]+) "
    r"scalar_repeated_avg_us=(?P<scalar>[0-9.]+).*?scalar_lane_avg_us=(?P<scalar_lane>[0-9.]+) "
    r"speedup_vs_scalar_repeated=(?P<speedup>[0-9.]+)x"
)


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)
    normalized = [{field: row.get(field, "") for field in fields} for row in row_list]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(row.get(field, "") for field in fields) + " |")
    return "\n".join(out)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def wsl_repo() -> str:
    drive = ROOT.drive.rstrip(":").lower()
    rest = ROOT.as_posix().split(":/", 1)[1]
    return f"/mnt/{drive}/{rest}"


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
        "-o UserKnownHostsFile=/tmp/codex_stage169_known_hosts "
        "-o ConnectTimeout=12 "
        f"{shlex.quote(REMOTE_USER + '@' + REMOTE_HOST)}"
    )


def remote_command(command: str) -> str:
    return f"{ssh_prefix()} {shlex.quote(command)}"


def append_once(path: Path, marker: str, block: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(path, text + block.strip("\n") + "\n")


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


def probe_remote_environment() -> int:
    cmd = (
        "printf 'hostname,'; hostname; "
        "printf 'whoami,'; whoami; "
        "printf 'uname,'; uname -a; "
        "printf 'remote_dir,'; printf " + shlex.quote(REMOTE_DIR) + "; printf '\\n'; "
        "lscpu"
    )
    return run_wsl(remote_command(cmd), OUT_DIR / "remote_environment.log", timeout=60)


def build_remote() -> int:
    cmd = (
        f"cd {shlex.quote(REMOTE_DIR)} && "
        "(make clean >/dev/null 2>&1 || true) && "
        f"make {BASE_FLAGS} -j{MAKE_JOBS}"
    )
    return run_wsl(remote_command(cmd), OUT_DIR / "build.log", timeout=1800)


def run_remote_once(run_id: int) -> int:
    cmd = f"cd {shlex.quote(REMOTE_DIR)} && stdbuf -o0 ./main"
    return run_wsl(remote_command(cmd), OUT_DIR / f"run_{run_id}.log", timeout=2400)


def cleanup_remote() -> int:
    cmd = f"cd {shlex.quote(REMOTE_DIR)} && (make clean >/dev/null 2>&1 || true)"
    return run_wsl(remote_command(cmd), OUT_DIR / "cleanup.log", timeout=300)


def parse_remote_environment() -> List[Dict[str, str]]:
    path = OUT_DIR / "remote_environment.log"
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    rows: List[Dict[str, str]] = []
    for key in ["hostname", "whoami", "uname", "remote_dir"]:
        m = re.search(rf"^{key},(.+)$", text, re.MULTILINE)
        if m:
            rows.append({"key": key, "value": m.group(1).strip(), "evidence": rel(path)})
    model = re.search(r"^Model name:\s+(.+)$", text, re.MULTILINE)
    flags = re.search(r"^Flags:\s+(.+)$", text, re.MULTILINE)
    cpus = re.search(r"^CPU\(s\):\s+(.+)$", text, re.MULTILINE)
    if model:
        rows.append({"key": "cpu_model", "value": model.group(1).strip(), "evidence": rel(path)})
    if cpus:
        rows.append({"key": "cpus", "value": cpus.group(1).strip(), "evidence": rel(path)})
    if flags:
        rows.append({"key": "has_avx512f", "value": "yes" if "avx512f" in flags.group(1) else "no", "evidence": rel(path)})
    return rows


def parse_run_log(run_id: int) -> Dict[str, str]:
    path = OUT_DIR / f"run_{run_id}.log"
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    row: Dict[str, str] = {
        "run": str(run_id),
        "run_rc": "",
        "correctness": "PASS" if re.search(r"SAB_PVW_BENCH correctness target_full .* Pass", text) else "FAIL",
        "r": "",
        "reps": "",
        "pvw_avg_us": "",
        "pvw_lane_avg_us": "",
        "scalar_repeated_avg_us": "",
        "scalar_lane_avg_us": "",
        "speedup_vs_scalar_repeated": "",
        "evidence": rel(path),
    }
    m_rc = re.search(r"^returncode:\s+(\d+)$", text, re.MULTILINE)
    if m_rc:
        row["run_rc"] = m_rc.group(1)
    for line in text.splitlines():
        m = SUMMARY_RE.search(line)
        if not m:
            continue
        row.update({
            "r": m.group("r"),
            "reps": m.group("reps"),
            "pvw_avg_us": m.group("pvw"),
            "pvw_lane_avg_us": m.group("pvw_lane"),
            "scalar_repeated_avg_us": m.group("scalar"),
            "scalar_lane_avg_us": m.group("scalar_lane"),
            "speedup_vs_scalar_repeated": m.group("speedup"),
        })
        break
    return row


def t_critical_95(n: int) -> float:
    table_by_df = {
        1: 12.706,
        2: 4.303,
        3: 3.182,
        4: 2.776,
        5: 2.571,
        6: 2.447,
        7: 2.365,
        8: 2.306,
        9: 2.262,
        10: 2.228,
    }
    return table_by_df.get(max(n - 1, 1), 1.960)


def aggregate_runs(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    good = [
        row for row in rows
        if row.get("correctness") == "PASS" and row.get("speedup_vs_scalar_repeated")
    ]
    if not good:
        return []
    metrics = [
        ("pvw_avg_us", "us"),
        ("pvw_lane_avg_us", "us_per_lane"),
        ("scalar_repeated_avg_us", "us"),
        ("scalar_lane_avg_us", "us_per_lane"),
        ("speedup_vs_scalar_repeated", "x"),
    ]
    out: List[Dict[str, str]] = []
    for metric, unit in metrics:
        values = [float(row[metric]) for row in good]
        n = len(values)
        stdev = statistics.stdev(values) if n > 1 else 0.0
        half = t_critical_95(n) * stdev / math.sqrt(n) if n > 1 else 0.0
        out.append({
            "metric": metric,
            "samples": str(n),
            "mean": f"{statistics.mean(values):.9f}",
            "median": f"{statistics.median(values):.9f}",
            "min": f"{min(values):.9f}",
            "max": f"{max(values):.9f}",
            "stdev": f"{stdev:.9f}",
            "ci95_low": f"{statistics.mean(values) - half:.9f}",
            "ci95_high": f"{statistics.mean(values) + half:.9f}",
            "unit": unit,
        })
    return out


def aggregate_value(rows: List[Dict[str, str]], metric: str, field: str) -> str:
    for row in rows:
        if row.get("metric") == metric:
            return row.get(field, "")
    return ""


def decide(sync_rc: int, env_rc: int, build_rc: int, run_rcs: List[int], rows: List[Dict[str, str]], agg: List[Dict[str, str]]) -> str:
    if not REMOTE_PASSWORD:
        return "BLOCKED_STAGE169_MISSING_REMOTE_PASSWORD_ENV"
    if sync_rc != 0:
        return "FAIL_STAGE169_REMOTE_SYNC"
    if env_rc != 0:
        return "FAIL_STAGE169_REMOTE_ENV"
    if build_rc != 0:
        return "FAIL_STAGE169_REMOTE_BUILD"
    if any(rc != 0 for rc in run_rcs):
        return "FAIL_STAGE169_REMOTE_RUN"
    if any(row.get("correctness") != "PASS" for row in rows):
        return "FAIL_STAGE169_CORRECTNESS"
    mean = float(aggregate_value(agg, "speedup_vs_scalar_repeated", "mean") or "0")
    min_v = float(aggregate_value(agg, "speedup_vs_scalar_repeated", "min") or "0")
    ci_low = float(aggregate_value(agg, "speedup_vs_scalar_repeated", "ci95_low") or "0")
    if mean >= 1.05 and min_v >= 1.0:
        return "PASS_STAGE169_NATIVE_REPEATED_R6_POSITIVE"
    if mean >= 1.0:
        return "WEAK_STAGE169_NATIVE_REPEATED_R6_POSITIVE_STATS_REVIEW_REQUIRED"
    if ci_low <= 1.0 <= float(aggregate_value(agg, "speedup_vs_scalar_repeated", "ci95_high") or "0"):
        return "NEUTRAL_STAGE169_NATIVE_REPEATED_R6_UNCERTAIN"
    return "REJECT_STAGE169_NATIVE_REPEATED_R6_NO_SPEEDUP"


def build_summary(
    decision: str,
    sync_rc: int,
    env_rc: int,
    build_rc: int,
    run_rcs: List[int],
    rows: List[Dict[str, str]],
    agg: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    correctness = "PASS" if rows and all(row.get("correctness") == "PASS" for row in rows) else "FAIL"
    speed_mean = aggregate_value(agg, "speedup_vs_scalar_repeated", "mean")
    speed_min = aggregate_value(agg, "speedup_vs_scalar_repeated", "min")
    speed_ci_low = aggregate_value(agg, "speedup_vs_scalar_repeated", "ci95_low")
    return [
        {
            "gate": "stage169_remote_secret",
            "status": "PASS" if REMOTE_PASSWORD else "BLOCKED",
            "metric": "STAGE169_SSHPASS",
            "value": "present" if REMOTE_PASSWORD else "missing",
            "evidence": "environment variable only; not written to artifacts",
            "detail": "Remote password is consumed from environment and scrubbed from logs.",
            "next_action": "Provide STAGE169_SSHPASS only at runtime.",
        },
        {
            "gate": "stage169_sync",
            "status": "PASS" if sync_rc == 0 else "FAIL",
            "metric": "sync_rc",
            "value": str(sync_rc),
            "evidence": rel(OUT_DIR / "sync.log"),
            "detail": "git archive HEAD synchronized to CB5.",
            "next_action": "Fix remote sync before interpreting runs.",
        },
        {
            "gate": "stage169_build",
            "status": "PASS" if build_rc == 0 else "FAIL",
            "metric": "build_rc",
            "value": str(build_rc),
            "evidence": rel(OUT_DIR / "build.log"),
            "detail": "Build current exact r=6 post-fusion path once on CB5.",
            "next_action": "Fix build before repeated timing.",
        },
        {
            "gate": "stage169_runs",
            "status": "PASS" if run_rcs and all(rc == 0 for rc in run_rcs) else "FAIL",
            "metric": "run_rcs",
            "value": ";".join(str(rc) for rc in run_rcs),
            "evidence": rel(RUNS_CSV),
            "detail": "Native no-perf repeated full-SAB runs.",
            "next_action": "Rerun failed samples before claiming native throughput.",
        },
        {
            "gate": "stage169_correctness",
            "status": correctness,
            "metric": "correctness",
            "value": ";".join(row.get("correctness", "") for row in rows),
            "evidence": rel(RUNS_CSV),
            "detail": "Every repeated run must pass target_full correctness.",
            "next_action": "Do not use performance numbers if any correctness fails.",
        },
        {
            "gate": "stage169_speedup_stats",
            "status": "PASS" if float(speed_mean or "0") >= 1.05 and float(speed_min or "0") >= 1.0 else "WEAK_OR_NEUTRAL",
            "metric": "speedup_mean;min;ci95_low",
            "value": f"{speed_mean};{speed_min};{speed_ci_low}",
            "evidence": rel(AGG_CSV),
            "detail": "Primary endpoint is T_bootstrap/r versus repeated scalar.",
            "next_action": "Use mean/min/CI and not a single sample.",
        },
        {
            "gate": "stage169_decision",
            "status": decision,
            "metric": "native_repeated_r6_route",
            "value": "current_exact_path",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Stage169 upgrades Stage167 timing from perf-wrapped single run to native repeated no-perf evidence.",
            "next_action": "If positive, proceed to split component counters or final claim refresh.",
        },
    ]


def artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        rows.append({
            "path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path) if path.exists() and path.is_file() else "",
            "bytes": str(path.stat().st_size) if path.exists() and path.is_file() else "",
        })
    write_csv(ARTIFACT_CSV, rows, ["path", "exists", "sha256", "bytes"])


def write_docs(decision: str, summary: List[Dict[str, str]], remote_rows: List[Dict[str, str]], rows: List[Dict[str, str]], agg: List[Dict[str, str]]) -> None:
    summary_fields = ["gate", "status", "metric", "value", "evidence", "detail", "next_action"]
    remote_fields = ["key", "value", "evidence"]
    run_fields = [
        "run", "run_rc", "correctness", "r", "pvw_lane_avg_us",
        "scalar_lane_avg_us", "speedup_vs_scalar_repeated", "evidence",
    ]
    agg_fields = ["metric", "samples", "mean", "median", "min", "max", "stdev", "ci95_low", "ci95_high", "unit"]
    write_text_lf(OUT_MD, f"""# Stage169 CB5 Native Repeated r=6 Gate

Decision: `{decision}`.

Stage169 is the native no-perf repeated full-SAB gate requested by Stage168.
It evaluates the current exact r=6 PVW/MAT-SAB path with the primary endpoint
`T_bootstrap/r` against repeated scalar SAB.

## Gate Summary

{table(summary, summary_fields)}

## Remote Environment

{table(remote_rows, remote_fields)}

## Run Results

{table(rows, run_fields)}

## Aggregates

{table(agg, agg_fields)}
""")
    write_text_lf(PLAN_MD, f"""# Stage169 Validation Plan

Goal: upgrade CB5 performance evidence from Stage167's single perf-wrapped run
to native no-perf repeated complete-SAB A/B.

Protocol:

- backend: `spqlios_avx512`;
- parameter: `BINARY SET_2_3_2048`;
- explicit path: active-buffer, backend FromDFT-add, sub-decompose fusion,
  r>4 tiled AVX512 MAT EP;
- runs: `{RUNS}` no-perf executions of `./main`;
- primary endpoint: `T_bootstrap/r`, reported as PVW lane time versus repeated
  scalar lane time.

Passing requires correctness for every sample and stable speedup statistics.
""")
    write_text_lf(THEORY_MD, """# Stage169 Native Repeated Stats Scope

Stage169 measures complete bootstrapping throughput on the native target. It
does not isolate MAT EP, from_DFT, or keygen cost; those require split counters
or microbenchmarks. It also does not prove theoretical optimality.

The output is appropriate for engineering throughput claims under the recorded
backend/parameter/platform, provided the confidence interval and minimum sample
do not contradict the claim.
""")
    write_text_lf(VARIANT_MD, f"""# Native Repeated Current r=6 PVW/MAT-SAB

Flags:

```text
{BASE_FLAGS}
```

Decision: `{decision}`.

This is the current exact r=6 path, not a new implementation variant.
""")


def update_global_docs(decision: str) -> None:
    append_once(ROADMAP_MD, "## Stage 169: CB5 Native Repeated r=6 Gate", f"""
## Stage 169: CB5 Native Repeated r=6 Gate

Goal:

```text
Run native no-perf repeated complete-SAB A/B for the current exact r=6
PVW/MAT-SAB path using T_bootstrap/r as the primary endpoint.
```

Status:

```text
Completed. Stage169 records {decision}. This is native repeated throughput
evidence for the current exact path, separate from component attribution and
theoretical optimality.
```
""")
    append_once(GOAL_MD, "Stage169 records CB5 native repeated r=6 throughput", f"""
Stage169 records CB5 native repeated r=6 throughput after Stage168. Decision:
`{decision}`. It upgrades Stage167's single perf-wrapped timing to no-perf
repeated complete-SAB evidence under the primary `T_bootstrap/r` endpoint.
""")
    append_once(CURRENT_GOAL_MD, "73. Treat Stage169 as the CB5 native repeated r=6 gate", f"""
73. Treat Stage169 as the CB5 native repeated r=6 gate:
    `{decision}`. It provides native no-perf repeated complete-SAB throughput
    evidence for the current exact path, but not theoretical optimality.
""")
    append_once(HYPOTHESIS_YAML, "id: H93_cb5_native_repeated_r6", f"""
  - id: H93_cb5_native_repeated_r6
    statement: >
      The current exact r=6 PVW/MAT-SAB path should retain positive amortized
      T_bootstrap/r throughput on CB5 when measured without perf overhead and
      repeated across multiple complete-SAB runs.
    mechanism: >
      The explicit path batches six independent lanes through MAT external
      products while preserving scalar/default SAB behavior; repeated native
      timing tests whether the speedup is stable outside perf instrumentation.
    status: stage169_cb5_native_repeated_r6_gate
    evidence: docs/stage169_cb5_native_repeated_r6_gate.md; experiments/stage169_cb5_native_repeated_r6_gate_plan.md; theory_checks/stage169_native_repeated_stats_scope.md; repro/stage169_cb5_native_repeated_r6_gate/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - any repeated run fails target_full correctness
      - mean/min speedup does not support a native throughput claim
      - results are used as theoretical optimality proof
""")
    append_once(RUN_LOG, "stage169-cb5-native-repeated-r6-gate-001", f"""
stage169-cb5-native-repeated-r6-gate-001,2026-07-04,{git_head()},Stage 169,spqlios_avx512,python scripts/build_stage169_cb5_native_repeated_r6_gate.py,CB5 native no-perf; r=6; runs={RUNS}; current exact path,default-rng,{decision},CB5 native repeated r=6 complete-SAB throughput gate.,repro/stage169_cb5_native_repeated_r6_gate
""")
    append_once(MANIFEST, "stage169_cb5_native_repeated_r6_gate", f"""
- stage169_cb5_native_repeated_r6_gate: `{decision}`
  - `docs/stage169_cb5_native_repeated_r6_gate.md`
  - `experiments/stage169_cb5_native_repeated_r6_gate_plan.md`
  - `theory_checks/stage169_native_repeated_stats_scope.md`
  - `algorithm_variants/mat_rlwe_sab_native_repeated_r6.md`
  - `repro/stage169_cb5_native_repeated_r6_gate/`
""")
    append_once(CHECKLIST, "Stage169 CB5 native repeated r=6 gate pack recorded", """
- [x] Stage169 CB5 native repeated r=6 gate pack recorded.
""")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not REMOTE_PASSWORD:
        sync_rc = env_rc = build_rc = 1
        run_rcs: List[int] = []
        remote_rows: List[Dict[str, str]] = []
        run_rows: List[Dict[str, str]] = []
    else:
        sync_rc = sync_repo()
        env_rc = probe_remote_environment() if sync_rc == 0 else 1
        remote_rows = parse_remote_environment()
        build_rc = build_remote() if env_rc == 0 else 1
        run_rcs = []
        if build_rc == 0:
            for run_id in range(1, RUNS + 1):
                run_rcs.append(run_remote_once(run_id))
        cleanup_remote()
        run_rows = [parse_run_log(run_id) for run_id in range(1, RUNS + 1)]

    agg = aggregate_runs(run_rows)
    decision = decide(sync_rc, env_rc, build_rc, run_rcs, run_rows, agg)
    summary = build_summary(decision, sync_rc, env_rc, build_rc, run_rcs, run_rows, agg)

    write_csv(REMOTE_CSV, remote_rows, ["key", "value", "evidence"])
    write_csv(RUNS_CSV, run_rows, [
        "run", "run_rc", "correctness", "r", "reps", "pvw_avg_us",
        "pvw_lane_avg_us", "scalar_repeated_avg_us", "scalar_lane_avg_us",
        "speedup_vs_scalar_repeated", "evidence",
    ])
    write_csv(AGG_CSV, agg, ["metric", "samples", "mean", "median", "min", "max", "stdev", "ci95_low", "ci95_high", "unit"])
    write_csv(SUMMARY_CSV, summary, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])

    write_docs(decision, summary, remote_rows, run_rows, agg)
    update_global_docs(decision)
    artifacts = [
        OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, SUMMARY_CSV, RUNS_CSV,
        AGG_CSV, REMOTE_CSV, OUT_DIR / "sync.log", OUT_DIR / "remote_environment.log",
        OUT_DIR / "build.log", OUT_DIR / "cleanup.log", Path(__file__),
    ]
    artifacts.extend(OUT_DIR / f"run_{run_id}.log" for run_id in range(1, RUNS + 1))
    artifact_index(artifacts)

    print(decision)
    print(f"speedup_mean={aggregate_value(agg, 'speedup_vs_scalar_repeated', 'mean')}")
    print(f"speedup_min={aggregate_value(agg, 'speedup_vs_scalar_repeated', 'min')}")
    print(f"speedup_ci95_low={aggregate_value(agg, 'speedup_vs_scalar_repeated', 'ci95_low')}")


if __name__ == "__main__":
    main()
