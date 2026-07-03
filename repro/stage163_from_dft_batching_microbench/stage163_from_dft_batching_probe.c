
#include "mosfhet.h"
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#ifndef STAGE163_R
#define STAGE163_R 6
#endif
#ifndef STAGE163_N
#define STAGE163_N 2048
#endif
#ifndef STAGE163_ITEMS
#define STAGE163_ITEMS 256
#endif
#ifndef STAGE163_RUNS
#define STAGE163_RUNS 7
#endif
#ifndef STAGE163_REPS
#define STAGE163_REPS 3
#endif
#ifndef STAGE163_WARMUPS
#define STAGE163_WARMUPS 1
#endif

enum stage163_variant {
  STAGE163_SEPARATE_CURRENT = 0,
  STAGE163_BACKEND_CURRENT = 1,
  STAGE163_BACKEND_COMPONENT_MAJOR = 2
};

static inline uint64_t now_ns(void) {
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return ((uint64_t) ts.tv_sec * 1000000000ULL) + (uint64_t) ts.tv_nsec;
}

static inline int idx_of(int item, int component) {
  return item * (1 + STAGE163_R) + component;
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

static void prepare_inputs(DFT_Polynomial *dft, TorusPolynomial *addend,
    int total) {
  TorusPolynomial tmp = polynomial_new_torus_polynomial(STAGE163_N);
  for (int item = 0; item < STAGE163_ITEMS; item++) {
    for (int component = 0; component < 1 + STAGE163_R; component++) {
      int idx = idx_of(item, component);
      dft[idx] = polynomial_new_DFT_polynomial(STAGE163_N);
      addend[idx] = polynomial_new_torus_polynomial(STAGE163_N);
      fill_source(tmp, item, component);
      polynomial_torus_to_DFT(dft[idx], tmp);
      fill_addend(addend[idx], item, component);
    }
  }
  (void) total;
  free_polynomial(tmp);
}

static void run_variant(enum stage163_variant variant, DFT_Polynomial *dft,
    TorusPolynomial *addend, TorusPolynomial *out) {
  if (variant == STAGE163_BACKEND_COMPONENT_MAJOR) {
    for (int component = 0; component < 1 + STAGE163_R; component++) {
      for (int item = 0; item < STAGE163_ITEMS; item++) {
        const int idx = idx_of(item, component);
        polynomial_DFT_to_torus_add(out[idx], dft[idx], addend[idx]);
      }
    }
    return;
  }

  for (int item = 0; item < STAGE163_ITEMS; item++) {
    for (int component = 0; component < 1 + STAGE163_R; component++) {
      const int idx = idx_of(item, component);
      if (variant == STAGE163_SEPARATE_CURRENT) {
        polynomial_DFT_to_torus(out[idx], dft[idx]);
        addto_poly(out[idx], addend[idx]);
      } else {
        polynomial_DFT_to_torus_add(out[idx], dft[idx], addend[idx]);
      }
    }
  }
}

static uint64_t checksum_outputs(TorusPolynomial *out, int total) {
  uint64_t acc = 0x84222325cbf29ce4ULL;
  for (int idx = 0; idx < total; idx++) {
    for (int i = 0; i < STAGE163_N; i += 17) {
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
    for (int i = 0; i < STAGE163_N; i++) {
      const uint64_t a = (uint64_t) ref[idx]->coeffs[i];
      const uint64_t b = (uint64_t) got[idx]->coeffs[i];
      const uint64_t gap = (a >= b) ? (a - b) : (b - a);
      if (gap != 0) mismatches++;
      if (gap > max_gap) max_gap = gap;
    }
  }
  printf("CORRECT163,%s,%" PRIu64 ",%" PRIu64 ",%s\n",
      variant, mismatches, max_gap, mismatches == 0 ? "PASS" : "FAIL");
}

static const char *variant_name(enum stage163_variant variant) {
  switch (variant) {
    case STAGE163_SEPARATE_CURRENT: return "separate_current_order";
    case STAGE163_BACKEND_CURRENT: return "backend_current_order";
    case STAGE163_BACKEND_COMPONENT_MAJOR: return "backend_component_major";
  }
  return "unknown";
}

static uint64_t bench_variant(enum stage163_variant variant, DFT_Polynomial *dft,
    TorusPolynomial *addend, TorusPolynomial *out, int total) {
  for (int w = 0; w < STAGE163_WARMUPS; w++) {
    run_variant(variant, dft, addend, out);
  }
  const uint64_t start = now_ns();
  for (int rep = 0; rep < STAGE163_REPS; rep++) {
    run_variant(variant, dft, addend, out);
  }
  const uint64_t end = now_ns();
  (void) total;
  return end - start;
}

int main(void) {
  const int components = 1 + STAGE163_R;
  const int total = STAGE163_ITEMS * components;
  init_fft(STAGE163_N);

  DFT_Polynomial *dft = (DFT_Polynomial *) calloc((size_t) total, sizeof(*dft));
  TorusPolynomial *addend = (TorusPolynomial *) calloc((size_t) total, sizeof(*addend));
  TorusPolynomial *out_sep = polynomial_new_array_of_torus_polynomials(STAGE163_N, total);
  TorusPolynomial *out_backend = polynomial_new_array_of_torus_polynomials(STAGE163_N, total);
  TorusPolynomial *out_batch = polynomial_new_array_of_torus_polynomials(STAGE163_N, total);

  if (!dft || !addend || !out_sep || !out_backend || !out_batch) {
    fprintf(stderr, "allocation failed\n");
    return 2;
  }

  prepare_inputs(dft, addend, total);
  run_variant(STAGE163_SEPARATE_CURRENT, dft, addend, out_sep);
  run_variant(STAGE163_BACKEND_CURRENT, dft, addend, out_backend);
  run_variant(STAGE163_BACKEND_COMPONENT_MAJOR, dft, addend, out_batch);
  compare_outputs("backend_current_order", out_sep, out_backend, total);
  compare_outputs("backend_component_major", out_sep, out_batch, total);

  enum stage163_variant variants[3] = {
    STAGE163_SEPARATE_CURRENT,
    STAGE163_BACKEND_CURRENT,
    STAGE163_BACKEND_COMPONENT_MAJOR,
  };
  TorusPolynomial *outs[3] = {out_sep, out_backend, out_batch};

  for (int run = 0; run < STAGE163_RUNS; run++) {
    for (int v = 0; v < 3; v++) {
      const uint64_t ns = bench_variant(variants[v], dft, addend, outs[v], total);
      const uint64_t calls = (uint64_t) STAGE163_REPS * (uint64_t) total;
      const double per_call_us = ((double) ns) / ((double) calls) / 1000.0;
      const uint64_t sink = checksum_outputs(outs[v], total);
      printf("BENCH163,%s,%d,%d,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%.9f,%" PRIu64 ",PASS\n",
          variant_name(variants[v]), run, STAGE163_R, STAGE163_N,
          STAGE163_ITEMS, components, STAGE163_REPS, calls, ns,
          per_call_us, sink);
    }
  }

  for (int idx = 0; idx < total; idx++) {
    free_DFT_polynomial(dft[idx]);
    free_polynomial(addend[idx]);
  }
  free(dft);
  free(addend);
  free_array_of_polynomials(out_sep, total);
  free_array_of_polynomials(out_backend, total);
  free_array_of_polynomials(out_batch, total);
  return 0;
}
