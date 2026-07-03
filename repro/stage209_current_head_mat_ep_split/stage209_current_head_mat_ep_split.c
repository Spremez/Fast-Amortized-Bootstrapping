
#include "mosfhet.h"
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifndef STAGE209_R
#define STAGE209_R 2
#endif
#ifndef STAGE209_N
#define STAGE209_N 2048
#endif
#ifndef STAGE209_ITEMS
#define STAGE209_ITEMS 128
#endif
#ifndef STAGE209_REPS
#define STAGE209_REPS 8
#endif
#ifndef STAGE209_WARMUPS
#define STAGE209_WARMUPS 2
#endif
#ifndef STAGE209_BG_BIT
#define STAGE209_BG_BIT 23
#endif

#define static
#include "src/mosfhet/src/mattrgsw.c"
#undef static

static inline uint64_t now_ns(void) {
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return ((uint64_t) ts.tv_sec * 1000000000ULL) + (uint64_t) ts.tv_nsec;
}

static void fill_poly(TorusPolynomial p, uint64_t seed) {
  uint64_t x = seed ^ 0x9e3779b97f4a7c15ULL;
  for (int i = 0; i < p->N; i++) {
    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    p->coeffs[i] = (Torus) (x * 0x2545f4914f6cdd1dULL + (uint64_t) i);
  }
}

static void fill_pvmtmlwe(PVW_TMLWE p, uint64_t seed) {
  fill_poly(p->a[0], seed ^ 0x100000001b3ULL);
  for (int lane = 0; lane < p->r; lane++) {
    fill_poly(p->b[lane], seed ^ ((uint64_t) lane << 32) ^ 0x84222325cbf29ce4ULL);
  }
}

static void fill_selector(MAT_TRGSW_DFT selector) {
  TorusPolynomial tmp = polynomial_new_torus_polynomial(STAGE209_N);
  const int rows = 1 + STAGE209_R;
  for (int row = 0; row < rows; row++) {
    fill_poly(tmp, 0xabcdef0011223344ULL ^ (uint64_t) row);
    polynomial_torus_to_DFT(selector->samples[row]->a[0], tmp);
    for (int lane = 0; lane < STAGE209_R; lane++) {
      fill_poly(tmp, 0x6677889900aabbccULL ^ ((uint64_t) row << 16) ^ (uint64_t) lane);
      polynomial_torus_to_DFT(selector->samples[row]->b[lane], tmp);
    }
  }
  free_polynomial(tmp);
}

static uint64_t checksum_torus_rows(TorusPolynomial *rows, int count) {
  uint64_t acc = 0xcbf29ce484222325ULL;
  for (int row = 0; row < count; row++) {
    for (int i = 0; i < rows[row]->N; i += 17) {
      acc ^= (uint64_t) rows[row]->coeffs[i] + (acc << 6) + (acc >> 2);
    }
  }
  return acc;
}

static uint64_t checksum_dft_rows(DFT_Polynomial *rows, int count) {
  uint64_t acc = 0x84222325cbf29ce4ULL;
  for (int row = 0; row < count; row++) {
    const uint64_t *v = (const uint64_t *) rows[row]->coeffs;
    for (int i = 0; i < rows[row]->N; i += 17) {
      acc ^= v[i] + (acc << 6) + (acc >> 2);
    }
  }
  return acc;
}

static uint64_t checksum_dft_out(PVW_TMLWE_DFT out) {
  uint64_t acc = 0x6a09e667f3bcc909ULL;
  const uint64_t *a = (const uint64_t *) out->a[0]->coeffs;
  for (int i = 0; i < STAGE209_N; i += 17) acc ^= a[i] + (acc << 6) + (acc >> 2);
  for (int lane = 0; lane < STAGE209_R; lane++) {
    const uint64_t *b = (const uint64_t *) out->b[lane]->coeffs;
    for (int i = 0; i < STAGE209_N; i += 17) acc ^= b[i] + (acc << 6) + (acc >> 2);
  }
  return acc;
}

