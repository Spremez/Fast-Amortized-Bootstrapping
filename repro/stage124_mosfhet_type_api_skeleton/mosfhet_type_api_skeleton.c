#include "mosfhet.h"
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#ifndef STAGE124_BACKEND
#define STAGE124_BACKEND "unknown"
#endif

typedef enum {
  STAGE124_KIND_ACC = 0,
  STAGE124_KIND_SHARED = 1,
  STAGE124_KIND_BODY = 2
} Stage124Kind;

typedef struct _Stage124LaneTMLWE {
  TorusPolynomial *a;
  TorusPolynomial b;
  int k;
  int N;
  int lane;
  int gadget;
  Stage124Kind kind;
} *Stage124LaneTMLWE;

typedef struct _Stage124LaneTMLWE_DFT {
  DFT_Polynomial *a;
  DFT_Polynomial b;
  int k;
  int N;
  int lane;
  int gadget;
  Stage124Kind kind;
} *Stage124LaneTMLWE_DFT;

typedef struct _Stage124Accumulator {
  Stage124LaneTMLWE *lane;
  int k;
  int r;
  int N;
} *Stage124Accumulator;

typedef struct _Stage124Accumulator_DFT {
  Stage124LaneTMLWE_DFT *lane;
  int k;
  int r;
  int N;
} *Stage124Accumulator_DFT;

typedef struct _Stage124Selector_DFT {
  Stage124LaneTMLWE_DFT *shared;
  Stage124LaneTMLWE_DFT *body;
  int T;
  int Q;
  int k;
  int r;
  int N;
} *Stage124Selector_DFT;

static uint64_t mix64(uint64_t salt, uint64_t a, uint64_t b, uint64_t c) {
  uint64_t x = salt * 0x9e3779b97f4a7c15ULL;
  x ^= (a + 0xbf58476d1ce4e5b9ULL) * 0x94d049bb133111ebULL;
  x ^= (b + 0x2545f4914f6cdd1dULL) * 0x9e3779b97f4a7c15ULL;
  x ^= (c + 0x100000001b3ULL) * 0xbf58476d1ce4e5b9ULL;
  x ^= x >> 33;
  x *= 0xff51afd7ed558ccdULL;
  x ^= x >> 33;
  return x;
}

static Torus small_torus(uint64_t salt, uint64_t lane, uint64_t comp,
    uint64_t idx) {
  return (Torus)(mix64(salt, lane, comp, idx) % 17ULL);
}

static uint64_t abs_gap(Torus a, Torus b) {
  const uint64_t d = (uint64_t)(a - b);
  if (d <= (1ULL << 63)) return d;
  return (~d) + 1ULL;
}

static Stage124LaneTMLWE lane_alloc(int k, int N, int lane, int gadget,
    Stage124Kind kind) {
  Stage124LaneTMLWE out = (Stage124LaneTMLWE)safe_malloc(sizeof(*out));
  out->a = (TorusPolynomial *)safe_malloc(sizeof(TorusPolynomial) * k);
  for (int i = 0; i < k; i++) out->a[i] = polynomial_new_torus_polynomial(N);
  out->b = polynomial_new_torus_polynomial(N);
  out->k = k;
  out->N = N;
  out->lane = lane;
  out->gadget = gadget;
  out->kind = kind;
  return out;
}

static Stage124LaneTMLWE_DFT lane_dft_alloc(int k, int N, int lane, int gadget,
    Stage124Kind kind) {
  Stage124LaneTMLWE_DFT out =
      (Stage124LaneTMLWE_DFT)safe_malloc(sizeof(*out));
  out->a = (DFT_Polynomial *)safe_malloc(sizeof(DFT_Polynomial) * k);
  for (int i = 0; i < k; i++) out->a[i] = polynomial_new_DFT_polynomial(N);
  out->b = polynomial_new_DFT_polynomial(N);
  out->k = k;
  out->N = N;
  out->lane = lane;
  out->gadget = gadget;
  out->kind = kind;
  return out;
}

