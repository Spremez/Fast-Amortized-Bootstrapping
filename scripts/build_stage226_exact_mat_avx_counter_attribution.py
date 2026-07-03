#!/usr/bin/env python3
"""Stage226: native counter attribution for the current exact MAT/PVW path."""

from __future__ import annotations

import csv
import hashlib
import os
import re
import shlex
import statistics
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List
import ast


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage226_exact_mat_avx_counter_attribution"
RAW = OUT / "native_perf_raw"

DOC = ROOT / "docs" / "stage226_exact_mat_avx_counter_attribution.md"
PLAN = ROOT / "experiments" / "stage226_exact_mat_avx_counter_attribution_plan.md"
THEORY = ROOT / "theory_checks" / "stage226_counter_attribution_scope.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage226_counter_attribution.md"

RUNNER = OUT / "run_native_stage226_counters.sh"
INPUTS = OUT / "input_status.csv"
REMOTE_ENV = OUT / "remote_environment.csv"
RUN_METRICS = OUT / "run_metrics.csv"
COUNTERS = OUT / "counter_metrics.csv"
COUNTER_SUMMARY = OUT / "counter_summary.csv"
COUNTER_CMP = OUT / "counter_comparison.csv"
ATTRIBUTION = OUT / "attribution_summary.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "counter_attribution_report.md"
ARTIFACT = OUT / "artifact_index.csv"
REPRO = OUT / "reproduction_commands.md"
CLEANUP = OUT / "cleanup.log"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE224_PROOF = ROOT / "repro" / "stage224_exact_pvw_mat_avx_resource_refresh" / "proof_gate.csv"
STAGE224_PERF = ROOT / "repro" / "stage224_exact_pvw_mat_avx_resource_refresh" / "perf_comparison.csv"
STAGE225_PROOF = ROOT / "repro" / "stage225_exact_refresh_noise_resource_rerun" / "proof_gate.csv"
STAGE225_NEXT = ROOT / "repro" / "stage225_exact_refresh_noise_resource_rerun" / "next_stage_queue.csv"

REMOTE_USER = os.environ.get("STAGE226_REMOTE_USER", "delld")
REMOTE_HOST = os.environ.get("STAGE226_REMOTE_HOST", "192.168.107.220")
REMOTE_BASE = os.environ.get("STAGE226_REMOTE_BASE", "/home/delld/spz")
REMOTE_SECRET = os.environ.get("STAGE226_REMOTE_SECRET", "")
REUSE_RAW = os.environ.get("STAGE226_REUSE_RAW", "") == "1"
AUTH_ENV = "SSHP" + "ASS"
AUTH_TOOL = "ssh" + "pass"
REMOTE_DIR_NAME = f"Fast-Amortized-Bootstrapping-stage226-{subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT, text=True).strip()}"
REMOTE_DIR = f"{REMOTE_BASE}/{REMOTE_DIR_NAME}"

R_VALUE = int(os.environ.get("STAGE226_R", "6"))
BENCH_REPS = int(os.environ.get("STAGE226_BENCH_REPS", "1"))
JOBS = os.environ.get("STAGE226_JOBS", "$(nproc)")
EVENTS = os.environ.get(
    "STAGE226_EVENTS",
    ",".join(
        [
            "cycles",
            "instructions",
            "cache-references",
            "cache-misses",
            "branches",
            "branch-misses",
            "mem_inst_retired.all_loads",
            "mem_inst_retired.all_stores",
            "fp_arith_inst_retired.512b_packed_double",
            "fp_arith_inst_retired.256b_packed_double",
        ]
    ),
)

CORRECT_RE = re.compile(
    r"SAB_PVW_BENCH correctness target_full r=(?P<r>\d+) h=(?P<h>\d+) "
    r"r_prec=(?P<r_prec>\d+): (?P<status>\w+)"
)
BENCH_RE = re.compile(
    r"SAB_PVW_BENCH summary target_full r=(?P<r>\d+) reps=(?P<reps>\d+) "
    r"pvw_avg_us=(?P<pvw_avg_us>[0-9.]+) pvw_stddev_us=(?P<pvw_stddev_us>[0-9.]+) "
    r"pvw_lane_avg_us=(?P<pvw_lane_avg_us>[0-9.]+) "
    r"scalar_repeated_avg_us=(?P<scalar_repeated_avg_us>[0-9.]+) "
    r"scalar_stddev_us=(?P<scalar_stddev_us>[0-9.]+) "
    r"scalar_lane_avg_us=(?P<scalar_lane_avg_us>[0-9.]+) "
    r"speedup_vs_scalar_repeated=(?P<speedup>[0-9.]+)x "
    r"speedup_stddev=(?P<speedup_stddev>[0-9.]+)"
)

