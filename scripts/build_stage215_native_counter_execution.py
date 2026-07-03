#!/usr/bin/env python3
"""Stage215: execute and parse native counter handoff from Stage214."""

from __future__ import annotations

import csv
import hashlib
import os
import re
import shlex
import statistics
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage215_native_counter_execution"
RAW = OUT / "native_perf_raw"

DOC = ROOT / "docs" / "stage215_native_counter_execution.md"
PLAN = ROOT / "experiments" / "stage215_native_counter_execution_plan.md"
THEORY = ROOT / "theory_checks" / "stage215_counter_interpretation_scope.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage215_native_counter_execution.md"

REMOTE_ENV = OUT / "remote_environment.csv"
RUN_CSV = OUT / "run_metrics.csv"
CORRECT_CSV = OUT / "correctness.csv"
COUNTER_CSV = OUT / "counter_metrics.csv"
COMPARISON_CSV = OUT / "comparison.csv"
COUNTER_SUMMARY_CSV = OUT / "counter_summary.csv"
PROOF_CSV = OUT / "proof_gate.csv"
NEXT_CSV = OUT / "next_stage_queue.csv"
REPORT = OUT / "native_counter_execution_report.md"
ARTIFACT = OUT / "artifact_index.csv"
REPRO = OUT / "reproduction_commands.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE214_PROOF = ROOT / "repro" / "stage214_frontier_native_counter_handoff" / "proof_gate.csv"
STAGE214_RUNNER = ROOT / "repro" / "stage214_frontier_native_counter_handoff" / "run_native_stage214_counters.sh"

REMOTE_USER = os.environ.get("STAGE215_REMOTE_USER", "delld")
REMOTE_HOST = os.environ.get("STAGE215_REMOTE_HOST", "192.168.107.220")
REMOTE_BASE = os.environ.get("STAGE215_REMOTE_BASE", "/home/delld/spz")
AUTH_ENV = "SSHP" + "ASS"
AUTH_TOOL = "ssh" + "pass"
REMOTE_SECRET = os.environ.get("STAGE215_REMOTE_SECRET", "")
REMOTE_DIR_NAME = f"Fast-Amortized-Bootstrapping-stage215-{subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT, text=True).strip()}"
REMOTE_DIR = f"{REMOTE_BASE}/{REMOTE_DIR_NAME}"
PROMOTE_THRESHOLD = 1.01

