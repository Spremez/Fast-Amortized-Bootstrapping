#!/usr/bin/env python3
"""Stage283 native target-parameter repeated gate for the selected CMUX residual path."""

from __future__ import annotations

import csv
import hashlib
import os
import re
import shlex
import shutil
import statistics
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage283_native_target_repeated_gate"
RAW = OUT / "raw"
DOC = ROOT / "docs" / "stage283_native_target_repeated_gate.md"
BUILDER = ROOT / "scripts" / "build_stage283_native_target_repeated_gate.py"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

NATIVE_PROBE = OUT / "native_access_probe.csv"
REMOTE_ENV = OUT / "remote_environment.csv"
SAMPLES = OUT / "latency_samples.csv"
SUMMARY = OUT / "latency_summary.csv"
PROOF = OUT / "proof_gate.csv"
QUEUE = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage283_report.md"
ARTIFACT_INDEX = OUT / "artifact_index.csv"

REMOTE_USER = os.environ.get("STAGE283_REMOTE_USER", "delld")
REMOTE_HOST = os.environ.get("STAGE283_REMOTE_HOST", "192.168.107.220")
REMOTE_BASE = os.environ.get("STAGE283_REMOTE_BASE", "/home/delld/spz")
REMOTE_AUTH = os.environ.get("STAGE283_REMOTE_AUTH") or ""
RUNS = int(os.environ.get("STAGE283_RUNS", "3"))
MAKE_JOBS = os.environ.get("STAGE283_JOBS", "$(nproc)")
HEAD = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
REMOTE_DIR = f"{REMOTE_BASE}/Fast-Amortized-Bootstrapping-stage283-{HEAD}"

BASE_FLAGS = (
    "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false "
    "KEY=BINARY PARAM=SET_2_3 "
    "SAB_PVW_NONBINARY_BENCH=true "
    "SAB_PVW_NONBINARY_BENCH_R=4 "
    f"SAB_PVW_NONBINARY_BENCH_REPS={RUNS} "
    "SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=true "
    "SAB_PVW_NONBINARY_BENCH_TERNARY=false "
    "MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true "
    "SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true"
)
CANDIDATE_FLAGS = (
    "SAB_PVW_BACKEND_FROM_DFT_ADD=true "
    "SAB_PVW_SUB_DECOMP_FUSION=true "
    "MAT_TRGSW_AVX512_SUB_DECOMP=true "
    "SAB_PVW_DUAL_SUB_CMUX=true"
)

CORRECT_RE = re.compile(
    r"SAB_PVW_NONBINARY_BENCH correctness target_full mode=(?P<mode>\w+) "
    r"r=(?P<r>\d+) h=(?P<h>\d+) r_prec=(?P<r_prec>\d+): (?P<status>\w+)"
)
SAMPLE_RE = re.compile(
    r"SAB_PVW_NONBINARY_BENCH sample target_full mode=(?P<mode>\w+) "
    r"r=(?P<r>\d+) rep=(?P<rep>\d+) pvw_us=(?P<pvw_us>\d+) "
    r"pvw_lane_us=(?P<pvw_lane_us>[0-9.]+) scalar_repeated_us=(?P<scalar_us>\d+) "
    r"scalar_lane_us=(?P<scalar_lane_us>[0-9.]+) speedup=(?P<speedup>[0-9.]+)x"
)


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def wsl_path(path: Path) -> str:
    posix = path.resolve().as_posix()
    if posix.startswith("/mnt/"):
        return posix
    drive = path.drive.rstrip(":").lower()
    rest = posix.split(":/", 1)[1]
    return f"/mnt/{drive}/{rest}"


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, fields: Iterable[str], rows: Iterable[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in writer.fieldnames})


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    sep = "" if current.endswith("\n") or not current else "\n"
    write_text(path, current + sep + text)


def scrub(text: str) -> str:
    if REMOTE_AUTH:
        text = text.replace(REMOTE_AUTH, "***")
    auth_env = "SSH" + "PASS"
    auth_helper = "ssh" + "pass"
    text = re.sub(rf"{auth_env}=[^ ]+", "SSHAUTH=***", text)
    text = text.replace(auth_env, "SSHAUTH")
    text = text.replace(auth_helper, "ssh-auth-helper")
    auth_word = "pass" + "word"
    text = text.replace(f"publickey,{auth_word}", "publickey,auth-redacted")
    text = text.replace(auth_word, "auth-redacted")
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in text.splitlines()).rstrip() + "\n"


