
#include "mosfhet.h"
#include "spqlios-fft.h"
#include <immintrin.h>
#include <inttypes.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifndef STAGE212_N
#define STAGE212_N 2048
#endif
#ifndef STAGE212_MAX_ROWS
#define STAGE212_MAX_ROWS 5
#endif
#ifndef STAGE212_ITEMS
#define STAGE212_ITEMS 128
#endif
#ifndef STAGE212_RUNS
#define STAGE212_RUNS 10
#endif
#ifndef STAGE212_REPS
#define STAGE212_REPS 8
#endif
#ifndef STAGE212_WARMUPS
#define STAGE212_WARMUPS 2
#endif

static inline uint64_t now_ns(void) {
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return ((uint64_t) ts.tv_sec * 1000000000ULL) + (uint64_t) ts.tv_nsec;
}

static inline int idx_of(int item, int row) {
  return item * STAGE212_MAX_ROWS + row;
}

static void fill_input(uint64_t *dst, int item, int row) {
  uint64_t x = 0x9e3779b97f4a7c15ULL ^ ((uint64_t) item << 32) ^ (uint64_t) row;
  for (int i = 0; i < STAGE212_N; i++) {
    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    dst[i] = x * 0x2545f4914f6cdd1dULL + (uint64_t) (i + 17 * row);
  }
}

static inline void convert_torus64_to_double(double *restrict dst,
    const uint64_t *restrict src) {
#if defined(__AVX512F__)
  __m512d *dst_v = (__m512d *) dst;
  const __m512i *src_v = (const __m512i *) src;
  for (int i = 0; i < STAGE212_N / 8; i++) {
    dst_v[i] = _mm512_cvtepi64_pd(src_v[i]);
  }
#else
  const int64_t *src_i = (const int64_t *) src;
  for (int i = 0; i < STAGE212_N; i++) {
    dst[i] = (double) src_i[i];
  }
#endif
}

static inline void copy_double_row(double *restrict dst,
    const double *restrict src) {
#if defined(__AVX512F__)
  __m512d *dst_v = (__m512d *) dst;
  const __m512d *src_v = (const __m512d *) src;
  for (int i = 0; i < STAGE212_N / 8; i++) {
    dst_v[i] = src_v[i];
  }
#else
  memcpy(dst, src, sizeof(double) * STAGE212_N);
#endif
}

static void current_execute_loop(double **out, uint64_t **in, int rows,
    FFT_Processor_Spqlios proc) {
  for (int item = 0; item < STAGE212_ITEMS; item++) {
    for (int row = 0; row < rows; row++) {
      int idx = idx_of(item, row);
      execute_reverse_torus64(out[idx], in[idx], proc);
    }
  }
}

static void multirow_interleaved_scratch(double **out, uint64_t **in, int rows,
    FFT_Processor_Spqlios proc, double **scratch) {
  for (int item = 0; item < STAGE212_ITEMS; item++) {
    for (int row = 0; row < rows; row++) {
      int idx = idx_of(item, row);
      convert_torus64_to_double(scratch[row], in[idx]);
      ifft(proc->tables_reverse, scratch[row]);
      copy_double_row(out[idx], scratch[row]);
    }
  }
}

static void multirow_two_phase_scratch(double **out, uint64_t **in, int rows,
    FFT_Processor_Spqlios proc, double **scratch) {
  for (int item = 0; item < STAGE212_ITEMS; item++) {
    for (int row = 0; row < rows; row++) {
      convert_torus64_to_double(scratch[row], in[idx_of(item, row)]);
    }
    for (int row = 0; row < rows; row++) {
      ifft(proc->tables_reverse, scratch[row]);
    }
    for (int row = 0; row < rows; row++) {
      copy_double_row(out[idx_of(item, row)], scratch[row]);
    }
  }
}

static void run_variant(const char *variant, double **out, uint64_t **in,
    int rows, FFT_Processor_Spqlios proc, double **scratch) {
  if (strcmp(variant, "current_execute_loop") == 0) {
    current_execute_loop(out, in, rows, proc);
  } else if (strcmp(variant, "multirow_interleaved_scratch") == 0) {
    multirow_interleaved_scratch(out, in, rows, proc, scratch);
  } else if (strcmp(variant, "multirow_two_phase_scratch") == 0) {
    multirow_two_phase_scratch(out, in, rows, proc, scratch);
  }
}

static uint64_t checksum_outputs(double **out, int rows) {
  uint64_t acc = 0xcbf29ce484222325ULL;
  for (int item = 0; item < STAGE212_ITEMS; item += 7) {
    for (int row = 0; row < rows; row++) {
      double *p = out[idx_of(item, row)];
      for (int i = 0; i < STAGE212_N; i += 127) {
        uint64_t bits = 0;
        memcpy(&bits, &p[i], sizeof(bits));
        acc ^= bits + 0x9e3779b97f4a7c15ULL + (acc << 6) + (acc >> 2);
      }
    }
  }
  return acc;
}

