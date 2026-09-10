/* probe_prealigned2.c -- COMPLETE pre-aligned combined packing+batching.
 *
 * Full multi-input: per-body-group b̄'_l setup (different rotation per
 * input), shared ā_common sub_a (single plaintext monomial), full
 * r1*r2 oracle gate. Pre-alignment simulated at plaintext level
 * (b'_l = b_l + (a_common - a_l)·s_in, phase-preserving by construction).
 *
 * Pipeline = STANDARD packing butterfly (sab_pvw path) with multi-body
 * TV pack; sub_a = per-slot plaintext monomial from a_common.
 */
#include <sab.h>
#include <sab_pvw.h>
#include <sab_rinput.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <time.h>

static double now_us(void){
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return ts.tv_sec * 1e6 + ts.tv_nsec / 1e3;
}

#define MAX_R1 4
#define MAX_R2 4
#define MAX_BODIES (MAX_R1 * MAX_R2)

static int run_trial(int trial, int reps){
  setvbuf(stdout, NULL, _IONBF, 0);
  int in_N = 256, out_N = 2048, h = 6, prec = 3;
  int r1 = 2, r2 = 2;
  { const char *e;
    if((e = getenv("SAB_PA_IN_N"))) in_N = atoi(e);
    if((e = getenv("SAB_PA_OUT_N"))) out_N = atoi(e);
    if((e = getenv("SAB_PA_H"))) h = atoi(e);
    if((e = getenv("SAB_PA_R1"))) r1 = atoi(e);
    if((e = getenv("SAB_PA_R2"))) r2 = atoi(e); }
  if(r1 > MAX_R1) r1 = MAX_R1; if(r2 > MAX_R2) r2 = MAX_R2;
  const int bodies = r1 * r2;
  printf("== PA2 trial %d/%d: in_N=%d out_N=%d h=%d r1=%d r2=%d ==\n",
      trial + 1, reps, in_N, out_N, h, r1, r2);

  /* sparse input key */
  TRLWE_Key input_key = NULL;
  RS_sparse_binary_key(&input_key, in_N, 1, h, pow(2, -15), 7);
  if(!input_key || !input_key->s[0]){ printf("keygen FAIL\n"); return 1; }

  /* r1 inputs + common mask */
  TRLWE ins[MAX_R1];
  TorusPolynomial msgs[MAX_R1];
  uint64_t a_common_raw[8192];
  { memset(a_common_raw, 0, sizeof(uint64_t)*in_N); /* zero = simplest */
    if(!getenv("SAB_PA_RANDOM_AC")){
      uint64_t lcg = 0x123456789ABCDEFULL;
      for(int i=0;i<in_N;i++){ lcg = lcg*6364136223846793005ULL+1442695040888963407ULL;
        a_common_raw[i] = lcg; } } }
  /* Pre-aligned b'_l = b_l + (a_common - a_l)·s_in (plaintext simulation) */
  uint64_t bpa[MAX_R1][8192]; /* pre-aligned b values */
  for(int l=0;l<r1;l++){
    msgs[l] = polynomial_new_torus_polynomial(in_N);
    for(int i=0;i<in_N;i++) msgs[l]->coeffs[i] = int2torus((i+3*l)&7, prec);
    ins[l] = trlwe_new_sample(msgs[l], input_key);
    /* compute b'_l[t] = b_l[t] + Σ_i (a_common[i]-a_l[i])·s_in[t-i] */
    for(int t=0;t<in_N;t++){
      /* Accumulate in uint64_t (torus wrap-around semantics).
       * int64_t overflow: h+1 terms each ~2^63 sum past int64 range. */
      uint64_t corr = 0;
      for(int i=0;i<in_N;i++){
        int j = (t - i + 2*in_N) % (2*in_N);
        int sign;
        if(j >= in_N){ j -= in_N; sign = -1; } else { sign = 1; }
        if(!input_key->s[0]->coeffs[j]) continue; /* sparse: skip zeros */
        uint64_t diff = a_common_raw[i] - ins[l]->a[0]->coeffs[i];
        if(sign > 0) corr += diff;
        else corr -= diff; /* uint64_t wraps = torus negation */
      }
      bpa[l][t] = (uint64_t)0 - (ins[l]->b->coeffs[t] + corr); /* NEGATE:
        boundary crossing sigma_-1 negates exponent; oracle expects
        E_full ≈ modswitch(-phi); need -b_bar' = modswitch(-phi),
        so b_bar' = modswitch(phi), i.e. bpa = +phi. But phi here is
        b+corr = b+(a'-a)s = phi. Actually we need bpa = phi (positive).
        The negation is WRONG -- revert to positive and check separately. */
      bpa[l][t] = ins[l]->b->coeffs[t] + corr; /* positive */
    }
  }

  /* Build TV pack: body (l*r2+j) carries TV_{l,j} */
  PVW_TMLWE_Key pvw_key = pvmtmlwe_new_binary_key(out_N, 1, bodies, pow(2,-70));
  SAB_PVW_Key pvw = sab_pvw_new_binary_key(input_key, pvw_key, prec, h, 7, 1, 23);

  /* Custom setup: per-body-group rotation by b̄'_l */
  const int log_2N = (int)log2(2*out_N);
  const uint64_t po = 1ULL << (64 - prec - 1);
  PVW_TMLWE *acc = pvmtmlwe_alloc_new_sample_array(in_N, 1, bodies, out_N);
  /* TV values per (l,j) */
  /* Piecewise-constant LUT: level q>>shift, distinct per body.
   * This is REAL bootstrapping semantics (ramp TV amplifies modswitch
   * rounding artifacts -- Direction A finding). */
  TorusPolynomial tvs[MAX_BODIES];
  {
    const int nlev = 1 << prec;         /* 2^prec LUT levels */
    const int block = out_N / nlev;      /* coefficients per level */
    for(int x=0;x<bodies;x++){
      tvs[x] = polynomial_new_torus_polynomial(out_N);
      for(int q=0;q<out_N;q++){
        const int level = q / block;     /* which LUT level */
        const int val = (level + 3*x + 1) & (nlev - 1);
        tvs[x]->coeffs[q] = int2torus(val, prec);
      }
    }
  }
  for(int t=0;t<in_N;t++){
    /* mask AND all bodies = 0 */
    memset(acc[t]->a[0]->coeffs, 0, sizeof(uint64_t)*out_N);
    for(int b=0;b<bodies;b++)
      memset(acc[t]->b[b]->coeffs, 0, sizeof(uint64_t)*out_N);
    for(int l=0;l<r1;l++){
      uint64_t bbar = torus2int(bpa[l][t] + po, log_2N);
      for(int j=0;j<r2;j++){
        int body = l*r2 + j;
        /* b[body] = X^{bbar} · TV_{l,j} */
        memset(acc[t]->b[body]->coeffs, 0, sizeof(uint64_t)*out_N);
        for(int q=0;q<out_N;q++){
          uint64_t pos = (q + bbar) % (2*out_N);
          if(pos < (uint64_t)out_N)
            acc[t]->b[body]->coeffs[pos] += tvs[l*r2+j]->coeffs[q];
          else
            acc[t]->b[body]->coeffs[pos - out_N] -= tvs[l*r2+j]->coeffs[q];
        }
      }
    }
  }

  /* Run the packing butterfly (uses input 0 for the selector schedule;
   * the SELECTORS depend only on the key's gap structure, not on which
   * input's a/b we pass for the sub_a — we handle sub_a ourselves below) */
  /* Build a "virtual" TRLWE with mask a_common for sub_a derivation */
  TRLWE virtual_in = trlwe_alloc_new_sample(1, in_N);
  memcpy(virtual_in->a[0]->coeffs, a_common_raw, sizeof(uint64_t)*in_N);
  memcpy(virtual_in->b->coeffs, ins[0]->b->coeffs, sizeof(uint64_t)*in_N);

  double t0 = now_us();
  /* DIAGNOSTIC: verify setup is correct for slot 0, body 0 */
  if(trial == 0){
    const int l=0, j=0, body=0, t=0;
    uint64_t bbar = torus2int(bpa[l][t] + po, log_2N);
    uint64_t expect = 0;
    for(int q=0;q<8;q++){
      uint64_t pos=(q+bbar)%(2*out_N);
      if(pos<(uint64_t)out_N) expect += tvs[body]->coeffs[q];
      else expect -= tvs[body]->coeffs[q];
    }
    printf("SETUP-CHK: bbar=%lu acc=%lu exp=%lu m=%s
",
",
        (unsigned long)bbar, (unsigned long)acc[t]->b[body]->coeffs[0],
        (unsigned long)expect,
        acc[t]->b[body]->coeffs[0]==expect?"YES":"NO");
    printf("  tv[0..3]=%lu,%lu,%lu,%lu
",
        (unsigned long)tvs[0]->coeffs[0],(unsigned long)tvs[0]->coeffs[1],
        (unsigned long)tvs[0]->coeffs[2],(unsigned long)tvs[0]->coeffs[3]);
    printf("  bpa[0][0]=%lu b_orig[0]=%lu
",
        (unsigned long)bpa[0][0],(unsigned long)ins[0]->b->coeffs[0]);
  }
  /* Use the library's TESTED butterfly + sub_a */
  { const uint64_t log2_2N = (uint64_t)log2(2*out_N);
    uint64_t ac_mod[8192];
    const char *npa = getenv("SAB_PA_NOALIGN");
    if(npa){ /* use ORIGINAL input 0's a and b (no pre-alignment) */
      for(int t=0;t<in_N;t++){
        ac_mod[t] = torus2int(ins[0]->a[0]->coeffs[t], log2_2N);
        uint64_t bbar = torus2int(ins[0]->b->coeffs[t] +
            (1ULL<<(64-prec-1)), log2_2N);
        /* redo setup with original b */
        for(int b=0;b<bodies;b++){
          memset(acc[t]->b[b]->coeffs,0,sizeof(uint64_t)*out_N);
          for(int q=0;q<out_N;q++){
            uint64_t pos=(q+bbar)%(2*out_N);
            if(pos<(uint64_t)out_N) acc[t]->b[b]->coeffs[pos]+=tvs[b]->coeffs[q];
            else acc[t]->b[b]->coeffs[pos-out_N]-=tvs[b]->coeffs[q]; } }
      }
    } else {
      for(int t=0;t<in_N;t++)
        ac_mod[t] = torus2int(a_common_raw[t], log2_2N);
    }
    sab_pvw_sparse_mul_binary(acc, ac_mod, 0, pvw);
  }
  double t_joint = now_us() - t0;

  /* Oracle gate: scalar SAB per (l,j) */
  int mism = 0, mism_ch[MAX_BODIES] = {0};
  double t_or = 0;
  TorusPolynomial p1 = polynomial_new_torus_polynomial(out_N);
  for(int l=0;l<r1;l++)
    for(int j=0;j<r2;j++){
      int ch = l*r2+j;
      TRLWE_Key lk = trlwe_new_binary_key(out_N, 1, pow(2,-70));
      TRGSW_Key sk = trgsw_new_key(lk, 1, 23);
      SAB_Key orc = min_oracle_key(input_key, sk, prec, h, 7);
      TRLWE tvr = trlwe_alloc_new_sample(1, out_N);
      memset(tvr->a[0]->coeffs, 0, sizeof(uint64_t)*out_N);
      memcpy(tvr->b->coeffs, tvs[ch]->coeffs, sizeof(uint64_t)*out_N);
      TRLWE *sa = trlwe_alloc_new_sample_array(in_N, 1, out_N);
      double tb = now_us();
      { const char *npa2 = getenv("SAB_PA_NOALIGN");
        sab_rlwe_bootstrap_wo_extract(sa,
            npa2 ? ins[0] : ins[l], tvr, orc); }
      t_or += now_us() - tb;
      for(int t=0;t<in_N;t++){
        trlwe_phase(p1, sa[t], lk);
        /* joint body ch phase */
        TorusPolynomial ph = polynomial_new_torus_polynomial(out_N);
        memset(ph->coeffs, 0, sizeof(uint64_t)*out_N);
        polynomial_mul_addto_torus(ph, acc[t]->a[0], pvw_key->s[0][ch]);
        polynomial_sub_torus_polynomials(ph, acc[t]->b[ch], ph);
        const int64_t vs = (((int64_t)p1->coeffs[0])
            + ((int64_t)1<<(62-prec-1))) >> (62-prec);
        const int64_t vj = (((int64_t)ph->coeffs[0])
            + ((int64_t)1<<(62-prec-1))) >> (62-prec);
        if(vs != vj){ mism++; mism_ch[ch]++; }
        free_polynomial(ph);
      }
      free_trlwe_array(sa,in_N); free_trlwe(tvr);
      free_trlwe_key(lk); free_trgsw_key(sk);
    }

  printf("PA2-GATE: mismatch %d / %d -- %s\n", mism, bodies*in_N,
      mism==0 ? "Pass" : "FAIL");
  if(mism) for(int x=0;x<bodies;x++) if(mism_ch[x])
    printf("  ch(l=%d,j=%d): %d\n", x/r2, x%r2, mism_ch[x]);
  printf("timing: joint=%.0f us, %dx-scalar=%.0f us\n",
      t_joint, bodies, t_or);

  for(int x=0;x<bodies;x++) free_polynomial(tvs[x]);
  free_polynomial(p1); free_trlwe(virtual_in);
  free_pvmtmlwe_array(acc, in_N);
  free_pvmtmlwe_key(pvw_key);
  for(int l=0;l<r1;l++){ free_trlwe(ins[l]); free_polynomial(msgs[l]); }
  free_trlwe_key(input_key);
  return mism==0 ? 0 : 1;
}

int main(void){
  int reps = 1;
  { const char *e = getenv("SAB_PA_REPS");
    if(e){ reps = atoi(e); if(reps<1) reps=1; if(reps>16) reps=16; } }
  int ok = 1;
  for(int r=0;r<reps;r++) if(run_trial(r,reps)!=0) ok=0;
  printf("PA2 %s\n", ok ? "ALL PASS" : "FAIL");
  return ok ? 0 : 1;
}
