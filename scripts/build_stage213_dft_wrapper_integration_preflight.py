#!/usr/bin/env python3
"""Stage213: flag-only MAT-EP multirow DFT wrapper integration preflight."""

from __future__ import annotations

import csv
import hashlib
import re
import statistics
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
MOSFHET_DIR = ROOT / "src" / "mosfhet"
OUT = ROOT / "repro" / "stage213_dft_wrapper_integration_preflight"
C_SOURCE = OUT / "stage213_dft_wrapper_integration_preflight.c"
STAGE209_SOURCE = ROOT / "repro" / "stage209_current_head_mat_ep_split" / "stage209_current_head_mat_ep_split.c"
STAGE212_PROOF = ROOT / "repro" / "stage212_multirow_fft_api_probe" / "proof_gate.csv"

ENV_CSV = OUT / "environment.csv"
RUN_CSV = OUT / "run_metrics.csv"
CORRECTNESS_CSV = OUT / "correctness.csv"
AGG_CSV = OUT / "aggregate.csv"
COMPARISON_CSV = OUT / "comparison.csv"
PROOF_CSV = OUT / "proof_gate.csv"
NEXT_CSV = OUT / "next_stage_queue.csv"
ARTIFACT_CSV = OUT / "artifact_index.csv"
REPORT = OUT / "dft_wrapper_integration_preflight_report.md"
REPRO_COMMANDS = OUT / "reproduction_commands.md"

DOC = ROOT / "docs" / "stage213_dft_wrapper_integration_preflight.md"
PLAN = ROOT / "experiments" / "stage213_dft_wrapper_integration_preflight_plan.md"
THEORY = ROOT / "theory_checks" / "stage213_dft_wrapper_integration_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage213_dft_wrapper_integration_preflight.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

R_VALUES = [2, 4]
VARIANTS = ["torus_to_dft_rows", "combined_current"]
IMPLEMENTATIONS = ["baseline", "wrapper"]
RUNS = 10
N_VALUE = 2048
ITEMS = 128
REPS = 8
WARMUPS = 2
BG_BIT = 23
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


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def wsl_path(path: Path) -> str:
    drive = path.drive.rstrip(":").lower()
    rest = path.as_posix().split(":/", 1)[1]
    return f"/mnt/{drive}/{rest}"


def wsl_repo() -> str:
    return wsl_path(ROOT)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


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
    write_text(path, current + text.strip() + "\n")


def sanitize(text: str) -> str:
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
                f"command: {command}",
                f"returncode: {proc.returncode}",
                "--- stdout ---",
                sanitize(proc.stdout),
                "--- stderr ---",
                sanitize(proc.stderr),
            ]
        ),
    )
    return proc.returncode


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


def write_c_source() -> None:
    source = read_text(STAGE209_SOURCE)
    needle = """for (int row = 0; row < rows; row++) {
          polynomial_torus_to_DFT(scratch->dec_dft[row], dec_bank[item * rows + row]);
        }"""
    replacement = """#if defined(MAT_TRGSW_MULTIROW_DFT_WRAPPER)
        polynomial_torus_to_DFT_array(scratch->dec_dft, &dec_bank[item * rows], rows);
#else
        for (int row = 0; row < rows; row++) {
          polynomial_torus_to_DFT(scratch->dec_dft[row], dec_bank[item * rows + row]);
        }
#endif"""
    count = source.count(needle)
    if count != 2:
        raise SystemExit(f"expected two Stage209 DFT-row loop sites, found {count}")
    write_text(C_SOURCE, source.replace(needle, replacement))


