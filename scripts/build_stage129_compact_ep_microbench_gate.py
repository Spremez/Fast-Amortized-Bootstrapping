#!/usr/bin/env python3
"""Build Stage129 isolated compact EP microbench/profiling gate."""

from __future__ import annotations

import csv
import hashlib
import statistics
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
MOSFHET_DIR = ROOT / "src" / "mosfhet"
STAGE128_C = ROOT / "repro" / "stage128_compact_ep_api_boundary_gate" / "compact_ep_api_boundary_gate.c"
OUT_DIR = ROOT / "repro" / "stage129_compact_ep_microbench_gate"
SUMMARY_CSV = OUT_DIR / "summary.csv"
API_CSV = OUT_DIR / "api_results.csv"
BENCH_CSV = OUT_DIR / "benchmark_samples.csv"
AGG_CSV = OUT_DIR / "benchmark_aggregate.csv"
RATIO_CSV = OUT_DIR / "ratio_summary.csv"
BUILD_LOG = OUT_DIR / "mosfhet_static_build.log"
COMPILE_LOG = OUT_DIR / "compile_probe.log"
RUN_LOG_TXT = OUT_DIR / "run_probe.log"
C_SOURCE = OUT_DIR / "compact_ep_microbench_gate.c"
C_BINARY = OUT_DIR / "compact_ep_microbench_gate"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage129_compact_ep_microbench_gate.md"
PLAN_MD = ROOT / "experiments" / "stage129_compact_ep_microbench_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage129_compact_ep_microbench_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_compact_ep_microbench.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"


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


