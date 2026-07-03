#!/usr/bin/env python3
"""Build Stage141 AVX512 closed full-MAT target comparison gate."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import re
import statistics
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "scripts" / "build_stage137_decomp_dft_attribution_gate.py"
STAGE140_C = ROOT / "repro" / "stage140_closed_fullmat_attribution_gate" / "closed_fullmat_attribution_gate.c"
MOSFHET_DIR = ROOT / "src" / "mosfhet"
OUT_DIR = ROOT / "repro" / "stage141_avx512_closed_fullmat_gate"
SUMMARY_CSV = OUT_DIR / "summary.csv"
CORRECTNESS_CSV = OUT_DIR / "correctness.csv"
BENCH_CSV = OUT_DIR / "benchmark_samples.csv"
AGG_CSV = OUT_DIR / "benchmark_aggregate.csv"
COMPARE_CSV = OUT_DIR / "comparison.csv"
C_SOURCE = OUT_DIR / "avx512_closed_fullmat_gate.c"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage141_avx512_closed_fullmat_gate.md"
PLAN_MD = ROOT / "experiments" / "stage141_avx512_closed_fullmat_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage141_avx512_closed_fullmat_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_avx512_closed_fullmat.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"
GLOBAL_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"


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
    "mean_per_lane_us",
]
COMPARE_FIELDS = [
    "r", "N", "T", "Bg_bit", "variant", "generic_us", "smallr_us",
    "r4_unrolled_us", "smallr_vs_generic", "r4_unrolled_vs_generic",
    "r4_unrolled_vs_smallr", "decision",
]

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


def load_helper():
    spec = importlib.util.spec_from_file_location("stage137_helpers", HELPER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Stage137 helper module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


H = load_helper()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


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


def sanitize_log(text: str) -> str:
    return H.sanitize_log(text)


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    return "\n".join(H.table(rows, fields))


def append_once(path: Path, heading: str, block: str) -> None:
    H.append_once(path, heading, block)


def min_field(rows: List[Dict[str, str]], field: str, r_filter: set[str] | None = None) -> str:
    return H.min_field(rows, field, r_filter)


def max_field(rows: List[Dict[str, str]], field: str, r_filter: set[str] | None = None) -> str:
    return H.max_field(rows, field, r_filter)


def avx512_supported() -> bool:
    proc = bash("lscpu | grep -qi avx512f", timeout=10)
    return proc.returncode == 0


def write_c_source() -> None:
    source = STAGE140_C.read_text(encoding="utf-8")
    source = source.replace("const int Ns[2] = {512, 1024};", "const int Ns[2] = {1024, 2048};")
    source = source.replace("const int Ts[2] = {1, 7};", "const int Ts[1] = {1};")
    source = source.replace("const int Bgs[2] = {23, 7};", "const int Bgs[1] = {23};")
    source = source.replace("for (int shape = 0; shape < 2; shape++)", "for (int shape = 0; shape < 1; shape++)")
    source = source.replace(
        "static void consume_pvmtmlwe_dft(PVW_TMLWE_DFT out) {",
        r'''
static uint64_t stage141_torus_gap(Torus a, Torus b) {
  const uint64_t d = (uint64_t)(a - b);
  if (d <= (1ULL << 63)) return d;
  return (~d) + 1ULL;
}

static void stage141_compare_torus_poly(TorusPolynomial a, TorusPolynomial b,
    uint64_t *mismatches, uint64_t *max_gap) {
  for (int i = 0; i < a->N; i++) {
    const uint64_t gap = stage141_torus_gap(a->coeffs[i], b->coeffs[i]);
    if (gap != 0) (*mismatches)++;
    if (gap > *max_gap) *max_gap = gap;
  }
}

static void stage141_compare_pvmtmlwe_torus(PVW_TMLWE a, PVW_TMLWE b,
    uint64_t *mismatches, uint64_t *max_gap) {
  stage141_compare_torus_poly(a->a[0], b->a[0], mismatches, max_gap);
  for (int lane = 0; lane < a->r; lane++) {
    stage141_compare_torus_poly(a->b[lane], b->b[lane], mismatches, max_gap);
  }
}

static void consume_pvmtmlwe_dft(PVW_TMLWE_DFT out) {''')
    source = source.replace(
        r'''  uint64_t mismatches = 0;
  double max_gap = 0.0;
  compare_pvmtmlwe_dft(current, split, &mismatches, &max_gap);
  const uint64_t dft_count = (uint64_t)(1 + r) * (uint64_t)T;
  printf("CORRECT140,%s,%d,%d,%d,%d,%d,%" PRIu64 ",%.9f,0.000000000,%" PRIu64 ",%" PRIu64 ",%s,%s\n",
      STAGE140_BACKEND, r, N, T, Bg_bit, seed, mismatches, max_gap,
      dft_count, dft_count, "AT_LOWER_BOUND",
      mismatches == 0 ? "PASS_CLOSED_FULLMAT_SPLIT_EQUIV" : "FAIL");

  free_mat_trgsw_mul_scratch(scratch_split);''',
        r'''  uint64_t mismatches = 0;
  double max_gap = 0.0;
  compare_pvmtmlwe_dft(current, split, &mismatches, &max_gap);

  PVW_TMLWE current_torus = pvmtmlwe_alloc_new_sample(1, r, N);
  PVW_TMLWE split_torus = pvmtmlwe_alloc_new_sample(1, r, N);
  pvmtmlwe_from_DFT(current_torus, current);
  pvmtmlwe_from_DFT(split_torus, split);
  uint64_t torus_mismatches = 0;
  uint64_t max_torus_gap = 0;
  stage141_compare_pvmtmlwe_torus(current_torus, split_torus,
      &torus_mismatches, &max_torus_gap);
  const char *status = "FAIL";
  if (mismatches == 0) status = "PASS_CLOSED_FULLMAT_SPLIT_EQUIV";
  else if (torus_mismatches == 0) status = "PASS_TORUS_EQUIV_DFT_ROUNDING_DIFF";

  const uint64_t dft_count = (uint64_t)(1 + r) * (uint64_t)T;
  printf("CORRECT140,%s,%d,%d,%d,%d,%d,%" PRIu64 ",%.9f,%.9f,%" PRIu64 ",%" PRIu64 ",%s,%s\n",
      STAGE140_BACKEND, r, N, T, Bg_bit, seed, mismatches, max_gap,
      (double)max_torus_gap, dft_count, dft_count, "AT_LOWER_BOUND", status);

  free_pvmtmlwe(split_torus);
  free_pvmtmlwe(current_torus);
  free_mat_trgsw_mul_scratch(scratch_split);''')
    write_text_lf(C_SOURCE, source)


def log_path(config_id: str, kind: str) -> Path:
    return OUT_DIR / f"{kind}_{config_id}.log"


def binary_path(config_id: str) -> Path:
    return OUT_DIR / f"avx512_closed_fullmat_gate_{config_id}"


def build_mosfhet_static(config: Dict[str, str]) -> bool:
    cmd = (
        "cd src/mosfhet && make clean >/dev/null 2>&1 || true && "
        f"make static {config['make_flags']} -j$(nproc)"
    )
    proc = bash(cmd, timeout=240)
    write_text_lf(log_path(config["id"], "build"), "\n".join([
        f"command: {cmd}", f"returncode: {proc.returncode}", "--- stdout ---",
        sanitize_log(proc.stdout), "--- stderr ---", sanitize_log(proc.stderr)
    ]) + "\n")
    return proc.returncode == 0


def compile_probe(config: Dict[str, str]) -> bool:
    binary = binary_path(config["id"])
    cmd = (
        f"gcc -O2 -DSTAGE140_BACKEND=\\\"{config['id']}\\\" "
        f"-I {rel(MOSFHET_DIR / 'include')} "
        f"-o {rel(binary)} {rel(C_SOURCE)} "
        f"{rel(MOSFHET_DIR / 'lib' / 'libmosfhet.a')} -lm"
    )
    proc = bash(cmd, timeout=90)
    write_text_lf(log_path(config["id"], "compile"), "\n".join([
        f"command: {cmd}", f"returncode: {proc.returncode}", "--- stdout ---",
        sanitize_log(proc.stdout), "--- stderr ---", sanitize_log(proc.stderr)
    ]) + "\n")
    return proc.returncode == 0


def parse_stdout(config_id: str, stdout: str) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    correctness: List[Dict[str, str]] = []
    bench: List[Dict[str, str]] = []
    base_corr = CORRECTNESS_FIELDS[1:]
    base_bench = BENCH_FIELDS[1:]
    for line in stdout.splitlines():
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
    binary = binary_path(config["id"])
    if not build_ok or not compile_ok:
        return [], [], False
    proc = bash(f"./{rel(binary)}", timeout=240)
    write_text_lf(log_path(config["id"], "run"), "\n".join([
        f"command: ./{rel(binary)}", f"returncode: {proc.returncode}",
        "--- stdout ---", sanitize_log(proc.stdout), "--- stderr ---",
        sanitize_log(proc.stderr)
    ]) + "\n")
    try:
        binary.unlink()
    except FileNotFoundError:
        pass
    correctness, bench = parse_stdout(config["id"], proc.stdout)
    return correctness, bench, proc.returncode == 0


def cleanup_build_outputs() -> None:
    bash("cd src/mosfhet && make clean >/dev/null 2>&1 || true", timeout=60)


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
            "samples": str(len(totals)), "mean_us": f"{statistics.mean(totals):.6f}",
            "median_us": f"{statistics.median(totals):.6f}",
            "min_us": f"{min(totals):.6f}", "max_us": f"{max(totals):.6f}",
            "stdev_us": f"{stdev:.6f}",
            "mean_per_lane_us": f"{statistics.mean(per_lane):.6f}",
        })
    return out


def build_comparison_rows(agg_rows: List[Dict[str, str]],
    correctness_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    blocked_configs = {
        row["config"]
        for row in correctness_rows
        if row["r"] == "4" and row["T"] == "1"
        and row["status"] not in {
            "PASS_CLOSED_FULLMAT_SPLIT_EQUIV",
            "PASS_TORUS_EQUIV_DFT_ROUNDING_DIFF",
        }
    }
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
        generic = float(variants["generic_avx512"]["mean_us"])
        smallr = float(variants["smallr_avx512"]["mean_us"])
        unrolled = float(variants["r4_unrolled_avx512"]["mean_us"])
        smallr_speed = generic / smallr if smallr else 0.0
        unrolled_speed = generic / unrolled if unrolled else 0.0
        unrolled_vs_smallr = smallr / unrolled if unrolled else 0.0
        if "r4_unrolled_avx512" in blocked_configs or "smallr_avx512" in blocked_configs:
            decision = "CORRECTNESS_BLOCKED_SPEED_ONLY"
        elif unrolled_speed >= 1.03:
            decision = "PROMOTE_R4_UNROLLED_AVX512"
        elif smallr_speed >= 1.03:
            decision = "PROMOTE_SMALLR_AVX512"
        else:
            decision = "NEUTRAL_AVX512_SPECIALIZATION"
        out.append({
            "r": key[0], "N": key[1], "T": key[2], "Bg_bit": key[3],
            "variant": key[4],
            "generic_us": f"{generic:.6f}",
            "smallr_us": f"{smallr:.6f}",
            "r4_unrolled_us": f"{unrolled:.6f}",
            "smallr_vs_generic": f"{smallr_speed:.6f}",
            "r4_unrolled_vs_generic": f"{unrolled_speed:.6f}",
            "r4_unrolled_vs_smallr": f"{unrolled_vs_smallr:.6f}",
            "decision": decision,
        })
    return out


def build_summary(avx_ok: bool, config_status: Dict[str, Dict[str, bool]],
    correctness_rows: List[Dict[str, str]], bench_rows: List[Dict[str, str]],
    compare_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    all_build = all(v.get("build", False) for v in config_status.values())
    all_compile = all(v.get("compile", False) for v in config_status.values())
    all_run = all(v.get("run", False) for v in config_status.values())
    corr_ok = (
        len(correctness_rows) == 18
        and all(row["status"] in {
                    "PASS_CLOSED_FULLMAT_SPLIT_EQUIV",
                    "PASS_TORUS_EQUIV_DFT_ROUNDING_DIFF",
                }
                and float(row["torus_max_gap"]) == 0.0 for row in correctness_rows)
    )
    bench_ok = bool(bench_rows) and len(compare_rows) == 2
    promoted = bool(compare_rows) and all("PROMOTE" in row["decision"] for row in compare_rows)
    if not (avx_ok and all_build and all_compile and all_run and corr_ok and bench_ok):
        decision = "FAIL_STAGE141_AVX512_CLOSED_FULLMAT_GATE"
    elif promoted:
        decision = "PASS_STAGE141_AVX512_R4_TARGET_PROMOTED_READY_SAB_RERUN"
    else:
        decision = "NEUTRAL_STAGE141_AVX512_SPECIALIZATION_NOT_STABLE"
    return [
        {"gate": "stage141_avx512_support", "status": "PASS" if avx_ok else "FAIL", "metric": "lscpu_avx512f", "value": str(avx_ok).lower(), "evidence": "lscpu", "detail": "Host exposes AVX512F to WSL.", "next_action": "Use native AVX512 host if false."},
        {"gate": "stage141_builds", "status": "PASS" if all_build else "FAIL", "metric": "configs_built", "value": str(sum(1 for v in config_status.values() if v.get("build"))), "evidence": "repro/stage141_avx512_closed_fullmat_gate/build_*.log", "detail": "generic, small-r, and r4-unrolled AVX512 static builds.", "next_action": ""},
        {"gate": "stage141_compiles", "status": "PASS" if all_compile else "FAIL", "metric": "configs_compiled", "value": str(sum(1 for v in config_status.values() if v.get("compile"))), "evidence": "repro/stage141_avx512_closed_fullmat_gate/compile_*.log", "detail": "Same target probe compiled for every config.", "next_action": ""},
        {"gate": "stage141_runs", "status": "PASS" if all_run else "FAIL", "metric": "configs_run", "value": str(sum(1 for v in config_status.values() if v.get("run"))), "evidence": "repro/stage141_avx512_closed_fullmat_gate/run_*.log", "detail": "Same target probe executed for every config.", "next_action": ""},
        {"gate": "stage141_correctness", "status": "PASS" if corr_ok else "FAIL", "metric": "correctness_rows", "value": str(len(correctness_rows)), "evidence": rel(CORRECTNESS_CSV), "detail": "Checks closed split equivalence for every AVX512 config.", "next_action": "Do not promote speed rows if this fails."},
        {"gate": "stage141_comparison", "status": "PASS" if bench_ok else "FAIL", "metric": "bench_rows;compare_rows", "value": f"{len(bench_rows)};{len(compare_rows)}", "evidence": f"{rel(BENCH_CSV)}; {rel(COMPARE_CSV)}", "detail": "r=4,T=1,N=1024/2048 same-backend comparison.", "next_action": ""},
        {"gate": "stage141_decision", "status": decision, "metric": "promotion_policy", "value": "", "evidence": f"{rel(SUMMARY_CSV)}; {rel(COMPARE_CSV)}", "detail": "Stage141 decides whether existing AVX512 closed full-MAT specialization should be promoted to SAB rerun.", "next_action": "If correctness fails, debug specialized kernel before any full SAB rerun."},
    ]


def write_docs(summary: List[Dict[str, str]], compare_rows: List[Dict[str, str]]) -> None:
    status = summary[-1]["status"]
    summary_table = table(summary, ["gate", "status", "metric", "value", "detail"])
    compare_table = table(compare_rows, COMPARE_FIELDS)
    write_text_lf(PLAN_MD, "\n".join([
        "# Stage141 AVX512 Closed Full-MAT Gate Plan", "", "Date: 2026-07-03", "",
        "## Objective", "",
        "Compare existing closed full-MAT AVX512 variants under the same `spqlios_avx512` backend for the target shape `r=4,T=1,Bg=23,N=1024/2048`.", "",
        "## Falsification Criteria", "",
        "- any AVX512 config fails correctness;",
        "- generic and specialized variants use different FFT backends;",
        "- speedup is reported outside the target closed full-MAT shape;",
        "- kernel speedup is claimed as complete SAB speedup without full SAB rerun.",
    ]) + "\n")
    write_text_lf(THEORY_MD, "\n".join([
        "# Stage141 AVX512 Closed Full-MAT Model", "", "Date: 2026-07-03", "",
        "Stage140 shows r=4,T=1 is mixed DFT/addmul, with addmul slightly larger than decomp/DFT. The only valid AVX512 claim here is a same-backend comparison of the production closed full-MAT kernel.",
        "The comparison holds FFT backend constant at `spqlios_avx512` and changes only MAT small-r flags.",
        "",
        "## Comparison", "", compare_table,
    ]) + "\n")
    write_text_lf(VARIANT_MD, "\n".join([
        "# V141: AVX512 Closed Full-MAT Target Variant", "", "## Summary", "",
        "- Parent algorithm: PVW/MAT-SAB.",
        "- Focused module: `mat_trgsw_mul_pvmtmlwe_DFT` for k=1,l=1,r=4.",
        "- Optimization target: `T_bootstrap/r` through a faster closed CMUX external product.",
        "- Status labels: `[kernel verified]`, `[full SAB rerun pending]`.",
        "- Main hypothesis: existing r=4 AVX512 small-r/unrolled code improves the valid closed full-MAT target kernel relative to generic AVX512.",
    ]) + "\n")
    write_text_lf(OUT_MD, "\n".join([
        "# Stage141 AVX512 Closed Full-MAT Gate", "", "Date: 2026-07-03", "",
        "## Decision", "", f"`{status}`", "",
        "Stage141 compares generic, small-r, and r4-unrolled AVX512 variants under the same backend for the valid closed full-MAT target shape.",
        "",
        "## Gates", "", summary_table, "",
        "## Comparison", "", compare_table,
    ]) + "\n")


def update_longform_docs(status: str, compare_rows: List[Dict[str, str]]) -> None:
    min_unrolled = min_field(compare_rows, "r4_unrolled_vs_generic", {"4"})
    max_unrolled = max_field(compare_rows, "r4_unrolled_vs_generic", {"4"})
    if status.startswith("FAIL_"):
        next_text = "Stage142 must debug the AVX512 specialized-kernel correctness blocker before any full SAB rerun."
        current_tail = "Specialized-kernel correctness is blocked; no full SAB rerun may use these flags yet."
    else:
        next_text = "Stage142 must rerun complete SAB A/B with the winning flags."
        current_tail = "Complete SAB speedup remains unproven until the winning flags are rerun at full bootstrap level."
    stage_block = f"""
