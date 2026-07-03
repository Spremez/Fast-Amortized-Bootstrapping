
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "mosfhet.h"

static uint64_t mix64(uint64_t x){
  x += 0x9e3779b97f4a7c15ULL;
  x = (x ^ (x >> 30)) * 0xbf58476d1ce4e5b9ULL;
  x = (x ^ (x >> 27)) * 0x94d049bb133111ebULL;
  return x ^ (x >> 31);
}

static void fill_poly(TorusPolynomial p, uint64_t tag){
  for(int i = 0; i < p->N; i++){
    uint64_t x = mix64(tag + (uint64_t)i * 0x100000001b3ULL);
    p->coeffs[i] = (Torus)(x & 0x0000ffffffffffffULL);
  }
}

static void clear_poly(TorusPolynomial p){
  memset(p->coeffs, 0, sizeof(Torus) * p->N);
}

static uint64_t abs_gap(Torus a, Torus b){
  uint64_t ua = (uint64_t)a;
  uint64_t ub = (uint64_t)b;
  return ua > ub ? ua - ub : ub - ua;
}

static void compare_poly(TorusPolynomial got, TorusPolynomial want,
    uint64_t tolerance, uint64_t * mismatches, uint64_t * max_gap){
  for(int i = 0; i < got->N; i++){
    uint64_t gap = abs_gap(got->coeffs[i], want->coeffs[i]);
    if(gap > *max_gap) *max_gap = gap;
    if(gap > tolerance) (*mismatches)++;
  }
}

static void reference_lane_local(TorusPolynomial ref_a, TorusPolynomial ref_b,
    PVW_TMLWE in, TorusPolynomial * shared_a, TorusPolynomial * shared_b,
    TorusPolynomial * body_a, TorusPolynomial * body_b,
    int r, int T, int Bg_bit, int lane,
    TorusPolynomial dec_shared, TorusPolynomial dec_body){
  clear_poly(ref_a);
  clear_poly(ref_b);
  for(int t = 0; t < T; t++){
    int idx = t * r + lane;
    polynomial_decompose_i(dec_shared, in->a[0], Bg_bit, T, t);
    polynomial_decompose_i(dec_body, in->b[lane], Bg_bit, T, t);
    polynomial_mul_addto_torus(ref_a, dec_shared, shared_a[idx]);
    polynomial_mul_addto_torus(ref_b, dec_shared, shared_b[idx]);
    polynomial_mul_addto_torus(ref_a, dec_body, body_a[idx]);
    polynomial_mul_addto_torus(ref_b, dec_body, body_b[idx]);
  }
}

static void add_cross_body_reference(TorusPolynomial ref_b, PVW_TMLWE in,
    TorusPolynomial cross, int r, int T, int Bg_bit, int lane,
    TorusPolynomial dec_body){
  int neighbor = (lane + 1) % r;
  for(int t = 0; t < T; t++){
    polynomial_decompose_i(dec_body, in->b[neighbor], Bg_bit, T, t);
    polynomial_mul_addto_torus(ref_b, dec_body, cross);
  }
}

