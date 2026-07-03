#!/usr/bin/env python3
"""Build Stage130 shared-source compact EP gate."""

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
OUT_DIR = ROOT / "repro" / "stage130_shared_source_compact_ep_gate"
SUMMARY_CSV = OUT_DIR / "summary.csv"
API_CSV = OUT_DIR / "api_results.csv"
BENCH_CSV = OUT_DIR / "benchmark_samples.csv"
AGG_CSV = OUT_DIR / "benchmark_aggregate.csv"
RATIO_CSV = OUT_DIR / "ratio_summary.csv"
BUILD_LOG = OUT_DIR / "mosfhet_static_build.log"
COMPILE_LOG = OUT_DIR / "compile_probe.log"
RUN_LOG_TXT = OUT_DIR / "run_probe.log"
C_SOURCE = OUT_DIR / "shared_source_compact_ep_gate.c"
C_BINARY = OUT_DIR / "shared_source_compact_ep_gate"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage130_shared_source_compact_ep_gate.md"
PLAN_MD = ROOT / "experiments" / "stage130_shared_source_compact_ep_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage130_shared_source_compact_ep_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_shared_source_compact_ep.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"


API_FIELDS = [
    "backend",
    "r",
    "N",
    "T",
    "k",
    "Bg_bit",
    "seed",
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
    "compact_shared_all_mean_us",
    "full_speedup",
    "dense_decomp_dft_mean_us",
    "compact_shared_decomp_dft_mean_us",
    "decomp_dft_speedup",
    "dense_addmul_mean_us",
    "compact_shared_addmul_mean_us",
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
    prefix = base[:pos].replace("#include <string.h>\n", "#include <string.h>\n#include <time.h>\n")
    body = r'''
#ifndef CLOCK_MONOTONIC_RAW
#define CLOCK_MONOTONIC_RAW CLOCK_MONOTONIC
#endif

static volatile double g_stage130_sink = 0.0;

static uint64_t now_ns_stage130(void) {
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
  return ((uint64_t)ts.tv_sec * 1000000000ULL) + (uint64_t)ts.tv_nsec;
}

static DFT_Polynomial *new_dft_array_api_stage130(int count, int N) {
  DFT_Polynomial *out = (DFT_Polynomial *)safe_malloc(sizeof(DFT_Polynomial) * count);
  for (int i = 0; i < count; i++) out[i] = api_new_dft_polynomial(N);
  return out;
}

static void free_dft_array_api_stage130(DFT_Polynomial *in, int count) {
  for (int i = 0; i < count; i++) api_free_dft_polynomial(in[i]);
  free(in);
}

static void consume_dft_array_stage130(DFT_Polynomial *arr, int count) {
  double s = 0.0;
  for (int i = 0; i < count; i++) s += arr[i]->coeffs[(i * 17) & (arr[i]->N - 1)];
  g_stage130_sink += s;
}

static void consume_outputs_stage130(CompactEpOutputDft *out, int r) {
  double s = 0.0;
  for (int q = 0; q < r; q++) {
    const int idx = (q * 19) & (out[q]->N - 1);
    s += out[q]->a->coeffs[idx] + out[q]->b->coeffs[idx];
  }
  g_stage130_sink += s;
}

static void fill_dense_rows_stage130(DFT_Polynomial *dense_rows, int m, int T,
    int N, int seed) {
  TorusPolynomial tmp = polynomial_new_torus_polynomial(N);
  for (int t = 0; t < T; t++) {
    for (int c = 0; c < m; c++) {
      for (int o = 0; o < m; o++) {
        fill_small_mask(tmp, c, t, o, seed + 2000);
        polynomial_torus_to_DFT(dense_rows[(t * m + c) * m + o], tmp);
      }
    }
  }
  free_polynomial(tmp);
}

static void dense_kernel_all_stage130(DFT_Polynomial *out,
    TorusPolynomial *source, DFT_Polynomial *dense_rows, int m, int T,
    int Bg_bit, CompactEpScratch scratch) {
  for (int o = 0; o < m; o++) zero_dft(out[o]);
  for (int t = 0; t < T; t++) {
    for (int c = 0; c < m; c++) {
      polynomial_decompose_i(scratch->dec_shared, source[c], Bg_bit, T, t);
      polynomial_torus_to_DFT(scratch->dec_shared_dft, scratch->dec_shared);
      for (int o = 0; o < m; o++) {
        polynomial_mul_addto_DFT(out[o], scratch->dec_shared_dft,
            dense_rows[(t * m + c) * m + o]);
      }
    }
  }
}

static void compact_shared_all_lanes(CompactEpOutputDft *out,
    TorusPolynomial source_shared, TorusPolynomial *source_body,
    CompactEpSelectorDft sel, CompactEpScratch scratch) {
  for (int q = 0; q < sel->r; q++) {
    zero_dft(out[q]->a);
    zero_dft(out[q]->b);
  }
  for (int t = 0; t < sel->T; t++) {
    polynomial_decompose_i(scratch->dec_shared, source_shared, sel->Bg_bit, sel->T, t);
    polynomial_torus_to_DFT(scratch->dec_shared_dft, scratch->dec_shared);
    for (int q = 0; q < sel->r; q++) {
      const int idx = t * sel->r + q;
      polynomial_decompose_i(scratch->dec_body, source_body[q], sel->Bg_bit, sel->T, t);
      polynomial_torus_to_DFT(scratch->dec_body_dft, scratch->dec_body);
      polynomial_mul_addto_DFT(out[q]->a, scratch->dec_shared_dft, sel->shared_a[idx]);
      polynomial_mul_addto_DFT(out[q]->b, scratch->dec_shared_dft, sel->shared_b[idx]);
      polynomial_mul_addto_DFT(out[q]->a, scratch->dec_body_dft, sel->body_a[idx]);
      polynomial_mul_addto_DFT(out[q]->b, scratch->dec_body_dft, sel->body_b[idx]);
    }
  }
}

static void compact_shared_body_only_all(CompactEpOutputDft *out,
    TorusPolynomial *source_body, CompactEpSelectorDft sel,
    CompactEpScratch scratch) {
  for (int q = 0; q < sel->r; q++) {
    zero_dft(out[q]->a);
    zero_dft(out[q]->b);
  }
  for (int t = 0; t < sel->T; t++) {
    for (int q = 0; q < sel->r; q++) {
      const int idx = t * sel->r + q;
      polynomial_decompose_i(scratch->dec_body, source_body[q], sel->Bg_bit, sel->T, t);
      polynomial_torus_to_DFT(scratch->dec_body_dft, scratch->dec_body);
      polynomial_mul_addto_DFT(out[q]->a, scratch->dec_body_dft, sel->body_a[idx]);
      polynomial_mul_addto_DFT(out[q]->b, scratch->dec_body_dft, sel->body_b[idx]);
    }
  }
}

static void dense_decomp_dft_stage130(DFT_Polynomial *digits,
    TorusPolynomial *source, int m, int T, int Bg_bit, CompactEpScratch scratch) {
  for (int t = 0; t < T; t++) {
    for (int c = 0; c < m; c++) {
      const int idx = t * m + c;
      polynomial_decompose_i(scratch->dec_shared, source[c], Bg_bit, T, t);
      polynomial_torus_to_DFT(digits[idx], scratch->dec_shared);
    }
  }
}

static void compact_shared_decomp_dft(DFT_Polynomial *digits_shared,
    DFT_Polynomial *digits_body, TorusPolynomial source_shared,
    TorusPolynomial *source_body, int r, int T, int Bg_bit,
    CompactEpScratch scratch) {
  for (int t = 0; t < T; t++) {
    polynomial_decompose_i(scratch->dec_shared, source_shared, Bg_bit, T, t);
    polynomial_torus_to_DFT(digits_shared[t], scratch->dec_shared);
    for (int q = 0; q < r; q++) {
      const int idx = t * r + q;
      polynomial_decompose_i(scratch->dec_body, source_body[q], Bg_bit, T, t);
      polynomial_torus_to_DFT(digits_body[idx], scratch->dec_body);
    }
  }
}

static void dense_addmul_stage130(DFT_Polynomial *out, DFT_Polynomial *digits,
    DFT_Polynomial *dense_rows, int m, int T) {
  for (int o = 0; o < m; o++) zero_dft(out[o]);
  for (int t = 0; t < T; t++) {
    for (int c = 0; c < m; c++) {
      const int didx = t * m + c;
      for (int o = 0; o < m; o++) {
        polynomial_mul_addto_DFT(out[o], digits[didx],
            dense_rows[(t * m + c) * m + o]);
      }
    }
  }
}

static void compact_shared_addmul(CompactEpOutputDft *out,
    DFT_Polynomial *digits_shared, DFT_Polynomial *digits_body,
    CompactEpSelectorDft sel) {
  for (int q = 0; q < sel->r; q++) {
    zero_dft(out[q]->a);
    zero_dft(out[q]->b);
  }
  for (int t = 0; t < sel->T; t++) {
    for (int q = 0; q < sel->r; q++) {
      const int idx = t * sel->r + q;
      polynomial_mul_addto_DFT(out[q]->a, digits_shared[t], sel->shared_a[idx]);
      polynomial_mul_addto_DFT(out[q]->b, digits_shared[t], sel->shared_b[idx]);
      polynomial_mul_addto_DFT(out[q]->a, digits_body[idx], sel->body_a[idx]);
      polynomial_mul_addto_DFT(out[q]->b, digits_body[idx], sel->body_b[idx]);
    }
  }
}

static void print_bench_stage130(int r, int N, int T, int k, int Bg_bit,
    int seed, int sample, int reps, int warmups, const char *variant,
    uint64_t total_ns) {
  const double avg_us = ((double)total_ns / (double)reps) / 1000.0;
  printf("BENCH,%s,%d,%d,%d,%d,%d,%d,%d,%d,%d,%s,%" PRIu64 ",%.6f,%.6f,%s\n",
      STAGE128_BACKEND, r, N, T, k, Bg_bit, seed, sample, reps, warmups,
      variant, total_ns, avg_us, avg_us / (double)r, "PASS_BENCH_ROW");
}

static void run_shared_source_case(int r, int N, int T, int k, int Bg_bit,
    int seed) {
  const uint64_t tol = 131072;
  const int rows = T * r;
  const int exp = (seed * 19 + r + 11) & (N - 1);
  const int64_t monomial = (seed & 1) ? -1 : 1;

  TorusPolynomial *secret = new_poly_array(r, N);
  TorusPolynomial source_shared = polynomial_new_torus_polynomial(N);
  TorusPolynomial *source_body = new_poly_array(r, N);
  TorusPolynomial *shared_a = new_poly_array(rows, N);
  TorusPolynomial *shared_b = new_poly_array(rows, N);
  TorusPolynomial *body_a = new_poly_array(rows, N);
  TorusPolynomial *body_b = new_poly_array(rows, N);
  TorusPolynomial *shared_noise = new_poly_array(rows, N);
  TorusPolynomial *body_noise = new_poly_array(rows, N);
  TorusPolynomial gadget = polynomial_new_torus_polynomial(N);
  TorusPolynomial coeff_a = polynomial_new_torus_polynomial(N);
  TorusPolynomial coeff_b = polynomial_new_torus_polynomial(N);
  TorusPolynomial out_a_torus = polynomial_new_torus_polynomial(N);
  TorusPolynomial out_b_torus = polynomial_new_torus_polynomial(N);
  TorusPolynomial coeff_phase = polynomial_new_torus_polynomial(N);
  TorusPolynomial api_phase = polynomial_new_torus_polynomial(N);
  TorusPolynomial expected_clean = polynomial_new_torus_polynomial(N);
  TorusPolynomial expected_noise = polynomial_new_torus_polynomial(N);
  TorusPolynomial expected_noisy = polynomial_new_torus_polynomial(N);
  TorusPolynomial observed_noise = polynomial_new_torus_polynomial(N);
  TorusPolynomial neg_a_torus = polynomial_new_torus_polynomial(N);
  TorusPolynomial neg_b_torus = polynomial_new_torus_polynomial(N);
  TorusPolynomial neg_phase = polynomial_new_torus_polynomial(N);

  CompactEpSelectorDft sel = compact_ep_selector_dft_alloc(T, Bg_bit, k, r, N);
  CompactEpScratch scratch = compact_ep_scratch_alloc(N);
  CompactEpOutputDft *out =
      (CompactEpOutputDft *)safe_malloc(sizeof(CompactEpOutputDft) * r);
  CompactEpOutputDft *neg_out =
      (CompactEpOutputDft *)safe_malloc(sizeof(CompactEpOutputDft) * r);
  for (int q = 0; q < r; q++) {
    out[q] = compact_ep_output_dft_alloc(N);
    neg_out[q] = compact_ep_output_dft_alloc(N);
  }

  fill_source(source_shared, 0, 0, seed);
  for (int q = 0; q < r; q++) {
    fill_secret(secret[q], q, seed);
    fill_source(source_body[q], q, 1, seed);
  }
  for (int t = 0; t < T; t++) {
    make_gadget(gadget, t, Bg_bit, exp, monomial);
    for (int q = 0; q < r; q++) {
      const int idx = t * r + q;
      fill_noise(shared_noise[idx], q, t, 0, seed, 1);
      fill_noise(body_noise[idx], q, t, 1, seed, 1);
      encrypt_row(shared_a[idx], shared_b[idx], secret[q], gadget,
          shared_noise[idx], q, t, 0, seed);
      encrypt_row(body_a[idx], body_b[idx], secret[q], gadget,
          body_noise[idx], q, t, 1, seed);
      compact_ep_selector_set_row_from_torus(sel, t, q, shared_a[idx],
          shared_b[idx], body_a[idx], body_b[idx]);
    }
  }

  compact_shared_all_lanes(out, source_shared, source_body, sel, scratch);
  compact_shared_body_only_all(neg_out, source_body, sel, scratch);

  uint64_t component_mismatches = 0;
  uint64_t phase_mismatches = 0;
  uint64_t noise_model_mismatches = 0;
  uint64_t negative_failures = 0;
  uint64_t max_component_gap = 0;
  uint64_t max_phase_gap = 0;
  uint64_t dummy_gap = 0;
  for (int q = 0; q < r; q++) {
    compact_ep_reference_coeff(coeff_a, coeff_b, source_shared,
        source_body[q], shared_a, shared_b, body_a, body_b, T, r, q, Bg_bit,
        scratch);
    polynomial_DFT_to_torus(out_a_torus, out[q]->a);
    polynomial_DFT_to_torus(out_b_torus, out[q]->b);
    compare_poly(coeff_a, out_a_torus, tol, &component_mismatches, &max_component_gap);
    compare_poly(coeff_b, out_b_torus, tol, &component_mismatches, &max_component_gap);

    zero_poly(expected_clean);
    zero_poly(expected_noise);
    for (int t = 0; t < T; t++) {
      const int idx = t * r + q;
      make_gadget(gadget, t, Bg_bit, exp, monomial);
      polynomial_decompose_i(scratch->dec_shared, source_shared, Bg_bit, T, t);
      polynomial_decompose_i(scratch->dec_body, source_body[q], Bg_bit, T, t);
      polynomial_naive_mul_addto_torus(expected_clean, scratch->dec_shared, gadget);
      polynomial_naive_mul_addto_torus(expected_clean, scratch->dec_body, gadget);
      polynomial_naive_mul_addto_torus(expected_noise, scratch->dec_shared, shared_noise[idx]);
      polynomial_naive_mul_addto_torus(expected_noise, scratch->dec_body, body_noise[idx]);
    }
    for (int i = 0; i < N; i++) {
      expected_noisy->coeffs[i] = expected_clean->coeffs[i] + expected_noise->coeffs[i];
    }
    phase(coeff_phase, coeff_a, coeff_b, secret[q]);
    phase(api_phase, out_a_torus, out_b_torus, secret[q]);
    compare_poly(api_phase, expected_noisy, tol, &phase_mismatches, &max_phase_gap);
    for (int i = 0; i < N; i++) {
      observed_noise->coeffs[i] = coeff_phase->coeffs[i] - expected_clean->coeffs[i];
    }
    compare_poly(observed_noise, expected_noise, 0, &noise_model_mismatches, &dummy_gap);

    polynomial_DFT_to_torus(neg_a_torus, neg_out[q]->a);
    polynomial_DFT_to_torus(neg_b_torus, neg_out[q]->b);
    phase(neg_phase, neg_a_torus, neg_b_torus, secret[q]);
    compare_poly(neg_phase, expected_noisy, 0, &negative_failures, &dummy_gap);
  }

  const uint64_t dense_dft_terms = (uint64_t)T * (uint64_t)(k + r) * (uint64_t)(k + r);
  const uint64_t compact_dft_terms = 4ULL * (uint64_t)T * (uint64_t)r;
  const uint64_t dense_dec_terms = (uint64_t)T * (uint64_t)(k + r);
  const uint64_t compact_dec_terms = (uint64_t)T * (uint64_t)(k + r);
  const double dft_ratio = (double)dense_dft_terms / (double)compact_dft_terms;
  const double total_ratio =
      (double)(dense_dft_terms + dense_dec_terms) /
      (double)(compact_dft_terms + compact_dec_terms);
  const int ok = component_mismatches == 0 && phase_mismatches == 0 &&
      noise_model_mismatches == 0 && negative_failures > 0;
  printf("SHAREDAPI,%s,%d,%d,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%.6f,%.6f,%s\n",
      STAGE128_BACKEND, r, N, T, k, Bg_bit, seed, component_mismatches,
      phase_mismatches, noise_model_mismatches, negative_failures,
      max_component_gap, max_phase_gap, tol, dft_ratio, total_ratio,
      ok ? "PASS_SHARED_SOURCE_COMPACT_EP" : "FAIL");

  for (int q = 0; q < r; q++) {
    compact_ep_output_dft_free(neg_out[q]);
    compact_ep_output_dft_free(out[q]);
  }
  free(neg_out);
  free(out);
  compact_ep_scratch_free(scratch);
  compact_ep_selector_dft_free(sel);
  free_poly_array_local(secret, r);
  free_polynomial(source_shared);
  free_poly_array_local(source_body, r);
  free_poly_array_local(shared_a, rows);
  free_poly_array_local(shared_b, rows);
  free_poly_array_local(body_a, rows);
  free_poly_array_local(body_b, rows);
  free_poly_array_local(shared_noise, rows);
  free_poly_array_local(body_noise, rows);
  free_polynomial(gadget);
  free_polynomial(coeff_a);
  free_polynomial(coeff_b);
  free_polynomial(out_a_torus);
  free_polynomial(out_b_torus);
  free_polynomial(coeff_phase);
  free_polynomial(api_phase);
  free_polynomial(expected_clean);
  free_polynomial(expected_noise);
  free_polynomial(expected_noisy);
  free_polynomial(observed_noise);
  free_polynomial(neg_a_torus);
  free_polynomial(neg_b_torus);
  free_polynomial(neg_phase);
}

static void bench_shared_case(int r, int N, int T, int k, int Bg_bit, int seed,
    int samples, int reps, int warmups) {
  const int rows = T * r;
  const int m = k + r;
  const int dense_row_count = T * m * m;
  const int dense_digit_count = T * m;
  const int body_digit_count = T * r;
  const int exp = (seed * 19 + r + 11) & (N - 1);
  const int64_t monomial = (seed & 1) ? -1 : 1;

  TorusPolynomial *secret = new_poly_array(r, N);
  TorusPolynomial source_shared = polynomial_new_torus_polynomial(N);
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

  DFT_Polynomial *dense_rows = new_dft_array_api_stage130(dense_row_count, N);
  DFT_Polynomial *dense_out = new_dft_array_api_stage130(m, N);
  DFT_Polynomial *dense_digits = new_dft_array_api_stage130(dense_digit_count, N);
  DFT_Polynomial *shared_digits = new_dft_array_api_stage130(T, N);
  DFT_Polynomial *body_digits = new_dft_array_api_stage130(body_digit_count, N);

  fill_source(source_shared, 0, 0, seed);
  for (int q = 0; q < r; q++) {
    fill_secret(secret[q], q, seed);
    fill_source(source_body[q], q, 1, seed);
  }
  for (int i = 0; i < N; i++) dense_source[0]->coeffs[i] = source_shared->coeffs[i];
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
  fill_dense_rows_stage130(dense_rows, m, T, N, seed);
  dense_decomp_dft_stage130(dense_digits, dense_source, m, T, Bg_bit, scratch);
  compact_shared_decomp_dft(shared_digits, body_digits, source_shared,
      source_body, r, T, Bg_bit, scratch);

  for (int sample = 0; sample < samples; sample++) {
    uint64_t start = 0;
    uint64_t total = 0;
    for (int i = 0; i < warmups; i++) {
      dense_kernel_all_stage130(dense_out, dense_source, dense_rows, m, T, Bg_bit, scratch);
    }
    start = now_ns_stage130();
    for (int i = 0; i < reps; i++) {
      dense_kernel_all_stage130(dense_out, dense_source, dense_rows, m, T, Bg_bit, scratch);
    }
    total = now_ns_stage130() - start;
    consume_dft_array_stage130(dense_out, m);
    print_bench_stage130(r, N, T, k, Bg_bit, seed, sample, reps, warmups,
        "dense_all_proxy", total);

    for (int i = 0; i < warmups; i++) {
      compact_shared_all_lanes(compact_out, source_shared, source_body, sel, scratch);
    }
    start = now_ns_stage130();
    for (int i = 0; i < reps; i++) {
      compact_shared_all_lanes(compact_out, source_shared, source_body, sel, scratch);
    }
    total = now_ns_stage130() - start;
    consume_outputs_stage130(compact_out, r);
    print_bench_stage130(r, N, T, k, Bg_bit, seed, sample, reps, warmups,
        "compact_shared_all_lanes", total);

    for (int i = 0; i < warmups; i++) {
      dense_decomp_dft_stage130(dense_digits, dense_source, m, T, Bg_bit, scratch);
    }
    start = now_ns_stage130();
    for (int i = 0; i < reps; i++) {
      dense_decomp_dft_stage130(dense_digits, dense_source, m, T, Bg_bit, scratch);
    }
    total = now_ns_stage130() - start;
    consume_dft_array_stage130(dense_digits, dense_digit_count);
    print_bench_stage130(r, N, T, k, Bg_bit, seed, sample, reps, warmups,
        "dense_decomp_dft_proxy", total);

    for (int i = 0; i < warmups; i++) {
      compact_shared_decomp_dft(shared_digits, body_digits, source_shared,
          source_body, r, T, Bg_bit, scratch);
    }
    start = now_ns_stage130();
    for (int i = 0; i < reps; i++) {
      compact_shared_decomp_dft(shared_digits, body_digits, source_shared,
          source_body, r, T, Bg_bit, scratch);
    }
    total = now_ns_stage130() - start;
    consume_dft_array_stage130(shared_digits, T);
    consume_dft_array_stage130(body_digits, body_digit_count);
    print_bench_stage130(r, N, T, k, Bg_bit, seed, sample, reps, warmups,
        "compact_shared_decomp_dft", total);

    for (int i = 0; i < warmups; i++) {
      dense_addmul_stage130(dense_out, dense_digits, dense_rows, m, T);
    }
    start = now_ns_stage130();
    for (int i = 0; i < reps; i++) {
      dense_addmul_stage130(dense_out, dense_digits, dense_rows, m, T);
    }
    total = now_ns_stage130() - start;
    consume_dft_array_stage130(dense_out, m);
    print_bench_stage130(r, N, T, k, Bg_bit, seed, sample, reps, warmups,
        "dense_addmul_proxy", total);

    for (int i = 0; i < warmups; i++) {
      compact_shared_addmul(compact_out, shared_digits, body_digits, sel);
    }
    start = now_ns_stage130();
    for (int i = 0; i < reps; i++) {
      compact_shared_addmul(compact_out, shared_digits, body_digits, sel);
    }
    total = now_ns_stage130() - start;
    consume_outputs_stage130(compact_out, r);
    print_bench_stage130(r, N, T, k, Bg_bit, seed, sample, reps, warmups,
        "compact_shared_addmul", total);
  }

  free_dft_array_api_stage130(body_digits, body_digit_count);
  free_dft_array_api_stage130(shared_digits, T);
  free_dft_array_api_stage130(dense_digits, dense_digit_count);
  free_dft_array_api_stage130(dense_out, m);
  free_dft_array_api_stage130(dense_rows, dense_row_count);
  for (int q = 0; q < r; q++) compact_ep_output_dft_free(compact_out[q]);
  free(compact_out);
  compact_ep_scratch_free(scratch);
  compact_ep_selector_dft_free(sel);
  free_poly_array_local(secret, r);
  free_polynomial(source_shared);
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

  run_shared_source_case(2, 512, T, k, Bg_bit, 0);
  run_shared_source_case(4, 512, T, k, Bg_bit, 0);
  run_shared_source_case(6, 512, T, k, Bg_bit, 0);
  run_shared_source_case(2, 1024, T, k, Bg_bit, 0);
  run_shared_source_case(4, 1024, T, k, Bg_bit, 0);
  run_shared_source_case(6, 1024, T, k, Bg_bit, 0);

  bench_shared_case(2, 512, T, k, Bg_bit, 0, samples, reps, warmups);
  bench_shared_case(4, 512, T, k, Bg_bit, 0, samples, reps, warmups);
  bench_shared_case(6, 512, T, k, Bg_bit, 0, samples, reps, warmups);
  bench_shared_case(2, 1024, T, k, Bg_bit, 0, samples, reps, warmups);
  bench_shared_case(4, 1024, T, k, Bg_bit, 0, samples, reps, warmups);
  bench_shared_case(6, 1024, T, k, Bg_bit, 0, samples, reps, warmups);

  fprintf(stderr, "stage130_sink=%f\n", g_stage130_sink);
  return 0;
}
'''
    write_text_lf(C_SOURCE, prefix + body.lstrip())


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


def parse_stdout(stdout: str) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    api_rows: List[Dict[str, str]] = []
    bench_rows: List[Dict[str, str]] = []
    for line in stdout.splitlines():
        parts = line.strip().split(",")
        if not parts:
            continue
        if parts[0] == "SHAREDAPI" and len(parts) == 18:
            api_rows.append(dict(zip(API_FIELDS, parts[1:])))
        elif parts[0] == "BENCH" and len(parts) == 16:
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
    api_rows, bench_rows = parse_stdout(proc.stdout)
    cleanup_build_outputs()
    return api_rows, bench_rows, proc.returncode == 0


def aggregate_bench(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    groups: Dict[Tuple[str, str, str, str, str, str, str, str], List[float]] = {}
    lanes: Dict[Tuple[str, str, str, str, str, str, str, str], List[float]] = {}
    for row in rows:
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
        lanes.setdefault(key, []).append(float(row["per_lane_us"]))
    out = []
    for key, values in sorted(groups.items(), key=lambda item: item[0]):
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
                "stdev_us": f"{statistics.stdev(values) if len(values) > 1 else 0.0:.6f}",
                "mean_per_lane_us": f"{statistics.mean(lanes[key]):.6f}",
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
    out = []
    for key, variants in sorted(by_case.items(), key=lambda item: item[0]):
        r = int(key[1])
        T = int(key[3])
        k = int(key[4])
        dense_dft = T * (k + r) * (k + r)
        compact_dft = 4 * T * r
        dense_total = dense_dft + T * (k + r)
        compact_total = compact_dft + T * (k + r)
        try:
            dense_all = float(variants["dense_all_proxy"]["mean_us"])
            compact_all = float(variants["compact_shared_all_lanes"]["mean_us"])
            dense_decomp = float(variants["dense_decomp_dft_proxy"]["mean_us"])
            compact_decomp = float(variants["compact_shared_decomp_dft"]["mean_us"])
            dense_addmul = float(variants["dense_addmul_proxy"]["mean_us"])
            compact_addmul = float(variants["compact_shared_addmul"]["mean_us"])
        except KeyError:
            continue
        full_speedup = dense_all / compact_all if compact_all else 0.0
        decomp_speedup = dense_decomp / compact_decomp if compact_decomp else 0.0
        addmul_speedup = dense_addmul / compact_addmul if compact_addmul else 0.0
        out.append(
            {
                "backend": key[0],
                "r": key[1],
                "N": key[2],
                "T": key[3],
                "k": key[4],
                "Bg_bit": key[5],
                "seed": key[6],
                "dense_all_mean_us": f"{dense_all:.6f}",
                "compact_shared_all_mean_us": f"{compact_all:.6f}",
                "full_speedup": f"{full_speedup:.6f}",
                "dense_decomp_dft_mean_us": f"{dense_decomp:.6f}",
                "compact_shared_decomp_dft_mean_us": f"{compact_decomp:.6f}",
                "decomp_dft_speedup": f"{decomp_speedup:.6f}",
                "dense_addmul_mean_us": f"{dense_addmul:.6f}",
                "compact_shared_addmul_mean_us": f"{compact_addmul:.6f}",
                "addmul_speedup": f"{addmul_speedup:.6f}",
                "dft_term_ratio": f"{dense_dft / compact_dft:.6f}",
                "total_term_ratio": f"{dense_total / compact_total:.6f}",
                "decision": "POSITIVE_SHARED_COMPACT_FASTER_THAN_DENSE_PROXY"
                if full_speedup >= 1.0
                else "NEGATIVE_SHARED_COMPACT_NOT_FASTER_THAN_DENSE_PROXY",
            }
        )
    return out


def api_pass(rows: List[Dict[str, str]]) -> bool:
    return bool(rows) and all(
        row["status"] == "PASS_SHARED_SOURCE_COMPACT_EP"
        and row["component_mismatches"] == "0"
        and row["phase_mismatches"] == "0"
        and row["noise_model_mismatches"] == "0"
        and int(row["negative_failures"]) > 0
        for row in rows
    )


def positive(rows: List[Dict[str, str]]) -> bool:
    targets = [row for row in rows if row["r"] in {"4", "6"}]
    return bool(targets) and all(float(row["full_speedup"]) >= 1.0 for row in targets)


def min_field(rows: List[Dict[str, str]], field: str, rs: set[str] | None = None) -> str:
    subset = [row for row in rows if rs is None or row["r"] in rs]
    return f"{min(float(row[field]) for row in subset):.6f}" if subset else ""


def max_field(rows: List[Dict[str, str]], field: str, rs: set[str] | None = None) -> str:
    subset = [row for row in rows if rs is None or row["r"] in rs]
    return f"{max(float(row[field]) for row in subset):.6f}" if subset else ""


def build_summary(
    build_ok: bool,
    compile_ok: bool,
    run_ok: bool,
    api_rows: List[Dict[str, str]],
    bench_rows: List[Dict[str, str]],
    ratio_rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    correctness = api_pass(api_rows)
    bench_ok = bool(bench_rows) and bool(ratio_rows)
    pos = positive(ratio_rows)
    if not (build_ok and compile_ok and run_ok and correctness and bench_ok):
        decision = "FAIL_STAGE130_SHARED_SOURCE_COMPACT_EP_GATE"
    elif pos:
        decision = "PASS_STAGE130_SHARED_SOURCE_COMPACT_EP_POSITIVE_PRODUCTION_API_REQUIRED"
    else:
        decision = "NEUTRAL_STAGE130_SHARED_SOURCE_COMPACT_EP_NOT_PROMOTED"
    return [
        {
            "gate": "stage130_mosfhet_static_build",
            "status": "PASS" if build_ok else "FAIL",
            "metric": "make_static_spqlios",
            "value": str(build_ok).lower(),
            "evidence": rel(BUILD_LOG),
            "detail": "MOSFHET static library build using FFT_LIB=spqlios.",
            "next_action": "",
        },
        {
            "gate": "stage130_probe_compile",
            "status": "PASS" if compile_ok else "FAIL",
            "metric": "gcc_probe_compile",
            "value": str(compile_ok).lower(),
            "evidence": rel(COMPILE_LOG),
            "detail": "Standalone shared-source compact EP probe linked against libmosfhet.a.",
            "next_action": "",
        },
        {
            "gate": "stage130_probe_run",
            "status": "PASS" if run_ok else "FAIL",
            "metric": "probe_returncode",
            "value": "0" if run_ok else "nonzero_or_skipped",
            "evidence": rel(RUN_LOG_TXT),
            "detail": "Shared-source compact EP probe executed.",
            "next_action": "",
        },
        {
            "gate": "stage130_shared_source_correctness",
            "status": "PASS" if correctness else "FAIL",
            "metric": "api_rows",
            "value": str(len(api_rows)),
            "evidence": rel(API_CSV),
            "detail": "Shared-source component, phase, noise, and negative-control checks.",
            "next_action": "Do not benchmark-interpret if correctness fails.",
        },
        {
            "gate": "stage130_microbench_rows",
            "status": "PASS" if bench_ok else "FAIL",
            "metric": "bench_rows;ratio_rows",
            "value": f"{len(bench_rows)};{len(ratio_rows)}",
            "evidence": f"{rel(BENCH_CSV)}; {rel(RATIO_CSV)}",
            "detail": "Dense-count proxy and shared-source compact samples were recorded.",
            "next_action": "",
        },
        {
            "gate": "stage130_full_microbench_signal",
            "status": "PASS_POSITIVE" if pos else ("NEUTRAL_OR_NEGATIVE" if bench_ok else "FAIL"),
            "metric": "min_full_speedup_r4_r6;max_full_speedup_all",
            "value": f"{min_field(ratio_rows, 'full_speedup', {'4', '6'})};{max_field(ratio_rows, 'full_speedup')}",
            "evidence": rel(RATIO_CSV),
            "detail": "Mean dense_all_proxy / compact_shared_all_lanes timing ratio.",
            "next_action": "Proceed only to production API design, not SAB integration.",
        },
        {
            "gate": "stage130_attribution_signal",
            "status": "RECORDED",
            "metric": "min_decomp_speedup;min_addmul_speedup",
            "value": f"{min_field(ratio_rows, 'decomp_dft_speedup')};{min_field(ratio_rows, 'addmul_speedup')}",
            "evidence": rel(RATIO_CSV),
            "detail": "Separate decomposition/DFT and DFT addmul timing attribution.",
            "next_action": "",
        },
        {
            "gate": "stage130_decision",
            "status": decision,
            "metric": "promotion_policy",
            "value": "",
            "evidence": f"{rel(SUMMARY_CSV)}; {rel(RATIO_CSV)}",
            "detail": "Stage130 decides only shared-source compact EP production-API readiness.",
            "next_action": "Full SAB claims remain blocked.",
        },
    ]


def table(rows: List[Dict[str, str]]) -> List[str]:
    lines = [
        "| r | N | dense all us | shared compact all us | full speedup | decomp/DFT speedup | addmul speedup | DFT term ratio | total term ratio | decision |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['dense_all_mean_us']} | "
            f"{row['compact_shared_all_mean_us']} | {row['full_speedup']} | "
            f"{row['decomp_dft_speedup']} | {row['addmul_speedup']} | "
            f"{row['dft_term_ratio']} | {row['total_term_ratio']} | {row['decision']} |"
        )
    return lines


def write_docs(summary: List[Dict[str, str]], ratio_rows: List[Dict[str, str]]) -> None:
    decision = summary[-1]["status"]
    write_text_lf(
        PLAN_MD,
        "\n".join(
            [
                "# Stage130 Shared-Source Compact EP Gate Plan",
                "",
                "Date: 2026-07-03",
                "",
                "## Objective",
                "",
                "Test the MAT-RLWE shape with one shared source/mask polynomial and r body",
                "polynomials. The selector remains lane-local compact/vector-shared.",
                "",
                "## Command",
                "",
                "```bash",
                "python scripts/build_stage130_shared_source_compact_ep_gate.py",
                "```",
                "",
                "## Falsification Criteria",
                "",
                "- shared-source phase/noise equivalence fails;",
                "- body-only negative control does not fail;",
                "- r=4/r=6 full microbench does not beat the dense-count proxy;",
                "- the result is used as complete SAB evidence before integration.",
            ]
        )
        + "\n",
    )
    write_text_lf(
        THEORY_MD,
        "\n".join(
            [
                "# Stage130 Shared-Source Compact EP Model",
                "",
                "Date: 2026-07-03",
                "",
                "Stage129 showed that compact addmul is positive but the `2r`",
                "decomposition/DFT stream cost blocks r=4. Stage130 changes only the",
                "source-side MAT-RLWE shape: one shared source polynomial plus r body",
                "polynomials. Selector rows remain lane-local, so the phase equation is",
                "checked per lane.",
                "",
                "## Count Model",
                "",
                "```text",
                "dense_dft_terms           = T * (k+r)^2",
                "shared_compact_dft_terms  = 4 * T * r",
                "dense_decomp_streams      = T * (k+r)",
                "shared_compact_streams    = T * (k+r)",
                "```",
                "",
                "## Results",
                "",
                *table(ratio_rows),
                "",
                "## Boundary",
                "",
                "This is isolated external-product evidence. It is not production header",
                "code, AVX512 optimality, SAB schedule integration, randomized noise, or",
                "complete `T_bootstrap/r` timing.",
            ]
        )
        + "\n",
    )
    write_text_lf(
        VARIANT_MD,
        "\n".join(
            [
                "# V130: Shared-Source Compact EP",
                "",
                "## Summary",
                "",
                "- Parent algorithm: PVW/MAT-SAB r-body research track.",
                "- Focused module: shared source/mask plus r body external product.",
                "- Optimization target: eventual complete-SAB `T_bootstrap/r`.",
                "- Status labels: `[shared-source]`, `[microbench]`, `[not-production-header]`, `[not-hot-path]`.",
                f"- Decision: `{decision}`.",
                "",
                "## Next Rule",
                "",
                "A positive Stage130 result permits a production API design gate only.",
                "It still does not permit changing scalar/default SAB or claiming full",
                "bootstrapping acceleration.",
            ]
        )
        + "\n",
    )
    md = [
        "# Stage130 Shared-Source Compact EP Gate",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{decision}`",
        "",
        "Stage130 tests the MAT-RLWE source shape with one shared source/mask and r",
        "body polynomials. It remains outside production headers and `sab_pvw_*`.",
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
    md += ["", "## Ratio Summary", "", *table(ratio_rows), "", "## Interpretation", ""]
    md += [
        "This gate directly addresses the Stage129 bottleneck by reducing compact",
        "decomposition/DFT streams from `2r` to `1+r`. Complete SAB acceleration",
        "still requires production API, SAB integration, correctness/noise, and",
        "full `T_bootstrap/r` A/B gates.",
    ]
    write_text_lf(OUT_MD, "\n".join(md) + "\n")


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
    run_id = "stage130-shared-source-compact-ep-001"
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
        BUILD_LOG,
        COMPILE_LOG,
        RUN_LOG_TXT,
        C_SOURCE,
        ARTIFACT_INDEX,
        Path("scripts/build_stage130_shared_source_compact_ep_gate.py"),
    ]
    rows.append(
        {
            "run_id": run_id,
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 130",
            "backend": "MOSFHET FFT_LIB=spqlios",
            "command": "python scripts/build_stage130_shared_source_compact_ep_gate.py",
            "params": "k=1 T=7 Bg_bit=7 r=2,4,6 N=512,1024 samples=5 reps=6",
            "seed": "0 subset",
            "status": status,
            "summary": "Stage130 tests shared-source compact EP correctness and microbench outside SAB.",
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
    write_docs(summary, ratio_rows)
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
    status = summary[-1]["status"]
    upsert_run_log(status)
    print(f"Stage130 shared-source compact EP gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if status.startswith("PASS_") or status.startswith("NEUTRAL_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
