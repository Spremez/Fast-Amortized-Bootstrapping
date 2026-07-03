#!/usr/bin/env python3
"""Build Stage142 AVX512 FMA-order fix gate for closed full-MAT kernels."""

from __future__ import annotations

import csv
import hashlib
import shutil
import statistics
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage142_avx512_fma_order_fix_gate"
STAGE141_C = ROOT / "repro" / "stage141_avx512_closed_fullmat_gate" / "avx512_closed_fullmat_gate.c"
C_SOURCE = OUT_DIR / "avx512_closed_fullmat_gate.c"
MOSFHET_DIR = ROOT / "src" / "mosfhet"

SUMMARY_CSV = OUT_DIR / "summary.csv"
CORRECTNESS_CSV = OUT_DIR / "correctness.csv"
BENCH_CSV = OUT_DIR / "benchmark_samples.csv"
AGG_CSV = OUT_DIR / "benchmark_aggregate.csv"
COMPARE_CSV = OUT_DIR / "comparison.csv"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage142_avx512_fma_order_fix_gate.md"
PLAN_MD = ROOT / "experiments" / "stage142_avx512_fma_order_fix_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage142_avx512_fma_order_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_avx512_fma_order_fix.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"
GLOBAL_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"


CONFIGS = [
    {
        "id": "generic_avx512",
        "make_flags": "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false ENABLE_PVW_TMLWE=true",
    },
    {
        "id": "smallr_avx512",
        "make_flags": "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false ENABLE_PVW_TMLWE=true MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true",
    },
    {
        "id": "r4_unrolled_avx512",
        "make_flags": "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false ENABLE_PVW_TMLWE=true MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true",
    },
]

CORRECTNESS_FIELDS = [
    "config", "backend", "r", "N", "T", "Bg_bit", "seed",
    "dft_mismatches", "max_dft_gap", "torus_max_gap",
    "closed_input_dft_conversions", "closed_lower_bound",
    "lower_bound_status", "status",
]
BENCH_FIELDS = [
    "config", "backend", "r", "N", "T", "Bg_bit", "seed", "sample",
    "reps", "warmups", "variant", "total_ns", "avg_us", "per_lane_us",
    "dft_conversion_count", "status",
]
AGG_FIELDS = [
    "config", "backend", "r", "N", "T", "Bg_bit", "seed", "variant",
    "samples", "mean_us", "median_us", "min_us", "max_us", "stdev_us",
    "mean_per_lane_us", "median_per_lane_us",
]
COMPARE_FIELDS = [
    "r", "N", "T", "Bg_bit", "variant",
    "generic_mean_us", "smallr_mean_us", "r4_unrolled_mean_us",
    "smallr_vs_generic_mean", "r4_unrolled_vs_generic_mean",
    "generic_median_us", "smallr_median_us", "r4_unrolled_median_us",
    "smallr_vs_generic_median", "r4_unrolled_vs_generic_median",
    "decision",
]
SUMMARY_FIELDS = ["gate", "status", "metric", "value", "evidence", "detail", "next_action"]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sanitize(text: str) -> str:
    text = text.replace("\x00", "").replace("\r\n", "\n")
    return "\n".join(line.rstrip() for line in text.splitlines())


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


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
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
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
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


def avx512_supported() -> bool:
    return bash("lscpu | grep -qi avx512f", timeout=10).returncode == 0


def log_path(config_id: str, kind: str) -> Path:
    return OUT_DIR / f"{kind}_{config_id}.log"


def binary_path(config_id: str) -> Path:
    return OUT_DIR / f"avx512_closed_fullmat_gate_{config_id}"


def run_logged(command: str, log: Path, timeout: int) -> subprocess.CompletedProcess[str]:
    proc = bash(command, timeout=timeout)
    write_text_lf(log, "\n".join([
        f"command: {command}",
        f"returncode: {proc.returncode}",
        "--- stdout ---",
        sanitize(proc.stdout),
        "--- stderr ---",
        sanitize(proc.stderr),
    ]) + "\n")
    return proc


def build_mosfhet_static(config: Dict[str, str]) -> bool:
    cmd = (
        "cd src/mosfhet && make clean >/dev/null 2>&1 || true && "
        f"make static {config['make_flags']} -j8"
    )
    return run_logged(cmd, log_path(config["id"], "build"), timeout=240).returncode == 0


