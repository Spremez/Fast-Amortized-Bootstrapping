/* probe_homtr.c -- Hom-Tr vs plaintext sub_a vs sub_a_ga benchmark.
 * Uses gaussian keygen (which builds aut_family) so Hom-Tr can run.
 * Key is binary (coeff=1) so plaintext sub_a reference is valid.
 * Three arms: (1) plaintext sub_a binary, (2) Hom-Tr, (3) scalar oracle.
 */
#include <sab_pvw.h>
#include <sab.h>
#include <mosfhet.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <time.h>

static void lane_phase(TorusPolynomial out, PVW_TMLWE in, PVW_TMLWE_Key key,
    int lane, int N){
  memset(out->coeffs, 0, sizeof(out->coeffs[0]) * N);
  polynomial_mul_addto_torus(out, in->a[0], key->s[0][lane]);
  polynomial_sub_torus_polynomials(out, in->b[lane], out);
}

int main(void){
  setvbuf(stdout, NULL, _IONBF, 0);
  const int in_N = 256, out_N = 1024, in_k = 1, out_k = 1;
  const int bg_bit = 23, prec = 3, h = 6, r = 2;
  int coeff_max = 1;
  {
    const char *e = getenv("SAB_GRHO_COEFF_MAX");
    if(e) coeff_max = atoi(e);
    if(coeff_max < 1) coeff_max = 1;
  }

  TRLWE_Key input_key, packing_key;
  RS_sparse_binary_key(&input_key, in_N, in_k, h, pow(2,-15), 5);
  RS_sparse_binary_key(&packing_key, in_N, in_k, h, pow(2,-44), 5);
  int bumped = 0;
  for (int i = 0; i < in_N; i++)
    if(input_key->s[0]->coeffs[i] == 1)
      input_key->s[0]->coeffs[i] = 1 + (bumped++ % coeff_max);
  if(bumped != h){ printf("support mismatch %d != %d\n", bumped, h); return 1; }

  uint64_t max_gap = 0, previous = in_N;
  for (int scan = 0; scan < in_N; scan++){
    const int current = in_N - scan - 1;
    if(input_key->s[0]->coeffs[current] == 0) continue;
    if(previous - current > max_gap) max_gap = previous - current;
    previous = current;
  }
  if(previous > max_gap) max_gap = previous;
  uint64_t r_prec = 1;
  while((1ULL << r_prec) <= max_gap) r_prec++;
  printf("key: h=%d coeff_max=%d r_prec=%lu\n", bumped, coeff_max,
      (unsigned long)r_prec);

  /* gaussian keygen builds aut_family (needed for Hom-Tr) */
  PVW_TMLWE_Key pvw_key = pvmtmlwe_new_binary_key(out_N, out_k, r, pow(2,-70));
  SAB_PVW_Key pvw = sab_pvw_new_gaussian_key(input_key, pvw_key, prec, h,
      r_prec, 1, bg_bit);
  printf("gaussian key built (aut family %d)\n", out_N);

  TorusPolynomial input_msg = polynomial_new_torus_polynomial(in_N);
  for (int i = 0; i < in_N; i++) input_msg->coeffs[i] = int2torus(i & 7, prec);
  TRLWE input = trlwe_new_sample(input_msg, input_key);
  TorusPolynomial *tv_msg = polynomial_new_array_of_torus_polynomials(out_N, r);
  for (int lane = 0; lane < r; lane++)
    for (int c = 0; c < out_N; c++)
      tv_msg[lane]->coeffs[c] = int2torus((3*lane + c) & 7, prec);
  PVW_TMLWE pvw_tv = pvmtmlwe_new_noiseless_trivial_sample(tv_msg, out_k, r, out_N);

  /* mod-switched a (odd, for Hom-Tr and ga) */
  const int log_N2 = (int)log2(2*out_N);
  uint64_t *a_odd = (uint64_t*)safe_malloc(sizeof(uint64_t)*in_N);
  for (int i = 0; i < in_N; i++){
    uint64_t v = torus2int(input->a[0]->coeffs[i], log_N2);
    if(!(v & 1)) v = (v - 1) & (2*out_N - 1);
    a_odd[i] = v;
  }

  const int64_t grid = 1LL << (64 - prec);
  TorusPolynomial p1 = polynomial_new_torus_polynomial(out_N);
  TorusPolynomial p2 = polynomial_new_torus_polynomial(out_N);

  /* --- Arm 1: plaintext sub_a (binary path, reference) --- */
  PVW_TMLWE *acc_bin = pvmtmlwe_alloc_new_sample_array(in_N, out_k, r, out_N);
  sab_pvw_setup_tv_xb(acc_bin, input->b->coeffs, pvw_tv, pvw);
  /* binary sub_a uses raw a (not odd), so we need the un-odd version */
  {
    /* manual binary sub_a: multiply each slot by X^{-a_raw[i]} */
    const int log_N2b = (int)log2(2*out_N);
    for (size_t step = 0; step < pvw->h; step++){
      sab_pvw_RGSW_monomial_mul(acc_bin, pvw->s[0][step], pvw);
      for (int i = 0; i < in_N; i++){
        uint64_t v = torus2int(input->a[0]->coeffs[i], log_N2b);
        pvmtmlwe_mul_by_xai(pvw->tmp->tmlwe, acc_bin[i], v);
        pvmtmlwe_copy(acc_bin[i], pvw->tmp->tmlwe);
      }
    }
    sab_pvw_RGSW_monomial_mul(acc_bin, pvw->s[0][pvw->h], pvw);
  }
  printf("arm1 (plaintext sub_a) done\n");

  /* --- Arm 2: Hom-Tr sub_a --- */
  PVW_TMLWE *acc_ht = pvmtmlwe_alloc_new_sample_array(in_N, out_k, r, out_N);
  sab_pvw_setup_tv_xb(acc_ht, input->b->coeffs, pvw_tv, pvw);
  {
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    sab_pvw_sparse_mul_homtr(acc_ht, (const uint64_t*)a_odd, 0, pvw);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ht_us = (t1.tv_sec - t0.tv_sec)*1e6 + (t1.tv_nsec - t0.tv_nsec)/1e3;
    printf("arm2 (Hom-Tr sub_a) done (%.0f us blind rotation)\n", ht_us);
  }

  /* --- Compare arm1 vs arm2 --- */
  int mism = 0; int64_t max_dev = 0;
  for (int lane = 0; lane < r; lane++)
    for (int j = 0; j < in_N; j++){
      lane_phase(p1, acc_bin[j], pvw_key, lane, out_N);
      lane_phase(p2, acc_ht[j], pvw_key, lane, out_N);
      {
        const int64_t d0 = (int64_t)p1->coeffs[0] - (int64_t)p2->coeffs[0];
        const int64_t ad = d0 < 0 ? -d0 : d0;
        if(ad > max_dev) max_dev = ad;
      }
      if((((int64_t)p1->coeffs[0] + grid/2) >> (64-prec))
          != (((int64_t)p2->coeffs[0] + grid/2) >> (64-prec))) mism++;
    }
  printf("HOMTR GATE: mismatch %d / %d -- %s; pair noise max dev log2 = %.2f (budget 2^-%d)\n",
      mism, r*in_N, mism==0?"Pass":"FAIL",
      log2((double)max_dev + 1.0), prec+1);

  /* --- Arm 3: scalar oracle (canonical wo_extract) --- */
  int oracle_mism = 0;
  for (int lane = 0; lane < r; lane++){
    TRLWE_Key lane_key = trlwe_alloc_key(out_N, out_k, pvw_key->sigma);
    memcpy(lane_key->s[0]->coeffs, pvw_key->s[0][lane]->coeffs,
        sizeof(lane_key->s[0]->coeffs[0]) * out_N);
    TRGSW_Key skey = trgsw_new_key(lane_key, 1, bg_bit);
    SAB_Key oracle = new_sparse_amortized_bootstrapping(input_key,
        packing_key, skey, prec, 14, 2, 12, 1, h, r_prec, false,false,true);
    TRLWE tv = trlwe_alloc_new_sample(in_k, out_N);
    memset(tv->a[0]->coeffs, 0, sizeof(tv->a[0]->coeffs[0])*out_N);
    memcpy(tv->b->coeffs, tv_msg[lane]->coeffs, sizeof(tv->b->coeffs[0])*out_N);
    TRLWE *sacc = trlwe_alloc_new_sample_array(in_N, in_k, out_N);
    sab_rlwe_bootstrap_wo_extract(sacc, input, tv, oracle);
    for (int j = 0; j < in_N; j++){
      trlwe_phase(p1, sacc[j], lane_key);
      lane_phase(p2, acc_ht[j], pvw_key, lane, out_N);
      if((((int64_t)p1->coeffs[0] + grid/2) >> (64-prec))
          != (((int64_t)p2->coeffs[0] + grid/2) >> (64-prec))) oracle_mism++;
    }
    free_trlwe_array(sacc, in_N); free_trlwe(tv);
  }
  printf("HOMTR ORACLE GATE: mismatch %d / %d -- %s\n",
      oracle_mism, r*in_N, oracle_mism==0?"Pass":"FAIL");

  /* --- Timing: sub_a only (isolated) --- */
  {
    PVW_TMLWE *tmp_arr = pvmtmlwe_alloc_new_sample_array(in_N, out_k, r, out_N);
    struct timespec t0, t1;
    /* plaintext sub_a timing */
    for (int i = 0; i < in_N; i++) pvmtmlwe_copy(tmp_arr[i], acc_bin[i]);
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (size_t step = 0; step < pvw->h; step++)
      for (int i = 0; i < in_N; i++){
        pvmtmlwe_mul_by_xai(pvw->tmp->tmlwe, tmp_arr[i], a_odd[i]);
        pvmtmlwe_copy(tmp_arr[i], pvw->tmp->tmlwe);
      }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double bin_us = (t1.tv_sec-t0.tv_sec)*1e6 + (t1.tv_nsec-t0.tv_nsec)/1e3;
    /* Hom-Tr sub_a timing */
    for (int i = 0; i < in_N; i++) pvmtmlwe_copy(tmp_arr[i], acc_bin[i]);
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (size_t step = 0; step < pvw->h; step++)
      sab_pvw_sub_a_homtr(tmp_arr, (const uint64_t*)a_odd, pvw);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ht_us2 = (t1.tv_sec-t0.tv_sec)*1e6 + (t1.tv_nsec-t0.tv_nsec)/1e3;
    printf("SUBA TIMING: plaintext=%.0f us  Hom-Tr=%.0f us  ratio=%.2fx\n",
        bin_us, ht_us2, ht_us2/bin_us);
    free_pvmtmlwe_array(tmp_arr, in_N);
  }

  free_polynomial(p1); free_polynomial(p2);
  free_pvmtmlwe_array(acc_bin, in_N);
  free_pvmtmlwe_array(acc_ht, in_N);
  free(a_odd);
  return 0;
}
