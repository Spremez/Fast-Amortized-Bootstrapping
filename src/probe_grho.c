/* probe_grho.c -- G-rho equivalence gate (S4/WS-C step 2). BUILD+RUN PENDING
 * (design frozen 2026-09-04; see HANDOFF 6c for the exact dell commands).
 *
 * Gate: multi-body gaussian (rho-SAB) blind rotation vs the scalar gaussian
 * oracle on identical keys/input/test vectors, compared at the message grid.
 * First gate uses positive coefficients in {1,2,3} (negative-exponent
 * convention check pending); in_N >= 256 on dell (toy N=16 SIGSEGVs there).
 */
#include <sab_pvw.h>
#include <sab.h>
#include <mosfhet.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static void lane_phase(TorusPolynomial out, PVW_TMLWE in, PVW_TMLWE_Key key,
    int lane, int N){
  /* b_lane - a*s[0][lane], mirroring trlwe_phase */
  memset(out->coeffs, 0, sizeof(out->coeffs[0]) * N);
  polynomial_mul_addto_torus(out, in->a[0], key->s[0][lane]);
  polynomial_sub_torus_polynomials(out, in->b[lane], out);
}

int main(void){
  setvbuf(stdout, NULL, _IONBF, 0);
  const int in_N = 256, out_N = 1024, in_k = 1, out_k = 1;
  const int bg_bit = 23, prec = 3, h = 6, r = 2;

  TRLWE_Key input_key, packing_key;
  RS_sparse_binary_key(&input_key, in_N, in_k, h, pow(2, -15), 5);
  RS_sparse_binary_key(&packing_key, in_N, in_k, h, pow(2, -44), 5);
  int bumped = 0;
  for (int i = 0; i < in_N; i++)
    if(input_key->s[0]->coeffs[i] == 1)
      input_key->s[0]->coeffs[i] = 1 + (bumped++ % 3);
  if(bumped != h){ printf("support mismatch %d != %d\n", bumped, h); return 1; }
  printf("gaussian key: h=%d coeffs in {1,2,3}, r_prec=%lu\n", bumped,
      (unsigned long) r_prec);

  PVW_TMLWE_Key pvw_key = pvmtmlwe_new_binary_key(out_N, out_k, r, pow(2, -70));
  SAB_PVW_Key pvw = sab_pvw_new_gaussian_key(input_key, pvw_key, prec, h,
      r_prec, 1, bg_bit);
  printf("pvw gaussian key built (aut family %d keys)\n", out_N);

  TorusPolynomial input_msg = polynomial_new_torus_polynomial(in_N);
  for (int i = 0; i < in_N; i++) input_msg->coeffs[i] = int2torus(i & 7, prec);
  TRLWE input = trlwe_new_sample(input_msg, input_key);
  TorusPolynomial * tv_msg = polynomial_new_array_of_torus_polynomials(out_N, r);
  for (int lane = 0; lane < r; lane++)
    for (int c = 0; c < out_N; c++)
      tv_msg[lane]->coeffs[c] = int2torus((3 * lane + c) & 7, prec);
  PVW_TMLWE pvw_tv = pvmtmlwe_new_noiseless_trivial_sample(tv_msg, out_k, r, out_N);

  PVW_TMLWE * acc = pvmtmlwe_alloc_new_sample_array(in_N, out_k, r, out_N);
  sab_pvw_setup_tv_xb(acc, input->b->coeffs, pvw_tv, pvw);
  sab_pvw_blind_rotate_gaussian(acc, input, pvw);
  printf("pvw gaussian blind rotate done\n");

  int mism = 0;
  const int64_t grid = 1LL << (64 - prec);
  for (int lane = 0; lane < r; lane++){
    TRLWE_Key lane_key = trlwe_alloc_key(out_N, out_k, pvw_key->sigma);
    memcpy(lane_key->s[0]->coeffs, pvw_key->s[0][lane]->coeffs,
        sizeof(lane_key->s[0]->coeffs[0]) * out_N);
    TRGSW_Key skey = trgsw_new_key(lane_key, 1, bg_bit);
    SAB_Key oracle = new_sparse_amortized_bootstrapping(input_key,
        packing_key, skey, prec, 14, 2, 12, 1, h, r_prec, false, false, true);

    TRLWE tv = trlwe_alloc_new_sample(in_k, out_N);
    memset(tv->a[0]->coeffs, 0, sizeof(tv->a[0]->coeffs[0]) * out_N);
    memcpy(tv->b->coeffs, tv_msg[lane]->coeffs,
        sizeof(tv->b->coeffs[0]) * out_N);
    TRLWE * sacc = trlwe_alloc_new_sample_array(in_N, in_k, out_N);
    uint64_t * b_mod = (uint64_t *) safe_malloc(sizeof(uint64_t) * in_N);
    const int log_N2 = (int) log2(2 * out_N);
    for (int i = 0; i < in_N; i++)
      b_mod[i] = torus2int(input->b->coeffs[i] + (1ULL << (64 - prec - 1)),
          log_N2);
    TRLWE * tv_arr = setup_single_tv(b_mod, tv, oracle);
    sab_blind_rotate(sacc, input, oracle);

    TorusPolynomial ps = polynomial_new_torus_polynomial(out_N);
    TorusPolynomial pp = polynomial_new_torus_polynomial(out_N);
    for (int j = 0; j < in_N; j++){
      trlwe_phase(ps, sacc[j], lane_key);
      lane_phase(pp, acc[j], pvw_key, lane, out_N);
      if((((int64_t) ps->coeffs[0] + grid / 2) >> (64 - prec))
          != (((int64_t) pp->coeffs[0] + grid / 2) >> (64 - prec))){
        if(mism < 5) printf("MISMATCH lane=%d slot=%d\n", lane, j);
        mism++;
      }
    }
    free_polynomial(ps); free_polynomial(pp);
    free(b_mod);
    free_trlwe_array(tv_arr, in_N);
    free_trlwe(tv);
    free(sacc);
    printf("lane %d oracle done\n", lane);
  }
  printf("GRHO GATE: mismatch %d / %d -- %s\n", mism, r * in_N,
      mism == 0 ? "Pass" : "FAIL");
  return mism == 0 ? 0 : 1;
}