static uint64_t compare_torus(PVW_TMLWE a, PVW_TMLWE b, uint64_t *max_gap) {
  uint64_t mismatches = 0;
  for (int i = 0; i < STAGE209_N; i++) {
    uint64_t x = (uint64_t) a->a[0]->coeffs[i];
    uint64_t y = (uint64_t) b->a[0]->coeffs[i];
    uint64_t gap = x >= y ? x - y : y - x;
    if (gap != 0) mismatches++;
    if (gap > *max_gap) *max_gap = gap;
  }
  for (int lane = 0; lane < STAGE209_R; lane++) {
    for (int i = 0; i < STAGE209_N; i++) {
      uint64_t x = (uint64_t) a->b[lane]->coeffs[i];
      uint64_t y = (uint64_t) b->b[lane]->coeffs[i];
      uint64_t gap = x >= y ? x - y : y - x;
      if (gap != 0) mismatches++;
      if (gap > *max_gap) *max_gap = gap;
    }
  }
  return mismatches;
}

static void fill_dec_bank(TorusPolynomial *bank, int rows) {
  for (int item = 0; item < STAGE209_ITEMS; item++) {
    for (int row = 0; row < rows; row++) {
      fill_poly(bank[item * rows + row], 0x1111222233334444ULL ^ ((uint64_t)item << 8) ^ (uint64_t)row);
    }
  }
}

static void fill_dec_dft_bank(DFT_Polynomial *bank, int rows) {
  TorusPolynomial tmp = polynomial_new_torus_polynomial(STAGE209_N);
  for (int item = 0; item < STAGE209_ITEMS; item++) {
    for (int row = 0; row < rows; row++) {
      fill_poly(tmp, 0x5555666677778888ULL ^ ((uint64_t)item << 8) ^ (uint64_t)row);
      polynomial_torus_to_DFT(bank[item * rows + row], tmp);
    }
  }
  free_polynomial(tmp);
}

