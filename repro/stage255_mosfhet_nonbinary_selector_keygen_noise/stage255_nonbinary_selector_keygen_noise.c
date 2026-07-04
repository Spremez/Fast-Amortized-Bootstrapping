
#include "mosfhet.h"
#include <inttypes.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static uint64_t now_us(void) {
  return (uint64_t)((double)clock() * 1000000.0 / (double)CLOCKS_PER_SEC);
}

static uint64_t abs_gap(Torus a, Torus b) {
  const uint64_t d = (uint64_t)(a - b);
  if (d <= (UINT64_MAX / 2ULL)) return d;
  return (~d) + 1ULL;
}

static void fill_msg(TorusPolynomial *msg, int r, int N, int prec, int seed) {
  for (int lane = 0; lane < r; lane++) {
    for (int coeff = 0; coeff < N; coeff++) {
      uint64_t v = (uint64_t)((seed * 7 + lane * 3 + coeff * 5 + coeff / 3) & ((1 << prec) - 1));
      msg[lane]->coeffs[coeff] = int2torus(v, (uint64_t)prec);
    }
  }
}

static void pvw_cmux_like_add(PVW_TMLWE out, PVW_TMLWE base,
    PVW_TMLWE delta, MAT_TRGSW_DFT selector, MAT_TRGSW_MUL_SCRATCH scratch,
    PVW_TMLWE tmp, PVW_TMLWE_DFT tmp_dft, uint64_t *ep_us) {
  const uint64_t begin = now_us();
  mat_trgsw_mul_pvmtmlwe_DFT(tmp_dft, delta, selector, scratch);
  *ep_us += now_us() - begin;
  pvmtmlwe_from_DFT(tmp, tmp_dft);
  pvmtmlwe_add(out, base, tmp);
}

static void include_zero_update(PVW_TMLWE out, PVW_TMLWE in, int a,
    int selector_value, MAT_TRGSW_DFT selector, MAT_TRGSW_MUL_SCRATCH scratch,
    PVW_TMLWE rotated, PVW_TMLWE delta, PVW_TMLWE tmp,
    PVW_TMLWE_DFT tmp_dft, uint64_t *ep_us) {
  (void)selector_value;
  pvmtmlwe_mul_by_xai(rotated, in, a);
  pvmtmlwe_sub(delta, rotated, in);
  pvw_cmux_like_add(out, in, delta, selector, scratch, tmp, tmp_dft, ep_us);
}

static void ternary_update(PVW_TMLWE out, PVW_TMLWE in, int a,
    int selector_value, MAT_TRGSW_DFT selector, MAT_TRGSW_MUL_SCRATCH scratch,
    PVW_TMLWE first, PVW_TMLWE inverse, PVW_TMLWE delta, PVW_TMLWE tmp,
    PVW_TMLWE_DFT tmp_dft, uint64_t *ep_us) {
  (void)selector_value;
  pvmtmlwe_mul_by_xai(first, in, a);
  pvmtmlwe_mul_by_xai(inverse, first, -2 * a);
  pvmtmlwe_sub(delta, inverse, first);
  pvw_cmux_like_add(out, first, delta, selector, scratch, tmp, tmp_dft, ep_us);
}

static void reference_update(PVW_TMLWE out, PVW_TMLWE in, const char *branch,
    int a, int selector_value) {
  if (strcmp(branch, "include_zero") == 0) {
    if (selector_value == 0) pvmtmlwe_copy(out, in);
    else pvmtmlwe_mul_by_xai(out, in, a);
  } else {
    if (selector_value == 0) pvmtmlwe_mul_by_xai(out, in, a);
    else pvmtmlwe_mul_by_xai(out, in, -a);
  }
}

static void compare_phases(PVW_TMLWE out, PVW_TMLWE ref, PVW_TMLWE_Key key,
    int prec, uint64_t *mismatches, uint64_t *max_gap, double *mean_gap) {
  const int N = key->s[0][0]->N;
  const int r = key->r;
  TorusPolynomial *out_phase = polynomial_new_array_of_torus_polynomials(N, r);
  TorusPolynomial *ref_phase = polynomial_new_array_of_torus_polynomials(N, r);
  uint64_t total_gap = 0;
  uint64_t total = 0;
  *mismatches = 0;
  *max_gap = 0;
  pvmtmlwe_phase(out_phase, out, key);
  pvmtmlwe_phase(ref_phase, ref, key);
  for (int lane = 0; lane < r; lane++) {
    for (int coeff = 0; coeff < N; coeff++) {
      const uint64_t gap = abs_gap(out_phase[lane]->coeffs[coeff], ref_phase[lane]->coeffs[coeff]);
      if (gap > *max_gap) *max_gap = gap;
      total_gap += gap;
      total++;
      if (torus2int(out_phase[lane]->coeffs[coeff], (uint64_t)prec) !=
          torus2int(ref_phase[lane]->coeffs[coeff], (uint64_t)prec)) {
        (*mismatches)++;
      }
    }
  }
  *mean_gap = total ? (double)total_gap / (double)total : 0.0;
  free_array_of_polynomials(ref_phase, r);
  free_array_of_polynomials(out_phase, r);
}

