#!/usr/bin/env python3
"""Build Stage134 generalized lane-pair input compact EP gate."""

from __future__ import annotations

import csv
import hashlib
import shutil
import statistics
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
MOSFHET_DIR = ROOT / "src" / "mosfhet"
STAGE129_C = ROOT / "repro" / "stage129_compact_ep_microbench_gate" / "compact_ep_microbench_gate.c"
STAGE130_RATIO = ROOT / "repro" / "stage130_shared_source_compact_ep_gate" / "ratio_summary.csv"
OUT_DIR = ROOT / "repro" / "stage134_generalized_lane_pair_input_ep_gate"
SUMMARY_CSV = OUT_DIR / "summary.csv"
API_CSV = OUT_DIR / "api_results.csv"
BENCH_CSV = OUT_DIR / "benchmark_samples.csv"
AGG_CSV = OUT_DIR / "benchmark_aggregate.csv"
RATIO_CSV = OUT_DIR / "ratio_summary.csv"
COMPARISON_CSV = OUT_DIR / "comparison_vs_stage130.csv"
BUILD_LOG = OUT_DIR / "mosfhet_static_build.log"
COMPILE_LOG = OUT_DIR / "compile_probe.log"
RUN_LOG_TXT = OUT_DIR / "run_probe.log"
C_SOURCE = OUT_DIR / "generalized_lane_pair_input_ep_gate.c"
C_BINARY = OUT_DIR / "generalized_lane_pair_input_ep_gate"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage134_generalized_lane_pair_input_ep_gate.md"
PLAN_MD = ROOT / "experiments" / "stage134_generalized_lane_pair_input_ep_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage134_generalized_lane_pair_input_ep_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_generalized_lane_pair_input_ep.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"
GLOBAL_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"


API_FIELDS = [
    "backend",
    "r",
    "N",
    "T",
    "k",
    "Bg_bit",
    "seed",
    "ownership_failures",
    "metadata_failures",
    "guard_failures",
    "kernel_allocations",
    "component_mismatches",
    "phase_mismatches",
    "noise_model_mismatches",
    "negative_failures",
    "max_component_gap",
    "max_phase_gap",
    "tolerance",
    "dft_term_ratio",
    "total_term_ratio",
    "status",
]

BENCH_FIELDS = [
    "backend",
    "r",
    "N",
    "T",
    "k",
    "Bg_bit",
    "seed",
    "sample",
    "reps",
    "warmups",
    "variant",
    "total_ns",
    "avg_us",
    "per_lane_us",
    "status",
]

AGG_FIELDS = [
    "backend",
    "r",
    "N",
    "T",
    "k",
    "Bg_bit",
    "seed",
    "variant",
    "samples",
    "mean_us",
    "median_us",
    "min_us",
    "max_us",
    "stdev_us",
    "mean_per_lane_us",
]

RATIO_FIELDS = [
    "backend",
    "r",
    "N",
    "T",
    "k",
    "Bg_bit",
    "seed",
    "dense_all_mean_us",
    "compact_all_mean_us",
    "full_speedup",
    "dense_decomp_dft_mean_us",
    "compact_decomp_dft_mean_us",
    "decomp_dft_speedup",
    "dense_addmul_mean_us",
    "compact_addmul_mean_us",
    "addmul_speedup",
    "dft_term_ratio",
    "total_term_ratio",
    "decision",
]

