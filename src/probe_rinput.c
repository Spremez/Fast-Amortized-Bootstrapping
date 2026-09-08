/* probe_rinput.c -- r-input batching + Hom-Tr correctness gate (stage396,
 * obligations I-7/I-8).
 *
 * Arm A (interleaved): one PVW_TMLWE (r=1) per slot over R = Z[X]/(X^N+1),
 *   N = out_N, lanes at residues (Y = X^2, d = N/2), setup + butterfly with
 *   Psi-corrected wraps + Hom-Tr sub_a + per-step rescale.
 * Arm B (oracle): two INDEPENDENT scalar SAB bootstraps (out ring d = N/2,
 *   granularity 2d), one per input ciphertext, same key, same TVs.
 * Gate: per slot t, lane l: quantized LUT value of interleaved phase
 *   coefficient l == scalar oracle phase coefficient 0. Plus noise pair
 *   accounting (I-8) and same-build timing.
 *
 * TVs quantized with 1 guard bit (v << (63-p), lemma HT-8) on BOTH arms. */
#include <sab_rinput.h>
#include <sab.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <time.h>

static void rinput_phase(TorusPolynomial out, PVW_TMLWE in,
    PVW_TMLWE_Key key){
  memset(out->coeffs, 0, sizeof(out->coeffs[0]) * out->N);
  for (size_t idx = 0; idx < (size_t) in->k; idx++){
    polynomial_mul_addto_torus(out, in->a[idx], key->s[idx][0]);
  }
  polynomial_sub_torus_polynomials(out, in->b[0], out);
}

static double now_us(void){
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return ts.tv_sec * 1e6 + ts.tv_nsec / 1e3;
}

/* Minimal wo-extract oracle key: selectors + aut_minus1 + tmp pool only
 * (avoids new_sparse_amortized_bootstrapping's packing/hw KS construction,
 * which is not exercised by sab_rlwe_bootstrap_wo_extract and which crashes
 * in the LOCAL MinGW build for some dims). Semantics identical to the
 * stock binary-key oracle path. */
static SAB_Key min_oracle_key(TRLWE_Key input_key, TRGSW_Key skey,
    uint64_t b_prec, uint64_t h, uint64_t r_prec){
  SAB_Key res = (SAB_Key) calloc(1, sizeof(*res));
  res->in_N = input_key->s[0]->N;
  res->in_k = input_key->k;
  res->out_N = skey->trlwe_key->s[0]->N;
  res->out_k = skey->trlwe_key->k;
  res->h = h;
  res->r_prec = r_prec;
  res->b_prec = b_prec;
  uint64_t gens[1] = {2 * res->out_N - 1};
  res->aut_minus1 = trlwe_new_automorphism_KS_keyset_2(skey->trlwe_key, gens,
      1, skey->l, skey->Bg_bit)[0];
  TRGSW tmp = trgsw_alloc_new_sample(skey->l, skey->Bg_bit, (int) res->out_k,
      (int) res->out_N);
  res->s = (TRGSW_DFT ***) safe_malloc(sizeof(TRGSW_DFT **) * res->in_k);
  for (size_t ki = 0; ki < res->in_k; ki++){
    res->s[ki] = (TRGSW_DFT **) safe_malloc(sizeof(TRGSW_DFT *) * (h + 1));
    uint64_t cnt = 0, prev = res->in_N;
    for (size_t scan = 0; scan < res->in_N; scan++){
      const uint64_t cur = res->in_N - scan - 1;
      if(input_key->s[ki]->coeffs[cur] == 0) continue;
      res->s[ki][cnt] = trgsw_alloc_new_DFT_sample_array((int) r_prec,
          skey->l, skey->Bg_bit, (int) res->out_k, (int) res->out_N);
      RGSW_encrypt_bits(res->s[ki][cnt], tmp, skey, prev - cur, r_prec);
      prev = cur;
      cnt++;
    }
    res->s[ki][cnt] = trgsw_alloc_new_DFT_sample_array((int) r_prec, skey->l,
        skey->Bg_bit, (int) res->out_k, (int) res->out_N);
    RGSW_encrypt_bits(res->s[ki][cnt], tmp, skey, prev, r_prec);
  }
  free_trgsw(tmp);
  res->tmp = (tmp_pool) calloc(1, sizeof(*res->tmp));
  res->tmp->rlwe_dft = trlwe_alloc_new_DFT_sample((int) res->out_k,
      (int) res->out_N);
  res->tmp->rlwe = trlwe_alloc_new_sample((int) res->out_k, (int) res->out_N);
  res->tmp->rlwe_poly1 = trlwe_alloc_new_sample_array((int) res->in_N,
      (int) res->out_k, (int) res->out_N);
  res->tmp->rlwe_poly2 = trlwe_alloc_new_sample_array((int) res->in_N,
      (int) res->out_k, (int) res->out_N);
  return res;
}

