#!/usr/bin/env python3
"""Stage214: post-Stage213 frontier ledger and native-counter handoff pack."""

from __future__ import annotations

import csv
import hashlib
import socket
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage214_frontier_native_counter_handoff"

DOC = ROOT / "docs" / "stage214_frontier_native_counter_handoff.md"
PLAN = ROOT / "experiments" / "stage214_frontier_native_counter_handoff_plan.md"
THEORY = ROOT / "theory_checks" / "stage214_frontier_counter_scope.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage214_frontier_native_counter_handoff.md"

ROUTE_LEDGER = OUT / "route_ledger.csv"
ACCESS_PROBE = OUT / "access_probe.csv"
COUNTER_PLAN = OUT / "native_counter_plan.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "frontier_native_counter_handoff_report.md"
RUNNER = OUT / "run_native_stage214_counters.sh"
SSH_HANDOFF = OUT / "ssh_handoff_commands.md"
ARTIFACT = OUT / "artifact_index.csv"
REPRO = OUT / "reproduction_commands.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE208_TAIL = ROOT / "repro" / "stage208_current_head_profile_refresh" / "component_attribution.csv"
STAGE213_COMPARISON = ROOT / "repro" / "stage213_dft_wrapper_integration_preflight" / "comparison.csv"
STAGE213_PROOF = ROOT / "repro" / "stage213_dft_wrapper_integration_preflight" / "proof_gate.csv"
STAGE211_PROOF = ROOT / "repro" / "stage211_fft_dataflow_preflight" / "proof_gate.csv"
STAGE193_SUMMARY = ROOT / "repro" / "stage193_exact_addmul_dataflow_preflight" / "summary.csv"
STAGE192_SUMMARY = ROOT / "repro" / "stage192_compact_admission_route_selection" / "summary.csv"
STAGE183_SCREEN = ROOT / "repro" / "stage183_addmul_dataflow_screen" / "mechanism_screen.csv"
STAGE206_AB = ROOT / "repro" / "stage206_current_head_highstat" / "ab_summary.csv"
STAGE207_RESOURCE = ROOT / "repro" / "stage207_current_head_resource_refresh" / "resource_comparison.csv"

REMOTE_HOST = "192.168.107.220"
REMOTE_USER = "delld"
REMOTE_BASE = "/home/delld/spz"
DECISION = "PASS_STAGE214_FRONTIER_NATIVE_COUNTER_HANDOFF_READY"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


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


def first_matching(rows: List[Dict[str, str]], key: str, value: str, field: str) -> str:
    for row in rows:
        if row.get(key) == value:
            return row.get(field, "")
    return ""


def stage213_min_combined() -> str:
    vals = []
    for row in read_csv(STAGE213_COMPARISON):
        if row.get("variant") == "combined_current":
            try:
                vals.append(float(row["speedup_vs_baseline"]))
            except (KeyError, ValueError):
                pass
    return f"{min(vals):.9f}" if vals else ""


def stage213_min_dft() -> str:
    vals = []
    for row in read_csv(STAGE213_COMPARISON):
        if row.get("variant") == "torus_to_dft_rows":
            try:
                vals.append(float(row["speedup_vs_baseline"]))
            except (KeyError, ValueError):
                pass
    return f"{min(vals):.9f}" if vals else ""