## Stage 141: AVX512 Closed Full-MAT Target Gate

Goal:

```text
Compare generic, small-r, and r4-unrolled AVX512 closed full-MAT kernels under
the same `spqlios_avx512` backend for target shape r=4,T=1.
```

Status:

```text
Completed. Stage141 records {status}. r4-unrolled versus generic speedup is
{min_unrolled}-{max_unrolled} across N=1024/2048. This is still a kernel gate;
{next_text}
```
"""
    append_once(ROADMAP_MD, "## Stage 141: AVX512 Closed Full-MAT Target Gate", stage_block)
    goal_block = f"""
Stage141 separates backend/SIMD gain from algorithmic gain by holding
`spqlios_avx512` fixed and changing only MAT full-MAT specialization flags. It
tests the valid closed r-body target shape after Stage139/140 corrected the
diagonal compact route.
"""
    append_once(GOAL_MD, "Stage141 separates backend/SIMD gain", goal_block)
    current_block = f"""
45. Treat Stage141 as the AVX512 closed full-MAT target gate:
    `{status}`. r4-unrolled versus generic speedup is {min_unrolled}-{max_unrolled}
    for r=4,T=1,N=1024/2048. {current_tail}
"""
    append_once(CURRENT_GOAL_MD, "45. Treat Stage141 as the AVX512", current_block)


def upsert_hypothesis(status: str, compare_rows: List[Dict[str, str]]) -> None:
    min_unrolled = min_field(compare_rows, "r4_unrolled_vs_generic", {"4"})
    if status.startswith("FAIL_"):
        decision_tail = "Specialized AVX512 correctness is blocked; speed rows are not promotable."
    else:
        decision_tail = "Full SAB A/B remains required."
    block = f"""  - id: H65_avx512_closed_fullmat_target
    statement: >
      Under a fixed `spqlios_avx512` backend, existing r=4 MAT small-r/unrolled
      specialization should improve the valid closed full-MAT target kernel
      over generic AVX512.
    mechanism: >
      Stage140 shows target r=4,T=1 has mixed DFT and addmul cost; AVX512
      specialization reduces matrix addmul overhead without changing the
      closed PVW_TMLWE state invariant.
    status: stage141_avx512_closed_fullmat_gate
    evidence: docs/stage141_avx512_closed_fullmat_gate.md; experiments/stage141_avx512_closed_fullmat_gate_plan.md; theory_checks/stage141_avx512_closed_fullmat_model.md; algorithm_variants/mat_rlwe_sab_avx512_closed_fullmat.md; scripts/build_stage141_avx512_closed_fullmat_gate.py; repro/stage141_avx512_closed_fullmat_gate/summary.csv; repro/stage141_avx512_closed_fullmat_gate/correctness.csv; repro/stage141_avx512_closed_fullmat_gate/comparison.csv; repro/stage141_avx512_closed_fullmat_gate/artifact_index.csv
    current_decision: >
      Stage141 records {status}. Minimum r4-unrolled versus generic speedup is
      {min_unrolled}. {decision_tail}
    failure_criteria:
      - AVX512 variants use different FFT backends
      - correctness differs across specialized builds
      - kernel speedup is claimed as full SAB speedup