def write_c_source() -> None:
    if not STAGE128_C.exists():
        raise FileNotFoundError(f"Stage128 C source missing: {STAGE128_C}")
    base = STAGE128_C.read_text(encoding="utf-8")
    marker = "int main(void) {"
    pos = base.rfind(marker)
    if pos < 0:
        raise RuntimeError("Could not locate Stage128 main() marker")
    prefix = base[:pos]
    prefix = prefix.replace("#include <string.h>\n", "#include <string.h>\n#include <time.h>\n")
    bench = r'''
#ifndef CLOCK_MONOTONIC_RAW
#define CLOCK_MONOTONIC_RAW CLOCK_MONOTONIC
#endif

static volatile double g_stage129_sink = 0.0;

static uint64_t stage129_now_ns(void) {
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
  return ((uint64_t)ts.tv_sec * 1000000000ULL) + (uint64_t)ts.tv_nsec;
}

static DFT_Polynomial *new_dft_array_api(int count, int N) {
  DFT_Polynomial *out = (DFT_Polynomial *)safe_malloc(sizeof(DFT_Polynomial) * count);
  for (int i = 0; i < count; i++) out[i] = api_new_dft_polynomial(N);
  return out;
}

static void free_dft_array_api(DFT_Polynomial *in, int count) {
  for (int i = 0; i < count; i++) api_free_dft_polynomial(in[i]);
  free(in);
}

static void consume_dft_array(DFT_Polynomial *arr, int count) {
  double s = 0.0;
  for (int i = 0; i < count; i++) {
    const int idx = (i * 17) & (arr[i]->N - 1);
    s += arr[i]->coeffs[idx];
  }
  g_stage129_sink += s;
}

static void consume_compact_outputs(CompactEpOutputDft *out, int r) {
  double s = 0.0;
  for (int q = 0; q < r; q++) {
    const int idx = (q * 19) & (out[q]->N - 1);
    s += out[q]->a->coeffs[idx] + out[q]->b->coeffs[idx];
  }
  g_stage129_sink += s;
}

static void fill_dense_rows(DFT_Polynomial *dense_rows, int m, int T, int N,
    int seed) {
  TorusPolynomial tmp = polynomial_new_torus_polynomial(N);
  for (int t = 0; t < T; t++) {
    for (int c = 0; c < m; c++) {
      for (int o = 0; o < m; o++) {
        const int idx = (t * m + c) * m + o;
        fill_small_mask(tmp, c, t, o, seed + 1000);
        polynomial_torus_to_DFT(dense_rows[idx], tmp);
      }
    }
  }
  free_polynomial(tmp);
}

static void dense_kernel_all(DFT_Polynomial *out, TorusPolynomial *source,
    DFT_Polynomial *dense_rows, int m, int T, int Bg_bit,
    CompactEpScratch scratch) {
  for (int o = 0; o < m; o++) zero_dft(out[o]);
  for (int t = 0; t < T; t++) {
    for (int c = 0; c < m; c++) {
      polynomial_decompose_i(scratch->dec_shared, source[c], Bg_bit, T, t);
      polynomial_torus_to_DFT(scratch->dec_shared_dft, scratch->dec_shared);
      for (int o = 0; o < m; o++) {
        const int idx = (t * m + c) * m + o;
        polynomial_mul_addto_DFT(out[o], scratch->dec_shared_dft, dense_rows[idx]);
      }
    }
  }
}

static void compact_kernel_all(CompactEpOutputDft *out,
    TorusPolynomial *source_shared, TorusPolynomial *source_body,
    CompactEpSelectorDft sel, CompactEpScratch scratch) {
  for (int q = 0; q < sel->r; q++) {
    compact_ep_kernel_dft_api(out[q], source_shared[q], source_body[q], sel, q, scratch);
  }
}

static void dense_decomp_dft_only(DFT_Polynomial *digits,
    TorusPolynomial *source, int m, int T, int Bg_bit, CompactEpScratch scratch) {
  for (int t = 0; t < T; t++) {
    for (int c = 0; c < m; c++) {
      const int idx = t * m + c;
      polynomial_decompose_i(scratch->dec_shared, source[c], Bg_bit, T, t);
      polynomial_torus_to_DFT(digits[idx], scratch->dec_shared);
    }
  }
}

static void compact_decomp_dft_only(DFT_Polynomial *digits_shared,
    DFT_Polynomial *digits_body, TorusPolynomial *source_shared,
    TorusPolynomial *source_body, int r, int T, int Bg_bit,
    CompactEpScratch scratch) {
  for (int t = 0; t < T; t++) {
    for (int q = 0; q < r; q++) {
      const int idx = t * r + q;
      polynomial_decompose_i(scratch->dec_shared, source_shared[q], Bg_bit, T, t);
      polynomial_torus_to_DFT(digits_shared[idx], scratch->dec_shared);
      polynomial_decompose_i(scratch->dec_body, source_body[q], Bg_bit, T, t);
      polynomial_torus_to_DFT(digits_body[idx], scratch->dec_body);
    }
  }
}

static void dense_addmul_only(DFT_Polynomial *out, DFT_Polynomial *digits,
    DFT_Polynomial *dense_rows, int m, int T) {
  for (int o = 0; o < m; o++) zero_dft(out[o]);
  for (int t = 0; t < T; t++) {
    for (int c = 0; c < m; c++) {
      const int didx = t * m + c;
      for (int o = 0; o < m; o++) {
        const int ridx = (t * m + c) * m + o;
        polynomial_mul_addto_DFT(out[o], digits[didx], dense_rows[ridx]);
      }
    }
  }
}

static void compact_addmul_only(CompactEpOutputDft *out,
    DFT_Polynomial *digits_shared, DFT_Polynomial *digits_body,
    CompactEpSelectorDft sel) {
  for (int q = 0; q < sel->r; q++) {
    zero_dft(out[q]->a);
    zero_dft(out[q]->b);
  }
  for (int t = 0; t < sel->T; t++) {
    for (int q = 0; q < sel->r; q++) {
      const int idx = t * sel->r + q;
      polynomial_mul_addto_DFT(out[q]->a, digits_shared[idx], sel->shared_a[idx]);
      polynomial_mul_addto_DFT(out[q]->b, digits_shared[idx], sel->shared_b[idx]);
      polynomial_mul_addto_DFT(out[q]->a, digits_body[idx], sel->body_a[idx]);
      polynomial_mul_addto_DFT(out[q]->b, digits_body[idx], sel->body_b[idx]);
    }
  }
}

static void print_bench_row(int r, int N, int T, int k, int Bg_bit, int seed,
    int sample, int reps, int warmups, const char *variant, uint64_t total_ns,
    int lanes) {
  const double avg_us = ((double)total_ns / (double)reps) / 1000.0;
  const double per_lane_us = avg_us / (double)lanes;
  printf("BENCH,%s,%d,%d,%d,%d,%d,%d,%d,%d,%d,%s,%" PRIu64 ",%.6f,%.6f,%s\n",
      STAGE128_BACKEND, r, N, T, k, Bg_bit, seed, sample, reps, warmups,
      variant, total_ns, avg_us, per_lane_us, "PASS_BENCH_ROW");
}

static void bench_case(int r, int N, int T, int k, int Bg_bit, int seed,
    int samples, int reps, int warmups) {
  const int rows = T * r;
  const int m = k + r;
  const int dense_row_count = T * m * m;
  const int dense_digit_count = T * m;
  const int compact_digit_count = T * r;
  const int exp = (seed * 19 + r + 11) & (N - 1);
  const int64_t monomial = (seed & 1) ? -1 : 1;

  TorusPolynomial *secret = new_poly_array(r, N);
  TorusPolynomial *source_shared = new_poly_array(r, N);
  TorusPolynomial *source_body = new_poly_array(r, N);
  TorusPolynomial *dense_source = new_poly_array(m, N);
  TorusPolynomial *shared_a = new_poly_array(rows, N);
  TorusPolynomial *shared_b = new_poly_array(rows, N);
  TorusPolynomial *body_a = new_poly_array(rows, N);
  TorusPolynomial *body_b = new_poly_array(rows, N);
  TorusPolynomial noise = polynomial_new_torus_polynomial(N);
  TorusPolynomial gadget = polynomial_new_torus_polynomial(N);

  CompactEpSelectorDft sel = compact_ep_selector_dft_alloc(T, Bg_bit, k, r, N);
  CompactEpScratch scratch = compact_ep_scratch_alloc(N);
  CompactEpOutputDft *compact_out =
      (CompactEpOutputDft *)safe_malloc(sizeof(CompactEpOutputDft) * r);
  for (int q = 0; q < r; q++) compact_out[q] = compact_ep_output_dft_alloc(N);

  DFT_Polynomial *dense_rows = new_dft_array_api(dense_row_count, N);
  DFT_Polynomial *dense_out = new_dft_array_api(m, N);
  DFT_Polynomial *dense_digits = new_dft_array_api(dense_digit_count, N);
  DFT_Polynomial *compact_digits_shared = new_dft_array_api(compact_digit_count, N);
  DFT_Polynomial *compact_digits_body = new_dft_array_api(compact_digit_count, N);

  for (int q = 0; q < r; q++) {
    fill_secret(secret[q], q, seed);
    fill_source(source_shared[q], q, 0, seed);
    fill_source(source_body[q], q, 1, seed);
  }
  fill_source(dense_source[0], 0, 0, seed);
  for (int q = 0; q < r; q++) {
    for (int i = 0; i < N; i++) dense_source[1 + q]->coeffs[i] = source_body[q]->coeffs[i];
  }
  zero_poly(noise);
  for (int t = 0; t < T; t++) {
    make_gadget(gadget, t, Bg_bit, exp, monomial);
    for (int q = 0; q < r; q++) {
      const int idx = t * r + q;
      encrypt_row(shared_a[idx], shared_b[idx], secret[q], gadget, noise,
          q, t, 0, seed);
      encrypt_row(body_a[idx], body_b[idx], secret[q], gadget, noise,
          q, t, 1, seed);
      compact_ep_selector_set_row_from_torus(sel, t, q, shared_a[idx],
          shared_b[idx], body_a[idx], body_b[idx]);
    }
  }
  fill_dense_rows(dense_rows, m, T, N, seed);
  dense_decomp_dft_only(dense_digits, dense_source, m, T, Bg_bit, scratch);
  compact_decomp_dft_only(compact_digits_shared, compact_digits_body,
      source_shared, source_body, r, T, Bg_bit, scratch);

  for (int sample = 0; sample < samples; sample++) {
    uint64_t start = 0;
    uint64_t total = 0;

    for (int i = 0; i < warmups; i++) {
      dense_kernel_all(dense_out, dense_source, dense_rows, m, T, Bg_bit, scratch);
    }
    start = stage129_now_ns();
    for (int i = 0; i < reps; i++) {
      dense_kernel_all(dense_out, dense_source, dense_rows, m, T, Bg_bit, scratch);
    }
    total = stage129_now_ns() - start;
    consume_dft_array(dense_out, m);
    print_bench_row(r, N, T, k, Bg_bit, seed, sample, reps, warmups,
        "dense_all_proxy", total, r);

    for (int i = 0; i < warmups; i++) {
      compact_kernel_all(compact_out, source_shared, source_body, sel, scratch);
    }
    start = stage129_now_ns();
    for (int i = 0; i < reps; i++) {
      compact_kernel_all(compact_out, source_shared, source_body, sel, scratch);
    }
    total = stage129_now_ns() - start;
    consume_compact_outputs(compact_out, r);
    print_bench_row(r, N, T, k, Bg_bit, seed, sample, reps, warmups,
        "compact_all_lanes", total, r);

    for (int i = 0; i < warmups; i++) {
      dense_decomp_dft_only(dense_digits, dense_source, m, T, Bg_bit, scratch);
    }
    start = stage129_now_ns();
    for (int i = 0; i < reps; i++) {
      dense_decomp_dft_only(dense_digits, dense_source, m, T, Bg_bit, scratch);
    }
    total = stage129_now_ns() - start;
    consume_dft_array(dense_digits, dense_digit_count);
    print_bench_row(r, N, T, k, Bg_bit, seed, sample, reps, warmups,
        "dense_decomp_dft_proxy", total, r);

    for (int i = 0; i < warmups; i++) {
      compact_decomp_dft_only(compact_digits_shared, compact_digits_body,
          source_shared, source_body, r, T, Bg_bit, scratch);
    }
    start = stage129_now_ns();
    for (int i = 0; i < reps; i++) {
      compact_decomp_dft_only(compact_digits_shared, compact_digits_body,
          source_shared, source_body, r, T, Bg_bit, scratch);
    }
    total = stage129_now_ns() - start;
    consume_dft_array(compact_digits_shared, compact_digit_count);
    consume_dft_array(compact_digits_body, compact_digit_count);
    print_bench_row(r, N, T, k, Bg_bit, seed, sample, reps, warmups,
        "compact_decomp_dft", total, r);

    for (int i = 0; i < warmups; i++) {
      dense_addmul_only(dense_out, dense_digits, dense_rows, m, T);
    }
    start = stage129_now_ns();
    for (int i = 0; i < reps; i++) {
      dense_addmul_only(dense_out, dense_digits, dense_rows, m, T);
    }
    total = stage129_now_ns() - start;
    consume_dft_array(dense_out, m);
    print_bench_row(r, N, T, k, Bg_bit, seed, sample, reps, warmups,
        "dense_addmul_proxy", total, r);

    for (int i = 0; i < warmups; i++) {
      compact_addmul_only(compact_out, compact_digits_shared, compact_digits_body, sel);
    }
    start = stage129_now_ns();
    for (int i = 0; i < reps; i++) {
      compact_addmul_only(compact_out, compact_digits_shared, compact_digits_body, sel);
    }
    total = stage129_now_ns() - start;
    consume_compact_outputs(compact_out, r);
    print_bench_row(r, N, T, k, Bg_bit, seed, sample, reps, warmups,
        "compact_addmul", total, r);
  }

  free_dft_array_api(compact_digits_body, compact_digit_count);
  free_dft_array_api(compact_digits_shared, compact_digit_count);
  free_dft_array_api(dense_digits, dense_digit_count);
  free_dft_array_api(dense_out, m);
  free_dft_array_api(dense_rows, dense_row_count);
  for (int q = 0; q < r; q++) compact_ep_output_dft_free(compact_out[q]);
  free(compact_out);
  compact_ep_scratch_free(scratch);
  compact_ep_selector_dft_free(sel);
  free_poly_array_local(secret, r);
  free_poly_array_local(source_shared, r);
  free_poly_array_local(source_body, r);
  free_poly_array_local(dense_source, m);
  free_poly_array_local(shared_a, rows);
  free_poly_array_local(shared_b, rows);
  free_poly_array_local(body_a, rows);
  free_poly_array_local(body_b, rows);
  free_polynomial(noise);
  free_polynomial(gadget);
}

int main(void) {
  const int k = 1;
  const int T = 7;
  const int Bg_bit = 7;
  const int samples = 5;
  const int reps = 6;
  const int warmups = 1;

  run_case(2, 512, T, k, Bg_bit, 0);
  run_case(4, 512, T, k, Bg_bit, 0);
  run_case(6, 512, T, k, Bg_bit, 0);
  run_case(2, 1024, T, k, Bg_bit, 0);
  run_case(4, 1024, T, k, Bg_bit, 0);
  run_case(6, 1024, T, k, Bg_bit, 0);

  bench_case(2, 512, T, k, Bg_bit, 0, samples, reps, warmups);
  bench_case(4, 512, T, k, Bg_bit, 0, samples, reps, warmups);
  bench_case(6, 512, T, k, Bg_bit, 0, samples, reps, warmups);
  bench_case(2, 1024, T, k, Bg_bit, 0, samples, reps, warmups);
  bench_case(4, 1024, T, k, Bg_bit, 0, samples, reps, warmups);
  bench_case(6, 1024, T, k, Bg_bit, 0, samples, reps, warmups);

  fprintf(stderr, "stage129_sink=%f\n", g_stage129_sink);
  return 0;
}
'''
    write_text_lf(C_SOURCE, prefix + bench.lstrip())