static void lane_free(Stage124LaneTMLWE in) {
  if (in == NULL) return;
  for (int i = 0; i < in->k; i++) free_polynomial(in->a[i]);
  free(in->a);
  free_polynomial(in->b);
  free(in);
}

static void lane_dft_free(Stage124LaneTMLWE_DFT in) {
  if (in == NULL) return;
  for (int i = 0; i < in->k; i++) free_DFT_polynomial(in->a[i]);
  free(in->a);
  free_DFT_polynomial(in->b);
  free(in);
}

static Stage124Accumulator acc_alloc(int k, int r, int N) {
  Stage124Accumulator out = (Stage124Accumulator)safe_malloc(sizeof(*out));
  out->lane = (Stage124LaneTMLWE *)safe_malloc(sizeof(Stage124LaneTMLWE) * r);
  for (int q = 0; q < r; q++) out->lane[q] = lane_alloc(k, N, q, -1, STAGE124_KIND_ACC);
  out->k = k;
  out->r = r;
  out->N = N;
  return out;
}

static Stage124Accumulator_DFT acc_dft_alloc(int k, int r, int N) {
  Stage124Accumulator_DFT out =
      (Stage124Accumulator_DFT)safe_malloc(sizeof(*out));
  out->lane = (Stage124LaneTMLWE_DFT *)safe_malloc(sizeof(Stage124LaneTMLWE_DFT) * r);
  for (int q = 0; q < r; q++) out->lane[q] = lane_dft_alloc(k, N, q, -1, STAGE124_KIND_ACC);
  out->k = k;
  out->r = r;
  out->N = N;
  return out;
}

static void acc_free(Stage124Accumulator in) {
  if (in == NULL) return;
  for (int q = 0; q < in->r; q++) lane_free(in->lane[q]);
  free(in->lane);
  free(in);
}

static void acc_dft_free(Stage124Accumulator_DFT in) {
  if (in == NULL) return;
  for (int q = 0; q < in->r; q++) lane_dft_free(in->lane[q]);
  free(in->lane);
  free(in);
}

static Stage124Selector_DFT selector_dft_alloc(int T, int Q, int k, int r,
    int N) {
  Stage124Selector_DFT out =
      (Stage124Selector_DFT)safe_malloc(sizeof(*out));
  const int rows = T * r;
  out->shared = (Stage124LaneTMLWE_DFT *)safe_malloc(sizeof(Stage124LaneTMLWE_DFT) * rows);
  out->body = (Stage124LaneTMLWE_DFT *)safe_malloc(sizeof(Stage124LaneTMLWE_DFT) * rows);
  for (int t = 0; t < T; t++) {
    for (int q = 0; q < r; q++) {
      const int idx = t * r + q;
      out->shared[idx] = lane_dft_alloc(k, N, q, t, STAGE124_KIND_SHARED);
      out->body[idx] = lane_dft_alloc(k, N, q, t, STAGE124_KIND_BODY);
    }
  }
  out->T = T;
  out->Q = Q;
  out->k = k;
  out->r = r;
  out->N = N;
  return out;
}

static Stage124LaneTMLWE_DFT selector_shared(Stage124Selector_DFT in, int t,
    int q) {
  return in->shared[t * in->r + q];
}

static Stage124LaneTMLWE_DFT selector_body(Stage124Selector_DFT in, int t,
    int q) {
  return in->body[t * in->r + q];
}

static void selector_dft_free(Stage124Selector_DFT in) {
  if (in == NULL) return;
  const int rows = in->T * in->r;
  for (int i = 0; i < rows; i++) {
    lane_dft_free(in->shared[i]);
    lane_dft_free(in->body[i]);
  }
  free(in->shared);
  free(in->body);
  free(in);
}

static void lane_fill(Stage124LaneTMLWE in, uint64_t salt) {
  for (int j = 0; j < in->k; j++) {
    for (int i = 0; i < in->N; i++) {
      in->a[j]->coeffs[i] = small_torus(salt, (uint64_t)in->lane,
          (uint64_t)(10 + j), (uint64_t)i);
    }
  }
  for (int i = 0; i < in->N; i++) {
    in->b->coeffs[i] = small_torus(salt, (uint64_t)in->lane, 100, (uint64_t)i);
  }
}