static int run_variant(const char *variant) {
  const int rows = 1 + STAGE209_R;
  init_fft(STAGE209_N);
  MAT_TRGSW_DFT selector =
      mat_trgsw_alloc_new_DFT_sample(1, STAGE209_BG_BIT, 1, STAGE209_R, STAGE209_N);
  fill_selector(selector);
  PVW_TMLWE *in1 = pvmtmlwe_alloc_new_sample_array(STAGE209_ITEMS, 1, STAGE209_R, STAGE209_N);
  PVW_TMLWE *in2 = pvmtmlwe_alloc_new_sample_array(STAGE209_ITEMS, 1, STAGE209_R, STAGE209_N);
  for (int item = 0; item < STAGE209_ITEMS; item++) {
    fill_pvmtmlwe(in1[item], 0x100000000ULL + (uint64_t)item);
    fill_pvmtmlwe(in2[item], 0x200000000ULL + (uint64_t)item);
  }
  MAT_TRGSW_MUL_SCRATCH scratch = mat_trgsw_alloc_mul_scratch(rows, STAGE209_N);
  PVW_TMLWE_DFT out = pvmtmlwe_alloc_new_DFT_sample(1, STAGE209_R, STAGE209_N);
  TorusPolynomial *dec_bank = polynomial_new_array_of_torus_polynomials(STAGE209_N, rows * STAGE209_ITEMS);
  DFT_Polynomial *dft_bank = polynomial_new_array_of_polynomials_DFT(STAGE209_N, rows * STAGE209_ITEMS);
  fill_dec_bank(dec_bank, rows);
  fill_dec_dft_bank(dft_bank, rows);

  PVW_TMLWE_DFT current = pvmtmlwe_alloc_new_DFT_sample(1, STAGE209_R, STAGE209_N);
  PVW_TMLWE_DFT split = pvmtmlwe_alloc_new_DFT_sample(1, STAGE209_R, STAGE209_N);
  mat_trgsw_mul_pvmtmlwe_sub_DFT(current, in1[0], in2[0], selector, scratch);
  mat_trgsw_sub_decompose(in1[0], in2[0], scratch->dec, selector->Q, selector->T);
  for (int row = 0; row < rows; row++) {
    polynomial_torus_to_DFT(scratch->dec_dft[row], scratch->dec[row]);
  }
  mat_trgsw_mul_pvmtmlwe_DFT_from_dec(split, selector, scratch->dec_dft);
  PVW_TMLWE current_torus = pvmtmlwe_alloc_new_sample(1, STAGE209_R, STAGE209_N);
  PVW_TMLWE split_torus = pvmtmlwe_alloc_new_sample(1, STAGE209_R, STAGE209_N);
  pvmtmlwe_from_DFT(current_torus, current);
  pvmtmlwe_from_DFT(split_torus, split);
  uint64_t max_gap = 0;
  uint64_t mismatches = compare_torus(current_torus, split_torus, &max_gap);
  printf("CORRECT209,%s,combined_vs_split,%" PRIu64 ",%" PRIu64 ",%s\n",
      variant, mismatches, max_gap, mismatches == 0 ? "PASS" : "FAIL");

  uint64_t sink = 0;
  for (int w = 0; w < STAGE209_WARMUPS; w++) {
    for (int item = 0; item < STAGE209_ITEMS; item++) {
      if (strcmp(variant, "sub_decompose") == 0) {
        mat_trgsw_sub_decompose(in1[item], in2[item], scratch->dec,
            selector->Q, selector->T);
      } else if (strcmp(variant, "torus_to_dft_rows") == 0) {
        for (int row = 0; row < rows; row++) {
          polynomial_torus_to_DFT(scratch->dec_dft[row], dec_bank[item * rows + row]);
        }
      } else if (strcmp(variant, "addmul_from_dec_dft") == 0) {
        mat_trgsw_mul_pvmtmlwe_DFT_from_dec(out, selector, &dft_bank[item * rows]);
      } else if (strcmp(variant, "combined_current") == 0) {
        mat_trgsw_mul_pvmtmlwe_sub_DFT(out, in1[item], in2[item], selector, scratch);
      }
    }
  }

  uint64_t start = now_ns();
  for (int rep = 0; rep < STAGE209_REPS; rep++) {
    for (int item = 0; item < STAGE209_ITEMS; item++) {
      if (strcmp(variant, "sub_decompose") == 0) {
        mat_trgsw_sub_decompose(in1[item], in2[item], scratch->dec,
            selector->Q, selector->T);
      } else if (strcmp(variant, "torus_to_dft_rows") == 0) {
        for (int row = 0; row < rows; row++) {
          polynomial_torus_to_DFT(scratch->dec_dft[row], dec_bank[item * rows + row]);
        }
      } else if (strcmp(variant, "addmul_from_dec_dft") == 0) {
        mat_trgsw_mul_pvmtmlwe_DFT_from_dec(out, selector, &dft_bank[item * rows]);
      } else if (strcmp(variant, "combined_current") == 0) {
        mat_trgsw_mul_pvmtmlwe_sub_DFT(out, in1[item], in2[item], selector, scratch);
      } else {
        fprintf(stderr, "unknown variant: %s\n", variant);
        return 2;
      }
    }
  }
  if (strcmp(variant, "sub_decompose") == 0) {
    sink = checksum_torus_rows(scratch->dec, rows);
  } else if (strcmp(variant, "torus_to_dft_rows") == 0) {
    sink = checksum_dft_rows(scratch->dec_dft, rows);
  } else {
    sink = checksum_dft_out(out);
  }
  uint64_t ns = now_ns() - start;
  uint64_t calls = (uint64_t) STAGE209_REPS * (uint64_t) STAGE209_ITEMS;
  double per_call_us = ((double)ns) / ((double)calls) / 1000.0;
  printf("RESULT209,%s,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%.9f,%" PRIu64 ",%s\n",
      variant, STAGE209_R, STAGE209_N, STAGE209_ITEMS, STAGE209_REPS,
      calls, ns, per_call_us, sink, mismatches == 0 ? "PASS" : "FAIL");

  free_pvmtmlwe(current_torus);
  free_pvmtmlwe(split_torus);
  free_pvmtmlwe_DFT(current);
  free_pvmtmlwe_DFT(split);
  for (int i = 0; i < rows * STAGE209_ITEMS; i++) free_DFT_polynomial(dft_bank[i]);
  free(dft_bank);
  free_array_of_polynomials(dec_bank, rows * STAGE209_ITEMS);
  free_pvmtmlwe_DFT(out);
  free_mat_trgsw_mul_scratch(scratch);
  free_pvmtmlwe_array(in1, STAGE209_ITEMS);
  free_pvmtmlwe_array(in2, STAGE209_ITEMS);
  free_mat_trgsw_DFT(selector);
  return mismatches == 0 ? 0 : 1;
}

int main(int argc, char **argv) {
  if (argc != 2) {
    fprintf(stderr, "usage: %s sub_decompose|torus_to_dft_rows|addmul_from_dec_dft|combined_current\n", argv[0]);
    return 2;
  }
  return run_variant(argv[1]);
}