def build_mosfhet_static(backend: str) -> bool:
    cmd = (
        "cd src/mosfhet && "
        "make clean >/dev/null 2>&1 || true && "
        f"make static FFT_LIB={backend} A_PRNG=none ENABLE_VAES=false "
        "ENABLE_PVW_TMLWE=false -j$(nproc)"
    )
    proc = bash(cmd, timeout=180)
    log = [
        f"command: {cmd}",
        f"returncode: {proc.returncode}",
        "--- stdout ---",
        sanitize_log(proc.stdout),
        "--- stderr ---",
        sanitize_log(proc.stderr),
    ]
    write_text_lf(BUILD_LOG, "\n".join(log) + "\n")
    return proc.returncode == 0


def compile_probe(backend: str) -> bool:
    cmd = (
        f"gcc -O2 -DSTAGE128_BACKEND=\\\"{backend}\\\" "
        f"-I {rel(MOSFHET_DIR / 'include')} "
        f"-o {rel(C_BINARY)} {rel(C_SOURCE)} "
        f"{rel(MOSFHET_DIR / 'lib' / 'libmosfhet.a')} -lm"
    )
    proc = bash(cmd, timeout=60)
    log = [
        f"command: {cmd}",
        f"returncode: {proc.returncode}",
        "--- stdout ---",
        sanitize_log(proc.stdout),
        "--- stderr ---",
        sanitize_log(proc.stderr),
    ]
    write_text_lf(COMPILE_LOG, "\n".join(log) + "\n")
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
        line = line.strip()
        if not line:
            continue
        parts = line.split(",")
        if parts[0] == "API" and len(parts) == 22:
            api_rows.append(dict(zip(API_FIELDS, parts[1:])))
        elif parts[0] == "BENCH" and len(parts) == 16:
            bench_rows.append(dict(zip(BENCH_FIELDS, parts[1:])))
    return api_rows, bench_rows


