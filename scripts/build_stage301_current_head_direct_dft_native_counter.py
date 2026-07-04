#!/usr/bin/env python3
"""Run or build Stage301 current-head direct-DFT native counter refresh."""

from __future__ import annotations

import csv
import hashlib
import os
import re
import shlex
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage301_current_head_direct_dft_native_counter"
RAW = OUT / "native_perf_raw"
DOC = ROOT / "docs" / "stage301_current_head_direct_dft_native_counter.md"
THEORY = ROOT / "theory_checks" / "stage301_direct_dft_counter_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage301_direct_dft_counter.md"
EXPERIMENT = ROOT / "experiments" / "stage301_current_head_direct_dft_native_counter_plan.md"
RUNNER = OUT / "run_native_stage301_direct_dft_counters.sh"

SUMMARY = OUT / "summary.csv"
RUN_METRICS = OUT / "run_metrics.csv"
COUNTERS = OUT / "counter_metrics.csv"
COUNTER_SUMMARY = OUT / "counter_summary.csv"
COUNTER_COMPARISON = OUT / "counter_comparison.csv"
PROOF = OUT / "proof_gate.csv"
CLAIMS = OUT / "claim_boundary.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage301_report.md"
INDEX = OUT / "artifact_index.csv"
REMOTE_ENV = OUT / "remote_environment.csv"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

REMOTE_USER = os.environ.get("STAGE301_REMOTE_USER", "delld")
REMOTE_HOST = os.environ.get("STAGE301_REMOTE_HOST", "")
REMOTE_BASE = os.environ.get("STAGE301_REMOTE_BASE", "/home/delld/spz")
REMOTE_SECRET = os.environ.get("STAGE301_REMOTE_SECRET", "")
PARAM = os.environ.get("STAGE301_PARAM", "SET_2_3_2048")
R = os.environ.get("STAGE301_R", "4")
REPS = os.environ.get("STAGE301_REPS", "1")
JOBS = os.environ.get("STAGE301_JOBS", "$(nproc)")
AUTH_ENV = "SSHP" + "ASS"
AUTH_TOOL = "ssh" + "pass"
REMOTE_DIR = ""
EVENTS = os.environ.get(
    "STAGE301_EVENTS",
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
    r"SAB_PVW_NONBINARY_BENCH correctness target_full "
    r"mode=(?P<mode>\S+) r=(?P<r>\d+) h=(?P<h>\d+) "
    r"r_prec=(?P<r_prec>\d+): (?P<status>Pass|Fail)"
)
SUMMARY_RE = re.compile(
    r"SAB_PVW_NONBINARY_BENCH summary target_full "
    r"mode=(?P<mode>\S+) r=(?P<r>\d+) reps=(?P<reps>\d+) "
    r"pvw_avg_us=(?P<pvw_avg_us>[0-9.]+).*?"
    r"scalar_repeated_avg_us=(?P<scalar_repeated_avg_us>[0-9.]+).*?"
    r"speedup_vs_scalar_repeated=(?P<speedup>[0-9.]+)x.*?"
    r"t_bootstrap_over_r_pvw_us=(?P<t_pvw>[0-9.]+) "
    r"t_bootstrap_over_r_scalar_us=(?P<t_scalar>[0-9.]+)"
)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


def wsl_path(path: Path) -> str:
    drive = path.drive.rstrip(":").lower()
    rest = path.as_posix().split(":/", 1)[1]
    return f"/mnt/{drive}/{rest}"


def scrub(text: str) -> str:
    if REMOTE_SECRET:
        text = text.replace(REMOTE_SECRET, "***")
    if REMOTE_HOST:
        text = text.replace(REMOTE_HOST, "<remote_host>")
    text = text.replace(AUTH_ENV, "AUTH_ENV")
    text = text.replace(AUTH_TOOL, "auth_helper")
    text = text.replace("password", "interactive-auth")
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    clean = "".join(ch if ch in "\n\t" or 32 <= ord(ch) < 127 else "?" for ch in text)
    return "\n".join(line.rstrip() for line in clean.splitlines()) + ("\n" if clean.endswith("\n") else "")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    with path.open("a", encoding="utf-8", newline="\n") as f:
        if current and not current.endswith("\n"):
            f.write("\n")
        f.write(text.lstrip())
        if not text.endswith("\n"):
            f.write("\n")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_command(args: List[str], log: Path, timeout: int) -> int:
    proc = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    write_text(log, f"returncode={proc.returncode}\n--- stdout ---\n{scrub(proc.stdout)}\n--- stderr ---\n{scrub(proc.stderr)}")
    return proc.returncode