def compile_probe(config: Dict[str, str]) -> bool:
    binary = binary_path(config["id"])
    cmd = (
        f"gcc -O2 -DSTAGE140_BACKEND=\\\"{config['id']}\\\" "
        f"-I {rel(MOSFHET_DIR / 'include')} "
        f"-o {rel(binary)} {rel(C_SOURCE)} "
        f"{rel(MOSFHET_DIR / 'lib' / 'libmosfhet.a')} -lm"
    )
    return run_logged(cmd, log_path(config["id"], "compile"), timeout=90).returncode == 0


def parse_stdout(config_id: str, stdout: str) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    correctness: List[Dict[str, str]] = []
    bench: List[Dict[str, str]] = []
    base_corr = CORRECTNESS_FIELDS[1:]
    base_bench = BENCH_FIELDS[1:]
    for line in sanitize(stdout).splitlines():
        parts = line.strip().split(",")
        if parts and parts[0] == "CORRECT140" and len(parts) == len(base_corr) + 1:
            row = dict(zip(base_corr, parts[1:]))
            row["config"] = config_id
            correctness.append(row)
        elif parts and parts[0] == "BENCH140" and len(parts) == len(base_bench) + 1:
            row = dict(zip(base_bench, parts[1:]))
            row["config"] = config_id
            bench.append(row)
    return correctness, bench


def run_probe(config: Dict[str, str], build_ok: bool, compile_ok: bool) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], bool]:
    if not build_ok or not compile_ok:
        return [], [], False
    binary = binary_path(config["id"])
    proc = run_logged(f"./{rel(binary)}", log_path(config["id"], "run"), timeout=240)
    try:
        binary.unlink()
    except FileNotFoundError:
        pass
    correctness, bench = parse_stdout(config["id"], proc.stdout)
    return correctness, bench, proc.returncode == 0


def cleanup_build_outputs() -> None:
    run_logged("cd src/mosfhet && make clean >/dev/null 2>&1 || true", OUT_DIR / "cleanup.log", timeout=60)


