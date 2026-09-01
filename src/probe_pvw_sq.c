/* probe_pvw_sq.c -- stage357 S1 gate: the SQ kernel inside the r-lane PVW
 * structure vs the stock sab_pvw implementation on identical inputs, keys
 * and test vectors. Gate = message equality on every lane x slot at the
 * message grid, r = 1 and r = 4. */
#include "sab_pvw_sq.h"
#include <sab_pvw.h>
#include <sab.h>
#include <stdio.h>
#include <stdlib.h>

static int run_gate(int r, int reps, uint64_t h_fair){
  const int in_N = 16, in_k = 1, out_N = 1024, out_k = 1;
  const int bg_bit = 23, prec = 3;
  const uint64_t selector_values[3] = {5, 4, 7};
  const uint64_t packing_distances[2] = {2, 7};
  const int ell_packing = 2, b_packing = 14, t_ks = 12, b_ks = 1;
  const uint64_t r_prec = 4;
  printf("== gate r=%d h=%lu ==\n", r, (unsigned long) h_fair);

  (void) selector_values; (void) packing_distances;
  TRLWE_Key input_key, packing_key;
  RS_sparse_binary_key(&input_key, in_N, in_k, h_fair, pow(2, -15), 4);
  RS_sparse_binary_key(&packing_key, in_N, in_k, h_fair, pow(2, -44), 4);
  PVW_TMLWE_Key pvw_key = pvmtmlwe_new_binary_key(out_N, out_k, r, pow(2, -70));

  SAB_PVW_Key stock = sab_pvw_new_binary_full_key(input_key, packing_key,
      pvw_key, prec, b_packing, ell_packing, t_ks, b_ks, h_fair, r_prec, 1,
      bg_bit);
  SAB_PVW_SQ_Key sq = sab_pvw_sq_new_binary_full_key(input_key, packing_key,
      pvw_key, prec, b_packing, ell_packing, t_ks, b_ks, h_fair, r_prec, 1,
      bg_bit);

  TorusPolynomial input_msg = polynomial_new_torus_polynomial(in_N);
  for (int i = 0; i < in_N; i++)
    input_msg->coeffs[i] = int2torus((3 * i + 1) & 7, prec);
  TRLWE input = trlwe_new_sample(input_msg, input_key);

  TorusPolynomial * tv_msg = polynomial_new_array_of_torus_polynomials(out_N, r);
  for (int lane = 0; lane < r; lane++)
    for (int c = 0; c < out_N; c++)
      tv_msg[lane]->coeffs[c] = int2torus((5 * lane + 3 * c) & 7, prec);
  PVW_TMLWE pvw_tv = pvmtmlwe_new_noiseless_trivial_sample(tv_msg, out_k, r, out_N);

  TRLWE * stock_out = trlwe_alloc_new_sample_array(r, in_k, in_N);
  TRLWE * sq_out = trlwe_alloc_new_sample_array(r, in_k, in_N);

  for (int rep = 0; rep < reps; rep++){
    sab_pvw_bootstrap_binary(stock_out, input, pvw_tv, stock);
    sab_pvw_sq_bootstrap_binary(sq_out, input, pvw_tv, sq);
    size_t mism = 0;
    for (int lane = 0; lane < r; lane++){
      TorusPolynomial ps = polynomial_new_torus_polynomial(in_N);
      TorusPolynomial pq = polynomial_new_torus_polynomial(in_N);
      trlwe_phase(ps, stock_out[lane], input_key);
      trlwe_phase(pq, sq_out[lane], input_key);
      for (int i = 0; i < in_N; i++){
        const int64_t grid = 1LL << (64 - prec);
        if ((((int64_t) ps->coeffs[i] + grid / 2) >> (64 - prec))
            != (((int64_t) pq->coeffs[i] + grid / 2) >> (64 - prec))){
          if(mism < 5) printf("  MISMATCH rep=%d lane=%d slot=%d\n", rep, lane, i);
          mism++;
        }
      }
      free_polynomial(ps); free_polynomial(pq);
    }
    printf("rep %d: mismatch %d / %d -- %s\n", rep, (int) mism, r * in_N,
           mism == 0 ? "Pass" : "FAIL");
    if(rep == 0 && mism) break;
  }
  return 0;
}