def record_environment() -> List[Dict[str, str]]:
    log = OUT / "environment.log"
    cmd = (
        "printf 'uname,'; uname -a; "
        "printf 'gcc_version,'; gcc --version | head -n 1; "
        "perf_bin=$(command -v perf 2>/dev/null || true); printf 'perf_path,%s\\n' \"$perf_bin\"; "
        "printf 'cpu_model,'; lscpu | sed -n 's/^Model name:[[:space:]]*//p' | head -n 1; "
        "printf 'flags,'; lscpu | sed -n 's/^Flags:[[:space:]]*//p' | head -n 1"
    )
    rc = run_wsl(cmd, log, timeout=60)
    text = read_text(log)
    rows = [{"key": "environment_rc", "value": str(rc), "evidence": rel(log)}]
    for key in ["uname", "gcc_version", "perf_path", "cpu_model", "flags"]:
        match = re.search(rf"^{key},(.*)$", text, re.MULTILINE)
        value = match.group(1).strip() if match else ""
        if key == "flags":
            rows.append({"key": "has_avx512f", "value": "yes" if "avx512f" in value else "no", "evidence": rel(log)})
        rows.append({"key": key, "value": value, "evidence": rel(log)})
    write_csv(ENV_CSV, rows, ["key", "value", "evidence"])
    return rows


def build_static(implementation: str) -> int:
    extra = " MAT_TRGSW_MULTIROW_DFT_WRAPPER=true" if implementation == "wrapper" else ""
    cmd = (
        "cd src/mosfhet && "
        "(make clean >/dev/null 2>&1 || true) && "
        "make static FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false "
        "ENABLE_PVW_TMLWE=true MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true"
        f"{extra} -j$(nproc)"
    )
    return run_wsl(cmd, OUT / f"build_{implementation}.log", timeout=1200)


def compile_probe(implementation: str, r: int) -> int:
    bin_path = OUT / f"stage213_{implementation}_r{r}_probe"
    extra = " -DMAT_TRGSW_MULTIROW_DFT_WRAPPER" if implementation == "wrapper" else ""
    cmd = (
        "gcc -O3 -march=native -Wall -Wextra "
        "-DUSE_SPQLIOS -DAVX512_OPT -DMAT_TRGSW_AVX512_SMALLR_SPECIALIZED"
        f"{extra} -DSTAGE209_R={r} -DSTAGE209_N={N_VALUE} "
        f"-DSTAGE209_ITEMS={ITEMS} -DSTAGE209_REPS={REPS} "
        f"-DSTAGE209_WARMUPS={WARMUPS} -DSTAGE209_BG_BIT={BG_BIT} "
        "-I . -I src/mosfhet/include "
        f"-o {wsl_path(bin_path)} {wsl_path(C_SOURCE)} src/mosfhet/lib/libmosfhet.a -lm"
    )
    return run_wsl(cmd, OUT / f"compile_{implementation}_r{r}.log", timeout=300)


def run_one(implementation: str, r: int, variant: str, sample: int) -> int:
    bin_path = OUT / f"stage213_{implementation}_r{r}_probe"
    log = OUT / f"run_{implementation}_r{r}_{variant}_{sample}.log"
    return run_wsl(f"stdbuf -o0 {wsl_path(bin_path)} {variant}", log, timeout=600)


def parse_run_log(implementation: str, r: int, variant: str, sample: int) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    log = OUT / f"run_{implementation}_r{r}_{variant}_{sample}.log"
    text = read_text(log)
    run_rows: List[Dict[str, str]] = []
    correct_rows: List[Dict[str, str]] = []
    for line in text.splitlines():
        m = RESULT_RE.search(line)
        if m:
            run_rows.append(
                {
                    "implementation": implementation,
                    "r": m.group("r"),
                    "variant": m.group("variant"),
                    "sample": str(sample),
                    "N": m.group("N"),
                    "items": m.group("items"),
                    "reps": m.group("reps"),
                    "calls": m.group("calls"),
                    "total_ns": m.group("total_ns"),
                    "per_call_us": m.group("per_call_us"),
                    "sink": m.group("sink"),
                    "status": m.group("status"),
                    "evidence": rel(log),
                }
            )
        c = CORRECT_RE.search(line)
        if c:
            correct_rows.append(
                {
                    "implementation": implementation,
                    "r": str(r),
                    "variant": c.group("variant"),
                    "sample": str(sample),
                    "check": c.group("check"),
                    "mismatches": c.group("mismatches"),
                    "max_gap": c.group("max_gap"),
                    "status": c.group("status"),
                    "evidence": rel(log),
                }
            )
    return run_rows, correct_rows