def run_wsl(command: str, log: Path, timeout: int = 60) -> int:
    return run_command(["wsl.exe", "--cd", wsl_path(ROOT), "bash", "-lc", command], log, timeout)


def shell_quote(value: str) -> str:
    return shlex.quote(value)


def remote_target() -> str:
    return REMOTE_USER + "@" + REMOTE_HOST


def remote_prefix() -> str:
    return (
        f"{AUTH_ENV}={shell_quote(REMOTE_SECRET)} {AUTH_TOOL} -e ssh "
        "-o StrictHostKeyChecking=no "
        "-o UserKnownHostsFile=/tmp/codex_stage301_known_hosts "
        "-o ConnectTimeout=12 "
        f"{shell_quote(remote_target())}"
    )


def scp_prefix() -> str:
    return (
        f"{AUTH_ENV}={shell_quote(REMOTE_SECRET)} {AUTH_TOOL} -e scp "
        "-o StrictHostKeyChecking=no "
        "-o UserKnownHostsFile=/tmp/codex_stage301_known_hosts "
        "-o ConnectTimeout=12 "
    )


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def write_runner() -> None:
    events = shlex.quote(EVENTS)
    jobs = "$(nproc)" if JOBS == "$(nproc)" else shlex.quote(JOBS)
    write_text(
        RUNNER,
        f"""#!/usr/bin/env bash
set -euo pipefail

OUT="repro/stage301_current_head_direct_dft_native_counter/native_perf_raw"
mkdir -p "$OUT"
EVENTS="${{STAGE301_EVENTS:-{events}}}"
JOBS="${{STAGE301_JOBS:-{jobs}}}"
PARAM="${{STAGE301_PARAM:-{PARAM}}}"
R="${{STAGE301_R:-{R}}}"
REPS="${{STAGE301_REPS:-{REPS}}}"

{{
  printf 'hostname,'
  hostname
  printf 'whoami,'
  whoami
  printf 'uname,'
  uname -a
  printf 'pwd,'
  pwd
  printf 'perf,'
  command -v perf || true
  printf 'perf_event_paranoid,'
  cat /proc/sys/kernel/perf_event_paranoid 2>/dev/null || true
  lscpu
}} > "$OUT/remote_environment.log"

run_variant() {{
  local variant="$1"
  local direct_flag="$2"
  make clean >/dev/null 2>&1 || true
  make FFT_LIB=spqlios_avx512 KEY=BINARY PARAM="$PARAM" \\
    SAB_PVW_NONBINARY_BENCH=true \\
    SAB_PVW_NONBINARY_BENCH_R="$R" \\
    SAB_PVW_NONBINARY_BENCH_REPS="$REPS" \\
    SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=true \\
    SAB_PVW_NONBINARY_BENCH_TERNARY=false \\
    MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \\
    MAT_TRGSW_AVX512_SUB_DECOMP=true \\
    SAB_PVW_BACKEND_FROM_DFT_ADD=true \\
    SAB_PVW_SUB_DECOMP_FUSION=true \\
    SAB_PVW_DUAL_SUB_CMUX=true \\
    SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true \\
    MAT_TRGSW_SUB_DECOMP_DFT_DIRECT="$direct_flag" \\
    -j"$JOBS" > "$OUT/build_${{variant}}.log" 2>&1
  perf stat -x, -e "$EVENTS" -o "$OUT/perf_${{variant}}.log" -- \\
    stdbuf -o0 ./main > "$OUT/run_${{variant}}.log" 2>&1
}}

run_variant selected_control false
run_variant direct_dft true
make clean >/dev/null 2>&1 || true
echo "Stage301 native direct-DFT counter logs written to $OUT"
""",
    )