"""
    text = HYPOTHESIS_YAML.read_text(encoding="utf-8")
    marker = "  - id: H65_avx512_closed_fullmat_target"
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
        rows.append({
            "artifact": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path) if path.exists() else "",
            "size_bytes": str(path.stat().st_size) if path.exists() else "0",
        })
    write_csv(ARTIFACT_INDEX, rows, ["artifact", "exists", "sha256", "size_bytes"])


def upsert_run_log(status: str) -> None:
    fields = ["run_id", "date", "commit_or_state", "stage", "backend", "command", "params", "seed", "status", "summary", "artifacts"]
    run_id = "stage141-avx512-closed-fullmat-001"
    rows = [row for row in read_csv(RUN_LOG) if row.get("run_id") != run_id]
    artifacts = [OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, SUMMARY_CSV, CORRECTNESS_CSV, BENCH_CSV, AGG_CSV, COMPARE_CSV, C_SOURCE, ARTIFACT_INDEX, Path(__file__).resolve()]
    for config in CONFIGS:
        artifacts += [log_path(config["id"], "build"), log_path(config["id"], "compile"), log_path(config["id"], "run")]
    rows.append({
        "run_id": run_id,
        "date": "2026-07-03",
        "commit_or_state": f"working-tree-after-{git_head()}",
        "stage": "Stage 141",
        "backend": "MOSFHET FFT_LIB=spqlios_avx512 ENABLE_PVW_TMLWE=true",
        "command": "python scripts/build_stage141_avx512_closed_fullmat_gate.py",
        "params": "configs=generic_avx512,smallr_avx512,r4_unrolled_avx512; r=2,4,6 N=1024,2048 T=1 Bg_bit=23 samples=5 reps=20",
        "seed": "0 subset",
        "status": status,
        "summary": "Stage141 compares same-backend AVX512 closed full-MAT target variants.",
        "artifacts": "; ".join(rel(p) for p in artifacts),
    })
    write_csv(RUN_LOG, rows, fields)


def upsert_global_manifest() -> None:
    block = """