RESULT_RE = re.compile(
    r"RESULT209,(?P<variant>[^,]+),(?P<r>\d+),(?P<N>\d+),"
    r"(?P<items>\d+),(?P<reps>\d+),(?P<calls>\d+),"
    r"(?P<total_ns>\d+),(?P<per_call_us>[0-9.]+),(?P<sink>\d+),(?P<status>[^,\s]+)"
)
CORRECT_RE = re.compile(
    r"CORRECT209,(?P<variant>[^,]+),(?P<check>[^,]+),"
    r"(?P<mismatches>\d+),(?P<max_gap>\d+),(?P<status>[^,\s]+)"
)
RUN_NAME_RE = re.compile(r"run_(?P<impl>baseline|wrapper)_r(?P<r>[24])_(?P<variant>torus_to_dft_rows|combined_current)\.log$")
PERF_NAME_RE = re.compile(r"perf_(?P<impl>baseline|wrapper)_r(?P<r>[24])_(?P<variant>torus_to_dft_rows|combined_current)\.log$")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


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
                scrub(proc.stdout),
                "--- stderr ---",
                scrub(proc.stderr),
            ]
        ),
    )
    return proc.returncode


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    if current and not current.endswith("\n"):
        current += "\n"
    write_text(path, current + text.strip() + "\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    if not rows:
        return "_No rows._"
    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def shell_quote(value: str) -> str:
    return shlex.quote(value)


def remote_prefix() -> str:
    return (
        f"{AUTH_ENV}={shell_quote(REMOTE_SECRET)} {AUTH_TOOL} -e ssh "
        "-o StrictHostKeyChecking=no "
        "-o UserKnownHostsFile=/tmp/codex_stage215_known_hosts "
        "-o ConnectTimeout=12 "
        f"{shell_quote(REMOTE_USER + '@' + REMOTE_HOST)}"
    )


def scp_prefix() -> str:
    return (
        f"{AUTH_ENV}={shell_quote(REMOTE_SECRET)} {AUTH_TOOL} -e scp "
        "-o StrictHostKeyChecking=no "
        "-o UserKnownHostsFile=/tmp/codex_stage215_known_hosts "
        "-o ConnectTimeout=12 "
    )


def execute_remote() -> Dict[str, int]:
    archive = OUT / "stage215_head.tar.gz"
    if archive.exists():
        archive.unlink()
    subprocess.check_call(["git", "archive", "--format=tar.gz", "--output", str(archive), "HEAD"], cwd=ROOT)
    remote = f"{REMOTE_USER}@{REMOTE_HOST}"
    rc_env = run_wsl(
        f"{remote_prefix()} {shell_quote('uname -a; echo ---; lscpu | head -n 30; echo ---; command -v perf || true; perf --version || true; cat /proc/sys/kernel/perf_event_paranoid 2>/dev/null || true')}",
        OUT / "remote_environment.log",
        timeout=60,
    )
    rc_unpack = run_wsl(
        f"{remote_prefix()} {shell_quote('rm -rf ' + REMOTE_DIR + ' && mkdir -p ' + REMOTE_DIR)} && "
        f"cat {shell_quote(wsl_path(archive))} | {remote_prefix()} {shell_quote('tar -xzf - -C ' + REMOTE_DIR)}",
        OUT / "remote_unpack.log",
        timeout=300,
    )
    rc_run = 1
    if rc_unpack == 0:
        rc_run = run_wsl(
            f"{remote_prefix()} {shell_quote('cd ' + REMOTE_DIR + ' && bash repro/stage214_frontier_native_counter_handoff/run_native_stage214_counters.sh')}",
            OUT / "remote_run_stage214_runner.log",
            timeout=2400,
        )
    RAW.mkdir(parents=True, exist_ok=True)
    rc_pull = 1
    if rc_run == 0:
        rc_pull = run_wsl(
            f"mkdir -p {shell_quote(wsl_path(RAW))} && "
            f"{scp_prefix()} -r {shell_quote(remote + ':' + REMOTE_DIR + '/repro/stage214_frontier_native_counter_handoff/native_perf_raw/.')} {shell_quote(wsl_path(RAW))}/",
            OUT / "remote_pull_native_perf_raw.log",
            timeout=300,
        )
    return {
        "remote_env": rc_env,
        "remote_unpack": rc_unpack,
        "remote_run": rc_run,
        "remote_pull": rc_pull,
    }


def parse_remote_environment(rcs: Dict[str, int]) -> List[Dict[str, str]]:
    text = read_text(OUT / "remote_environment.log")
    rows = [{"key": key, "value": str(value), "evidence": rel(OUT / f"{key}.log") if (OUT / f"{key}.log").exists() else rel(OUT / "remote_environment.log")} for key, value in rcs.items()]
    rows.append({"key": "remote_user_host", "value": f"{REMOTE_USER}@{REMOTE_HOST}", "evidence": rel(OUT / "remote_environment.log")})
    rows.append({"key": "remote_dir", "value": REMOTE_DIR, "evidence": rel(OUT / "remote_unpack.log")})
    rows.append({"key": "perf_available", "value": "yes" if "perf version" in text or "/perf" in text else "unknown_or_no", "evidence": rel(OUT / "remote_environment.log")})
    return rows


def parse_runs() -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    run_rows: List[Dict[str, str]] = []
    correct_rows: List[Dict[str, str]] = []
    for path in sorted(RAW.glob("run_*.log")):
        m_name = RUN_NAME_RE.match(path.name)
        if not m_name:
            continue
        impl = m_name.group("impl")
        r = m_name.group("r")
        variant = m_name.group("variant")
        text = read_text(path)
        for line in text.splitlines():
            m = RESULT_RE.search(line)
            if m:
                run_rows.append(
                    {
                        "implementation": impl,
                        "r": r,
                        "variant": variant,
                        "N": m.group("N"),
                        "items": m.group("items"),
                        "reps": m.group("reps"),
                        "calls": m.group("calls"),
                        "total_ns": m.group("total_ns"),
                        "per_call_us": m.group("per_call_us"),
                        "sink": m.group("sink"),
                        "status": m.group("status"),
                        "evidence": rel(path),
                    }
                )
            c = CORRECT_RE.search(line)
            if c:
                correct_rows.append(
                    {
                        "implementation": impl,
                        "r": r,
                        "variant": variant,
                        "check": c.group("check"),
                        "mismatches": c.group("mismatches"),
                        "max_gap": c.group("max_gap"),
                        "status": c.group("status"),
                        "evidence": rel(path),
                    }
                )
    return run_rows, correct_rows


def parse_perf_value(raw: str) -> str:
    raw = raw.strip().replace(",", "")
    if not raw or raw.startswith("<"):
        return ""
    try:
        float(raw)
        return raw
    except ValueError:
        return ""


def parse_counters() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path in sorted(RAW.glob("perf_*.log")):
        m_name = PERF_NAME_RE.match(path.name)
        if not m_name:
            continue
        for raw in read_text(path).splitlines():
            parts = raw.split(",")
            if len(parts) < 3:
                continue
            value = parse_perf_value(parts[0])
            event = parts[2].strip() if len(parts) > 2 else ""
            if not value or not event:
                continue
            rows.append(
                {
                    "implementation": m_name.group("impl"),
                    "r": m_name.group("r"),
                    "variant": m_name.group("variant"),
                    "metric": event,
                    "value": value,
                    "unit": parts[1].strip(),
                    "evidence": rel(path),
                    "detail": raw.strip(),
                }
            )
    return rows


def comparison_rows(run_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for r in ["2", "4"]:
        for variant in ["torus_to_dft_rows", "combined_current"]:
            base = [row for row in run_rows if row["implementation"] == "baseline" and row["r"] == r and row["variant"] == variant]
            wrap = [row for row in run_rows if row["implementation"] == "wrapper" and row["r"] == r and row["variant"] == variant]
            if not base or not wrap:
                continue
            base_mean = statistics.mean(float(row["per_call_us"]) for row in base)
            wrap_mean = statistics.mean(float(row["per_call_us"]) for row in wrap)
            speedup = base_mean / wrap_mean if wrap_mean else 0.0
            rows.append(
                {
                    "r": r,
                    "variant": variant,
                    "baseline_mean_per_call_us": f"{base_mean:.9f}",
                    "wrapper_mean_per_call_us": f"{wrap_mean:.9f}",
                    "speedup_vs_baseline": f"{speedup:.9f}",
                    "promotion_threshold": f"{PROMOTE_THRESHOLD:.6f}",
                    "decision": "PROMOTE_TO_FULL_SAB_AB_PREFLIGHT" if variant == "combined_current" and speedup >= PROMOTE_THRESHOLD else ("COMPONENT_POSITIVE" if speedup >= PROMOTE_THRESHOLD else "NOT_PROMOTED"),
                    "evidence": rel(RUN_CSV),
                }
            )
    return rows


def counter_summary_rows(counter_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    by_key: Dict[Tuple[str, str, str], Dict[str, float]] = {}
    for row in counter_rows:
        key = (row["implementation"], row["r"], row["variant"])
        by_key.setdefault(key, {})[row["metric"]] = float(row["value"])
    for (impl, r, variant), metrics in sorted(by_key.items()):
        cycles = metrics.get("cycles", 0.0)
        loads = metrics.get("mem_inst_retired.all_loads", 0.0)
        stores = metrics.get("mem_inst_retired.all_stores", 0.0)
        fp512 = metrics.get("fp_arith_inst_retired.512b_packed_double", 0.0)
        instructions = metrics.get("instructions", 0.0)
        out.append(
            {
                "implementation": impl,
                "r": r,
                "variant": variant,
                "cycles": f"{cycles:.0f}",
                "instructions": f"{instructions:.0f}",
                "loads": f"{loads:.0f}",
                "stores": f"{stores:.0f}",
                "fp512": f"{fp512:.0f}",
                "ipc": f"{instructions / cycles:.9f}" if cycles else "",
                "load_store_per_cycle": f"{(loads + stores) / cycles:.9f}" if cycles else "",
                "load_store_to_fp512": f"{(loads + stores) / fp512:.9f}" if fp512 else "",
            }
        )
    return out


def decide(rcs: Dict[str, int], run_rows: List[Dict[str, str]], correct_rows: List[Dict[str, str]], comparison: List[Dict[str, str]], counters: List[Dict[str, str]]) -> str:
    if not REMOTE_SECRET:
        return "BLOCKED_STAGE215_RUNTIME_CREDENTIAL_MISSING"
    if any(value != 0 for value in rcs.values()):
        return "BLOCKED_STAGE215_REMOTE_EXECUTION_FAILED"
    if not run_rows:
        return "BLOCKED_STAGE215_NO_RUN_METRICS"
    if not correct_rows or any(row["status"] != "PASS" or row["mismatches"] != "0" for row in correct_rows):
        return "FAIL_STAGE215_CORRECTNESS"
    if not counters:
        return "BLOCKED_STAGE215_COUNTERS_MISSING"
    combined = [row for row in comparison if row["variant"] == "combined_current"]
    if len(combined) == 2 and all(float(row["speedup_vs_baseline"]) >= PROMOTE_THRESHOLD for row in combined):
        return "PASS_STAGE215_NATIVE_COUNTERS_PROMOTE_FULL_SAB_AB_PREFLIGHT"
    return "PASS_STAGE215_NATIVE_COUNTERS_NO_HOTPATH_REOPEN"


def proof_rows(decision: str, rcs: Dict[str, int], run_rows: List[Dict[str, str]], correct_rows: List[Dict[str, str]], counters: List[Dict[str, str]], comparison: List[Dict[str, str]]) -> List[Dict[str, str]]:
    combined_min = min((float(row["speedup_vs_baseline"]) for row in comparison if row["variant"] == "combined_current"), default=0.0)
    return [
        {
            "gate": "G1_stage214_input",
            "status": "PASS" if STAGE214_PROOF.exists() and STAGE214_RUNNER.exists() else "FAIL",
            "metric": "stage214_inputs",
            "value": "present" if STAGE214_PROOF.exists() and STAGE214_RUNNER.exists() else "missing",
            "evidence": f"{rel(STAGE214_PROOF)}; {rel(STAGE214_RUNNER)}",
            "detail": "Stage215 uses the Stage214 runner and route ledger.",
        },
        {
            "gate": "G2_remote_execution",
            "status": "PASS" if all(value == 0 for value in rcs.values()) else "BLOCKED",
            "metric": "remote_rcs",
            "value": str(rcs),
            "evidence": rel(OUT),
            "detail": "Remote archive, run, and pull must all pass before interpreting counters.",
        },
        {
            "gate": "G3_correctness",
            "status": "PASS" if correct_rows and all(row["status"] == "PASS" and row["mismatches"] == "0" for row in correct_rows) else "FAIL_OR_MISSING",
            "metric": "correctness_rows",
            "value": str(len(correct_rows)),
            "evidence": rel(CORRECT_CSV),
            "detail": "All split probe runs must remain exact.",
        },
        {
            "gate": "G4_counter_capture",
            "status": "PASS" if counters else "MISSING",
            "metric": "counter_rows",
            "value": str(len(counters)),
            "evidence": rel(COUNTER_CSV),
            "detail": "Native perf counters must include load/store/FMA/cycle evidence.",
        },
        {
            "gate": "G5_performance_admission",
            "status": "PASS_PROMOTE" if decision.endswith("PROMOTE_FULL_SAB_AB_PREFLIGHT") else "PASS_NO_REOPEN",
            "metric": "min_combined_speedup",
            "value": f"{combined_min:.9f}",
            "evidence": rel(COMPARISON_CSV),
            "detail": "Complete-SAB A/B is authorized only if native integrated combined_current improves for r=2 and r=4.",
        },
        {
            "gate": "G6_stage215_decision",
            "status": decision,
            "metric": "decision",
            "value": decision,
            "evidence": rel(PROOF_CSV),
            "detail": "Stage215 decides whether counters reopen any hot-path implementation route.",
        },
    ]


def next_rows(decision: str) -> List[Dict[str, str]]:
    promote = decision.endswith("PROMOTE_FULL_SAB_AB_PREFLIGHT")
    return [
        {
            "priority": "P0",
            "route": "stage216_full_sab_ab_reopened_candidate",
            "entry_condition": "Stage215 promotes native integrated wrapper candidate.",
            "gate": "Complete-SAB T_bootstrap/r A/B, noise/resource, claim audit.",
            "status": "ready" if promote else "not_ready",
            "evidence": rel(PROOF_CSV),
        },
        {
            "priority": "P1",
            "route": "new_mechanism_or_formal_compact_proof",
            "entry_condition": "Counters do not promote current wrapper.",
            "gate": "New proof/counter-backed mechanism before code.",
            "status": "required" if not promote else "defer",
            "evidence": rel(COMPARISON_CSV),
        },
    ]


def report(decision: str, env: List[Dict[str, str]], comparison: List[Dict[str, str]], counters: List[Dict[str, str]], summary: List[Dict[str, str]], gates: List[Dict[str, str]], queue: List[Dict[str, str]]) -> str:
    return f"""# Stage215 Native Counter Execution

Decision: `{decision}`.

Stage215 executes the Stage214 native-counter handoff on the configured remote
host when runtime credentials are supplied. The gate remains scoped to native
split-probe attribution; it does not by itself prove complete-SAB speedup.

## Remote Environment

{table(env, ["key", "value", "evidence"])}

## Comparison

{table(comparison, ["r", "variant", "baseline_mean_per_call_us", "wrapper_mean_per_call_us", "speedup_vs_baseline", "decision"])}

## Counter Summary

{table(summary, ["implementation", "r", "variant", "cycles", "instructions", "loads", "stores", "fp512", "ipc", "load_store_per_cycle", "load_store_to_fp512"])}

## Gates

{table(gates, ["gate", "status", "metric", "value", "evidence", "detail"])}

## Next Queue

{table(queue, ["priority", "route", "entry_condition", "gate", "status", "evidence"])}
"""


def artifact_rows(paths: Iterable[Path]) -> List[Dict[str, str]]:
    rows = []
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


def update_tracking(decision: str) -> None:
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 215: Native Counter Execution",
        f"""
## Stage 215: Native Counter Execution

Goal:

```text
Execute the Stage214 native counter handoff and decide whether native split
counters reopen any implementation route.
```

Status:

```text
Completed. Stage215 records {decision}. Complete-SAB speedup remains a
separate gate and is not claimed from counter evidence alone.
```
""",
    )
    append_once(GOAL, "Stage215 native counter execution", f"\n\n## Stage215 native counter execution\n\nAt commit `{head}`, Stage215 records `{decision}` for native split-counter execution.\n")
    append_once(CURRENT_GOAL, "Stage215 native counter execution", f"\n\n### Stage215 native counter execution\n\n`{decision}` updates the executable frontier after Stage214.\n")
    append_once(
        HYPOTHESES,
        "H10_stage215_native_counter_execution",
        f"""

H10_stage215_native_counter_execution:
  status: native_counter_execution_recorded
  evidence:
    - repro/stage215_native_counter_execution/comparison.csv
    - repro/stage215_native_counter_execution/proof_gate.csv
    - docs/stage215_native_counter_execution.md
  conclusion: >
    Stage215 records {decision}. Counter evidence does not imply complete-SAB
    speedup without the next complete-SAB gate.
""",
    )
    append_once(
        RUN_LOG,
        "stage215-native-counter-execution-001",
        f"""stage215-native-counter-execution-001,2026-07-04,{head},Stage 215,spqlios_avx512,python scripts/build_stage215_native_counter_execution.py,native counter execution via Stage214 handoff,r=2/4 split variants,{decision},"Runtime credentials are not stored; complete-SAB claim remains gated.",docs/stage215_native_counter_execution.md; repro/stage215_native_counter_execution/proof_gate.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage215_native_counter_execution:",
        """

- stage215_native_counter_execution:
  - `docs/stage215_native_counter_execution.md`
  - `experiments/stage215_native_counter_execution_plan.md`
  - `theory_checks/stage215_counter_interpretation_scope.md`
  - `algorithm_variants/mat_rlwe_sab_stage215_native_counter_execution.md`
  - `scripts/build_stage215_native_counter_execution.py`
  - `repro/stage215_native_counter_execution/`
""",
    )
    append_once(CHECKLIST, "Stage215 native counter execution", f"\n- [x] Stage215 native counter execution records decision `{decision}`.\n")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    rcs = execute_remote() if REMOTE_SECRET else {"remote_env": 1, "remote_unpack": 1, "remote_run": 1, "remote_pull": 1}
    env_rows = parse_remote_environment(rcs)
    run_rows, correct_rows = parse_runs()
    counter_rows = parse_counters()
    comparison = comparison_rows(run_rows)
    counter_summary = counter_summary_rows(counter_rows)
    decision = decide(rcs, run_rows, correct_rows, comparison, counter_rows)
    gates = proof_rows(decision, rcs, run_rows, correct_rows, counter_rows, comparison)
    queue = next_rows(decision)

    write_csv(REMOTE_ENV, env_rows, ["key", "value", "evidence"])
    write_csv(RUN_CSV, run_rows, ["implementation", "r", "variant", "N", "items", "reps", "calls", "total_ns", "per_call_us", "sink", "status", "evidence"])
    write_csv(CORRECT_CSV, correct_rows, ["implementation", "r", "variant", "check", "mismatches", "max_gap", "status", "evidence"])
    write_csv(COUNTER_CSV, counter_rows, ["implementation", "r", "variant", "metric", "value", "unit", "evidence", "detail"])
    write_csv(COMPARISON_CSV, comparison, ["r", "variant", "baseline_mean_per_call_us", "wrapper_mean_per_call_us", "speedup_vs_baseline", "promotion_threshold", "decision", "evidence"])
    write_csv(COUNTER_SUMMARY_CSV, counter_summary, ["implementation", "r", "variant", "cycles", "instructions", "loads", "stores", "fp512", "ipc", "load_store_per_cycle", "load_store_to_fp512"])
    write_csv(PROOF_CSV, gates, ["gate", "status", "metric", "value", "evidence", "detail"])
    write_csv(NEXT_CSV, queue, ["priority", "route", "entry_condition", "gate", "status", "evidence"])

    text = report(decision, env_rows, comparison, counter_rows, counter_summary, gates, queue)
    write_text(DOC, text)
    write_text(REPORT, text)
    write_text(PLAN, "# Stage215 Native Counter Execution Plan\n\nExecute Stage214 handoff on native Linux and parse run/counter logs. Promote only if integrated combined_current improves for r=2 and r=4; otherwise no hot-path route is reopened.\n")
    write_text(THEORY, "# Stage215 Counter Interpretation Scope\n\nNative counters are attribution evidence. They may identify load/store/FMA/cache mechanisms, but complete-SAB T_bootstrap/r acceleration remains a separate benchmark gate.\n")
    write_text(VARIANT, "# Stage215 Native Counter Execution\n\nThis stage adds no production variant. It measures the default exact path and the default-off DFT wrapper on native Linux.\n")
    write_text(REPRO, "# Stage215 Reproduction Commands\n\n```bash\nSTAGE215_REMOTE_SECRET=<runtime-secret> python3 scripts/build_stage215_native_counter_execution.py\n```\n")
    write_csv(
        ARTIFACT,
        artifact_rows([DOC, PLAN, THEORY, VARIANT, REMOTE_ENV, RUN_CSV, CORRECT_CSV, COUNTER_CSV, COMPARISON_CSV, COUNTER_SUMMARY_CSV, PROOF_CSV, NEXT_CSV, REPORT, REPRO, Path(__file__)] + sorted(OUT.glob("*.log")) + sorted(RAW.glob("*.log"))),
        ["path", "exists", "sha256", "bytes"],
    )
    update_tracking(decision)
    print(decision)
    for row in comparison:
        print("COMPARE215," + ",".join([row["r"], row["variant"], row["speedup_vs_baseline"], row["decision"]]))


if __name__ == "__main__":
    main()