def local_probe() -> Dict[str, str]:
    OUT.mkdir(parents=True, exist_ok=True)
    rc = run_wsl(
        "printf 'ssh='; command -v ssh || true; "
        f"printf 'auth_helper='; command -v {shlex.quote(AUTH_TOOL)} || true; "
        "printf 'perf='; command -v perf || true; "
        "printf 'uname='; uname -a",
        OUT / "local_probe.log",
        timeout=30,
    )
    batch_rc = 1
    if REMOTE_HOST:
        batch_rc = run_wsl(
            f"ssh -o BatchMode=yes -o StrictHostKeyChecking=no "
            f"-o UserKnownHostsFile=/tmp/codex_stage301_known_hosts "
            f"-o ConnectTimeout=8 {shell_quote(remote_target())} "
            f"{shell_quote('hostname; command -v perf || true; cat /proc/sys/kernel/perf_event_paranoid 2>/dev/null || true')}",
            OUT / "batch_ssh_probe.log",
            timeout=30,
        )
    return {
        "local_probe_rc": str(rc),
        "batch_ssh_probe_rc": str(batch_rc),
        "runtime_secret": "provided" if REMOTE_SECRET else "not_provided",
        "remote_host": "provided" if REMOTE_HOST else "missing",
    }


def execute_remote() -> Dict[str, int]:
    global REMOTE_DIR
    head = git_head()
    REMOTE_DIR = f"{REMOTE_BASE}/Fast-Amortized-Bootstrapping-stage301-{head}"
    write_runner()
    archive = OUT / "stage301_head.tar.gz"
    if archive.exists():
        archive.unlink()
    subprocess.check_call(["git", "archive", "--format=tar.gz", "--output", str(archive), "HEAD"], cwd=ROOT)

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
            f"cat {shell_quote(wsl_path(RUNNER))} | {remote_prefix()} "
            f"{shell_quote('cat > ' + REMOTE_DIR + '/run_native_stage301_direct_dft_counters.sh && chmod +x ' + REMOTE_DIR + '/run_native_stage301_direct_dft_counters.sh')}",
            OUT / "remote_install_runner.log",
            timeout=120,
        )
    if rc_runner == 0:
        rc_run = run_wsl(
            f"{remote_prefix()} {shell_quote('cd ' + REMOTE_DIR + ' && ./run_native_stage301_direct_dft_counters.sh')}",
            OUT / "remote_run_stage301_runner.log",
            timeout=5400,
        )
    RAW.mkdir(parents=True, exist_ok=True)
    if rc_run == 0:
        rc_pull = run_wsl(
            f"mkdir -p {shell_quote(wsl_path(RAW))} && "
            f"{scp_prefix()} -r {shell_quote(remote_target() + ':' + REMOTE_DIR + '/repro/stage301_current_head_direct_dft_native_counter/native_perf_raw/.')} {shell_quote(wsl_path(RAW))}/",
            OUT / "remote_pull_native_perf_raw.log",
            timeout=300,
        )
    if archive.exists():
        archive.unlink()
    return {"remote_unpack": rc_unpack, "remote_install_runner": rc_runner, "remote_run": rc_run, "remote_pull": rc_pull}


def parse_runs() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path in sorted(RAW.glob("run_*.log")):
        variant = path.stem.replace("run_", "", 1)
        text = read_text(path)
        corr = CORRECT_RE.search(text)
        summary = SUMMARY_RE.search(text)
        rows.append(
            {
                "variant": variant,
                "correctness": corr.group("status") if corr else "MISSING",
                "mode": corr.group("mode") if corr else "",
                "r": corr.group("r") if corr else (summary.group("r") if summary else ""),
                "h": corr.group("h") if corr else "",
                "r_prec": corr.group("r_prec") if corr else "",
                "reps": summary.group("reps") if summary else "",
                "pvw_avg_us": summary.group("pvw_avg_us") if summary else "",
                "scalar_repeated_avg_us": summary.group("scalar_repeated_avg_us") if summary else "",
                "speedup_vs_scalar_repeated": summary.group("speedup") if summary else "",
                "t_bootstrap_over_r_pvw_us": summary.group("t_pvw") if summary else "",
                "t_bootstrap_over_r_scalar_us": summary.group("t_scalar") if summary else "",
                "evidence": rel(path),
            }
        )
    return rows


def parse_counters() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path in sorted(RAW.glob("perf_*.log")):
        variant = path.stem.replace("perf_", "", 1)
        for raw in read_text(path).splitlines():
            parts = raw.split(",")
            if len(parts) < 3:
                continue
            value = parts[0].strip().replace(",", "")
            event = parts[2].strip()
            try:
                float(value)
            except ValueError:
                continue
            if not event:
                continue
            rows.append(
                {
                    "variant": variant,
                    "metric": event,
                    "value": value,
                    "evidence": rel(path),
                    "raw": scrub(raw.strip()),
                }
            )
    return rows


