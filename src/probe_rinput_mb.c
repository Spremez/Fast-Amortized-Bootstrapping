/* probe_rinput_mb.c -- JOINT r1-input x r2-LUT gate (HT-10 C-level, I-5+).
 *
 * One interleaved multi-body blind rotation: r1=2 distinct inputs, r2=2
 * LUT bodies per ciphertext (out key r=2). Gate: per slot t, lane l,
 * body j: quantized extraction of the joint pipeline == scalar SAB
 * oracle for (input l, TV_j), 0 mismatches expected. Pair noise per
 * channel + same-build timing vs r1*r2 scalar bootstraps.
 * Env: SAB_RINPUT_IN_N / OUT_N / H / RPREC / REPS (target 7 at FINAL). */
#include <sab_rinput.h>
#include <sab.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <time.h>

#define LANES 2
#define BODIES 2

static void mb_phase(TorusPolynomial out, PVW_TMLWE in, PVW_TMLWE_Key key,
    int body){
  memset(out->coeffs, 0, sizeof(out->coeffs[0]) * out->N);
  for (size_t idx = 0; idx < (size_t) in->k; idx++)
    polynomial_mul_addto_torus(out, in->a[idx], key->s[idx][body]);
  polynomial_sub_torus_polynomials(out, in->b[body], out);
}

static double now_us(void){
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return ts.tv_sec * 1e6 + ts.tv_nsec / 1e3;
}

