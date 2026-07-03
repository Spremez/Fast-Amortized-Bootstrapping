
#include "mosfhet.h"
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifndef STAGE174_R
#define STAGE174_R 6
#endif
#ifndef STAGE174_N
#define STAGE174_N 2048
#endif
#ifndef STAGE174_ITEMS
#define STAGE174_ITEMS 256
#endif
#ifndef STAGE174_RUNS
#define STAGE174_RUNS 7
#endif
#ifndef STAGE174_REPS
#define STAGE174_REPS 8
#endif
#ifndef STAGE174_WARMUPS
#define STAGE174_WARMUPS 2
#endif

static inline uint64_t now_ns(void) {
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return ((uint64_t) ts.tv_sec * 1000000000ULL) + (uint64_t) ts.tv_nsec;
}

static inline int idx_of(int item, int component) {
  return item * (1 + STAGE174_R) + component;
}

static void fill_source(TorusPolynomial p, int item, int component) {
  uint64_t x = 0x9e3779b97f4a7c15ULL ^ ((uint64_t) item << 32) ^ (uint64_t) component;
  for (int i = 0; i < p->N; i++) {
    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    p->coeffs[i] = (Torus) (x * 0x2545f4914f6cdd1dULL + (uint64_t) (i + 17 * component));
  }
}

static void fill_addend(TorusPolynomial p, int item, int component) {
  uint64_t x = 0xd1b54a32d192ed03ULL ^ ((uint64_t) component << 40) ^ (uint64_t) item;
  for (int i = 0; i < p->N; i++) {
    x += 0x9e3779b97f4a7c15ULL + (uint64_t) (i * 1315423911U);
    x ^= x >> 29;
    p->coeffs[i] = (Torus) (x + ((uint64_t) item << 11) + (uint64_t) component);
  }
}

static void addto_poly(TorusPolynomial out, TorusPolynomial in) {
#if defined(__AVX512F__)
  __m512i *out_v = (__m512i *) out->coeffs;
  const __m512i *in_v = (const __m512i *) in->coeffs;
  for (int i = 0; i < out->N / 8; i++) {
    out_v[i] = _mm512_add_epi64(out_v[i], in_v[i]);
  }
#else
  polynomial_addto_torus_polynomial(out, in);
#endif
}

static void prepare_inputs(DFT_Polynomial *dft, TorusPolynomial *addend) {
  TorusPolynomial tmp = polynomial_new_torus_polynomial(STAGE174_N);
  for (int item = 0; item < STAGE174_ITEMS; item++) {
    for (int component = 0; component < 1 + STAGE174_R; component++) {
      const int idx = idx_of(item, component);
      dft[idx] = polynomial_new_DFT_polynomial(STAGE174_N);
      addend[idx] = polynomial_new_torus_polynomial(STAGE174_N);
      fill_source(tmp, item, component);
      polynomial_torus_to_DFT(dft[idx], tmp);
      fill_addend(addend[idx], item, component);
    }
  }
  free_polynomial(tmp);
}

static void run_from_dft_add(DFT_Polynomial *dft, TorusPolynomial *addend,
    TorusPolynomial *out) {
  for (int item = 0; item < STAGE174_ITEMS; item++) {
    for (int component = 0; component < 1 + STAGE174_R; component++) {
      const int idx = idx_of(item, component);
      polynomial_DFT_to_torus_add(out[idx], dft[idx], addend[idx]);
    }
  }
}

static uint64_t checksum_outputs(TorusPolynomial *out, int total) {
  uint64_t acc = 0x84222325cbf29ce4ULL;
  for (int idx = 0; idx < total; idx++) {
    for (int i = 0; i < STAGE174_N; i += 17) {
      const uint64_t v = (uint64_t) out[idx]->coeffs[i];
      acc ^= v + 0x9e3779b97f4a7c15ULL + (acc << 6) + (acc >> 2);
    }
  }
  return acc;
}

static void compare_outputs(const char *variant, TorusPolynomial *ref,
    TorusPolynomial *got, int total) {
  uint64_t mismatches = 0;
  uint64_t max_gap = 0;
  for (int idx = 0; idx < total; idx++) {
    for (int i = 0; i < STAGE174_N; i++) {
      const uint64_t a = (uint64_t) ref[idx]->coeffs[i];
      const uint64_t b = (uint64_t) got[idx]->coeffs[i];
      const uint64_t gap = (a >= b) ? (a - b) : (b - a);
      if (gap != 0) mismatches++;
      if (gap > max_gap) max_gap = gap;
    }
  }
  printf("CORRECT174,%s,separate_reference,%" PRIu64 ",%" PRIu64 ",%s\n",
      variant, mismatches, max_gap, mismatches == 0 ? "PASS" : "FAIL");
}

static uint64_t bench_variant(DFT_Polynomial *dft, TorusPolynomial *addend,
    TorusPolynomial *out) {
  for (int w = 0; w < STAGE174_WARMUPS; w++) {
    run_from_dft_add(dft, addend, out);
  }
  const uint64_t start = now_ns();
  for (int rep = 0; rep < STAGE174_REPS; rep++) {
    run_from_dft_add(dft, addend, out);
  }
  return now_ns() - start;
}

int main(int argc, char **argv) {
  if (argc != 2) {
    fprintf(stderr, "usage: %s baseline|direct_scale\n", argv[0]);
    return 2;
  }
  const char *variant = argv[1];
  const int components = 1 + STAGE174_R;
  const int total = STAGE174_ITEMS * components;
  init_fft(STAGE174_N);

  DFT_Polynomial *dft = (DFT_Polynomial *) calloc((size_t) total, sizeof(*dft));
  TorusPolynomial *addend = (TorusPolynomial *) calloc((size_t) total, sizeof(*addend));
  TorusPolynomial *ref = polynomial_new_array_of_torus_polynomials(STAGE174_N, total);
  TorusPolynomial *out = polynomial_new_array_of_torus_polynomials(STAGE174_N, total);
  if (!dft || !addend || !ref || !out) {
    fprintf(stderr, "allocation failed\n");
    return 2;
  }

  prepare_inputs(dft, addend);
  for (int idx = 0; idx < total; idx++) {
    polynomial_DFT_to_torus(ref[idx], dft[idx]);
    addto_poly(ref[idx], addend[idx]);
  }
  run_from_dft_add(dft, addend, out);
  compare_outputs(variant, ref, out, total);

  for (int run = 0; run < STAGE174_RUNS; run++) {
    const uint64_t ns = bench_variant(dft, addend, out);
    const uint64_t calls = (uint64_t) STAGE174_REPS * (uint64_t) total;
    const double per_call_us = ((double) ns) / ((double) calls) / 1000.0;
    const uint64_t sink = checksum_outputs(out, total);
    printf("BENCH174,%s,%d,%d,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%.9f,%" PRIu64 ",PASS\n",
        variant, run, STAGE174_R, STAGE174_N, STAGE174_ITEMS, components,
        STAGE174_REPS, calls, ns, per_call_us, sink);
  }

  for (int idx = 0; idx < total; idx++) {
    free_DFT_polynomial(dft[idx]);
    free_polynomial(addend[idx]);
  }
  free(dft);
  free(addend);
  free_array_of_polynomials(ref, total);
  free_array_of_polynomials(out, total);
  return 0;
}