int main(void){
  setvbuf(stdout, NULL, _IONBF, 0);
  int in_N = 256, out_N = 2048, h = 6, prec = 3, bg_bit = 23, l = 1;
  {
    const char *e;
    if((e = getenv("SAB_RINPUT_IN_N"))) in_N = atoi(e);
    if((e = getenv("SAB_RINPUT_OUT_N"))) out_N = atoi(e);
    if((e = getenv("SAB_RINPUT_H"))) h = atoi(e);
  }
  const int d = out_N / 2;
  const int in_k = 1, out_k = 1;
  printf("rinput probe: in_N=%d out_N=%d (d=%d) h=%d prec=%d\n",
      in_N, out_N, d, h, prec);

  /* shared sparse input key (both inputs encrypted under it) */
  TRLWE_Key input_key, packing_key;
  RS_sparse_binary_key(&input_key, in_N, in_k, h, pow(2, -15), 6);
  RS_sparse_binary_key(&packing_key, in_N, in_k, h, pow(2, -44), 6);
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
  printf("key: h=%d r_prec=%lu (max_gap=%lu)\n", h, (unsigned long) r_prec,
      (unsigned long) max_gap);

  /* two distinct inputs */
  TorusPolynomial msg0 = polynomial_new_torus_polynomial(in_N);
  TorusPolynomial msg1 = polynomial_new_torus_polynomial(in_N);
  for (int i = 0; i < in_N; i++){
    msg0->coeffs[i] = int2torus(i & 7, prec);
    msg1->coeffs[i] = int2torus((3 * i + 1) & 7, prec);
  }
  TRLWE in0 = trlwe_new_sample(msg0, input_key);
  TRLWE in1 = trlwe_new_sample(msg1, input_key);

  /* TVs: distinct LUTs per lane, 1 guard bit (v << (63 - p) = int2torus(.,p+1)) */
  TorusPolynomial tv0 = polynomial_new_torus_polynomial(d);
  TorusPolynomial tv1 = polynomial_new_torus_polynomial(d);
  for (int q = 0; q < d; q++){
    tv0->coeffs[q] = int2torus(q & 7, prec + 1);
    tv1->coeffs[q] = int2torus((5 * q + 2) & 7, prec + 1);
  }

  /* Arm A: interleaved accumulator (single-body PVW_TMLWE) */
  PVW_TMLWE_Key pvw_key = pvmtmlwe_new_binary_key(out_N, out_k, 1,
      pow(2, -70));
  SAB_RINPUT_Key ri = sab_rinput_new_key(input_key, pvw_key, prec, h,
      r_prec, l, bg_bit);
  PVW_TMLWE *acc = pvmtmlwe_alloc_new_sample_array(in_N, out_k, 1, out_N);
  /* G0: setup-only gate on a separate array vs plaintext expectation */
  {
    PVW_TMLWE *su = pvmtmlwe_alloc_new_sample_array(in_N, out_k, 1, out_N);
    sab_rinput_setup_tv(su, in0, in1, tv0, tv1, ri);
    const int log_2d = (int) log2(2 * d);
    const uint64_t prec_offset = 1ULL << (64 - prec - 1);
    int setup_mism = 0;
    for (int t = 0; t < in_N; t++){
      uint64_t exp[out_N];
      memset(exp, 0, sizeof(exp));
      for (int lane = 0; lane < 2; lane++){
        TRLWE in = lane == 0 ? in0 : in1;
        TorusPolynomial tv = lane == 0 ? tv0 : tv1;
        const uint64_t bbar = torus2int(in->b->coeffs[t] + prec_offset,
            log_2d);
        for (int q = 0; q < d; q++){
          const uint64_t pos = (q + bbar) % (2 * d);
          if(pos < (uint64_t) d)
            exp[lane + 2 * pos] += tv->coeffs[q];
          else
            exp[lane + 2 * (pos - d)] -= tv->coeffs[q];
        }
      }
      for (int i = 0; i < out_N; i++){
        if(su[t]->b[0]->coeffs[i] != exp[i]
            || su[t]->a[0]->coeffs[i] != 0){
          if(setup_mism < 5)
            printf("G0 slot%d coef%d: got %lu want %lu (a=%lu)\n", t, i,
                (unsigned long) su[t]->b[0]->coeffs[i],
                (unsigned long) exp[i],
                (unsigned long) su[t]->a[0]->coeffs[i]);
          setup_mism++;
        }
      }
    }
    printf("G0 SETUP GATE: mismatch %d -- %s\n", setup_mism,
        setup_mism == 0 ? "Pass" : "FAIL");
    free_pvmtmlwe_array(su, in_N);
  }
  double t0 = now_us();
  sab_rinput_bootstrap_wo_extract(acc, in0, in1, tv0, tv1, ri);
  double t_int = now_us() - t0;
  printf("arm A (interleaved, 2 inputs): %.0f us\n", t_int);
  /* Arm B: two independent scalar oracles (out ring d, granularity 2d) */
  TorusPolynomial p1 = polynomial_new_torus_polynomial(d);
  TorusPolynomial p2 = polynomial_new_torus_polynomial(out_N);
  double t_or = 0;
  int mism = 0, lane_mism[2] = {0, 0};
  uint64_t pair_dev_max = 0;
  for (int lane = 0; lane < 2; lane++){
    TRLWE in = lane == 0 ? in0 : in1;
    TorusPolynomial tv = lane == 0 ? tv0 : tv1;
    TRLWE_Key lane_key = trlwe_new_binary_key(d, out_k, pow(2, -70));
    TRGSW_Key skey = trgsw_new_key(lane_key, l, bg_bit);
    SAB_Key oracle = min_oracle_key(input_key, skey, prec, h, r_prec);
    TRLWE tv_rlwe = trlwe_alloc_new_sample(in_k, d);
    memset(tv_rlwe->a[0]->coeffs, 0, sizeof(tv_rlwe->a[0]->coeffs[0]) * d);
    memcpy(tv_rlwe->b->coeffs, tv->coeffs, sizeof(tv->coeffs[0]) * d);
    TRLWE *sacc = trlwe_alloc_new_sample_array(in_N, in_k, d);
    double tb = now_us();
    sab_rlwe_bootstrap_wo_extract(sacc, in, tv_rlwe, oracle);
    t_or += now_us() - tb;
    for (int t = 0; t < in_N; t++){
      trlwe_phase(p1, sacc[t], lane_key);
      rinput_phase(p2, acc[t], pvw_key);
      /* scalar message at v*2^(60); interleaved final keeps the x2: 2v*2^(60) */
      const int64_t v_scalar =
          (((int64_t) p1->coeffs[0]) + ((int64_t) 1 << (63 - prec - 1)))
          >> (63 - prec);
      const int64_t v_int =
          (((int64_t) p2->coeffs[lane]) + ((int64_t) 1 << (64 - prec - 1)))
          >> (64 - prec);
      if(v_scalar != v_int){ mism++; lane_mism[lane]++; }
      if(t < 6 && lane == 0)
        printf("  t%d lane0: v_scalar=%lld v_int=%lld (raw sc=%lld int/2=%lld)\n",
            t, (long long) v_scalar, (long long) v_int,
            (long long) (((int64_t) p1->coeffs[0]) >> (63 - prec)),
            (long long) ((((int64_t) p2->coeffs[lane]) + ((int64_t) 1 << 60)) >> 61));
      /* pair noise: de-double the interleaved side before comparing */
      const int64_t dev = (int64_t) p1->coeffs[0]
          - (((int64_t) p2->coeffs[lane]) >> 1);
      const int64_t adev = dev < 0 ? -dev : dev;
      if((uint64_t) adev > pair_dev_max) pair_dev_max = (uint64_t) adev;
    }
    free_trlwe_array(sacc, in_N);
    free_trlwe(tv_rlwe);
    free_trlwe_key(lane_key);
    free_trgsw_key(skey);
  }
  printf("arm B (2x scalar oracle): %.0f us\n", t_or);
  printf("RINPUT GATE: mismatch %d / %d (lane0 %d, lane1 %d) -- %s\n", mism,
      2 * in_N, lane_mism[0], lane_mism[1], mism == 0 ? "Pass" : "FAIL");
  printf("RINPUT NOISE: pair max dev log2 = %.2f (extra vs scalar path)\n",
      log2((double) pair_dev_max + 1.0));
  printf("RINPUT TIMING: interleaved=%.0f us  2x-scalar=%.0f us  "
      "ratio(inter/2xscalar)=%.2fx\n", t_int, t_or, t_int / t_or);

  free_polynomial(p1); free_polynomial(p2);
  free_pvmtmlwe_array(acc, in_N);
  free_sab_rinput_key(ri);
  free_pvmtmlwe_key(pvw_key);
  free_polynomial(tv0); free_polynomial(tv1);
  free_trlwe(in0); free_trlwe(in1);
  free_polynomial(msg0); free_polynomial(msg1);
  free_trlwe_key(input_key); free_trlwe_key(packing_key);
  return 0;
}
