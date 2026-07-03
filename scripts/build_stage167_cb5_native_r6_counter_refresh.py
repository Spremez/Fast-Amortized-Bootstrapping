#!/usr/bin/env python3
"""Stage167: CB5 native current r=6 counter refresh."""

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
OUT_DIR = ROOT / "repro" / "stage167_cb5_native_r6_counter_refresh"

SUMMARY_CSV = OUT_DIR / "summary.csv"
COUNTER_CSV = OUT_DIR / "counter_metrics.csv"
RUN_METRICS_CSV = OUT_DIR / "run_metrics.csv"
REMOTE_CSV = OUT_DIR / "remote_environment.csv"
POST_RESTORE_CSV = OUT_DIR / "post_restore_verification.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage167_cb5_native_r6_counter_refresh.md"
PLAN_MD = ROOT / "experiments" / "stage167_cb5_native_r6_counter_refresh_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage167_native_counter_scope.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_native_counter_current_r6.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

REMOTE_USER = os.environ.get("STAGE167_REMOTE_USER", "delld")
REMOTE_HOST = os.environ.get("STAGE167_REMOTE_HOST", "192.168.107.220")
REMOTE_BASE = os.environ.get("STAGE167_REMOTE_BASE", "/home/delld/spz")
REMOTE_PASSWORD = os.environ.get("STAGE167_SSHPASS", "")
MAKE_JOBS = os.environ.get("STAGE167_JOBS", "$(nproc)")
REMOTE_DIR_NAME = f"Fast-Amortized-Bootstrapping-stage167-{subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT, text=True).strip()}"
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

PERF_EVENTS = (
    "cycles,instructions,cache-references,cache-misses,branches,branch-misses,"
    "mem_inst_retired.all_loads,mem_inst_retired.all_stores,"
    "fp_arith_inst_retired.512b_packed_double,"
    "fp_arith_inst_retired.256b_packed_double"
)

PERF_LINE_RE = re.compile(r"^\s*([\d,]+)\s+([A-Za-z0-9_.-]+)\b")
ELAPSED_RE = re.compile(r"^\s*([\d.]+)\s+seconds time elapsed")
USER_RE = re.compile(r"^\s*([\d.]+)\s+seconds user")
SYS_RE = re.compile(r"^\s*([\d.]+)\s+seconds sys")
SUMMARY_RE = re.compile(
    r"SAB_PVW_BENCH summary target_full r=(?P<r>\d+) reps=(?P<reps>\d+) "
    r"pvw_avg_us=(?P<pvw>[0-9.]+).*?scalar_repeated_avg_us=(?P<scalar>[0-9.]+).*?"
    r"speedup_vs_scalar_repeated=(?P<speedup>[0-9.]+)x"
)


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
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
        "-o UserKnownHostsFile=/tmp/codex_stage167_known_hosts "
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
    remote_extract = f"rm -rf {shlex.quote(REMOTE_DIR)} && mkdir -p {shlex.quote(REMOTE_DIR)} && tar -xf - -C {shlex.quote(REMOTE_DIR)}"
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
        "printf 'perf,'; command -v perf || true; "
        "printf 'perf_event_paranoid,'; cat /proc/sys/kernel/perf_event_paranoid; "
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


def perf_remote() -> int:
    sudo_prefix = f"printf %s {shlex.quote(REMOTE_PASSWORD)} | sudo -S -p ''"
    cmd = (
        f"cd {shlex.quote(REMOTE_DIR)} && "
        "orig=$(cat /proc/sys/kernel/perf_event_paranoid); "
        "restore_perf_paranoid(){ "
        f"{sudo_prefix} sysctl -w kernel.perf_event_paranoid=$orig >/dev/null; "
        "}; "
        "trap restore_perf_paranoid EXIT; "
        f"{sudo_prefix} sysctl -w kernel.perf_event_paranoid=1 >/dev/null && "
        f"perf stat -e {shlex.quote(PERF_EVENTS)} -- stdbuf -o0 ./main"
    )
    return run_wsl(remote_command(cmd), OUT_DIR / "run_perf.log", timeout=3600)


def cleanup_remote() -> int:
    cmd = f"cd {shlex.quote(REMOTE_DIR)} && (make clean >/dev/null 2>&1 || true)"
    return run_wsl(remote_command(cmd), OUT_DIR / "cleanup.log", timeout=300)