#include <time.h>
static void run_timing(void);

int main(void){
  setvbuf(stdout, NULL, _IONBF, 0);
  if(getenv("SAB_PVW_SQ_TIMING")){
    run_timing();
    printf("timing done\n");
    return 0;
  }
  run_gate(1, 2, 2);   /* toy point: same as the stock lane-equivalence test */
  run_gate(4, 2, 2);
  printf("probe_pvw_sq done\n");
  return 0;
}

/* S2 timing mode: full SET_2_3_2048 shape, fairness point via SAB_SQ_H,
 * r via SAB_PVW_SQ_R (default 4); SQ vs stock sab_pvw back-to-back. */
static void run_timing(void){
  const int in_N = 2048, in_k = 1, out_N = 2048, out_k = 1;
  const int bg_bit = 23, prec = 3;
  const int ell_packing = 2, b_packing = 14, t_ks = 12, b_ks = 1;
  uint64_t h = 39, r = 4, reps = 3;
  int sigma_shift = 0;   /* 2026/279 hardening: raises the BSK key sigma,
                          * mirrors SAB_SQ_SIGMA_SHIFT in probe_sq.c */
  {
    const char * e = getenv("SAB_SQ_H");
    if(e) h = strtoull(e, NULL, 0);
    e = getenv("SAB_PVW_SQ_R");
    if(e) r = strtoull(e, NULL, 0);
    e = getenv("SAB_PVW_SQ_REPS");
    if(e) reps = strtoull(e, NULL, 0);
    e = getenv("SAB_SQ_SIGMA_SHIFT");
    if(e) sigma_shift = atoi(e);
  }
  printf("== timing r=%lu h=%lu sigma_shift=%d ==\n", (unsigned long) r,
         (unsigned long) h, sigma_shift);
  /* B_gap control: rejection-sampling target for the sparse support
   * (max circular gap <= 2^target_r_prec). Default mirrors probe_sq's
   * auto-derivation log2(N/h)+2; override via SAB_SQ_RPREC. */
  uint64_t target_r_prec = (uint64_t)(log2((double) in_N / (double) h) + 2.0);
  {
    const char * e = getenv("SAB_SQ_RPREC");
    if(e) target_r_prec = strtoull(e, NULL, 0);
  }
  TRLWE_Key input_key, packing_key;
  RS_sparse_binary_key(&input_key, in_N, in_k, h, pow(2, -15), target_r_prec);
  RS_sparse_binary_key(&packing_key, in_N, in_k, 256, pow(2, -44), 7);
  const uint64_t r_prec = get_min_prec(input_key);
  printf("r_prec = %lu\n", (unsigned long) r_prec);
  PVW_TMLWE_Key pvw_key = pvmtmlwe_new_binary_key(out_N, out_k, (int) r,
      pow(2, -50 + sigma_shift));
  SAB_PVW_Key stock = sab_pvw_new_binary_full_key(input_key, packing_key,
      pvw_key, prec, b_packing, ell_packing, t_ks, b_ks, h, r_prec, 1, bg_bit);
  SAB_PVW_SQ_Key sq = sab_pvw_sq_new_binary_full_key(input_key, packing_key,
      pvw_key, prec, b_packing, ell_packing, t_ks, b_ks, h, r_prec, 1, bg_bit);

  TorusPolynomial input_msg = polynomial_new_torus_polynomial(in_N);
  for (int i = 0; i < in_N; i++)
    input_msg->coeffs[i] = int2torus(i & 7, prec);
  TRLWE input = trlwe_new_sample(input_msg, input_key);
  TorusPolynomial * tv_msg = polynomial_new_array_of_torus_polynomials(out_N,
      (int) r);
  uint64_t LUT[8];
  generate_random_bytes(sizeof(LUT), (uint8_t *) LUT);
  for (int lane = 0; lane < (int) r; lane++)
    for (int c = 0; c < out_N; c++)
      tv_msg[lane]->coeffs[c] = int2torus((LUT[(lane + c) & 7]) & 7, prec);
  PVW_TMLWE pvw_tv = pvmtmlwe_new_noiseless_trivial_sample(tv_msg, out_k,
      (int) r, out_N);
  TRLWE * stock_out = trlwe_alloc_new_sample_array((int) r, in_k, in_N);
  TRLWE * sq_out = trlwe_alloc_new_sample_array((int) r, in_k, in_N);

  /* S2b: warm up both paths (cold pages), then alternate the measurement
   * order per rep to cancel allocation-order / cache-state bias */
  sab_pvw_bootstrap_binary(stock_out, input, pvw_tv, stock);
  sab_pvw_sq_bootstrap_binary(sq_out, input, pvw_tv, sq);
  for (int rep = 0; rep < (int) reps; rep++){
    struct timespec t0, t1;
    double stock_us, sq_us;
    if(rep & 1){
      clock_gettime(CLOCK_MONOTONIC, &t0);
      sab_pvw_sq_bootstrap_binary(sq_out, input, pvw_tv, sq);
      clock_gettime(CLOCK_MONOTONIC, &t1);
      sq_us = (t1.tv_sec - t0.tv_sec) * 1e6 + (t1.tv_nsec - t0.tv_nsec) / 1e3;
      clock_gettime(CLOCK_MONOTONIC, &t0);
      sab_pvw_bootstrap_binary(stock_out, input, pvw_tv, stock);
      clock_gettime(CLOCK_MONOTONIC, &t1);
      stock_us = (t1.tv_sec - t0.tv_sec) * 1e6 + (t1.tv_nsec - t0.tv_nsec) / 1e3;
    }else{
      clock_gettime(CLOCK_MONOTONIC, &t0);
      sab_pvw_bootstrap_binary(stock_out, input, pvw_tv, stock);
      clock_gettime(CLOCK_MONOTONIC, &t1);
      stock_us = (t1.tv_sec - t0.tv_sec) * 1e6 + (t1.tv_nsec - t0.tv_nsec) / 1e3;
      clock_gettime(CLOCK_MONOTONIC, &t0);
      sab_pvw_sq_bootstrap_binary(sq_out, input, pvw_tv, sq);
      clock_gettime(CLOCK_MONOTONIC, &t1);
      sq_us = (t1.tv_sec - t0.tv_sec) * 1e6 + (t1.tv_nsec - t0.tv_nsec) / 1e3;
    }
    size_t mism = 0;
    for (int lane = 0; lane < (int) r; lane++){
      TorusPolynomial ps = polynomial_new_torus_polynomial(in_N);
      TorusPolynomial pq = polynomial_new_torus_polynomial(in_N);
      trlwe_phase(ps, stock_out[lane], input_key);
      trlwe_phase(pq, sq_out[lane], input_key);
      const int64_t grid = 1LL << (64 - prec);
      for (int i = 0; i < in_N; i++)
        if ((((int64_t) ps->coeffs[i] + grid / 2) >> (64 - prec))
            != (((int64_t) pq->coeffs[i] + grid / 2) >> (64 - prec))) mism++;
      free_polynomial(ps); free_polynomial(pq);
    }
    printf("TIMING r=%lu h=%lu rep=%d stock=%.0fus sq=%.0fus ratio=%.4f mism=%d %s\n",
           (unsigned long) r, (unsigned long) h, rep, stock_us, sq_us,
           sq_us / stock_us, (int) mism, mism == 0 ? "Pass" : "FAIL");
  }
}
