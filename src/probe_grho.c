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
  int coeff_max = 3;
  {
    const char * e = getenv("SAB_GRHO_COEFF_MAX");
    if(e) coeff_max = atoi(e);
    if(coeff_max < 1) coeff_max = 1;
  }
  const int signed_cycle[6] = {1, -1, 2, -2, 3, -3};
  const bool use_neg = getenv("SAB_GRHO_NEG") != NULL;
  int bumped = 0;
  for (int i = 0; i < in_N; i++)
    if(input_key->s[0]->coeffs[i] == 1)
      input_key->s[0]->coeffs[i] = use_neg ?
          signed_cycle[bumped++ % 6] : 1 + (bumped++ % coeff_max);
  if(bumped != h){ printf("support mismatch %d != %d\n", bumped, h); return 1; }
  /* r_prec must bound interior gaps AND the final wrap gap (keygen checks
   * previous < 2^r_prec), so derive it from the actual support */
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
  printf("gaussian key: h=%d coeff_max=%d, max_gap=%lu r_prec=%lu\n",
      bumped, coeff_max, (unsigned long) max_gap, (unsigned long) r_prec);

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
  const int64_t grid = 1LL << (64 - prec);
  sab_pvw_setup_tv_xb(acc, input->b->coeffs, pvw_tv, pvw);
  sab_pvw_blind_rotate_gaussian(acc, input, pvw);
  printf("pvw gaussian blind rotate done\n");

  /* 3-way arm is opt-in only: the binary path mod-switches a WITHOUT
   * round-to-odd, so its a-vector differs and the comparison is not an
   * equivalence check -- it only demonstrates the parity divergence */
  int bin_mism = -1;
  if(getenv("SAB_GRHO_3WAY") && coeff_max == 1){
    SAB_PVW_Key pvw_bin = sab_pvw_new_binary_key(input_key, pvw_key, prec, h,
        r_prec, 1, bg_bit);
    PVW_TMLWE * accb = pvmtmlwe_alloc_new_sample_array(in_N, out_k, r, out_N);
    sab_pvw_setup_tv_xb(accb, input->b->coeffs, pvw_tv, pvw_bin);
    sab_pvw_blind_rotate_binary(accb, input, pvw_bin);
    bin_mism = 0;
    TorusPolynomial pg = polynomial_new_torus_polynomial(out_N);
    TorusPolynomial pb = polynomial_new_torus_polynomial(out_N);
    for (int lane = 0; lane < r; lane++)
      for (int j = 0; j < in_N; j++){
        lane_phase(pg, acc[j], pvw_key, lane, out_N);
        lane_phase(pb, accb[j], pvw_key, lane, out_N);
        if((((int64_t) pg->coeffs[0] + grid / 2) >> (64 - prec))
            != (((int64_t) pb->coeffs[0] + grid / 2) >> (64 - prec))) bin_mism++;
      }
    free_polynomial(pg); free_polynomial(pb);
    free_pvmtmlwe_array(accb, in_N);
    free_sab_pvw_key(pvw_bin);
    printf("PVWGAUSS vs PVWBINARY: mismatch %d / %d -- %s\n", bin_mism,
        r * in_N, bin_mism == 0 ? "Pass(ga machinery OK)" : "FAIL(ga machinery)");
  }

  /* single-step minimal repro (HANDOFF 6e): one sub_a_ga application vs
   * the plain monomial multiplication it must equal for coeff=1.
   * sub_a_ga indexes p[i] over in_N coefficients, so use full arrays. */
  if(getenv("SAB_GRHO_STEPTEST")){
    PVW_TMLWE * in_arr = pvmtmlwe_alloc_new_sample_array(in_N, out_k, r, out_N);
    PVW_TMLWE * got_arr = pvmtmlwe_alloc_new_sample_array(in_N, out_k, r, out_N);
    PVW_TMLWE ref = pvmtmlwe_alloc_new_sample(out_k, r, out_N);
    TorusPolynomial * msg = polynomial_new_array_of_torus_polynomials(out_N, r);
    for (int lane = 0; lane < r; lane++)
      for (int c = 0; c < out_N; c++)
        msg[lane]->coeffs[c] = int2torus((7 * lane + 3 * c) & 7, prec);
    PVW_TMLWE base = pvmtmlwe_new_noiseless_trivial_sample(msg, out_k, r, out_N);
    TorusPolynomial p1 = polynomial_new_torus_polynomial(out_N);
    TorusPolynomial p2 = polynomial_new_torus_polynomial(out_N);
    uint64_t * a_arr = (uint64_t *) safe_malloc(sizeof(uint64_t) * in_N);
    const int log_N2s = (int) log2(2 * out_N);
    for (int ai = 0; ai < 3; ai++){
      const uint64_t a0 = (uint64_t)(2 * ai + 1);
      for (int i = 0; i < in_N; i++){
        pvmtmlwe_copy(in_arr[i], base);
        if(ai < 2){
          a_arr[i] = a0;                    /* uniform mode */
        }else{
          uint64_t v = torus2int(input->a[0]->coeffs[i], log_N2s);
          if(!(v & 1)) v = (v - 1) & (2 * out_N - 1);
          a_arr[i] = v;                     /* diverse real odd_a */
        }
      }
      pvmtmlwe_mul_by_xai(ref, in_arr[0], a_arr[0]);
      pvmtmlwe_copy(got_arr[0], in_arr[0]);
      sab_pvw_sub_a_ga(got_arr, (const uint64_t *) a_arr,
          pvw->s_coff[0][0], pvw);
      int step_mism = 0;
      for (int lane = 0; lane < r; lane++){
        lane_phase(p1, ref, pvw_key, lane, out_N);
        lane_phase(p2, got_arr[0], pvw_key, lane, out_N);
        for (int c = 0; c < out_N; c++)
          if((((int64_t) p1->coeffs[c] + grid / 2) >> (64 - prec))
              != (((int64_t) p2->coeffs[c] + grid / 2) >> (64 - prec)))
            step_mism++;
      }
      printf("STEPTEST a0=%lu: mismatch %d / %d -- %s\n",
          (unsigned long) a0, step_mism, r * out_N,
          step_mism == 0 ? "OK" : "BAD");
    }
    free(a_arr);
    free_polynomial(p1); free_polynomial(p2);
    free_pvmtmlwe(base); free_pvmtmlwe(ref);
    free_pvmtmlwe_array(got_arr, in_N);
    free_pvmtmlwe_array(in_arr, in_N);
    free_array_of_polynomials(msg, r);
  }

  /* chain isolation: gaussian sparse_mul vs a hand-built reference chain
   * (butterfly + per-slot odd-a monomial mul) -- mathematically equal per
   * step for coeff=1; isolates sub_a_ga under diverse slot values */
  if(getenv("SAB_GRHO_CHAINTEST")){
    const int log_N2c = (int) log2(2 * out_N);
    uint64_t * odd_a = (uint64_t *) safe_malloc(sizeof(uint64_t) * in_N);
    for (int i = 0; i < in_N; i++){
      uint64_t v = torus2int(input->a[0]->coeffs[i], log_N2c);
      if(!(v & 1)) v = (v - 1) & (2 * out_N - 1);
      odd_a[i] = v;
    }
    PVW_TMLWE * ga = pvmtmlwe_alloc_new_sample_array(in_N, out_k, r, out_N);
    PVW_TMLWE * rf = pvmtmlwe_alloc_new_sample_array(in_N, out_k, r, out_N);
    sab_pvw_setup_tv_xb(ga, input->b->coeffs, pvw_tv, pvw);
    sab_pvw_setup_tv_xb(rf, input->b->coeffs, pvw_tv, pvw);
    sab_pvw_sparse_mul_gaussian(ga, (const uint64_t *) odd_a, 0, pvw);
    for (size_t step = 0; step < pvw->h; step++){
      sab_pvw_RGSW_monomial_mul(rf, pvw->s[0][step], pvw);
      for (int i = 0; i < in_N; i++){
        /* mirror sab_pvw_sub_a_binary: via tmp, not in place */
        pvmtmlwe_mul_by_xai(pvw->tmp->tmlwe, rf[i], odd_a[i]);
        pvmtmlwe_copy(rf[i], pvw->tmp->tmlwe);
      }
    }
    sab_pvw_RGSW_monomial_mul(rf, pvw->s[0][pvw->h], pvw);
    int chain_mism = 0;
    TorusPolynomial q1 = polynomial_new_torus_polynomial(out_N);
    TorusPolynomial q2 = polynomial_new_torus_polynomial(out_N);
    for (int lane = 0; lane < r; lane++)
      for (int j = 0; j < in_N; j++){
        lane_phase(q1, ga[j], pvw_key, lane, out_N);
        lane_phase(q2, rf[j], pvw_key, lane, out_N);
        if((((int64_t) q1->coeffs[0] + grid / 2) >> (64 - prec))
            != (((int64_t) q2->coeffs[0] + grid / 2) >> (64 - prec)))
          chain_mism++;
      }
    free_polynomial(q1); free_polynomial(q2);
    free_pvmtmlwe_array(ga, in_N);
    free_pvmtmlwe_array(rf, in_N);
    free(odd_a);
    printf("CHAINTEST gauss-vs-reference: mismatch %d / %d -- %s\n",
        chain_mism, r * in_N,
        chain_mism == 0 ? "OK(schedule consistent)" : "BAD(schedule bug)");
  }

  int mism = 0;
  int64_t max_dev = 0;
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
    /* canonical scalar pipeline: setup_tv_xb offset (1/(2*2^b_prec))
     * differs from the legacy setup_single_tv (1/(2*b_prec)) -- use the
     * library's own wo_extract so the oracle wiring is exactly canonical */
    TRLWE * sacc = trlwe_alloc_new_sample_array(in_N, in_k, out_N);
    sab_rlwe_bootstrap_wo_extract(sacc, input, tv, oracle);

    TorusPolynomial ps = polynomial_new_torus_polynomial(out_N);
    TorusPolynomial pp = polynomial_new_torus_polynomial(out_N);
    for (int j = 0; j < in_N; j++){
      trlwe_phase(ps, sacc[j], lane_key);
      lane_phase(pp, acc[j], pvw_key, lane, out_N);
      {
        const int64_t d0 = (int64_t) ps->coeffs[0] - (int64_t) pp->coeffs[0];
        const int64_t ad = d0 < 0 ? -d0 : d0;
        if(ad > max_dev) max_dev = ad;
      }
      if((((int64_t) ps->coeffs[0] + grid / 2) >> (64 - prec))
          != (((int64_t) pp->coeffs[0] + grid / 2) >> (64 - prec))){
        if(mism < 5) printf("MISMATCH lane=%d slot=%d\n", lane, j);
        mism++;
      }
    }
    free_polynomial(ps); free_polynomial(pp);
    free_trlwe_array(sacc, in_N);
    free_trlwe(tv);
    printf("lane %d oracle done\n", lane);
  }
  printf("GRHO GATE: mismatch %d / %d -- %s; pair noise max dev log2 = %.2f (message budget 2^-%d)\n",
      mism, r * in_N, mism == 0 ? "Pass" : "FAIL",
      log2((double) max_dev + 1.0), prec + 1);
  return mism == 0 ? 0 : 1;
}