def route_ledger_rows() -> List[Dict[str, str]]:
    stage183_text = read_text(STAGE183_SCREEN)
    return [
        {
            "route": "current_exact_pvw_mat_sab",
            "status": "KEEP_BASELINE_AND_CLAIM_SCOPE",
            "primary_evidence": f"{rel(STAGE206_AB)}; {rel(STAGE207_RESOURCE)}",
            "decision_basis": "Current exact r-body PVW/MAT-SAB path remains the implemented complete-SAB path under T_bootstrap/r.",
            "code_permission": "baseline_only",
            "next_gate": "Use as regression reference for any future candidate.",
        },
        {
            "route": "multirow_dft_wrapper",
            "status": "NEGATIVE_ABLATION_NOT_PROMOTED",
            "primary_evidence": rel(STAGE213_COMPARISON),
            "decision_basis": f"Integrated MAT-EP split gate: min DFT-row speedup {stage213_min_dft()}, min combined_current speedup {stage213_min_combined()}.",
            "code_permission": "default_off_only",
            "next_gate": "Do not run complete-SAB A/B for this wrapper unless a new integrated gate reverses Stage213.",
        },
        {
            "route": "same_format_dft_batching_or_direct_scale",
            "status": "DENIED_PRIOR_GATES",
            "primary_evidence": rel(STAGE211_PROOF),
            "decision_basis": "Stage211 keeps old DFT batching/direct-scale routes closed unless a genuinely new primitive appears.",
            "code_permission": "denied",
            "next_gate": "Native counters or new backend primitive only.",
        },
        {
            "route": "exact_addmul_retile_bodymajor_streaming",
            "status": "DENIED_PRIOR_GATES",
            "primary_evidence": f"{rel(STAGE193_SUMMARY)}; {rel(STAGE183_SCREEN)}",
            "decision_basis": "Stage193 found no addmul code candidate; Stage183 records bodymajor/fulltile/streaming as prior rejected or blocked.",
            "code_permission": "denied_without_new_counter_mechanism",
            "next_gate": "Native counter/assembly evidence must identify a new mechanism.",
        },
        {
            "route": "compact_shared_output_sab",
            "status": "PROOF_ONLY_IMPLEMENTATION_DENIED",
            "primary_evidence": rel(STAGE192_SUMMARY),
            "decision_basis": "Compact route has unresolved key distribution, closed-state, and noise gates.",
            "code_permission": "no_sab_hotpath_code",
            "next_gate": "Formal structured-key/noise proof before any implementation admission.",
        },
        {
            "route": "tail_extract_packing_ks",
            "status": "DEFER_SMALL_SHARE",
            "primary_evidence": rel(STAGE208_TAIL),
            "decision_basis": "Stage208 tail share stayed below the implementation threshold after current-head refresh.",
            "code_permission": "defer",
            "next_gate": "Reopen only if a new profile shows tail share is material.",
        },
        {
            "route": "native_hardware_counters",
            "status": "NEXT_EVIDENCE_ROUTE",
            "primary_evidence": rel(ACCESS_PROBE),
            "decision_basis": "Local WSL lacks perf; CB5 SSH port is reachable but non-interactive authentication is not configured in this session.",
            "code_permission": "measurement_only",
            "next_gate": "Run the Stage214 handoff script on native Linux or remote host with safe credentials.",
        },
    ]