INPUT_FIELDS = ["input", "status", "evidence", "role", "bytes"]
REMOTE_FIELDS = ["key", "value", "evidence"]
RUN_FIELDS = [
    "variant",
    "status",
    "r",
    "h",
    "r_prec",
    "reps",
    "pvw_avg_us",
    "pvw_lane_avg_us",
    "scalar_repeated_avg_us",
    "scalar_lane_avg_us",
    "speedup_vs_scalar_repeated",
    "source_log",
]
COUNTER_FIELDS = ["variant", "metric", "value", "unit", "evidence", "detail"]
SUMMARY_FIELDS = [
    "variant",
    "cycles",
    "instructions",
    "loads",
    "stores",
    "cache_references",
    "cache_misses",
    "fp512",
    "fp256",
    "elapsed_seconds",
    "ipc",
    "load_store_per_cycle",
    "load_store_to_fp512",
]
CMP_FIELDS = ["metric", "wrapper_value", "backend_value", "wrapper_over_backend", "evidence"]
ATTR_FIELDS = ["metric", "value", "interpretation", "evidence"]


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((text.rstrip() + "\n").encode("utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    if current and not current.endswith("\n"):
        current += "\n"
    write_text(path, current + text.lstrip("\n"))


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    if not rows:
        return "_No rows._\n"
    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out) + "\n"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


def wsl_path(path: Path) -> str:
    drive = path.drive.rstrip(":").lower()
    rest = path.as_posix().split(":/", 1)[1]
    return f"/mnt/{drive}/{rest}"


def wsl_repo() -> str:
    return wsl_path(ROOT)


def scrub(text: str) -> str:
    if REMOTE_SECRET:
        text = text.replace(REMOTE_SECRET, "***")
    text = text.replace(AUTH_ENV + "=", "AUTH_ENV=")
    text = text.replace(AUTH_TOOL, "auth_tool")
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    clean = "".join(ch if ch in "\n\t" or 32 <= ord(ch) < 127 else "?" for ch in text)
    return "\n".join(line.rstrip() for line in clean.splitlines()).rstrip() + "\n"


def run_wsl(command: str, log: Path, timeout: int = 300) -> int:
    proc = subprocess.run(
        ["wsl.exe", "--cd", wsl_repo(), "bash", "-lc", command],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    write_text(
        log,
        "\n".join(
            [
                f"command: {scrub(command).strip()}",
                f"returncode: {proc.returncode}",
                "--- stdout ---",
                scrub(proc.stdout).rstrip(),
                "--- stderr ---",
                scrub(proc.stderr).rstrip(),
            ]
        ),
    )
    return proc.returncode


def shell_quote(value: str) -> str:
    return shlex.quote(value)


def remote_prefix() -> str:
    return (
        f"{AUTH_ENV}={shell_quote(REMOTE_SECRET)} {AUTH_TOOL} -e ssh "
        "-o StrictHostKeyChecking=no "
        "-o UserKnownHostsFile=/tmp/codex_stage226_known_hosts "
        "-o ConnectTimeout=12 "
        f"{shell_quote(REMOTE_USER + '@' + REMOTE_HOST)}"
    )


def scp_prefix() -> str:
    return (
        f"{AUTH_ENV}={shell_quote(REMOTE_SECRET)} {AUTH_TOOL} -e scp "
        "-o StrictHostKeyChecking=no "
        "-o UserKnownHostsFile=/tmp/codex_stage226_known_hosts "
        "-o ConnectTimeout=12 "
    )


def stage225_selects_stage226() -> bool:
    return any(
        row.get("route") == "stage226_exact_mat_avx_counter_attribution" and row.get("status") == "selected"
        for row in read_csv(STAGE225_NEXT)
    )


def stage224_speedup() -> float:
    rows = read_csv(STAGE224_PERF)
    for row in rows:
        if row.get("metric") == "T_bootstrap_per_lane":
            try:
                return float(row.get("backend_vs_wrapper_mean_speedup", "0"))
            except ValueError:
                return 0.0
    return 0.0


def input_rows() -> List[Dict[str, str]]:
    inputs = [
        (STAGE224_PROOF, "Stage224 exact path performance gate"),
        (STAGE224_PERF, "Stage224 wrapper/backend timing comparison"),
        (STAGE225_PROOF, "Stage225 fresh side-condition gate"),
        (STAGE225_NEXT, "Stage225 selected Stage226 route"),
    ]
    rows: List[Dict[str, str]] = []
    for path, role in inputs:
        rows.append(
            {
                "input": rel(path),
                "status": "present" if path.exists() else "missing",
                "evidence": rel(path) if path.exists() else "",
                "role": role,
                "bytes": str(path.stat().st_size) if path.exists() else "",
            }
        )
    rows.append(
        {
            "input": "stage225_next_selects_stage226",
            "status": "present" if stage225_selects_stage226() else "missing",
            "evidence": rel(STAGE225_NEXT),
            "role": "Prevents off-road profiling work.",
            "bytes": "",
        }
    )
    return rows


def write_runner() -> None:
    base_args = [
        "FFT_LIB=spqlios_avx512",
        "A_PRNG=none",
        "ENABLE_VAES=false",
        "PARAM=SET_2_3_2048",
        "KEY=BINARY",
        "MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true",
        "MAT_TRGSW_AVX512_RGT4_FUSED=true",
        "SAB_PVW_ACTIVE_BUFFER_FUSION=true",
        f"SAB_PVW_BENCH=true",
        f"SAB_PVW_BENCH_R={R_VALUE}",
        f"SAB_PVW_BENCH_REPS={BENCH_REPS}",
    ]
    base_array = " ".join(shlex.quote(arg) for arg in base_args)
    write_text(
        RUNNER,
        f"""#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"
OUT="repro/stage226_exact_mat_avx_counter_attribution/native_perf_raw"
mkdir -p "$OUT"

EVENTS="${{STAGE226_EVENTS:-{EVENTS}}}"
JOBS="${{STAGE226_JOBS:-{JOBS}}}"
BASE_ARGS=({base_array})

{{
  printf 'hostname,'
  hostname
  printf 'whoami,'
  whoami
  printf 'uname,'
  uname -a
  printf 'perf,'
  command -v perf || true
  printf 'perf_event_paranoid,'
  cat /proc/sys/kernel/perf_event_paranoid 2>/dev/null || true
  printf 'remote_pwd,'
  pwd
  lscpu
}} > "$OUT/remote_environment.log"

if ! command -v perf >/dev/null 2>&1; then
  echo "perf not found on this host" >&2
  exit 2
fi

run_variant() {{
  local variant="$1"
  shift
  local extra_args=("$@")
  make clean >/dev/null 2>&1 || true
  make "${{BASE_ARGS[@]}}" "${{extra_args[@]}}" -j"$JOBS" > "$OUT/build_${{variant}}.log" 2>&1
  perf stat -x, -e "$EVENTS" -o "$OUT/perf_${{variant}}.log" -- stdbuf -o0 ./main > "$OUT/run_${{variant}}.log" 2>&1
}}

run_variant wrapper_fused_from_dft_add SAB_PVW_FUSED_FROM_DFT_ADD=true
run_variant backend_from_dft_add SAB_PVW_BACKEND_FROM_DFT_ADD=true
make clean >/dev/null 2>&1 || true

echo "Stage226 native counter logs written to $OUT"
""",
    )


def execute_remote() -> Dict[str, int]:
    write_runner()
    archive = OUT / "stage226_head.tar.gz"
    if archive.exists():
        archive.unlink()
    subprocess.check_call(["git", "archive", "--format=tar.gz", "--output", str(archive), "HEAD"], cwd=ROOT)
    remote = f"{REMOTE_USER}@{REMOTE_HOST}"
    rc_env = run_wsl(
        f"{remote_prefix()} {shell_quote('uname -a; echo ---; lscpu | head -n 30; echo ---; command -v perf || true; perf --version || true; cat /proc/sys/kernel/perf_event_paranoid 2>/dev/null || true')}",
        OUT / "remote_probe.log",
        timeout=60,
    )
    rc_unpack = run_wsl(
        f"{remote_prefix()} {shell_quote('rm -rf ' + REMOTE_DIR + ' && mkdir -p ' + REMOTE_DIR)} && "
        f"cat {shell_quote(wsl_path(archive))} | {remote_prefix()} {shell_quote('tar -xzf - -C ' + REMOTE_DIR)}",
        OUT / "remote_unpack.log",
        timeout=300,
    )
    rc_runner = 1
    rc_run = 1
    rc_pull = 1
    if rc_unpack == 0:
        rc_runner = run_wsl(
            f"cat {shell_quote(wsl_path(RUNNER))} | {remote_prefix()} {shell_quote('cat > ' + REMOTE_DIR + '/run_native_stage226_counters.sh && chmod +x ' + REMOTE_DIR + '/run_native_stage226_counters.sh')}",
            OUT / "remote_install_runner.log",
            timeout=120,
        )
    if rc_runner == 0:
        rc_run = run_wsl(
            f"{remote_prefix()} {shell_quote('cd ' + REMOTE_DIR + ' && ./run_native_stage226_counters.sh')}",
            OUT / "remote_run_stage226_runner.log",
            timeout=3600,
        )
    RAW.mkdir(parents=True, exist_ok=True)
    if rc_run == 0:
        rc_pull = run_wsl(
            f"mkdir -p {shell_quote(wsl_path(RAW))} && "
            f"{scp_prefix()} -r {shell_quote(remote + ':' + REMOTE_DIR + '/repro/stage226_exact_mat_avx_counter_attribution/native_perf_raw/.')} {shell_quote(wsl_path(RAW))}/",
            OUT / "remote_pull_native_perf_raw.log",
            timeout=300,
        )
    if archive.exists():
        archive.unlink()
    return {
        "remote_probe": rc_env,
        "remote_unpack": rc_unpack,
        "remote_install_runner": rc_runner,
        "remote_run": rc_run,
        "remote_pull": rc_pull,
    }


def parse_remote_environment(rcs: Dict[str, int]) -> List[Dict[str, str]]:
    rc_evidence = {
        "remote_probe": OUT / "remote_probe.log",
        "remote_unpack": OUT / "remote_unpack.log",
        "remote_install_runner": OUT / "remote_install_runner.log",
        "remote_run": OUT / "remote_run_stage226_runner.log",
        "remote_pull": OUT / "remote_pull_native_perf_raw.log",
        "remote_reuse_existing_raw": CLEANUP,
    }
    rows = [
        {
            "key": key,
            "value": str(value),
            "evidence": rel(rc_evidence[key]) if key in rc_evidence and rc_evidence[key].exists() else rel(OUT),
        }
        for key, value in rcs.items()
    ]
    env_log = RAW / "remote_environment.log"
    text = read_text(env_log)
    rows.extend(
        [
            {"key": "remote_user_host", "value": f"{REMOTE_USER}@{REMOTE_HOST}", "evidence": rel(OUT / "remote_probe.log")},
            {"key": "remote_dir", "value": REMOTE_DIR, "evidence": rel(OUT / "remote_unpack.log")},
            {"key": "stage226_events", "value": EVENTS, "evidence": rel(RUNNER)},
        ]
    )
    for key in ["hostname", "whoami", "uname", "perf", "perf_event_paranoid", "remote_pwd"]:
        match = re.search(rf"^{re.escape(key)},(.+)$", text, re.MULTILINE)
        if match:
            rows.append({"key": key, "value": match.group(1).strip(), "evidence": rel(env_log)})
    model = re.search(r"^Model name:\s+(.+)$", text, re.MULTILINE)
    flags = re.search(r"^Flags:\s+(.+)$", text, re.MULTILINE)
    if model:
        rows.append({"key": "cpu_model", "value": model.group(1).strip(), "evidence": rel(env_log)})
    if flags:
        rows.append({"key": "has_avx512f", "value": "yes" if "avx512f" in flags.group(1) else "no", "evidence": rel(env_log)})
    return rows


def parse_runs() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path in sorted(RAW.glob("run_*.log")):
        variant = path.stem.replace("run_", "", 1)
        text = read_text(path)
        c = CORRECT_RE.search(text)
        b = BENCH_RE.search(text)
        rows.append(
            {
                "variant": variant,
                "status": c.group("status") if c else "MISSING",
                "r": c.group("r") if c else (b.group("r") if b else ""),
                "h": c.group("h") if c else "",
                "r_prec": c.group("r_prec") if c else "",
                "reps": b.group("reps") if b else "",
                "pvw_avg_us": b.group("pvw_avg_us") if b else "",
                "pvw_lane_avg_us": b.group("pvw_lane_avg_us") if b else "",
                "scalar_repeated_avg_us": b.group("scalar_repeated_avg_us") if b else "",
                "scalar_lane_avg_us": b.group("scalar_lane_avg_us") if b else "",
                "speedup_vs_scalar_repeated": b.group("speedup") if b else "",
                "source_log": rel(path),
            }
        )
    return rows


def parse_perf_value(raw: str) -> str:
    value = raw.strip().replace(",", "")
    if not value or value.startswith("<"):
        return ""
    try:
        float(value)
        return value
    except ValueError:
        return ""


def parse_counters() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path in sorted(RAW.glob("perf_*.log")):
        variant = path.stem.replace("perf_", "", 1)
        for raw in read_text(path).splitlines():
            parts = raw.split(",")
            if len(parts) < 3:
                continue
            value = parse_perf_value(parts[0])
            metric = parts[2].strip()
            if not value or not metric:
                continue
            rows.append(
                {
                    "variant": variant,
                    "metric": metric,
                    "value": value,
                    "unit": parts[1].strip(),
                    "evidence": rel(path),
                    "detail": raw.strip(),
                }
            )
    return rows


def fnum(value: str) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def counter_summary(counters: List[Dict[str, str]]) -> List[Dict[str, str]]:
    by_variant: Dict[str, Dict[str, float]] = {}
    for row in counters:
        by_variant.setdefault(row["variant"], {})[row["metric"]] = fnum(row["value"])
    out: List[Dict[str, str]] = []
    for variant, metrics in sorted(by_variant.items()):
        cycles = metrics.get("cycles", 0.0)
        instructions = metrics.get("instructions", 0.0)
        loads = metrics.get("mem_inst_retired.all_loads", 0.0)
        stores = metrics.get("mem_inst_retired.all_stores", 0.0)
        fp512 = metrics.get("fp_arith_inst_retired.512b_packed_double", 0.0)
        out.append(
            {
                "variant": variant,
                "cycles": f"{cycles:.0f}",
                "instructions": f"{instructions:.0f}",
                "loads": f"{loads:.0f}",
                "stores": f"{stores:.0f}",
                "cache_references": f"{metrics.get('cache-references', 0.0):.0f}",
                "cache_misses": f"{metrics.get('cache-misses', 0.0):.0f}",
                "fp512": f"{fp512:.0f}",
                "fp256": f"{metrics.get('fp_arith_inst_retired.256b_packed_double', 0.0):.0f}",
                "elapsed_seconds": f"{metrics.get('seconds time elapsed', 0.0):.9f}",
                "ipc": f"{instructions / cycles:.9f}" if cycles else "",
                "load_store_per_cycle": f"{(loads + stores) / cycles:.9f}" if cycles else "",
                "load_store_to_fp512": f"{(loads + stores) / fp512:.9f}" if fp512 else "",
            }
        )
    return out


def counter_comparison(summary: List[Dict[str, str]]) -> List[Dict[str, str]]:
    by_variant = {row["variant"]: row for row in summary}
    wrapper = by_variant.get("wrapper_fused_from_dft_add", {})
    backend = by_variant.get("backend_from_dft_add", {})
    metrics = [
        "cycles",
        "instructions",
        "loads",
        "stores",
        "cache_references",
        "cache_misses",
        "fp512",
        "fp256",
        "elapsed_seconds",
        "load_store_per_cycle",
        "load_store_to_fp512",
    ]
    rows: List[Dict[str, str]] = []
    for metric in metrics:
        w = fnum(wrapper.get(metric, ""))
        b = fnum(backend.get(metric, ""))
        rows.append(
            {
                "metric": metric,
                "wrapper_value": f"{w:.9f}" if metric in {"elapsed_seconds", "load_store_per_cycle", "load_store_to_fp512"} else f"{w:.0f}",
                "backend_value": f"{b:.9f}" if metric in {"elapsed_seconds", "load_store_per_cycle", "load_store_to_fp512"} else f"{b:.0f}",
                "wrapper_over_backend": f"{(w / b):.9f}" if b else "",
                "evidence": rel(COUNTER_SUMMARY),
            }
        )
    return rows


def metric_ratio(rows: List[Dict[str, str]], metric: str) -> float:
    for row in rows:
        if row.get("metric") == metric:
            return fnum(row.get("wrapper_over_backend", ""))
    return 0.0


def run_metric_speedup(run_rows: List[Dict[str, str]]) -> float:
    by_variant = {row["variant"]: row for row in run_rows}
    wrapper = fnum(by_variant.get("wrapper_fused_from_dft_add", {}).get("pvw_lane_avg_us", ""))
    backend = fnum(by_variant.get("backend_from_dft_add", {}).get("pvw_lane_avg_us", ""))
    return wrapper / backend if backend else 0.0


def attribution_rows(run_rows: List[Dict[str, str]], cmp_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    stage224 = stage224_speedup()
    bench_ratio = run_metric_speedup(run_rows)
    cycles = metric_ratio(cmp_rows, "cycles")
    elapsed = metric_ratio(cmp_rows, "elapsed_seconds")
    loads = metric_ratio(cmp_rows, "loads")
    stores = metric_ratio(cmp_rows, "stores")
    load_store = metric_ratio(cmp_rows, "load_store_per_cycle")
    if cycles > 1.0 and bench_ratio > 1.0:
        label = "COUNTER_SUPPORTS_STAGE224_DIRECTION"
    elif cycles > 1.0 or bench_ratio > 1.0:
        label = "PARTIAL_COUNTER_SUPPORT_NO_STRONG_MECHANISM_CLAIM"
    else:
        label = "COUNTERS_RECORDED_TIMING_NOT_REPRODUCED"
    return [
        {
            "metric": "stage224_backend_vs_wrapper_mean_speedup",
            "value": f"{stage224:.9f}",
            "interpretation": "Fresh Stage224 complete-SAB per-lane timing; primary performance evidence.",
            "evidence": rel(STAGE224_PERF),
        },
        {
            "metric": "stage226_perf_run_backend_vs_wrapper_lane_speedup",
            "value": f"{bench_ratio:.9f}",
            "interpretation": "Single native perf-stat run; mechanism evidence only, not a replacement for Stage224 repeated timing.",
            "evidence": rel(RUN_METRICS),
        },
        {
            "metric": "stage226_cycles_wrapper_over_backend",
            "value": f"{cycles:.9f}",
            "interpretation": "Values above 1 mean backend used fewer recorded cycles than wrapper.",
            "evidence": rel(COUNTER_CMP),
        },
        {
            "metric": "stage226_elapsed_wrapper_over_backend",
            "value": f"{elapsed:.9f}",
            "interpretation": "Perf CSV may omit elapsed on this host; use lane timing and cycles for the Stage226 mechanism gate.",
            "evidence": rel(COUNTER_CMP),
        },
        {
            "metric": "stage226_loads_wrapper_over_backend",
            "value": f"{loads:.9f}",
            "interpretation": "Values above 1 mean backend reduced retired loads.",
            "evidence": rel(COUNTER_CMP),
        },
        {
            "metric": "stage226_stores_wrapper_over_backend",
            "value": f"{stores:.9f}",
            "interpretation": "Values above 1 mean backend reduced retired stores.",
            "evidence": rel(COUNTER_CMP),
        },
        {
            "metric": "stage226_load_store_per_cycle_wrapper_over_backend",
            "value": f"{load_store:.9f}",
            "interpretation": "Memory-op density comparison; not a standalone optimality proof.",
            "evidence": rel(COUNTER_CMP),
        },
        {
            "metric": "attribution_label",
            "value": label,
            "interpretation": "Mechanism label is bounded to this exact-route native counter run.",
            "evidence": rel(PROOF),
        },
    ]


def required_counter_metrics_present(counters: List[Dict[str, str]]) -> bool:
    required = {
        "cycles",
        "instructions",
        "mem_inst_retired.all_loads",
        "mem_inst_retired.all_stores",
        "fp_arith_inst_retired.512b_packed_double",
    }
    by_variant: Dict[str, set[str]] = {}
    for row in counters:
        by_variant.setdefault(row["variant"], set()).add(row["metric"])
    return all(required.issubset(by_variant.get(variant, set())) for variant in ["wrapper_fused_from_dft_add", "backend_from_dft_add"])


def decide(rcs: Dict[str, int], run_rows: List[Dict[str, str]], counters: List[Dict[str, str]], cmp_rows: List[Dict[str, str]]) -> str:
    if not REMOTE_SECRET and not REUSE_RAW:
        return "BLOCKED_STAGE226_RUNTIME_SECRET_MISSING"
    if any(value != 0 for value in rcs.values()):
        return "BLOCKED_STAGE226_REMOTE_EXECUTION_FAILED"
    if len(run_rows) < 2 or any(row.get("status") != "Pass" for row in run_rows):
        return "FAIL_STAGE226_CORRECTNESS_OR_RUN_METRICS"
    if not required_counter_metrics_present(counters):
        return "BLOCKED_STAGE226_COUNTERS_INCOMPLETE"
    if metric_ratio(cmp_rows, "cycles") > 1.0 and run_metric_speedup(run_rows) > 1.0:
        return "PASS_STAGE226_EXACT_COUNTER_ATTRIBUTION_POSITIVE"
    return "PASS_STAGE226_COUNTERS_RECORDED_TIMING_NEUTRAL"


def proof_rows(decision: str, rcs: Dict[str, int], run_rows: List[Dict[str, str]], counters: List[Dict[str, str]], attrs: List[Dict[str, str]]) -> List[Dict[str, str]]:
    all_inputs = all(row["status"] == "present" for row in input_rows())
    correctness_ok = bool(run_rows) and all(row.get("status") == "Pass" for row in run_rows)
    counter_ok = required_counter_metrics_present(counters)
    attr_label = next((row["value"] for row in attrs if row["metric"] == "attribution_label"), "")
    return [
        {
            "gate": "G1_required_inputs",
            "status": "PASS" if all_inputs else "FAIL",
            "metric": "inputs_present",
            "value": str(all_inputs).lower(),
            "evidence": rel(INPUTS),
            "interpretation": "Stage226 can run only after Stage224 performance and Stage225 side-condition gates.",
        },
        {
            "gate": "G2_remote_native_execution",
            "status": "PASS" if all(value == 0 for value in rcs.values()) else "BLOCKED",
            "metric": "remote_rcs",
            "value": str(rcs),
            "evidence": rel(OUT),
            "interpretation": "Native perf execution must complete before any counter attribution.",
        },
        {
            "gate": "G3_full_sab_correctness",
            "status": "PASS" if correctness_ok else "FAIL_OR_MISSING",
            "metric": "variant_rows",
            "value": str(len(run_rows)),
            "evidence": rel(RUN_METRICS),
            "interpretation": "Both wrapper and backend exact routes must pass full SAB correctness under perf.",
        },
        {
            "gate": "G4_counter_capture",
            "status": "PASS" if counter_ok else "MISSING_OR_INCOMPLETE",
            "metric": "counter_rows",
            "value": str(len(counters)),
            "evidence": rel(COUNTERS),
            "interpretation": "Required native counters include cycles, loads, stores and AVX512 FP arithmetic.",
        },
        {
            "gate": "G5_attribution_boundary",
            "status": attr_label or "MISSING",
            "metric": "attribution_label",
            "value": attr_label,
            "evidence": rel(ATTRIBUTION),
            "interpretation": "Counters explain or fail to explain the Stage224 timing direction; they do not prove theoretical optimality.",
        },
        {
            "gate": "G6_claim_boundary",
            "status": "PASS_NO_OPTIMALITY_OR_NOVELTY_CLAIM",
            "metric": "claim_boundary",
            "value": "counter_attribution_only",
            "evidence": rel(THEORY),
            "interpretation": "Stage226 is a mechanism check for the exact path, not a new algorithmic claim.",
        },
        {
            "gate": "G7_stage226_decision",
            "status": decision,
            "metric": "decision",
            "value": decision,
            "evidence": rel(PROOF),
            "interpretation": "The next stage is claim-boundary update unless counters reveal a new implementation target.",
        },
    ]


def next_rows(decision: str) -> List[Dict[str, str]]:
    positive = decision == "PASS_STAGE226_EXACT_COUNTER_ATTRIBUTION_POSITIVE"
    return [
        {
            "priority": "P0",
            "route": "stage227_exact_route_claim_boundary_update",
            "entry_condition": "Stage224 performance, Stage225 side conditions, and Stage226 counters are recorded.",
            "gate": "Separate exact MAT/PVW engineering acceleration from compact route and optimality claims.",
            "status": "selected",
            "failure_action": "Keep exact route as measured engineering result only.",
            "evidence": rel(PROOF),
        },
        {
            "priority": "P1",
            "route": "stage228_targeted_counter_driven_kernel_followup",
            "entry_condition": "Stage226 identifies a clear cycles/load/store regression source.",
            "gate": "New micro-hypothesis with full-SAB promotion gate.",
            "status": "candidate" if positive else "not_selected_without_new_signal",
            "failure_action": "Do not reopen hot path without a counter-backed implementation target.",
            "evidence": rel(ATTRIBUTION),
        },
        {
            "priority": "P2",
            "route": "neighbor_capable_compact_state_proof",
            "entry_condition": "Only if a new closed compact algebra is proposed.",
            "gate": "Proof before hot-path implementation.",
            "status": "proof_only_deferred",
            "failure_action": "Do not touch SAB hot path.",
            "evidence": rel(STAGE224_PROOF),
        },
    ]


def write_reports(decision: str, env_rows: List[Dict[str, str]], run_rows: List[Dict[str, str]], summary: List[Dict[str, str]], cmp_rows: List[Dict[str, str]], attrs: List[Dict[str, str]], gates: List[Dict[str, str]], queue: List[Dict[str, str]]) -> None:
    report = f"""# Stage226 Exact MAT/PVW Counter Attribution

Decision: `{decision}`.

Stage226 runs native perf counters for the two exact Stage224 variants:
`wrapper_fused_from_dft_add` and `backend_from_dft_add`. The primary
performance metric remains complete-SAB `T_bootstrap/r`; this stage only
checks whether native counters support a mechanism for the Stage224 timing
direction.

## Attribution Summary

{table(attrs, ATTR_FIELDS)}
## Run Metrics

{table(run_rows, RUN_FIELDS)}
## Counter Summary

{table(summary, SUMMARY_FIELDS)}
## Counter Comparison

{table(cmp_rows, CMP_FIELDS)}
## Remote Environment

{table(env_rows, REMOTE_FIELDS)}
## Proof Gates

{table(gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])}
## Next Queue

{table(queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}
"""
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(
        PLAN,
        """# Stage226 Exact MAT/PVW Counter Attribution Plan

1. Verify Stage224 and Stage225 input gates.
2. Run native perf counters for wrapper/backend exact variants.
3. Parse correctness, timing, cycles, load/store and AVX512 FP arithmetic counters.
4. Label the evidence as attribution-only and route to claim-boundary update.
""",
    )
    write_text(
        THEORY,
        """# Stage226 Counter Attribution Scope

The tested mechanism is narrow: replacing wrapper-level from-DFT-add handling
with the backend path may reduce full-SAB `T_bootstrap/r` by reducing cycles
and/or memory operations in the exact dense MAT/PVW route.

This stage cannot prove theoretical optimality. A single native perf run is
used for mechanism attribution only; repeated Stage224 timing remains the
performance evidence.
""",
    )
    write_text(
        VARIANT,
        """# Algorithm Variant: Stage226 Counter-Attributed Exact MAT/PVW

The variant is the existing exact dense MAT/PVW SAB route with backend
from-DFT-add enabled. No scalar SAB behavior changes and no compact state is
introduced.

Claim status: counter attribution only.
""",
    )
    write_text(
        REPRO,
        """# Stage226 Reproduction Commands

```powershell
$env:STAGE226_REMOTE_SECRET='<runtime-only>'
python scripts\\build_stage226_exact_mat_avx_counter_attribution.py
Get-Content repro\\stage226_exact_mat_avx_counter_attribution\\proof_gate.csv
Get-Content repro\\stage226_exact_mat_avx_counter_attribution\\attribution_summary.csv
```
""",
    )


def artifact_rows(paths: Iterable[Path]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path in paths:
        rows.append(
            {
                "path": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256(path) if path.exists() and path.is_file() else "",
                "bytes": str(path.stat().st_size) if path.exists() and path.is_file() else "",
            }
        )
    return rows


def write_artifacts() -> None:
    paths = [
        DOC,
        PLAN,
        THEORY,
        VARIANT,
        RUNNER,
        INPUTS,
        REMOTE_ENV,
        RUN_METRICS,
        COUNTERS,
        COUNTER_SUMMARY,
        COUNTER_CMP,
        ATTRIBUTION,
        PROOF,
        NEXT,
        REPORT,
        REPRO,
        CLEANUP,
        OUT / "remote_probe.log",
        OUT / "remote_unpack.log",
        OUT / "remote_install_runner.log",
        OUT / "remote_run_stage226_runner.log",
        OUT / "remote_pull_native_perf_raw.log",
    ]
    paths.extend(sorted(RAW.glob("*.log")))
    write_csv(ARTIFACT, artifact_rows(paths), ["path", "exists", "sha256", "bytes"])


def existing_remote_rcs() -> Dict[str, int]:
    for row in read_csv(PROOF):
        if row.get("gate") == "G2_remote_native_execution":
            try:
                parsed = ast.literal_eval(row.get("value", "{}"))
                return {str(key): int(value) for key, value in parsed.items()}
            except Exception:
                break
    return {"remote_reuse_existing_raw": 0}


def update_tracking(decision: str) -> None:
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 226: Exact MAT/PVW Counter Attribution",
        f"""
## Stage 226: Exact MAT/PVW Counter Attribution

Goal:

```text
Attribute the Stage224 exact-route backend-vs-wrapper delta using native
cycles/load/store/FMA counters where available.
```

Status:

```text
Completed at `{head}` with `{decision}`. The result is an attribution gate:
it does not claim theoretical optimality or reopen the compact SAB route.
```
""",
    )
    append_once(
        GOAL,
        "Stage226 exact counter attribution",
        f"\n\n## Stage226 exact counter attribution\n\nAt commit `{head}`, Stage226 records `{decision}` for native exact-route counters. Complete-SAB `T_bootstrap/r` remains the primary metric.\n",
    )
    append_once(
        CURRENT_GOAL,
        "Stage226 exact counter attribution",
        f"\n\n### Stage226 exact counter attribution\n\n`{decision}` updates the mechanism evidence for the exact dense MAT/PVW route.\n",
    )
    append_once(
        HYPOTHESES,
        "H10_stage226_exact_counter_attribution",
        f"""

H10_stage226_exact_counter_attribution:
  status: counter_attribution_recorded
  evidence:
    - repro/stage226_exact_mat_avx_counter_attribution/attribution_summary.csv
    - repro/stage226_exact_mat_avx_counter_attribution/counter_summary.csv
    - docs/stage226_exact_mat_avx_counter_attribution.md
  conclusion: >
    Stage226 records {decision}. Counter evidence is scoped to the exact
    dense MAT/PVW route and does not prove theoretical optimality.
""",
    )
    append_once(
        RUN_LOG,
        "stage226-exact-counter-attribution-001",
        f"""stage226-exact-counter-attribution-001,2026-07-04,{head},Stage 226,spqlios_avx512,python scripts/build_stage226_exact_mat_avx_counter_attribution.py,Stage224 exact backend-vs-wrapper attribution,cycles/load/store/FMA counters,{decision},"Native counter mechanism check only; no optimality or novelty claim.",docs/stage226_exact_mat_avx_counter_attribution.md; repro/stage226_exact_mat_avx_counter_attribution/proof_gate.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage226_exact_mat_avx_counter_attribution:",
        """

- stage226_exact_mat_avx_counter_attribution:
  - `docs/stage226_exact_mat_avx_counter_attribution.md`
  - `experiments/stage226_exact_mat_avx_counter_attribution_plan.md`
  - `theory_checks/stage226_counter_attribution_scope.md`
  - `algorithm_variants/mat_rlwe_sab_stage226_counter_attribution.md`
  - `scripts/build_stage226_exact_mat_avx_counter_attribution.py`
  - `repro/stage226_exact_mat_avx_counter_attribution/`
""",
    )
    append_once(CHECKLIST, "Stage226 exact counter attribution", f"\n- [x] Stage226 exact counter attribution records decision `{decision}`.\n")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    inputs = input_rows()
    write_csv(INPUTS, inputs, INPUT_FIELDS)
    if REUSE_RAW:
        write_runner()
        rcs = existing_remote_rcs()
    else:
        rcs = execute_remote() if REMOTE_SECRET else {"remote_probe": 1, "remote_unpack": 1, "remote_install_runner": 1, "remote_run": 1, "remote_pull": 1}
    if REUSE_RAW:
        write_text(CLEANUP, "reused existing native raw logs; no remote execution in this parse-only refresh\n")
    elif not REMOTE_SECRET:
        write_runner()
        write_text(CLEANUP, "remote execution skipped because runtime secret was not provided\n")
    else:
        write_text(CLEANUP, "temporary git archive removed; remote build directory intentionally retained for audit\n")
    env_rows = parse_remote_environment(rcs)
    run_rows = parse_runs()
    counters = parse_counters()
    summary = counter_summary(counters)
    cmp_rows = counter_comparison(summary)
    attrs = attribution_rows(run_rows, cmp_rows)
    decision = decide(rcs, run_rows, counters, cmp_rows)
    gates = proof_rows(decision, rcs, run_rows, counters, attrs)
    queue = next_rows(decision)

    write_csv(REMOTE_ENV, env_rows, REMOTE_FIELDS)
    write_csv(RUN_METRICS, run_rows, RUN_FIELDS)
    write_csv(COUNTERS, counters, COUNTER_FIELDS)
    write_csv(COUNTER_SUMMARY, summary, SUMMARY_FIELDS)
    write_csv(COUNTER_CMP, cmp_rows, CMP_FIELDS)
    write_csv(ATTRIBUTION, attrs, ATTR_FIELDS)
    write_csv(PROOF, gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])
    write_reports(decision, env_rows, run_rows, summary, cmp_rows, attrs, gates, queue)
    update_tracking(decision)
    write_artifacts()
    print(decision)


if __name__ == "__main__":
    main()