static int run_case(int r, int N, int seed){
  const int T = 7;
  const int Bg_bit = 7;
  const uint64_t tolerance = 131072ULL;
  uint64_t component_mismatches = 0;
  uint64_t phase_mismatches = 0;
  uint64_t cross_body_negative = 0;
  uint64_t max_component_gap = 0;
  uint64_t max_phase_gap = 0;
  uint64_t max_negative_gap = 0;

  PVW_TMLWE in = pvmtmlwe_alloc_new_sample(1, r, N);
  MAT_TRGSW_COMPACT_DFT selector = mat_trgsw_compact_alloc_new_DFT_sample(T, Bg_bit, 1, r, N);
  MAT_TRGSW_COMPACT_OUTPUT_DFT out = mat_trgsw_compact_alloc_new_output_DFT(r, N);
  MAT_TRGSW_COMPACT_MUL_SCRATCH scratch = mat_trgsw_compact_alloc_mul_scratch(N);

  TorusPolynomial * shared_a = polynomial_new_array_of_torus_polynomials(N, T * r);
  TorusPolynomial * shared_b = polynomial_new_array_of_torus_polynomials(N, T * r);
  TorusPolynomial * body_a = polynomial_new_array_of_torus_polynomials(N, T * r);
  TorusPolynomial * body_b = polynomial_new_array_of_torus_polynomials(N, T * r);
  TorusPolynomial got_a = polynomial_new_torus_polynomial(N);
  TorusPolynomial got_b = polynomial_new_torus_polynomial(N);
  TorusPolynomial ref_a = polynomial_new_torus_polynomial(N);
  TorusPolynomial ref_b = polynomial_new_torus_polynomial(N);
  TorusPolynomial cross_ref_b = polynomial_new_torus_polynomial(N);
  TorusPolynomial cross = polynomial_new_torus_polynomial(N);
  TorusPolynomial dec_shared = polynomial_new_torus_polynomial(N);
  TorusPolynomial dec_body = polynomial_new_torus_polynomial(N);

  fill_poly(in->a[0], 0x1000 + (uint64_t)seed * 97 + (uint64_t)r);
  for(int lane = 0; lane < r; lane++){
    fill_poly(in->b[lane], 0x2000 + (uint64_t)seed * 131 + (uint64_t)lane * 17 + (uint64_t)r);
  }
  for(int t = 0; t < T; t++){
    for(int lane = 0; lane < r; lane++){
      int idx = t * r + lane;
      fill_poly(shared_a[idx], 0x3000 + (uint64_t)seed * 193 + (uint64_t)t * 29 + (uint64_t)lane);
      fill_poly(shared_b[idx], 0x4000 + (uint64_t)seed * 211 + (uint64_t)t * 31 + (uint64_t)lane);
      fill_poly(body_a[idx], 0x5000 + (uint64_t)seed * 223 + (uint64_t)t * 37 + (uint64_t)lane);
      fill_poly(body_b[idx], 0x6000 + (uint64_t)seed * 227 + (uint64_t)t * 41 + (uint64_t)lane);
      if(mat_trgsw_compact_set_row_from_torus(selector, t, lane,
          shared_a[idx], shared_b[idx], body_a[idx], body_b[idx]) != 0){
        fprintf(stderr, "set_row_failed r=%d N=%d seed=%d t=%d lane=%d\n", r, N, seed, t, lane);
        return 2;
      }
    }
  }

  mat_trgsw_compact_mul_pvmtmlwe_DFT(out, in, selector, scratch);
  fill_poly(cross, 0x7000 + (uint64_t)seed * 239 + (uint64_t)r);

  for(int lane = 0; lane < r; lane++){
    polynomial_DFT_to_torus(got_a, out->a[lane]);
    polynomial_DFT_to_torus(got_b, out->b[lane]);
    reference_lane_local(ref_a, ref_b, in, shared_a, shared_b, body_a, body_b,
        r, T, Bg_bit, lane, dec_shared, dec_body);
    compare_poly(got_a, ref_a, tolerance, &component_mismatches, &max_component_gap);
    compare_poly(got_b, ref_b, tolerance, &component_mismatches, &max_component_gap);
    compare_poly(got_b, ref_b, tolerance, &phase_mismatches, &max_phase_gap);
    polynomial_copy_torus_polynomial(cross_ref_b, ref_b);
    add_cross_body_reference(cross_ref_b, in, cross, r, T, Bg_bit, lane, dec_body);
    compare_poly(got_b, cross_ref_b, tolerance, &cross_body_negative, &max_negative_gap);
  }

  const char * status =
      (component_mismatches == 0 && phase_mismatches == 0 && cross_body_negative > 0)
      ? "PASS_LANE_LOCAL_COMPACT_EP_AND_REJECTS_CROSS_BODY"
      : "FAIL_COMPACT_EP_PROBE";

  printf("API,spqlios,%d,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%s\n",
      r, N, T, Bg_bit, seed, component_mismatches, phase_mismatches,
      cross_body_negative, max_component_gap, max_phase_gap, max_negative_gap,
      tolerance, status);

  free_polynomial(got_a);
  free_polynomial(got_b);
  free_polynomial(ref_a);
  free_polynomial(ref_b);
  free_polynomial(cross_ref_b);
  free_polynomial(cross);
  free_polynomial(dec_shared);
  free_polynomial(dec_body);
  for(int i = 0; i < T * r; i++){
    free_polynomial(shared_a[i]);
    free_polynomial(shared_b[i]);
    free_polynomial(body_a[i]);
    free_polynomial(body_b[i]);
  }
  free(shared_a);
  free(shared_b);
  free(body_a);
  free(body_b);
  free_mat_trgsw_compact_mul_scratch(scratch);
  free_mat_trgsw_compact_output_DFT(out);
  free_mat_trgsw_compact_DFT(selector);
  free_pvmtmlwe(in);
  return strcmp(status, "PASS_LANE_LOCAL_COMPACT_EP_AND_REJECTS_CROSS_BODY") == 0 ? 0 : 1;
}

int main(void){
  int failures = 0;
  int rs[] = {2, 4, 6};
  int ns[] = {512, 1024};
  for(size_t ri = 0; ri < sizeof(rs)/sizeof(rs[0]); ri++){
    for(size_t ni = 0; ni < sizeof(ns)/sizeof(ns[0]); ni++){
      failures += run_case(rs[ri], ns[ni], 0);
      failures += run_case(rs[ri], ns[ni], 1);
    }
  }
  return failures == 0 ? 0 : 1;
}