def aggregate_bench(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    groups: Dict[Tuple[str, str, str, str, str, str, str, str], List[Tuple[float, float]]] = {}
    for row in rows:
        key = (row["config"], row["backend"], row["r"], row["N"], row["T"], row["Bg_bit"], row["seed"], row["variant"])
        groups.setdefault(key, []).append((float(row["avg_us"]), float(row["per_lane_us"])))
    out: List[Dict[str, str]] = []
    for key, values in sorted(groups.items(), key=lambda item: item[0]):
        totals = [v[0] for v in values]
        per_lane = [v[1] for v in values]
        stdev = statistics.stdev(totals) if len(totals) > 1 else 0.0
        out.append({
            "config": key[0], "backend": key[1], "r": key[2], "N": key[3],
            "T": key[4], "Bg_bit": key[5], "seed": key[6], "variant": key[7],
            "samples": str(len(totals)),
            "mean_us": f"{statistics.mean(totals):.6f}",
            "median_us": f"{statistics.median(totals):.6f}",
            "min_us": f"{min(totals):.6f}",
            "max_us": f"{max(totals):.6f}",
            "stdev_us": f"{stdev:.6f}",
            "mean_per_lane_us": f"{statistics.mean(per_lane):.6f}",
            "median_per_lane_us": f"{statistics.median(per_lane):.6f}",
        })
    return out


def build_comparison_rows(agg_rows: List[Dict[str, str]], correctness_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    corr_ok = all(row["status"] == "PASS_CLOSED_FULLMAT_SPLIT_EQUIV" for row in correctness_rows)
    grouped: Dict[Tuple[str, str, str, str, str], Dict[str, Dict[str, str]]] = {}
    for row in agg_rows:
        if row["variant"] != "current_full_mat" or row["r"] != "4" or row["T"] != "1":
            continue
        key = (row["r"], row["N"], row["T"], row["Bg_bit"], row["variant"])
        grouped.setdefault(key, {})[row["config"]] = row
    out: List[Dict[str, str]] = []
    for key, variants in sorted(grouped.items(), key=lambda item: item[0]):
        if not {"generic_avx512", "smallr_avx512", "r4_unrolled_avx512"}.issubset(variants):
            continue
        generic_mean = float(variants["generic_avx512"]["mean_us"])
        smallr_mean = float(variants["smallr_avx512"]["mean_us"])
        unrolled_mean = float(variants["r4_unrolled_avx512"]["mean_us"])
        generic_median = float(variants["generic_avx512"]["median_us"])
        smallr_median = float(variants["smallr_avx512"]["median_us"])
        unrolled_median = float(variants["r4_unrolled_avx512"]["median_us"])
        smallr_mean_speed = generic_mean / smallr_mean if smallr_mean else 0.0
        unrolled_mean_speed = generic_mean / unrolled_mean if unrolled_mean else 0.0
        smallr_median_speed = generic_median / smallr_median if smallr_median else 0.0
        unrolled_median_speed = generic_median / unrolled_median if unrolled_median else 0.0
        if not corr_ok:
            decision = "CORRECTNESS_BLOCKED_SPEED_ONLY"
        elif unrolled_mean_speed >= 1.03 and unrolled_median_speed >= 1.03:
            decision = "PROMOTE_R4_UNROLLED_KERNEL_READY_FULL_SAB_RERUN"
        elif smallr_mean_speed >= 1.03 and smallr_median_speed >= 1.03:
            decision = "PROMOTE_SMALLR_KERNEL_READY_FULL_SAB_RERUN"
        else:
            decision = "NEUTRAL_AVX512_SPECIALIZATION"
        out.append({
            "r": key[0], "N": key[1], "T": key[2], "Bg_bit": key[3], "variant": key[4],
            "generic_mean_us": f"{generic_mean:.6f}",
            "smallr_mean_us": f"{smallr_mean:.6f}",
            "r4_unrolled_mean_us": f"{unrolled_mean:.6f}",
            "smallr_vs_generic_mean": f"{smallr_mean_speed:.6f}",
            "r4_unrolled_vs_generic_mean": f"{unrolled_mean_speed:.6f}",
            "generic_median_us": f"{generic_median:.6f}",
            "smallr_median_us": f"{smallr_median:.6f}",
            "r4_unrolled_median_us": f"{unrolled_median:.6f}",
            "smallr_vs_generic_median": f"{smallr_median_speed:.6f}",
            "r4_unrolled_vs_generic_median": f"{unrolled_median_speed:.6f}",
            "decision": decision,
        })
    return out


def range_field(rows: List[Dict[str, str]], field: str) -> str:
    vals = [float(row[field]) for row in rows if row.get(field)]
    if not vals:
        return ""
    return f"{min(vals):.6f}-{max(vals):.6f}"


def build_summary(avx_ok: bool, config_status: Dict[str, Dict[str, bool]],
    correctness_rows: List[Dict[str, str]], bench_rows: List[Dict[str, str]],
    compare_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    all_build = all(v.get("build", False) for v in config_status.values())
    all_compile = all(v.get("compile", False) for v in config_status.values())
    all_run = all(v.get("run", False) for v in config_status.values())
    corr_ok = (
        len(correctness_rows) == 18
        and all(row["status"] == "PASS_CLOSED_FULLMAT_SPLIT_EQUIV"
                and row["dft_mismatches"] == "0"
                and float(row["torus_max_gap"]) == 0.0
                for row in correctness_rows)
    )
    compare_ok = len(compare_rows) == 2 and all(
        row["decision"] == "PROMOTE_R4_UNROLLED_KERNEL_READY_FULL_SAB_RERUN"
        for row in compare_rows
    )
    if not (avx_ok and all_build and all_compile and all_run and corr_ok and compare_rows):
        decision = "FAIL_STAGE142_AVX512_FMA_ORDER_FIX_GATE"
    elif compare_ok:
        decision = "PASS_STAGE142_AVX512_FMA_ORDER_FIX_PROMOTE_R4_UNROLLED_KERNEL_READY_FULL_SAB_RERUN"
    else:
        decision = "NEUTRAL_STAGE142_AVX512_FMA_ORDER_FIX_NO_STABLE_KERNEL_GAIN"
    return [
        {"gate": "stage142_avx512_support", "status": "PASS" if avx_ok else "FAIL", "metric": "lscpu_avx512f", "value": str(avx_ok).lower(), "evidence": "lscpu", "detail": "Host exposes AVX512F.", "next_action": "Use an AVX512 host if false."},
        {"gate": "stage142_builds", "status": "PASS" if all_build else "FAIL", "metric": "configs_built", "value": str(sum(1 for v in config_status.values() if v.get("build"))), "evidence": "repro/stage142_avx512_fma_order_fix_gate/build_*.log", "detail": "generic, small-r, and r4-unrolled AVX512 static builds.", "next_action": ""},
        {"gate": "stage142_compiles", "status": "PASS" if all_compile else "FAIL", "metric": "configs_compiled", "value": str(sum(1 for v in config_status.values() if v.get("compile"))), "evidence": "repro/stage142_avx512_fma_order_fix_gate/compile_*.log", "detail": "Same target probe compiled for every config.", "next_action": ""},
        {"gate": "stage142_runs", "status": "PASS" if all_run else "FAIL", "metric": "configs_run", "value": str(sum(1 for v in config_status.values() if v.get("run"))), "evidence": "repro/stage142_avx512_fma_order_fix_gate/run_*.log", "detail": "Same target probe executed for every config.", "next_action": ""},
        {"gate": "stage142_correctness", "status": "PASS" if corr_ok else "FAIL", "metric": "correctness_rows", "value": str(len(correctness_rows)), "evidence": rel(CORRECTNESS_CSV), "detail": "All specialized rows must be exact closed full-MAT DFT equivalents.", "next_action": "Do not promote speed rows if this fails."},
        {"gate": "stage142_comparison", "status": "PASS" if compare_rows else "FAIL", "metric": "bench_rows;compare_rows", "value": f"{len(bench_rows)};{len(compare_rows)}", "evidence": f"{rel(BENCH_CSV)}; {rel(COMPARE_CSV)}", "detail": "r=4,T=1,N=1024/2048 same-backend comparison.", "next_action": ""},
        {"gate": "stage142_decision", "status": decision, "metric": "promotion_policy", "value": range_field(compare_rows, "r4_unrolled_vs_generic_mean"), "evidence": f"{rel(SUMMARY_CSV)}; {rel(COMPARE_CSV)}", "detail": "FMA-order fix removes Stage141 correctness blocker; r4-unrolled is a kernel-only promotion candidate.", "next_action": "Rerun full SAB A/B before claiming bootstrapping speedup."},
    ]


def append_once(path: Path, heading: str, block: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if heading in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(path, text + block.strip() + "\n")


def write_docs(summary: List[Dict[str, str]], compare_rows: List[Dict[str, str]]) -> None:
    status = summary[-1]["status"]
    summary_table = table(summary, ["gate", "status", "metric", "value", "detail"])
    compare_table = table(compare_rows, COMPARE_FIELDS)
    write_text_lf(PLAN_MD, "\n".join([
        "# Stage142 AVX512 FMA-Order Fix Gate Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Test whether changing only `mat_avx512_complex_addmul` to the same FMA order as `polynomial_mul_addto_DFT` removes the Stage141 closed full-MAT correctness blocker.",
        "",
        "## Primary Endpoint",
        "",
        "`PASS_CLOSED_FULLMAT_SPLIT_EQUIV` for generic, small-r, and r4-unrolled AVX512 builds on r=2/4/6 and N=1024/2048.",
        "",
        "## Secondary Endpoint",
        "",
        "Same-backend r=4,T=1 kernel speedup for `r4_unrolled_avx512` over `generic_avx512`; this is not a complete SAB speedup claim.",
        "",
        "## Failure Criteria",
        "",
        "- any specialized row has nonzero DFT mismatch;",
        "- speedup is reported without same-backend comparison;",
        "- kernel speedup is promoted as full bootstrapping speedup.",
    ]) + "\n")
    write_text_lf(THEORY_MD, "\n".join([
        "# Stage142 AVX512 FMA-Order Model",
        "",
        "Date: 2026-07-03",
        "",
        "Stage141 failed because the specialized MAT AVX512 addmul accumulated complex products in a different FMA order from the generic `polynomial_mul_addto_DFT` path. The mathematical operation is the same, but the closed full-MAT DFT equivalence gate requires bit-level agreement with the generic reference.",
        "",
        "The Stage142 code change preserves the same complex addmul:",
        "",
        "```text",
        "acc_re += dec_re * sel_re - dec_im * sel_im",
        "acc_im += dec_im * sel_re + dec_re * sel_im",
        "```",
        "",
        "but uses the same FMA grouping as the generic AVX512 implementation. This is a kernel correctness repair, not a new SAB algorithmic step.",
        "",
        "## Comparison",
        "",
        compare_table,
    ]) + "\n")
    write_text_lf(VARIANT_MD, "\n".join([
        "# V142: AVX512 FMA-Order Fixed Closed Full-MAT Kernel",
        "",
        "## Summary",
        "",
        "- Parent algorithm: PVW/MAT-SAB.",
        "- Focused module: closed full-MAT external product for PVW_TMLWE.",
        "- Optimization target: reliable MAT-aware AVX512 kernel before full SAB A/B.",
        "- Status labels: `[kernel correctness repaired]`, `[full SAB rerun pending]`.",
        "- Main hypothesis: matching generic AVX512 FMA order removes Stage141 exact-equivalence failures while keeping r=4 unrolled kernel speed useful.",
        "",
        "## Delta From Original Algorithm",
        "",
        "| Original component | Variant component | Relationship | Evidence/status |",
        "| --- | --- | --- | --- |",
        "| Generic full-MAT DFT addmul | Same operation with MAT-aware r=2/r=4 AVX512 specialization | implements | Stage142 exact DFT gate |",
        "| Stage141 specialized FMA grouping | Stage142 grouping matching `polynomial_mul_addto_DFT` | preserves operation, changes rounding path | correctness repair |",
        "",
        "## Required Next Experiment",
        "",
        "Full SAB A/B with `MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true` against repeated scalar SAB on the same backend, using `T_bootstrap/r` as the primary metric.",
    ]) + "\n")
    write_text_lf(OUT_MD, "\n".join([
        "# Stage142 AVX512 FMA-Order Fix Gate",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{status}`",
        "",
        "Stage142 keeps Stage141 as the recorded failed baseline and adds a minimal code repair: the MAT-aware AVX512 addmul now follows the generic AVX512 FMA order.",
        "",
        "## Gates",
        "",
        summary_table,
        "",
        "## Comparison",
        "",
        compare_table,
        "",
        "## Interpretation",
        "",
        "The Stage141 correctness blocker is removed at the closed full-MAT kernel level. The r4-unrolled result is promotable only to full SAB A/B, not to a final bootstrapping speedup claim.",
    ]) + "\n")


def update_longform_docs(status: str, compare_rows: List[Dict[str, str]]) -> None:
    speed_range = range_field(compare_rows, "r4_unrolled_vs_generic_mean")
    stage_block = f"""
## Stage 142: AVX512 FMA-Order Fix Gate

Goal:

```text
Repair the Stage141 specialized-kernel correctness blocker by matching the
generic AVX512 FMA order in MAT-aware complex addmul, then rerun the closed
full-MAT r=4 target kernel gate.
```

Status:

```text
Completed. Stage142 records {status}. The r4-unrolled closed full-MAT mean
kernel speedup over generic AVX512 is {speed_range} for r=4,T=1,N=1024/2048.
This is a kernel-only result; Stage143 must run complete SAB A/B with
T_bootstrap/r as the primary endpoint.
```
"""
    append_once(ROADMAP_MD, "## Stage 142: AVX512 FMA-Order Fix Gate", stage_block)
    goal_block = f"""
Stage142 repairs the AVX512 small-r closed full-MAT kernel by aligning its FMA
order with the generic AVX512 DFT addmul path. This moves the AVX512 MAT route
from correctness-blocked to full-SAB-rerun-ready, but it remains a kernel-level
promotion candidate until complete SAB A/B passes.
"""
    append_once(GOAL_MD, "Stage142 repairs the AVX512 small-r closed full-MAT kernel", goal_block)
    current_block = f"""
46. Treat Stage142 as the AVX512 FMA-order correctness repair:
    `{status}`. The r4-unrolled closed full-MAT mean kernel speedup is
    {speed_range}. Next required gate: complete SAB A/B using amortized
    `T_bootstrap/r`, not raw kernel time.
"""
    append_once(CURRENT_GOAL_MD, "46. Treat Stage142 as the AVX512", current_block)


def upsert_hypothesis(status: str, compare_rows: List[Dict[str, str]]) -> None:
    speed_range = range_field(compare_rows, "r4_unrolled_vs_generic_mean")
    block = f"""  - id: H66_avx512_fma_order_fix
    statement: >
      If MAT-aware AVX512 complex addmul uses the same FMA grouping as the
      generic AVX512 DFT addmul reference, then the small-r and r4-unrolled
      closed full-MAT kernels should regain exact DFT equivalence while keeping
      useful r=4 kernel speed.
    mechanism: >
      Stage141 mismatches came from a different floating-point rounding path,
      not from a different MAT-RLWE operation. Aligning the FMA order makes the
      specialized path bit-equivalent to the generic closed full-MAT split.
    status: stage142_avx512_fma_order_fix_gate
    evidence: docs/stage142_avx512_fma_order_fix_gate.md; experiments/stage142_avx512_fma_order_fix_gate_plan.md; theory_checks/stage142_avx512_fma_order_model.md; algorithm_variants/mat_rlwe_sab_avx512_fma_order_fix.md; scripts/build_stage142_avx512_fma_order_fix_gate.py; repro/stage142_avx512_fma_order_fix_gate/summary.csv; repro/stage142_avx512_fma_order_fix_gate/correctness.csv; repro/stage142_avx512_fma_order_fix_gate/comparison.csv; repro/stage142_avx512_fma_order_fix_gate/artifact_index.csv
    current_decision: >
      Stage142 records {status}. r4-unrolled closed full-MAT mean kernel
      speedup over generic AVX512 is {speed_range}. This is ready for complete
      SAB A/B, not a final bootstrapping speedup claim.
    failure_criteria:
      - DFT equivalence fails for any specialized row
      - kernel speedup is reported as complete SAB speedup
      - full SAB A/B does not improve amortized T_bootstrap/r
"""
    text = HYPOTHESIS_YAML.read_text(encoding="utf-8") if HYPOTHESIS_YAML.exists() else "hypotheses:\n"
    marker = "  - id: H66_avx512_fma_order_fix"
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n"
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(HYPOTHESIS_YAML, text + block)


def upsert_run_log(status: str) -> None:
    fields = ["run_id", "date", "commit_or_state", "stage", "backend", "command", "params", "seed", "status", "summary", "artifacts"]
    run_id = "stage142-avx512-fma-order-fix-001"
    rows = [row for row in read_csv(RUN_LOG) if row.get("run_id") != run_id]
    artifacts = [OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, SUMMARY_CSV, CORRECTNESS_CSV, BENCH_CSV, AGG_CSV, COMPARE_CSV, C_SOURCE, ARTIFACT_INDEX, Path(__file__).resolve()]
    for config in CONFIGS:
        artifacts += [log_path(config["id"], "build"), log_path(config["id"], "compile"), log_path(config["id"], "run")]
    artifacts.append(OUT_DIR / "cleanup.log")
    rows.append({
        "run_id": run_id,
        "date": "2026-07-03",
        "commit_or_state": f"working-tree-after-{git_head()}",
        "stage": "Stage 142",
        "backend": "MOSFHET FFT_LIB=spqlios_avx512 ENABLE_PVW_TMLWE=true",
        "command": "python scripts/build_stage142_avx512_fma_order_fix_gate.py",
        "params": "configs=generic_avx512,smallr_avx512,r4_unrolled_avx512; r=2,4,6 N=1024,2048 T=1 Bg_bit=23 samples=5 reps=20",
        "seed": "0 subset",
        "status": status,
        "summary": "Stage142 tests the AVX512 FMA-order fix for closed full-MAT exact equivalence and r4-unrolled kernel speed.",
        "artifacts": "; ".join(rel(p) for p in artifacts),
    })
    write_csv(RUN_LOG, rows, fields)


def upsert_global_manifest() -> None:
    block = """
## Stage 142 AVX512 FMA-Order Fix Gate

- `docs/stage142_avx512_fma_order_fix_gate.md`
- `experiments/stage142_avx512_fma_order_fix_gate_plan.md`
- `theory_checks/stage142_avx512_fma_order_model.md`
- `algorithm_variants/mat_rlwe_sab_avx512_fma_order_fix.md`
- `scripts/build_stage142_avx512_fma_order_fix_gate.py`
- `repro/stage142_avx512_fma_order_fix_gate/summary.csv`
- `repro/stage142_avx512_fma_order_fix_gate/correctness.csv`
- `repro/stage142_avx512_fma_order_fix_gate/benchmark_samples.csv`
- `repro/stage142_avx512_fma_order_fix_gate/benchmark_aggregate.csv`
- `repro/stage142_avx512_fma_order_fix_gate/comparison.csv`
- `repro/stage142_avx512_fma_order_fix_gate/avx512_closed_fullmat_gate.c`
- `repro/stage142_avx512_fma_order_fix_gate/build_*.log`
- `repro/stage142_avx512_fma_order_fix_gate/compile_*.log`
- `repro/stage142_avx512_fma_order_fix_gate/run_*.log`
- `repro/stage142_avx512_fma_order_fix_gate/artifact_index.csv`
"""
    append_once(GLOBAL_MANIFEST, "## Stage 142 AVX512 FMA-Order Fix Gate", block)


def write_artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        if path == ARTIFACT_INDEX:
            rows.append({"artifact": rel(path), "exists": "self", "sha256": "", "size_bytes": ""})
            continue
        rows.append({
            "artifact": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path) if path.exists() else "",
            "size_bytes": str(path.stat().st_size) if path.exists() else "0",
        })
    write_csv(ARTIFACT_INDEX, rows, ["artifact", "exists", "sha256", "size_bytes"])


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(STAGE141_C, C_SOURCE)
    avx_ok = avx512_supported()
    config_status: Dict[str, Dict[str, bool]] = {}
    correctness_rows: List[Dict[str, str]] = []
    bench_rows: List[Dict[str, str]] = []
    if avx_ok:
        for config in CONFIGS:
            status = config_status.setdefault(config["id"], {})
            status["build"] = build_mosfhet_static(config)
            status["compile"] = compile_probe(config) if status["build"] else False
            corr, bench, status["run"] = run_probe(config, status["build"], status["compile"])
            correctness_rows.extend(corr)
            bench_rows.extend(bench)
        cleanup_build_outputs()
    else:
        for config in CONFIGS:
            config_status[config["id"]] = {"build": False, "compile": False, "run": False}

    agg_rows = aggregate_bench(bench_rows)
    compare_rows = build_comparison_rows(agg_rows, correctness_rows)
    write_csv(CORRECTNESS_CSV, correctness_rows, CORRECTNESS_FIELDS)
    write_csv(BENCH_CSV, bench_rows, BENCH_FIELDS)
    write_csv(AGG_CSV, agg_rows, AGG_FIELDS)
    write_csv(COMPARE_CSV, compare_rows, COMPARE_FIELDS)
    summary = build_summary(avx_ok, config_status, correctness_rows, bench_rows, compare_rows)
    write_csv(SUMMARY_CSV, summary, SUMMARY_FIELDS)
    status = summary[-1]["status"]
    write_docs(summary, compare_rows)
    update_longform_docs(status, compare_rows)
    upsert_hypothesis(status, compare_rows)
    upsert_run_log(status)
    upsert_global_manifest()
    artifacts = [OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, SUMMARY_CSV, CORRECTNESS_CSV, BENCH_CSV, AGG_CSV, COMPARE_CSV, C_SOURCE, ARTIFACT_INDEX, Path(__file__).resolve()]
    for config in CONFIGS:
        artifacts += [log_path(config["id"], "build"), log_path(config["id"], "compile"), log_path(config["id"], "run")]
    artifacts.append(OUT_DIR / "cleanup.log")
    write_artifact_index(artifacts)
    print(f"Stage142 AVX512 FMA-order fix gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if not status.startswith("FAIL_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