def aggregate(run_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    keys = sorted({(r["implementation"], r["r"], r["variant"]) for r in run_rows}, key=lambda x: (x[0], int(x[1]), x[2]))
    for implementation, r, variant in keys:
        vals = [
            float(row["per_call_us"])
            for row in run_rows
            if row["implementation"] == implementation and row["r"] == r and row["variant"] == variant
        ]
        rows.append(
            {
                "implementation": implementation,
                "r": r,
                "variant": variant,
                "samples": str(len(vals)),
                "mean_per_call_us": f"{statistics.mean(vals):.9f}",
                "median_per_call_us": f"{statistics.median(vals):.9f}",
                "min_per_call_us": f"{min(vals):.9f}",
                "max_per_call_us": f"{max(vals):.9f}",
                "stdev_per_call_us": f"{statistics.stdev(vals):.9f}" if len(vals) > 1 else "0.000000000",
            }
        )
    write_csv(
        AGG_CSV,
        rows,
        [
            "implementation",
            "r",
            "variant",
            "samples",
            "mean_per_call_us",
            "median_per_call_us",
            "min_per_call_us",
            "max_per_call_us",
            "stdev_per_call_us",
        ],
    )
    return rows


def compare(agg: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for r in R_VALUES:
        for variant in VARIANTS:
            base = next(row for row in agg if row["implementation"] == "baseline" and row["r"] == str(r) and row["variant"] == variant)
            wrap = next(row for row in agg if row["implementation"] == "wrapper" and row["r"] == str(r) and row["variant"] == variant)
            base_mean = float(base["mean_per_call_us"])
            wrap_mean = float(wrap["mean_per_call_us"])
            speedup = base_mean / wrap_mean if wrap_mean else 0.0
            rows.append(
                {
                    "r": str(r),
                    "variant": variant,
                    "baseline_mean_per_call_us": f"{base_mean:.9f}",
                    "wrapper_mean_per_call_us": f"{wrap_mean:.9f}",
                    "speedup_vs_baseline": f"{speedup:.9f}",
                    "promotion_threshold": f"{PROMOTE_THRESHOLD:.6f}",
                    "decision": "PROMOTE_TO_FULL_SAB_AB" if variant == "combined_current" and speedup >= PROMOTE_THRESHOLD else ("COMPONENT_POSITIVE" if speedup >= PROMOTE_THRESHOLD else "NOT_PROMOTED"),
                    "evidence": rel(AGG_CSV),
                }
            )
    write_csv(
        COMPARISON_CSV,
        rows,
        [
            "r",
            "variant",
            "baseline_mean_per_call_us",
            "wrapper_mean_per_call_us",
            "speedup_vs_baseline",
            "promotion_threshold",
            "decision",
            "evidence",
        ],
    )
    return rows


def decide(build_rcs: Dict[str, int], compile_rcs: Dict[Tuple[str, int], int], run_rcs: List[int], correct_rows: List[Dict[str, str]], comparison: List[Dict[str, str]]) -> str:
    if any(rc != 0 for rc in build_rcs.values()) or any(rc != 0 for rc in compile_rcs.values()) or any(rc != 0 for rc in run_rcs):
        return "BLOCKED_STAGE213_BUILD_OR_RUN"
    if not correct_rows or any(row["status"] != "PASS" or row["mismatches"] != "0" for row in correct_rows):
        return "FAIL_STAGE213_CORRECTNESS"
    combined = [row for row in comparison if row["variant"] == "combined_current"]
    if combined and all(float(row["speedup_vs_baseline"]) >= PROMOTE_THRESHOLD for row in combined):
        return "PASS_STAGE213_DFT_WRAPPER_PROMOTE_FULL_SAB_AB"
    return "PASS_STAGE213_DFT_WRAPPER_COMPONENT_ONLY"


def proof_rows(decision: str, build_rcs: Dict[str, int], compile_rcs: Dict[Tuple[str, int], int], run_rcs: List[int], correct_rows: List[Dict[str, str]], comparison: List[Dict[str, str]]) -> List[Dict[str, str]]:
    correct_ok = bool(correct_rows) and all(row["status"] == "PASS" and row["mismatches"] == "0" for row in correct_rows)
    combined_min = min((float(row["speedup_vs_baseline"]) for row in comparison if row["variant"] == "combined_current"), default=0.0)
    dft_min = min((float(row["speedup_vs_baseline"]) for row in comparison if row["variant"] == "torus_to_dft_rows"), default=0.0)
    return [
        {
            "gate": "G1_stage212_entry",
            "status": "PASS" if STAGE212_PROOF.exists() else "FAIL",
            "metric": "stage212_proof_present",
            "value": "1" if STAGE212_PROOF.exists() else "0",
            "evidence": rel(STAGE212_PROOF),
            "detail": "Stage213 starts only after the standalone wrapper probe is promoted.",
        },
        {
            "gate": "G2_build_compile",
            "status": "PASS" if all(v == 0 for v in build_rcs.values()) and all(v == 0 for v in compile_rcs.values()) else "FAIL",
            "metric": "build_rcs;compile_rcs",
            "value": f"{build_rcs};{compile_rcs}",
            "evidence": rel(OUT),
            "detail": "Build and compile baseline and wrapper variants for r=2 and r=4.",
        },
        {
            "gate": "G3_correctness",
            "status": "PASS" if correct_ok else "FAIL",
            "metric": "all_mismatches",
            "value": "0" if correct_ok else "nonzero_or_missing",
            "evidence": rel(CORRECTNESS_CSV),
            "detail": "Each integrated wrapper run must match the row-loop split reference.",
        },
        {
            "gate": "G4_component_and_combined_timing",
            "status": "PASS_PROMOTE" if combined_min >= PROMOTE_THRESHOLD else "PASS_COMPONENT_ONLY",
            "metric": "min_dft_rows_speedup;min_combined_speedup",
            "value": f"{dft_min:.9f};{combined_min:.9f}",
            "evidence": rel(COMPARISON_CSV),
            "detail": "Full SAB A/B is allowed only if combined_current improves for both r=2 and r=4.",
        },
        {
            "gate": "G5_stage213_decision",
            "status": decision,
            "metric": "decision",
            "value": decision,
            "evidence": rel(PROOF_CSV),
            "detail": "Stage213 decides whether to run complete-SAB A/B for the wrapper path.",
        },
    ]


def next_rows(decision: str) -> List[Dict[str, str]]:
    promoted = decision == "PASS_STAGE213_DFT_WRAPPER_PROMOTE_FULL_SAB_AB"
    return [
        {
            "priority": "P0",
            "route": "stage214_full_sab_ab_dft_wrapper",
            "entry_condition": "Stage213 integrated combined_current gate is positive for r=2 and r=4.",
            "gate": "Run complete SAB T_bootstrap/r A/B with scalar baseline, current PVW, and wrapper PVW.",
            "status": "ready" if promoted else "not_ready",
            "evidence": rel(PROOF_CSV),
        },
        {
            "priority": "P1",
            "route": "native_counter_refresh",
            "entry_condition": "Hardware counter attribution is needed before paper-level microarchitectural claims.",
            "gate": "Collect load/store/FMA/cycle/cache counters on native Linux.",
            "status": "blocked_locally",
            "evidence": rel(ENV_CSV),
        },
    ]


def report_text(decision: str, agg: List[Dict[str, str]], comparison: List[Dict[str, str]], correct_rows: List[Dict[str, str]], gates: List[Dict[str, str]], queue: List[Dict[str, str]]) -> str:
    return f"""# Stage213 DFT Wrapper Integration Preflight

Decision: `{decision}`.

Stage213 integrates the Stage212 multirow reverse-DFT wrapper behind
`MAT_TRGSW_MULTIROW_DFT_WRAPPER` and compares it against the baseline exact
MAT-EP split probe. This is still not a complete-SAB speedup claim. It is the
gate that decides whether complete-SAB A/B is worth running.

## Correctness

{table(correct_rows, ["implementation", "r", "variant", "sample", "mismatches", "max_gap", "status"])}

## Aggregate Timing

{table(agg, ["implementation", "r", "variant", "samples", "mean_per_call_us", "min_per_call_us", "max_per_call_us"])}

## Comparison

{table(comparison, ["r", "variant", "baseline_mean_per_call_us", "wrapper_mean_per_call_us", "speedup_vs_baseline", "decision"])}

## Gates

{table(gates, ["gate", "status", "metric", "value", "evidence", "detail"])}

## Next Queue

{table(queue, ["priority", "route", "entry_condition", "gate", "status", "evidence"])}
"""


def small_doc(title: str, decision: str, body: str) -> str:
    return f"# {title}\n\nDecision: `{decision}`.\n\n{body}\n"


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
        "## Stage 213: DFT Wrapper Integration Preflight",
        f"""
## Stage 213: DFT Wrapper Integration Preflight

Goal:

```text
Integrate the Stage212 multirow reverse-DFT wrapper behind an explicit flag
and decide whether complete-SAB A/B is authorized.
```

Status:

```text
Completed. Stage213 records {decision}. The scalar/default path remains
unchanged because `MAT_TRGSW_MULTIROW_DFT_WRAPPER` is default-off.
```
""",
    )
    append_once(
        GOAL,
        "Stage213 DFT wrapper integration preflight",
        f"""

## Stage213 DFT wrapper integration preflight

At commit `{head}`, Stage213 records `{decision}` for the default-off MAT-EP
multirow DFT wrapper integration preflight.
""",
    )
    append_once(
        CURRENT_GOAL,
        "Stage213 DFT wrapper integration preflight",
        f"""

### Stage213 DFT wrapper integration preflight

`{decision}` moves the loop from standalone backend evidence to guarded MAT-EP
integration evidence without claiming complete SAB speedup yet.
""",
    )
    append_once(
        HYPOTHESES,
        "H10_stage213_dft_wrapper_integration_preflight",
        f"""

H10_stage213_dft_wrapper_integration_preflight:
  status: guarded_integration_preflight_recorded
  evidence:
    - repro/stage213_dft_wrapper_integration_preflight/comparison.csv
    - repro/stage213_dft_wrapper_integration_preflight/proof_gate.csv
    - docs/stage213_dft_wrapper_integration_preflight.md
  conclusion: >
    Stage213 integrates the multirow DFT wrapper behind
    MAT_TRGSW_MULTIROW_DFT_WRAPPER and records decision {decision}.
""",
    )
    append_once(
        RUN_LOG,
        "stage213-dft-wrapper-integration-preflight-001",
        f"""stage213-dft-wrapper-integration-preflight-001,2026-07-04,{head},Stage 213,spqlios_avx512,python scripts/build_stage213_dft_wrapper_integration_preflight.py,flag-only MAT-EP DFT wrapper integration preflight,r=2/4;variants=torus_to_dft_rows/combined_current;runs={RUNS},{decision},"Default path unchanged; complete-SAB claim remains gated.",docs/stage213_dft_wrapper_integration_preflight.md; repro/stage213_dft_wrapper_integration_preflight/comparison.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage213_dft_wrapper_integration_preflight:",
        """

- stage213_dft_wrapper_integration_preflight:
  - `docs/stage213_dft_wrapper_integration_preflight.md`
  - `experiments/stage213_dft_wrapper_integration_preflight_plan.md`
  - `theory_checks/stage213_dft_wrapper_integration_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage213_dft_wrapper_integration_preflight.md`
  - `scripts/build_stage213_dft_wrapper_integration_preflight.py`
  - `repro/stage213_dft_wrapper_integration_preflight/`
""",
    )
    append_once(
        CHECKLIST,
        "Stage213 DFT wrapper integration preflight",
        f"""
- [x] Stage213 DFT wrapper integration preflight records guarded integration
  correctness, split timing, and next queue. Decision: `{decision}`.
""",
    )


def main() -> None:
    if not STAGE212_PROOF.exists():
        raise SystemExit(f"missing Stage212 proof: {STAGE212_PROOF}")
    OUT.mkdir(parents=True, exist_ok=True)
    write_c_source()
    record_environment()

    build_rcs: Dict[str, int] = {}
    compile_rcs: Dict[Tuple[str, int], int] = {}
    run_rcs: List[int] = []
    run_rows: List[Dict[str, str]] = []
    correct_rows: List[Dict[str, str]] = []

    for implementation in IMPLEMENTATIONS:
        build_rcs[implementation] = build_static(implementation)
        for r in R_VALUES:
            compile_rcs[(implementation, r)] = compile_probe(implementation, r) if build_rcs[implementation] == 0 else 1
            if compile_rcs[(implementation, r)] != 0:
                continue
            for variant in VARIANTS:
                for sample in range(RUNS):
                    rc = run_one(implementation, r, variant, sample)
                    run_rcs.append(rc)
                    rows, corr = parse_run_log(implementation, r, variant, sample)
                    run_rows.extend(rows)
                    correct_rows.extend(corr)
            bin_path = OUT / f"stage213_{implementation}_r{r}_probe"
            if bin_path.exists():
                bin_path.unlink()

    write_csv(RUN_CSV, run_rows, ["implementation", "r", "variant", "sample", "N", "items", "reps", "calls", "total_ns", "per_call_us", "sink", "status", "evidence"])
    write_csv(CORRECTNESS_CSV, correct_rows, ["implementation", "r", "variant", "sample", "check", "mismatches", "max_gap", "status", "evidence"])
    agg = aggregate(run_rows) if run_rows else []
    comparison = compare(agg) if agg else []
    decision = decide(build_rcs, compile_rcs, run_rcs, correct_rows, comparison)
    gates = proof_rows(decision, build_rcs, compile_rcs, run_rcs, correct_rows, comparison)
    queue = next_rows(decision)
    write_csv(PROOF_CSV, gates, ["gate", "status", "metric", "value", "evidence", "detail"])
    write_csv(NEXT_CSV, queue, ["priority", "route", "entry_condition", "gate", "status", "evidence"])

    text = report_text(decision, agg, comparison, correct_rows, gates, queue)
    write_text(DOC, text)
    write_text(REPORT, text)
    write_text(PLAN, small_doc("Stage213 DFT Wrapper Integration Preflight Plan", decision, "Run baseline and wrapper MAT-EP split probes for r=2/r=4. Promote only if correctness passes and combined_current improves for both r values."))
    write_text(THEORY, small_doc("Stage213 DFT Wrapper Integration Model", decision, "The wrapper can only improve complete SAB if the MAT-EP combined path retains enough of the Stage212 DFT-row gain after decomposition and addmul costs. Therefore complete-SAB A/B remains a separate Stage214 gate."))
    write_text(VARIANT, small_doc("Stage213 DFT Wrapper Integration Variant", decision, "The variant is `MAT_TRGSW_MULTIROW_DFT_WRAPPER=true`, default-off. It routes exact MAT-EP row conversion through `polynomial_torus_to_DFT_array`."))
    write_text(REPRO_COMMANDS, "# Stage213 Reproduction Commands\n\n```bash\npython3 scripts/build_stage213_dft_wrapper_integration_preflight.py\n```\n")
    write_csv(
        ARTIFACT_CSV,
        artifact_rows(
            [
                DOC,
                PLAN,
                THEORY,
                VARIANT,
                C_SOURCE,
                ENV_CSV,
                OUT / "environment.log",
                RUN_CSV,
                CORRECTNESS_CSV,
                AGG_CSV,
                COMPARISON_CSV,
                PROOF_CSV,
                NEXT_CSV,
                REPORT,
                REPRO_COMMANDS,
                Path(__file__),
            ]
            + sorted(OUT.glob("*.log"))
        ),
        ["path", "exists", "sha256", "bytes"],
    )
    update_tracking(decision)
    print(decision)
    for row in comparison:
        print("COMPARE213," + ",".join([row["r"], row["variant"], row["speedup_vs_baseline"], row["decision"]]))


if __name__ == "__main__":
    main()