def run_probe(build_ok: bool, compile_ok: bool) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], bool]:
    if not build_ok or not compile_ok:
        cleanup_build_outputs()
        return [], [], False
    proc = bash(f"./{rel(C_BINARY)}", timeout=180)
    log = [
        f"command: ./{rel(C_BINARY)}",
        f"returncode: {proc.returncode}",
        "--- stdout ---",
        sanitize_log(proc.stdout),
        "--- stderr ---",
        sanitize_log(proc.stderr),
    ]
    write_text_lf(RUN_LOG_TXT, "\n".join(log) + "\n")
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
        dense_total_terms = dense_dft_terms + dense_dec_terms
        compact_total_terms = compact_dft_terms + compact_dec_terms
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
        if full_speedup >= 1.0:
            decision = "POSITIVE_COMPACT_FASTER_THAN_DENSE_PROXY"
        else:
            decision = "NEGATIVE_COMPACT_NOT_FASTER_THAN_DENSE_PROXY"
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
                "total_term_ratio": f"{dense_total_terms / compact_total_terms:.6f}",
                "decision": decision,
            }
        )
    return ratios


def all_api_pass(api_rows: List[Dict[str, str]]) -> bool:
    if not api_rows:
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


def microbench_positive(ratio_rows: List[Dict[str, str]]) -> bool:
    target = [row for row in ratio_rows if row["r"] in {"4", "6"}]
    return bool(target) and all(float(row["full_speedup"]) >= 1.0 for row in target)