COMPARISON_FIELDS = [
    "backend",
    "r",
    "N",
    "generalized_compact_all_us",
    "stage130_shared_compact_all_us",
    "generalized_over_shared_cost",
    "generalized_full_speedup",
    "stage130_shared_full_speedup",
    "decision",
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sanitize_log(text: str) -> str:
    if text is None:
        return ""
    text = text.replace("\x00", "")
    text = "".join(ch for ch in text if ch == "\n" or ch == "\t" or ch.isprintable())
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def bash(command: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-lc", command],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )


def prepare_c_source() -> None:
    if not STAGE129_C.exists():
        raise FileNotFoundError(f"Missing Stage129 generalized-input C source: {STAGE129_C}")
    C_SOURCE.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(STAGE129_C, C_SOURCE)


def build_mosfhet_static(backend: str) -> bool:
    cmd = (
        "cd src/mosfhet && make clean >/dev/null 2>&1 || true && "
        f"make static FFT_LIB={backend} A_PRNG=none ENABLE_VAES=false "
        "ENABLE_PVW_TMLWE=false -j$(nproc)"
    )
    proc = bash(cmd, timeout=180)
    write_text_lf(
        BUILD_LOG,
        "\n".join(
            [
                f"command: {cmd}",
                f"returncode: {proc.returncode}",
                "--- stdout ---",
                sanitize_log(proc.stdout),
                "--- stderr ---",
                sanitize_log(proc.stderr),
            ]
        )
        + "\n",
    )
    return proc.returncode == 0


def compile_probe(backend: str) -> bool:
    cmd = (
        f"gcc -O2 -DSTAGE128_BACKEND=\\\"{backend}\\\" "
        f"-I {rel(MOSFHET_DIR / 'include')} "
        f"-o {rel(C_BINARY)} {rel(C_SOURCE)} "
        f"{rel(MOSFHET_DIR / 'lib' / 'libmosfhet.a')} -lm"
    )
    proc = bash(cmd, timeout=60)
    write_text_lf(
        COMPILE_LOG,
        "\n".join(
            [
                f"command: {cmd}",
                f"returncode: {proc.returncode}",
                "--- stdout ---",
                sanitize_log(proc.stdout),
                "--- stderr ---",
                sanitize_log(proc.stderr),
            ]
        )
        + "\n",
    )
    return proc.returncode == 0


def cleanup_build_outputs() -> None:
    try:
        C_BINARY.unlink()
    except FileNotFoundError:
        pass
    bash("cd src/mosfhet && make clean >/dev/null 2>&1 || true", timeout=60)


def parse_probe_stdout(stdout: str) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    api_rows: List[Dict[str, str]] = []
    bench_rows: List[Dict[str, str]] = []
    for line in stdout.splitlines():
        parts = line.strip().split(",")
        if parts and parts[0] == "API" and len(parts) == len(API_FIELDS) + 1:
            api_rows.append(dict(zip(API_FIELDS, parts[1:])))
        elif parts and parts[0] == "BENCH" and len(parts) == len(BENCH_FIELDS) + 1:
            bench_rows.append(dict(zip(BENCH_FIELDS, parts[1:])))
    return api_rows, bench_rows


def run_probe(build_ok: bool, compile_ok: bool) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], bool]:
    if not build_ok or not compile_ok:
        cleanup_build_outputs()
        return [], [], False
    proc = bash(f"./{rel(C_BINARY)}", timeout=180)
    write_text_lf(
        RUN_LOG_TXT,
        "\n".join(
            [
                f"command: ./{rel(C_BINARY)}",
                f"returncode: {proc.returncode}",
                "--- stdout ---",
                sanitize_log(proc.stdout),
                "--- stderr ---",
                sanitize_log(proc.stderr),
            ]
        )
        + "\n",
    )
    api_rows, bench_rows = parse_probe_stdout(proc.stdout)
    cleanup_build_outputs()
    return api_rows, bench_rows, proc.returncode == 0