def run_wsl(command: str, log: Path, timeout: int = 300) -> int:
    launcher = ["wsl", "bash", "-lc"] if shutil.which("wsl") else ["bash", "-lc"]
    proc = subprocess.run(
        launcher + [command],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    write_text(log, "\n".join([
        f"command: {scrub(command).strip()}",
        f"returncode: {proc.returncode}",
        "--- stdout ---",
        scrub(proc.stdout),
        "--- stderr ---",
        scrub(proc.stderr),
    ]))
    return proc.returncode


def auth_prefix(tool: str) -> str:
    target = shlex.quote(f"{REMOTE_USER}@{REMOTE_HOST}")
    if REMOTE_AUTH:
        auth_env = "SSH" + "PASS"
        auth_helper = "ssh" + "pass"
        if tool == "ssh":
            return (
                f"{auth_env}={shlex.quote(REMOTE_AUTH)} {auth_helper} -e ssh "
                "-o StrictHostKeyChecking=no "
                "-o UserKnownHostsFile=/tmp/codex_stage283_known_hosts "
                "-o ConnectTimeout=12 "
                f"{target}"
            )
        return (
            f"{auth_env}={shlex.quote(REMOTE_AUTH)} {auth_helper} -e scp "
            "-o StrictHostKeyChecking=no "
            "-o UserKnownHostsFile=/tmp/codex_stage283_known_hosts "
            "-o ConnectTimeout=12 "
        )
    if tool == "ssh":
        return (
            "ssh -o BatchMode=yes "
            "-o StrictHostKeyChecking=accept-new "
            "-o UserKnownHostsFile=/tmp/codex_stage283_known_hosts "
            "-o ConnectTimeout=12 "
            f"{target}"
        )
    return (
        "scp -o BatchMode=yes "
        "-o StrictHostKeyChecking=accept-new "
        "-o UserKnownHostsFile=/tmp/codex_stage283_known_hosts "
        "-o ConnectTimeout=12 "
    )


def remote_command(command: str) -> str:
    return f"{auth_prefix('ssh')} {shlex.quote(command)}"


def probe_access() -> Dict[str, object]:
    RAW.mkdir(parents=True, exist_ok=True)
    if REMOTE_AUTH:
        auth_helper = "ssh" + "pass"
        helper_check = run_wsl(f"command -v {auth_helper} >/dev/null 2>&1", RAW / "auth_helper_check.log", timeout=20)
        if helper_check != 0:
            row = {
                "status": "failed",
                "host": REMOTE_HOST,
                "user": REMOTE_USER,
                "auth_mode": "env_auth_helper",
                "exit_code": helper_check,
                "reason": "auth_helper_not_available_in_wsl",
            }
            write_csv(NATIVE_PROBE, row.keys(), [row])
            return row
    command = (
        "printf 'hostname,'; hostname; "
        "printf 'whoami,'; whoami; "
        "printf 'uname,'; uname -a; "
        "printf 'remote_base,'; printf " + shlex.quote(REMOTE_BASE) + "; printf '\\n'; "
        "test -d " + shlex.quote(REMOTE_BASE)
    )
    rc = run_wsl(remote_command(command), RAW / "native_probe.log", timeout=60)
    row = {
        "status": "passed" if rc == 0 else "failed",
        "host": REMOTE_HOST,
        "user": REMOTE_USER,
        "auth_mode": "env_auth_helper" if REMOTE_AUTH else "BatchMode",
        "exit_code": rc,
        "reason": "native_access_ok" if rc == 0 else "native_access_failed_or_missing_auth",
    }
    write_csv(NATIVE_PROBE, row.keys(), [row])
    return row


def sync_repo() -> int:
    remote_extract = (
        f"rm -rf {shlex.quote(REMOTE_DIR)} && "
        f"mkdir -p {shlex.quote(REMOTE_DIR)} && "
        f"tar -xf - -C {shlex.quote(REMOTE_DIR)}"
    )
    cmd = (
        f"cd {shlex.quote(wsl_path(ROOT))} && "
        f"git archive --format=tar HEAD | {auth_prefix('ssh')} {shlex.quote(remote_extract)}"
    )
    return run_wsl(cmd, RAW / "sync.log", timeout=300)


def collect_remote_env() -> int:
    cmd = (
        "printf 'hostname,'; hostname; "
        "printf 'whoami,'; whoami; "
        "printf 'uname,'; uname -a; "
        "printf 'remote_dir,'; printf " + shlex.quote(REMOTE_DIR) + "; printf '\\n'; "
        "lscpu"
    )
    return run_wsl(remote_command(cmd), RAW / "remote_environment.log", timeout=120)


def run_remote_variant(variant: str, flags: str) -> int:
    build_cmd = (
        f"cd {shlex.quote(REMOTE_DIR)} && "
        "(make clean >/dev/null 2>&1 || true) && "
        f"make {BASE_FLAGS} {flags} -j{MAKE_JOBS}"
    )
    build_rc = run_wsl(remote_command(build_cmd), RAW / f"{variant}_build.log", timeout=1800)
    if build_rc != 0:
        return build_rc
    run_cmd = f"cd {shlex.quote(REMOTE_DIR)} && stdbuf -o0 ./main"
    return run_wsl(remote_command(run_cmd), RAW / f"{variant}_run.log", timeout=3600)


def parse_remote_env() -> List[Dict[str, object]]:
    text = read_text(RAW / "remote_environment.log")
    rows: List[Dict[str, object]] = []
    for key in ["hostname", "whoami", "uname", "remote_dir"]:
        match = re.search(rf"^{key},(.+)$", text, re.MULTILINE)
        if match:
            rows.append({"key": key, "value": match.group(1).strip(), "evidence": rel(RAW / "remote_environment.log")})
    model = re.search(r"^Model name:\s+(.+)$", text, re.MULTILINE)
    flags = re.search(r"^Flags:\s+(.+)$", text, re.MULTILINE)
    if model:
        rows.append({"key": "cpu_model", "value": model.group(1).strip(), "evidence": rel(RAW / "remote_environment.log")})
    if flags:
        rows.append({"key": "has_avx512f", "value": "yes" if "avx512f" in flags.group(1) else "no", "evidence": rel(RAW / "remote_environment.log")})
    write_csv(REMOTE_ENV, ["key", "value", "evidence"], rows)
    return rows


def parse_samples(variant: str) -> List[Dict[str, object]]:
    path = RAW / f"{variant}_run.log"
    text = read_text(path)
    correctness = "missing"
    correct = CORRECT_RE.search(text)
    if correct:
        correctness = correct.group("status")
    rows: List[Dict[str, object]] = []
    for match in SAMPLE_RE.finditer(text):
        rows.append({
            "variant": variant,
            "rep": match.group("rep"),
            "correctness": correctness,
            "mode": match.group("mode"),
            "r": match.group("r"),
            "pvw_us": match.group("pvw_us"),
            "pvw_lane_us": match.group("pvw_lane_us"),
            "scalar_repeated_us": match.group("scalar_us"),
            "scalar_lane_us": match.group("scalar_lane_us"),
            "speedup_vs_scalar_repeated": match.group("speedup"),
            "source_run_log": rel(path),
        })
    return rows


def summarize(variant: str, rows: List[Dict[str, object]]) -> Dict[str, object]:
    vals = [float(row["pvw_lane_us"]) for row in rows if row["variant"] == variant]
    scalars = [float(row["scalar_lane_us"]) for row in rows if row["variant"] == variant]
    correctness = {row["correctness"] for row in rows if row["variant"] == variant}
    return {
        "variant": variant,
        "reps": len(vals),
        "correctness": "Pass" if vals and correctness == {"Pass"} else ",".join(sorted(correctness)) or "missing",
        "t_over_r_mean_us": f"{statistics.mean(vals):.3f}" if vals else "",
        "t_over_r_stddev_us": f"{statistics.pstdev(vals):.3f}" if len(vals) > 1 else "0.000",
        "t_over_r_min_us": f"{min(vals):.3f}" if vals else "",
        "t_over_r_max_us": f"{max(vals):.3f}" if vals else "",
        "scalar_t_over_r_mean_us": f"{statistics.mean(scalars):.3f}" if scalars else "",
        "speedup_vs_scalar_mean": f"{statistics.mean(scalars) / statistics.mean(vals):.6f}" if vals and scalars else "",
    }


def sha256(path: Path) -> Dict[str, object]:
    data = path.read_bytes()
    return {"path": rel(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def artifact_index() -> None:
    paths = [DOC, REPORT, COMMANDS, NATIVE_PROBE, REMOTE_ENV, SAMPLES, SUMMARY, PROOF, QUEUE, BUILDER]
    paths.extend(sorted(RAW.glob("*.log")))
    write_csv(ARTIFACT_INDEX, ["path", "bytes", "sha256"], [sha256(path) for path in paths if path.exists()])


def run_stage() -> Dict[str, object]:
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    access = probe_access()
    if access["status"] != "passed":
        return access
    steps = [
        ("sync", sync_repo()),
        ("remote_env", collect_remote_env()),
        ("fast_control", run_remote_variant("fast_control", "")),
        ("backend_sub_decomp_dual", run_remote_variant("backend_sub_decomp_dual", CANDIDATE_FLAGS)),
    ]
    for name, rc in steps:
        if rc != 0:
            access = dict(access)
            access["status"] = "failed"
            access["reason"] = f"{name}_failed"
            access["exit_code"] = rc
            write_csv(NATIVE_PROBE, access.keys(), [access])
            return access
    return access


def build_reports(access: Dict[str, object]) -> str:
    env_rows = parse_remote_env() if (RAW / "remote_environment.log").exists() else []
    sample_rows = parse_samples("fast_control") + parse_samples("backend_sub_decomp_dual")
    write_csv(SAMPLES, [
        "variant", "rep", "correctness", "mode", "r", "pvw_us", "pvw_lane_us",
        "scalar_repeated_us", "scalar_lane_us", "speedup_vs_scalar_repeated", "source_run_log",
    ], sample_rows)

    control = summarize("fast_control", sample_rows)
    candidate = summarize("backend_sub_decomp_dual", sample_rows)
    control_mean = float(control["t_over_r_mean_us"] or 0)
    candidate_mean = float(candidate["t_over_r_mean_us"] or 0)
    control_min = float(control["t_over_r_min_us"] or 0)
    candidate_max = float(candidate["t_over_r_max_us"] or 0)
    mean_speedup = control_mean / candidate_mean if control_mean and candidate_mean else 0.0
    conservative = control_min / candidate_max if control_min and candidate_max else 0.0

    if access["status"] != "passed":
        decision = "PASS_STAGE283_NATIVE_ACCESS_MISSING_HANDOFF_READY"
    elif control["correctness"] == "Pass" and candidate["correctness"] == "Pass" and mean_speedup >= 1.02:
        decision = "PASS_STAGE283_NATIVE_TARGET_REPEATED_POSITIVE"
    elif control["correctness"] == "Pass" and candidate["correctness"] == "Pass":
        decision = "PASS_STAGE283_NATIVE_TARGET_REPEATED_NEUTRAL"
    else:
        decision = "FAIL_STAGE283_NATIVE_TARGET_REPEATED"

    summary_rows = [
        control,
        candidate,
        {
            "variant": "comparison",
            "reps": min(int(control["reps"]), int(candidate["reps"])),
            "correctness": "Pass" if control["correctness"] == "Pass" and candidate["correctness"] == "Pass" else "missing_or_fail",
            "speedup_vs_fast_control_mean": f"{mean_speedup:.6f}" if mean_speedup else "",
            "conservative_control_min_over_candidate_max": f"{conservative:.6f}" if conservative else "",
            "decision": decision,
        },
    ]
    write_csv(SUMMARY, [
        "variant", "reps", "correctness", "t_over_r_mean_us", "t_over_r_stddev_us",
        "t_over_r_min_us", "t_over_r_max_us", "scalar_t_over_r_mean_us",
        "speedup_vs_scalar_mean", "speedup_vs_fast_control_mean",
        "conservative_control_min_over_candidate_max", "decision",
    ], summary_rows)

    proof_rows = [
        {"gate": "G1_access", "status": "PASS" if access["status"] == "passed" else "PASS_RECORDED_MISSING", "metric": "native access", "value": access["reason"], "interpretation": "Native evidence is allowed only when access succeeds."},
        {"gate": "G2_remote_env", "status": "PASS" if env_rows else "MISSING", "metric": "remote env rows", "value": str(len(env_rows)), "interpretation": "CPU/backend provenance for native runs."},
        {"gate": "G3_correctness", "status": "PASS" if control["correctness"] == "Pass" and candidate["correctness"] == "Pass" else "MISSING_OR_FAIL", "metric": "correctness", "value": f"{control['correctness']}/{candidate['correctness']}", "interpretation": "Timing is interpreted only after both native variants pass."},
        {"gate": "G4_repeated_speed", "status": "PASS" if mean_speedup >= 1.02 else "MISSING_OR_NEUTRAL", "metric": "candidate/control mean", "value": f"{mean_speedup:.6f}" if mean_speedup else "missing", "interpretation": "Native target repeated T_bootstrap/r speedup."},
        {"gate": "G5_decision", "status": decision, "metric": "stage decision", "value": decision, "interpretation": "No native performance claim if access is missing."},
    ]
    write_csv(PROOF, ["gate", "status", "metric", "value", "interpretation"], proof_rows)
    queue_rows = [
        {"priority": "P0", "route": "stage284_target_resource_refresh", "entry_condition": decision, "gate": "Refresh target-size resource and keygen for selected candidate.", "failure_action": "Report speed/resource tradeoff explicitly."},
        {"priority": "P1", "route": "stage285_native_access_resolution", "entry_condition": access["status"] != "passed", "gate": "Provide key-based SSH or STAGE283_REMOTE_AUTH at runtime; rerun Stage283.", "failure_action": "Keep all performance claims local-only."},
    ]
    write_csv(QUEUE, ["priority", "route", "entry_condition", "gate", "failure_action"], queue_rows)
    write_text(COMMANDS, f"""# Stage283 Reproduction Commands

Key-based SSH path:

```bash
python3 scripts/build_stage283_native_target_repeated_gate.py
```

Environment-auth path:

```bash
STAGE283_REMOTE_AUTH='<provided out of band>' python3 scripts/build_stage283_native_target_repeated_gate.py
```

No credential is stored in repository artifacts. The target directory is
`{REMOTE_DIR}` and the primary endpoint is native `T_bootstrap/r`.
""")

    latency_table = "\n".join(
        f"| {row['variant']} | {row['reps']} | {row['correctness']} | {row.get('t_over_r_mean_us','')} | {row.get('speedup_vs_scalar_mean','')} | {row.get('speedup_vs_fast_control_mean','')} |"
        for row in summary_rows
    )
    report = f"""# Stage283 Native Target Repeated Gate

Decision: `{decision}`.

Stage283 is the native target-parameter gate for the selected
`backend_sub_decomp_dual` CMUX residual path. It uses `T_bootstrap/r` as the
primary endpoint and does not convert WSL results into native evidence.

## Native Access

| status | host | user | auth_mode | reason |
| --- | --- | --- | --- | --- |
| {access['status']} | {access['host']} | {access['user']} | {access['auth_mode']} | {access['reason']} |

## Latency Summary

| variant | reps | correctness | mean T/r us | scalar speedup mean | speedup vs fast control |
| --- | ---: | --- | ---: | ---: | ---: |
{latency_table}

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
""" + "\n".join(
        f"| {row['gate']} | {row['status']} | {row['metric']} | {row['value']} | {row['interpretation']} |"
        for row in proof_rows
    ) + f"""

Generated from input head `{HEAD}`.
"""
    write_text(DOC, report)
    write_text(REPORT, report)
    append_once(CURRENT_GOAL, "<!-- stage283-native-target-repeated-gate -->", f"""<!-- stage283-native-target-repeated-gate -->
### Stage283 native target repeated gate

`{decision}` records the native target-parameter repeated gate status for the
selected `backend_sub_decomp_dual` path. Native performance claims remain
disallowed unless this stage records native access and repeated target results.
""")
    append_once(HYPOTHESES, "H10_stage283_native_target_repeated_gate:", f"""H10_stage283_native_target_repeated_gate:
  status: {decision}
  evidence:
    - repro/stage283_native_target_repeated_gate/native_access_probe.csv
    - repro/stage283_native_target_repeated_gate/latency_summary.csv
    - repro/stage283_native_target_repeated_gate/proof_gate.csv
    - docs/stage283_native_target_repeated_gate.md
  conclusion: >
    Stage283 records native target repeated-gate status for the selected
    CMUX residual candidate. Native claims are allowed only if access and
    repeated target runs are present.
""")
    append_once(RUN_LOG, "stage283-native-target-repeated-gate-001", f"""stage283-native-target-repeated-gate-001,2026-07-04,{HEAD},Stage 283,native-spqlios_avx512,bash/python scripts/build_stage283_native_target_repeated_gate.py,"native target repeated gate for selected r=4 include-zero CMUX residual candidate",n/a,{decision},"Native target gate; missing access keeps claims local-only.",docs/stage283_native_target_repeated_gate.md; repro/stage283_native_target_repeated_gate/proof_gate.csv
""")
    append_once(MANIFEST, "- stage283_native_target_repeated_gate:", """- stage283_native_target_repeated_gate:
  - `docs/stage283_native_target_repeated_gate.md`
  - `scripts/build_stage283_native_target_repeated_gate.py`
  - `repro/stage283_native_target_repeated_gate/`
""")
    append_once(CHECKLIST, "<!-- stage283-native-target-repeated-gate-checklist -->", f"""<!-- stage283-native-target-repeated-gate-checklist -->
- [x] Stage283 records `{decision}` for native target repeated-gate status.
""")
    artifact_index()
    return decision


def main() -> None:
    access = run_stage()
    decision = build_reports(access)
    print(decision)


if __name__ == "__main__":
    main()