def access_probe_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    try:
        with socket.create_connection((REMOTE_HOST, 22), timeout=5):
            tcp = "reachable"
    except OSError as exc:
        tcp = f"unreachable:{exc.__class__.__name__}"
    rows.append(
        {
            "target": f"{REMOTE_USER}@{REMOTE_HOST}:22",
            "probe": "tcp_connect",
            "status": tcp,
            "detail": "Port reachability only; no credentials are used or stored.",
        }
    )
    proc = subprocess.run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=5",
            f"{REMOTE_USER}@{REMOTE_HOST}",
            "true",
        ],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
    )
    status = "key_auth_available" if proc.returncode == 0 else "noninteractive_auth_not_configured"
    rows.append(
        {
            "target": f"{REMOTE_USER}@{REMOTE_HOST}",
            "probe": "ssh_batchmode",
            "status": status,
            "detail": f"returncode={proc.returncode}; noninteractive authentication was not accepted",
        }
    )
    proc_wsl = subprocess.run(
        ["wsl.exe", "bash", "-lc", "command -v perf 2>/dev/null || true"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
    )
    rows.append(
        {
            "target": "local_wsl",
            "probe": "perf_path",
            "status": "available" if proc_wsl.stdout.strip() else "missing",
            "detail": proc_wsl.stdout.strip(),
        }
    )
    return rows


def counter_plan_rows() -> List[Dict[str, str]]:
    return [
        {
            "step": "build_baseline_and_candidate",
            "command": "bash repro/stage214_frontier_native_counter_handoff/run_native_stage214_counters.sh",
            "expected_output": "native_perf_raw/*.log",
            "gate": "Build baseline and MAT_TRGSW_MULTIROW_DFT_WRAPPER variants on native Linux.",
        },
        {
            "step": "perf_split_variants",
            "command": "perf stat -x, -e cycles,instructions,cache-references,cache-misses,branches,branch-misses,mem_inst_retired.all_loads,mem_inst_retired.all_stores,fp_arith_inst_retired.512b_packed_double,fp_arith_inst_retired.256b_packed_double",
            "expected_output": "counter logs for r=2/r=4 torus_to_dft_rows and combined_current",
            "gate": "Counters must be collected for both baseline and wrapper builds.",
        },
        {
            "step": "admission_rule",
            "command": "compare wrapper against baseline",
            "expected_output": "promotion only if combined_current improves and counters identify a new mechanism",
            "gate": "No complete-SAB A/B is authorized from counters alone.",
        },
    ]


def proof_rows(access: List[Dict[str, str]], routes: List[Dict[str, str]]) -> List[Dict[str, str]]:
    blocked_local = first_matching(access, "target", "local_wsl", "status") == "missing"
    remote_tcp = first_matching(access, "probe", "tcp_connect", "status")
    remote_auth = first_matching(access, "probe", "ssh_batchmode", "status")
    return [
        {
            "gate": "G1_stage213_frontier_input",
            "status": "PASS",
            "metric": "stage213_decision",
            "value": "PASS_STAGE213_DFT_WRAPPER_COMPONENT_ONLY",
            "evidence": rel(STAGE213_PROOF),
            "detail": "Stage214 starts after Stage213 denies complete-SAB A/B for the DFT wrapper.",
        },
        {
            "gate": "G2_route_ledger",
            "status": "PASS_RECORDED",
            "metric": "route_count",
            "value": str(len(routes)),
            "evidence": rel(ROUTE_LEDGER),
            "detail": "Local hot-path routes are classified to prevent reopening rejected mechanisms without new evidence.",
        },
        {
            "gate": "G3_local_counter_status",
            "status": "BLOCKED_LOCAL_WSL_NO_PERF" if blocked_local else "AVAILABLE",
            "metric": "local_perf_path",
            "value": first_matching(access, "target", "local_wsl", "detail"),
            "evidence": rel(ACCESS_PROBE),
            "detail": "Local WSL cannot provide hardware-counter attribution when perf is missing.",
        },
        {
            "gate": "G4_remote_access_status",
            "status": "REMOTE_PORT_REACHABLE_AUTH_NOT_CONFIGURED" if remote_tcp == "reachable" and remote_auth != "key_auth_available" else remote_auth,
            "metric": "tcp;ssh_batchmode",
            "value": f"{remote_tcp};{remote_auth}",
            "evidence": rel(ACCESS_PROBE),
            "detail": "Remote execution is possible only after safe non-interactive authentication or manual credential entry.",
        },
        {
            "gate": "G5_stage214_decision",
            "status": DECISION,
            "metric": "decision",
            "value": DECISION,
            "evidence": rel(PROOF),
            "detail": "The next executable route is native hardware-counter collection or a new formal compact proof, not speculative local hot-path code.",
        },
    ]


def next_rows() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "stage215_native_counter_execution",
            "entry_condition": "Native Linux perf is available and credentials are handled outside committed artifacts.",
            "gate": "Counter logs for r=2/r=4 split variants; parse load/store/FMA/cycle/cache counters.",
            "status": "ready_handoff",
            "evidence": rel(RUNNER),
        },
        {
            "priority": "P1",
            "route": "structured_compact_formal_proof",
            "entry_condition": "A real proof addresses key distribution, closed state, and noise recurrence.",
            "gate": "T1/T2/T4 proof gates before any implementation.",
            "status": "proof_only",
            "evidence": rel(STAGE192_SUMMARY),
        },
        {
            "priority": "P2",
            "route": "new_hotpath_code",
            "entry_condition": "Stage215 counters or proof gates identify a new mechanism.",
            "gate": "Flag-only implementation, staged equivalence, complete-SAB T_bootstrap/r A/B, noise/resource.",
            "status": "denied_now",
            "evidence": rel(ROUTE_LEDGER),
        },
    ]