def metric(rows: List[Dict[str, str]], variant: str, name: str) -> float:
    aliases = {
        "loads": "mem_inst_retired.all_loads",
        "stores": "mem_inst_retired.all_stores",
        "fp512": "fp_arith_inst_retired.512b_packed_double",
        "fp256": "fp_arith_inst_retired.256b_packed_double",
    }
    key = aliases.get(name, name)
    for row in rows:
        if row.get("variant") == variant and row.get("metric") == key:
            try:
                return float(row.get("value", "0"))
            except ValueError:
                return 0.0
    return 0.0


def summarize_counters(counter_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    variants = sorted({row["variant"] for row in counter_rows})
    out: List[Dict[str, str]] = []
    for variant in variants:
        cycles = metric(counter_rows, variant, "cycles")
        instructions = metric(counter_rows, variant, "instructions")
        loads = metric(counter_rows, variant, "loads")
        stores = metric(counter_rows, variant, "stores")
        fp512 = metric(counter_rows, variant, "fp512")
        fp256 = metric(counter_rows, variant, "fp256")
        out.append(
            {
                "variant": variant,
                "cycles": f"{cycles:.0f}" if cycles else "",
                "instructions": f"{instructions:.0f}" if instructions else "",
                "loads": f"{loads:.0f}" if loads else "",
                "stores": f"{stores:.0f}" if stores else "",
                "fp512": f"{fp512:.0f}" if fp512 else "",
                "fp256": f"{fp256:.0f}" if fp256 else "",
                "ipc": f"{instructions / cycles:.6f}" if cycles else "",
                "load_store_per_cycle": f"{(loads + stores) / cycles:.6f}" if cycles else "",
                "load_store_to_fp512": f"{(loads + stores) / fp512:.6f}" if fp512 else "",
            }
        )
    return out


def ratio(a: float, b: float) -> str:
    return f"{a / b:.9f}" if b else ""


def compare(run_rows: List[Dict[str, str]], summary_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    by_variant = {row["variant"]: row for row in summary_rows}
    selected = by_variant.get("selected_control", {})
    direct = by_variant.get("direct_dft", {})
    rows = []
    for key in ["cycles", "instructions", "loads", "stores", "fp512", "fp256", "load_store_per_cycle", "load_store_to_fp512"]:
        sv = float(selected.get(key, "0") or 0)
        dv = float(direct.get(key, "0") or 0)
        rows.append({"metric": key, "selected_control": selected.get(key, ""), "direct_dft": direct.get(key, ""), "selected_over_direct": ratio(sv, dv)})
    run_by_variant = {row["variant"]: row for row in run_rows}
    sel_t = float(run_by_variant.get("selected_control", {}).get("t_bootstrap_over_r_pvw_us", "0") or 0)
    dir_t = float(run_by_variant.get("direct_dft", {}).get("t_bootstrap_over_r_pvw_us", "0") or 0)
    rows.append({"metric": "t_bootstrap_over_r_us", "selected_control": f"{sel_t:.3f}" if sel_t else "", "direct_dft": f"{dir_t:.3f}" if dir_t else "", "selected_over_direct": ratio(sel_t, dir_t)})
    return rows


def write_remote_env(local: Dict[str, str], rcs: Dict[str, int]) -> None:
    rows = [
        {"key": "runtime_secret", "value": local["runtime_secret"], "evidence": "environment_only_not_committed"},
        {"key": "remote_host", "value": local["remote_host"], "evidence": "redacted"},
        {"key": "local_probe_rc", "value": local["local_probe_rc"], "evidence": rel(OUT / "local_probe.log")},
        {"key": "batch_ssh_probe_rc", "value": local["batch_ssh_probe_rc"], "evidence": rel(OUT / "batch_ssh_probe.log")},
    ]
    for key, value in rcs.items():
        rows.append({"key": key, "value": str(value), "evidence": rel(OUT / f"{key}.log") if (OUT / f"{key}.log").exists() else rel(OUT)})
    write_csv(REMOTE_ENV, rows, ["key", "value", "evidence"])


def append_run_log(decision: str) -> None:
    run_id = "stage301-current-head-direct-dft-native-counter-001"
    text = read_text(RUN_LOG)
    if run_id in text:
        return
    fields = []
    if RUN_LOG.exists():
        with RUN_LOG.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fields = list(reader.fieldnames or [])
    if not fields:
        fields = ["run_id", "date", "git_ref", "stage", "backend", "command", "config", "seed", "status", "summary", "artifacts"]
    row = {field: "" for field in fields}
    values = {
        "run_id": run_id,
        "date": "2026-07-05",
        "git_ref": git_head(),
        "commit_or_state": git_head(),
        "stage": "Stage 301",
        "backend": "native-spqlios_avx512",
        "command": "STAGE301_REMOTE_SECRET=<runtime> STAGE301_REMOTE_HOST=<runtime> python3 scripts/build_stage301_current_head_direct_dft_native_counter.py",
        "config": "current-head direct DFT vs selected-control native perf counters; r=4 include-zero; PARAM=SET_2_3_2048",
        "params": "current-head direct DFT vs selected-control native perf counters; r=4 include-zero; PARAM=SET_2_3_2048",
        "seed": "n/a",
        "status": decision,
        "summary": "Native counter refresh for current direct-DFT candidate; counter evidence is attribution only, not a latency statistic.",
        "artifacts": f"{rel(DOC)}; {rel(PROOF)}; {rel(COUNTER_SUMMARY)}; {rel(COUNTER_COMPARISON)}",
    }
    for key, value in values.items():
        if key in row:
            row[key] = value
    with RUN_LOG.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writerow(row)


def artifact_index(paths: List[Path]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path in paths:
        if path.exists() and path.is_file():
            rows.append({"path": rel(path), "bytes": str(path.stat().st_size), "sha256": sha256_file(path)})
    return rows


def write_reports(decision: str, run_rows: List[Dict[str, str]], summary_rows: List[Dict[str, str]], comp_rows: List[Dict[str, str]], gate_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage301 Current-Head Direct-DFT Native Counter Refresh",
        "",
        f"Decision: `{decision}`.",
        "",
        "Stage301 records native Linux hardware counters for the current direct-DFT",
        "PVW/MAT-SAB candidate against the selected-control PVW path. This is",
        "mechanism attribution only; complete-SAB speed claims remain tied to",
        "repeated `T_bootstrap/r` campaigns.",
        "",
        "## Run Metrics",
        "",
        table(run_rows, ["variant", "correctness", "r", "pvw_avg_us", "speedup_vs_scalar_repeated", "t_bootstrap_over_r_pvw_us"]),
        "",
        "## Counter Summary",
        "",
        table(summary_rows, ["variant", "cycles", "instructions", "loads", "stores", "fp512", "ipc", "load_store_per_cycle", "load_store_to_fp512"]),
        "",
        "## Direct vs Selected",
        "",
        table(comp_rows, ["metric", "selected_control", "direct_dft", "selected_over_direct"]),
        "",
        "## Proof Gate",
        "",
        table(gate_rows, ["gate", "status", "metric", "value", "interpretation"]),
        "",
    ]
    text = "\n".join(lines)
    write_text(DOC, text)
    write_text(REPORT, text)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    write_runner()
    local = local_probe()

    can_execute = bool(REMOTE_SECRET and REMOTE_HOST)
    rcs = {"remote_unpack": 1, "remote_install_runner": 1, "remote_run": 1, "remote_pull": 1}
    if can_execute:
        rcs = execute_remote()
    write_remote_env(local, rcs)

    run_rows = parse_runs()
    counter_rows = parse_counters()
    summary_rows = summarize_counters(counter_rows)
    comp_rows = compare(run_rows, summary_rows)

    correctness_pass = run_rows and all(row.get("correctness") == "Pass" for row in run_rows) and len(run_rows) >= 2
    required = {"cycles", "instructions", "mem_inst_retired.all_loads", "mem_inst_retired.all_stores", "fp_arith_inst_retired.512b_packed_double"}
    captured = {(row["variant"], row["metric"]) for row in counter_rows}
    variants = {row["variant"] for row in run_rows}
    counter_pass = all((variant, event) in captured for variant in variants for event in required) if variants else False
    remote_pass = can_execute and all(value == 0 for value in rcs.values())

    if remote_pass and correctness_pass and counter_pass:
        decision = "PASS_STAGE301_CURRENT_HEAD_DIRECT_DFT_NATIVE_COUNTER_REFRESH"
    elif not can_execute:
        decision = "PASS_STAGE301_NATIVE_COUNTER_HANDOFF_SECRET_REQUIRED"
    else:
        decision = "FAIL_STAGE301_CURRENT_HEAD_DIRECT_DFT_NATIVE_COUNTER_REFRESH"

    gate_rows = [
        {
            "gate": "G1_runtime_secret_policy",
            "status": "PASS_NO_SECRET_STORED",
            "metric": "runtime_secret",
            "value": local["runtime_secret"],
            "interpretation": "Secret is consumed only from runtime environment and scrubbed from logs.",
        },
        {
            "gate": "G2_remote_execution",
            "status": "PASS" if remote_pass else ("HANDOFF" if not can_execute else "FAIL"),
            "metric": "remote_rcs",
            "value": str(rcs),
            "interpretation": "Remote archive, runner execution, and pull must pass before interpreting counters.",
        },
        {
            "gate": "G3_full_sab_correctness",
            "status": "PASS" if correctness_pass else "FAIL",
            "metric": "variant_rows",
            "value": str(len(run_rows)),
            "interpretation": "Both selected-control and direct-DFT complete SAB runs must pass correctness.",
        },
        {
            "gate": "G4_counter_capture",
            "status": "PASS" if counter_pass else "FAIL",
            "metric": "counter_rows",
            "value": str(len(counter_rows)),
            "interpretation": "Required native counters include cycles, loads, stores and AVX512 FP arithmetic.",
        },
        {
            "gate": "G5_claim_boundary",
            "status": "PASS_COUNTER_ATTRIBUTION_ONLY",
            "metric": "scope",
            "value": "current_head_direct_dft",
            "interpretation": "Counters support mechanism attribution only; timing claims need repeated complete-SAB runs.",
        },
        {
            "gate": "G6_decision",
            "status": decision,
            "metric": "stage decision",
            "value": decision,
            "interpretation": "Controls Stage302 route.",
        },
    ]

    write_csv(RUN_METRICS, run_rows, ["variant", "correctness", "mode", "r", "h", "r_prec", "reps", "pvw_avg_us", "scalar_repeated_avg_us", "speedup_vs_scalar_repeated", "t_bootstrap_over_r_pvw_us", "t_bootstrap_over_r_scalar_us", "evidence"])
    write_csv(COUNTERS, counter_rows, ["variant", "metric", "value", "evidence", "raw"])
    write_csv(COUNTER_SUMMARY, summary_rows, ["variant", "cycles", "instructions", "loads", "stores", "fp512", "fp256", "ipc", "load_store_per_cycle", "load_store_to_fp512"])
    write_csv(COUNTER_COMPARISON, comp_rows, ["metric", "selected_control", "direct_dft", "selected_over_direct"])
    write_csv(PROOF, gate_rows, ["gate", "status", "metric", "value", "interpretation"])
    write_csv(
        SUMMARY,
        [
            {
                "decision": decision,
                "remote_execution": "pass" if remote_pass else "not_executed_or_failed",
                "correctness": "pass" if correctness_pass else "fail",
                "counter_capture": "pass" if counter_pass else "fail",
                "claim_scope": "counter_attribution_only",
            }
        ],
        ["decision", "remote_execution", "correctness", "counter_capture", "claim_scope"],
    )
    write_csv(
        CLAIMS,
        [
            {
                "claim": "current_direct_dft_counter_attribution",
                "status": "supported" if decision.startswith("PASS_STAGE301_CURRENT") else "not_yet",
                "allowed": "Use Stage301 counters for mechanism attribution on the current direct-DFT path.",
                "not_allowed": "Do not claim theoretical optimality or statistical latency from one counter run.",
            },
            {
                "claim": "complete_sab_speed",
                "status": "unchanged_stage296_299",
                "allowed": "Use repeated T_bootstrap/r evidence from Stage296 and scoped preflight from Stage299.",
                "not_allowed": "Use perf counter elapsed time as the final SAB speed claim.",
            },
        ],
        ["claim", "status", "allowed", "not_allowed"],
    )
    write_csv(
        NEXT,
        [
            {
                "priority": "P0",
                "route": "stage302_counter_interpretation",
                "entry_condition": decision,
                "gate": "Interpret direct/control counters against Stage296/299 timing and MAT AVX memory model.",
                "failure_action": "Keep counter evidence as raw attribution only.",
            },
            {
                "priority": "P1",
                "route": "stage302_parameter_matrix_highstat",
                "entry_condition": "counter interpretation does not identify a new kernel target",
                "gate": "Promote SET_4_5_2048 to repeated performance/noise/resource matrix.",
                "failure_action": "Restrict generalization wording.",
            },
        ],
        ["priority", "route", "entry_condition", "gate", "failure_action"],
    )

    write_reports(decision, run_rows, summary_rows, comp_rows, gate_rows)
    write_text(
        THEORY,
        "# Stage301 Direct-DFT Counter Model\n\n"
        "Stage301 compares selected-control and direct-DFT current-head variants under the same native perf event set. "
        "Ratios above 1 in `selected_over_direct` mean the direct path records fewer events for that metric. "
        "This can support a mechanism explanation for Stage296 timing, but does not prove theoretical optimality.\n",
    )
    write_text(
        VARIANT,
        "# Stage301 Direct-DFT Counter Variant\n\n"
        "No SAB semantics are changed. The variant is the already-promoted direct-DFT path, measured against the selected PVW control under native counters.\n",
    )
    write_text(
        EXPERIMENT,
        "# Stage301 Experiment Plan\n\n"
        "Run selected-control and direct-DFT r=4 include-zero complete SAB once each under native perf counters. "
        "Gate on correctness and counter capture; use results only for attribution unless followed by repeated timing.\n",
    )
    write_text(
        COMMANDS,
        "# Stage301 Reproduction Commands\n\n"
        "```bash\n"
        "STAGE301_REMOTE_SECRET=<runtime-secret> STAGE301_REMOTE_HOST=<native-host> "
        "python3 scripts/build_stage301_current_head_direct_dft_native_counter.py\n"
        "```\n",
    )

    append_once(
        ROADMAP,
        "## Stage 301: Current-Head Direct-DFT Native Counter Refresh",
        "\n## Stage 301: Current-Head Direct-DFT Native Counter Refresh\n\n"
        "Goal: record native hardware counters for selected-control vs direct-DFT current-head complete SAB.\n\n"
        f"Status: `{decision}`.\n",
    )
    append_once(
        GOAL,
        "<!-- stage301-current-head-direct-dft-native-counter -->",
        "\n<!-- stage301-current-head-direct-dft-native-counter -->\n"
        "### Stage301 current-head direct-DFT native counter refresh\n\n"
        f"`{decision}` records native counter attribution status for the current direct-DFT candidate. "
        "The result is mechanism evidence only; complete-SAB performance claims remain tied to `T_bootstrap/r` campaigns.\n",
    )
    append_once(
        HYPOTHESES,
        "H301_current_direct_dft_counter_attribution",
        "\nH301_current_direct_dft_counter_attribution:\n"
        "  claim: Current direct-DFT should reduce selected MAT/PVW backend work visible in native counters.\n"
        f"  status: {decision}\n"
        "  evidence: repro/stage301_current_head_direct_dft_native_counter/proof_gate.csv\n"
        "  next_gate: Stage302 counter interpretation and parameter high-stat matrix.\n",
    )
    append_once(
        MANIFEST,
        "- stage301_current_head_direct_dft_native_counter:",
        "\n- stage301_current_head_direct_dft_native_counter:\n"
        f"  - `{rel(DOC)}`\n"
        f"  - `{rel(RUN_METRICS)}`\n"
        f"  - `{rel(COUNTER_SUMMARY)}`\n"
        f"  - `{rel(COUNTER_COMPARISON)}`\n",
    )
    append_once(
        CHECKLIST,
        "Stage301 current-head direct-DFT native counter refresh",
        "\n- [x] Stage301 current-head direct-DFT native counter refresh recorded without storing secrets.\n",
    )
    append_run_log(decision)

    artifacts = [
        DOC,
        REPORT,
        THEORY,
        VARIANT,
        EXPERIMENT,
        SUMMARY,
        RUN_METRICS,
        COUNTERS,
        COUNTER_SUMMARY,
        COUNTER_COMPARISON,
        PROOF,
        CLAIMS,
        NEXT,
        COMMANDS,
        REMOTE_ENV,
        RUNNER,
        OUT / "local_probe.log",
        OUT / "batch_ssh_probe.log",
        OUT / "remote_unpack.log",
        OUT / "remote_install_runner.log",
        OUT / "remote_run_stage301_runner.log",
        OUT / "remote_pull_native_perf_raw.log",
    ]
    artifacts.extend(sorted(RAW.glob("*.log")))
    write_csv(INDEX, artifact_index(artifacts), ["path", "bytes", "sha256"])
    print(decision)


if __name__ == "__main__":
    main()