static int run_trial(int trial, int reps, double * t_joint, double * t_or){
  setvbuf(stdout, NULL, _IONBF, 0);
  int in_N = 256, out_N = 2048, h = 6, prec = 3;
  { const char *e;
    if((e = getenv("SAB_RINPUT_IN_N"))) in_N = atoi(e);
    if((e = getenv("SAB_RINPUT_OUT_N"))) out_N = atoi(e);
    if((e = getenv("SAB_RINPUT_H"))) h = atoi(e); }
  const int d = out_N / LANES, in_k = 1, out_k = 1, l = 1, bg = 23;
  printf("joint trial %d/%d: in_N=%d out_N=%d (d=%d) h=%d r1=%d r2=%d\n",
      trial + 1, reps, in_N, out_N, d, h, LANES, BODIES);

  TRLWE_Key input_key = NULL, packing_key = NULL;
  RS_sparse_binary_key(&input_key, in_N, in_k, h, pow(2, -15), 7);
  RS_sparse_binary_key(&packing_key, in_N, in_k, h, pow(2, -44), 7);
  if(input_key == NULL || input_key->s[0] == NULL){
    printf("RS keygen FAILED\n"); return 1; }
  uint64_t max_gap = 0, prev = in_N, r_prec = 1;
  for (int scan = 0; scan < in_N; scan++){
    const int cur = in_N - scan - 1;
    if(input_key->s[0]->coeffs[cur] == 0) continue;
    if((uint64_t)(prev - cur) > max_gap) max_gap = prev - cur;
    prev = cur;
  }
  if(prev > max_gap) max_gap = prev;
  while((1ULL << r_prec) <= max_gap) r_prec++;
  { const char *e = getenv("SAB_RINPUT_RPREC");
    if(e) r_prec = (uint64_t) atoi(e); }

  TorusPolynomial msg[LANES];
  TRLWE ins[LANES];
  for (int l_ = 0; l_ < LANES; l_++){
    msg[l_] = polynomial_new_torus_polynomial(in_N);
    for (int i = 0; i < in_N; i++)
      msg[l_]->coeffs[i] = int2torus((i + 3 * l_) & 7, prec);
    ins[l_] = trlwe_new_sample(msg[l_], input_key);
  }
  /* tv[lane*bodies + body], two guard bits (HT-8) */
  TorusPolynomial tv[LANES * BODIES];
  for (int x = 0; x < LANES * BODIES; x++){
    tv[x] = polynomial_new_torus_polynomial(d);
    for (int q = 0; q < d; q++)
      tv[x]->coeffs[q] = int2torus((5 * x + 2 * q + 1) & 7, prec + 2);
  }

  /* joint pipeline: multi-body output key (r = BODIES) */
  PVW_TMLWE_Key pvw_key = pvmtmlwe_new_binary_key(out_N, out_k, BODIES,
      pow(2, -70));
  SAB_RINPUT_Key ri = sab_rinput_new_key(input_key, pvw_key, prec, h,
      r_prec, l, bg);
  PVW_TMLWE * acc = pvmtmlwe_alloc_new_sample_array(in_N, out_k, BODIES,
      out_N);
  sab_rinput_setup_tv_mb(acc, ins, tv, BODIES, ri);
  double t0 = now_us();
  sab_rinput_blind_rotate(acc, ins[0], ins[1], ri);
  *t_joint = now_us() - t0;

  /* oracles: (lane, body) scalar bootstraps + gate + pair noise */
  TorusPolynomial ph = polynomial_new_torus_polynomial(out_N);
  TorusPolynomial p1 = polynomial_new_torus_polynomial(d);
  int mism = 0, mism_ch[LANES * BODIES] = {0};
  uint64_t pair_max[LANES * BODIES] = {0};
  double pair_sq[LANES * BODIES] = {0};
  long pair_cnt[LANES * BODIES] = {0};
  double t_or_all = 0;
  *t_or = 0;
  for (int l_ = 0; l_ < LANES; l_++)
    for (int j = 0; j < BODIES; j++){
      const int ch = l_ * BODIES + j;
      TRLWE_Key lane_key = trlwe_new_binary_key(d, out_k, pow(2, -70));
      TRGSW_Key skey = trgsw_new_key(lane_key, l, bg);
      SAB_Key oracle = min_oracle_key(input_key, skey, prec, h, r_prec);
      TRLWE tv_rlwe = trlwe_alloc_new_sample(in_k, d);
      memset(tv_rlwe->a[0]->coeffs, 0, sizeof(tv_rlwe->a[0]->coeffs[0]) * d);
      memcpy(tv_rlwe->b->coeffs, tv[ch]->coeffs, sizeof(tv[0]->coeffs[0]) * d);
      TRLWE * sacc = trlwe_alloc_new_sample_array(in_N, in_k, d);
      double tb = now_us();
      sab_rlwe_bootstrap_wo_extract(sacc, ins[l_], tv_rlwe, oracle);
      t_or_all += now_us() - tb;
      for (int t = 0; t < in_N; t++){
        trlwe_phase(p1, sacc[t], lane_key);
        mb_phase(ph, acc[t], pvw_key, j);
        const int64_t v_scalar =
            (((int64_t) p1->coeffs[0]) + ((int64_t) 1 << (62 - prec - 1)))
            >> (62 - prec);
        const int64_t v_joint =
            (((int64_t) ph->coeffs[l_]) + ((int64_t) 1 << (62 - prec)))
            >> (62 - prec + 1);
        if(v_scalar != v_joint){ mism++; mism_ch[ch]++; }
        const int64_t dev = (int64_t) p1->coeffs[0]
            - (((int64_t) ph->coeffs[l_]) >> 1);
        const int64_t adev = dev < 0 ? -dev : dev;
        if((uint64_t) adev > pair_max[ch]) pair_max[ch] = (uint64_t) adev;
        pair_sq[ch] += (double) dev * dev; pair_cnt[ch]++;
      }
      free_trlwe_array(sacc, in_N);
      free_trlwe(tv_rlwe);
      free_trlwe_key(lane_key);
      free_trgsw_key(skey);
    }
  *t_or = t_or_all;
  printf("GATE: mismatch %d / %d (per-channel %d,%d,%d,%d) -- %s\n", mism,
      LANES * BODIES * in_N, mism_ch[0], mism_ch[1], mism_ch[2], mism_ch[3],
      mism == 0 ? "Pass" : "FAIL");
  for (int ch = 0; ch < LANES * BODIES; ch++)
    printf("  ch(l=%d,j=%d): pair max %.2f rms %.2f\n", ch / BODIES,
        ch % BODIES, log2((double) pair_max[ch] + 1.0),
        log2(sqrt(pair_sq[ch] / (pair_cnt[ch] ? pair_cnt[ch] : 1)) + 1.0));
  printf("timing: joint = %.0f us, %dx-scalar = %.0f us, ratio = %.3fx\n",
      *t_joint, *t_or, *t_joint / (*t_or > 0 ? *t_or : 1));

  free_polynomial(ph); free_polynomial(p1);
  free_pvmtmlwe_array(acc, in_N);
  free_sab_rinput_key(ri);
  free_pvmtmlwe_key(pvw_key);
  for (int x = 0; x < LANES * BODIES; x++) free_polynomial(tv[x]);
  for (int l_ = 0; l_ < LANES; l_++){
    free_trlwe(ins[l_]); free_polynomial(msg[l_]); }
  free_trlwe_key(input_key); free_trlwe_key(packing_key);
  return mism == 0 ? 0 : 1;
}

int main(void){
  int reps = 1;
  { const char *e = getenv("SAB_RINPUT_REPS");
    if(e){ reps = atoi(e); if(reps < 1) reps = 1; if(reps > 64) reps = 64; } }
  int all_ok = 1;
  double tj = 0, to = 0, tj_sum = 0, to_sum = 0;
  for (int rep = 0; rep < reps; rep++){
    if(run_trial(rep, reps, &tj, &to) != 0) all_ok = 0;
    tj_sum += tj; to_sum += to;
  }
  printf("JOINT %s (%d trials); mean joint %.0f us, mean %dx-scalar %.0f us, "
      "ratio %.3fx\n", all_ok ? "ALL PASS" : "FAIL", reps, tj_sum / reps,
      to_sum / reps, tj_sum / (to_sum > 0 ? to_sum : 1));
  return all_ok ? 0 : 1;
}
