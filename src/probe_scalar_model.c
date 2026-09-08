/* probe_scalar_model.c -- locate the divergence between the C scalar
 * oracle machinery and my plaintext dim-d model.
 * T1: bare trlwe sigma_{-1} (KS) on trivial input
 * T2: NCMUX(A, B, sel=1) on trivial inputs
 * T3: bare CMUX(A, C, sel=1) on trivial inputs
 * Then staged setup/bfly/suba comparison with the oracle's public stages.
 * Env: SM_OUT_N (interleaved N; d = N/2), SM_SEED. */
#include <sab_rinput.h>
#include <sab.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

int main(void){
  setvbuf(stdout, NULL, _IONBF, 0);
  int in_N = 256, out_N = 1024, h = 6, prec = 3, bg_bit = 23, l = 1;
  { const char *e = getenv("SM_OUT_N"); if(e) out_N = atoi(e); }
  uint64_t seed0 = 1;
  { const char *e = getenv("SM_SEED"); if(e) seed0 = strtoull(e, 0, 10); }
  const int d = out_N / 2;
  printf("scalar-model probe: in_N=%d d=%d h=%d seed=%lu\n", in_N, d, h,
      (unsigned long) seed0);

  TRLWE_Key input_key = NULL, packing_key = NULL;
  for (uint64_t st_ = seed0; st_ < seed0 + 40; st_++){
    mosfhet_set_deterministic_seed(st_);
    RS_sparse_binary_key(&input_key, in_N, 1, h, pow(2, -15), 6);
    int nz_ = 0;
    for (int i = 0; i < in_N; i++) if(input_key->s[0]->coeffs[i]) nz_++;
    if(nz_ == h) break;
    free_trlwe_key(input_key);
    input_key = NULL;
  }
  if(input_key == NULL){ printf("no good key\n"); return 1; }
  RS_sparse_binary_key(&packing_key, in_N, 1, h, pow(2, -44), 6);
  uint64_t r_prec = 1, max_gap = 0, previous = in_N;
  for (int scan = 0; scan < in_N; scan++){
    const int cur = in_N - scan - 1;
    if(input_key->s[0]->coeffs[cur] == 0) continue;
    if(previous - cur > max_gap) max_gap = previous - cur;
    previous = cur;
  }
  if(previous > max_gap) max_gap = previous;
  while((1ULL << r_prec) <= max_gap) r_prec++;
  uint64_t gaps[h + 1];
  { uint64_t prev = in_N, gi = 0;
    for (int scan = 0; scan < in_N; scan++){
      const int cur = in_N - scan - 1;
      if(input_key->s[0]->coeffs[cur] == 0) continue;
      gaps[gi++] = prev - cur;
      prev = cur;
    }
    gaps[gi] = prev;
  }
  printf("r_prec=%lu gaps:", (unsigned long) r_prec);
  for (int i = 0; i <= h; i++) printf(" %lu", (unsigned long) gaps[i]);
  printf("\n");

  TorusPolynomial msg0 = polynomial_new_torus_polynomial(in_N);
  for (int i = 0; i < in_N; i++) msg0->coeffs[i] = int2torus(i & 7, prec);
  TRLWE in0 = trlwe_new_sample(msg0, input_key);
  TorusPolynomial tv0 = polynomial_new_torus_polynomial(d);
  for (int q = 0; q < d; q++) tv0->coeffs[q] = int2torus(q & 7, prec + 1);

  TRLWE_Key lane_key = trlwe_new_binary_key(d, 1, pow(2, -70));
  TRGSW_Key skey = trgsw_new_key(lane_key, l, bg_bit);
  SAB_Key oracle = new_sparse_amortized_bootstrapping(input_key, packing_key,
      skey, prec, 14, 2, 12, 1, h, r_prec, false, false, false);
  TRLWE tv_rlwe = trlwe_alloc_new_sample(1, d);
  memset(tv_rlwe->a[0]->coeffs, 0, sizeof(tv_rlwe->a[0]->coeffs[0]) * d);
  memcpy(tv_rlwe->b->coeffs, tv0->coeffs, sizeof(tv0->coeffs[0]) * d);
  TorusPolynomial sph = polynomial_new_torus_polynomial(d);

  /* ---- T1..T3 on trivial dim-d samples ---- */
  {
    TRLWE A = trlwe_alloc_new_sample(1, d);
    TRLWE B = trlwe_alloc_new_sample(1, d);
    TRLWE R = trlwe_alloc_new_sample(1, d);
    uint64_t *bv = calloc(d, sizeof(uint64_t));
    uint64_t *sig = calloc(d, sizeof(uint64_t));
    for (int q = 0; q < d; q++){
      B->b->coeffs[q] = int2torus((q * 5 + 2) & 7, prec + 1);
      bv[q] = B->b->coeffs[q];
      A->b->coeffs[q] = int2torus((q * 3 + 1) & 7, prec + 1);
      A->a[0]->coeffs[q] = 0;
      B->a[0]->coeffs[q] = 0;
    }
    for (int q = 0; q < d; q++){
      uint64_t e = ((uint64_t)(-(uint64_t) q)) % (2 * d);
      if(e < (uint64_t) d) sig[q] += bv[e];
      else sig[q] -= bv[e - d];
    }
    trlwe_eval_automorphism(R, B, 2 * d - 1, oracle->aut_minus1);
    trlwe_phase(sph, R, lane_key);
    { uint64_t dev = 0;
      for (int q = 0; q < d; q++){
        int64_t dv = (int64_t) sph->coeffs[q] - (int64_t) sig[q];
        if(dv < 0) dv = -dv; if((uint64_t) dv > dev) dev = (uint64_t) dv; }
      printf("T1 sigma_-1: dev log2 = %.2f\n", log2((double) dev + 1.0)); }
    TRGSW_DFT sel1 = trgsw_alloc_new_DFT_sample(l, bg_bit, 1, d);
    { TRGSW tmps = trgsw_alloc_new_sample(l, bg_bit, 1, d);
      trgsw_monomial_sample(tmps, 1, 0, skey);
      trgsw_to_DFT(sel1, tmps);
      free_trgsw(tmps); }
    NCMUX(R, A, B, sel1, oracle);
    trlwe_phase(sph, R, lane_key);
    { uint64_t dev = 0;
      for (int q = 0; q < d; q++){
        int64_t dv = (int64_t) sph->coeffs[q] - (int64_t) sig[q];
        if(dv < 0) dv = -dv; if((uint64_t) dv > dev) dev = (uint64_t) dv; }
      printf("T2 NCMUX(sel=1): dev log2 = %.2f\n", log2((double) dev + 1.0)); }
    CMUX(R, A, B, sel1, oracle);
    trlwe_phase(sph, R, lane_key);
    { uint64_t dev = 0;
      for (int q = 0; q < d; q++){
        int64_t dv = (int64_t) sph->coeffs[q] - (int64_t) bv[q];
        if(dv < 0) dv = -dv; if((uint64_t) dv > dev) dev = (uint64_t) dv; }
      printf("T3 CMUX(sel=1): dev log2 = %.2f\n", log2((double) dev + 1.0)); }
    free_trlwe(A); free_trlwe(B); free_trlwe(R);
    free(bv); free(sig);
  }

  /* ---- staged comparison ---- */
  TRLWE *st = trlwe_alloc_new_sample_array(in_N, 1, d);
  uint64_t *bvec = malloc(sizeof(uint64_t) * in_N);
  for (int t = 0; t < in_N; t++) bvec[t] = in0->b->coeffs[t];
  setup_tv_xb(st, bvec, tv_rlwe, oracle);
  uint64_t *avec = malloc(sizeof(uint64_t) * in_N);
  mod_switch_a(avec, in0->a[0]->coeffs, (int) log2(2 * d), in_N, false);
  uint64_t **sm = malloc(sizeof(uint64_t *) * in_N);
  uint64_t **smt = malloc(sizeof(uint64_t *) * in_N);
  for (int t = 0; t < in_N; t++){
    sm[t] = calloc(d, sizeof(uint64_t));
    smt[t] = calloc(d, sizeof(uint64_t));
  }
  const int log_2d = (int) log2(2 * d);
  const uint64_t po = 1ULL << (64 - prec - 1);
  for (int t = 0; t < in_N; t++){
    const uint64_t bbar = torus2int(in0->b->coeffs[t] + po, log_2d);
    for (int q = 0; q < d; q++){
      uint64_t e = ((uint64_t) q + bbar) % (2 * d);
      if(e < (uint64_t) d) sm[t][e] += tv0->coeffs[q];
      else sm[t][e - d] -= tv0->coeffs[q];
    }
  }
  int stage_no = 0;
  for (int pass = 0; ; pass++){
    uint64_t sdev = 0;
    int bt = -1, bq = -1; int64_t bg_ = 0, bw = 0;
    for (int t = 0; t < in_N; t++){
      trlwe_phase(sph, st[t], lane_key);
      for (int q = 0; q < d; q++){
        int64_t dv = (int64_t) sph->coeffs[q] - (int64_t) sm[t][q];
        if(dv < 0) dv = -dv;
        if((uint64_t) dv > (1ULL << 50)){
          if(bt < 0){ bt = t; bq = q; bg_ = sph->coeffs[q]; bw = sm[t][q]; }
        } else if((uint64_t) dv > sdev) sdev = (uint64_t) dv;
      }
    }
    printf("S-stage %d (%s): dev log2 = %.2f", stage_no,
        pass == 0 ? "setup" : (pass % 2 == 1 ? "bfly" : "suba"),
        log2((double) sdev + 1.0));
    if(bt >= 0) printf("  BAD slot%d q%d got %lld want %lld", bt, bq,
        (long long) bg_, (long long) bw);
    printf("\n");
    if(bt >= 0 || pass == 2 * h + 1) break;
    if(pass % 2 == 0){
      int step = pass / 2;
      RGSW_monomial_mul(st, oracle->s[0][step], oracle);
      for (size_t bit = 0; bit < r_prec; bit++){
        const uint64_t power = 1ULL << bit;
        if((gaps[step] >> bit) & 1){
          for (int j = 0; j < (int) power; j++){
            const uint64_t *src = sm[in_N - power + j];
            memset(smt[j], 0, sizeof(uint64_t) * d);
            for (int i = 0; i < d; i++){
              uint64_t e = ((uint64_t)(-(uint64_t) i)) % (2 * d);
              if(e < (uint64_t) d) smt[j][e] += src[i];
              else smt[j][e - d] -= src[i];
            }
          }
          for (int j = power; j < in_N; j++)
            memcpy(smt[j], sm[j - power], sizeof(uint64_t) * d);
          uint64_t **sw = sm; sm = smt; smt = sw;
        }
      }
    }else{
      sub_a(st, avec, 0, oracle);
      for (int t = 0; t < in_N; t++){
        memcpy(smt[t], sm[t], sizeof(uint64_t) * d);
        memset(sm[t], 0, sizeof(uint64_t) * d);
        for (int q = 0; q < d; q++){
          uint64_t e = ((uint64_t) q + avec[t]) % (2 * d);
          if(e < (uint64_t) d) sm[t][e] += smt[t][q];
          else sm[t][e - d] -= smt[t][q];
        }
      }
    }
    stage_no++;
  }
  return 0;
}