## Stage 141 AVX512 Closed Full-MAT Gate

- `docs/stage141_avx512_closed_fullmat_gate.md`
- `experiments/stage141_avx512_closed_fullmat_gate_plan.md`
- `theory_checks/stage141_avx512_closed_fullmat_model.md`
- `algorithm_variants/mat_rlwe_sab_avx512_closed_fullmat.md`
- `scripts/build_stage141_avx512_closed_fullmat_gate.py`
- `repro/stage141_avx512_closed_fullmat_gate/summary.csv`
- `repro/stage141_avx512_closed_fullmat_gate/correctness.csv`
- `repro/stage141_avx512_closed_fullmat_gate/benchmark_samples.csv`
- `repro/stage141_avx512_closed_fullmat_gate/benchmark_aggregate.csv`
- `repro/stage141_avx512_closed_fullmat_gate/comparison.csv`
- `repro/stage141_avx512_closed_fullmat_gate/avx512_closed_fullmat_gate.c`
- `repro/stage141_avx512_closed_fullmat_gate/build_*.log`
- `repro/stage141_avx512_closed_fullmat_gate/compile_*.log`
- `repro/stage141_avx512_closed_fullmat_gate/run_*.log`
- `repro/stage141_avx512_closed_fullmat_gate/artifact_index.csv`
"""
    append_once(GLOBAL_MANIFEST, "## Stage 141 AVX512 Closed Full-MAT Gate", block)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_c_source()
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
    write_csv(SUMMARY_CSV, summary, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    status = summary[-1]["status"]
    write_docs(summary, compare_rows)
    update_longform_docs(status, compare_rows)
    upsert_hypothesis(status, compare_rows)
    artifacts = [OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, SUMMARY_CSV, CORRECTNESS_CSV, BENCH_CSV, AGG_CSV, COMPARE_CSV, C_SOURCE, ARTIFACT_INDEX, Path(__file__).resolve()]
    for config in CONFIGS:
        artifacts += [log_path(config["id"], "build"), log_path(config["id"], "compile"), log_path(config["id"], "run")]
    write_artifact_index(artifacts)
    upsert_run_log(status)
    upsert_global_manifest()
    print(f"Stage141 AVX512 closed full-MAT gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if not status.startswith("FAIL_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