def verify_restore_remote() -> int:
    cmd = "printf 'perf_event_paranoid_after,'; cat /proc/sys/kernel/perf_event_paranoid"
    return run_wsl(remote_command(cmd), OUT_DIR / "post_restore_verification.log", timeout=60)


def parse_remote_environment() -> List[Dict[str, str]]:
    path = OUT_DIR / "remote_environment.log"
    rows: List[Dict[str, str]] = []
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    for key in ["hostname", "whoami", "uname", "perf", "perf_event_paranoid", "remote_dir"]:
        m = re.search(rf"^{key},(.+)$", text, re.MULTILINE)
        if m:
            rows.append({"key": key, "value": m.group(1).strip(), "evidence": rel(path)})
    model = re.search(r"^Model name:\s+(.+)$", text, re.MULTILINE)
    flags = re.search(r"^Flags:\s+(.+)$", text, re.MULTILINE)
    if model:
        rows.append({"key": "cpu_model", "value": model.group(1).strip(), "evidence": rel(path)})
    if flags:
        rows.append({"key": "has_avx512f", "value": "yes" if "avx512f" in flags.group(1) else "no", "evidence": rel(path)})
    return rows


def parse_perf_and_run() -> tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    path = OUT_DIR / "run_perf.log"
    counter_rows: List[Dict[str, str]] = []
    run_rows: List[Dict[str, str]] = []
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    for raw in text.splitlines():
        line = raw.strip()
        m = PERF_LINE_RE.match(raw)
        if m:
            counter_rows.append({
                "metric": m.group(2),
                "value": m.group(1).replace(",", ""),
                "unit": "count",
                "evidence": rel(path),
                "detail": line,
            })
            continue
        for regex, metric in [(ELAPSED_RE, "elapsed_seconds"), (USER_RE, "user_seconds"), (SYS_RE, "sys_seconds")]:
            m2 = regex.match(raw)
            if m2:
                counter_rows.append({
                    "metric": metric,
                    "value": m2.group(1),
                    "unit": "seconds",
                    "evidence": rel(path),
                    "detail": line,
                })
                break
    correctness = "PASS" if re.search(r"SAB_PVW_BENCH correctness target_full .* Pass", text) else "FAIL"
    run_rows.append({
        "metric": "target_full_correctness",
        "value": correctness,
        "unit": "gate",
        "evidence": rel(path),
        "detail": "target_full correctness Pass line found" if correctness == "PASS" else "target_full correctness Pass line missing",
    })
    for line in text.splitlines():
        m = SUMMARY_RE.search(line)
        if not m:
            continue
        for metric, value in [
            ("r", m.group("r")),
            ("reps", m.group("reps")),
            ("pvw_avg_us", m.group("pvw")),
            ("scalar_repeated_avg_us", m.group("scalar")),
            ("speedup_vs_scalar_repeated", m.group("speedup")),
        ]:
            run_rows.append({
                "metric": metric,
                "value": value,
                "unit": "us" if metric.endswith("_us") else ("x" if metric == "speedup_vs_scalar_repeated" else "value"),
                "evidence": rel(path),
                "detail": line.strip(),
            })
    return counter_rows, run_rows


def metric(rows: List[Dict[str, str]], key: str) -> str:
    for row in rows:
        if row.get("metric") == key:
            return row.get("value", "")
    return ""


def decide(sync_rc: int, env_rc: int, build_rc: int, perf_rc: int, counters: List[Dict[str, str]], run_rows: List[Dict[str, str]]) -> str:
    if not REMOTE_PASSWORD:
        return "BLOCKED_STAGE167_MISSING_REMOTE_PASSWORD_ENV"
    if sync_rc != 0:
        return "FAIL_STAGE167_REMOTE_SYNC"
    if env_rc != 0:
        return "FAIL_STAGE167_REMOTE_ENV_PROBE"
    if build_rc != 0:
        return "FAIL_STAGE167_REMOTE_BUILD"
    if perf_rc != 0:
        return "FAIL_STAGE167_REMOTE_PERF_RUN"
    required = ["cycles", "instructions", "mem_inst_retired.all_loads", "mem_inst_retired.all_stores"]
    if any(not metric(counters, item) for item in required):
        return "FAIL_STAGE167_COUNTERS_INCOMPLETE"
    if metric(run_rows, "target_full_correctness") != "PASS":
        return "FAIL_STAGE167_TARGET_CORRECTNESS"
    return "PASS_STAGE167_CB5_NATIVE_R6_COUNTERS_RECORDED"