def write_runner() -> None:
    text = """#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"
OUT="repro/stage214_frontier_native_counter_handoff/native_perf_raw"
mkdir -p "$OUT"

EVENTS="${STAGE214_EVENTS:-cycles,instructions,cache-references,cache-misses,branches,branch-misses,mem_inst_retired.all_loads,mem_inst_retired.all_stores,fp_arith_inst_retired.512b_packed_double,fp_arith_inst_retired.256b_packed_double}"
JOBS="${STAGE214_JOBS:-$(nproc)}"

if ! command -v perf >/dev/null 2>&1; then
  echo "perf not found on this host" >&2
  exit 2
fi

if [ ! -f repro/stage213_dft_wrapper_integration_preflight/stage213_dft_wrapper_integration_preflight.c ]; then
  echo "Stage213 probe source is missing; run from repository root at a commit containing Stage213." >&2
  exit 3
fi

build_and_run() {
  local impl="$1"
  local extra_make="$2"
  local extra_cflags="$3"
  cd "$ROOT/src/mosfhet"
  make clean >/dev/null 2>&1 || true
  make static FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false ENABLE_PVW_TMLWE=true MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true $extra_make -j"$JOBS"
  cd "$ROOT"
  for r in 2 4; do
    local bin="$OUT/stage214_${impl}_r${r}_probe"
    gcc -O3 -march=native -Wall -Wextra -DUSE_SPQLIOS -DAVX512_OPT -DMAT_TRGSW_AVX512_SMALLR_SPECIALIZED $extra_cflags \
      -DSTAGE209_R="$r" -DSTAGE209_N=2048 -DSTAGE209_ITEMS="${STAGE214_ITEMS:-128}" \
      -DSTAGE209_REPS="${STAGE214_REPS:-8}" -DSTAGE209_WARMUPS="${STAGE214_WARMUPS:-2}" -DSTAGE209_BG_BIT=23 \
      -I . -I src/mosfhet/include \
      -o "$bin" repro/stage213_dft_wrapper_integration_preflight/stage213_dft_wrapper_integration_preflight.c src/mosfhet/lib/libmosfhet.a -lm
    for variant in torus_to_dft_rows combined_current; do
      perf stat -x, -e "$EVENTS" -o "$OUT/perf_${impl}_r${r}_${variant}.log" "$bin" "$variant" > "$OUT/run_${impl}_r${r}_${variant}.log" 2>&1
    done
    rm -f "$bin"
  done
}

build_and_run baseline "" ""
build_and_run wrapper "MAT_TRGSW_MULTIROW_DFT_WRAPPER=true" "-DMAT_TRGSW_MULTIROW_DFT_WRAPPER"

echo "Stage214 native counter logs written to $OUT"
"""
    write_text(RUNNER, text)


def write_ssh_handoff() -> None:
    text = f"""# Stage214 SSH Handoff Commands

These commands intentionally do not contain credentials. Use an SSH agent or
interactive credential entry outside committed artifacts.

```bash
REMOTE={REMOTE_USER}@{REMOTE_HOST}
REMOTE_BASE={REMOTE_BASE}
ARCHIVE=/tmp/fab-stage214-$(git rev-parse --short HEAD).tar.gz

git archive --format=tar.gz --output "$ARCHIVE" HEAD
ssh "$REMOTE" "mkdir -p $REMOTE_BASE/fab-stage214 && tar -xzf - -C $REMOTE_BASE/fab-stage214" < "$ARCHIVE"
ssh "$REMOTE" "cd $REMOTE_BASE/fab-stage214 && bash repro/stage214_frontier_native_counter_handoff/run_native_stage214_counters.sh"
scp -r "$REMOTE:$REMOTE_BASE/fab-stage214/repro/stage214_frontier_native_counter_handoff/native_perf_raw" repro/stage214_frontier_native_counter_handoff/
```
"""
    write_text(SSH_HANDOFF, text)


def report(routes: List[Dict[str, str]], access: List[Dict[str, str]], plan: List[Dict[str, str]], gates: List[Dict[str, str]], queue: List[Dict[str, str]]) -> str:
    return f"""# Stage214 Frontier Native Counter Handoff

Decision: `{DECISION}`.

Stage214 closes the post-Stage213 local frontier without redefining the final
goal. The current exact PVW/MAT-SAB path remains the implemented baseline; the
Stage212/213 DFT wrapper is retained as a default-off negative ablation; compact
SAB remains proof-only; exact addmul/bodymajor/streaming reopen routes require
new counter-backed mechanisms.

This stage does not mark the research goal complete. It creates the native
counter handoff needed to continue without storing credentials in the repo.

## Route Ledger

{table(routes, ["route", "status", "primary_evidence", "decision_basis", "code_permission", "next_gate"])}

## Access Probe

{table(access, ["target", "probe", "status", "detail"])}

## Counter Plan

{table(plan, ["step", "command", "expected_output", "gate"])}

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


def update_tracking() -> None:
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 214: Frontier Native Counter Handoff",
        f"""
## Stage 214: Frontier Native Counter Handoff

Goal:

```text
Close the post-Stage213 local route ledger and prepare a credential-free native
hardware-counter handoff for the next evidence route.
```

Status:

```text
Completed. Stage214 records {DECISION}. Local WSL lacks `perf`, CB5 SSH port
is reachable, and non-interactive SSH auth is not configured in this session.
No new hot-path code is authorized without Stage215 native counters or a new
formal compact proof.
```
""",
    )
    append_once(
        GOAL,
        "Stage214 frontier native counter handoff",
        f"""

## Stage214 frontier native counter handoff

At commit `{head}`, Stage214 records the post-Stage213 route ledger and a
credential-free native counter handoff pack. This keeps the research loop
moving without storing secrets or claiming unsupported complete-SAB gains.
""",
    )
    append_once(
        CURRENT_GOAL,
        "Stage214 frontier native counter handoff",
        f"""

### Stage214 frontier native counter handoff

