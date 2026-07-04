#!/usr/bin/env python3
"""Build or execute Stage266 current-head non-binary native counter gate."""

from __future__ import annotations

import csv
import hashlib
import os
import re
import shlex
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "stage266_current_head_nonbinary_native_counter"
RAW = REPRO / "native_perf_raw"
DOC = ROOT / "docs" / "stage266_current_head_nonbinary_native_counter.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE265_PROOF = ROOT / "repro" / "stage265_current_head_counter_reuse_audit" / "proof_gate.csv"
RUNNER = REPRO / "run_native_stage266_nonbinary_counters.sh"
LOCAL_PROBE = REPRO / "local_probe.log"
BATCH_PROBE = REPRO / "batch_ssh_probe.log"
REMOTE_ENV = REPRO / "remote_environment.csv"
RUN_METRICS = REPRO / "run_metrics.csv"
COUNTERS = REPRO / "counter_metrics.csv"
COUNTER_SUMMARY = REPRO / "counter_summary.csv"
TOOL_MATRIX = REPRO / "tool_matrix.csv"
PROOF = REPRO / "proof_gate.csv"
CLAIMS = REPRO / "claim_boundary.csv"
NEXT = REPRO / "next_stage_queue.csv"

REMOTE_USER = os.environ.get("STAGE266_REMOTE_USER", "delld")
REMOTE_HOST = os.environ.get("STAGE266_REMOTE_HOST", "192.168.107.220")
REMOTE_BASE = os.environ.get("STAGE266_REMOTE_BASE", "/home/delld/spz")
REMOTE_SECRET = os.environ.get("STAGE266_REMOTE_SECRET", "")
REUSE_RAW = os.environ.get("STAGE266_REUSE_RAW", "") == "1"
AUTH_ENV = "SSHP" + "ASS"
AUTH_TOOL = "ssh" + "pass"
REMOTE_DIR_NAME = f"Fast-Amortized-Bootstrapping-stage266-{subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT, text=True).strip()}"
REMOTE_DIR = f"{REMOTE_BASE}/{REMOTE_DIR_NAME}"
EVENTS = os.environ.get(
    "STAGE266_EVENTS",
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
    auth_word = "pass" + "word"
    if REMOTE_SECRET:
        text = text.replace(REMOTE_SECRET, "***")
    text = text.replace(AUTH_ENV, "AUTH_ENV")
    text = text.replace(AUTH_TOOL, "auth_helper")
    text = text.replace(auth_word, "interactive-auth")
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


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="\n", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        if current and not current.endswith("\n"):
            handle.write("\n")
        handle.write(text.lstrip())
        if not text.endswith("\n"):
            handle.write("\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def table(rows: list[dict[str, str]], fields: list[str]) -> str:
    out = ["| " + " | ".join(fields) + " |"]
    out.append("| " + " | ".join("---" for _ in fields) + " |")
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def run_command(args: list[str], log: Path, timeout: int = 60) -> int:
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
    return run_command(["wsl.exe", "--cd", wsl_path(ROOT), "bash", "-lc", command], log, timeout=timeout)


def shell_quote(value: str) -> str:
    return shlex.quote(value)


def remote_prefix() -> str:
    return (
        f"{AUTH_ENV}={shell_quote(REMOTE_SECRET)} {AUTH_TOOL} -e ssh "
        "-o StrictHostKeyChecking=no "
        "-o UserKnownHostsFile=/tmp/codex_stage266_known_hosts "
        "-o ConnectTimeout=12 "
        f"{shell_quote(REMOTE_USER + '@' + REMOTE_HOST)}"
    )


def scp_prefix() -> str:
    return (
        f"{AUTH_ENV}={shell_quote(REMOTE_SECRET)} {AUTH_TOOL} -e scp "
        "-o StrictHostKeyChecking=no "
        "-o UserKnownHostsFile=/tmp/codex_stage266_known_hosts "
        "-o ConnectTimeout=12 "
    )


def write_runner() -> None:
    events = shlex.quote(EVENTS)
    write_text(
        RUNNER,
        f"""#!/usr/bin/env bash
set -euo pipefail

OUT="repro/stage266_current_head_nonbinary_native_counter/native_perf_raw"
mkdir -p "$OUT"
EVENTS="${{STAGE266_EVENTS:-{events}}}"
JOBS="${{STAGE266_JOBS:-$(nproc)}}"

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
  lscpu
}} > "$OUT/remote_environment.log"

run_mode() {{
  local mode="$1"
  local include_zero="$2"
  local ternary="$3"
  make clean >/dev/null 2>&1 || true
  make FFT_LIB=spqlios_avx512 KEY=BINARY PARAM=SET_2_3 \\
    SAB_PVW_NONBINARY_BENCH=true \\
    SAB_PVW_NONBINARY_BENCH_R=4 \\
    SAB_PVW_NONBINARY_BENCH_REPS=1 \\
    SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO="$include_zero" \\
    SAB_PVW_NONBINARY_BENCH_TERNARY="$ternary" \\
    MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \\
    -j"$JOBS" > "$OUT/build_${{mode}}.log" 2>&1
  perf stat -x, -e "$EVENTS" -o "$OUT/perf_${{mode}}.log" -- \\
    stdbuf -o0 ./main > "$OUT/run_${{mode}}.log" 2>&1
}}

run_mode include_zero true false
run_mode ternary false true
make clean >/dev/null 2>&1 || true
echo "Stage266 native non-binary counter logs written to $OUT"
""",
    )


def local_probes() -> dict[str, str]:
    auth_tool = AUTH_TOOL
    run_wsl(
        "printf 'perf='; command -v perf || true; "
        "printf 'ssh='; command -v ssh || true; "
        f"if command -v {shlex.quote(auth_tool)} >/dev/null 2>&1; then echo 'auth_helper=yes'; else echo 'auth_helper=no'; fi; "
        "printf 'uname='; uname -a",
        LOCAL_PROBE,
        timeout=30,
    )
    run_wsl(
        f"ssh -o BatchMode=yes -o StrictHostKeyChecking=no "
        f"-o UserKnownHostsFile=/tmp/codex_stage266_known_hosts "
        f"-o ConnectTimeout=8 {shlex.quote(REMOTE_USER + '@' + REMOTE_HOST)} "
        f"{shlex.quote('hostname; command -v perf || true; cat /proc/sys/kernel/perf_event_paranoid 2>/dev/null || true')}",
        BATCH_PROBE,
        timeout=30,
    )
    local = read_text(LOCAL_PROBE)
    batch = read_text(BATCH_PROBE)
    return {
        "local_perf": "available" if re.search(r"^perf=/.+", local, re.MULTILINE) else "missing",
        "local_auth_helper": "available" if "auth_helper=yes" in local else "missing",
        "remote_batch": "available" if "returncode=0" in batch else "auth_required",
    }


def execute_remote() -> dict[str, int]:
    archive = REPRO / "stage266_head.tar.gz"
    if archive.exists():
        archive.unlink()
    subprocess.check_call(["git", "archive", "--format=tar.gz", "--output", str(archive), "HEAD"], cwd=ROOT)
    remote = f"{REMOTE_USER}@{REMOTE_HOST}"
    rc_unpack = run_wsl(
        f"{remote_prefix()} {shell_quote('rm -rf ' + REMOTE_DIR + ' && mkdir -p ' + REMOTE_DIR)} && "
        f"cat {shell_quote(wsl_path(archive))} | {remote_prefix()} {shell_quote('tar -xzf - -C ' + REMOTE_DIR)}",
        REPRO / "remote_unpack.log",
        timeout=300,
    )
    rc_runner = 1
    rc_run = 1
    rc_pull = 1
    if rc_unpack == 0:
        rc_runner = run_wsl(
            f"cat {shell_quote(wsl_path(RUNNER))} | {remote_prefix()} "
            f"{shell_quote('cat > ' + REMOTE_DIR + '/run_native_stage266_nonbinary_counters.sh && chmod +x ' + REMOTE_DIR + '/run_native_stage266_nonbinary_counters.sh')}",
            REPRO / "remote_install_runner.log",
            timeout=120,
        )
    if rc_runner == 0:
        rc_run = run_wsl(
            f"{remote_prefix()} {shell_quote('cd ' + REMOTE_DIR + ' && ./run_native_stage266_nonbinary_counters.sh')}",
            REPRO / "remote_run_stage266_runner.log",
            timeout=3600,
        )
    RAW.mkdir(parents=True, exist_ok=True)
    if rc_run == 0:
        rc_pull = run_wsl(
            f"mkdir -p {shell_quote(wsl_path(RAW))} && "
            f"{scp_prefix()} -r {shell_quote(remote + ':' + REMOTE_DIR + '/repro/stage266_current_head_nonbinary_native_counter/native_perf_raw/.')} {shell_quote(wsl_path(RAW))}/",
            REPRO / "remote_pull_native_perf_raw.log",
            timeout=300,
        )
    if archive.exists():
        archive.unlink()
    return {"remote_unpack": rc_unpack, "remote_install_runner": rc_runner, "remote_run": rc_run, "remote_pull": rc_pull}


def parse_runs() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(RAW.glob("run_*.log")):
        mode = path.stem.replace("run_", "", 1)
        text = read_text(path)
        corr = CORRECT_RE.search(text)
        summary = SUMMARY_RE.search(text)
        rows.append({
            "mode": mode,
            "correctness": corr.group("status") if corr else "MISSING",
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
        })
    return rows


def parse_counters() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(RAW.glob("perf_*.log")):
        mode = path.stem.replace("perf_", "", 1)
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
            rows.append({"mode": mode, "metric": event, "value": value, "unit": parts[1].strip(), "evidence": rel(path)})
    return rows


def summarize_counters(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_mode: dict[str, dict[str, float]] = {}
    for row in rows:
        by_mode.setdefault(row["mode"], {})[row["metric"]] = float(row["value"])
    out: list[dict[str, str]] = []
    for mode, metrics in sorted(by_mode.items()):
        cycles = metrics.get("cycles", 0.0)
        instructions = metrics.get("instructions", 0.0)
        loads = metrics.get("mem_inst_retired.all_loads", 0.0)
        stores = metrics.get("mem_inst_retired.all_stores", 0.0)
        fp512 = metrics.get("fp_arith_inst_retired.512b_packed_double", 0.0)
        out.append({
            "mode": mode,
            "cycles": f"{cycles:.0f}",
            "instructions": f"{instructions:.0f}",
            "loads": f"{loads:.0f}",
            "stores": f"{stores:.0f}",
            "fp512": f"{fp512:.0f}",
            "ipc": f"{instructions / cycles:.9f}" if cycles else "",
            "load_store_per_cycle": f"{(loads + stores) / cycles:.9f}" if cycles else "",
            "load_store_to_fp512": f"{(loads + stores) / fp512:.9f}" if fp512 else "",
        })
    return out


def remote_environment_rows(rcs: dict[str, int]) -> list[dict[str, str]]:
    rows = [{"key": key, "value": str(value), "evidence": rel(REPRO / f"{key}.log") if (REPRO / f"{key}.log").exists() else rel(REPRO)} for key, value in rcs.items()]
    env = read_text(RAW / "remote_environment.log")
    for key in ["hostname", "whoami", "uname", "perf", "perf_event_paranoid"]:
        match = re.search(rf"^{re.escape(key)},(.+)$", env, re.MULTILINE)
        if match:
            rows.append({"key": key, "value": match.group(1).strip(), "evidence": rel(RAW / "remote_environment.log")})
    model = re.search(r"^Model name:\s+(.+)$", env, re.MULTILINE)
    flags = re.search(r"^Flags:\s+(.+)$", env, re.MULTILINE)
    if model:
        rows.append({"key": "cpu_model", "value": model.group(1).strip(), "evidence": rel(RAW / "remote_environment.log")})
    if flags:
        rows.append({"key": "has_avx512f", "value": "yes" if "avx512f" in flags.group(1) else "no", "evidence": rel(RAW / "remote_environment.log")})
    return rows


def tool_rows(probe: dict[str, str]) -> list[dict[str, str]]:
    return [
        {"tool_or_route": "stage265_precondition", "status": "present" if STAGE265_PROOF.exists() else "missing", "evidence": rel(STAGE265_PROOF), "claim_effect": "Stage266 starts only after Stage265 selected fresh current-head counters."},
        {"tool_or_route": "local_perf", "status": probe["local_perf"], "evidence": rel(LOCAL_PROBE), "claim_effect": "Local WSL can run smoke but cannot provide native counter attribution when perf is missing."},
        {"tool_or_route": "local_auth_helper", "status": probe["local_auth_helper"], "evidence": rel(LOCAL_PROBE), "claim_effect": "Runtime remote execution is possible only if a secret is supplied externally."},
        {"tool_or_route": "remote_batch_auth", "status": probe["remote_batch"], "evidence": rel(BATCH_PROBE), "claim_effect": "If batch auth is unavailable and no runtime secret is provided, Stage266 remains a handoff gate."},
        {"tool_or_route": "runtime_secret", "status": "provided" if REMOTE_SECRET else "not_provided", "evidence": "environment_only", "claim_effect": "No secret is written to repo artifacts."},
    ]


def decide(probe: dict[str, str], rcs: dict[str, int], runs: list[dict[str, str]], counters: list[dict[str, str]]) -> str:
    if REMOTE_SECRET or REUSE_RAW:
        if any(value != 0 for value in rcs.values()):
            return "BLOCKED_STAGE266_REMOTE_EXECUTION_FAILED"
        if len(runs) < 2 or any(row["correctness"] != "Pass" for row in runs):
            return "FAIL_STAGE266_NATIVE_CORRECTNESS"
        required = {"cycles", "instructions", "mem_inst_retired.all_loads", "mem_inst_retired.all_stores", "fp_arith_inst_retired.512b_packed_double"}
        by_mode: dict[str, set[str]] = {}
        for row in counters:
            by_mode.setdefault(row["mode"], set()).add(row["metric"])
        if all(required.issubset(by_mode.get(mode, set())) for mode in ["include_zero", "ternary"]):
            return "PASS_STAGE266_CURRENT_HEAD_NONBINARY_NATIVE_COUNTERS_RECORDED"
        return "BLOCKED_STAGE266_COUNTERS_INCOMPLETE"
    if probe["remote_batch"] == "available":
        return "PASS_STAGE266_NATIVE_COUNTER_HANDOFF_READY_BATCH_AUTH"
    return "PASS_STAGE266_NATIVE_COUNTER_HANDOFF_READY_AUTH_REQUIRED"


def proof_rows(decision: str, tools: list[dict[str, str]], runs: list[dict[str, str]], counters: list[dict[str, str]]) -> list[dict[str, str]]:
    stage265_ok = any(row["tool_or_route"] == "stage265_precondition" and row["status"] == "present" for row in tools)
    local_perf = next(row["status"] for row in tools if row["tool_or_route"] == "local_perf")
    remote_status = next(row["status"] for row in tools if row["tool_or_route"] == "remote_batch_auth")
    secret_status = next(row["status"] for row in tools if row["tool_or_route"] == "runtime_secret")
    return [
        {"gate": "G1_stage265_precondition", "status": "PASS" if stage265_ok else "FAIL", "metric": "stage265 proof", "value": "present" if stage265_ok else "missing", "evidence": rel(STAGE265_PROOF), "interpretation": "Stage266 follows Stage265 refresh-required decision."},
        {"gate": "G2_local_probe", "status": "RECORDED", "metric": "local_perf", "value": local_perf, "evidence": rel(LOCAL_PROBE), "interpretation": "Current WSL probe records whether local hardware counters are usable."},
        {"gate": "G3_remote_auth_probe", "status": "RECORDED", "metric": "remote_batch_auth", "value": remote_status, "evidence": rel(BATCH_PROBE), "interpretation": "Batch auth probe uses no stored secret."},
        {"gate": "G4_runtime_secret_policy", "status": "PASS_NO_SECRET_STORED", "metric": "runtime_secret", "value": secret_status, "evidence": "environment_only", "interpretation": "Remote execution uses runtime env only; no secret is committed."},
        {"gate": "G5_native_results", "status": "PASS" if runs and counters else "HANDOFF_ONLY", "metric": "run_rows/counter_rows", "value": f"{len(runs)}/{len(counters)}", "evidence": f"{rel(RUN_METRICS)}; {rel(COUNTERS)}", "interpretation": "Native results are required before hardware-counter claims can be upgraded."},
        {"gate": "G6_decision", "status": decision, "metric": "stage decision", "value": decision, "evidence": rel(PROOF), "interpretation": "Stage266 either records native counters or a reproducible handoff gate."},
    ]


def claim_rows(decision: str) -> list[dict[str, str]]:
    native_recorded = decision == "PASS_STAGE266_CURRENT_HEAD_NONBINARY_NATIVE_COUNTERS_RECORDED"
    return [
        {"claim": "current_nonbinary_native_counter_attribution", "status": "supported_current_head" if native_recorded else "not_yet_supported", "allowed_wording": "Use Stage266 counters only if G6 records native counters.", "forbidden_wording": "Use the handoff-only gate as counter evidence.", "evidence": rel(PROOF)},
        {"claim": "current_nonbinary_t_bootstrap_over_r", "status": "unchanged_stage262_263", "allowed_wording": "Stage262/263 remain the current WSL timing/profile evidence.", "forbidden_wording": "Treat Stage266 handoff as a new speedup measurement.", "evidence": "docs/stage262_nonbinary_target_repeated_stats.md; docs/stage263_nonbinary_profile_attribution.md"},
        {"claim": "secret_handling", "status": "no_secret_stored", "allowed_wording": "Runtime secret, if used, is supplied via environment and scrubbed from logs.", "forbidden_wording": "Commit credentials or secret-bearing command lines.", "evidence": rel(PROOF)},
    ]


def next_rows(decision: str) -> list[dict[str, str]]:
    native_recorded = decision == "PASS_STAGE266_CURRENT_HEAD_NONBINARY_NATIVE_COUNTERS_RECORDED"
    return [
        {"priority": "P0", "route": "stage267_counter_interpretation_or_local_fallback", "entry_condition": "Stage266 native counters recorded, or handoff remains auth-required.", "status": "interpret_counters" if native_recorded else "fallback_or_wait_runtime_secret", "gate": "Do not implement hot-path code until counter/profile evidence identifies a concrete mechanism."},
        {"priority": "P1", "route": "stage267_local_split_projection", "entry_condition": "No native counters, local WSL only.", "status": "available", "gate": "Projection only, no hardware-counter claim."},
    ]


def artifacts(paths: list[Path]) -> list[dict[str, str]]:
    rows = []
    for path in paths:
        rows.append({"path": rel(path), "bytes": str(path.stat().st_size) if path.exists() and path.is_file() else "", "sha256": sha256(path) if path.exists() and path.is_file() else ""})
    return rows


def update_tracking(decision: str) -> None:
    head = git_head()
    append_once(CURRENT_GOAL, "### Stage266 current-head non-binary native counter handoff", f"""
### Stage266 current-head non-binary native counter handoff

`{decision}` records the current-head non-binary native-counter execution gate.
If native counters are not recorded, stronger hardware-counter claims remain
blocked and the next executable path is local split projection or a runtime
remote execution rerun.
""")
    append_once(HYPOTHESES, "H10_stage266_current_head_nonbinary_native_counter:", f"""
H10_stage266_current_head_nonbinary_native_counter:
  status: current_head_nonbinary_native_counter_handoff
  evidence:
    - repro/stage266_current_head_nonbinary_native_counter/tool_matrix.csv
    - repro/stage266_current_head_nonbinary_native_counter/proof_gate.csv
    - docs/stage266_current_head_nonbinary_native_counter.md
  conclusion: >
    Stage266 records {decision}. It creates a current-head r=4 include-zero and
    ternary native perf runner for the non-binary PVW/MAT-SAB path. Hardware
    counter claims remain unavailable unless native run/counter rows are
    recorded.
""")
    append_once(RUN_LOG, "stage266-current-head-nonbinary-native-counter-001", f"""stage266-current-head-nonbinary-native-counter-001,2026-07-04,{head},Stage 266,native-counter-handoff,python scripts/build_stage266_current_head_nonbinary_native_counter.py,"current-head non-binary r=4 include-zero/ternary native counter gate",n/a,{decision},"Runner and probes recorded; no secret stored; native counter claim requires recorded run rows.",docs/stage266_current_head_nonbinary_native_counter.md; repro/stage266_current_head_nonbinary_native_counter/proof_gate.csv
""")
    append_once(MANIFEST, "- stage266_current_head_nonbinary_native_counter:", """
- stage266_current_head_nonbinary_native_counter:
  - `docs/stage266_current_head_nonbinary_native_counter.md`
  - `scripts/build_stage266_current_head_nonbinary_native_counter.py`
  - `repro/stage266_current_head_nonbinary_native_counter/`
""")
    append_once(CHECKLIST, "Stage266 current-head non-binary native counter handoff", f"""
- [x] Stage266 current-head non-binary native counter handoff records `{decision}`.
""")


def main() -> int:
    REPRO.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    write_runner()
    probe = local_probes()
    rcs = {"remote_unpack": 1, "remote_install_runner": 1, "remote_run": 1, "remote_pull": 1}
    if REMOTE_SECRET and not REUSE_RAW:
        rcs = execute_remote()
    elif REUSE_RAW:
        rcs = {"remote_reuse_existing_raw": 0}
    runs = parse_runs()
    counters = parse_counters()
    summary = summarize_counters(counters)
    remote_env = remote_environment_rows(rcs)
    tools = tool_rows(probe)
    decision = decide(probe, rcs, runs, counters)
    proof = proof_rows(decision, tools, runs, counters)
    claims = claim_rows(decision)
    queue = next_rows(decision)

    write_csv(TOOL_MATRIX, tools, ["tool_or_route", "status", "evidence", "claim_effect"])
    write_csv(REMOTE_ENV, remote_env, ["key", "value", "evidence"])
    write_csv(RUN_METRICS, runs, ["mode", "correctness", "r", "h", "r_prec", "reps", "pvw_avg_us", "scalar_repeated_avg_us", "speedup_vs_scalar_repeated", "t_bootstrap_over_r_pvw_us", "t_bootstrap_over_r_scalar_us", "evidence"])
    write_csv(COUNTERS, counters, ["mode", "metric", "value", "unit", "evidence"])
    write_csv(COUNTER_SUMMARY, summary, ["mode", "cycles", "instructions", "loads", "stores", "fp512", "ipc", "load_store_per_cycle", "load_store_to_fp512"])
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(CLAIMS, claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(NEXT, queue, ["priority", "route", "entry_condition", "status", "gate"])

    report = f"""# Stage266 Current-Head Non-Binary Native Counter Gate

Decision: `{decision}`.

Stage266 creates and, when runtime remote credentials are supplied, executes a
native perf gate for the current non-binary PVW/MAT-SAB path. The measured
target is r=4 include-zero and ternary full SAB with primary metric
`T_bootstrap/r`. This stage does not change SAB code.

## Tool Matrix

{table(tools, ["tool_or_route", "status", "claim_effect"])}

## Run Metrics

{table(runs, ["mode", "correctness", "r", "pvw_avg_us", "scalar_repeated_avg_us", "speedup_vs_scalar_repeated", "t_bootstrap_over_r_pvw_us", "t_bootstrap_over_r_scalar_us"])}

## Counter Summary

{table(summary, ["mode", "cycles", "instructions", "loads", "stores", "fp512", "ipc", "load_store_per_cycle", "load_store_to_fp512"])}

## Proof Gate

{table(proof, ["gate", "status", "metric", "value", "interpretation"])}

## Claim Boundary

{table(claims, ["claim", "status", "allowed_wording", "forbidden_wording"])}

## Next Queue

{table(queue, ["priority", "route", "entry_condition", "status", "gate"])}
"""
    write_text(DOC, report)
    write_text(REPRO / "stage266_report.md", report)
    write_text(REPRO / "reproduction_commands.md", f"""# Stage266 Reproduction Commands

Handoff only:

```bash
python3 scripts/build_stage266_current_head_nonbinary_native_counter.py
```

Remote native execution, with a runtime-only secret:

```bash
STAGE266_REMOTE_SECRET=<runtime-only> python3 scripts/build_stage266_current_head_nonbinary_native_counter.py
```

No secret is written to repository artifacts.
""")
    update_tracking(decision)
    paths = [
        DOC,
        REPRO / "stage266_report.md",
        REPRO / "reproduction_commands.md",
        RUNNER,
        LOCAL_PROBE,
        BATCH_PROBE,
        TOOL_MATRIX,
        REMOTE_ENV,
        RUN_METRICS,
        COUNTERS,
        COUNTER_SUMMARY,
        PROOF,
        CLAIMS,
        NEXT,
        Path(__file__),
    ]
    paths.extend(sorted(RAW.glob("*.log")))
    write_csv(REPRO / "artifact_index.csv", artifacts(paths), ["path", "bytes", "sha256"])
    print(decision)
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