static void acc_to_dft(Stage124Accumulator_DFT out, Stage124Accumulator in) {
  for (int q = 0; q < in->r; q++) {
    for (int j = 0; j < in->k; j++) {
      polynomial_torus_to_DFT(out->lane[q]->a[j], in->lane[q]->a[j]);
    }
    polynomial_torus_to_DFT(out->lane[q]->b, in->lane[q]->b);
  }
}

static void acc_from_dft(Stage124Accumulator out, Stage124Accumulator_DFT in) {
  for (int q = 0; q < in->r; q++) {
    for (int j = 0; j < in->k; j++) {
      polynomial_DFT_to_torus(out->lane[q]->a[j], in->lane[q]->a[j]);
    }
    polynomial_DFT_to_torus(out->lane[q]->b, in->lane[q]->b);
  }
}

static void compare_acc(Stage124Accumulator a, Stage124Accumulator b,
    uint64_t tol, uint64_t *mismatches, uint64_t *max_gap) {
  for (int q = 0; q < a->r; q++) {
    for (int j = 0; j < a->k; j++) {
      for (int i = 0; i < a->N; i++) {
        const uint64_t gap = abs_gap(a->lane[q]->a[j]->coeffs[i],
            b->lane[q]->a[j]->coeffs[i]);
        if (gap > tol) (*mismatches)++;
        if (gap > *max_gap) *max_gap = gap;
      }
    }
    for (int i = 0; i < a->N; i++) {
      const uint64_t gap = abs_gap(a->lane[q]->b->coeffs[i],
          b->lane[q]->b->coeffs[i]);
      if (gap > tol) (*mismatches)++;
      if (gap > *max_gap) *max_gap = gap;
    }
  }
}

static int collect_acc_ptrs(Stage124Accumulator acc, void **ptrs, int offset) {
  int n = offset;
  for (int q = 0; q < acc->r; q++) {
    for (int j = 0; j < acc->k; j++) ptrs[n++] = acc->lane[q]->a[j]->coeffs;
    ptrs[n++] = acc->lane[q]->b->coeffs;
  }
  return n;
}

static int collect_selector_ptrs(Stage124Selector_DFT sel, void **ptrs,
    int offset) {
  int n = offset;
  for (int t = 0; t < sel->T; t++) {
    for (int q = 0; q < sel->r; q++) {
      Stage124LaneTMLWE_DFT rows[2] = {
        selector_shared(sel, t, q),
        selector_body(sel, t, q)
      };
      for (int x = 0; x < 2; x++) {
        for (int j = 0; j < rows[x]->k; j++) ptrs[n++] = rows[x]->a[j]->coeffs;
        ptrs[n++] = rows[x]->b->coeffs;
      }
    }
  }
  return n;
}

static uint64_t pointer_failures(void **ptrs, int count) {
  uint64_t failures = 0;
  for (int i = 0; i < count; i++) {
    if (ptrs[i] == NULL) failures++;
    for (int j = i + 1; j < count; j++) {
      if (ptrs[i] == ptrs[j]) failures++;
    }
  }
  return failures;
}

static uint64_t selector_coverage_failures(Stage124Selector_DFT sel) {
  uint64_t failures = 0;
  for (int t = 0; t < sel->T; t++) {
    for (int q = 0; q < sel->r; q++) {
      Stage124LaneTMLWE_DFT s = selector_shared(sel, t, q);
      Stage124LaneTMLWE_DFT b = selector_body(sel, t, q);
      if (s->lane != q || s->gadget != t || s->kind != STAGE124_KIND_SHARED) failures++;
      if (b->lane != q || b->gadget != t || b->kind != STAGE124_KIND_BODY) failures++;
    }
  }
  return failures;
}