static void run_case(const char *branch, int r, int seed, int selector_value) {
  const int N = 1024;
  const int k = 1;
  const int l = 1;
  const int bg_bit = 23;
  const int prec = 3;
  const int rows = (k + r) * l;
  const int a = 3 + ((seed * 5 + r + selector_value) % 31) * 2;

  PVW_TMLWE_Key key = pvmtmlwe_new_binary_key(N, k, r, pow(2, -70));
  MAT_TRGSW_Key mat_key = mat_trgsw_new_key(key, l, bg_bit);
  MAT_TRGSW_DFT selector = mat_trgsw_alloc_new_DFT_sample(l, bg_bit, k, r, N);
  MAT_TRGSW_MUL_SCRATCH scratch = mat_trgsw_alloc_mul_scratch(rows, N);
  TorusPolynomial *msg = polynomial_new_array_of_torus_polynomials(N, r);
  fill_msg(msg, r, N, prec, seed);

  const uint64_t kg_begin = now_us();
  mat_trgsw_monomial_DFT_sample(selector, selector_value, 0, mat_key);
  const uint64_t selector_keygen_us = now_us() - kg_begin;

  PVW_TMLWE in = pvmtmlwe_new_sample(msg, key);
  PVW_TMLWE out = pvmtmlwe_alloc_new_sample(k, r, N);
  PVW_TMLWE ref = pvmtmlwe_alloc_new_sample(k, r, N);
  PVW_TMLWE t1 = pvmtmlwe_alloc_new_sample(k, r, N);
  PVW_TMLWE t2 = pvmtmlwe_alloc_new_sample(k, r, N);
  PVW_TMLWE t3 = pvmtmlwe_alloc_new_sample(k, r, N);
  PVW_TMLWE_DFT t_dft = pvmtmlwe_alloc_new_DFT_sample(k, r, N);
  uint64_t ep_us = 0;

  if (strcmp(branch, "include_zero") == 0) {
    include_zero_update(out, in, a, selector_value, selector, scratch, t1, t2, t3, t_dft, &ep_us);
  } else {
    ternary_update(out, in, a, selector_value, selector, scratch, t1, t2, t3, t3, t_dft, &ep_us);
  }
  reference_update(ref, in, branch, a, selector_value);

  uint64_t mismatches = 0;
  uint64_t max_gap = 0;
  double mean_gap = 0.0;
  compare_phases(out, ref, key, prec, &mismatches, &max_gap, &mean_gap);
  const char *status = mismatches == 0 ? "PASS_MOSFHET_SELECTOR_SUBA" : "FAIL";
  printf("%s,%d,%d,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%.3f,%" PRIu64 ",%" PRIu64 ",%s\n",
      branch, r, seed, selector_value, N, prec, a, mismatches, max_gap,
      mean_gap, selector_keygen_us, ep_us, status);

  free_pvmtmlwe_DFT(t_dft);
  free_pvmtmlwe(t3);
  free_pvmtmlwe(t2);
  free_pvmtmlwe(t1);
  free_pvmtmlwe(ref);
  free_pvmtmlwe(out);
  free_pvmtmlwe(in);
  free_array_of_polynomials(msg, r);
  free_mat_trgsw_mul_scratch(scratch);
  free_mat_trgsw_DFT(selector);
  free_mat_trgsw_key(mat_key);
  free_pvmtmlwe_key(key);
}

int main(void) {
  printf("branch,r,seed,selector_value,N,prec,a,phase_mismatches,max_phase_gap,mean_phase_gap,selector_keygen_us,external_product_us,status\n");
  for (int r_idx = 0; r_idx < 3; r_idx++) {
    const int r_values[3] = {1, 2, 4};
    const int r = r_values[r_idx];
    for (int seed = 0; seed < 5; seed++) {
      for (int selector_value = 0; selector_value <= 1; selector_value++) {
        run_case("include_zero", r, seed, selector_value);
        run_case("ternary", r, seed, selector_value);
      }
    }
  }
  return 0;
}