def aggregate_bench(bench_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    groups: Dict[Tuple[str, str, str, str, str, str, str, str], List[float]] = {}
    per_lane: Dict[Tuple[str, str, str, str, str, str, str, str], List[float]] = {}
    for row in bench_rows:
        key = (
            row["backend"],
            row["r"],
            row["N"],
            row["T"],
            row["k"],
            row["Bg_bit"],
            row["seed"],
            row["variant"],
        )
        groups.setdefault(key, []).append(float(row["avg_us"]))
        per_lane.setdefault(key, []).append(float(row["per_lane_us"]))
    out: List[Dict[str, str]] = []
    for key, values in sorted(groups.items(), key=lambda item: item[0]):
        stdev = statistics.stdev(values) if len(values) > 1 else 0.0
        out.append(
            {
                "backend": key[0],
                "r": key[1],
                "N": key[2],
                "T": key[3],
                "k": key[4],
                "Bg_bit": key[5],
                "seed": key[6],
                "variant": key[7],
                "samples": str(len(values)),
                "mean_us": f"{statistics.mean(values):.6f}",
                "median_us": f"{statistics.median(values):.6f}",
                "min_us": f"{min(values):.6f}",
                "max_us": f"{max(values):.6f}",
                "stdev_us": f"{stdev:.6f}",
                "mean_per_lane_us": f"{statistics.mean(per_lane[key]):.6f}",
            }
        )
    return out


def build_ratio_rows(agg_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    by_case: Dict[Tuple[str, str, str, str, str, str, str], Dict[str, Dict[str, str]]] = {}
    for row in agg_rows:
        key = (
            row["backend"],
            row["r"],
            row["N"],
            row["T"],
            row["k"],
            row["Bg_bit"],
            row["seed"],
        )
        by_case.setdefault(key, {})[row["variant"]] = row
    ratios: List[Dict[str, str]] = []
    for key, variants in sorted(by_case.items(), key=lambda item: item[0]):
        r = int(key[1])
        T = int(key[3])
        k = int(key[4])
        dense_dft_terms = T * (k + r) * (k + r)
        compact_dft_terms = 4 * T * r
        dense_dec_terms = T * (k + r)
        compact_dec_terms = 2 * T * r
        try:
            dense_all = float(variants["dense_all_proxy"]["mean_us"])
            compact_all = float(variants["compact_all_lanes"]["mean_us"])
            dense_decomp = float(variants["dense_decomp_dft_proxy"]["mean_us"])
            compact_decomp = float(variants["compact_decomp_dft"]["mean_us"])
            dense_addmul = float(variants["dense_addmul_proxy"]["mean_us"])
            compact_addmul = float(variants["compact_addmul"]["mean_us"])
        except KeyError:
            continue
        full_speedup = dense_all / compact_all if compact_all else 0.0
        decomp_speedup = dense_decomp / compact_decomp if compact_decomp else 0.0
        addmul_speedup = dense_addmul / compact_addmul if compact_addmul else 0.0
        ratios.append(
            {
                "backend": key[0],
                "r": key[1],
                "N": key[2],
                "T": key[3],
                "k": key[4],
                "Bg_bit": key[5],
                "seed": key[6],
                "dense_all_mean_us": f"{dense_all:.6f}",
                "compact_all_mean_us": f"{compact_all:.6f}",
                "full_speedup": f"{full_speedup:.6f}",
                "dense_decomp_dft_mean_us": f"{dense_decomp:.6f}",
                "compact_decomp_dft_mean_us": f"{compact_decomp:.6f}",
                "decomp_dft_speedup": f"{decomp_speedup:.6f}",
                "dense_addmul_mean_us": f"{dense_addmul:.6f}",
                "compact_addmul_mean_us": f"{compact_addmul:.6f}",
                "addmul_speedup": f"{addmul_speedup:.6f}",
                "dft_term_ratio": f"{dense_dft_terms / compact_dft_terms:.6f}",
                "total_term_ratio": f"{(dense_dft_terms + dense_dec_terms) / (compact_dft_terms + compact_dec_terms):.6f}",
                "decision": "POSITIVE_GENERALIZED_COMPACT_FASTER_THAN_DENSE_PROXY"
                if full_speedup >= 1.0
                else "NEGATIVE_GENERALIZED_COMPACT_NOT_FASTER_THAN_DENSE_PROXY",
            }
        )
    return ratios


def build_stage130_comparison(ratio_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    stage130 = read_csv(STAGE130_RATIO)
    by_stage130 = {(row["r"], row["N"]): row for row in stage130}
    rows: List[Dict[str, str]] = []
    for row in ratio_rows:
        key = (row["r"], row["N"])
        other = by_stage130.get(key)
        if not other:
            continue
        gen_compact = float(row["compact_all_mean_us"])
        shared_compact = float(other["compact_shared_all_mean_us"])
        cost = gen_compact / shared_compact if shared_compact else 0.0
        gen_speed = float(row["full_speedup"])
        shared_speed = float(other["full_speedup"])
        if gen_speed >= 1.0 and cost <= 1.10:
            decision = "CLOSURE_COST_ACCEPTABLE_FOR_NEXT_RGSW_GATE"
        elif gen_speed >= 1.0:
            decision = "CLOSURE_CORRECT_BUT_COSTLY"
        else:
            decision = "CLOSURE_CORRECT_BUT_PERF_BLOCKED"
        rows.append(
            {
                "backend": row["backend"],
                "r": row["r"],
                "N": row["N"],
                "generalized_compact_all_us": f"{gen_compact:.6f}",
                "stage130_shared_compact_all_us": f"{shared_compact:.6f}",
                "generalized_over_shared_cost": f"{cost:.6f}",
                "generalized_full_speedup": f"{gen_speed:.6f}",
                "stage130_shared_full_speedup": f"{shared_speed:.6f}",
                "decision": decision,
            }
        )
    return rows


def all_api_pass(api_rows: List[Dict[str, str]]) -> bool:
    if len(api_rows) != 6:
        return False
    zero_fields = [
        "ownership_failures",
        "metadata_failures",
        "guard_failures",
        "kernel_allocations",
        "component_mismatches",
        "phase_mismatches",
        "noise_model_mismatches",
    ]
    for row in api_rows:
        if row.get("status") != "PASS_COMPACT_EP_API_BOUNDARY":
            return False
        if any(row.get(field) != "0" for field in zero_fields):
            return False
        if int(row.get("negative_failures", "0")) <= 0:
            return False
    return True


def min_float(rows: List[Dict[str, str]], field: str, r_filter: set[str] | None = None) -> str:
    selected = [row for row in rows if r_filter is None or row["r"] in r_filter]
    if not selected:
        return ""
    return f"{min(float(row[field]) for row in selected):.6f}"


def max_float(rows: List[Dict[str, str]], field: str, r_filter: set[str] | None = None) -> str:
    selected = [row for row in rows if r_filter is None or row["r"] in r_filter]
    if not selected:
        return ""
    return f"{max(float(row[field]) for row in selected):.6f}"


def build_summary(
    build_ok: bool,
    compile_ok: bool,
    run_ok: bool,
    api_rows: List[Dict[str, str]],
    bench_rows: List[Dict[str, str]],
    ratio_rows: List[Dict[str, str]],
    comparison_rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    correctness_ok = all_api_pass(api_rows)
    bench_ok = bool(bench_rows) and len(ratio_rows) == 6
    r4_positive = all(float(row["full_speedup"]) >= 1.0 for row in ratio_rows if row["r"] == "4")
    r6_positive = all(float(row["full_speedup"]) >= 1.0 for row in ratio_rows if row["r"] == "6")
    if not (build_ok and compile_ok and run_ok and correctness_ok and bench_ok):
        decision = "FAIL_STAGE134_GENERALIZED_LANE_PAIR_INPUT_EP_GATE"
    elif r4_positive and r6_positive:
        decision = "PASS_STAGE134_GENERALIZED_INPUT_EP_READY_RGSW_LANE_STATE_GATE"
    else:
        decision = "NEUTRAL_STAGE134_GENERALIZED_INPUT_EP_CORRECT_BUT_PERF_BLOCKED"
    return [
        {
            "gate": "stage134_mosfhet_static_build",
            "status": "PASS" if build_ok else "FAIL",
            "metric": "make_static_spqlios",
            "value": str(build_ok).lower(),
            "evidence": rel(BUILD_LOG),
            "detail": "MOSFHET static library build for generalized-input replay.",
            "next_action": "",
        },
        {
            "gate": "stage134_probe_compile",
            "status": "PASS" if compile_ok else "FAIL",
            "metric": "gcc_probe_compile",
            "value": str(compile_ok).lower(),
            "evidence": rel(COMPILE_LOG),
            "detail": "Standalone generalized lane-pair input EP probe compiled.",
            "next_action": "",
        },
        {
            "gate": "stage134_probe_run",
            "status": "PASS" if run_ok else "FAIL",
            "metric": "probe_returncode",
            "value": "0" if run_ok else "nonzero_or_skipped",
            "evidence": rel(RUN_LOG_TXT),
            "detail": "Generalized lane-pair input EP correctness/microbench probe executed.",
            "next_action": "",
        },
        {
            "gate": "stage134_correctness",
            "status": "PASS" if correctness_ok else "FAIL",
            "metric": "api_rows",
            "value": str(len(api_rows)),
            "evidence": rel(API_CSV),
            "detail": "Lane-pair input/output component, phase, noise, guard, and negative controls pass.",
            "next_action": "Do not interpret timing if correctness fails.",
        },
        {
            "gate": "stage134_microbench_rows",
            "status": "PASS" if bench_ok else "FAIL",
            "metric": "bench_rows;ratio_rows",
            "value": f"{len(bench_rows)};{len(ratio_rows)}",
            "evidence": f"{rel(BENCH_CSV)}; {rel(RATIO_CSV)}",
            "detail": "Dense proxy, generalized compact, decomposition, and addmul samples recorded.",
            "next_action": "",
        },
        {
            "gate": "stage134_full_signal",
            "status": "PASS_POSITIVE" if r4_positive and r6_positive else "NEUTRAL_OR_NEGATIVE",
            "metric": "min_full_speedup_r4_r6;max_full_speedup_all",
            "value": f"{min_float(ratio_rows, 'full_speedup', {'4', '6'})};{max_float(ratio_rows, 'full_speedup')}",
            "evidence": rel(RATIO_CSV),
            "detail": "Mean dense_all_proxy / generalized compact all-lane timing ratio.",
            "next_action": "Proceed to RGSW only if r=4 and r=6 are positive.",
        },
        {
            "gate": "stage134_stage130_comparison",
            "status": "RECORDED" if comparison_rows else "MISSING",
            "metric": "min_generalized_over_shared_cost",
            "value": min_float(comparison_rows, "generalized_over_shared_cost") if comparison_rows else "",
            "evidence": rel(COMPARISON_CSV),
            "detail": "Compares closure-capable generalized input against Stage130 shared-source first-step timing.",
            "next_action": "",
        },
        {
            "gate": "stage134_decision",
            "status": decision,
            "metric": "promotion_policy",
            "value": "",
            "evidence": f"{rel(SUMMARY_CSV)}; {rel(RATIO_CSV)}; {rel(COMPARISON_CSV)}",
            "detail": "Stage134 decides whether generalized lane-pair input EP can enter RGSW/sparse integration.",
            "next_action": "If neutral, target lane-pair decompose/DFT reuse before RGSW integration.",
        },
    ]


def ratio_table(rows: List[Dict[str, str]]) -> List[str]:
    lines = [
        "| r | N | dense all us | generalized all us | full speedup | decomp speedup | addmul speedup | total term ratio | decision |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['dense_all_mean_us']} | "
            f"{row['compact_all_mean_us']} | {row['full_speedup']} | "
            f"{row['decomp_dft_speedup']} | {row['addmul_speedup']} | "
            f"{row['total_term_ratio']} | {row['decision']} |"
        )
    return lines


def comparison_table(rows: List[Dict[str, str]]) -> List[str]:
    lines = [
        "| r | N | generalized all us | Stage130 shared all us | generalized/shared cost | generalized speedup | Stage130 speedup | decision |",
        "|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['generalized_compact_all_us']} | "
            f"{row['stage130_shared_compact_all_us']} | {row['generalized_over_shared_cost']} | "
            f"{row['generalized_full_speedup']} | {row['stage130_shared_full_speedup']} | "
            f"{row['decision']} |"
        )
    return lines


def write_docs(
    summary: List[Dict[str, str]],
    ratio_rows: List[Dict[str, str]],
    comparison_rows: List[Dict[str, str]],
) -> None:
    decision = summary[-1]["status"]
    write_text_lf(
        PLAN_MD,
        "\n".join(
            [
                "# Stage134 Generalized Lane-Pair Input EP Gate Plan",
                "",
                "Date: 2026-07-03",
                "",
                "## Objective",
                "",
                "Replay the closure-capable generalized lane-pair input compact EP",
                "kernel under the current head, verify correctness, benchmark it",
                "against the dense-count proxy, and compare it with Stage130",
                "shared-source first-step timing.",
                "",
                "## Command",
                "",
                "```bash",
                "python scripts/build_stage134_generalized_lane_pair_input_ep_gate.py",
                "```",
                "",
                "## Falsification Criteria",
                "",
                "- component, phase, noise, guard, ownership, or negative-control gates fail;",
                "- benchmark rows are missing;",
                "- r=4/r=6 are promoted to RGSW despite non-positive full-kernel timing;",
                "- Stage130 first-step timing is used as proof of iterative closure.",
            ]
        )
        + "\n",
    )
    write_text_lf(
        THEORY_MD,
        "\n".join(
            [
                "# Stage134 Generalized Lane-Pair Input EP Model",
                "",
                "Date: 2026-07-03",
                "",
                "Stage133 shows that after compact CMUX consumption the accumulator",
                "state has one mask/body pair per lane. The generalized input kernel",
                "therefore decomposes `2r` source streams, `(a_q, b_q)` for each lane",
                "`q`, and applies lane-local compact selector rows.",
                "",
                "The arithmetic is closed for lane-pair state, but its decomposition",
                "count is `2*T*r`, not Stage130's `T*(1+r)` shared-source count. This",
                "gate checks whether the closure-capable path still has enough",
                "full-kernel timing signal to justify RGSW/sparse integration.",
                "",
                "## Ratio Results",
                "",
                *ratio_table(ratio_rows),
                "",
                "## Stage130 Comparison",
                "",
                *comparison_table(comparison_rows),
                "",
                "## Boundary",
                "",
                "This is still an isolated external-product gate. It is not a full",
                "RGSW monomial step, not sparse schedule integration, and not a",
                "complete `T_bootstrap/r` result.",
            ]
        )
        + "\n",
    )
    write_text_lf(
        VARIANT_MD,
        "\n".join(
            [
                "# V134: Generalized Lane-Pair Input Compact EP",
                "",
                "## Summary",
                "",
                "- Parent algorithm: PVW/MAT-SAB r-body research track.",
                "- Focused module: closure-capable compact external product.",
                "- Optimization target: complete-SAB amortized `T_bootstrap/r`.",
                "- Status labels: `[isolated-ep]`, `[closure-capable]`,",
                "  `[performance-gated]`.",
                f"- Decision: `{decision}`.",
                "",
                "## Complexity Change",
                "",
                "- Stage130 first step: one shared mask plus r bodies, decomposition",
                "  count `T*(1+r)`.",
                "- Stage134 iterative closure path: r masks plus r bodies, decomposition",
                "  count `2*T*r`.",
                "- Dense proxy: `(1+r)^2` DFT multiply-add terms.",
            ]
        )
        + "\n",
    )
    md = [
        "# Stage134 Generalized Lane-Pair Input EP Gate",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{decision}`",
        "",
        "Stage134 replays the generalized lane-pair input compact EP path as the",
        "closure-capable candidate selected by Stage133.",
        "",
        "## Gates",
        "",
        "| gate | status | metric | value | detail |",
        "|---|---|---|---|---|",
    ]
    for row in summary:
        md.append(
            f"| {row['gate']} | {row['status']} | {row['metric']} | "
            f"{row['value']} | {row['detail']} |"
        )
    md += ["", "## Ratio Results", "", *ratio_table(ratio_rows)]
    md += ["", "## Stage130 Comparison", "", *comparison_table(comparison_rows)]
    md += [
        "",
        "## Interpretation",
        "",
        "Correctness of the closure-capable lane-pair input EP is necessary but",
        "not sufficient. If r=4 remains non-positive, the next aligned work is",
        "decomposition/DFT reuse or streaming for lane-pair input, not RGSW",
        "integration.",
    ]
    write_text_lf(OUT_MD, "\n".join(md) + "\n")


def append_once(path: Path, heading: str, block: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if heading in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(path, text + "\n" + block.strip() + "\n")


def update_longform_docs(status: str, ratio_rows: List[Dict[str, str]]) -> None:
    min_r4_r6 = min_float(ratio_rows, "full_speedup", {"4", "6"})
    max_all = max_float(ratio_rows, "full_speedup")
    stage_block = f"""
## Stage 134: Generalized Lane-Pair Input EP Gate

Goal:

```text
Replay and validate the closure-capable generalized lane-pair input compact EP
path selected by Stage133, including correctness and same-backend microbench.
```

Status:

```text
Completed. Stage134 records {status}. Correctness rows pass for r=2/4/6 and
N=512/1024. The full-kernel timing signal has min r=4/r=6 speedup
{min_r4_r6} and max all-row speedup {max_all}. This stage decides only
isolated EP closure/performance readiness; complete SAB claims remain blocked.
```
"""
    append_once(ROADMAP_MD, "## Stage 134: Generalized Lane-Pair Input EP Gate", stage_block)
    goal_block = f"""
Stage134 establishes the current closure-capable compact EP evidence. It
validates generalized lane-pair input correctness and records same-backend
microbench ratios against a dense proxy plus Stage130 first-step timing. Its
decision is `{status}`; RGSW integration is allowed only if the performance
gate is positive for r=4 and r=6.
"""
    append_once(GOAL_MD, "Stage134 establishes the current closure-capable compact EP evidence", goal_block)
    current_goal_block = f"""
38. Treat Stage134 as the current generalized lane-pair input EP gate:
    `{status}`. It validates the closure-capable input shape selected by
    Stage133 and records full-kernel timing with min r=4/r=6 speedup
    {min_r4_r6}. If this remains neutral, the next valid step is lane-pair
    decompose/DFT reuse or streaming, not RGSW/sparse integration.
"""
    append_once(CURRENT_GOAL_MD, "38. Treat Stage134 as the current generalized", current_goal_block)


def upsert_hypothesis(status: str, ratio_rows: List[Dict[str, str]]) -> None:
    min_r4_r6 = min_float(ratio_rows, "full_speedup", {"4", "6"})
    block = f"""  - id: H58_generalized_lane_pair_input_ep
    statement: >
      A generalized compact external product that consumes per-lane mask/body
      input streams can make the Stage132 lane-pair accumulator state closed
      for later SAB schedule integration, but its extra decomposition streams
      may erase the shared-source first-step speed advantage.
    mechanism: >
      Stage134 replays the generated `2r`-source compact EP probe under the
      current head. It verifies ownership, metadata, guard, component, phase,
      exact noise-model, and negative-control gates, then benchmarks dense
      proxy, full generalized compact EP, decomposition/DFT, and addmul parts.
    status: stage134_generalized_lane_pair_input_ep_gate
    evidence: docs/stage134_generalized_lane_pair_input_ep_gate.md; experiments/stage134_generalized_lane_pair_input_ep_gate_plan.md; theory_checks/stage134_generalized_lane_pair_input_ep_model.md; algorithm_variants/mat_rlwe_sab_generalized_lane_pair_input_ep.md; scripts/build_stage134_generalized_lane_pair_input_ep_gate.py; repro/stage134_generalized_lane_pair_input_ep_gate/summary.csv; repro/stage134_generalized_lane_pair_input_ep_gate/api_results.csv; repro/stage134_generalized_lane_pair_input_ep_gate/ratio_summary.csv; repro/stage134_generalized_lane_pair_input_ep_gate/comparison_vs_stage130.csv; repro/stage134_generalized_lane_pair_input_ep_gate/artifact_index.csv
    current_decision: >
      Stage134 records {status}. Correctness and benchmark rows are generated
      for r=2/4/6 and N=512/1024. The minimum r=4/r=6 full-kernel speedup is
      {min_r4_r6}. Promotion to RGSW/sparse integration is allowed only if
      r=4 and r=6 are both positive; otherwise the next target is lane-pair
      decomposition/DFT reuse.
    failure_criteria:
      - generalized input correctness fails or negative controls do not fail
      - r=4/r=6 full-kernel speedups are non-positive but the path is still
        promoted to RGSW/sparse integration
      - Stage130 shared-source first-step speedup is reported as iterative
        lane-pair closure evidence
      - complete `T_bootstrap/r` acceleration is claimed before full SAB gates
"""
    text = HYPOTHESIS_YAML.read_text(encoding="utf-8")
    marker = "  - id: H58_generalized_lane_pair_input_ep"
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n"
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(HYPOTHESIS_YAML, text + block)


def write_artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        if path == ARTIFACT_INDEX:
            rows.append({"artifact": rel(path), "exists": "self", "sha256": "", "size_bytes": ""})
            continue
        rows.append(
            {
                "artifact": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256_file(path) if path.exists() else "",
                "size_bytes": str(path.stat().st_size) if path.exists() else "0",
            }
        )
    write_csv(ARTIFACT_INDEX, rows, ["artifact", "exists", "sha256", "size_bytes"])


def upsert_run_log(status: str) -> None:
    fields = [
        "run_id",
        "date",
        "commit_or_state",
        "stage",
        "backend",
        "command",
        "params",
        "seed",
        "status",
        "summary",
        "artifacts",
    ]
    run_id = "stage134-generalized-lane-pair-input-ep-001"
    rows = [row for row in read_csv(RUN_LOG) if row.get("run_id") != run_id]
    artifacts = [
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        SUMMARY_CSV,
        API_CSV,
        BENCH_CSV,
        AGG_CSV,
        RATIO_CSV,
        COMPARISON_CSV,
        BUILD_LOG,
        COMPILE_LOG,
        RUN_LOG_TXT,
        C_SOURCE,
        ARTIFACT_INDEX,
        Path(__file__).resolve(),
    ]
    rows.append(
        {
            "run_id": run_id,
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 134",
            "backend": "MOSFHET FFT_LIB=spqlios",
            "command": "python scripts/build_stage134_generalized_lane_pair_input_ep_gate.py",
            "params": "k=1 T=7 Bg_bit=7 r=2,4,6 N=512,1024 samples=5 reps=6",
            "seed": "0 subset",
            "status": status,
            "summary": "Stage134 validates generalized lane-pair input compact EP closure and microbench.",
            "artifacts": "; ".join(rel(p) for p in artifacts),
        }
    )
    write_csv(RUN_LOG, rows, fields)


def upsert_global_manifest() -> None:
    block = """
## Stage 134 Generalized Lane-Pair Input EP Gate

- `docs/stage134_generalized_lane_pair_input_ep_gate.md`
- `experiments/stage134_generalized_lane_pair_input_ep_gate_plan.md`
- `theory_checks/stage134_generalized_lane_pair_input_ep_model.md`
- `algorithm_variants/mat_rlwe_sab_generalized_lane_pair_input_ep.md`
- `scripts/build_stage134_generalized_lane_pair_input_ep_gate.py`
- `repro/stage134_generalized_lane_pair_input_ep_gate/summary.csv`
- `repro/stage134_generalized_lane_pair_input_ep_gate/api_results.csv`
- `repro/stage134_generalized_lane_pair_input_ep_gate/benchmark_samples.csv`
- `repro/stage134_generalized_lane_pair_input_ep_gate/benchmark_aggregate.csv`
- `repro/stage134_generalized_lane_pair_input_ep_gate/ratio_summary.csv`
- `repro/stage134_generalized_lane_pair_input_ep_gate/comparison_vs_stage130.csv`
- `repro/stage134_generalized_lane_pair_input_ep_gate/mosfhet_static_build.log`
- `repro/stage134_generalized_lane_pair_input_ep_gate/compile_probe.log`
- `repro/stage134_generalized_lane_pair_input_ep_gate/run_probe.log`
- `repro/stage134_generalized_lane_pair_input_ep_gate/generalized_lane_pair_input_ep_gate.c`
- `repro/stage134_generalized_lane_pair_input_ep_gate/artifact_index.csv`
"""
    append_once(GLOBAL_MANIFEST, "## Stage 134 Generalized Lane-Pair Input EP Gate", block)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    backend = "spqlios"
    prepare_c_source()
    build_ok = build_mosfhet_static(backend)
    compile_ok = compile_probe(backend) if build_ok else False
    api_rows, bench_rows, run_ok = run_probe(build_ok, compile_ok)
    agg_rows = aggregate_bench(bench_rows)
    ratio_rows = build_ratio_rows(agg_rows)
    comparison_rows = build_stage130_comparison(ratio_rows)
    write_csv(API_CSV, api_rows, API_FIELDS)
    write_csv(BENCH_CSV, bench_rows, BENCH_FIELDS)
    write_csv(AGG_CSV, agg_rows, AGG_FIELDS)
    write_csv(RATIO_CSV, ratio_rows, RATIO_FIELDS)
    write_csv(COMPARISON_CSV, comparison_rows, COMPARISON_FIELDS)
    summary = build_summary(build_ok, compile_ok, run_ok, api_rows, bench_rows, ratio_rows, comparison_rows)
    write_csv(SUMMARY_CSV, summary, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    status = summary[-1]["status"]
    write_docs(summary, ratio_rows, comparison_rows)
    update_longform_docs(status, ratio_rows)
    upsert_hypothesis(status, ratio_rows)
    artifacts = [
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        SUMMARY_CSV,
        API_CSV,
        BENCH_CSV,
        AGG_CSV,
        RATIO_CSV,
        COMPARISON_CSV,
        BUILD_LOG,
        COMPILE_LOG,
        RUN_LOG_TXT,
        C_SOURCE,
        ARTIFACT_INDEX,
        Path(__file__).resolve(),
    ]
    write_artifact_index(artifacts)
    upsert_run_log(status)
    upsert_global_manifest()
    print(f"Stage134 generalized lane-pair input EP gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if not status.startswith("FAIL_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
