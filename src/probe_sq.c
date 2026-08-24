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

int main(){
  setvbuf(stdout, NULL, _IONBF, 0);
#ifndef SAB_SQ_Q
#define SAB_SQ_Q 16
#endif
  const uint64_t q = SAB_SQ_Q;
  const uint64_t reps = 3;
  const uint64_t in_N = 2048, in_k = 1, out_N = 2048, out_k = 1, l = 1, bg_bit = 23, b_packing = 14, ell_packing = 2, t_ks = 12, b_ks = 1, h_in = 39, h_out = 512, msg_prec = 3;
  const double sigma_in = pow(2, -15);
  /* 2026/279 hardening demo: SAB_SQ_SIGMA_SHIFT=<bits> raises the output
   * key sigma by that many bits (restoring the isometry-hybrid margin).
   * Expected: SQ(q<=16) keeps the gate, the stock scalar path degrades. */
  int sigma_shift = 0;
  {
    const char * env = getenv("SAB_SQ_SIGMA_SHIFT");
    if(env != NULL) sigma_shift = atoi(env);
  }
  const double sigma_out = pow(2, -50 + sigma_shift);
  const uint64_t target_r_prec = 7;
  printf("SAB_SQ probe (q = %d, 2025/1711 x 2025/686, 2026/279 preflight)\n", (int) q);
  printf("Input: (N=%d, h=%d, binary, sigma=2^-15)\n", (int) in_N, (int) h_in);
  printf("Output: (N=%d, h=%d, ternary, sigma=2^-%d%s)\n", (int) out_N, (int) h_out,
         (int)(50 - sigma_shift), sigma_shift ? " HARDENED" : "");

  TRLWE_Key input_key;
  RS_sparse_binary_key(&input_key, in_N, in_k, h_in, sigma_in, target_r_prec);
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
  SAB_SQ_Key sq = sab_sq_new_key(input_key, packing_key, sq_output_key, msg_prec, b_packing, ell_packing, t_ks, b_ks, h_in, r_prec, q);
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
  printf("SAB_SQ probe done\n");
  return pass ? 0 : 1;
}