static uint64_t metadata_failures(Stage124Accumulator acc,
    Stage124Accumulator_DFT acc_dft, Stage124Selector_DFT sel, int k, int r,
    int N, int T) {
  uint64_t failures = 0;
  if (acc->k != k || acc->r != r || acc->N != N) failures++;
  if (acc_dft->k != k || acc_dft->r != r || acc_dft->N != N) failures++;
  if (sel->k != k || sel->r != r || sel->N != N || sel->T != T) failures++;
  for (int q = 0; q < r; q++) {
    if (acc->lane[q]->lane != q || acc->lane[q]->kind != STAGE124_KIND_ACC) failures++;
    if (acc_dft->lane[q]->lane != q || acc_dft->lane[q]->kind != STAGE124_KIND_ACC) failures++;
  }
  return failures;
}

static void run_case(int r, int N, int T, int k) {
  const int Q = 7;
  const uint64_t tol = 1024;
  const uint64_t current_acc = (uint64_t)(k + r);
  const uint64_t vector_acc = (uint64_t)r * (uint64_t)(k + 1);
  const uint64_t current_sel = (uint64_t)T * (uint64_t)(k + r) * (uint64_t)(k + r);
  const uint64_t vector_sel = 2ULL * (uint64_t)T * (uint64_t)r * (uint64_t)(k + 1);
  const uint64_t current_total = current_acc + current_sel;
  const uint64_t vector_total = vector_acc + vector_sel;

  Stage124Accumulator acc = acc_alloc(k, r, N);
  Stage124Accumulator_DFT acc_dft = acc_dft_alloc(k, r, N);
  Stage124Accumulator roundtrip = acc_alloc(k, r, N);
  Stage124Selector_DFT selector = selector_dft_alloc(T, Q, k, r, N);

  for (int q = 0; q < r; q++) lane_fill(acc->lane[q], 1234 + (uint64_t)N);
  acc_to_dft(acc_dft, acc);
  acc_from_dft(roundtrip, acc_dft);

  uint64_t mismatches = 0;
  uint64_t max_gap = 0;
  compare_acc(acc, roundtrip, tol, &mismatches, &max_gap);

  const int ptr_cap = (int)(2 * vector_acc + vector_sel + 16);
  void **ptrs = (void **)safe_malloc(sizeof(void *) * ptr_cap);
  int ptr_count = 0;
  ptr_count = collect_acc_ptrs(acc, ptrs, ptr_count);
  ptr_count = collect_acc_ptrs(roundtrip, ptrs, ptr_count);
  ptr_count = collect_selector_ptrs(selector, ptrs, ptr_count);
  const uint64_t component_failures = pointer_failures(ptrs, ptr_count);
  free(ptrs);

  const uint64_t meta_failures =
      metadata_failures(acc, acc_dft, selector, k, r, N, T);
  const uint64_t coverage_failures = selector_coverage_failures(selector);
  const int api_ok = component_failures == 0 && meta_failures == 0
      && coverage_failures == 0 && mismatches == 0;

  const double acc_overhead = (double)vector_acc / (double)current_acc;
  const double selector_ratio = (double)current_sel / (double)vector_sel;
  const double total_ratio = (double)current_total / (double)vector_total;
  const int layout_ok = selector_ratio > 1.0 && total_ratio > 1.0;

  printf("API,%s,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%s\n",
      STAGE124_BACKEND, r, N, T, k, component_failures, meta_failures,
      coverage_failures, mismatches, max_gap, tol,
      api_ok ? "PASS_TYPE_API_SKELETON" : "FAIL");

  printf("LAYOUT,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%.6f,%" PRIu64
         ",%" PRIu64 ",%.6f,%" PRIu64 ",%" PRIu64 ",%.6f,%s\n",
      r, N, T, k, current_acc, vector_acc, acc_overhead, current_sel,
      vector_sel, selector_ratio, current_total, vector_total, total_ratio,
      layout_ok ? "PASS_LAYOUT_MODEL" : "FAIL");

  selector_dft_free(selector);
  acc_free(roundtrip);
  acc_dft_free(acc_dft);
  acc_free(acc);
}

int main(void) {
  const int k = 1;
  const int T = 7;
  run_case(2, 1024, T, k);
  run_case(4, 1024, T, k);
  run_case(6, 1024, T, k);
  run_case(2, 2048, T, k);
  run_case(4, 2048, T, k);
  run_case(6, 2048, T, k);
  return 0;
}