def min_ratio(ratio_rows: List[Dict[str, str]], field: str, r_filter: set[str] | None = None) -> str:
    rows = [row for row in ratio_rows if r_filter is None or row["r"] in r_filter]
    if not rows:
        return ""
    return f"{min(float(row[field]) for row in rows):.6f}"


def max_ratio(ratio_rows: List[Dict[str, str]], field: str, r_filter: set[str] | None = None) -> str:
    rows = [row for row in ratio_rows if r_filter is None or row["r"] in r_filter]
    if not rows:
        return ""
    return f"{max(float(row[field]) for row in rows):.6f}"


def build_summary(
    build_ok: bool,
    compile_ok: bool,
    run_ok: bool,
    api_rows: List[Dict[str, str]],
    bench_rows: List[Dict[str, str]],
    ratio_rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    correctness_ok = all_api_pass(api_rows)
    bench_ok = bool(bench_rows) and bool(ratio_rows)
    positive = microbench_positive(ratio_rows)
    if not (build_ok and compile_ok and run_ok and correctness_ok and bench_ok):
        decision = "FAIL_STAGE129_COMPACT_EP_MICROBENCH_GATE"
    elif positive:
        decision = "PASS_STAGE129_COMPACT_EP_MICROBENCH_POSITIVE_PRODUCTION_API_REQUIRED"
    else:
        decision = "NEUTRAL_STAGE129_COMPACT_EP_MICROBENCH_NOT_PROMOTED"
    rows = [
        {
            "gate": "stage129_mosfhet_static_build",
            "status": "PASS" if build_ok else "FAIL",
            "metric": "make_static_spqlios",
            "value": str(build_ok).lower(),
            "evidence": rel(BUILD_LOG),
            "detail": "MOSFHET static library build using FFT_LIB=spqlios.",
            "next_action": "Fix build before microbench." if not build_ok else "",
        },
        {
            "gate": "stage129_probe_compile",
            "status": "PASS" if compile_ok else "FAIL",
            "metric": "gcc_probe_compile",
            "value": str(compile_ok).lower(),
            "evidence": rel(COMPILE_LOG),
            "detail": "Standalone compact EP microbench probe linked against libmosfhet.a.",
            "next_action": "Fix compile before interpreting performance." if not compile_ok else "",
        },
        {
            "gate": "stage129_probe_run",
            "status": "PASS" if run_ok else "FAIL",
            "metric": "probe_returncode",
            "value": "0" if run_ok else "nonzero_or_skipped",
            "evidence": rel(RUN_LOG_TXT),
            "detail": "Compact EP microbench probe executed.",
            "next_action": "Fix runtime failure before interpreting performance." if not run_ok else "",
        },
        {
            "gate": "stage129_api_correctness_guard",
            "status": "PASS" if correctness_ok else "FAIL",
            "metric": "api_rows",
            "value": str(len(api_rows)),
            "evidence": rel(API_CSV),
            "detail": "Stage128 API correctness gate is replayed before timing.",
            "next_action": "Do not interpret timing until correctness replay passes." if not correctness_ok else "",
        },
        {
            "gate": "stage129_microbench_rows",
            "status": "PASS" if bench_ok else "FAIL",
            "metric": "bench_rows;ratio_rows",
            "value": f"{len(bench_rows)};{len(ratio_rows)}",
            "evidence": f"{rel(BENCH_CSV)}; {rel(RATIO_CSV)}",
            "detail": "Dense-count proxy and compact all-lane samples were recorded.",
            "next_action": "Fix benchmark harness if rows are missing." if not bench_ok else "",
        },
        {
            "gate": "stage129_full_microbench_signal",
            "status": "PASS_POSITIVE" if positive else ("NEUTRAL_OR_NEGATIVE" if bench_ok else "FAIL"),
            "metric": "min_full_speedup_r4_r6;max_full_speedup_all",
            "value": f"{min_ratio(ratio_rows, 'full_speedup', {'4', '6'})};{max_ratio(ratio_rows, 'full_speedup')}",
            "evidence": rel(RATIO_CSV),
            "detail": "Mean dense_all_proxy / compact_all_lanes timing ratio.",
            "next_action": "Proceed to production API design only if positive; otherwise record neutral and redesign.",
        },
        {
            "gate": "stage129_attribution_signal",
            "status": "RECORDED",
            "metric": "min_decomp_speedup;min_addmul_speedup",
            "value": f"{min_ratio(ratio_rows, 'decomp_dft_speedup')};{min_ratio(ratio_rows, 'addmul_speedup')}",
            "evidence": rel(RATIO_CSV),
            "detail": "Separate decomposition/DFT and DFT addmul timing attribution.",
            "next_action": "Use attribution to decide whether the bottleneck is decomposition/DFT or multiply-add.",
        },
        {
            "gate": "stage129_decision",
            "status": decision,
            "metric": "promotion_policy",
            "value": "",
            "evidence": f"{rel(SUMMARY_CSV)}; {rel(RATIO_CSV)}",
            "detail": "Stage129 decides only isolated microbench promotion readiness.",
            "next_action": "No SAB integration claim until production API, AVX512, and full SAB gates pass.",
        },
    ]
    return rows


def write_plan() -> None:
    lines = [
        "# Stage129 Compact EP Microbench Gate Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Benchmark the Stage128 API-shaped compact EP kernel in isolation and",
        "attribute time to full kernel, decomposition/DFT, and DFT multiply-add.",
        "This stage remains outside production MOSFHET headers and outside SAB.",
        "",
        "## Command",
        "",
        "```bash",
        "python scripts/build_stage129_compact_ep_microbench_gate.py",
        "```",
        "",
        "## Falsification Criteria",
        "",
        "- MOSFHET build or probe compile fails;",
        "- Stage128 API correctness replay fails;",
        "- benchmark rows are missing;",
        "- r=4/r=6 compact all-lane timing does not beat the dense-count proxy.",
        "",
        "A negative timing result is recorded as neutral/rejected evidence rather",
        "than treated as a theory blocker.",
    ]
    write_text_lf(PLAN_MD, "\n".join(lines) + "\n")


def ratio_table(ratio_rows: List[Dict[str, str]]) -> List[str]:
    lines = [
        "| r | N | dense all us | compact all us | full speedup | decomp/DFT speedup | addmul speedup | DFT term ratio | total term ratio | decision |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in ratio_rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['dense_all_mean_us']} | "
            f"{row['compact_all_mean_us']} | {row['full_speedup']} | "
            f"{row['decomp_dft_speedup']} | {row['addmul_speedup']} | "
            f"{row['dft_term_ratio']} | {row['total_term_ratio']} | {row['decision']} |"
        )
    return lines


def write_theory(ratio_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage129 Compact EP Microbench Model",
        "",
        "Date: 2026-07-03",
        "",
        "Stage129 uses an isolated dense-count proxy and the Stage128 compact",
        "all-lane API kernel. The dense proxy is a cost proxy for current dense",
        "`(k+r)^2` DFT multiply-add work, not a complete SAB or production key-format",
        "benchmark. Compact timing is measured over all r lanes, so the endpoint is",
        "compatible with the amortized `T_kernel/r` lens.",
        "",
        "## Count Model",
        "",
        "For k=1 and gadget level T:",
        "",
        "```text",
        "dense_dft_terms   = T * (k+r)^2",
        "compact_dft_terms = 4 * T * r",
        "dense_total_terms = dense_dft_terms + T * (k+r)",
        "compact_total     = compact_dft_terms + 2 * T * r",
        "```",
        "",
        "The timing gate separately records full kernel, decomposition/DFT-only,",
        "and DFT-addmul-only measurements.",
        "",
        "## Results",
        "",
        *ratio_table(ratio_rows),
        "",
        "## Boundary",
        "",
        "This is isolated microbench evidence only. It is not AVX512 theoretical",
        "optimality, production MOSFHET API evidence, SAB schedule integration,",
        "randomized noise/failure-rate evidence, or complete `T_bootstrap/r` timing.",
    ]
    write_text_lf(THEORY_MD, "\n".join(lines) + "\n")


def write_variant(decision: str) -> None:
    lines = [
        "# V129: Compact EP Isolated Microbench",
        "",
        "## Summary",
        "",
        "- Parent algorithm: PVW/MAT-SAB r-body research track.",
        "- Focused module: isolated compact EP all-lane timing.",
        "- Optimization target: eventual complete-SAB `T_bootstrap/r`.",
        "- Status labels: `[microbench]`, `[production-dft-linked]`, `[not-production-header]`, `[not-hot-path]`.",
        f"- Decision: `{decision}`.",
        "",
        "## Interpretation Rules",
        "",
        "- Promote only toward production API design if r=4/r=6 compact all-lane",
        "  timing beats the dense-count proxy.",
        "- If only addmul wins but full timing loses, the next hypothesis must target",
        "  decomposition/DFT reuse or streaming.",
        "- If full timing wins, Stage130 may design a production-header API gate, still",
        "  without changing scalar/default SAB.",
    ]
    write_text_lf(VARIANT_MD, "\n".join(lines) + "\n")


def write_md(summary: List[Dict[str, str]], ratio_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage129 Compact EP Microbench Gate",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{summary[-1]['status']}`",
        "",
        "Stage129 benchmarks the Stage128 API-shaped compact EP kernel in isolation",
        "against a dense-count proxy. It remains outside production headers and",
        "`sab_pvw_*`.",
        "",
        "## Gates",
        "",
        "| gate | status | metric | value | detail |",
        "|---|---|---|---|---|",
    ]
    for row in summary:
        lines.append(
            f"| {row['gate']} | {row['status']} | {row['metric']} | "
            f"{row['value']} | {row['detail']} |"
        )
    lines += [
        "",
        "## Ratio Summary",
        "",
        *ratio_table(ratio_rows),
        "",
        "## Interpretation",
        "",
        "The benchmark endpoint is all r compact lanes versus a dense-count proxy.",
        "The valid downstream use is production API or kernel design only if the",
        "microbench signal is positive. Complete SAB acceleration still requires",
        "later full `T_bootstrap/r` A/B, correctness, noise, and resource gates.",
    ]
    write_text_lf(OUT_MD, "\n".join(lines) + "\n")


def write_artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
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
    run_id = "stage129-compact-ep-microbench-001"
    rows = read_csv(RUN_LOG)
    rows = [row for row in rows if row.get("run_id") != run_id]
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
        BUILD_LOG,
        COMPILE_LOG,
        RUN_LOG_TXT,
        C_SOURCE,
        ARTIFACT_INDEX,
        Path("scripts/build_stage129_compact_ep_microbench_gate.py"),
    ]
    rows.append(
        {
            "run_id": run_id,
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 129",
            "backend": "MOSFHET FFT_LIB=spqlios",
            "command": "python scripts/build_stage129_compact_ep_microbench_gate.py",
            "params": "k=1 T=7 Bg_bit=7 r=2,4,6 N=512,1024 samples=5 reps=6",
            "seed": "0 subset",
            "status": status,
            "summary": "Stage129 records isolated compact EP microbench/profiling outside SAB.",
            "artifacts": "; ".join(rel(p if p.is_absolute() else ROOT / p) for p in artifacts),
        }
    )
    write_csv(RUN_LOG, rows, fields)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    backend = "spqlios"
    write_c_source()
    build_ok = build_mosfhet_static(backend)
    compile_ok = compile_probe(backend) if build_ok else False
    api_rows, bench_rows, run_ok = run_probe(build_ok, compile_ok)
    agg_rows = aggregate_bench(bench_rows)
    ratio_rows = build_ratio_rows(agg_rows)
    write_csv(API_CSV, api_rows, API_FIELDS)
    write_csv(BENCH_CSV, bench_rows, BENCH_FIELDS)
    write_csv(AGG_CSV, agg_rows, AGG_FIELDS)
    write_csv(RATIO_CSV, ratio_rows, RATIO_FIELDS)
    summary = build_summary(build_ok, compile_ok, run_ok, api_rows, bench_rows, ratio_rows)
    write_csv(
        SUMMARY_CSV,
        summary,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    status = summary[-1]["status"]
    write_plan()
    write_theory(ratio_rows)
    write_variant(status)
    write_md(summary, ratio_rows)
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
        BUILD_LOG,
        COMPILE_LOG,
        RUN_LOG_TXT,
        C_SOURCE,
        Path(__file__),
    ]
    write_artifact_index(artifacts)
    upsert_run_log(status)
    print(f"Stage129 compact EP microbench gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if status.startswith("PASS_") or status.startswith("NEUTRAL_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