def build_summary(decision: str, sync_rc: int, env_rc: int, build_rc: int, perf_rc: int, restore_rows: List[Dict[str, str]], counters: List[Dict[str, str]], run_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    restored = any(row.get("key") == "perf_event_paranoid_after" and row.get("value") == "4" for row in restore_rows)
    return [
        {
            "gate": "stage167_remote_secret",
            "status": "PASS" if REMOTE_PASSWORD else "BLOCKED",
            "metric": "STAGE167_SSHPASS",
            "value": "present" if REMOTE_PASSWORD else "missing",
            "evidence": "environment variable only; not written to artifacts",
            "detail": "Remote password is consumed from environment and scrubbed from logs.",
            "next_action": "Provide STAGE167_SSHPASS only at runtime.",
        },
        {
            "gate": "stage167_sync",
            "status": "PASS" if sync_rc == 0 else "FAIL",
            "metric": "sync_rc",
            "value": str(sync_rc),
            "evidence": rel(OUT_DIR / "sync.log"),
            "detail": "git archive HEAD synchronized to CB5 remote spz directory.",
            "next_action": "Fix SSH/sync before interpreting remote evidence.",
        },
        {
            "gate": "stage167_remote_env",
            "status": "PASS" if env_rc == 0 else "FAIL",
            "metric": "env_probe_rc",
            "value": str(env_rc),
            "evidence": rel(REMOTE_CSV),
            "detail": "Remote CPU, perf path, and perf_event_paranoid recorded.",
            "next_action": "Use native Linux AVX512 host for counter claims.",
        },
        {
            "gate": "stage167_build",
            "status": "PASS" if build_rc == 0 else "FAIL",
            "metric": "build_rc",
            "value": str(build_rc),
            "evidence": rel(OUT_DIR / "build.log"),
            "detail": "Build current r=6 post-fusion path on CB5.",
            "next_action": "Fix build before using counters.",
        },
        {
            "gate": "stage167_perf",
            "status": "PASS" if perf_rc == 0 else "FAIL",
            "metric": "perf_rc",
            "value": str(perf_rc),
            "evidence": rel(OUT_DIR / "run_perf.log"),
            "detail": "Run perf stat with temporary perf_event_paranoid lowering.",
            "next_action": "If perf fails, keep optimality claims blocked.",
        },
        {
            "gate": "stage167_restore_verification",
            "status": "PASS" if restored else "CHECK",
            "metric": "perf_event_paranoid_after",
            "value": next((row.get("value", "") for row in restore_rows if row.get("key") == "perf_event_paranoid_after"), ""),
            "evidence": rel(POST_RESTORE_CSV),
            "detail": "Verify remote perf_event_paranoid after the counter run.",
            "next_action": "Restore to the pre-run value before closing the stage.",
        },
        {
            "gate": "stage167_counters",
            "status": "PASS" if metric(counters, "cycles") and metric(counters, "mem_inst_retired.all_loads") else "FAIL",
            "metric": "cycles;loads;stores;fp512",
            "value": f"{metric(counters, 'cycles')};{metric(counters, 'mem_inst_retired.all_loads')};{metric(counters, 'mem_inst_retired.all_stores')};{metric(counters, 'fp_arith_inst_retired.512b_packed_double')}",
            "evidence": rel(COUNTER_CSV),
            "detail": "Native counter values recorded for current r=6 path.",
            "next_action": "Use counters for attribution, not as proof of theoretical optimality by themselves.",
        },
        {
            "gate": "stage167_decision",
            "status": decision,
            "metric": "speedup_vs_scalar_repeated",
            "value": metric(run_rows, "speedup_vs_scalar_repeated"),
            "evidence": rel(SUMMARY_CSV),
            "detail": "Stage167 refreshes native counter evidence for the current exact r=6 path.",
            "next_action": "Interpret counters against Stage160/161/165 before any optimality wording.",
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


def write_docs(decision: str, summary: List[Dict[str, str]], remote_rows: List[Dict[str, str]], counters: List[Dict[str, str]], run_rows: List[Dict[str, str]]) -> None:
    summary_fields = ["gate", "status", "metric", "value", "evidence", "detail", "next_action"]
    remote_fields = ["key", "value", "evidence"]
    counter_fields = ["metric", "value", "unit", "evidence", "detail"]
    run_fields = ["metric", "value", "unit", "evidence", "detail"]
    write_text_lf(OUT_MD, f"""# Stage167 CB5 Native r=6 Counter Refresh

Decision: `{decision}`.

Stage167 records native Linux perf counters for the current exact r=6
post-fusion PVW/MAT-SAB path. It temporarily lowers
`perf_event_paranoid` for the run and restores the original value afterward.
The remote password is consumed from `STAGE167_SSHPASS` and scrubbed from logs.

## Gate Summary

{table(summary, summary_fields)}

## Remote Environment

{table(remote_rows, remote_fields)}

## Run Metrics

{table(run_rows, run_fields)}

## Counter Metrics

{table(counters, counter_fields)}

## Interpretation

This is attribution evidence for the current implementation. It does not prove
the MAT external product is theoretically optimal; it supplies native
load/store/FMA/cycle context for deciding the next optimization frontier.
""")
    write_text_lf(PLAN_MD, """# Stage167 Validation Plan

Goal: refresh native hardware-counter evidence for the current r=6
post-fusion PVW/MAT-SAB path on CB5.

Procedure:

1. sync current `git archive HEAD` to the remote `spz` directory;
2. build the explicit r=6 path with `spqlios_avx512`;
3. run `perf stat` on `./main`;
4. parse correctness, complete-SAB speedup, cycles, instructions, load/store,
   and AVX512 FP counters;
5. restore `perf_event_paranoid`.

The password must be supplied at runtime through `STAGE167_SSHPASS`; it must
not be written into artifacts.
""")
    write_text_lf(THEORY_MD, """# Stage167 Native Counter Scope

Native counters answer an implementation-attribution question: whether the
current exact r=6 path appears dominated by memory traffic, FMA work, branch
cost, or cache behavior on the target CPU.

They do not by themselves prove theoretical optimality. A theoretical claim
would still need a lower bound tied to the MAT-RLWE/SAB operation count and a
comparison against all relevant representation/keygen alternatives.
""")
    write_text_lf(VARIANT_MD, f"""# Native Counter Current r=6 Path

Flags:

```text
{BASE_FLAGS}
```

Decision: `{decision}`.

The tested path is the current exact r=6 post-fusion PVW/MAT-SAB path:
active-buffer fusion, backend FromDFT-add, sub-decompose fusion, and r>4 tiled
AVX512 MAT external product.
""")


def update_global_docs(decision: str) -> None:
    append_once(ROADMAP_MD, "## Stage 167: CB5 Native r=6 Counter Refresh", f"""
## Stage 167: CB5 Native r=6 Counter Refresh

Goal:

```text
Refresh native Linux perf-counter attribution for the current exact r=6
post-fusion PVW/MAT-SAB path.
```

Status:

```text
Completed. Stage167 records {decision}. Counter evidence is attribution-only
and remains separate from theoretical optimality claims.
```
""")
    append_once(GOAL_MD, "Stage167 refreshes CB5 native r=6 counters", f"""
Stage167 refreshes CB5 native r=6 counters after Stage166. Decision:
`{decision}`. This provides native implementation attribution for the current
exact path, not a new algorithmic speedup claim.
""")
    append_once(CURRENT_GOAL_MD, "71. Treat Stage167 as the CB5 native r=6 counter refresh", f"""
71. Treat Stage167 as the CB5 native r=6 counter refresh:
    `{decision}`. Use it to interpret the current exact path's hardware
    behavior; do not treat counters alone as theoretical optimality proof.
""")
    append_once(HYPOTHESIS_YAML, "id: H91_cb5_native_r6_counters", f"""
  - id: H91_cb5_native_r6_counters
    statement: >
      Native CB5 counters should refresh attribution for the current exact r=6
      post-fusion PVW/MAT-SAB path after backend batching, streaming, and
      generic compact routes are closed or blocked.
    mechanism: >
      Running the current explicit path under perf records cycles,
      instructions, load/store, cache, and AVX512 FP counters on a native
      AVX512 Xeon host.
    status: stage167_cb5_native_r6_counter_refresh
    evidence: docs/stage167_cb5_native_r6_counter_refresh.md; experiments/stage167_cb5_native_r6_counter_refresh_plan.md; theory_checks/stage167_native_counter_scope.md; repro/stage167_cb5_native_r6_counter_refresh/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - remote sync/build/perf fails
      - target_full correctness fails
      - counters are reported as theoretical optimality without lower-bound analysis
""")
    append_once(RUN_LOG, "stage167-cb5-native-r6-counter-refresh-001", f"""
stage167-cb5-native-r6-counter-refresh-001,2026-07-03,{git_head()},Stage 167,spqlios_avx512,python scripts/build_stage167_cb5_native_r6_counter_refresh.py,CB5 native Xeon Gold 6230R; r=6; post-fusion current path,default-rng,{decision},CB5 native r=6 counter refresh.,repro/stage167_cb5_native_r6_counter_refresh
""")
    append_once(MANIFEST, "stage167_cb5_native_r6_counter_refresh", f"""
- stage167_cb5_native_r6_counter_refresh: `{decision}`
  - `docs/stage167_cb5_native_r6_counter_refresh.md`
  - `experiments/stage167_cb5_native_r6_counter_refresh_plan.md`
  - `theory_checks/stage167_native_counter_scope.md`
  - `algorithm_variants/mat_rlwe_sab_native_counter_current_r6.md`
  - `repro/stage167_cb5_native_r6_counter_refresh/`
""")
    append_once(CHECKLIST, "Stage167 CB5 native r=6 counter refresh pack recorded", """
- [x] Stage167 CB5 native r=6 counter refresh pack recorded.
""")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not REMOTE_PASSWORD:
        sync_rc = env_rc = build_rc = perf_rc = 1
        remote_rows: List[Dict[str, str]] = []
        counters: List[Dict[str, str]] = []
        run_rows: List[Dict[str, str]] = []
    else:
        sync_rc = sync_repo()
        env_rc = probe_remote_environment() if sync_rc == 0 else 1
        remote_rows = parse_remote_environment()
        build_rc = build_remote() if env_rc == 0 else 1
        perf_rc = perf_remote() if build_rc == 0 else 1
        counters, run_rows = parse_perf_and_run()
        cleanup_remote()
        verify_restore_remote()

    write_csv(REMOTE_CSV, remote_rows, ["key", "value", "evidence"])
    restore_rows = []
    restore_log = OUT_DIR / "post_restore_verification.log"
    if restore_log.exists():
        text = restore_log.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^perf_event_paranoid_after,(\d+)$", text, re.MULTILINE)
        if m:
            restore_rows.append({
                "key": "perf_event_paranoid_after",
                "value": m.group(1),
                "evidence": rel(restore_log),
                "detail": "Remote value after Stage167 run and cleanup.",
            })
    write_csv(POST_RESTORE_CSV, restore_rows, ["key", "value", "evidence", "detail"])
    write_csv(COUNTER_CSV, counters, ["metric", "value", "unit", "evidence", "detail"])
    write_csv(RUN_METRICS_CSV, run_rows, ["metric", "value", "unit", "evidence", "detail"])
    decision = decide(sync_rc, env_rc, build_rc, perf_rc, counters, run_rows)
    summary = build_summary(decision, sync_rc, env_rc, build_rc, perf_rc, restore_rows, counters, run_rows)
    write_csv(SUMMARY_CSV, summary, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    write_docs(decision, summary, remote_rows, counters, run_rows)
    update_global_docs(decision)
    artifact_index([
        OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, SUMMARY_CSV, COUNTER_CSV,
        RUN_METRICS_CSV, REMOTE_CSV, OUT_DIR / "sync.log",
        OUT_DIR / "remote_environment.log", OUT_DIR / "build.log",
        OUT_DIR / "run_perf.log", OUT_DIR / "cleanup.log", Path(__file__),
        POST_RESTORE_CSV, OUT_DIR / "post_restore_verification.log",
    ])
    print(decision)
    print(f"speedup={metric(run_rows, 'speedup_vs_scalar_repeated')}")
    print(f"cycles={metric(counters, 'cycles')}")
    print(f"loads={metric(counters, 'mem_inst_retired.all_loads')}")


if __name__ == "__main__":
    main()