static void compare_outputs(const char *variant, double **baseline,
    double **candidate, int rows) {
  int mismatches = 0;
  double max_abs_diff = 0.0;
  for (int item = 0; item < STAGE212_ITEMS; item++) {
    for (int row = 0; row < rows; row++) {
      int idx = idx_of(item, row);
      for (int i = 0; i < STAGE212_N; i++) {
        double diff = fabs(baseline[idx][i] - candidate[idx][i]);
        if (diff != 0.0) {
          mismatches++;
          if (diff > max_abs_diff) max_abs_diff = diff;
        }
      }
    }
  }
  printf("CORRECT212,%d,%s,%d,%.17g,%s\n", rows, variant, mismatches,
      max_abs_diff, mismatches == 0 ? "PASS" : "FAIL");
}

static uint64_t bench_variant(const char *variant, double **out, uint64_t **in,
    int rows, FFT_Processor_Spqlios proc, double **scratch, int run) {
  for (int w = 0; w < STAGE212_WARMUPS; w++) {
    run_variant(variant, out, in, rows, proc, scratch);
  }
  uint64_t start = now_ns();
  for (int rep = 0; rep < STAGE212_REPS; rep++) {
    run_variant(variant, out, in, rows, proc, scratch);
  }
  uint64_t total_ns = now_ns() - start;
  uint64_t sink = checksum_outputs(out, rows);
  double per_group_us = (double) total_ns / (double) (STAGE212_ITEMS * STAGE212_REPS) / 1000.0;
  double per_row_us = (double) total_ns / (double) (STAGE212_ITEMS * STAGE212_REPS * rows) / 1000.0;
  printf("BENCH212,%d,%s,%d,%d,%d,%d,%" PRIu64 ",%.9f,%.9f,%" PRIu64 ",PASS\n",
      rows, variant, run, STAGE212_N, STAGE212_ITEMS, STAGE212_REPS,
      total_ns, per_group_us, per_row_us, sink);
  return sink;
}

static double *alloc_double_row(void) {
  return (double *) safe_aligned_malloc(sizeof(double) * STAGE212_N);
}

static uint64_t *alloc_torus_row(void) {
  return (uint64_t *) safe_aligned_malloc(sizeof(uint64_t) * STAGE212_N);
}

int main(void) {
  const char *variants[] = {
    "current_execute_loop",
    "multirow_interleaved_scratch",
    "multirow_two_phase_scratch"
  };
  const int variant_count = 3;
  const int row_cases[] = {3, 5};
  const int row_case_count = 2;
  const int total_slots = STAGE212_ITEMS * STAGE212_MAX_ROWS;

  uint64_t **inputs = (uint64_t **) calloc((size_t) total_slots, sizeof(uint64_t *));
  double **baseline = (double **) calloc((size_t) total_slots, sizeof(double *));
  double **candidate = (double **) calloc((size_t) total_slots, sizeof(double *));
  double **scratch = (double **) calloc((size_t) STAGE212_MAX_ROWS, sizeof(double *));
  if (!inputs || !baseline || !candidate || !scratch) return 2;

  for (int idx = 0; idx < total_slots; idx++) {
    inputs[idx] = alloc_torus_row();
    baseline[idx] = alloc_double_row();
    candidate[idx] = alloc_double_row();
  }
  for (int row = 0; row < STAGE212_MAX_ROWS; row++) {
    scratch[row] = alloc_double_row();
  }
  for (int item = 0; item < STAGE212_ITEMS; item++) {
    for (int row = 0; row < STAGE212_MAX_ROWS; row++) {
      fill_input(inputs[idx_of(item, row)], item, row);
    }
  }

  FFT_Processor_Spqlios proc = new_FFT_Processor_Spqlios(STAGE212_N);
  if (!proc) return 3;

  for (int case_idx = 0; case_idx < row_case_count; case_idx++) {
    int rows = row_cases[case_idx];
    current_execute_loop(baseline, inputs, rows, proc);
    for (int v = 1; v < variant_count; v++) {
      memset(candidate[0], 0, sizeof(double) * STAGE212_N);
      run_variant(variants[v], candidate, inputs, rows, proc, scratch);
      compare_outputs(variants[v], baseline, candidate, rows);
    }
    for (int run = 0; run < STAGE212_RUNS; run++) {
      for (int v = 0; v < variant_count; v++) {
        bench_variant(variants[v], candidate, inputs, rows, proc, scratch, run);
      }
    }
  }
  return 0;
}