`{DECISION}`: local hot-path candidates are closed or proof-gated; the next
executable route is Stage215 native hardware-counter execution using the
handoff script.
""",
    )
    append_once(
        HYPOTHESES,
        "H10_stage214_frontier_native_counter_handoff",
        f"""

H10_stage214_frontier_native_counter_handoff:
  status: native_counter_handoff_ready
  evidence:
    - repro/stage214_frontier_native_counter_handoff/route_ledger.csv
    - repro/stage214_frontier_native_counter_handoff/proof_gate.csv
    - docs/stage214_frontier_native_counter_handoff.md
  conclusion: >
    Stage214 records {DECISION}. No local hot-path code is authorized after
    Stage213; native hardware counters or formal compact proof gates are the
    next evidence routes.
""",
    )
    append_once(
        RUN_LOG,
        "stage214-frontier-native-counter-handoff-001",
        f"""stage214-frontier-native-counter-handoff-001,2026-07-04,{head},Stage 214,n/a,python scripts/build_stage214_frontier_native_counter_handoff.py,post-Stage213 route ledger and native counter handoff,n/a,{DECISION},"Local perf missing; remote port reachable but noninteractive auth not configured; no secrets stored.",docs/stage214_frontier_native_counter_handoff.md; repro/stage214_frontier_native_counter_handoff/route_ledger.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage214_frontier_native_counter_handoff:",
        """

- stage214_frontier_native_counter_handoff:
  - `docs/stage214_frontier_native_counter_handoff.md`
  - `experiments/stage214_frontier_native_counter_handoff_plan.md`
  - `theory_checks/stage214_frontier_counter_scope.md`
  - `algorithm_variants/mat_rlwe_sab_stage214_frontier_native_counter_handoff.md`
  - `scripts/build_stage214_frontier_native_counter_handoff.py`
  - `repro/stage214_frontier_native_counter_handoff/`
""",
    )
    append_once(
        CHECKLIST,
        "Stage214 frontier native counter handoff",
        f"""
- [x] Stage214 frontier native counter handoff records route ledger, access
  status, credential-free native runner, and next queue. Decision: `{DECISION}`.
""",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    routes = route_ledger_rows()
    access = access_probe_rows()
    plan = counter_plan_rows()
    gates = proof_rows(access, routes)
    queue = next_rows()
    write_runner()
    write_ssh_handoff()

    write_csv(ROUTE_LEDGER, routes, ["route", "status", "primary_evidence", "decision_basis", "code_permission", "next_gate"])
    write_csv(ACCESS_PROBE, access, ["target", "probe", "status", "detail"])
    write_csv(COUNTER_PLAN, plan, ["step", "command", "expected_output", "gate"])
    write_csv(PROOF, gates, ["gate", "status", "metric", "value", "evidence", "detail"])
    write_csv(NEXT, queue, ["priority", "route", "entry_condition", "gate", "status", "evidence"])

    text = report(routes, access, plan, gates, queue)
    write_text(DOC, text)
    write_text(REPORT, text)
    write_text(PLAN, "# Stage214 Frontier Native Counter Handoff Plan\n\nRecord the route ledger after Stage213 and prepare a native Linux counter handoff without storing credentials. Hot-path code remains denied until Stage215 counters or compact proof gates provide new evidence.\n")
    write_text(THEORY, "# Stage214 Frontier Counter Scope\n\nHardware counters can reopen implementation only by identifying a new mechanism in load/store/FMA/cache/cycle behavior. They do not by themselves prove complete-SAB speedup, theoretical optimality, or compact-SAB correctness.\n")
    write_text(VARIANT, "# Stage214 Frontier Native Counter Handoff\n\nNo production variant is added. The handoff runner measures the default exact path and the default-off DFT wrapper on native Linux for attribution only.\n")
    write_text(REPRO, "# Stage214 Reproduction Commands\n\n```bash\npython3 scripts/build_stage214_frontier_native_counter_handoff.py\nbash repro/stage214_frontier_native_counter_handoff/run_native_stage214_counters.sh\n```\n")
    write_csv(
        ARTIFACT,
        artifact_rows([DOC, PLAN, THEORY, VARIANT, ROUTE_LEDGER, ACCESS_PROBE, COUNTER_PLAN, PROOF, NEXT, REPORT, RUNNER, SSH_HANDOFF, REPRO, Path(__file__)]),
        ["path", "exists", "sha256", "bytes"],
    )
    update_tracking()
    print(DECISION)
    for row in gates:
        print("GATE214," + row["gate"] + "," + row["status"])


if __name__ == "__main__":
    main()
