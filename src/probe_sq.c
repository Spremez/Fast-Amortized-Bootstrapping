/* probe_sq.c -- stage356 standalone verification vehicle for the
 * scale-quantized SAB (sab_sq). Carries its own main() following the
 * repo's probe_mul.c / probe_v6.c convention, because main.c is under
 * concurrent edit by the candidate-D track and cannot hold stable
 * instrumentation. The main.c SAB_SQ_EQUIV_TEST block remains as the
 * (equivalent) integration point; this probe is the evidence artifact.
 *
 * Gate: all in_N bootstrapped messages equal the LUT expectation
 * (SAB_SQ gate: Pass), noise deviation reported in log2, scalar SAB
 * timed in the same binary for the speed comparison.
 */
#include "sab_sq.h"
#include <sab.h>
#include <benchmark_util.h>
#include <sab_profile.h>
#include <time.h>

#define MEASURE_BOOTSTRAP_TIME(NAME, REP, MSG, CODE) \
  do { \
    SAB_PROFILE_RESET(); \
    MEASURE_TIME(NAME, REP, MSG, CODE); \
    SAB_PROFILE_PRINT(); \
  } while (0)

int sq_key_check(TRLWE_Key key, uint64_t N, const char * where){
  uint64_t bad = 0, ones = 0;
  for (size_t j = 0; j < N; j++){
    const uint64_t c = key->s[0]->coeffs[j];
    if(c == 1) ones++;
    else if(c != 0) bad++;
  }
  printf("[sqchk] %s: ones=%d bad=%d\n", where, (int) ones, (int) bad);
  return bad;
}

/* D4-convergence contract check (stage356 -> candidate D offer):
 * the LUT-late-binding product bind(F, U) with U holding quarter-scale
 * (2^62) unit spikes, computed as the raw-int DFT envelope with the
 * SPECTRUM prescale 1/4 and the <<2 tail recovery, must reproduce
 * F * X^p to 1-ulp at torus. This pins the integer semantics
 * (toward-zero mod-2^64 truncation in execute_direct_torus64, real
 * spectrum prescale) that D4's UNIT3 integer-multiple error is
 * fighting; the SQ kernel uses the identical contract at general q. */
static void bind_contract_check(uint64_t N){
  TorusPolynomial F = polynomial_new_torus_polynomial(N);
  TorusPolynomial U = polynomial_new_torus_polynomial(N);
  TorusPolynomial exp = polynomial_new_torus_polynomial(N);
  TorusPolynomial got = polynomial_new_torus_polynomial(N);
  DFT_Polynomial fd = polynomial_new_DFT_polynomial(N);
  DFT_Polynomial ud = polynomial_new_DFT_polynomial(N);
  DFT_Polynomial od = polynomial_new_DFT_polynomial(N);
  uint64_t raw[8];
  generate_random_bytes(sizeof(raw), (uint8_t *) raw);
  for (size_t i = 0; i < N; i++) F->coeffs[i] = raw[i % 8] * 0x9E3779B97F4A7C15ULL + i;
  const uint64_t p = 17;
  U->coeffs[p] += (Torus)(1LL << 62);            // quarter-scale unit spike
  U->coeffs[(p + 5) % N] += (Torus)(-(int64_t)(1LL << 62));
  torus_polynomial_mul_by_xai(exp, F, p);         // expected: F*(X^p - X^(p+5))
  {
    TorusPolynomial t = polynomial_new_torus_polynomial(N);
    torus_polynomial_mul_by_xai(t, F, (p + 5) % N);
    for (size_t i = 0; i < N; i++) exp->coeffs[i] -= t->coeffs[i];
    free_polynomial(t);
  }
  // raw-int envelope: |F| ~ 2^63, |U| ~ 2^62 -> products ~2^125 blow the
  // 53-bit mantissa long before the mod-2^64 reduction; the quarter-scale
  // prescale + <<2 recovery CANNOT carry a full-torus F (this is the shape
  // of D4's UNIT3 integer-multiple error). Correct contract: prescale the
  // public side by 2^-s so |product| ~< 2^52, recover with <<(s-62).
  const int s_prescale = 73;
  const int s_recover = s_prescale - 62;          // U spikes sit at 2^62
  polynomial_torus_to_DFT(fd, F);
  polynomial_torus_to_DFT(ud, U);
  const double prescale = ldexp(1.0, -s_prescale);
  for (size_t i = 0; i < N; i++) fd->coeffs[i] *= prescale;
  polynomial_mul_DFT(od, fd, ud);
  polynomial_DFT_to_torus(got, od);
  int64_t max_dev = 0;
  for (size_t i = 0; i < N; i++){
    int64_t v = ((int64_t) got->coeffs[i]) << s_recover;
    int64_t d = v - (int64_t) exp->coeffs[i];
    if(d < 0) d = -d;
    if(d > max_dev) max_dev = d;
  }
  /* absolute floor includes the sqrt(N) transform growth on top of the
   * 2^-53 mantissa: relative deviation is the meaningful quantity */
  const int64_t floor = 1LL << (s_recover + 6);
  printf("BIND_CONTRACT prescale 2^-%d, <<%d recovery: max dev log2 = %.2f abs"
         " (relative 2^%.1f, floor 2^%d, %s)\n",
         s_prescale, s_recover, log2((double)(max_dev + 1)),
         log2((double)(max_dev + 1)) - 63.0, (int) log2((double) floor),
         max_dev <= floor ? "Pass" : "FAIL");
  free_polynomial(F); free_polynomial(U); free_polynomial(exp);
  free_polynomial(got); free_DFT_polynomial(fd); free_DFT_polynomial(ud); free_DFT_polynomial(od);
}

int main(){
  setvbuf(stdout, NULL, _IONBF, 0);
  bind_contract_check(2048);
#ifndef SAB_SQ_Q
#define SAB_SQ_Q 16
#endif
  const uint64_t q = SAB_SQ_Q;
  const uint64_t reps = 3;
  uint64_t in_N = 2048, out_N = 2048, msg_prec = 3, sigma_shift_in = 0;
  double sigma_in_exp = 15.0;
  {
    const char * e;
    if((e = getenv("SAB_SQ_N"))) in_N = strtoull(e, NULL, 0);
    if((e = getenv("SAB_SQ_OUTN"))) out_N = strtoull(e, NULL, 0);
    if((e = getenv("SAB_SQ_P"))) msg_prec = strtoull(e, NULL, 0);
  }
  const uint64_t in_k = 1, out_k = 1, l = 1, bg_bit = 23, b_packing = 14, ell_packing = 2, b_ks = 1, h_out = 512;
  /* precision-dependent KS parameters (mirror 686's per-set values from main.c):
   * t_ks: HW-reducing KS decomposition length, grows with message precision
   * to keep the packing/HW noise under the message budget */
  uint64_t t_ks = 12;
  if(msg_prec >= 5) t_ks = 14;
  if(msg_prec >= 7) t_ks = 17;
  if(msg_prec >= 9) t_ks = 20;
  {
    const char * e = getenv("SAB_SQ_TKS");
    if(e) t_ks = strtoull(e, NULL, 0);
  }
  /* fairness protocol (stage356-F): CRYPTO'26 (ex-279) corrected input-key
   * weight. T3 combinatorial tier gives h*=38 at n=2048 (current 39 is
   * borderline, T3=128.13 vs claim 128.90); the estimator tier (MitM-H2,
   * ~6.7-10.5 bits below claims) is covered at h=42 (B2-class, +8.4 bits
   * of T3 ceiling). SAB_SQ_H selects the point; both schemes share it. */
  uint64_t h_in = 39;
  {
    const char * e = getenv("SAB_SQ_H");
    if(e) h_in = strtoull(e, NULL, 0);
  }
  printf("Input key: h = %d (fairness point)\n", (int) h_in);
  { const char * e = getenv("SAB_SQ_SIG_IN"); if(e) sigma_in_exp = atof(e); }
  double sigma_in = pow(2, -sigma_in_exp);
  /* SAB_SQ_SIGMA_SHIFT=<bits> shifts the BSK/output key sigma from the
   * -50 base. BSK option A (2026-09-04, user-confirmed): alternating-sign
   * honest-model dual-hybrid is 127.9 < 128 at 2^-50, 130.4 at 2^-49, so
   * the committed default is now shift=1; set 0 to reproduce the old arm. */
  int sigma_shift = 1;
  {
    const char * env = getenv("SAB_SQ_SIGMA_SHIFT");
    if(env != NULL) sigma_shift = atoi(env);
  }
  const double sigma_out = pow(2, -50 + sigma_shift);
  /* 2026/279 hardened KS gadget (stage357 v2 sweep): finer decomposition
   * trades key size for sigma-tolerant KS noise. */
  uint64_t aut_l = 1, aut_bg = 23, pack_ell = 2, pack_bg = 14;
  {
    const char * e = getenv("SQKS_AUT_L");
    if(e) aut_l = strtoull(e, NULL, 0);
    e = getenv("SQKS_AUT_BG");
    if(e) aut_bg = strtoull(e, NULL, 0);
    e = getenv("SQKS_PACK_ELL");
    if(e) pack_ell = strtoull(e, NULL, 0);
    e = getenv("SQKS_PACK_BG");
    if(e) pack_bg = strtoull(e, NULL, 0);
  }
  /* auto-derive r_prec from N and h (max gap ≈ N/h, need ceil(log2) + 1);
   * override via SAB_SQ_RPREC; 686's original targets: 2048→7, 4096→8/9, 8192→10 */
  uint64_t target_r_prec = (uint64_t)(log2((double) in_N / (double) h_in) + 2.0);
  if(target_r_prec < 4) target_r_prec = 4;
  {
    const char * e = getenv("SAB_SQ_RPREC");
    if(e) target_r_prec = strtoull(e, NULL, 0);
  }
  printf("SAB_SQ probe (q = %d, 2025/1711 x 2025/686, 2026/279 preflight)\n", (int) q);
  printf("Input: (N=%d, h=%d, binary, sigma=2^-15)\n", (int) in_N, (int) h_in);
  printf("Output: (N=%d, h=%d, ternary, sigma=2^-%d%s)\n", (int) out_N, (int) h_out,
         (int)(50 - sigma_shift), sigma_shift ? " HARDENED" : "");
  printf("KS gadgets: aut(l=%d,Bg=2^%d) pack(ell=%d,b=2^%d)\n",
         (int) aut_l, (int) aut_bg, (int) pack_ell, (int) pack_bg);

  TRLWE_Key input_key;
  {
    clock_t t_kg = clock();
    const uint64_t attempts = RS_sparse_binary_key(&input_key, in_N, in_k, h_in,
        sigma_in, target_r_prec);
    printf("RS attempts = %lu\n", (unsigned long) attempts);
    printf("[keygen input RS] %.1fs\n",
           (double)(clock() - t_kg) / CLOCKS_PER_SEC);
  }
  printf("[sqchk] born: input=%p input_dft=%p %s\n",
         (void*) input_key->s[0]->coeffs, (void*) input_key->s_dft[0]->coeffs,
         input_key->s[0]->coeffs == input_key->s_dft[0]->coeffs ? "ALIASED!!" : "distinct");
  sq_key_check(input_key, in_N, "after RS");
  TRLWE_Key out_key = trlwe_alloc_key(out_N, out_k, sigma_out);
  extern void gen_sparse_array(uint64_t * out, uint64_t size, uint64_t h, bool ternary, bool gaussian, double key_sigma);
  gen_sparse_array(out_key->s[0]->coeffs, out_N, h_out, true, false, 0);
  sq_key_check(input_key, in_N, "after gen_sparse");
  polynomial_torus_to_DFT(out_key->s_dft[0], out_key->s[0]);
  sq_key_check(input_key, in_N, "after to_DFT");
  printf("[sqchk] ptrs: input=%p out=%p\n",
         (void*) input_key->s[0]->coeffs, (void*) out_key->s[0]->coeffs);
  sq_key_check(input_key, in_N, "after out_key");
  TRLWE_Key packing_key = trlwe_new_ternary_key(in_N, in_k, 256, pow(2, -44));
  sq_key_check(input_key, in_N, "after packing_key");
  TRGSW_Key sq_output_key = trgsw_new_key(out_key, 1, q);
  TRGSW_Key scalar_output_key = trgsw_new_key(out_key, l, bg_bit);
  sq_key_check(input_key, in_N, "after trgsw keys");
  const uint64_t r_prec = get_min_prec(input_key);
  printf("Max monomial distance (log B): %d\n", (int) r_prec);
  printf("[sq] keygen sq r_prec=%d\n", (int) r_prec);
  SAB_SQ_Key sq = sab_sq_new_key(input_key, packing_key, sq_output_key, msg_prec, pack_bg, pack_ell, t_ks, b_ks, h_in, r_prec, q);
  printf("[sq] keygen sq ok\n");
  SAB_Key sab = new_sparse_amortized_bootstrapping(input_key, packing_key, scalar_output_key, msg_prec, b_packing, ell_packing, t_ks, b_ks, h_in, r_prec, false, false, false);
  printf("[sq] keygen scalar ok\n");

  TorusPolynomial poly_in = polynomial_new_torus_polynomial(in_N);
  const uint64_t mod_mask = (1ULL<<(msg_prec - 1)) - 1;
  for (size_t i = 0; i < in_N; i++) poly_in->coeffs[i] = int2torus(i&mod_mask, msg_prec);
  TRLWE rlwe_in = trlwe_new_sample(poly_in, input_key);
  TRLWE rlwe_in2 = trlwe_new_sample(poly_in, input_key);
  TRLWE rlwe_tv = trlwe_new_noiseless_trivial_sample(NULL, out_k, out_N);
  uint64_t LUT[1ULL << msg_prec];
  generate_random_bytes(sizeof(uint64_t)*(1ULL << msg_prec), (uint8_t *) LUT);
  for (size_t i = 0; i < (1ULL << msg_prec); i++) LUT[i] &= mod_mask;
  sab_LUT_packing(rlwe_tv, LUT, sab);
  printf("[sq] inputs ready\n");

  TRLWE sq_out = trlwe_new_sample(NULL, input_key);
  printf("[sq] bootstrap start\n");
  MEASURE_BOOTSTRAP_TIME("", reps, "SAB_SQ bootstrap",
    sab_sq_bootstrap(sq_out, rlwe_in, rlwe_tv, sq);
  );
  printf("[sq] bootstrap done\n");
  TorusPolynomial res_poly = polynomial_new_torus_polynomial(in_N);
  trlwe_phase(res_poly, sq_out, input_key);
  bool pass = true;
  size_t mism = 0;
  int64_t max_dev = 0;
  for (size_t i = 0; i < in_N; i++){
    const uint64_t in_msg = torus2int(poly_in->coeffs[i], msg_prec);
    const uint64_t expected = LUT[in_msg];
    const uint64_t res = torus2int(res_poly->coeffs[i], msg_prec);
    if(res != expected){
      if(mism <= 8) printf("SQ Fail %zu: %d != %d\n", i, (int) res, (int) expected);
      mism++;
      pass = false;
    }
    int64_t dev = ((int64_t) res_poly->coeffs[i]) - (int64_t) int2torus(expected, msg_prec);
    if(dev < 0) dev = -dev;
    if(dev > max_dev) max_dev = dev;
  }
  printf("SAB_SQ noise: max phase deviation log2 = %.2f (message budget 2^-%d)\n",
         log2((double)(max_dev + 1)), (int)(msg_prec + 1));
  printf("SAB_SQ gate: %s (mismatch %d / %d)\n", pass ? "Pass" : "Fail", (int) mism, (int) in_N);

  /* headroom-as-output: apply SAB_SQ_POSTOPS external products after the
   * bootstrap (multiply-by-one TRGSW selectors under the input key) and
   * report the noise after each -- the post-bootstrap capacity curve. */
  {
    uint64_t postops = 0;
    const char * e = getenv("SAB_SQ_POSTOPS");
    if(e) postops = strtoull(e, NULL, 0);
    if(postops){
      uint64_t post_l = 8, post_bg = 8, post_sig = 40;
      { const char * e2 = getenv("SAB_SQ_POST_L"); if(e2) post_l = strtoull(e2, NULL, 0);
        e2 = getenv("SAB_SQ_POST_BG"); if(e2) post_bg = strtoull(e2, NULL, 0);
        e2 = getenv("SAB_SQ_POST_SIG"); if(e2) post_sig = strtoull(e2, NULL, 0); }
      /* circuit keys must sample at small sigma: the input key's own
       * sigma (2^-15) amplifies to ~half-torus per EP (sqrt(lN)*Bg/12^0.5
       * * sigma ~ 2^-1.8, measured 2^63 saturation). Clone the secret at
       * an adjustable sampling sigma instead. */
      TRLWE_Key post_ik = trlwe_alloc_key((int) in_N, (int) in_k, pow(2, -(double) post_sig));
      for (size_t ci = 0; ci < in_k; ci++){
        memcpy(post_ik->s[ci]->coeffs, input_key->s[ci]->coeffs, sizeof(Torus) * in_N);
        polynomial_torus_to_DFT(post_ik->s_dft[ci], post_ik->s[ci]);
      }
      TRGSW_Key post_key = trgsw_new_key(post_ik, (int) post_l, (int) post_bg);
      TRGSW sel_raw = trgsw_alloc_new_sample((int) post_l, (int) post_bg, (int) in_k, (int) in_N);
      TRGSW_DFT sel = trgsw_alloc_new_DFT_sample((int) post_l, (int) post_bg, (int) in_k, (int) in_N);
      trgsw_monomial_sample(sel_raw, 1, 0, post_key);
      trgsw_to_DFT(sel, sel_raw);
      TRLWE_DFT buf = trlwe_alloc_new_DFT_sample((int) in_k, (int) in_N);
      for (uint64_t s = 0; s < postops; s++){
        trgsw_mul_trlwe_DFT(buf, sq_out, sel);
        trlwe_from_DFT(sq_out, buf);
        trlwe_phase(res_poly, sq_out, input_key);
        int64_t dev_max = 0;
        for (size_t i = 0; i < in_N; i++){
          const uint64_t expected = LUT[torus2int(poly_in->coeffs[i], msg_prec)];
          int64_t dev = ((int64_t) res_poly->coeffs[i]) - (int64_t) int2torus(expected, msg_prec);
          if(dev < 0) dev = -dev;
          if(dev > dev_max) dev_max = dev;
        }
        printf("SAB_SQ postop %lu: max phase deviation log2 = %.2f\n",
               (unsigned long)(s + 1), log2((double)(dev_max + 1)));
      }
    }
  }

  TRLWE scalar_out = trlwe_new_sample(NULL, input_key);
  MEASURE_BOOTSTRAP_TIME("", reps, "SAB_scalar bootstrap",
    sab_rlwe_bootstrap(scalar_out, rlwe_in2, rlwe_tv, sab);
  );
  trlwe_phase(res_poly, scalar_out, input_key);
  int64_t max_dev_scalar = 0;
  for (size_t i = 0; i < in_N; i++){
    const uint64_t expected = LUT[torus2int(poly_in->coeffs[i], msg_prec)];
    int64_t dev = ((int64_t) res_poly->coeffs[i]) - (int64_t) int2torus(expected, msg_prec);
    if(dev < 0) dev = -dev;
    if(dev > max_dev_scalar) max_dev_scalar = dev;
  }
  printf("SAB_scalar noise: max phase deviation log2 = %.2f\n", log2((double)(max_dev_scalar + 1)));
  {
    uint64_t postops = 0;
    const char * e = getenv("SAB_SQ_POSTOPS");
    if(e) postops = strtoull(e, NULL, 0);
    if(postops){
      uint64_t post_l = 8, post_bg = 8, post_sig = 40;
      { const char * e2 = getenv("SAB_SQ_POST_L"); if(e2) post_l = strtoull(e2, NULL, 0);
        e2 = getenv("SAB_SQ_POST_BG"); if(e2) post_bg = strtoull(e2, NULL, 0);
        e2 = getenv("SAB_SQ_POST_SIG"); if(e2) post_sig = strtoull(e2, NULL, 0); }
      /* circuit keys must sample at small sigma: the input key's own
       * sigma (2^-15) amplifies to ~half-torus per EP (sqrt(lN)*Bg/12^0.5
       * * sigma ~ 2^-1.8, measured 2^63 saturation). Clone the secret at
       * an adjustable sampling sigma instead. */
      TRLWE_Key post_ik = trlwe_alloc_key((int) in_N, (int) in_k, pow(2, -(double) post_sig));
      for (size_t ci = 0; ci < in_k; ci++){
        memcpy(post_ik->s[ci]->coeffs, input_key->s[ci]->coeffs, sizeof(Torus) * in_N);
        polynomial_torus_to_DFT(post_ik->s_dft[ci], post_ik->s[ci]);
      }
      TRGSW_Key post_key = trgsw_new_key(post_ik, (int) post_l, (int) post_bg);
      TRGSW sel_raw = trgsw_alloc_new_sample((int) post_l, (int) post_bg, (int) in_k, (int) in_N);
      TRGSW_DFT sel = trgsw_alloc_new_DFT_sample((int) post_l, (int) post_bg, (int) in_k, (int) in_N);
      trgsw_monomial_sample(sel_raw, 1, 0, post_key);
      trgsw_to_DFT(sel, sel_raw);
      TRLWE_DFT buf = trlwe_alloc_new_DFT_sample((int) in_k, (int) in_N);
      for (uint64_t s = 0; s < postops; s++){
        trgsw_mul_trlwe_DFT(buf, scalar_out, sel);
        trlwe_from_DFT(scalar_out, buf);
        trlwe_phase(res_poly, scalar_out, input_key);
        int64_t dev_max = 0;
        for (size_t i = 0; i < in_N; i++){
          const uint64_t expected = LUT[torus2int(poly_in->coeffs[i], msg_prec)];
          int64_t dev = ((int64_t) res_poly->coeffs[i]) - (int64_t) int2torus(expected, msg_prec);
          if(dev < 0) dev = -dev;
          if(dev > dev_max) dev_max = dev;
        }
        printf("SAB_scalar postop %lu: max phase deviation log2 = %.2f\n",
               (unsigned long)(s + 1), log2((double)(dev_max + 1)));
      }
    }
  }
  printf("SAB_SQ probe done\n");
  return pass ? 0 : 1;
}
