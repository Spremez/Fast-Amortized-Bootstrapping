#include <sab_b.h>
//#include <sab.h>
#include <benchmark_util.h>
#include <sab_profile.h>
#include <inttypes.h>
#if defined(SAB_PVW_KERNEL_TEST) || defined(SAB_PVW_RGT4_KERNEL_TEST) || defined(SAB_PVW_TARGET_TEST) || defined(SAB_PVW_BENCH) || defined(SAB_PVW_NOISE_TEST) || defined(SAB_PVW_STAGE_NOISE_TEST) || defined(SAB_PVW_RESOURCE_TEST)
#include <sab_pvw.h>
#endif

// #define PRINT_POLY

#define MEASURE_BOOTSTRAP_TIME(NAME, REP, MSG, CODE) \
  do { \
    SAB_PROFILE_RESET(); \
    MEASURE_TIME(NAME, REP, MSG, CODE); \
    SAB_PROFILE_PRINT(); \
  } while (0)

void tlwe_print(TLWE c, TLWE_Key key, uint64_t prec){
  printf("%lu", torus2int(tlwe_phase(c, key), prec));
}

void trlwe_print(TRLWE c, TRLWE_Key key, uint64_t prec){
  TorusPolynomial tmp = polynomial_new_torus_polynomial(c->b->N);
  trlwe_phase(tmp, c, key);
#ifdef PRINT_POLY
  for (int64_t i = c->b->N - 1; i >= 0; i--){
    const uint64_t val = torus2int(tmp->coeffs[i], prec);
    if(val){
      printf("+ %lux^%ld ", val, i);
    }
  }
#else
  for (int64_t i = 0; i < c->b->N; i++){
    const uint64_t val = torus2int(tmp->coeffs[i], prec);
    printf("%lu, ", val);
  }
#endif
  printf("\n");
  free_polynomial(tmp);
}

void print_exp_poly(TRLWE * c, TRLWE_Key key, uint64_t n, uint64_t prec){
  TorusPolynomial tmp = polynomial_new_torus_polynomial(c[0]->b->N);
  for (size_t i = 0; i < n; i++){
    int64_t idx = -1;
    int64_t sign = 1;
    trlwe_phase(tmp, c[i], key);
    for (size_t j = 0; j < c[i]->b->N; j++){
      const uint64_t val = torus2int(tmp->coeffs[j], prec);
      if(val){
        if(idx != -1){
          printf("Decryption failed\n");
        }
        if(val > 1ULL << (prec - 1)) sign = -1;
        else sign = 1;
        idx = j;
      }
    }
    if(idx == -1){
      printf("Decryption failed\n");
    }
    #ifdef PRINT_POLY
    printf("+ %ldx^%ld ", idx*sign, i);
    #else
    printf("%ld, ", idx*sign);
    #endif
  }
  printf("\n");
  free_polynomial(tmp);
}

void test_NCMUX(){
  const uint64_t in_N = 1024, in_k = 1, out_N = 2048, out_k = 1, l = 1, bg_bit = 23, b_packing = 12, ell_packing = 2, t_aut = l, b_aut = bg_bit, h_in = 64, msg_prec = 4;
  TRLWE_Key input_key = trlwe_new_sparse_binary_key(in_N, in_k, h_in, pow(2, -20));
  TRLWE_Key out_key = trlwe_new_sparse_binary_key(out_N, out_k, h_in, pow(2, -53));
  TRGSW_Key output_key = trgsw_new_key(out_key, l, bg_bit);
  const uint64_t r_prec = get_min_prec(input_key);
  printf("Min precision: %lu\n", r_prec);
  SAB_Key sab = new_sparse_amortized_bootstrapping(input_key, out_key, output_key, msg_prec, b_packing, ell_packing, t_aut, b_aut, h_in, r_prec, false, false, false);
  TRLWE * rlwe = trlwe_alloc_new_sample_array(4, out_k, out_N);
  TRGSW_DFT * sel = trgsw_alloc_new_DFT_sample_array(2, l, bg_bit, out_k, out_N);
  trgsw_monomial_DFT_sample(sel[0], 0, 0, output_key);
  trgsw_monomial_DFT_sample(sel[1], 1, 0, output_key);
  trlwe_noiseless_trivial_sample(rlwe[1], NULL);
  trlwe_noiseless_trivial_sample(rlwe[2], NULL);
  rlwe[1]->b->coeffs[1] = int2torus(7, 4);
  rlwe[2]->b->coeffs[1] = int2torus(7, 4);
  NCMUX(rlwe[0], rlwe[1], rlwe[2], sel[0], sab);
  NCMUX(rlwe[3], rlwe[1], rlwe[2], sel[1], sab);
  trlwe_print(rlwe[0], out_key, 4);
  trlwe_print(rlwe[3], out_key, 4);
}

void test_monomial_mul(){
  const uint64_t in_N = 1024, in_k = 1, out_N = 2048, out_k = 1, l = 1, bg_bit = 23, b_packing = 12, ell_packing = 2, t_aut = l, b_aut = bg_bit, h_in = 64, msg_prec = 4;
  TRLWE_Key input_key = trlwe_new_sparse_binary_key(in_N, in_k, h_in, pow(2, -20));
  TRLWE_Key out_key = trlwe_new_sparse_binary_key(out_N, out_k, h_in, pow(2, -53));
  TRGSW_Key output_key = trgsw_new_key(out_key, l, bg_bit);
  const uint64_t r_prec = get_min_prec(input_key);
  printf("Min precision: %lu\n", r_prec);
  SAB_Key sab = new_sparse_amortized_bootstrapping(input_key, out_key, output_key, msg_prec, b_packing, ell_packing, t_aut, b_aut, h_in, r_prec, false, false, false);

  TRGSW_DFT * sel = trgsw_alloc_new_DFT_sample_array(r_prec, l, bg_bit, out_k, out_N);
  
  TRLWE rlwe_in = trlwe_new_sample(NULL, input_key);
  TRLWE rlwe_tv = trlwe_new_noiseless_trivial_sample(NULL, out_k, out_N);
  rlwe_tv->b->coeffs[1] += int2torus(1, 4);


  TRLWE * rlwe_acc = setup_single_tv(rlwe_in->b->coeffs, rlwe_tv, sab);
  
  print_exp_poly(rlwe_acc, out_key, sab->in_N, 4);
  RGSW_encrypt_bits(sel, sab->tmp->rgsw, output_key, 10, r_prec);
  RGSW_monomial_mul(rlwe_acc, sel, sab);
  print_exp_poly(rlwe_acc, out_key, sab->in_N, 4);
}

void test_sab_br(){
  const uint64_t in_N = 1024, in_k = 1, out_N = 2048, out_k = 1, l = 1, bg_bit = 23, b_packing = 12, ell_packing = 2, t_aut = l, b_aut = bg_bit, h_in = 64, msg_prec = 4;
  TRLWE_Key input_key = trlwe_new_sparse_binary_key(in_N, in_k, h_in, pow(2, -20));
  TRLWE_Key out_key = trlwe_new_sparse_binary_key(out_N, out_k, h_in, pow(2, -53));
  TRGSW_Key output_key = trgsw_new_key(out_key, l, bg_bit);
  const uint64_t r_prec = get_min_prec(input_key);
  printf("Min precision: %lu\n", r_prec);
  SAB_Key sab = new_sparse_amortized_bootstrapping(input_key, out_key, output_key, msg_prec, b_packing, ell_packing, t_aut, b_aut, h_in, r_prec, false, false, false);
  
  TorusPolynomial poly_in = polynomial_new_torus_polynomial(in_N);

  const uint64_t mod_mask = (1ULL<<(msg_prec - 1)) - 1;
  for (size_t i = 0; i < in_N; i++) poly_in->coeffs[i] = int2torus(i&mod_mask, msg_prec);

  TRLWE rlwe_in = trlwe_new_sample(poly_in, input_key);
  TRLWE rlwe_tv = trlwe_new_noiseless_trivial_sample(NULL, out_k, out_N);
  rlwe_tv->b->coeffs[1] += int2torus(1, 4);


  TRLWE * rlwe_acc = trlwe_alloc_new_sample_array(sab->in_N, sab->out_k, sab->out_N);
  MEASURE_BOOTSTRAP_TIME("", 10, "SAB",
    sab_rlwe_bootstrap_wo_extract(rlwe_acc, rlwe_in, rlwe_tv, sab);
  );

  print_exp_poly(rlwe_acc, out_key, sab->in_N, 4);
}

void test_sab(){
  const uint64_t reps = 3;
#if defined(SET_2_3_2048)
  const uint64_t in_N = 2048, in_k = 1, out_N = 2048, out_k = 1, l = 1, bg_bit = 23, b_packing = 14, ell_packing = 2, t_ks = 12, b_ks = 1, h_in = 39, h_out = 512, msg_prec = 3;
  const double sigma_in = pow(2, -15);
  const double sigma_out = pow(2, -50);
  const uint64_t target_r_prec = 7;
#elif defined(SET_2_3_4096)
  const uint64_t in_N = 4096, in_k = 1, out_N = 2048, out_k = 1, l = 1, bg_bit = 23, b_packing = 14, ell_packing = 2, t_ks = 12, b_ks = 1, h_in = 32, h_out = 512, msg_prec = 3;
  const double sigma_in = pow(2, -15);
  const double sigma_out = pow(2, -50);
  const uint64_t target_r_prec = 8; 
#elif defined(SET_2_3_8192)
  const uint64_t in_N = 8192, in_k = 1, out_N = 2048, out_k = 1, l = 1, bg_bit = 23, b_packing = 14, ell_packing = 2, t_ks = 12, b_ks = 1, h_in = 25, h_out = 512, msg_prec = 3;
  const double sigma_in = pow(2, -15);
  const double sigma_out = pow(2, -50);
  const uint64_t target_r_prec = 10; 
#elif defined(SET_4_5_2048)
  const uint64_t in_N = 2048, in_k = 1, out_N = 2048, out_k = 1, l = 1, bg_bit = 23, b_packing = 14, ell_packing = 2, t_ks = 14, b_ks = 1, h_in = 42, h_out = 512, msg_prec = 5;
  const double sigma_in = pow(2, -17);
  const double sigma_out = pow(2, -50);
  const uint64_t target_r_prec = 7;
#elif defined(SET_4_5_4096)
  const uint64_t in_N = 4096, in_k = 1, out_N = 2048, out_k = 1, l = 1, bg_bit = 23, b_packing = 14, ell_packing = 2, t_ks = 14, b_ks = 1, h_in = 34, h_out = 512, msg_prec = 5;
  const double sigma_in = pow(2, -18);
  const double sigma_out = pow(2, -50);
  const uint64_t target_r_prec = 8;
#elif defined(SET_4_5_8192)
  const uint64_t in_N = 8192, in_k = 1, out_N = 2048, out_k = 1, l = 1, bg_bit = 23, b_packing = 14, ell_packing = 2, t_ks = 14, b_ks = 1, h_in = 26, h_out = 512, msg_prec = 5;
  const double sigma_in = pow(2, -18);
  const double sigma_out = pow(2, -50);
  const uint64_t target_r_prec = 10;
#elif defined(SET_6_7_4096)
  const uint64_t in_N = 4096, in_k = 1, out_N = 2048, out_k = 1, l = 1, bg_bit = 23, b_packing = 14, ell_packing = 2, t_ks = 17, b_ks = 1, h_in = 33, h_out = 512, msg_prec = 7;
  const double sigma_in = pow(2, -21);
  const double sigma_out = pow(2, -50);
  const uint64_t target_r_prec = 9;
#elif defined(SET_6_7_8192)
  const uint64_t in_N = 8192, in_k = 1, out_N = 2048, out_k = 1, l = 1, bg_bit = 23, b_packing = 14, ell_packing = 2, t_ks = 17, b_ks = 1, h_in = 27, h_out = 512, msg_prec = 7;
  const double sigma_in = pow(2, -21);
  const double sigma_out = pow(2, -50);
  const uint64_t target_r_prec = 10;
#elif defined(SET_8_9_4096)
  const uint64_t in_N = 4096, in_k = 1, out_N = 8192, out_k = 1, l = 1, bg_bit = 22, b_packing = 14, ell_packing = 2, t_ks = 20, b_ks = 1, h_in = 34, h_out = 512, msg_prec = 9;
  const double sigma_in = pow(2, -24);
  const double sigma_out = pow(2, -51);
  const uint64_t target_r_prec = 9;
#elif defined(SET_8_9_8192)
  const uint64_t in_N = 8192, in_k = 1, out_N = 8192, out_k = 1, l = 1, bg_bit = 22, b_packing = 14, ell_packing = 2, t_ks = 20, b_ks = 1, h_in = 28, h_out = 512, msg_prec = 9;
  const double sigma_in = pow(2, -24);
  const double sigma_out = pow(2, -51);
  const uint64_t target_r_prec = 10;
#elif defined(SET_8_9_HIGH_FR)
  const uint64_t in_N = 8192, in_k = 1, out_N = 4096, out_k = 1, l = 1, bg_bit = 23, b_packing = 14, ell_packing = 2, t_ks = 17, b_ks = 1, h_in = 28, h_out = 512, msg_prec = 9;
  const double sigma_in = pow(2, -22);
  const double sigma_out = pow(2, -50);
  const uint64_t target_r_prec = 10;
#else
  const uint64_t in_N = 2048, in_k = 1, out_N = 2048, out_k = 1, l = 1, bg_bit = 23, b_packing = 14, ell_packing = 2, t_ks = 12, b_ks = 1, h_in = 39, h_out = 512, msg_prec = 3;
  const double sigma_in = pow(2, -15);
  const double sigma_out = pow(2, -50);
  const uint64_t target_r_prec = 7;
#endif
  printf("Sparse bootstrapping with binary keys\n");
  printf("Input: (N=%ld, h=%ld, binary, σ=2^%ld)\n", in_N, h_in, (int64_t) round(log2(sigma_in)));
  printf("Packing: (N=%ld, h=%ld, ternary, σ=2^%ld)\n", in_N, (uint64_t) 256, (int64_t) -44);
  printf("Output: (N=%ld, h=%ld, ternary, σ=2^%ld)\n", out_N, h_out, (int64_t) round(log2(sigma_out)));
  printf("Decomposition: BS(ℓ=%ld, β=2^%ld) PCK(ℓ=%ld, β=2^%ld) KS(ℓ=%ld, β=2^%ld)\n", 
        l, bg_bit, ell_packing, b_packing, t_ks, b_ks);
  printf("Message precision: %ld - Repetitions: %ld\n", msg_prec, reps);

  // end of parameters
  TRLWE_Key input_key;
  uint64_t rs_attempts = RS_sparse_binary_key(&input_key, in_N, in_k, h_in, sigma_in, target_r_prec);
  TRLWE_Key out_key = trlwe_new_ternary_key(out_N, out_k, h_out, sigma_out);
  TRLWE_Key packing_key = trlwe_new_ternary_key(in_N, in_k, 256, pow(2, -44));
  // TRLWE_Key packing_key = out_key;
  TRGSW_Key output_key = trgsw_new_key(out_key, l, bg_bit);
  const uint64_t r_prec = get_min_prec(input_key);
  printf("\nMax monomial distance (log B): %lu\n", r_prec);
  printf("Rejection Sampling Attempts: %lu\n", rs_attempts);
  SAB_Key sab = new_sparse_amortized_bootstrapping(input_key, packing_key, output_key, msg_prec, b_packing, ell_packing, t_ks, b_ks, h_in, r_prec, false, false, false);
  
  TorusPolynomial poly_in = polynomial_new_torus_polynomial(in_N);

  const uint64_t mod_mask = (1ULL<<(msg_prec - 1)) - 1;
  for (size_t i = 0; i < in_N; i++) poly_in->coeffs[i] = int2torus(i&mod_mask, msg_prec);

  TRLWE rlwe_in = trlwe_new_sample(poly_in, input_key);
  TRLWE rlwe_tv = trlwe_new_noiseless_trivial_sample(NULL, out_k, out_N);
  uint64_t LUT[1ULL << msg_prec];
  generate_random_bytes(sizeof(uint64_t)*(1ULL << msg_prec), (uint8_t *) LUT);
  for (size_t i = 0; i < (1ULL << msg_prec); i++) LUT[i] &= mod_mask;
  sab_LUT_packing(rlwe_tv, LUT, sab);
  // rlwe_tv->b->coeffs[0] += int2torus(1, 3);

  // TRLWE rlwe_out = trlwe_alloc_new_sample(in_k, in_N);
  // printf("in: "); trlwe_print(rlwe_in, input_key, msg_prec);
  // printf("tv: "); trlwe_print(rlwe_tv, out_key, msg_prec);
  MEASURE_BOOTSTRAP_TIME("", reps, "Bootstrapping time",
    sab_rlwe_bootstrap(rlwe_in, rlwe_in, rlwe_tv, sab);
  );
  TorusPolynomial res_poly = polynomial_new_torus_polynomial(in_N);
  trlwe_phase(res_poly, rlwe_in, input_key);
  bool pass = true;
  for (size_t i = 0; i < in_N; i++){
    const uint64_t res = torus2int(res_poly->coeffs[i], msg_prec);
    uint64_t expected = LUT[torus2int(poly_in->coeffs[i], msg_prec)];
    for (size_t j = 1; j < reps; j++) expected = LUT[expected];
    if(res != expected){
      printf("\nFail %lu: %lu != %lu\n", i, res, expected);
      pass = false;
    }
  }
  if(pass) printf("Pass");
  printf("\n");
  // printf("out: "); trlwe_print(rlwe_in, input_key, msg_prec);
}

void test_sab_tern(){
  const uint64_t reps = 3;
#if defined(SET_2_3_2048)
  const uint64_t in_N = 2048, in_k = 1, out_N = 2048, out_k = 1, l = 1, bg_bit = 23, b_packing = 14, ell_packing = 2, t_ks = 12, b_ks = 1, h_in = 35, h_out = 512, msg_prec = 3;
  const double sigma_in = pow(2, -15);
  const double sigma_out = pow(2, -50);
  const uint64_t target_r_prec = 7;
#elif defined(SET_2_3_4096)
  const uint64_t in_N = 4096, in_k = 1, out_N = 2048, out_k = 1, l = 1, bg_bit = 23, b_packing = 14, ell_packing = 2, t_ks = 12, b_ks = 1, h_in = 26, h_out = 512, msg_prec = 3;
  const double sigma_in = pow(2, -15);
  const double sigma_out = pow(2, -50);
  const uint64_t target_r_prec = 9;
#elif defined(SET_2_3_8192)
  const uint64_t in_N = 8192, in_k = 1, out_N = 2048, out_k = 1, l = 1, bg_bit = 23, b_packing = 14, ell_packing = 2, t_ks = 12, b_ks = 1, h_in = 23, h_out = 512, msg_prec = 3;
  const double sigma_in = pow(2, -16);
  const double sigma_out = pow(2, -50);
  const uint64_t target_r_prec = 10;
#elif defined(SET_4_5_2048)
  const uint64_t in_N = 2048, in_k = 1, out_N = 2048, out_k = 1, l = 1, bg_bit = 23, b_packing = 14, ell_packing = 2, t_ks = 14, b_ks = 1, h_in = 38, h_out = 512, msg_prec = 5;
  const double sigma_in = pow(2, -17);
  const double sigma_out = pow(2, -50);
  const uint64_t target_r_prec = 7;
#elif defined(SET_4_5_4096)
  const uint64_t in_N = 4096, in_k = 1, out_N = 2048, out_k = 1, l = 1, bg_bit = 23, b_packing = 14, ell_packing = 2, t_ks = 15, b_ks = 1, h_in = 28, h_out = 512, msg_prec = 5;
  const double sigma_in = pow(2, -18);
  const double sigma_out = pow(2, -50);
  const uint64_t target_r_prec = 9;
#elif defined(SET_4_5_8192)
  const uint64_t in_N = 8192, in_k = 1, out_N = 2048, out_k = 1, l = 1, bg_bit = 23, b_packing = 14, ell_packing = 2, t_ks = 15, b_ks = 1, h_in = 24, h_out = 512, msg_prec = 5;
  const double sigma_in = pow(2, -18);
  const double sigma_out = pow(2, -50);
  const uint64_t target_r_prec = 10;
#elif defined(SET_6_7_4096)
  const uint64_t in_N = 4096, in_k = 1, out_N = 2048, out_k = 1, l = 1, bg_bit = 23, b_packing = 14, ell_packing = 2, t_ks = 17, b_ks = 1, h_in = 30, h_out = 512, msg_prec = 7;
  const double sigma_in = pow(2, -21);
  const double sigma_out = pow(2, -50);
  const uint64_t target_r_prec = 9;
#elif defined(SET_6_7_8192)
  const uint64_t in_N = 8192, in_k = 1, out_N = 2048, out_k = 1, l = 1, bg_bit = 23, b_packing = 14, ell_packing = 2, t_ks = 17, b_ks = 1, h_in = 25, h_out = 512, msg_prec = 7;
  const double sigma_in = pow(2, -21);
  const double sigma_out = pow(2, -50);
  const uint64_t target_r_prec = 10;
#elif defined(SET_8_9_4096)
  const uint64_t in_N = 4096, in_k = 1, out_N = 8192, out_k = 1, l = 1, bg_bit = 22, b_packing = 14, ell_packing = 2, t_ks = 19, b_ks = 1, h_in = 32, h_out = 512, msg_prec = 9;
  const double sigma_in = pow(2, -24);
  const double sigma_out = pow(2, -50);
  const uint64_t target_r_prec = 9;
#elif defined(SET_8_9_8192)
  const uint64_t in_N = 8192, in_k = 1, out_N = 8192, out_k = 1, l = 1, bg_bit = 22, b_packing = 14, ell_packing = 2, t_ks = 19, b_ks = 1, h_in = 26, h_out = 512, msg_prec = 9;
  const double sigma_in = pow(2, -23);
  const double sigma_out = pow(2, -50);
  const uint64_t target_r_prec = 10;
#else 
  const uint64_t in_N = 2048, in_k = 1, out_N = 2048, out_k = 1, l = 1, bg_bit = 23, b_packing = 14, ell_packing = 2, t_ks = 10, b_ks = 1, h_in = 17, h_out = 512, msg_prec = 3;
  const double sigma_in = pow(2, -15);
  const double sigma_out = pow(2, -50);
  const uint64_t target_r_prec = 8;
  #endif
  printf("Sparse bootstrapping with ternary keys\n");
  printf("Input: (N=%ld, h=%ld, ternary, σ=2^%ld)\n", in_N, h_in, (int64_t) round(log2(sigma_in)));
  printf("Packing: (N=%ld, h=%ld, ternary, σ=2^%ld)\n", in_N, (uint64_t) 256, (int64_t) -44);
  printf("Output: (N=%ld, h=%ld, ternary, σ=2^%ld)\n", out_N, h_out, (int64_t) round(log2(sigma_out)));
  printf("Decomposition: BS(ℓ=%ld, β=2^%ld) PCK(ℓ=%ld, β=2^%ld) KS(ℓ=%ld, β=2^%ld)\n", 
        l, bg_bit, ell_packing, b_packing, t_ks, b_ks);
  printf("Message precision: %ld - Repetitions: %ld\n", msg_prec, reps);

  // end of parameters
  TRLWE_Key input_key;
  const uint64_t rs_attempts = RS_sparse_ternary_key(&input_key, in_N, in_k, h_in, sigma_in, target_r_prec);
  TRLWE_Key out_key = trlwe_new_ternary_key(out_N, out_k, h_out, sigma_out);
  TRLWE_Key packing_key = trlwe_new_ternary_key(in_N, in_k, 256, pow(2, -44));
  // TRLWE_Key packing_key = out_key;
  TRGSW_Key output_key = trgsw_new_key(out_key, l, bg_bit);
  const uint64_t r_prec = get_min_prec(input_key);
  printf("\nMonomial distance (log B): %lu\n", r_prec);
  printf("Rejection Sampling Attempts: %lu\n", rs_attempts);
  SAB_Key sab = new_sparse_amortized_bootstrapping(input_key, packing_key, output_key, msg_prec, b_packing, ell_packing, t_ks, b_ks, h_in, r_prec, false, true, false);
  
  TorusPolynomial poly_in = polynomial_new_torus_polynomial(in_N);

  const uint64_t mod_mask = (1ULL<<(msg_prec - 1)) - 1;
  for (size_t i = 0; i < in_N; i++) poly_in->coeffs[i] = int2torus(i&mod_mask, msg_prec);

  TRLWE rlwe_in = trlwe_new_sample(poly_in, input_key);
  TRLWE rlwe_tv = trlwe_new_noiseless_trivial_sample(NULL, out_k, out_N);
  uint64_t LUT[1ULL << msg_prec];
  generate_random_bytes(sizeof(uint64_t)*(1ULL << msg_prec), (uint8_t *) LUT);
  for (size_t i = 0; i < (1ULL << msg_prec); i++) LUT[i] &= mod_mask;
  sab_LUT_packing(rlwe_tv, LUT, sab);
  // rlwe_tv->b->coeffs[0] += int2torus(1, 3);

  // TRLWE rlwe_out = trlwe_alloc_new_sample(in_k, in_N);
  // printf("in: "); trlwe_print(rlwe_in, input_key, msg_prec);
  // printf("tv: "); trlwe_print(rlwe_tv, out_key, msg_prec);
  MEASURE_BOOTSTRAP_TIME("", reps, "Bootstrapping time",
    sab_rlwe_bootstrap(rlwe_in, rlwe_in, rlwe_tv, sab);
  );
  TorusPolynomial res_poly = polynomial_new_torus_polynomial(in_N);
  trlwe_phase(res_poly, rlwe_in, input_key);
  bool pass = true;
  for (size_t i = 0; i < in_N; i++){
    const uint64_t res = torus2int(res_poly->coeffs[i], msg_prec);
    uint64_t expected = LUT[torus2int(poly_in->coeffs[i], msg_prec)];
    for (size_t j = 1; j < reps; j++) expected = LUT[expected];
    if(res != expected){
      printf("\nFail %lu: %lu != %lu\n", i, res, expected);
      pass = false;
    }
  }
  if(pass) printf("Pass");
  printf("\n");
  // printf("out: "); trlwe_print(rlwe_in, input_key, msg_prec);
}


void test_sab_arbitrary(){
  const uint64_t reps = 3;
  const uint64_t key_bound = 8; // key in Z_8 = [-3,+4]
#if defined(SET_A2)
  const uint64_t in_N = 4096, in_k = 1, out_N = 2048, out_k = 1, l = 1, bg_bit = 23, b_packing = 14, ell_packing = 2, t_ks = 19, b_ks = 1, h_in = 32, h_out = 512, msg_prec = 5;
  const double sigma_in = pow(2, -24);
  const double sigma_out = pow(2, -50);
  const uint64_t target_r_prec = 9;
#elif defined(SET_A3)
  const uint64_t in_N = 8192, in_k = 1, out_N = 2048, out_k = 1, l = 1, bg_bit = 23, b_packing = 14, ell_packing = 2, t_ks = 19, b_ks = 1, h_in = 32, h_out = 512, msg_prec = 5;
  const double sigma_in = pow(2, -24);
  const double sigma_out = pow(2, -50);
  const uint64_t target_r_prec = 10;
#elif defined(SET_A4)
  const uint64_t in_N = 4096, in_k = 1, out_N = 8192, out_k = 1, l = 1, bg_bit = 22, b_packing = 14, ell_packing = 2, t_ks = 19, b_ks = 1, h_in = 32, h_out = 512, msg_prec = 7;
  const double sigma_in = pow(2, -24);
  const double sigma_out = pow(2, -50);
  const uint64_t target_r_prec = 9;
#elif defined(SET_A5)
  const uint64_t in_N = 8192, in_k = 1, out_N = 8192, out_k = 1, l = 1, bg_bit = 22, b_packing = 14, ell_packing = 2, t_ks = 19, b_ks = 1, h_in = 32, h_out = 512, msg_prec = 7;
  const double sigma_in = pow(2, -24);
  const double sigma_out = pow(2, -50);
  const uint64_t target_r_prec = 10;
#else 
  const uint64_t in_N = 4096, in_k = 1, out_N = 2048, out_k = 1, l = 1, bg_bit = 23, b_packing = 14, ell_packing = 2, t_ks = 19, b_ks = 1, h_in = 32, h_out = 512, msg_prec = 5;
  const double sigma_in = pow(2, -24);
  const double sigma_out = pow(2, -50);
  const uint64_t target_r_prec = 9;
#endif
  printf("Sparse bootstrapping with arbitrary keys\n");
  printf("Input: (N=%ld, h=%ld, θ=%ld, σ=2^%ld)\n", in_N, h_in, key_bound, (int64_t) round(log2(sigma_in)));
  printf("Packing: (N=%ld, h=%ld, ternary, σ=2^%ld)\n", in_N, (uint64_t) 256, (int64_t) -44);
  printf("Output: (N=%ld, h=%ld, ternary, σ=2^%ld)\n", out_N, h_out, (int64_t) round(log2(sigma_out)));
  printf("Decomposition: BS(ℓ=%ld, β=2^%ld) PCK(ℓ=%ld, β=2^%ld) KS(ℓ=%ld, β=2^%ld)\n", 
         l, bg_bit, ell_packing, b_packing, t_ks, b_ks);
  printf("Message precision: %ld - Repetitions: %ld\n", msg_prec, reps);

  // end of parameters
  TRLWE_Key input_key;
  const uint64_t rs_attempts = RS_sparse_arbitrary_key(&input_key, in_N, in_k, h_in, key_bound, sigma_in, target_r_prec);
  TRLWE_Key out_key = trlwe_new_ternary_key(out_N, out_k, h_out, sigma_out);
  TRLWE_Key packing_key = trlwe_new_ternary_key(in_N, in_k, 256, pow(2, -44));
  // TRLWE_Key packing_key = out_key;
  TRGSW_Key output_key = trgsw_new_key(out_key, l, bg_bit);
  const uint64_t r_prec = get_min_prec(input_key);
  printf("\nMonomial distance (log B): %lu\n", r_prec);
  printf("Rejection Sampling Attempts: %lu\n", rs_attempts);
  SAB_Key sab = new_sparse_amortized_bootstrapping(input_key, packing_key, output_key, msg_prec, b_packing, ell_packing, t_ks, b_ks, h_in, r_prec, false, false, true);
  
  TorusPolynomial poly_in = polynomial_new_torus_polynomial(in_N);

  const uint64_t mod_mask = (1ULL<<(msg_prec - 1)) - 1;
  for (size_t i = 0; i < in_N; i++) poly_in->coeffs[i] = int2torus(i&mod_mask, msg_prec);

  TRLWE rlwe_in = trlwe_new_sample(poly_in, input_key);
  TRLWE rlwe_tv = trlwe_new_noiseless_trivial_sample(NULL, out_k, out_N);
  uint64_t LUT[1ULL << msg_prec];
  for (size_t i = 0; i < (1ULL << msg_prec); i++) LUT[i] = ((i*i) &mod_mask);
  sab_LUT_packing(rlwe_tv, LUT, sab);
  // rlwe_tv->b->coeffs[0] += int2torus(1, 3);

  // TRLWE rlwe_out = trlwe_alloc_new_sample(in_k, in_N);
  // printf("in: "); trlwe_print(rlwe_in, input_key, msg_prec);
  // printf("tv: "); trlwe_print(rlwe_tv, out_key, msg_prec);
  MEASURE_BOOTSTRAP_TIME("", reps, "Bootstrapping time",
    sab_rlwe_bootstrap(rlwe_in, rlwe_in, rlwe_tv, sab);
  );
  TorusPolynomial res_poly = polynomial_new_torus_polynomial(in_N);
  trlwe_phase(res_poly, rlwe_in, input_key);
  bool pass = true;
  for (size_t i = 0; i < in_N; i++){
    const uint64_t res = torus2int(res_poly->coeffs[i], msg_prec);
    uint64_t expected = LUT[torus2int(poly_in->coeffs[i], msg_prec)];
    for (size_t j = 1; j < reps; j++) expected = LUT[expected];
    if(res != expected){
      printf("\nFail %lu: %lu != %lu\n", i, res, expected);
      pass = false;
    }
  }
  if(pass) printf("Pass");
  printf("\n");
  // printf("out: "); trlwe_print(rlwe_in, input_key, msg_prec);
}

void test_sab_lwe(){
  const uint64_t in_N = 1024, in_k = 1, out_N = 2048, out_k = 1, l = 1, bg_bit = 23, b_packing = 12, ell_packing = 2, t_aut = 20, b_aut = 1, h_in = 64, msg_prec = 4;
  TRLWE_Key input_key = trlwe_new_sparse_binary_key(in_N, in_k, h_in, pow(2, -20));
  TRLWE_Key out_key = trlwe_new_sparse_binary_key(out_N, out_k, h_in, pow(2, -53));
  TRGSW_Key output_key = trgsw_new_key(out_key, l, bg_bit);
  const uint64_t r_prec = get_min_prec(input_key);
  printf("Min precision: %lu\n", r_prec);
  SAB_Key sab = new_sparse_amortized_bootstrapping(input_key, out_key, output_key, msg_prec, b_packing, ell_packing, t_aut, b_aut, h_in, r_prec, false, false, false);
  
  TorusPolynomial poly_in = polynomial_new_torus_polynomial(in_N);

  const uint64_t mod_mask = (1ULL<<(msg_prec - 1)) - 1;
  for (size_t i = 0; i < in_N; i++) poly_in->coeffs[i] = int2torus(i&mod_mask, msg_prec);

  TRLWE rlwe_in = trlwe_new_sample(poly_in, input_key);
  TRLWE rlwe_tv = trlwe_new_noiseless_trivial_sample(NULL, out_k, out_N);
  uint64_t LUT[1ULL << msg_prec];
  for (size_t i = 0; i < (1ULL << msg_prec); i++) LUT[i] = i;
  sab_LUT_packing(rlwe_tv, LUT, sab);

  printf("in: "); trlwe_print(rlwe_in, input_key, msg_prec);
  printf("tv: "); trlwe_print(rlwe_tv, out_key, msg_prec);
  MEASURE_BOOTSTRAP_TIME("", 1, "SAB LWE",
    sab_rlwe_to_lwe_bootstrap(sab->tmp->extracted_poly, rlwe_in, rlwe_tv, sab);
  );
  TLWE_Key extracted_key = tlwe_alloc_key(out_N*out_k, output_key->trlwe_key->sigma);

  trlwe_extract_tlwe_key(extracted_key, output_key->trlwe_key);
  printf("out: ");
  for (size_t i = 0; i < in_N; i++){
    const uint64_t res = torus2int(tlwe_phase(sab->tmp->extracted_poly[i], extracted_key), msg_prec);
    const uint64_t expected = LUT[torus2int(poly_in->coeffs[i], msg_prec)];
    if(res != expected){
      printf("\nFail %lu: %lu != %lu\n", i, res, expected);
    }
    printf("%lu, ", res);
  }
  printf("\n");

  // trlwe_print(rlwe_out, input_key, msg_prec);
}

void test_sab_microbench(){
  const uint64_t in_N = 2048, in_k = 1, out_N = 2048, out_k = 1;
  const uint64_t l = 1, bg_bit = 23, b_packing = 14, ell_packing = 2;
  const uint64_t t_ks = 12, b_ks = 1, h_in = 39, msg_prec = 3;
  const uint64_t target_r_prec = 7;
  const uint64_t ep_reps = 2000, cmux_reps = 2000, monomial_reps = 5;
  const double sigma_in = pow(2, -15);
  const double sigma_out = pow(2, -50);

  printf("SAB microbench with binary SET_2_3_2048 shape\n");
  printf("Reps: external_product=%" PRIu64 ", CMUX=%" PRIu64 ", RGSW_monomial_mul=%" PRIu64 "\n",
         ep_reps, cmux_reps, monomial_reps);

  TRLWE_Key input_key;
  uint64_t rs_attempts = RS_sparse_binary_key(&input_key, in_N, in_k, h_in, sigma_in, target_r_prec);
  TRLWE_Key out_key = trlwe_new_ternary_key(out_N, out_k, 512, sigma_out);
  TRLWE_Key packing_key = trlwe_new_ternary_key(in_N, in_k, 256, pow(2, -44));
  TRGSW_Key output_key = trgsw_new_key(out_key, l, bg_bit);
  const uint64_t r_prec = get_min_prec(input_key);
  printf("Max monomial distance (log B): %" PRIu64 "\n", r_prec);
  printf("Rejection Sampling Attempts: %" PRIu64 "\n", rs_attempts);

  SAB_Key sab = new_sparse_amortized_bootstrapping(input_key, packing_key, output_key, msg_prec,
      b_packing, ell_packing, t_ks, b_ks, h_in, r_prec, false, false, false);

  TRLWE ep_in = trlwe_new_sample(NULL, out_key);
  TRLWE_DFT ep_out = trlwe_alloc_new_DFT_sample(out_k, out_N);
  MEASURE_BOOTSTRAP_TIME("", ep_reps, "Microbench trgsw_mul_trlwe_DFT",
    trgsw_mul_trlwe_DFT(ep_out, ep_in, sab->s[0][0][0]);
  );

  TRLWE cmux_out = trlwe_new_noiseless_trivial_sample(NULL, out_k, out_N);
  TRLWE cmux_in1 = trlwe_new_sample(NULL, out_key);
  TRLWE cmux_in2 = trlwe_new_sample(NULL, out_key);
  MEASURE_BOOTSTRAP_TIME("", cmux_reps, "Microbench CMUX",
    CMUX(cmux_out, cmux_in1, cmux_in2, sab->s[0][0][0], sab);
  );

  TRLWE rlwe_in = trlwe_new_sample(NULL, input_key);
  TRLWE tv = trlwe_new_noiseless_trivial_sample(NULL, out_k, out_N);
  tv->b->coeffs[1] += int2torus(1, msg_prec);
  TRLWE * acc = trlwe_alloc_new_sample_array(in_N, out_k, out_N);
  setup_tv_xb(acc, rlwe_in->b->coeffs, tv, sab);
  MEASURE_BOOTSTRAP_TIME("", monomial_reps, "Microbench RGSW_monomial_mul",
    RGSW_monomial_mul(acc, sab->s[0][0], sab);
  );
}

#if defined(SAB_PVW_KERNEL_TEST) || defined(SAB_PVW_RGT4_KERNEL_TEST) || defined(SAB_PVW_TARGET_TEST) || defined(SAB_PVW_BENCH) || defined(SAB_PVW_NOISE_TEST) || defined(SAB_PVW_STAGE_NOISE_TEST) || defined(SAB_PVW_RESOURCE_TEST)
static TRLWE_Key trlwe_key_from_pvmtmlwe_lane(PVW_TMLWE_Key in, int lane){
  const int N = in->s[0][lane]->N;
  TRLWE_Key out = trlwe_alloc_key(N, in->k, in->sigma);
  for (size_t i = 0; i < in->k; i++){
    polynomial_copy_torus_polynomial(out->s[i], in->s[i][lane]);
    polynomial_copy_DFT_polynomial(out->s_dft[i], in->s_dft[i][lane]);
  }
  return out;
}

#ifndef SAB_PVW_BENCH_R
#define SAB_PVW_BENCH_R 2
#endif

#ifndef SAB_PVW_BENCH_REPS
#define SAB_PVW_BENCH_REPS 3
#endif

#ifndef SAB_PVW_NOISE_R
#define SAB_PVW_NOISE_R 2
#endif

#ifndef SAB_PVW_NOISE_TRIALS
#define SAB_PVW_NOISE_TRIALS 3
#endif

#ifndef SAB_PVW_NOISE_MAX_LOG2_GAP
#define SAB_PVW_NOISE_MAX_LOG2_GAP 4.0
#endif

#ifndef SAB_PVW_RESOURCE_R
#define SAB_PVW_RESOURCE_R 2
#endif

#if !defined(BINARY)
#error "SAB_PVW target harness currently supports only KEY=BINARY"
#endif

typedef struct {
  int in_N;
  int in_k;
  int out_N;
  int out_k;
  int l;
  int bg_bit;
  int prec;
  int h;
  int r_prec;
  int h_out;
  int h_packing;
  int ell_packing;
  int b_packing;
  int t_ks;
  int b_ks;
  double sigma_in;
  double sigma_out;
  double sigma_packing;
} SAB_PVW_Target_Params;

static SAB_PVW_Target_Params sab_pvw_target_params(void){
#if defined(SET_2_3_4096)
  return (SAB_PVW_Target_Params){4096, 1, 2048, 1, 1, 23, 3, 32, 8,
      512, 256, 2, 14, 12, 1, pow(2, -15), pow(2, -50), pow(2, -44)};
#elif defined(SET_2_3_8192)
  return (SAB_PVW_Target_Params){8192, 1, 2048, 1, 1, 23, 3, 25, 10,
      512, 256, 2, 14, 12, 1, pow(2, -15), pow(2, -50), pow(2, -44)};
#elif defined(SET_4_5_2048)
  return (SAB_PVW_Target_Params){2048, 1, 2048, 1, 1, 23, 5, 42, 7,
      512, 256, 2, 14, 14, 1, pow(2, -17), pow(2, -50), pow(2, -44)};
#elif defined(SET_4_5_4096)
  return (SAB_PVW_Target_Params){4096, 1, 2048, 1, 1, 23, 5, 34, 8,
      512, 256, 2, 14, 14, 1, pow(2, -18), pow(2, -50), pow(2, -44)};
#elif defined(SET_4_5_8192)
  return (SAB_PVW_Target_Params){8192, 1, 2048, 1, 1, 23, 5, 26, 10,
      512, 256, 2, 14, 14, 1, pow(2, -18), pow(2, -50), pow(2, -44)};
#elif defined(SET_6_7_4096)
  return (SAB_PVW_Target_Params){4096, 1, 2048, 1, 1, 23, 7, 33, 9,
      512, 256, 2, 14, 17, 1, pow(2, -21), pow(2, -50), pow(2, -44)};
#elif defined(SET_6_7_8192)
  return (SAB_PVW_Target_Params){8192, 1, 2048, 1, 1, 23, 7, 27, 10,
      512, 256, 2, 14, 17, 1, pow(2, -21), pow(2, -50), pow(2, -44)};
#elif defined(SET_8_9_4096)
  return (SAB_PVW_Target_Params){4096, 1, 8192, 1, 1, 22, 9, 34, 9,
      512, 256, 2, 14, 20, 1, pow(2, -24), pow(2, -51), pow(2, -44)};
#elif defined(SET_8_9_8192)
  return (SAB_PVW_Target_Params){8192, 1, 8192, 1, 1, 22, 9, 28, 10,
      512, 256, 2, 14, 20, 1, pow(2, -24), pow(2, -51), pow(2, -44)};
#elif defined(SET_8_9_HIGH_FR)
  return (SAB_PVW_Target_Params){8192, 1, 4096, 1, 1, 23, 9, 28, 10,
      512, 256, 2, 14, 17, 1, pow(2, -22), pow(2, -50), pow(2, -44)};
#else
  return (SAB_PVW_Target_Params){2048, 1, 2048, 1, 1, 23, 3, 39, 7,
      512, 256, 2, 14, 12, 1, pow(2, -15), pow(2, -50), pow(2, -44)};
#endif
}

static void sab_pvw_fill_target_distances(uint64_t * distances,
    const SAB_PVW_Target_Params * params){
  const uint64_t slots = (uint64_t) params->h + 1;
  const uint64_t base = ((uint64_t) params->in_N) / slots;
  const uint64_t remainder = ((uint64_t) params->in_N) % slots;
  const uint64_t r_max = 1ULL << params->r_prec;
  uint64_t sum = 0;
  for (size_t idx = 0; idx < (size_t) params->h; idx++){
    const uint64_t distance = base + (idx < remainder ? 1 : 0);
    if(distance == 0 || distance >= r_max){
      printf("SAB_PVW target unsupported distance idx=%" PRIu64
             " distance=%" PRIu64 " r_prec=%d\n",
             (uint64_t) idx, distance, params->r_prec);
      exit(1);
    }
    distances[idx] = distance;
    sum += distance;
  }
  const uint64_t tail = ((uint64_t) params->in_N) - sum;
  if(tail == 0 || tail >= r_max){
    printf("SAB_PVW target unsupported tail distance=%" PRIu64
           " r_prec=%d\n", tail, params->r_prec);
    exit(1);
  }
}

typedef struct {
  double sq_sum;
  uint64_t count;
  uint64_t failures;
  uint64_t max_abs;
} TorusNoiseStats;

static double mean_u64(const uint64_t * values, int count){
  double sum = 0.0;
  for (size_t idx = 0; idx < (size_t) count; idx++) sum += values[idx];
  return sum / count;
}

static double stddev_u64(const uint64_t * values, int count, double mean){
  if(count < 2) return 0.0;
  double sq_sum = 0.0;
  for (size_t idx = 0; idx < (size_t) count; idx++){
    const double diff = values[idx] - mean;
    sq_sum += diff * diff;
  }
  return sqrt(sq_sum / (count - 1));
}

static double mean_double(const double * values, int count){
  double sum = 0.0;
  for (size_t idx = 0; idx < (size_t) count; idx++) sum += values[idx];
  return sum / count;
}

static double stddev_double(const double * values, int count, double mean){
  if(count < 2) return 0.0;
  double sq_sum = 0.0;
  for (size_t idx = 0; idx < (size_t) count; idx++){
    const double diff = values[idx] - mean;
    sq_sum += diff * diff;
  }
  return sqrt(sq_sum / (count - 1));
}

static uint64_t read_proc_status_kb(const char * key){
  FILE * fd = fopen("/proc/self/status", "r");
  if(fd == NULL) return 0;
  char line[256];
  uint64_t value = 0;
  const size_t key_len = strlen(key);
  while(fgets(line, sizeof(line), fd) != NULL){
    if(strncmp(line, key, key_len) == 0 && line[key_len] == ':'){
      char * p = line + key_len + 1;
      while(*p == ' ' || *p == '\t') p++;
      value = strtoull(p, NULL, 10);
      break;
    }
  }
  fclose(fd);
  return value;
}

static void print_resource_rss(const char * label, int r, const char * mode){
  printf("SAB_PVW_RESOURCE rss target_full r=%d mode=%s label=%s vmrss_kb=%" PRIu64
         " vmhwm_kb=%" PRIu64 "\n",
         r, mode, label, read_proc_status_kb("VmRSS"),
         read_proc_status_kb("VmHWM"));
}

static uint64_t bytes_torus_polynomial(int N){
  return sizeof(struct _TorusPolynomial) + sizeof(Torus) * (uint64_t) N;
}

static uint64_t bytes_dft_polynomial(int N){
  return sizeof(struct _DFT_Polynomial) + sizeof(double) * (uint64_t) N;
}

static uint64_t bytes_trlwe_sample(int k, int N){
  return sizeof(struct _TRLWE) + sizeof(TorusPolynomial) * (uint64_t) k
      + ((uint64_t) k + 1) * bytes_torus_polynomial(N);
}

static uint64_t bytes_trlwe_dft_sample(int k, int N){
  return sizeof(struct _TRLWE_DFT) + sizeof(DFT_Polynomial) * (uint64_t) k
      + ((uint64_t) k + 1) * bytes_dft_polynomial(N);
}

static uint64_t bytes_pvmtmlwe_sample(int k, int r, int N){
  return sizeof(struct _PVW_TMLWE)
      + sizeof(TorusPolynomial) * ((uint64_t) k + (uint64_t) r)
      + ((uint64_t) k + (uint64_t) r) * bytes_torus_polynomial(N);
}

static uint64_t bytes_pvmtmlwe_dft_sample(int k, int r, int N){
  return sizeof(struct _PVW_TMLWE_DFT)
      + sizeof(DFT_Polynomial) * ((uint64_t) k + (uint64_t) r)
      + ((uint64_t) k + (uint64_t) r) * bytes_dft_polynomial(N);
}

static uint64_t bytes_trgsw_dft_sample(int l, int k, int N){
  const uint64_t rows = (uint64_t) l * ((uint64_t) k + 1);
  return sizeof(struct _TRGSW_DFT) + sizeof(TRLWE_DFT) * rows
      + rows * bytes_trlwe_dft_sample(k, N);
}

static uint64_t bytes_mat_trgsw_dft_sample(int l, int k, int r, int N){
  const uint64_t rows = (uint64_t) l * ((uint64_t) k + (uint64_t) r);
  return sizeof(struct _MAT_TRGSW_DFT) + sizeof(PVW_TMLWE_DFT) * rows
      + rows * bytes_pvmtmlwe_dft_sample(k, r, N);
}

static uint64_t bytes_trlwe_ks_key(int in_k, int t, int out_k, int out_N){
  return sizeof(struct _TRLWE_KS_Key) + sizeof(TRLWE_DFT *) * (uint64_t) in_k
      + sizeof(TRLWE_DFT) * (uint64_t) in_k * (uint64_t) t
      + (uint64_t) in_k * (uint64_t) t
          * bytes_trlwe_dft_sample(out_k, out_N);
}

static uint64_t bytes_pvmtmlwe_ks_key(int in_k, int t, int out_k, int r,
    int out_N){
  return sizeof(struct _PVW_TMLWE_KS_Key)
      + sizeof(PVW_TMLWE_DFT *) * (uint64_t) in_k
      + sizeof(PVW_TMLWE_DFT) * (uint64_t) in_k * (uint64_t) t
      + (uint64_t) in_k * (uint64_t) t
          * bytes_pvmtmlwe_dft_sample(out_k, r, out_N);
}

static uint64_t estimate_scalar_sab_public_key_bytes(int in_N, int in_k,
    int out_N, int out_k, int h, int r_prec, int l, int ell_packing,
    int t_ks){
  const uint64_t selector_ptr_bytes =
      sizeof(TRGSW_DFT ***) * (uint64_t) in_k
      + sizeof(TRGSW_DFT **) * (uint64_t) in_k * ((uint64_t) h + 1)
      + sizeof(TRGSW_DFT) * (uint64_t) in_k * ((uint64_t) h + 1)
          * (uint64_t) r_prec;
  const uint64_t selector_bytes =
      (uint64_t) in_k * ((uint64_t) h + 1) * (uint64_t) r_prec
      * bytes_trgsw_dft_sample(l, out_k, out_N);
  const uint64_t aut_bytes = bytes_trlwe_ks_key(out_k, l, out_k, out_N);
  const uint64_t packing_bytes = bytes_trlwe_ks_key(out_N * out_k,
      ell_packing, in_k, in_N);
  const uint64_t hw_bytes = bytes_trlwe_ks_key(in_k, t_ks, in_k, in_N);
  return sizeof(struct _SAB_Key) + selector_ptr_bytes + selector_bytes
      + aut_bytes + packing_bytes + hw_bytes;
}

static uint64_t estimate_pvw_sab_public_key_bytes(int in_N, int in_k,
    int out_N, int out_k, int lanes, int h, int r_prec, int l,
    int ell_packing, int t_ks){
  const uint64_t selector_ptr_bytes =
      sizeof(MAT_TRGSW_DFT ***) * (uint64_t) in_k
      + sizeof(MAT_TRGSW_DFT **) * (uint64_t) in_k * ((uint64_t) h + 1)
      + sizeof(MAT_TRGSW_DFT) * (uint64_t) in_k * ((uint64_t) h + 1)
          * (uint64_t) r_prec;
  const uint64_t selector_bytes =
      (uint64_t) in_k * ((uint64_t) h + 1) * (uint64_t) r_prec
      * bytes_mat_trgsw_dft_sample(l, out_k, lanes, out_N);
  const uint64_t aut_bytes = bytes_pvmtmlwe_ks_key(out_k, l, out_k, lanes,
      out_N);
  const uint64_t packing_bytes = (uint64_t) lanes
      * bytes_trlwe_ks_key(out_N * out_k, ell_packing, in_k, in_N);
  const uint64_t hw_bytes = bytes_trlwe_ks_key(in_k, t_ks, in_k, in_N);
  return sizeof(struct _SAB_PVW_Key) + sizeof(struct _MAT_TRGSW_Key)
      + sizeof(TRLWE_KS_Key) * (uint64_t) lanes + selector_ptr_bytes
      + selector_bytes + aut_bytes + packing_bytes + hw_bytes;
}

static uint64_t torus_abs_diff(Torus lhs, Torus rhs){
  const uint64_t lhs_to_rhs = (uint64_t) (lhs - rhs);
  const uint64_t rhs_to_lhs = (uint64_t) (rhs - lhs);
  return lhs_to_rhs < rhs_to_lhs ? lhs_to_rhs : rhs_to_lhs;
}

static void torus_noise_stats_add(TorusNoiseStats * stats, Torus value,
    Torus expected, uint64_t value_q, uint64_t expected_q){
  const uint64_t diff = torus_abs_diff(value, expected);
  const double diff_d = (double) diff;
  stats->sq_sum += diff_d * diff_d;
  stats->count++;
  if(diff > stats->max_abs) stats->max_abs = diff;
  if(value_q != expected_q) stats->failures++;
}

static void torus_noise_stats_merge(TorusNoiseStats * out,
    TorusNoiseStats in){
  out->sq_sum += in.sq_sum;
  out->count += in.count;
  out->failures += in.failures;
  if(in.max_abs > out->max_abs) out->max_abs = in.max_abs;
}

static double torus_noise_log2_sigma(TorusNoiseStats stats){
  if(stats.count == 0 || stats.sq_sum == 0.0) return -INFINITY;
  return 0.5 * log2(stats.sq_sum / (double) stats.count) - 64.0;
}

static double torus_noise_log2_max_abs(TorusNoiseStats stats){
  if(stats.max_abs == 0) return -INFINITY;
  return log2((double) stats.max_abs) - 64.0;
}

static void print_torus_noise_stats(const char * label, TorusNoiseStats stats){
  printf("%s count=%" PRIu64 " failures=%" PRIu64
         " log2_sigma_torus=%.3f log2_max_abs_torus=%.3f\n",
         label, stats.count, stats.failures, torus_noise_log2_sigma(stats),
         torus_noise_log2_max_abs(stats));
}

static TRLWE_Key test_binary_key_from_distances(int N, int k,
    const uint64_t * distances, int h, double sigma){
  TRLWE_Key out = trlwe_alloc_key(N, k, sigma);
  for (size_t key_idx = 0; key_idx < (size_t) k; key_idx++){
    memset(out->s[key_idx]->coeffs, 0, sizeof(Torus) * N);
    uint64_t previous = N;
    for (size_t step = 0; step < (size_t) h; step++){
      const uint64_t distance = distances[step];
      if(distance == 0 || distance > previous){
        printf("Invalid test sparse distance step=%" PRIu64 " distance=%" PRIu64
               " previous=%" PRIu64 "\n", (uint64_t) step, distance, previous);
        exit(1);
      }
      previous -= distance;
      out->s[key_idx]->coeffs[previous] = 1;
    }
    polynomial_torus_to_DFT(out->s_dft[key_idx], out->s[key_idx]);
  }
  return out;
}

static bool check_mat_trgsw_identity_lane(int r){
  const int N = 1024, k = 1, l = 1, bg_bit = 23, prec = 3;
  const int rows = (k + r) * l;
  PVW_TMLWE_Key key = pvmtmlwe_new_binary_key(N, k, r, pow(2, -50));
  MAT_TRGSW_Key mat_key = mat_trgsw_new_key(key, l, bg_bit);
  TorusPolynomial * msg = polynomial_new_array_of_torus_polynomials(N, r);
  TorusPolynomial * phase_in = polynomial_new_array_of_torus_polynomials(N, r);
  TorusPolynomial * phase_out = polynomial_new_array_of_torus_polynomials(N, r);

  for (size_t lane = 0; lane < r; lane++){
    for (size_t i = 0; i < N; i++){
      msg[lane]->coeffs[i] = int2torus((i + lane) & 3, prec);
    }
  }

  PVW_TMLWE in = pvmtmlwe_new_sample(msg, key);
  PVW_TMLWE out = pvmtmlwe_alloc_new_sample(k, r, N);
  PVW_TMLWE_DFT out_dft = pvmtmlwe_alloc_new_DFT_sample(k, r, N);
  MAT_TRGSW_DFT selector = mat_trgsw_alloc_new_DFT_sample(l, bg_bit, k, r, N);
  MAT_TRGSW_MUL_SCRATCH scratch = mat_trgsw_alloc_mul_scratch(rows, N);

  mat_trgsw_monomial_DFT_sample(selector, 1, 0, mat_key);
  mat_trgsw_mul_pvmtmlwe_DFT(out_dft, in, selector, scratch);
  pvmtmlwe_from_DFT(out, out_dft);
  pvmtmlwe_phase(phase_in, in, key);
  pvmtmlwe_phase(phase_out, out, key);

  bool pass = true;
  for (size_t lane = 0; lane < r; lane++){
    for (size_t i = 0; i < N; i++){
      const uint64_t expected = torus2int(phase_in[lane]->coeffs[i], prec);
      const uint64_t got = torus2int(phase_out[lane]->coeffs[i], prec);
      if(got != expected){
        printf("MAT_TRGSW identity fail r=%d lane=%" PRIu64 " coeff=%" PRIu64 ": %" PRIu64 " != %" PRIu64 "\n",
               r, (uint64_t) lane, (uint64_t) i, got, expected);
        pass = false;
        break;
      }
    }
    if(!pass) break;
  }

  free_mat_trgsw_mul_scratch(scratch);
  free_mat_trgsw_DFT(selector);
  free_pvmtmlwe_DFT(out_dft);
  free_pvmtmlwe(out);
  free_pvmtmlwe(in);
  free_array_of_polynomials(phase_out, r);
  free_array_of_polynomials(phase_in, r);
  free_array_of_polynomials(msg, r);
  free_mat_trgsw_key(mat_key);
  free_pvmtmlwe_key(key);
  return pass;
}

static bool check_mat_trgsw_scalar_equivalence(void){
  const int N = 1024, k = 1, r = 1, l = 1, bg_bit = 23, prec = 3;
  const int rows = (k + r) * l;

  PVW_TMLWE_Key pvw_key = pvmtmlwe_new_binary_key(N, k, r, pow(2, -50));
  TRLWE_Key scalar_key = trlwe_key_from_pvmtmlwe_lane(pvw_key, 0);
  MAT_TRGSW_Key mat_key = mat_trgsw_new_key(pvw_key, l, bg_bit);
  TRGSW_Key scalar_trgsw_key = trgsw_new_key(scalar_key, l, bg_bit);

  TorusPolynomial * msg = polynomial_new_array_of_torus_polynomials(N, r);
  for (size_t i = 0; i < N; i++){
    msg[0]->coeffs[i] = int2torus(i & 3, prec);
  }

  PVW_TMLWE pvw_in = pvmtmlwe_new_sample(msg, pvw_key);
  TRLWE scalar_in = trlwe_alloc_new_sample(k, N);
  polynomial_copy_torus_polynomial(scalar_in->a[0], pvw_in->a[0]);
  polynomial_copy_torus_polynomial(scalar_in->b, pvw_in->b[0]);

  MAT_TRGSW_DFT mat_selector = mat_trgsw_alloc_new_DFT_sample(l, bg_bit, k, r, N);
  TRGSW_DFT scalar_selector = trgsw_alloc_new_DFT_sample(l, bg_bit, k, N);
  PVW_TMLWE_DFT pvw_out_dft = pvmtmlwe_alloc_new_DFT_sample(k, r, N);
  TRLWE_DFT scalar_out_dft = trlwe_alloc_new_DFT_sample(k, N);
  PVW_TMLWE pvw_out = pvmtmlwe_alloc_new_sample(k, r, N);
  TRLWE scalar_out = trlwe_alloc_new_sample(k, N);
  MAT_TRGSW_MUL_SCRATCH scratch = mat_trgsw_alloc_mul_scratch(rows, N);
  TorusPolynomial * pvw_phase = polynomial_new_array_of_torus_polynomials(N, r);
  TorusPolynomial scalar_phase = polynomial_new_torus_polynomial(N);

  mat_trgsw_monomial_DFT_sample(mat_selector, 1, 0, mat_key);
  trgsw_monomial_DFT_sample(scalar_selector, 1, 0, scalar_trgsw_key);
  mat_trgsw_mul_pvmtmlwe_DFT(pvw_out_dft, pvw_in, mat_selector, scratch);
  trgsw_mul_trlwe_DFT(scalar_out_dft, scalar_in, scalar_selector);
  pvmtmlwe_from_DFT(pvw_out, pvw_out_dft);
  trlwe_from_DFT(scalar_out, scalar_out_dft);
  pvmtmlwe_phase(pvw_phase, pvw_out, pvw_key);
  trlwe_phase(scalar_phase, scalar_out, scalar_key);

  bool pass = true;
  for (size_t i = 0; i < N; i++){
    const uint64_t pvw_val = torus2int(pvw_phase[0]->coeffs[i], prec);
    const uint64_t scalar_val = torus2int(scalar_phase->coeffs[i], prec);
    if(pvw_val != scalar_val){
      printf("MAT_TRGSW scalar equivalence fail coeff=%" PRIu64 ": %" PRIu64 " != %" PRIu64 "\n",
             (uint64_t) i, pvw_val, scalar_val);
      pass = false;
      break;
    }
  }

  free_array_of_polynomials(pvw_phase, r);
  free_polynomial(scalar_phase);
  free_mat_trgsw_mul_scratch(scratch);
  free_pvmtmlwe(pvw_out);
  free_trlwe(scalar_out);
  free_pvmtmlwe_DFT(pvw_out_dft);
  free_trlwe(scalar_out_dft);
  free_mat_trgsw_DFT(mat_selector);
  free_trgsw(scalar_selector);
  free_trlwe(scalar_in);
  free_pvmtmlwe(pvw_in);
  free_array_of_polynomials(msg, r);
  free_trgsw_key(scalar_trgsw_key);
  free_mat_trgsw_key(mat_key);
  free_trlwe_key(scalar_key);
  free_pvmtmlwe_key(pvw_key);
  return pass;
}

static void bench_mat_trgsw_kernel_lane(int r){
  const int N = 2048, k = 1, l = 1, bg_bit = 23;
  const int rows = (k + r) * l;
  const uint64_t reps = 1000;
  PVW_TMLWE_Key key = pvmtmlwe_new_binary_key(N, k, r, pow(2, -50));
  MAT_TRGSW_Key mat_key = mat_trgsw_new_key(key, l, bg_bit);
  MAT_TRGSW_DFT selector = mat_trgsw_alloc_new_DFT_sample(l, bg_bit, k, r, N);
  PVW_TMLWE in = pvmtmlwe_new_sample(NULL, key);
  PVW_TMLWE_DFT out = pvmtmlwe_alloc_new_DFT_sample(k, r, N);
  MAT_TRGSW_MUL_SCRATCH scratch = mat_trgsw_alloc_mul_scratch(rows, N);

  mat_trgsw_monomial_DFT_sample(selector, 1, 0, mat_key);
  for (size_t i = 0; i < 10; i++){
    mat_trgsw_mul_pvmtmlwe_DFT(out, in, selector, scratch);
  }

  uint64_t total_us = 0;
  for (size_t i = 0; i < reps; i++){
    const uint64_t start = get_time();
    mat_trgsw_mul_pvmtmlwe_DFT(out, in, selector, scratch);
    total_us += get_time() - start;
  }
  printf("MAT_TRGSW microbench r=%d reps=%" PRIu64 " avg_us=%" PRIu64 " lane_avg_us=%" PRIu64 "\n",
         r, reps, total_us / reps, total_us / (reps * r));

  free_mat_trgsw_mul_scratch(scratch);
  free_pvmtmlwe_DFT(out);
  free_pvmtmlwe(in);
  free_mat_trgsw_DFT(selector);
  free_mat_trgsw_key(mat_key);
  free_pvmtmlwe_key(key);
}

static void bench_mat_trgsw_vs_scalar_lane(int r){
  const int N = 2048, k = 1, l = 1, bg_bit = 23;
  const int rows = (k + r) * l;
  const uint64_t reps = 1000;

  PVW_TMLWE_Key pvw_key = pvmtmlwe_new_binary_key(N, k, r, pow(2, -50));
  MAT_TRGSW_Key mat_key = mat_trgsw_new_key(pvw_key, l, bg_bit);
  MAT_TRGSW_DFT mat_selector = mat_trgsw_alloc_new_DFT_sample(l, bg_bit, k, r, N);
  PVW_TMLWE pvw_in = pvmtmlwe_new_sample(NULL, pvw_key);
  PVW_TMLWE_DFT mat_out = pvmtmlwe_alloc_new_DFT_sample(k, r, N);
  MAT_TRGSW_MUL_SCRATCH scratch = mat_trgsw_alloc_mul_scratch(rows, N);

  TRLWE_Key * scalar_keys = (TRLWE_Key *) safe_malloc(sizeof(TRLWE_Key) * r);
  TRGSW_Key * scalar_trgsw_keys = (TRGSW_Key *) safe_malloc(sizeof(TRGSW_Key) * r);
  TRGSW_DFT * scalar_selectors = (TRGSW_DFT *) safe_malloc(sizeof(TRGSW_DFT) * r);
  TRLWE * scalar_in = (TRLWE *) safe_malloc(sizeof(TRLWE) * r);
  TRLWE_DFT * scalar_out = (TRLWE_DFT *) safe_malloc(sizeof(TRLWE_DFT) * r);

  mat_trgsw_monomial_DFT_sample(mat_selector, 1, 0, mat_key);
  for (size_t lane = 0; lane < (size_t) r; lane++){
    scalar_keys[lane] = trlwe_key_from_pvmtmlwe_lane(pvw_key, lane);
    scalar_trgsw_keys[lane] = trgsw_new_key(scalar_keys[lane], l, bg_bit);
    scalar_selectors[lane] = trgsw_alloc_new_DFT_sample(l, bg_bit, k, N);
    trgsw_monomial_DFT_sample(scalar_selectors[lane], 1, 0, scalar_trgsw_keys[lane]);
    scalar_in[lane] = trlwe_alloc_new_sample(k, N);
    scalar_out[lane] = trlwe_alloc_new_DFT_sample(k, N);
    polynomial_copy_torus_polynomial(scalar_in[lane]->a[0], pvw_in->a[0]);
    polynomial_copy_torus_polynomial(scalar_in[lane]->b, pvw_in->b[lane]);
  }

  for (size_t i = 0; i < 10; i++){
    for (size_t lane = 0; lane < (size_t) r; lane++){
      trgsw_mul_trlwe_DFT(scalar_out[lane], scalar_in[lane], scalar_selectors[lane]);
    }
    mat_trgsw_mul_pvmtmlwe_DFT(mat_out, pvw_in, mat_selector, scratch);
  }

  uint64_t scalar_total_us = 0;
  for (size_t i = 0; i < reps; i++){
    const uint64_t start = get_time();
    for (size_t lane = 0; lane < (size_t) r; lane++){
      trgsw_mul_trlwe_DFT(scalar_out[lane], scalar_in[lane], scalar_selectors[lane]);
    }
    scalar_total_us += get_time() - start;
  }

  uint64_t mat_total_us = 0;
  for (size_t i = 0; i < reps; i++){
    const uint64_t start = get_time();
    mat_trgsw_mul_pvmtmlwe_DFT(mat_out, pvw_in, mat_selector, scratch);
    mat_total_us += get_time() - start;
  }

  const double scalar_avg_us = ((double) scalar_total_us) / ((double) reps);
  const double scalar_lane_avg_us = scalar_avg_us / ((double) r);
  const double mat_avg_us = ((double) mat_total_us) / ((double) reps);
  const double mat_lane_avg_us = mat_avg_us / ((double) r);
  const double speedup = mat_total_us == 0 ? 0.0 : ((double) scalar_total_us) / ((double) mat_total_us);

  printf("MAT_TRGSW vs scalar r=%d reps=%" PRIu64
         " scalar_repeated_avg_us=%.3f scalar_lane_avg_us=%.3f"
         " mat_avg_us=%.3f mat_lane_avg_us=%.3f speedup_vs_scalar_repeated=%.3fx\n",
         r, reps, scalar_avg_us, scalar_lane_avg_us, mat_avg_us, mat_lane_avg_us, speedup);

  for (size_t lane = 0; lane < (size_t) r; lane++){
    free_trlwe(scalar_out[lane]);
    free_trlwe(scalar_in[lane]);
    free_trgsw(scalar_selectors[lane]);
    free_trgsw_key(scalar_trgsw_keys[lane]);
    free_trlwe_key(scalar_keys[lane]);
  }
  free(scalar_out);
  free(scalar_in);
  free(scalar_selectors);
  free(scalar_trgsw_keys);
  free(scalar_keys);
  free_mat_trgsw_mul_scratch(scratch);
  free_pvmtmlwe_DFT(mat_out);
  free_pvmtmlwe(pvw_in);
  free_mat_trgsw_DFT(mat_selector);
  free_mat_trgsw_key(mat_key);
  free_pvmtmlwe_key(pvw_key);
}

static void bench_mat_trgsw_vs_scalar_lane_full(int r){
  const int N = 2048, k = 1, l = 1, bg_bit = 23;
  const int rows = (k + r) * l;
  const uint64_t reps = 1000;

  PVW_TMLWE_Key pvw_key = pvmtmlwe_new_binary_key(N, k, r, pow(2, -50));
  MAT_TRGSW_Key mat_key = mat_trgsw_new_key(pvw_key, l, bg_bit);
  MAT_TRGSW_DFT mat_selector = mat_trgsw_alloc_new_DFT_sample(l, bg_bit, k, r, N);
  PVW_TMLWE pvw_in = pvmtmlwe_new_sample(NULL, pvw_key);
  PVW_TMLWE_DFT mat_out_dft = pvmtmlwe_alloc_new_DFT_sample(k, r, N);
  PVW_TMLWE mat_out = pvmtmlwe_alloc_new_sample(k, r, N);
  MAT_TRGSW_MUL_SCRATCH scratch = mat_trgsw_alloc_mul_scratch(rows, N);

  TRLWE_Key * scalar_keys = (TRLWE_Key *) safe_malloc(sizeof(TRLWE_Key) * r);
  TRGSW_Key * scalar_trgsw_keys = (TRGSW_Key *) safe_malloc(sizeof(TRGSW_Key) * r);
  TRGSW_DFT * scalar_selectors = (TRGSW_DFT *) safe_malloc(sizeof(TRGSW_DFT) * r);
  TRLWE * scalar_in = (TRLWE *) safe_malloc(sizeof(TRLWE) * r);
  TRLWE_DFT * scalar_out_dft = (TRLWE_DFT *) safe_malloc(sizeof(TRLWE_DFT) * r);
  TRLWE * scalar_out = (TRLWE *) safe_malloc(sizeof(TRLWE) * r);

  mat_trgsw_monomial_DFT_sample(mat_selector, 1, 0, mat_key);
  for (size_t lane = 0; lane < (size_t) r; lane++){
    scalar_keys[lane] = trlwe_key_from_pvmtmlwe_lane(pvw_key, lane);
    scalar_trgsw_keys[lane] = trgsw_new_key(scalar_keys[lane], l, bg_bit);
    scalar_selectors[lane] = trgsw_alloc_new_DFT_sample(l, bg_bit, k, N);
    trgsw_monomial_DFT_sample(scalar_selectors[lane], 1, 0, scalar_trgsw_keys[lane]);
    scalar_in[lane] = trlwe_alloc_new_sample(k, N);
    scalar_out_dft[lane] = trlwe_alloc_new_DFT_sample(k, N);
    scalar_out[lane] = trlwe_alloc_new_sample(k, N);
    polynomial_copy_torus_polynomial(scalar_in[lane]->a[0], pvw_in->a[0]);
    polynomial_copy_torus_polynomial(scalar_in[lane]->b, pvw_in->b[lane]);
  }

  for (size_t i = 0; i < 10; i++){
    for (size_t lane = 0; lane < (size_t) r; lane++){
      trgsw_mul_trlwe_DFT(scalar_out_dft[lane], scalar_in[lane], scalar_selectors[lane]);
      trlwe_from_DFT(scalar_out[lane], scalar_out_dft[lane]);
    }
    mat_trgsw_mul_pvmtmlwe_DFT(mat_out_dft, pvw_in, mat_selector, scratch);
    pvmtmlwe_from_DFT(mat_out, mat_out_dft);
  }

  uint64_t scalar_total_us = 0;
  for (size_t i = 0; i < reps; i++){
    const uint64_t start = get_time();
    for (size_t lane = 0; lane < (size_t) r; lane++){
      trgsw_mul_trlwe_DFT(scalar_out_dft[lane], scalar_in[lane], scalar_selectors[lane]);
      trlwe_from_DFT(scalar_out[lane], scalar_out_dft[lane]);
    }
    scalar_total_us += get_time() - start;
  }

  uint64_t mat_total_us = 0;
  for (size_t i = 0; i < reps; i++){
    const uint64_t start = get_time();
    mat_trgsw_mul_pvmtmlwe_DFT(mat_out_dft, pvw_in, mat_selector, scratch);
    pvmtmlwe_from_DFT(mat_out, mat_out_dft);
    mat_total_us += get_time() - start;
  }

  const double scalar_avg_us = ((double) scalar_total_us) / ((double) reps);
  const double scalar_lane_avg_us = scalar_avg_us / ((double) r);
  const double mat_avg_us = ((double) mat_total_us) / ((double) reps);
  const double mat_lane_avg_us = mat_avg_us / ((double) r);
  const double speedup = mat_total_us == 0 ? 0.0 : ((double) scalar_total_us) / ((double) mat_total_us);

  printf("MAT_TRGSW_FULL vs scalar_full r=%d reps=%" PRIu64
         " scalar_repeated_avg_us=%.3f scalar_lane_avg_us=%.3f"
         " mat_avg_us=%.3f mat_lane_avg_us=%.3f speedup_vs_scalar_repeated=%.3fx\n",
         r, reps, scalar_avg_us, scalar_lane_avg_us, mat_avg_us, mat_lane_avg_us, speedup);

  for (size_t lane = 0; lane < (size_t) r; lane++){
    free_trlwe(scalar_out[lane]);
    free_trlwe(scalar_out_dft[lane]);
    free_trlwe(scalar_in[lane]);
    free_trgsw(scalar_selectors[lane]);
    free_trgsw_key(scalar_trgsw_keys[lane]);
    free_trlwe_key(scalar_keys[lane]);
  }
  free(scalar_out);
  free(scalar_out_dft);
  free(scalar_in);
  free(scalar_selectors);
  free(scalar_trgsw_keys);
  free(scalar_keys);
  free_mat_trgsw_mul_scratch(scratch);
  free_pvmtmlwe(mat_out);
  free_pvmtmlwe_DFT(mat_out_dft);
  free_pvmtmlwe(pvw_in);
  free_mat_trgsw_DFT(mat_selector);
  free_mat_trgsw_key(mat_key);
  free_pvmtmlwe_key(pvw_key);
}

typedef struct {
  uint64_t alloc_us;
  uint64_t decompose_us;
  uint64_t dft_us;
  uint64_t clear_us;
  uint64_t mul_us;
  uint64_t free_us;
} ExternalProductPhases;

static void print_external_product_phases(const char * label, int r, uint64_t reps, ExternalProductPhases phases){
  const uint64_t phase_sum = phases.alloc_us + phases.decompose_us + phases.dft_us +
      phases.clear_us + phases.mul_us + phases.free_us;
  const double denom = phase_sum == 0 ? 1.0 : (double) phase_sum;
  printf("EP_BREAKDOWN %s r=%d reps=%" PRIu64 " phase_sum_avg_us=%.3f"
         " alloc_avg_us=%.3f alloc_pct=%.2f"
         " decompose_avg_us=%.3f decompose_pct=%.2f"
         " dft_avg_us=%.3f dft_pct=%.2f"
         " clear_avg_us=%.3f clear_pct=%.2f"
         " mul_avg_us=%.3f mul_pct=%.2f"
         " free_avg_us=%.3f free_pct=%.2f\n",
         label, r, reps, ((double) phase_sum) / ((double) reps),
         ((double) phases.alloc_us) / ((double) reps), 100.0 * ((double) phases.alloc_us) / denom,
         ((double) phases.decompose_us) / ((double) reps), 100.0 * ((double) phases.decompose_us) / denom,
         ((double) phases.dft_us) / ((double) reps), 100.0 * ((double) phases.dft_us) / denom,
         ((double) phases.clear_us) / ((double) reps), 100.0 * ((double) phases.clear_us) / denom,
         ((double) phases.mul_us) / ((double) reps), 100.0 * ((double) phases.mul_us) / denom,
         ((double) phases.free_us) / ((double) reps), 100.0 * ((double) phases.free_us) / denom);
}

static void bench_external_product_phase_breakdown(int r){
  const int N = 2048, k = 1, l = 1, bg_bit = 23;
  const int scalar_rows = (k + 1) * l;
  const int mat_rows = (k + r) * l;
  const uint64_t reps = 1000;

  PVW_TMLWE_Key pvw_key = pvmtmlwe_new_binary_key(N, k, r, pow(2, -50));
  MAT_TRGSW_Key mat_key = mat_trgsw_new_key(pvw_key, l, bg_bit);
  MAT_TRGSW_DFT mat_selector = mat_trgsw_alloc_new_DFT_sample(l, bg_bit, k, r, N);
  PVW_TMLWE pvw_in = pvmtmlwe_new_sample(NULL, pvw_key);
  PVW_TMLWE_DFT mat_out = pvmtmlwe_alloc_new_DFT_sample(k, r, N);
  MAT_TRGSW_MUL_SCRATCH scratch = mat_trgsw_alloc_mul_scratch(mat_rows, N);

  TRLWE_Key * scalar_keys = (TRLWE_Key *) safe_malloc(sizeof(TRLWE_Key) * r);
  TRGSW_Key * scalar_trgsw_keys = (TRGSW_Key *) safe_malloc(sizeof(TRGSW_Key) * r);
  TRGSW_DFT * scalar_selectors = (TRGSW_DFT *) safe_malloc(sizeof(TRGSW_DFT) * r);
  TRLWE * scalar_in = (TRLWE *) safe_malloc(sizeof(TRLWE) * r);
  TRLWE_DFT * scalar_out = (TRLWE_DFT *) safe_malloc(sizeof(TRLWE_DFT) * r);

  mat_trgsw_monomial_DFT_sample(mat_selector, 1, 0, mat_key);
  for (size_t lane = 0; lane < (size_t) r; lane++){
    scalar_keys[lane] = trlwe_key_from_pvmtmlwe_lane(pvw_key, lane);
    scalar_trgsw_keys[lane] = trgsw_new_key(scalar_keys[lane], l, bg_bit);
    scalar_selectors[lane] = trgsw_alloc_new_DFT_sample(l, bg_bit, k, N);
    trgsw_monomial_DFT_sample(scalar_selectors[lane], 1, 0, scalar_trgsw_keys[lane]);
    scalar_in[lane] = trlwe_alloc_new_sample(k, N);
    scalar_out[lane] = trlwe_alloc_new_DFT_sample(k, N);
    polynomial_copy_torus_polynomial(scalar_in[lane]->a[0], pvw_in->a[0]);
    polynomial_copy_torus_polynomial(scalar_in[lane]->b, pvw_in->b[lane]);
  }

  ExternalProductPhases scalar_phases = {0, 0, 0, 0, 0, 0};
  ExternalProductPhases mat_phases = {0, 0, 0, 0, 0, 0};

  TorusPolynomial ** scalar_dec = (TorusPolynomial **) safe_malloc(sizeof(TorusPolynomial *) * r);
  DFT_Polynomial ** scalar_dec_dft = (DFT_Polynomial **) safe_malloc(sizeof(DFT_Polynomial *) * r);
  for (size_t lane = 0; lane < (size_t) r; lane++){
    scalar_dec[lane] = polynomial_new_array_of_torus_polynomials(N, scalar_rows);
    scalar_dec_dft[lane] = polynomial_new_array_of_polynomials_DFT(N, scalar_rows);
  }

  for (size_t rep = 0; rep < reps; rep++){
    uint64_t start = get_time();
    for (size_t lane = 0; lane < (size_t) r; lane++){
      for (size_t level = 0; level < (size_t) l; level++){
        polynomial_decompose_i(scalar_dec[lane][level], scalar_in[lane]->a[0], bg_bit, l, level);
        polynomial_decompose_i(scalar_dec[lane][l + level], scalar_in[lane]->b, bg_bit, l, level);
      }
    }
    scalar_phases.decompose_us += get_time() - start;

    start = get_time();
    for (size_t lane = 0; lane < (size_t) r; lane++){
      for (size_t row = 0; row < (size_t) scalar_rows; row++){
        polynomial_torus_to_DFT(scalar_dec_dft[lane][row], scalar_dec[lane][row]);
      }
    }
    scalar_phases.dft_us += get_time() - start;

    start = get_time();
    for (size_t lane = 0; lane < (size_t) r; lane++){
      polynomial_mul_DFT(scalar_out[lane]->a[0], scalar_dec_dft[lane][0], scalar_selectors[lane]->samples[0]->a[0]);
      polynomial_mul_DFT(scalar_out[lane]->b, scalar_dec_dft[lane][0], scalar_selectors[lane]->samples[0]->b);
      for (size_t row = 1; row < (size_t) scalar_rows; row++){
        polynomial_mul_addto_DFT(scalar_out[lane]->a[0], scalar_dec_dft[lane][row], scalar_selectors[lane]->samples[row]->a[0]);
        polynomial_mul_addto_DFT(scalar_out[lane]->b, scalar_dec_dft[lane][row], scalar_selectors[lane]->samples[row]->b);
      }
    }
    scalar_phases.mul_us += get_time() - start;

    start = get_time();
    pvmtmlwe_decompose(scratch->dec, pvw_in, bg_bit, l);
    mat_phases.decompose_us += get_time() - start;

    start = get_time();
    for (size_t row = 0; row < (size_t) mat_rows; row++){
      polynomial_torus_to_DFT(scratch->dec_dft[row], scratch->dec[row]);
    }
    mat_phases.dft_us += get_time() - start;

    start = get_time();
    for (size_t j = 0; j < (size_t) k; j++){
      polynomial_mul_DFT(mat_out->a[j], scratch->dec_dft[0], mat_selector->samples[0]->a[j]);
    }
    for (size_t lane = 0; lane < (size_t) r; lane++){
      polynomial_mul_DFT(mat_out->b[lane], scratch->dec_dft[0], mat_selector->samples[0]->b[lane]);
    }
    for (size_t row = 1; row < (size_t) mat_rows; row++){
      for (size_t j = 0; j < (size_t) k; j++){
        polynomial_mul_addto_DFT(mat_out->a[j], scratch->dec_dft[row], mat_selector->samples[row]->a[j]);
      }
      for (size_t lane = 0; lane < (size_t) r; lane++){
        polynomial_mul_addto_DFT(mat_out->b[lane], scratch->dec_dft[row], mat_selector->samples[row]->b[lane]);
      }
    }
    mat_phases.mul_us += get_time() - start;
  }

  print_external_product_phases("scalar_repeated", r, reps, scalar_phases);
  print_external_product_phases("mat_shared_mask", r, reps, mat_phases);

  for (size_t lane = 0; lane < (size_t) r; lane++){
    free_array_of_polynomials((void **) scalar_dec[lane], scalar_rows);
    free_array_of_polynomials((void **) scalar_dec_dft[lane], scalar_rows);
  }
  free(scalar_dec_dft);
  free(scalar_dec);

  for (size_t lane = 0; lane < (size_t) r; lane++){
    free_trlwe(scalar_out[lane]);
    free_trlwe(scalar_in[lane]);
    free_trgsw(scalar_selectors[lane]);
    free_trgsw_key(scalar_trgsw_keys[lane]);
    free_trlwe_key(scalar_keys[lane]);
  }
  free(scalar_out);
  free(scalar_in);
  free(scalar_selectors);
  free(scalar_trgsw_keys);
  free(scalar_keys);
  free_mat_trgsw_mul_scratch(scratch);
  free_pvmtmlwe_DFT(mat_out);
  free_pvmtmlwe(pvw_in);
  free_mat_trgsw_DFT(mat_selector);
  free_mat_trgsw_key(mat_key);
  free_pvmtmlwe_key(pvw_key);
}

static void copy_pvw_lane_to_trlwe(TRLWE out, PVW_TMLWE in, int lane){
  for (size_t i = 0; i < (size_t) in->k; i++){
    polynomial_copy_torus_polynomial(out->a[i], in->a[i]);
  }
  polynomial_copy_torus_polynomial(out->b, in->b[lane]);
}

static void trlwe_raw_automorphism(TRLWE out, TRLWE in, uint64_t gen){
  for (size_t i = 0; i < (size_t) in->k; i++){
    polynomial_permute(out->a[i], in->a[i], gen);
  }
  polynomial_permute(out->b, in->b, gen);
}

static void pvmtmlwe_raw_automorphism(PVW_TMLWE out, PVW_TMLWE in, uint64_t gen){
  for (size_t i = 0; i < (size_t) in->k; i++){
    polynomial_permute(out->a[i], in->a[i], gen);
  }
  for (size_t lane = 0; lane < (size_t) in->r; lane++){
    polynomial_permute(out->b[lane], in->b[lane], gen);
  }
}

static void isolated_scalar_CMUX(TRLWE out, TRLWE in1, TRLWE in2,
    TRGSW_DFT selector, TRLWE tmp, TRLWE_DFT tmp_dft){
  trlwe_sub(tmp, in2, in1);
  trgsw_mul_trlwe_DFT(tmp_dft, tmp, selector);
  trlwe_from_DFT(tmp, tmp_dft);
  trlwe_add(out, tmp, in1);
}

static void isolated_pvw_CMUX(PVW_TMLWE out, PVW_TMLWE in1, PVW_TMLWE in2,
    MAT_TRGSW_DFT selector, MAT_TRGSW_MUL_SCRATCH scratch,
    PVW_TMLWE tmp, PVW_TMLWE_DFT tmp_dft){
  pvmtmlwe_sub(tmp, in2, in1);
  mat_trgsw_mul_pvmtmlwe_DFT(tmp_dft, tmp, selector, scratch);
  pvmtmlwe_from_DFT(tmp, tmp_dft);
  pvmtmlwe_add(out, tmp, in1);
}

static void isolated_scalar_NCMUX_raw(TRLWE out, TRLWE in1, TRLWE in2,
    TRGSW_DFT selector, TRLWE rotated, TRLWE tmp, TRLWE_DFT tmp_dft){
  const uint64_t gen = 2 * in2->b->N - 1;
  trlwe_raw_automorphism(rotated, in2, gen);
  isolated_scalar_CMUX(out, in1, rotated, selector, tmp, tmp_dft);
}

static void isolated_pvw_NCMUX_raw(PVW_TMLWE out, PVW_TMLWE in1, PVW_TMLWE in2,
    MAT_TRGSW_DFT selector, MAT_TRGSW_MUL_SCRATCH scratch,
    PVW_TMLWE rotated, PVW_TMLWE tmp, PVW_TMLWE_DFT tmp_dft){
  const uint64_t gen = 2 * in2->b[0]->N - 1;
  pvmtmlwe_raw_automorphism(rotated, in2, gen);
  isolated_pvw_CMUX(out, in1, rotated, selector, scratch, tmp, tmp_dft);
}

static void isolated_scalar_NCMUX_auto(TRLWE out, TRLWE in1, TRLWE in2,
    TRGSW_DFT selector, TRLWE_KS_Key aut_minus1,
    TRLWE rotated, TRLWE tmp, TRLWE_DFT tmp_dft){
  const uint64_t gen = 2 * in2->b->N - 1;
  trlwe_eval_automorphism(rotated, in2, gen, aut_minus1);
  isolated_scalar_CMUX(out, in1, rotated, selector, tmp, tmp_dft);
}

static void isolated_pvw_NCMUX_auto(PVW_TMLWE out, PVW_TMLWE in1, PVW_TMLWE in2,
    MAT_TRGSW_DFT selector, MAT_TRGSW_MUL_SCRATCH scratch,
    PVW_TMLWE_KS_Key aut_minus1, PVW_TMLWE rotated,
    PVW_TMLWE tmp, PVW_TMLWE_DFT tmp_dft){
  const uint64_t gen = 2 * in2->b[0]->N - 1;
  pvmtmlwe_eval_automorphism(rotated, in2, gen, aut_minus1);
  isolated_pvw_CMUX(out, in1, rotated, selector, scratch, tmp, tmp_dft);
}

static bool compare_pvw_scalar_lane_phases(const char * label, int r, int prec,
    PVW_TMLWE pvw_out, PVW_TMLWE_Key pvw_key,
    TRLWE * scalar_out, TRLWE_Key * scalar_keys){
  const int N = pvw_out->b[0]->N;
  TorusPolynomial * pvw_phase = polynomial_new_array_of_torus_polynomials(N, r);
  TorusPolynomial scalar_phase = polynomial_new_torus_polynomial(N);
  bool pass = true;

  pvmtmlwe_phase(pvw_phase, pvw_out, pvw_key);
  for (size_t lane = 0; lane < (size_t) r; lane++){
    trlwe_phase(scalar_phase, scalar_out[lane], scalar_keys[lane]);
    for (size_t i = 0; i < (size_t) N; i++){
      const uint64_t pvw_val = torus2int(pvw_phase[lane]->coeffs[i], prec);
      const uint64_t scalar_val = torus2int(scalar_phase->coeffs[i], prec);
      if(pvw_val != scalar_val){
        printf("SAB_PVW %s phase fail r=%d lane=%" PRIu64 " coeff=%" PRIu64
               ": %" PRIu64 " != %" PRIu64 "\n",
               label, r, (uint64_t) lane, (uint64_t) i, pvw_val, scalar_val);
        pass = false;
        break;
      }
    }
    if(!pass) break;
  }

  free_polynomial(scalar_phase);
  free_array_of_polynomials(pvw_phase, r);
  return pass;
}

static bool check_pvw_cmux_ncmux_lane_equivalence(int r){
  const int N = 1024, k = 1, l = 1, bg_bit = 23, prec = 3;
  const int rows = (k + r) * l;
  bool pass = true;

  PVW_TMLWE_Key pvw_key = pvmtmlwe_new_binary_key(N, k, r, pow(2, -50));
  MAT_TRGSW_Key mat_key = mat_trgsw_new_key(pvw_key, l, bg_bit);
  MAT_TRGSW_DFT mat_selector_zero = mat_trgsw_alloc_new_DFT_sample(l, bg_bit, k, r, N);
  MAT_TRGSW_DFT mat_selector_one = mat_trgsw_alloc_new_DFT_sample(l, bg_bit, k, r, N);
  MAT_TRGSW_MUL_SCRATCH scratch = mat_trgsw_alloc_mul_scratch(rows, N);

  TRLWE_Key * scalar_keys = (TRLWE_Key *) safe_malloc(sizeof(TRLWE_Key) * r);
  TRGSW_Key * scalar_trgsw_keys = (TRGSW_Key *) safe_malloc(sizeof(TRGSW_Key) * r);
  TRGSW_DFT * scalar_selector_zero = (TRGSW_DFT *) safe_malloc(sizeof(TRGSW_DFT) * r);
  TRGSW_DFT * scalar_selector_one = (TRGSW_DFT *) safe_malloc(sizeof(TRGSW_DFT) * r);
  TRLWE * scalar_in1 = (TRLWE *) safe_malloc(sizeof(TRLWE) * r);
  TRLWE * scalar_in2 = (TRLWE *) safe_malloc(sizeof(TRLWE) * r);
  TRLWE * scalar_trivial_in1 = (TRLWE *) safe_malloc(sizeof(TRLWE) * r);
  TRLWE * scalar_trivial_in2 = (TRLWE *) safe_malloc(sizeof(TRLWE) * r);
  TRLWE * scalar_out = (TRLWE *) safe_malloc(sizeof(TRLWE) * r);
  TRLWE * scalar_tmp = (TRLWE *) safe_malloc(sizeof(TRLWE) * r);
  TRLWE * scalar_rotated = (TRLWE *) safe_malloc(sizeof(TRLWE) * r);
  TRLWE_DFT * scalar_tmp_dft = (TRLWE_DFT *) safe_malloc(sizeof(TRLWE_DFT) * r);

  TorusPolynomial * msg_in1 = polynomial_new_array_of_torus_polynomials(N, r);
  TorusPolynomial * msg_in2 = polynomial_new_array_of_torus_polynomials(N, r);
  for (size_t lane = 0; lane < (size_t) r; lane++){
    for (size_t i = 0; i < (size_t) N; i++){
      msg_in1[lane]->coeffs[i] = int2torus((i + lane) & 7, prec);
      msg_in2[lane]->coeffs[i] = int2torus((3 * i + 2 * lane + 1) & 7, prec);
    }
  }

  mat_trgsw_monomial_DFT_sample(mat_selector_zero, 0, 0, mat_key);
  mat_trgsw_monomial_DFT_sample(mat_selector_one, 1, 0, mat_key);

  PVW_TMLWE pvw_in1 = pvmtmlwe_new_sample(msg_in1, pvw_key);
  PVW_TMLWE pvw_in2 = pvmtmlwe_new_sample(msg_in2, pvw_key);
  PVW_TMLWE pvw_trivial_in1 = pvmtmlwe_new_noiseless_trivial_sample(msg_in1, k, r, N);
  PVW_TMLWE pvw_trivial_in2 = pvmtmlwe_new_noiseless_trivial_sample(msg_in2, k, r, N);
  PVW_TMLWE pvw_out = pvmtmlwe_alloc_new_sample(k, r, N);
  PVW_TMLWE pvw_tmp = pvmtmlwe_alloc_new_sample(k, r, N);
  PVW_TMLWE pvw_rotated = pvmtmlwe_alloc_new_sample(k, r, N);
  PVW_TMLWE_DFT pvw_tmp_dft = pvmtmlwe_alloc_new_DFT_sample(k, r, N);

  for (size_t lane = 0; lane < (size_t) r; lane++){
    scalar_keys[lane] = trlwe_key_from_pvmtmlwe_lane(pvw_key, lane);
    scalar_trgsw_keys[lane] = trgsw_new_key(scalar_keys[lane], l, bg_bit);
    scalar_selector_zero[lane] = trgsw_alloc_new_DFT_sample(l, bg_bit, k, N);
    scalar_selector_one[lane] = trgsw_alloc_new_DFT_sample(l, bg_bit, k, N);
    trgsw_monomial_DFT_sample(scalar_selector_zero[lane], 0, 0, scalar_trgsw_keys[lane]);
    trgsw_monomial_DFT_sample(scalar_selector_one[lane], 1, 0, scalar_trgsw_keys[lane]);

    scalar_in1[lane] = trlwe_alloc_new_sample(k, N);
    scalar_in2[lane] = trlwe_alloc_new_sample(k, N);
    scalar_trivial_in1[lane] = trlwe_alloc_new_sample(k, N);
    scalar_trivial_in2[lane] = trlwe_alloc_new_sample(k, N);
    scalar_out[lane] = trlwe_alloc_new_sample(k, N);
    scalar_tmp[lane] = trlwe_alloc_new_sample(k, N);
    scalar_rotated[lane] = trlwe_alloc_new_sample(k, N);
    scalar_tmp_dft[lane] = trlwe_alloc_new_DFT_sample(k, N);

    copy_pvw_lane_to_trlwe(scalar_in1[lane], pvw_in1, lane);
    copy_pvw_lane_to_trlwe(scalar_in2[lane], pvw_in2, lane);
    copy_pvw_lane_to_trlwe(scalar_trivial_in1[lane], pvw_trivial_in1, lane);
    copy_pvw_lane_to_trlwe(scalar_trivial_in2[lane], pvw_trivial_in2, lane);
  }

  isolated_pvw_CMUX(pvw_out, pvw_in1, pvw_in2, mat_selector_zero, scratch, pvw_tmp, pvw_tmp_dft);
  for (size_t lane = 0; lane < (size_t) r; lane++){
    isolated_scalar_CMUX(scalar_out[lane], scalar_in1[lane], scalar_in2[lane],
        scalar_selector_zero[lane], scalar_tmp[lane], scalar_tmp_dft[lane]);
  }
  pass &= compare_pvw_scalar_lane_phases("CMUX selector=0", r, prec, pvw_out, pvw_key, scalar_out, scalar_keys);

  isolated_pvw_CMUX(pvw_out, pvw_in1, pvw_in2, mat_selector_one, scratch, pvw_tmp, pvw_tmp_dft);
  for (size_t lane = 0; lane < (size_t) r; lane++){
    isolated_scalar_CMUX(scalar_out[lane], scalar_in1[lane], scalar_in2[lane],
        scalar_selector_one[lane], scalar_tmp[lane], scalar_tmp_dft[lane]);
  }
  pass &= compare_pvw_scalar_lane_phases("CMUX selector=1", r, prec, pvw_out, pvw_key, scalar_out, scalar_keys);

  isolated_pvw_NCMUX_raw(pvw_out, pvw_trivial_in1, pvw_trivial_in2,
      mat_selector_zero, scratch, pvw_rotated, pvw_tmp, pvw_tmp_dft);
  for (size_t lane = 0; lane < (size_t) r; lane++){
    isolated_scalar_NCMUX_raw(scalar_out[lane], scalar_trivial_in1[lane], scalar_trivial_in2[lane],
        scalar_selector_zero[lane], scalar_rotated[lane], scalar_tmp[lane], scalar_tmp_dft[lane]);
  }
  pass &= compare_pvw_scalar_lane_phases("NCMUX raw selector=0", r, prec, pvw_out, pvw_key, scalar_out, scalar_keys);

  isolated_pvw_NCMUX_raw(pvw_out, pvw_trivial_in1, pvw_trivial_in2,
      mat_selector_one, scratch, pvw_rotated, pvw_tmp, pvw_tmp_dft);
  for (size_t lane = 0; lane < (size_t) r; lane++){
    isolated_scalar_NCMUX_raw(scalar_out[lane], scalar_trivial_in1[lane], scalar_trivial_in2[lane],
        scalar_selector_one[lane], scalar_rotated[lane], scalar_tmp[lane], scalar_tmp_dft[lane]);
  }
  pass &= compare_pvw_scalar_lane_phases("NCMUX raw selector=1", r, prec, pvw_out, pvw_key, scalar_out, scalar_keys);

  for (size_t lane = 0; lane < (size_t) r; lane++){
    free_trlwe(scalar_tmp_dft[lane]);
    free_trlwe(scalar_rotated[lane]);
    free_trlwe(scalar_tmp[lane]);
    free_trlwe(scalar_out[lane]);
    free_trlwe(scalar_trivial_in2[lane]);
    free_trlwe(scalar_trivial_in1[lane]);
    free_trlwe(scalar_in2[lane]);
    free_trlwe(scalar_in1[lane]);
    free_trgsw(scalar_selector_one[lane]);
    free_trgsw(scalar_selector_zero[lane]);
    free_trgsw_key(scalar_trgsw_keys[lane]);
    free_trlwe_key(scalar_keys[lane]);
  }

  free(scalar_tmp_dft);
  free(scalar_rotated);
  free(scalar_tmp);
  free(scalar_out);
  free(scalar_trivial_in2);
  free(scalar_trivial_in1);
  free(scalar_in2);
  free(scalar_in1);
  free(scalar_selector_one);
  free(scalar_selector_zero);
  free(scalar_trgsw_keys);
  free(scalar_keys);
  free_pvmtmlwe_DFT(pvw_tmp_dft);
  free_pvmtmlwe(pvw_rotated);
  free_pvmtmlwe(pvw_tmp);
  free_pvmtmlwe(pvw_out);
  free_pvmtmlwe(pvw_trivial_in2);
  free_pvmtmlwe(pvw_trivial_in1);
  free_pvmtmlwe(pvw_in2);
  free_pvmtmlwe(pvw_in1);
  free_array_of_polynomials(msg_in2, r);
  free_array_of_polynomials(msg_in1, r);
  free_mat_trgsw_mul_scratch(scratch);
  free_mat_trgsw_DFT(mat_selector_one);
  free_mat_trgsw_DFT(mat_selector_zero);
  free_mat_trgsw_key(mat_key);
  free_pvmtmlwe_key(pvw_key);

  printf("SAB_PVW isolated CMUX/NCMUX lane equivalence r=%d: %s\n", r, pass ? "Pass" : "Fail");
  return pass;
}

static PVW_TMLWE * alloc_pvw_sample_array_local(int count, int k, int r, int N){
  PVW_TMLWE * res = (PVW_TMLWE *) safe_malloc(sizeof(PVW_TMLWE) * count);
  for (size_t i = 0; i < (size_t) count; i++){
    res[i] = pvmtmlwe_alloc_new_sample(k, r, N);
  }
  return res;
}

static void free_pvw_sample_array_local(PVW_TMLWE * arr, int count){
  for (size_t i = 0; i < (size_t) count; i++){
    free_pvmtmlwe(arr[i]);
  }
  free(arr);
}

static void mat_trgsw_noiseless_trivial_sample_local(MAT_TRGSW out,
    int64_t m, int e, int l, int bg_bit, int k, int r, int N){
  const int rows = (k + r) * l;
  if(e & N) m *= -1;
  e &= (N - 1);

  for (size_t row = 0; row < (size_t) rows; row++){
    pvmtmlwe_noiseless_trivial_sample(out->samples[row], NULL);
  }
  for (size_t level = 0; level < (size_t) l; level++){
    const Torus h = 1ULL << (sizeof(Torus) * 8 - (level + 1) * bg_bit);
    for (size_t j = 0; j < (size_t) k; j++){
      out->samples[j * l + level]->a[j]->coeffs[e] += m * h;
    }
    for (size_t lane = 0; lane < (size_t) r; lane++){
      out->samples[(k + lane) * l + level]->b[lane]->coeffs[e] += m * h;
    }
  }
}

static void mat_trgsw_noiseless_trivial_DFT_sample_local(MAT_TRGSW_DFT out,
    int64_t m, int e, int l, int bg_bit, int k, int r, int N){
  MAT_TRGSW tmp = mat_trgsw_alloc_new_sample(l, bg_bit, k, r, N);
  mat_trgsw_noiseless_trivial_sample_local(tmp, m, e, l, bg_bit, k, r, N);
  mat_trgsw_to_DFT(out, tmp);
  free_mat_trgsw(tmp);
}

static void trgsw_noiseless_trivial_DFT_sample_local(TRGSW_DFT out,
    int64_t m, int l, int bg_bit, int k, int N){
  TRGSW tmp = trgsw_alloc_new_sample(l, bg_bit, k, N);
  trgsw_noiseless_trivial_sample(tmp, m, l, bg_bit, k, N);
  trgsw_to_DFT(out, tmp);
  free_trgsw(tmp);
}

static bool compare_pvw_scalar_array_phases(const char * label, int r, int count,
    int prec, PVW_TMLWE * pvw_arr, PVW_TMLWE_Key pvw_key,
    TRLWE ** scalar_arr, TRLWE_Key * scalar_keys){
  const int N = pvw_arr[0]->b[0]->N;
  TorusPolynomial * pvw_phase = polynomial_new_array_of_torus_polynomials(N, r);
  TorusPolynomial scalar_phase = polynomial_new_torus_polynomial(N);
  bool pass = true;

  for (size_t idx = 0; idx < (size_t) count; idx++){
    pvmtmlwe_phase(pvw_phase, pvw_arr[idx], pvw_key);
    for (size_t lane = 0; lane < (size_t) r; lane++){
      trlwe_phase(scalar_phase, scalar_arr[lane][idx], scalar_keys[lane]);
      for (size_t coeff = 0; coeff < (size_t) N; coeff++){
        const uint64_t pvw_val = torus2int(pvw_phase[lane]->coeffs[coeff], prec);
        const uint64_t scalar_val = torus2int(scalar_phase->coeffs[coeff], prec);
        if(pvw_val != scalar_val){
          printf("SAB_PVW %s RGSW phase fail idx=%" PRIu64 " r=%d lane=%" PRIu64
                 " coeff=%" PRIu64 ": %" PRIu64 " != %" PRIu64 "\n",
                 label, (uint64_t) idx, r, (uint64_t) lane,
                 (uint64_t) coeff, pvw_val, scalar_val);
          pass = false;
          break;
        }
      }
      if(!pass) break;
    }
    if(!pass) break;
  }

  free_polynomial(scalar_phase);
  free_array_of_polynomials(pvw_phase, r);
  return pass;
}

static bool compare_pvwtlwe_scalar_array_phases(const char * label, int r,
    int count, int prec, PVW_TLWE * pvw_arr, PVW_TLWE_Key pvw_key,
    TLWE ** scalar_arr, TLWE_Key * scalar_keys){
  Torus * pvw_phase = (Torus *) safe_malloc(sizeof(Torus) * r);
  bool pass = true;

  for (size_t idx = 0; idx < (size_t) count; idx++){
    pvwtlwe_phase(pvw_phase, pvw_arr[idx], pvw_key);
    for (size_t lane = 0; lane < (size_t) r; lane++){
      const Torus scalar_phase = tlwe_phase(scalar_arr[lane][idx],
          scalar_keys[lane]);
      const uint64_t pvw_val = torus2int(pvw_phase[lane], prec);
      const uint64_t scalar_val = torus2int(scalar_phase, prec);
      if(pvw_val != scalar_val){
        printf("SAB_PVW %s extracted phase fail idx=%" PRIu64
               " r=%d lane=%" PRIu64 ": %" PRIu64 " != %" PRIu64 "\n",
               label, (uint64_t) idx, r, (uint64_t) lane,
               pvw_val, scalar_val);
        pass = false;
        break;
      }
    }
    if(!pass) break;
  }

  free(pvw_phase);
  return pass;
}

static void copy_pvwtlwe_lane_to_tlwe(TLWE out, PVW_TLWE in, int lane){
  for (size_t idx = 0; idx < (size_t) in->n; idx++){
    out->a[idx] = in->a[idx];
  }
  out->b = in->b[lane];
}

static bool compare_tlwe_scalar_array_phases(const char * label, int r,
    int count, int prec, TLWE ** lhs_arr, TLWE_Key * lhs_keys,
    TLWE ** rhs_arr, TLWE_Key * rhs_keys){
  bool pass = true;

  for (size_t idx = 0; idx < (size_t) count; idx++){
    for (size_t lane = 0; lane < (size_t) r; lane++){
      const Torus lhs_phase = tlwe_phase(lhs_arr[lane][idx],
          lhs_keys[lane]);
      const Torus rhs_phase = tlwe_phase(rhs_arr[lane][idx],
          rhs_keys[lane]);
      const uint64_t lhs_val = torus2int(lhs_phase, prec);
      const uint64_t rhs_val = torus2int(rhs_phase, prec);
      if(lhs_val != rhs_val){
        printf("SAB_PVW %s materialized TLWE phase fail idx=%" PRIu64
               " r=%d lane=%" PRIu64 ": %" PRIu64 " != %" PRIu64 "\n",
               label, (uint64_t) idx, r, (uint64_t) lane,
               lhs_val, rhs_val);
        pass = false;
        break;
      }
    }
    if(!pass) break;
  }

  return pass;
}

static bool compare_trlwe_pair_phases(const char * label, TRLWE lhs,
    TRLWE_Key lhs_key, TRLWE rhs, TRLWE_Key rhs_key, int prec, int lane){
  const int N = lhs->b->N;
  TorusPolynomial lhs_phase = polynomial_new_torus_polynomial(N);
  TorusPolynomial rhs_phase = polynomial_new_torus_polynomial(N);
  bool pass = true;

  trlwe_phase(lhs_phase, lhs, lhs_key);
  trlwe_phase(rhs_phase, rhs, rhs_key);
  for (size_t coeff = 0; coeff < (size_t) N; coeff++){
    const uint64_t lhs_val = torus2int(lhs_phase->coeffs[coeff], prec);
    const uint64_t rhs_val = torus2int(rhs_phase->coeffs[coeff], prec);
    if(lhs_val != rhs_val){
      printf("SAB_PVW %s TRLWE phase fail lane=%d coeff=%" PRIu64
             ": %" PRIu64 " != %" PRIu64 "\n",
             label, lane, (uint64_t) coeff, lhs_val, rhs_val);
      pass = false;
      break;
    }
  }

  free_polynomial(rhs_phase);
  free_polynomial(lhs_phase);
  return pass;
}

static void isolated_pvw_RGSW_monomial_step(PVW_TMLWE * out, PVW_TMLWE * in,
    MAT_TRGSW_DFT selector, int in_N, int power,
    MAT_TRGSW_MUL_SCRATCH scratch, PVW_TMLWE rotated,
    PVW_TMLWE tmp, PVW_TMLWE_DFT tmp_dft){
  for (size_t j = 0; j < (size_t) power; j++){
    isolated_pvw_NCMUX_raw(out[j], in[j], in[in_N - power + j],
        selector, scratch, rotated, tmp, tmp_dft);
  }
  for (size_t j = 0; j < (size_t) (in_N - power); j++){
    isolated_pvw_CMUX(out[j + power], in[j + power], in[j],
        selector, scratch, tmp, tmp_dft);
  }
}

static void isolated_scalar_RGSW_monomial_step(TRLWE * out, TRLWE * in,
    TRGSW_DFT selector, int in_N, int power,
    TRLWE rotated, TRLWE tmp, TRLWE_DFT tmp_dft){
  for (size_t j = 0; j < (size_t) power; j++){
    isolated_scalar_NCMUX_raw(out[j], in[j], in[in_N - power + j],
        selector, rotated, tmp, tmp_dft);
  }
  for (size_t j = 0; j < (size_t) (in_N - power); j++){
    isolated_scalar_CMUX(out[j + power], in[j + power], in[j],
        selector, tmp, tmp_dft);
  }
}

static void isolated_pvw_RGSW_monomial_step_auto(PVW_TMLWE * out, PVW_TMLWE * in,
    MAT_TRGSW_DFT selector, int in_N, int power,
    MAT_TRGSW_MUL_SCRATCH scratch, PVW_TMLWE_KS_Key aut_minus1,
    PVW_TMLWE rotated, PVW_TMLWE tmp, PVW_TMLWE_DFT tmp_dft){
  for (size_t j = 0; j < (size_t) power; j++){
    isolated_pvw_NCMUX_auto(out[j], in[j], in[in_N - power + j],
        selector, scratch, aut_minus1, rotated, tmp, tmp_dft);
  }
  for (size_t j = 0; j < (size_t) (in_N - power); j++){
    isolated_pvw_CMUX(out[j + power], in[j + power], in[j],
        selector, scratch, tmp, tmp_dft);
  }
}

static void isolated_scalar_RGSW_monomial_step_auto(TRLWE * out, TRLWE * in,
    TRGSW_DFT selector, int in_N, int power, TRLWE_KS_Key aut_minus1,
    TRLWE rotated, TRLWE tmp, TRLWE_DFT tmp_dft){
  for (size_t j = 0; j < (size_t) power; j++){
    isolated_scalar_NCMUX_auto(out[j], in[j], in[in_N - power + j],
        selector, aut_minus1, rotated, tmp, tmp_dft);
  }
  for (size_t j = 0; j < (size_t) (in_N - power); j++){
    isolated_scalar_CMUX(out[j + power], in[j + power], in[j],
        selector, tmp, tmp_dft);
  }
}

static bool check_pvw_rgsw_monomial_lane_case(int r, int r_prec,
    const int * selector_bits, bool encrypted_selectors, const char * label){
  const int N = 1024, k = 1, l = 1, bg_bit = 23, prec = 3;
  const int in_N = 1 << r_prec;
  const int rows = (k + r) * l;
  bool pass = true;

  PVW_TMLWE_Key pvw_key = pvmtmlwe_new_binary_key(N, k, r, pow(2, -50));
  MAT_TRGSW_Key mat_key = mat_trgsw_new_key(pvw_key, l, bg_bit);
  MAT_TRGSW_DFT * mat_selectors = (MAT_TRGSW_DFT *) safe_malloc(sizeof(MAT_TRGSW_DFT) * r_prec);
  for (size_t bit = 0; bit < (size_t) r_prec; bit++){
    mat_selectors[bit] = mat_trgsw_alloc_new_DFT_sample(l, bg_bit, k, r, N);
  }
  MAT_TRGSW_MUL_SCRATCH scratch = mat_trgsw_alloc_mul_scratch(rows, N);

  TRLWE_Key * scalar_keys = (TRLWE_Key *) safe_malloc(sizeof(TRLWE_Key) * r);
  TRGSW_Key * scalar_trgsw_keys = (TRGSW_Key *) safe_malloc(sizeof(TRGSW_Key) * r);
  TRGSW_DFT ** scalar_selectors = (TRGSW_DFT **) safe_malloc(sizeof(TRGSW_DFT *) * r);
  TRLWE ** scalar_acc = (TRLWE **) safe_malloc(sizeof(TRLWE *) * r);
  TRLWE ** scalar_tmp_poly = (TRLWE **) safe_malloc(sizeof(TRLWE *) * r);
  TRLWE * scalar_rotated = (TRLWE *) safe_malloc(sizeof(TRLWE) * r);
  TRLWE * scalar_tmp = (TRLWE *) safe_malloc(sizeof(TRLWE) * r);
  TRLWE_DFT * scalar_tmp_dft = (TRLWE_DFT *) safe_malloc(sizeof(TRLWE_DFT) * r);

  PVW_TMLWE * pvw_acc = alloc_pvw_sample_array_local(in_N, k, r, N);
  PVW_TMLWE * pvw_tmp_poly = alloc_pvw_sample_array_local(in_N, k, r, N);
  PVW_TMLWE pvw_rotated = pvmtmlwe_alloc_new_sample(k, r, N);
  PVW_TMLWE pvw_tmp = pvmtmlwe_alloc_new_sample(k, r, N);
  PVW_TMLWE_DFT pvw_tmp_dft = pvmtmlwe_alloc_new_DFT_sample(k, r, N);

  for (size_t lane = 0; lane < (size_t) r; lane++){
    scalar_keys[lane] = trlwe_key_from_pvmtmlwe_lane(pvw_key, lane);
    scalar_trgsw_keys[lane] = trgsw_new_key(scalar_keys[lane], l, bg_bit);
    scalar_selectors[lane] = (TRGSW_DFT *) safe_malloc(sizeof(TRGSW_DFT) * r_prec);
    scalar_acc[lane] = trlwe_alloc_new_sample_array(in_N, k, N);
    scalar_tmp_poly[lane] = trlwe_alloc_new_sample_array(in_N, k, N);
    scalar_rotated[lane] = trlwe_alloc_new_sample(k, N);
    scalar_tmp[lane] = trlwe_alloc_new_sample(k, N);
    scalar_tmp_dft[lane] = trlwe_alloc_new_DFT_sample(k, N);
    for (size_t bit = 0; bit < (size_t) r_prec; bit++){
      scalar_selectors[lane][bit] = trgsw_alloc_new_DFT_sample(l, bg_bit, k, N);
    }
  }

  for (size_t bit = 0; bit < (size_t) r_prec; bit++){
    if(encrypted_selectors){
      mat_trgsw_monomial_DFT_sample(mat_selectors[bit], selector_bits[bit], 0, mat_key);
    }else{
      mat_trgsw_noiseless_trivial_DFT_sample_local(mat_selectors[bit],
          selector_bits[bit], 0, l, bg_bit, k, r, N);
    }
    for (size_t lane = 0; lane < (size_t) r; lane++){
      if(encrypted_selectors){
        trgsw_monomial_DFT_sample(scalar_selectors[lane][bit],
            selector_bits[bit], 0, scalar_trgsw_keys[lane]);
      }else{
        trgsw_noiseless_trivial_DFT_sample_local(scalar_selectors[lane][bit],
            selector_bits[bit], l, bg_bit, k, N);
      }
    }
  }

  TorusPolynomial * msg = polynomial_new_array_of_torus_polynomials(N, r);
  for (size_t idx = 0; idx < (size_t) in_N; idx++){
    for (size_t lane = 0; lane < (size_t) r; lane++){
      for (size_t coeff = 0; coeff < (size_t) N; coeff++){
        msg[lane]->coeffs[coeff] = int2torus((idx + 2 * lane + 3 * coeff) & 7, prec);
      }
    }
    pvmtmlwe_noiseless_trivial_sample(pvw_acc[idx], msg);
    for (size_t lane = 0; lane < (size_t) r; lane++){
      copy_pvw_lane_to_trlwe(scalar_acc[lane][idx], pvw_acc[idx], lane);
    }
  }

  PVW_TMLWE * pvw_p[2] = {pvw_acc, pvw_tmp_poly};

  for (size_t bit = 0; bit < (size_t) r_prec; bit++){
    const int power = 1 << bit;
    const int out = (bit + 1) & 1;
    const int in = out ^ 1;
    isolated_pvw_RGSW_monomial_step(pvw_p[out], pvw_p[in],
        mat_selectors[bit], in_N, power, scratch,
        pvw_rotated, pvw_tmp, pvw_tmp_dft);
    for (size_t lane = 0; lane < (size_t) r; lane++){
      TRLWE * scalar_p[2] = {scalar_acc[lane], scalar_tmp_poly[lane]};
      isolated_scalar_RGSW_monomial_step(scalar_p[out], scalar_p[in],
          scalar_selectors[lane][bit], in_N, power,
          scalar_rotated[lane], scalar_tmp[lane], scalar_tmp_dft[lane]);
    }

    TRLWE ** scalar_current = (TRLWE **) safe_malloc(sizeof(TRLWE *) * r);
    for (size_t lane = 0; lane < (size_t) r; lane++){
      scalar_current[lane] = ((bit + 1) & 1) ? scalar_tmp_poly[lane] : scalar_acc[lane];
    }
    char step_label[128];
    snprintf(step_label, sizeof(step_label), "%s bit=%" PRIu64, label, (uint64_t) bit);
    pass &= compare_pvw_scalar_array_phases(step_label, r, in_N, prec,
        pvw_p[out], pvw_key, scalar_current, scalar_keys);
    free(scalar_current);
    if(!pass) break;
  }

  if(pass && (r_prec & 1)){
    for (size_t idx = 0; idx < (size_t) in_N; idx++){
      pvmtmlwe_copy(pvw_acc[idx], pvw_tmp_poly[idx]);
    }
    for (size_t lane = 0; lane < (size_t) r; lane++){
      for (size_t idx = 0; idx < (size_t) in_N; idx++){
        trlwe_copy(scalar_acc[lane][idx], scalar_tmp_poly[lane][idx]);
      }
    }
    pass &= compare_pvw_scalar_array_phases(label, r, in_N, prec,
        pvw_acc, pvw_key, scalar_acc, scalar_keys);
  }

  printf("SAB_PVW isolated RGSW_monomial lane equivalence %s r=%d r_prec=%d: %s\n",
         label, r, r_prec, pass ? "Pass" : "Fail");

  free_array_of_polynomials(msg, r);
  free_pvmtmlwe_DFT(pvw_tmp_dft);
  free_pvmtmlwe(pvw_tmp);
  free_pvmtmlwe(pvw_rotated);
  free_pvw_sample_array_local(pvw_tmp_poly, in_N);
  free_pvw_sample_array_local(pvw_acc, in_N);

  for (size_t lane = 0; lane < (size_t) r; lane++){
    for (size_t bit = 0; bit < (size_t) r_prec; bit++){
      free_trgsw(scalar_selectors[lane][bit]);
    }
    free(scalar_selectors[lane]);
    free_trlwe(scalar_tmp_dft[lane]);
    free_trlwe(scalar_tmp[lane]);
    free_trlwe(scalar_rotated[lane]);
    free_trlwe_array(scalar_tmp_poly[lane], in_N);
    free_trlwe_array(scalar_acc[lane], in_N);
    free_trgsw_key(scalar_trgsw_keys[lane]);
    free_trlwe_key(scalar_keys[lane]);
  }
  free(scalar_tmp_dft);
  free(scalar_tmp);
  free(scalar_rotated);
  free(scalar_tmp_poly);
  free(scalar_acc);
  free(scalar_selectors);
  free(scalar_trgsw_keys);
  free(scalar_keys);

  free_mat_trgsw_mul_scratch(scratch);
  for (size_t bit = 0; bit < (size_t) r_prec; bit++){
    free_mat_trgsw_DFT(mat_selectors[bit]);
  }
  free(mat_selectors);
  free_mat_trgsw_key(mat_key);
  free_pvmtmlwe_key(pvw_key);
  return pass;
}

static bool check_pvw_rgsw_monomial_full_encrypted_case(int r){
  const int N = 1024, k = 1, l = 1, bg_bit = 23, prec = 3;
  const int r_prec = 3, in_N = 1 << r_prec;
  const int rows = (k + r) * l;
  const int selector_bits[3] = {1, 0, 1};
  const uint64_t gen_minus1 = 2 * N - 1;
  bool pass = true;

  PVW_TMLWE_Key pvw_key = pvmtmlwe_new_binary_key(N, k, r, pow(2, -60));
  PVW_TMLWE_KS_Key pvw_aut_minus1 = pvmtmlwe_new_automorphism_KS_key(pvw_key, gen_minus1, l, bg_bit);
  MAT_TRGSW_Key mat_key = mat_trgsw_new_key(pvw_key, l, bg_bit);
  MAT_TRGSW_DFT * mat_selectors = (MAT_TRGSW_DFT *) safe_malloc(sizeof(MAT_TRGSW_DFT) * r_prec);
  for (size_t bit = 0; bit < (size_t) r_prec; bit++){
    mat_selectors[bit] = mat_trgsw_alloc_new_DFT_sample(l, bg_bit, k, r, N);
    mat_trgsw_monomial_DFT_sample(mat_selectors[bit], selector_bits[bit], 0, mat_key);
  }
  MAT_TRGSW_MUL_SCRATCH scratch = mat_trgsw_alloc_mul_scratch(rows, N);

  TRLWE_Key * scalar_keys = (TRLWE_Key *) safe_malloc(sizeof(TRLWE_Key) * r);
  TRLWE_KS_Key * scalar_aut_minus1 = (TRLWE_KS_Key *) safe_malloc(sizeof(TRLWE_KS_Key) * r);
  TRGSW_Key * scalar_trgsw_keys = (TRGSW_Key *) safe_malloc(sizeof(TRGSW_Key) * r);
  TRGSW_DFT ** scalar_selectors = (TRGSW_DFT **) safe_malloc(sizeof(TRGSW_DFT *) * r);
  TRLWE ** scalar_acc = (TRLWE **) safe_malloc(sizeof(TRLWE *) * r);
  TRLWE ** scalar_tmp_poly = (TRLWE **) safe_malloc(sizeof(TRLWE *) * r);
  TRLWE * scalar_rotated = (TRLWE *) safe_malloc(sizeof(TRLWE) * r);
  TRLWE * scalar_tmp = (TRLWE *) safe_malloc(sizeof(TRLWE) * r);
  TRLWE_DFT * scalar_tmp_dft = (TRLWE_DFT *) safe_malloc(sizeof(TRLWE_DFT) * r);

  PVW_TMLWE * pvw_acc = alloc_pvw_sample_array_local(in_N, k, r, N);
  PVW_TMLWE * pvw_tmp_poly = alloc_pvw_sample_array_local(in_N, k, r, N);
  PVW_TMLWE pvw_rotated = pvmtmlwe_alloc_new_sample(k, r, N);
  PVW_TMLWE pvw_tmp = pvmtmlwe_alloc_new_sample(k, r, N);
  PVW_TMLWE_DFT pvw_tmp_dft = pvmtmlwe_alloc_new_DFT_sample(k, r, N);

  for (size_t lane = 0; lane < (size_t) r; lane++){
    scalar_keys[lane] = trlwe_key_from_pvmtmlwe_lane(pvw_key, lane);
    uint64_t scalar_aut_gens[1] = {gen_minus1};
    TRLWE_KS_Key * aut_set = trlwe_new_automorphism_KS_keyset_2(scalar_keys[lane],
        scalar_aut_gens, 1, l, bg_bit);
    scalar_aut_minus1[lane] = aut_set[0];
    free(aut_set);

    scalar_trgsw_keys[lane] = trgsw_new_key(scalar_keys[lane], l, bg_bit);
    scalar_selectors[lane] = (TRGSW_DFT *) safe_malloc(sizeof(TRGSW_DFT) * r_prec);
    scalar_acc[lane] = trlwe_alloc_new_sample_array(in_N, k, N);
    scalar_tmp_poly[lane] = trlwe_alloc_new_sample_array(in_N, k, N);
    scalar_rotated[lane] = trlwe_alloc_new_sample(k, N);
    scalar_tmp[lane] = trlwe_alloc_new_sample(k, N);
    scalar_tmp_dft[lane] = trlwe_alloc_new_DFT_sample(k, N);
    for (size_t bit = 0; bit < (size_t) r_prec; bit++){
      scalar_selectors[lane][bit] = trgsw_alloc_new_DFT_sample(l, bg_bit, k, N);
      trgsw_monomial_DFT_sample(scalar_selectors[lane][bit],
          selector_bits[bit], 0, scalar_trgsw_keys[lane]);
    }
  }

  TorusPolynomial * msg = polynomial_new_array_of_torus_polynomials(N, r);
  for (size_t idx = 0; idx < (size_t) in_N; idx++){
    for (size_t lane = 0; lane < (size_t) r; lane++){
      for (size_t coeff = 0; coeff < (size_t) N; coeff++){
        msg[lane]->coeffs[coeff] = int2torus((idx + lane + 5 * coeff) & 7, prec);
      }
    }
    pvmtmlwe_sample(pvw_acc[idx], msg, pvw_key);
    for (size_t lane = 0; lane < (size_t) r; lane++){
      copy_pvw_lane_to_trlwe(scalar_acc[lane][idx], pvw_acc[idx], lane);
    }
  }

  PVW_TMLWE * pvw_p[2] = {pvw_acc, pvw_tmp_poly};
  for (size_t bit = 0; bit < (size_t) r_prec; bit++){
    const int power = 1 << bit;
    const int out = (bit + 1) & 1;
    const int in = out ^ 1;
    isolated_pvw_RGSW_monomial_step_auto(pvw_p[out], pvw_p[in],
        mat_selectors[bit], in_N, power, scratch, pvw_aut_minus1,
        pvw_rotated, pvw_tmp, pvw_tmp_dft);
    for (size_t lane = 0; lane < (size_t) r; lane++){
      TRLWE * scalar_p[2] = {scalar_acc[lane], scalar_tmp_poly[lane]};
      isolated_scalar_RGSW_monomial_step_auto(scalar_p[out], scalar_p[in],
          scalar_selectors[lane][bit], in_N, power, scalar_aut_minus1[lane],
          scalar_rotated[lane], scalar_tmp[lane], scalar_tmp_dft[lane]);
    }

    TRLWE ** scalar_current = (TRLWE **) safe_malloc(sizeof(TRLWE *) * r);
    for (size_t lane = 0; lane < (size_t) r; lane++){
      scalar_current[lane] = out ? scalar_tmp_poly[lane] : scalar_acc[lane];
    }
    char step_label[128];
    snprintf(step_label, sizeof(step_label), "full-encrypted multibit bit=%" PRIu64, (uint64_t) bit);
    pass &= compare_pvw_scalar_array_phases(step_label, r, in_N, prec,
        pvw_p[out], pvw_key, scalar_current, scalar_keys);
    free(scalar_current);
    if(!pass) break;
  }

  if(pass && (r_prec & 1)){
    for (size_t idx = 0; idx < (size_t) in_N; idx++){
      pvmtmlwe_copy(pvw_acc[idx], pvw_tmp_poly[idx]);
    }
    for (size_t lane = 0; lane < (size_t) r; lane++){
      for (size_t idx = 0; idx < (size_t) in_N; idx++){
        trlwe_copy(scalar_acc[lane][idx], scalar_tmp_poly[lane][idx]);
      }
    }
    pass &= compare_pvw_scalar_array_phases("full-encrypted multibit final", r, in_N, prec,
        pvw_acc, pvw_key, scalar_acc, scalar_keys);
  }

  printf("SAB_PVW isolated RGSW_monomial lane equivalence full-encrypted multibit r=%d r_prec=%d: %s\n",
         r, r_prec, pass ? "Pass" : "Fail");

  free_array_of_polynomials(msg, r);
  free_pvmtmlwe_DFT(pvw_tmp_dft);
  free_pvmtmlwe(pvw_tmp);
  free_pvmtmlwe(pvw_rotated);
  free_pvw_sample_array_local(pvw_tmp_poly, in_N);
  free_pvw_sample_array_local(pvw_acc, in_N);

  for (size_t lane = 0; lane < (size_t) r; lane++){
    for (size_t bit = 0; bit < (size_t) r_prec; bit++){
      free_trgsw(scalar_selectors[lane][bit]);
    }
    free(scalar_selectors[lane]);
    free_trlwe(scalar_tmp_dft[lane]);
    free_trlwe(scalar_tmp[lane]);
    free_trlwe(scalar_rotated[lane]);
    free_trlwe_array(scalar_tmp_poly[lane], in_N);
    free_trlwe_array(scalar_acc[lane], in_N);
    free_trgsw_key(scalar_trgsw_keys[lane]);
    free_trlwe_ks_key(scalar_aut_minus1[lane]);
    free_trlwe_key(scalar_keys[lane]);
  }
  free(scalar_tmp_dft);
  free(scalar_tmp);
  free(scalar_rotated);
  free(scalar_tmp_poly);
  free(scalar_acc);
  free(scalar_selectors);
  free(scalar_trgsw_keys);
  free(scalar_aut_minus1);
  free(scalar_keys);

  free_mat_trgsw_mul_scratch(scratch);
  for (size_t bit = 0; bit < (size_t) r_prec; bit++){
    free_mat_trgsw_DFT(mat_selectors[bit]);
  }
  free(mat_selectors);
  free_mat_trgsw_key(mat_key);
  free_pvmtmlwe_ks_key(pvw_aut_minus1);
  free_pvmtmlwe_key(pvw_key);
  return pass;
}

static void isolated_pvw_RGSW_monomial_mul_auto(PVW_TMLWE * p0, PVW_TMLWE * tmp_poly,
    MAT_TRGSW_DFT * selectors, int r_prec, int in_N,
    MAT_TRGSW_MUL_SCRATCH scratch, PVW_TMLWE_KS_Key aut_minus1,
    PVW_TMLWE rotated, PVW_TMLWE tmp, PVW_TMLWE_DFT tmp_dft){
  PVW_TMLWE * p[2] = {p0, tmp_poly};
  for (size_t bit = 0; bit < (size_t) r_prec; bit++){
    const int power = 1 << bit;
    const int out = (bit + 1) & 1;
    const int in = out ^ 1;
    isolated_pvw_RGSW_monomial_step_auto(p[out], p[in], selectors[bit],
        in_N, power, scratch, aut_minus1, rotated, tmp, tmp_dft);
  }
  if(p[r_prec & 1] != p0){
    for (size_t idx = 0; idx < (size_t) in_N; idx++){
      pvmtmlwe_copy(p0[idx], p[r_prec & 1][idx]);
    }
  }
}

static void isolated_scalar_RGSW_monomial_mul_auto(TRLWE * p0, TRLWE * tmp_poly,
    TRGSW_DFT * selectors, int r_prec, int in_N, TRLWE_KS_Key aut_minus1,
    TRLWE rotated, TRLWE tmp, TRLWE_DFT tmp_dft){
  TRLWE * p[2] = {p0, tmp_poly};
  for (size_t bit = 0; bit < (size_t) r_prec; bit++){
    const int power = 1 << bit;
    const int out = (bit + 1) & 1;
    const int in = out ^ 1;
    isolated_scalar_RGSW_monomial_step_auto(p[out], p[in], selectors[bit],
        in_N, power, aut_minus1, rotated, tmp, tmp_dft);
  }
  if(p[r_prec & 1] != p0){
    for (size_t idx = 0; idx < (size_t) in_N; idx++){
      trlwe_copy(p0[idx], p[r_prec & 1][idx]);
    }
  }
}

static void isolated_pvw_sub_a_binary(PVW_TMLWE * p, const uint64_t * a,
    int in_N, PVW_TMLWE tmp){
  for (size_t idx = 0; idx < (size_t) in_N; idx++){
    pvmtmlwe_mul_by_xai(tmp, p[idx], a[idx]);
    pvmtmlwe_copy(p[idx], tmp);
  }
}

static void isolated_scalar_sub_a_binary(TRLWE * p, const uint64_t * a,
    int in_N, TRLWE tmp){
  for (size_t idx = 0; idx < (size_t) in_N; idx++){
    trlwe_mul_by_xai(tmp, p[idx], a[idx]);
    trlwe_copy(p[idx], tmp);
  }
}

static bool check_pvw_sparse_mul_binary_lane_equivalence(int r){
  const int N = 1024, k = 1, l = 1, bg_bit = 23, prec = 3;
  const int r_prec = 3, in_N = 16, h = 2;
  const uint64_t selector_values[3] = {5, 4, 7};
  const uint64_t a[16] = {
    1, 3, 5, 7, 9, 11, 13, 15,
    17, 19, 21, 23, 25, 27, 29, 31
  };
  const uint64_t gen_minus1 = 2 * N - 1;
  const int total_selectors = (h + 1) * r_prec;
  bool pass = true;

  printf("SAB_PVW_KERNEL_TEST sparse_mul r=%d step=input_key\n", r);
  TRLWE_Key input_key = test_binary_key_from_distances(in_N, k,
      selector_values, h, pow(2, -15));
  printf("SAB_PVW_KERNEL_TEST sparse_mul r=%d step=pvw_key\n", r);
  PVW_TMLWE_Key pvw_key = pvmtmlwe_new_binary_key(N, k, r, pow(2, -70));
  printf("SAB_PVW_KERNEL_TEST sparse_mul r=%d step=sab_pvw_key\n", r);
  SAB_PVW_Key pvw_sab = sab_pvw_new_binary_key(input_key, pvw_key,
      prec, h, r_prec, l, bg_bit);
  printf("SAB_PVW_KERNEL_TEST sparse_mul r=%d step=scalar_alloc\n", r);

  TRLWE_Key * scalar_keys = (TRLWE_Key *) safe_malloc(sizeof(TRLWE_Key) * r);
  TRLWE_KS_Key * scalar_aut_minus1 = (TRLWE_KS_Key *) safe_malloc(sizeof(TRLWE_KS_Key) * r);
  TRGSW_Key * scalar_trgsw_keys = (TRGSW_Key *) safe_malloc(sizeof(TRGSW_Key) * r);
  TRGSW_DFT ** scalar_selectors = (TRGSW_DFT **) safe_malloc(sizeof(TRGSW_DFT *) * r);
  TRLWE ** scalar_acc = (TRLWE **) safe_malloc(sizeof(TRLWE *) * r);
  TRLWE ** scalar_tmp_poly = (TRLWE **) safe_malloc(sizeof(TRLWE *) * r);
  TRLWE * scalar_rotated = (TRLWE *) safe_malloc(sizeof(TRLWE) * r);
  TRLWE * scalar_tmp = (TRLWE *) safe_malloc(sizeof(TRLWE) * r);
  TRLWE_DFT * scalar_tmp_dft = (TRLWE_DFT *) safe_malloc(sizeof(TRLWE_DFT) * r);

  PVW_TMLWE * pvw_acc = alloc_pvw_sample_array_local(in_N, k, r, N);

  printf("SAB_PVW_KERNEL_TEST sparse_mul r=%d step=scalar_keys\n", r);
  for (size_t lane = 0; lane < (size_t) r; lane++){
    scalar_keys[lane] = trlwe_key_from_pvmtmlwe_lane(pvw_key, lane);
    uint64_t scalar_aut_gens[1] = {gen_minus1};
    TRLWE_KS_Key * aut_set = trlwe_new_automorphism_KS_keyset_2(scalar_keys[lane],
        scalar_aut_gens, 1, l, bg_bit);
    scalar_aut_minus1[lane] = aut_set[0];
    free(aut_set);

    scalar_trgsw_keys[lane] = trgsw_new_key(scalar_keys[lane], l, bg_bit);
    scalar_selectors[lane] = (TRGSW_DFT *) safe_malloc(sizeof(TRGSW_DFT) * total_selectors);
    scalar_acc[lane] = trlwe_alloc_new_sample_array(in_N, k, N);
    scalar_tmp_poly[lane] = trlwe_alloc_new_sample_array(in_N, k, N);
    scalar_rotated[lane] = trlwe_alloc_new_sample(k, N);
    scalar_tmp[lane] = trlwe_alloc_new_sample(k, N);
    scalar_tmp_dft[lane] = trlwe_alloc_new_DFT_sample(k, N);
    for (size_t round = 0; round < (size_t) (h + 1); round++){
      for (size_t bit = 0; bit < (size_t) r_prec; bit++){
        const size_t idx = round * r_prec + bit;
        scalar_selectors[lane][idx] = trgsw_alloc_new_DFT_sample(l, bg_bit, k, N);
        trgsw_monomial_DFT_sample(scalar_selectors[lane][idx],
            (selector_values[round] >> bit) & 1, 0, scalar_trgsw_keys[lane]);
      }
    }
  }

  printf("SAB_PVW_KERNEL_TEST sparse_mul r=%d step=acc_init\n", r);
  TorusPolynomial * msg = polynomial_new_array_of_torus_polynomials(N, r);
  for (size_t idx = 0; idx < (size_t) in_N; idx++){
    for (size_t lane = 0; lane < (size_t) r; lane++){
      for (size_t coeff = 0; coeff < (size_t) N; coeff++){
        msg[lane]->coeffs[coeff] = int2torus((3 * idx + 2 * lane + coeff) & 7, prec);
      }
    }
    pvmtmlwe_sample(pvw_acc[idx], msg, pvw_key);
    for (size_t lane = 0; lane < (size_t) r; lane++){
      copy_pvw_lane_to_trlwe(scalar_acc[lane][idx], pvw_acc[idx], lane);
    }
  }

  printf("SAB_PVW_KERNEL_TEST sparse_mul r=%d step=rounds\n", r);
  for (size_t round = 0; round < (size_t) h; round++){
    printf("SAB_PVW_KERNEL_TEST sparse_mul r=%d round=%" PRIu64 " step=RGSW\n",
           r, (uint64_t) round);
    sab_pvw_RGSW_monomial_mul(pvw_acc, pvw_sab->s[0][round], pvw_sab);
    for (size_t lane = 0; lane < (size_t) r; lane++){
      isolated_scalar_RGSW_monomial_mul_auto(scalar_acc[lane], scalar_tmp_poly[lane],
          &scalar_selectors[lane][round * r_prec], r_prec, in_N,
          scalar_aut_minus1[lane], scalar_rotated[lane],
          scalar_tmp[lane], scalar_tmp_dft[lane]);
    }
    char label[128];
    snprintf(label, sizeof(label), "binary sparse round=%" PRIu64 " after RGSW", (uint64_t) round);
    pass &= compare_pvw_scalar_array_phases(label, r, in_N, prec,
        pvw_acc, pvw_key, scalar_acc, scalar_keys);
    if(!pass) break;

    printf("SAB_PVW_KERNEL_TEST sparse_mul r=%d round=%" PRIu64 " step=sub_a\n",
           r, (uint64_t) round);
    sab_pvw_sub_a_binary(pvw_acc, a, pvw_sab);
    for (size_t lane = 0; lane < (size_t) r; lane++){
      isolated_scalar_sub_a_binary(scalar_acc[lane], a, in_N, scalar_tmp[lane]);
    }
    snprintf(label, sizeof(label), "binary sparse round=%" PRIu64 " after sub_a", (uint64_t) round);
    pass &= compare_pvw_scalar_array_phases(label, r, in_N, prec,
        pvw_acc, pvw_key, scalar_acc, scalar_keys);
    if(!pass) break;
  }

  if(pass){
    printf("SAB_PVW_KERNEL_TEST sparse_mul r=%d step=final_RGSW\n", r);
    sab_pvw_RGSW_monomial_mul(pvw_acc, pvw_sab->s[0][h], pvw_sab);
    for (size_t lane = 0; lane < (size_t) r; lane++){
      isolated_scalar_RGSW_monomial_mul_auto(scalar_acc[lane], scalar_tmp_poly[lane],
          &scalar_selectors[lane][h * r_prec], r_prec, in_N,
          scalar_aut_minus1[lane], scalar_rotated[lane],
          scalar_tmp[lane], scalar_tmp_dft[lane]);
    }
    pass &= compare_pvw_scalar_array_phases("binary sparse after final RGSW", r, in_N, prec,
        pvw_acc, pvw_key, scalar_acc, scalar_keys);
  }

  printf("SAB_PVW API binary sparse_mul lane equivalence r=%d h=%d r_prec=%d: %s\n",
         r, h, r_prec, pass ? "Pass" : "Fail");

  free_array_of_polynomials(msg, r);
  free_pvw_sample_array_local(pvw_acc, in_N);

  for (size_t lane = 0; lane < (size_t) r; lane++){
    for (size_t idx = 0; idx < (size_t) total_selectors; idx++){
      free_trgsw(scalar_selectors[lane][idx]);
    }
    free(scalar_selectors[lane]);
    free_trlwe(scalar_tmp_dft[lane]);
    free_trlwe(scalar_tmp[lane]);
    free_trlwe(scalar_rotated[lane]);
    free_trlwe_array(scalar_tmp_poly[lane], in_N);
    free_trlwe_array(scalar_acc[lane], in_N);
    free_trgsw_key(scalar_trgsw_keys[lane]);
    free_trlwe_ks_key(scalar_aut_minus1[lane]);
    free_trlwe_key(scalar_keys[lane]);
  }
  free(scalar_tmp_dft);
  free(scalar_tmp);
  free(scalar_rotated);
  free(scalar_tmp_poly);
  free(scalar_acc);
  free(scalar_selectors);
  free(scalar_trgsw_keys);
  free(scalar_aut_minus1);
  free(scalar_keys);

  free_sab_pvw_key(pvw_sab);
  free_pvmtmlwe_key(pvw_key);
  free_trlwe_key(input_key);
  return pass;
}

static bool check_pvw_bootstrap_wo_extract_binary_lane_equivalence(int r){
  const int in_N = 16, in_k = 1, out_N = 1024, out_k = 1;
  const int l = 1, bg_bit = 23, prec = 3, h = 2, r_prec = 3;
  const int ell_packing = 2, b_packing = 14, ell_hw = 12, b_hw = 1;
  const uint64_t selector_values[3] = {5, 4, 7};
  const uint64_t packing_key_distances[2] = {2, 7};
  bool pass = true;

  TRLWE_Key input_key = test_binary_key_from_distances(in_N, in_k,
      selector_values, h, pow(2, -15));
  TRLWE_Key packing_key = test_binary_key_from_distances(in_N, in_k,
      packing_key_distances, h, pow(2, -70));
  PVW_TMLWE_Key pvw_key = pvmtmlwe_new_binary_key(out_N, out_k, r, pow(2, -70));
  SAB_PVW_Key pvw_sab = sab_pvw_new_binary_full_key(input_key, packing_key,
      pvw_key, prec, b_packing, ell_packing, ell_hw, b_hw, h, r_prec, l,
      bg_bit);

  TRLWE_Key * scalar_keys = (TRLWE_Key *) safe_malloc(sizeof(TRLWE_Key) * r);
  TRLWE_KS_Key * scalar_aut_minus1 = (TRLWE_KS_Key *) safe_malloc(sizeof(TRLWE_KS_Key) * r);
  TRGSW_Key * scalar_trgsw_keys = (TRGSW_Key *) safe_malloc(sizeof(TRGSW_Key) * r);
  TRGSW_DFT ** scalar_selectors = (TRGSW_DFT **) safe_malloc(sizeof(TRGSW_DFT *) * r);
  TRLWE ** scalar_out = (TRLWE **) safe_malloc(sizeof(TRLWE *) * r);
  TRLWE ** scalar_tmp_poly = (TRLWE **) safe_malloc(sizeof(TRLWE *) * r);
  TRLWE * scalar_rotated = (TRLWE *) safe_malloc(sizeof(TRLWE) * r);
  TRLWE * scalar_tmp = (TRLWE *) safe_malloc(sizeof(TRLWE) * r);
  TRLWE_DFT * scalar_tmp_dft = (TRLWE_DFT *) safe_malloc(sizeof(TRLWE_DFT) * r);
  TRLWE * scalar_tv = (TRLWE *) safe_malloc(sizeof(TRLWE) * r);

  TorusPolynomial input_msg = polynomial_new_torus_polynomial(in_N);
  for (size_t idx = 0; idx < (size_t) in_N; idx++){
    input_msg->coeffs[idx] = int2torus((3 * idx + 1) & 7, prec);
  }
  TRLWE input = trlwe_new_sample(input_msg, input_key);

  TorusPolynomial * tv_msg = polynomial_new_array_of_torus_polynomials(out_N, r);
  for (size_t lane = 0; lane < (size_t) r; lane++){
    for (size_t coeff = 0; coeff < (size_t) out_N; coeff++){
      tv_msg[lane]->coeffs[coeff] = int2torus((5 * lane + 3 * coeff) & 7, prec);
    }
  }
  PVW_TMLWE pvw_tv = pvmtmlwe_new_noiseless_trivial_sample(tv_msg, out_k, r, out_N);
  PVW_TMLWE * pvw_out = alloc_pvw_sample_array_local(in_N, out_k, r, out_N);
  TRLWE * pvw_full_out = trlwe_alloc_new_sample_array(r, in_k, in_N);

  for (size_t lane = 0; lane < (size_t) r; lane++){
    scalar_keys[lane] = trlwe_key_from_pvmtmlwe_lane(pvw_key, lane);
    uint64_t scalar_aut_gens[1] = {2 * out_N - 1};
    TRLWE_KS_Key * aut_set = trlwe_new_automorphism_KS_keyset_2(scalar_keys[lane],
        scalar_aut_gens, 1, l, bg_bit);
    scalar_aut_minus1[lane] = aut_set[0];
    free(aut_set);

    scalar_trgsw_keys[lane] = trgsw_new_key(scalar_keys[lane], l, bg_bit);
    scalar_selectors[lane] = (TRGSW_DFT *) safe_malloc(sizeof(TRGSW_DFT) * (h + 1) * r_prec);
    for (size_t round = 0; round < (size_t) (h + 1); round++){
      for (size_t bit = 0; bit < (size_t) r_prec; bit++){
        const size_t idx = round * r_prec + bit;
        scalar_selectors[lane][idx] = trgsw_alloc_new_DFT_sample(l, bg_bit,
            out_k, out_N);
        trgsw_monomial_DFT_sample(scalar_selectors[lane][idx],
            (selector_values[round] >> bit) & 1, 0, scalar_trgsw_keys[lane]);
      }
    }
    scalar_tv[lane] = trlwe_new_noiseless_trivial_sample(tv_msg[lane],
        out_k, out_N);
    scalar_out[lane] = trlwe_alloc_new_sample_array(in_N, out_k, out_N);
    scalar_tmp_poly[lane] = trlwe_alloc_new_sample_array(in_N, out_k, out_N);
    scalar_rotated[lane] = trlwe_alloc_new_sample(out_k, out_N);
    scalar_tmp[lane] = trlwe_alloc_new_sample(out_k, out_N);
    scalar_tmp_dft[lane] = trlwe_alloc_new_DFT_sample(out_k, out_N);
  }

  sab_pvw_bootstrap_wo_extract_binary(pvw_out, input, pvw_tv, pvw_sab);
  sab_pvw_bootstrap_binary(pvw_full_out, input, pvw_tv, pvw_sab);
  for (size_t lane = 0; lane < (size_t) r; lane++){
    const int log_N2 = (int) log2(2 * out_N);
    const uint64_t prec_offset = 1ULL << (64 - prec - 1);
    uint64_t a_mod[in_N];
    for (size_t idx = 0; idx < (size_t) in_N; idx++){
      trlwe_mul_by_xai(scalar_out[lane][idx], scalar_tv[lane],
          torus2int(input->b->coeffs[idx] + prec_offset, log_N2));
      a_mod[idx] = torus2int(input->a[0]->coeffs[idx], log_N2);
    }
    for (size_t round = 0; round < (size_t) h; round++){
      isolated_scalar_RGSW_monomial_mul_auto(scalar_out[lane],
          scalar_tmp_poly[lane], &scalar_selectors[lane][round * r_prec],
          r_prec, in_N, scalar_aut_minus1[lane], scalar_rotated[lane],
          scalar_tmp[lane], scalar_tmp_dft[lane]);
      isolated_scalar_sub_a_binary(scalar_out[lane], a_mod, in_N,
          scalar_tmp[lane]);
    }
    isolated_scalar_RGSW_monomial_mul_auto(scalar_out[lane],
        scalar_tmp_poly[lane], &scalar_selectors[lane][h * r_prec],
        r_prec, in_N, scalar_aut_minus1[lane], scalar_rotated[lane],
        scalar_tmp[lane], scalar_tmp_dft[lane]);
  }

  pass &= compare_pvw_scalar_array_phases("bootstrap_wo_extract binary", r,
      in_N, prec, pvw_out, pvw_key, scalar_out, scalar_keys);

  printf("SAB_PVW API bootstrap_wo_extract binary lane equivalence r=%d h=%d r_prec=%d: %s\n",
         r, h, r_prec, pass ? "Pass" : "Fail");

  PVW_TLWE_Key pvw_extracted_key = pvwtlwe_alloc_key(out_N * out_k, r,
      pvw_key->sigma);
  pvmtmlwe_extract_pvmtlwe_key(pvw_extracted_key, pvw_key);
  PVW_TLWE * pvw_extracted = pvwtlwe_alloc_sample_array(in_N,
      out_N * out_k, r);
  sab_pvw_extract_pvwtlwe(pvw_extracted, pvw_out, pvw_sab);

  TLWE_Key * scalar_extracted_keys = (TLWE_Key *) safe_malloc(sizeof(TLWE_Key) * r);
  TLWE ** scalar_extracted = (TLWE **) safe_malloc(sizeof(TLWE *) * r);
  for (size_t lane = 0; lane < (size_t) r; lane++){
    scalar_extracted_keys[lane] = tlwe_alloc_key(out_N * out_k,
        scalar_keys[lane]->sigma);
    trlwe_extract_tlwe_key(scalar_extracted_keys[lane], scalar_keys[lane]);
    scalar_extracted[lane] = tlwe_alloc_sample_array(in_N, out_N * out_k);
    for (size_t idx = 0; idx < (size_t) in_N; idx++){
      trlwe_extract_tlwe(scalar_extracted[lane][idx], scalar_out[lane][idx], 0);
    }
  }

  const bool extract_pass = compare_pvwtlwe_scalar_array_phases(
      "bootstrap_extract binary", r, in_N, prec, pvw_extracted,
      pvw_extracted_key, scalar_extracted, scalar_extracted_keys);
  pass &= extract_pass;
  printf("SAB_PVW API extract binary lane equivalence r=%d h=%d r_prec=%d: %s\n",
         r, h, r_prec, extract_pass ? "Pass" : "Fail");

  TLWE ** pvw_lane_extracted = (TLWE **) safe_malloc(sizeof(TLWE *) * r);
  for (size_t lane = 0; lane < (size_t) r; lane++){
    pvw_lane_extracted[lane] = tlwe_alloc_sample_array(in_N, out_N * out_k);
    for (size_t idx = 0; idx < (size_t) in_N; idx++){
      copy_pvwtlwe_lane_to_tlwe(pvw_lane_extracted[lane][idx],
          pvw_extracted[idx], lane);
    }
  }

  const bool materialized_pass = compare_tlwe_scalar_array_phases(
      "bootstrap_extract binary", r, in_N, prec, pvw_lane_extracted,
      scalar_extracted_keys, scalar_extracted, scalar_extracted_keys);
  pass &= materialized_pass;
  printf("SAB_PVW API materialized TLWE binary lane equivalence r=%d h=%d r_prec=%d: %s\n",
         r, h, r_prec, materialized_pass ? "Pass" : "Fail");

  bool packing_hwks_pass = true;
  bool full_api_pass = true;
  for (size_t lane = 0; lane < (size_t) r; lane++){
    TRLWE_KS_Key packing_ks = pvw_sab->packing_keys[lane];
    TRLWE pvw_packed = trlwe_alloc_new_sample(in_k, in_N);
    TRLWE scalar_packed = trlwe_alloc_new_sample(in_k, in_N);
    TRLWE pvw_hwks = trlwe_alloc_new_sample(in_k, in_N);
    TRLWE scalar_hwks = trlwe_alloc_new_sample(in_k, in_N);

    trlwe_full_packing_keyswitch(pvw_packed, pvw_lane_extracted[lane],
        in_N, packing_ks);
    trlwe_full_packing_keyswitch(scalar_packed, scalar_extracted[lane],
        in_N, packing_ks);
    packing_hwks_pass &= compare_trlwe_pair_phases("packing binary",
        pvw_packed, packing_key, scalar_packed, packing_key, prec, lane);

    trlwe_keyswitch(pvw_hwks, pvw_packed, pvw_sab->hw_reducing_key);
    trlwe_keyswitch(scalar_hwks, scalar_packed, pvw_sab->hw_reducing_key);
    packing_hwks_pass &= compare_trlwe_pair_phases("HW-KS binary",
        pvw_hwks, input_key, scalar_hwks, input_key, prec, lane);
    full_api_pass &= compare_trlwe_pair_phases("full bootstrap binary",
        pvw_full_out[lane], input_key, scalar_hwks, input_key, prec, lane);

    free_trlwe(scalar_hwks);
    free_trlwe(pvw_hwks);
    free_trlwe(scalar_packed);
    free_trlwe(pvw_packed);
  }
  pass &= packing_hwks_pass;
  printf("SAB_PVW API packing/HW-KS binary lane equivalence r=%d h=%d r_prec=%d: %s\n",
         r, h, r_prec, packing_hwks_pass ? "Pass" : "Fail");
  pass &= full_api_pass;
  printf("SAB_PVW API full bootstrap binary lane equivalence r=%d h=%d r_prec=%d: %s\n",
         r, h, r_prec, full_api_pass ? "Pass" : "Fail");

  for (size_t lane = 0; lane < (size_t) r; lane++){
    free_tlwe_array(pvw_lane_extracted[lane], in_N);
    free_tlwe_array(scalar_extracted[lane], in_N);
    free_tlwe_key(scalar_extracted_keys[lane]);
    for (size_t idx = 0; idx < (size_t) (h + 1) * r_prec; idx++){
      free_trgsw(scalar_selectors[lane][idx]);
    }
    free(scalar_selectors[lane]);
    free_trlwe(scalar_tmp_dft[lane]);
    free_trlwe(scalar_tmp[lane]);
    free_trlwe(scalar_rotated[lane]);
    free_trlwe_array(scalar_tmp_poly[lane], in_N);
    free_trlwe_array(scalar_out[lane], in_N);
    free_trlwe(scalar_tv[lane]);
    free_trgsw_key(scalar_trgsw_keys[lane]);
    free_trlwe_ks_key(scalar_aut_minus1[lane]);
    free_trlwe_key(scalar_keys[lane]);
  }
  free_trlwe_key(packing_key);
  free(pvw_lane_extracted);
  free(scalar_extracted);
  free(scalar_extracted_keys);
  free_pvwtlwe_array(pvw_extracted, in_N);
  free_pvwtlwe_key(pvw_extracted_key);
  free(scalar_tv);
  free(scalar_tmp_dft);
  free(scalar_tmp);
  free(scalar_rotated);
  free(scalar_tmp_poly);
  free(scalar_out);
  free(scalar_selectors);
  free(scalar_trgsw_keys);
  free(scalar_aut_minus1);
  free(scalar_keys);
  free_trlwe_array(pvw_full_out, r);
  free_pvw_sample_array_local(pvw_out, in_N);
  free_pvmtmlwe(pvw_tv);
  free_array_of_polynomials(tv_msg, r);
  free_trlwe(input);
  free_polynomial(input_msg);
  free_sab_pvw_key(pvw_sab);
  free_pvmtmlwe_key(pvw_key);
  free_trlwe_key(input_key);
  return pass;
}

static bool check_pvw_rgsw_monomial_lane_equivalence(int r){
  bool pass = true;
  const int bit_zero[1] = {0};
  const int bit_one[1] = {1};
  const int multi_bits[3] = {1, 0, 1};

  printf("SAB_PVW_KERNEL_TEST begin RGSW_monomial r=%d case=encrypted-selector bit0\n", r);
  pass &= check_pvw_rgsw_monomial_lane_case(r, 1, bit_zero, true,
      "encrypted-selector bit0");
  printf("SAB_PVW_KERNEL_TEST begin RGSW_monomial r=%d case=encrypted-selector bit1\n", r);
  pass &= check_pvw_rgsw_monomial_lane_case(r, 1, bit_one, true,
      "encrypted-selector bit1");
  printf("SAB_PVW_KERNEL_TEST begin RGSW_monomial r=%d case=trivial-selector multibit\n", r);
  pass &= check_pvw_rgsw_monomial_lane_case(r, 3, multi_bits, false,
      "trivial-selector multibit");
  printf("SAB_PVW_KERNEL_TEST begin RGSW_monomial r=%d case=full-encrypted multibit\n", r);
  pass &= check_pvw_rgsw_monomial_full_encrypted_case(r);
#if defined(USE_SPQLIOS) && defined(AVX512_OPT)
  printf("SAB_PVW_KERNEL_TEST skip small-N sparse/bootstrap r=%d backend=spqlios_avx512 reason=N=16 staged TRLWE key helpers are not supported by this backend; use target full gate\n", r);
  return pass;
#endif
  printf("SAB_PVW_KERNEL_TEST begin sparse_mul r=%d\n", r);
  pass &= check_pvw_sparse_mul_binary_lane_equivalence(r);
  printf("SAB_PVW_KERNEL_TEST begin bootstrap_wo_extract r=%d\n", r);
  pass &= check_pvw_bootstrap_wo_extract_binary_lane_equivalence(r);
  return pass;
}

static bool check_pvw_target_full_binary_lane_equivalence(int r){
  const SAB_PVW_Target_Params params = sab_pvw_target_params();
  const int in_N = params.in_N, in_k = params.in_k;
  const int out_N = params.out_N, out_k = params.out_k;
  const int l = params.l, bg_bit = params.bg_bit, prec = params.prec;
  const int h = params.h, r_prec = params.r_prec;
  const int h_out = params.h_out, h_packing = params.h_packing;
  const int ell_packing = params.ell_packing;
  const int b_packing = params.b_packing;
  const int ell_hw = params.t_ks, b_hw = params.b_ks;
  uint64_t distances[h];
  bool pass = true;

  sab_pvw_fill_target_distances(distances, &params);

  TRLWE_Key input_key = test_binary_key_from_distances(in_N, in_k,
      distances, h, params.sigma_in);
  TRLWE_Key packing_key = trlwe_new_ternary_key(in_N, in_k, h_packing,
      params.sigma_packing);
  PVW_TMLWE_Key pvw_key = pvmtmlwe_new_ternary_key(out_N, out_k, r, h_out,
      params.sigma_out);
  SAB_PVW_Key pvw_sab = sab_pvw_new_binary_full_key(input_key, packing_key,
      pvw_key, prec, b_packing, ell_packing, ell_hw, b_hw, h, r_prec, l,
      bg_bit);

  TorusPolynomial input_msg = polynomial_new_torus_polynomial(in_N);
  for (size_t idx = 0; idx < (size_t) in_N; idx++){
    input_msg->coeffs[idx] = int2torus((3 * idx + 1) & 7, prec);
  }
  TRLWE input = trlwe_new_sample(input_msg, input_key);

  TorusPolynomial * tv_msg = polynomial_new_array_of_torus_polynomials(out_N, r);
  for (size_t lane = 0; lane < (size_t) r; lane++){
    for (size_t coeff = 0; coeff < (size_t) out_N; coeff++){
      tv_msg[lane]->coeffs[coeff] = int2torus(
          (5 * lane + 3 * coeff + 1) & 7, prec);
    }
  }
  PVW_TMLWE pvw_tv = pvmtmlwe_new_noiseless_trivial_sample(tv_msg, out_k, r,
      out_N);
  TRLWE * pvw_out = trlwe_alloc_new_sample_array(r, in_k, in_N);
  sab_pvw_bootstrap_binary(pvw_out, input, pvw_tv, pvw_sab);

  for (size_t lane = 0; lane < (size_t) r; lane++){
    TRLWE_Key scalar_key = trlwe_key_from_pvmtmlwe_lane(pvw_key, lane);
    TRGSW_Key scalar_trgsw_key = trgsw_new_key(scalar_key, l, bg_bit);
    SAB_Key scalar_sab = new_sparse_amortized_bootstrapping(input_key,
        packing_key, scalar_trgsw_key, prec, b_packing, ell_packing,
        ell_hw, b_hw, h, r_prec, false, false, false);
    TRLWE scalar_tv = trlwe_new_noiseless_trivial_sample(tv_msg[lane],
        out_k, out_N);
    TRLWE scalar_out = trlwe_alloc_new_sample(in_k, in_N);

    sab_rlwe_bootstrap(scalar_out, input, scalar_tv, scalar_sab);
    pass &= compare_trlwe_pair_phases("target full bootstrap binary",
        pvw_out[lane], input_key, scalar_out, input_key, prec, lane);

    free_trlwe(scalar_out);
    free_trlwe(scalar_tv);
    free_trgsw_key(scalar_trgsw_key);
    free_trlwe_key(scalar_key);
  }

  printf("SAB_PVW target full bootstrap binary lane equivalence r=%d h=%d r_prec=%d: %s\n",
         r, h, r_prec, pass ? "Pass" : "Fail");

  free_trlwe_array(pvw_out, r);
  free_pvmtmlwe(pvw_tv);
  free_array_of_polynomials(tv_msg, r);
  free_trlwe(input);
  free_polynomial(input_msg);
  free_sab_pvw_key(pvw_sab);
  free_pvmtmlwe_key(pvw_key);
  free_trlwe_key(packing_key);
  free_trlwe_key(input_key);
  return pass;
}

void test_sab_pvw_target_full(){
  const int r = 2;
  const bool pass = check_pvw_target_full_binary_lane_equivalence(r);
  printf("SAB_PVW target full bootstrap gate: %s\n", pass ? "Pass" : "Fail");
  if(!pass) exit(1);
}

void test_sab_pvw_target_bench(){
  const int r = SAB_PVW_BENCH_R, reps = SAB_PVW_BENCH_REPS;
  const SAB_PVW_Target_Params params = sab_pvw_target_params();
  const int in_N = params.in_N, in_k = params.in_k;
  const int out_N = params.out_N, out_k = params.out_k;
  const int l = params.l, bg_bit = params.bg_bit, prec = params.prec;
  const int h = params.h, r_prec = params.r_prec;
  const int h_out = params.h_out, h_packing = params.h_packing;
  const int ell_packing = params.ell_packing;
  const int b_packing = params.b_packing;
  const int ell_hw = params.t_ks, b_hw = params.b_ks;
  uint64_t distances[h];

  if(r < 1 || reps < 1){
    printf("SAB_PVW_BENCH invalid config r=%d reps=%d\n", r, reps);
    exit(1);
  }

  sab_pvw_fill_target_distances(distances, &params);

  TRLWE_Key input_key = test_binary_key_from_distances(in_N, in_k,
      distances, h, params.sigma_in);
  TRLWE_Key packing_key = trlwe_new_ternary_key(in_N, in_k, h_packing,
      params.sigma_packing);
  PVW_TMLWE_Key pvw_key = pvmtmlwe_new_ternary_key(out_N, out_k, r, h_out,
      params.sigma_out);
  SAB_PVW_Key pvw_sab = sab_pvw_new_binary_full_key(input_key, packing_key,
      pvw_key, prec, b_packing, ell_packing, ell_hw, b_hw, h, r_prec, l,
      bg_bit);

  SAB_Key * scalar_sabs = (SAB_Key *) safe_malloc(sizeof(SAB_Key) * r);
  TRGSW_Key * scalar_trgsw_keys = (TRGSW_Key *) safe_malloc(sizeof(TRGSW_Key) * r);
  TRLWE_Key * scalar_keys = (TRLWE_Key *) safe_malloc(sizeof(TRLWE_Key) * r);

  TorusPolynomial input_msg = polynomial_new_torus_polynomial(in_N);
  for (size_t idx = 0; idx < (size_t) in_N; idx++){
    input_msg->coeffs[idx] = int2torus((3 * idx + 1) & 7, prec);
  }
  TRLWE input = trlwe_new_sample(input_msg, input_key);

  TorusPolynomial * tv_msg = polynomial_new_array_of_torus_polynomials(out_N, r);
  for (size_t lane = 0; lane < (size_t) r; lane++){
    for (size_t coeff = 0; coeff < (size_t) out_N; coeff++){
      tv_msg[lane]->coeffs[coeff] = int2torus(
          (5 * lane + 3 * coeff + 1) & 7, prec);
    }
  }
  PVW_TMLWE pvw_tv = pvmtmlwe_new_noiseless_trivial_sample(tv_msg, out_k, r,
      out_N);
  TRLWE * scalar_tvs = trlwe_alloc_new_sample_array(r, out_k, out_N);
  TRLWE * scalar_out = trlwe_alloc_new_sample_array(r, in_k, in_N);
  TRLWE * pvw_out = trlwe_alloc_new_sample_array(r, in_k, in_N);

  for (size_t lane = 0; lane < (size_t) r; lane++){
    scalar_keys[lane] = trlwe_key_from_pvmtmlwe_lane(pvw_key, lane);
    scalar_trgsw_keys[lane] = trgsw_new_key(scalar_keys[lane], l, bg_bit);
    scalar_sabs[lane] = new_sparse_amortized_bootstrapping(input_key,
        packing_key, scalar_trgsw_keys[lane], prec, b_packing, ell_packing,
        ell_hw, b_hw, h, r_prec, false, false, false);
    trlwe_noiseless_trivial_sample(scalar_tvs[lane], tv_msg[lane]);
  }

  sab_pvw_bootstrap_binary(pvw_out, input, pvw_tv, pvw_sab);
  bool pass = true;
  for (size_t lane = 0; lane < (size_t) r; lane++){
    sab_rlwe_bootstrap(scalar_out[lane], input, scalar_tvs[lane],
        scalar_sabs[lane]);
    pass &= compare_trlwe_pair_phases("bench target full bootstrap binary",
        pvw_out[lane], input_key, scalar_out[lane], input_key, prec, lane);
  }
  printf("SAB_PVW_BENCH correctness target_full r=%d h=%d r_prec=%d: %s\n",
         r, h, r_prec, pass ? "Pass" : "Fail");
  if(!pass) exit(1);

  uint64_t * pvw_times = (uint64_t *) safe_malloc(sizeof(uint64_t) * reps);
  uint64_t * scalar_times = (uint64_t *) safe_malloc(sizeof(uint64_t) * reps);
  double * speedups = (double *) safe_malloc(sizeof(double) * reps);
  for (size_t rep = 0; rep < (size_t) reps; rep++){
    uint64_t begin = get_time();
    sab_pvw_bootstrap_binary(pvw_out, input, pvw_tv, pvw_sab);
    pvw_times[rep] = get_time() - begin;

    begin = get_time();
    for (size_t lane = 0; lane < (size_t) r; lane++){
      sab_rlwe_bootstrap(scalar_out[lane], input, scalar_tvs[lane],
          scalar_sabs[lane]);
    }
    scalar_times[rep] = get_time() - begin;
    speedups[rep] = ((double) scalar_times[rep]) / pvw_times[rep];
    printf("SAB_PVW_BENCH sample target_full r=%d rep=%" PRIu64
           " pvw_us=%" PRIu64 " scalar_repeated_us=%" PRIu64
           " speedup=%.3fx\n",
           r, (uint64_t) rep, pvw_times[rep], scalar_times[rep],
           speedups[rep]);
  }
  const double pvw_avg = mean_u64(pvw_times, reps);
  const double scalar_avg = mean_u64(scalar_times, reps);
  const double pvw_stddev = stddev_u64(pvw_times, reps, pvw_avg);
  const double scalar_stddev = stddev_u64(scalar_times, reps, scalar_avg);
  const double speedup_avg = mean_double(speedups, reps);
  const double speedup_stddev = stddev_double(speedups, reps, speedup_avg);
  printf("SAB_PVW_BENCH summary target_full r=%d reps=%d pvw_avg_us=%.3f pvw_stddev_us=%.3f pvw_lane_avg_us=%.3f scalar_repeated_avg_us=%.3f scalar_stddev_us=%.3f scalar_lane_avg_us=%.3f speedup_vs_scalar_repeated=%.3fx speedup_stddev=%.3f\n",
         r, reps, pvw_avg, pvw_stddev, pvw_avg / r, scalar_avg,
         scalar_stddev, scalar_avg / r, scalar_avg / pvw_avg,
         speedup_stddev);

  free(speedups);
  free(scalar_times);
  free(pvw_times);
  free_trlwe_array(pvw_out, r);
  free_trlwe_array(scalar_out, r);
  free_trlwe_array(scalar_tvs, r);
  free_pvmtmlwe(pvw_tv);
  free_array_of_polynomials(tv_msg, r);
  free_trlwe(input);
  free_polynomial(input_msg);
  free_sab_pvw_key(pvw_sab);
  for (size_t lane = 0; lane < (size_t) r; lane++){
    free_trgsw_key(scalar_trgsw_keys[lane]);
    free_trlwe_key(scalar_keys[lane]);
  }
  free(scalar_sabs);
  free(scalar_trgsw_keys);
  free(scalar_keys);
  free_pvmtmlwe_key(pvw_key);
  free_trlwe_key(packing_key);
  free_trlwe_key(input_key);
}

void test_sab_pvw_resource(){
  const int r = SAB_PVW_RESOURCE_R;
  const SAB_PVW_Target_Params params = sab_pvw_target_params();
  const int in_N = params.in_N, in_k = params.in_k;
  const int out_N = params.out_N, out_k = params.out_k;
  const int l = params.l, bg_bit = params.bg_bit, prec = params.prec;
  const int h = params.h, r_prec = params.r_prec;
  const int h_out = params.h_out, h_packing = params.h_packing;
  const int ell_packing = params.ell_packing;
  const int b_packing = params.b_packing;
  const int ell_hw = params.t_ks, b_hw = params.b_ks;
  const char * mode = getenv("SAB_PVW_RESOURCE_MODE");
  uint64_t distances[h];

  if(mode == NULL || mode[0] == '\0') mode = "both";
  const bool run_pvw = strcmp(mode, "pvw") == 0 || strcmp(mode, "both") == 0;
  const bool run_scalar = strcmp(mode, "scalar") == 0 || strcmp(mode, "both") == 0;
  if(r < 1 || (!run_pvw && !run_scalar)){
    printf("SAB_PVW_RESOURCE invalid config r=%d mode=%s\n", r, mode);
    exit(1);
  }

  sab_pvw_fill_target_distances(distances, &params);

  printf("SAB_PVW_RESOURCE config target_full r=%d mode=%s in_N=%d out_N=%d h=%d r_prec=%d ell_packing=%d b_packing=%d ell_hw=%d b_hw=%d\n",
         r, mode, in_N, out_N, h, r_prec, ell_packing, b_packing,
         ell_hw, b_hw);

  uint64_t begin = get_time();
  TRLWE_Key input_key = test_binary_key_from_distances(in_N, in_k,
      distances, h, params.sigma_in);
  const uint64_t input_keygen_us = get_time() - begin;

  begin = get_time();
  TRLWE_Key packing_key = trlwe_new_ternary_key(in_N, in_k, h_packing,
      params.sigma_packing);
  const uint64_t packing_keygen_us = get_time() - begin;

  begin = get_time();
  PVW_TMLWE_Key pvw_key = pvmtmlwe_new_ternary_key(out_N, out_k, r, h_out,
      params.sigma_out);
  const uint64_t pvw_secret_keygen_us = get_time() - begin;

  const uint64_t scalar_one_key_bytes = estimate_scalar_sab_public_key_bytes(
      in_N, in_k, out_N, out_k, h, r_prec, l, ell_packing, ell_hw);
  const uint64_t scalar_repeated_key_bytes = scalar_one_key_bytes * (uint64_t) r;
  const uint64_t pvw_key_bytes = estimate_pvw_sab_public_key_bytes(in_N, in_k,
      out_N, out_k, r, h, r_prec, l, ell_packing, ell_hw);

  printf("SAB_PVW_RESOURCE base_keygen target_full r=%d input_keygen_us=%" PRIu64
         " packing_keygen_us=%" PRIu64 " pvw_secret_keygen_us=%" PRIu64 "\n",
         r, input_keygen_us, packing_keygen_us, pvw_secret_keygen_us);
  printf("SAB_PVW_RESOURCE key_bytes target_full r=%d pvw_estimated_key_bytes=%" PRIu64
         " scalar_one_estimated_key_bytes=%" PRIu64
         " scalar_repeated_estimated_key_bytes=%" PRIu64
         " pvw_vs_scalar_repeated_ratio=%.6f estimate_scope=public_bootstrap_key_excludes_secret_keys_and_tmp\n",
         r, pvw_key_bytes, scalar_one_key_bytes, scalar_repeated_key_bytes,
         scalar_repeated_key_bytes == 0 ? 0.0
             : (double) pvw_key_bytes / (double) scalar_repeated_key_bytes);
  print_resource_rss("after_base_keys", r, mode);

  if(run_pvw){
    begin = get_time();
    SAB_PVW_Key pvw_sab = sab_pvw_new_binary_full_key(input_key, packing_key,
        pvw_key, prec, b_packing, ell_packing, ell_hw, b_hw, h, r_prec, l,
        bg_bit);
    const uint64_t pvw_sab_keygen_us = get_time() - begin;
    printf("SAB_PVW_RESOURCE keygen target_full r=%d mode=pvw pvw_sab_keygen_us=%" PRIu64 "\n",
           r, pvw_sab_keygen_us);
    print_resource_rss("after_pvw_sab_keygen", r, "pvw");
    (void) pvw_sab;
  }

  if(run_scalar){
    SAB_Key * scalar_sabs = (SAB_Key *) safe_malloc(sizeof(SAB_Key) * r);
    TRGSW_Key * scalar_trgsw_keys = (TRGSW_Key *) safe_malloc(sizeof(TRGSW_Key) * r);
    TRLWE_Key * scalar_keys = (TRLWE_Key *) safe_malloc(sizeof(TRLWE_Key) * r);
    begin = get_time();
    for (size_t lane = 0; lane < (size_t) r; lane++){
      scalar_keys[lane] = trlwe_key_from_pvmtmlwe_lane(pvw_key, lane);
      scalar_trgsw_keys[lane] = trgsw_new_key(scalar_keys[lane], l, bg_bit);
      scalar_sabs[lane] = new_sparse_amortized_bootstrapping(input_key,
          packing_key, scalar_trgsw_keys[lane], prec, b_packing, ell_packing,
          ell_hw, b_hw, h, r_prec, false, false, false);
    }
    const uint64_t scalar_sab_keygen_us = get_time() - begin;
    printf("SAB_PVW_RESOURCE keygen target_full r=%d mode=scalar scalar_repeated_sab_keygen_us=%" PRIu64
           " scalar_lane_avg_keygen_us=%.3f\n",
           r, scalar_sab_keygen_us, (double) scalar_sab_keygen_us / r);
    print_resource_rss("after_scalar_repeated_sab_keygen", r, "scalar");
    (void) scalar_sabs;
    (void) scalar_trgsw_keys;
    (void) scalar_keys;
  }

  printf("SAB_PVW_RESOURCE target_full gate: Pass\n");
}

void test_sab_pvw_noise(){
  const int r = SAB_PVW_NOISE_R, trials = SAB_PVW_NOISE_TRIALS;
  const SAB_PVW_Target_Params params = sab_pvw_target_params();
  const int in_N = params.in_N, in_k = params.in_k;
  const int out_N = params.out_N, out_k = params.out_k;
  const int l = params.l, bg_bit = params.bg_bit, prec = params.prec;
  const int h = params.h, r_prec = params.r_prec;
  const int h_out = params.h_out, h_packing = params.h_packing;
  const int ell_packing = params.ell_packing;
  const int b_packing = params.b_packing;
  const int ell_hw = params.t_ks, b_hw = params.b_ks;
  const uint64_t lut_size = 1ULL << prec;
  const uint64_t mod_mask = (1ULL << (prec - 1)) - 1;
  uint64_t distances[h];

  if(r < 1 || trials < 1){
    printf("SAB_PVW_NOISE invalid config r=%d trials=%d\n", r, trials);
    exit(1);
  }

  sab_pvw_fill_target_distances(distances, &params);

  TRLWE_Key input_key = test_binary_key_from_distances(in_N, in_k,
      distances, h, params.sigma_in);
  TRLWE_Key packing_key = trlwe_new_ternary_key(in_N, in_k, h_packing,
      params.sigma_packing);
  PVW_TMLWE_Key pvw_key = pvmtmlwe_new_ternary_key(out_N, out_k, r, h_out,
      params.sigma_out);
  SAB_PVW_Key pvw_sab = sab_pvw_new_binary_full_key(input_key, packing_key,
      pvw_key, prec, b_packing, ell_packing, ell_hw, b_hw, h, r_prec, l,
      bg_bit);

  SAB_Key * scalar_sabs = (SAB_Key *) safe_malloc(sizeof(SAB_Key) * r);
  TRGSW_Key * scalar_trgsw_keys = (TRGSW_Key *) safe_malloc(sizeof(TRGSW_Key) * r);
  TRLWE_Key * scalar_keys = (TRLWE_Key *) safe_malloc(sizeof(TRLWE_Key) * r);
  for (size_t lane = 0; lane < (size_t) r; lane++){
    scalar_keys[lane] = trlwe_key_from_pvmtmlwe_lane(pvw_key, lane);
    scalar_trgsw_keys[lane] = trgsw_new_key(scalar_keys[lane], l, bg_bit);
    scalar_sabs[lane] = new_sparse_amortized_bootstrapping(input_key,
        packing_key, scalar_trgsw_keys[lane], prec, b_packing, ell_packing,
        ell_hw, b_hw, h, r_prec, false, false, false);
  }

  TorusNoiseStats * pvw_lane = (TorusNoiseStats *) safe_malloc(
      sizeof(TorusNoiseStats) * r);
  TorusNoiseStats * scalar_lane = (TorusNoiseStats *) safe_malloc(
      sizeof(TorusNoiseStats) * r);
  TorusNoiseStats * pair_lane = (TorusNoiseStats *) safe_malloc(
      sizeof(TorusNoiseStats) * r);
  memset(pvw_lane, 0, sizeof(TorusNoiseStats) * r);
  memset(scalar_lane, 0, sizeof(TorusNoiseStats) * r);
  memset(pair_lane, 0, sizeof(TorusNoiseStats) * r);

  uint64_t * luts = (uint64_t *) safe_malloc(sizeof(uint64_t) * r * lut_size);
  TorusPolynomial input_msg = polynomial_new_torus_polynomial(in_N);
  TRLWE input = trlwe_alloc_new_sample(in_k, in_N);
  TorusPolynomial * tv_msg = polynomial_new_array_of_torus_polynomials(out_N,
      r);
  PVW_TMLWE pvw_tv = pvmtmlwe_alloc_new_sample(out_k, r, out_N);
  TRLWE * scalar_tvs = trlwe_alloc_new_sample_array(r, out_k, out_N);
  TRLWE * scalar_out = trlwe_alloc_new_sample_array(r, in_k, in_N);
  TRLWE * pvw_out = trlwe_alloc_new_sample_array(r, in_k, in_N);
  TorusPolynomial pvw_phase = polynomial_new_torus_polynomial(in_N);
  TorusPolynomial scalar_phase = polynomial_new_torus_polynomial(in_N);

  for (size_t trial = 0; trial < (size_t) trials; trial++){
    for (size_t idx = 0; idx < (size_t) in_N; idx++){
      input_msg->coeffs[idx] = int2torus((idx + trial) & mod_mask, prec);
    }
    trlwe_sample(input, input_msg, input_key);

    for (size_t lane = 0; lane < (size_t) r; lane++){
      uint64_t * lane_lut = &luts[lane * lut_size];
      for (size_t value = 0; value < lut_size; value++){
        lane_lut[value] = (3 * value + 5 * lane + trial + 1) & mod_mask;
      }
      sab_LUT_packing(scalar_tvs[lane], lane_lut, scalar_sabs[lane]);
      polynomial_copy_torus_polynomial(tv_msg[lane], scalar_tvs[lane]->b);
    }
    pvmtmlwe_noiseless_trivial_sample(pvw_tv, tv_msg);

    sab_pvw_bootstrap_binary(pvw_out, input, pvw_tv, pvw_sab);
    for (size_t lane = 0; lane < (size_t) r; lane++){
      sab_rlwe_bootstrap(scalar_out[lane], input, scalar_tvs[lane],
          scalar_sabs[lane]);
    }

    for (size_t lane = 0; lane < (size_t) r; lane++){
      trlwe_phase(pvw_phase, pvw_out[lane], input_key);
      trlwe_phase(scalar_phase, scalar_out[lane], input_key);
      const uint64_t * lane_lut = &luts[lane * lut_size];
      for (size_t idx = 0; idx < (size_t) in_N; idx++){
        const uint64_t input_val = torus2int(input_msg->coeffs[idx], prec);
        const uint64_t expected_val = lane_lut[input_val];
        const Torus expected_torus = int2torus(expected_val, prec);
        const uint64_t pvw_val = torus2int(pvw_phase->coeffs[idx], prec);
        const uint64_t scalar_val = torus2int(scalar_phase->coeffs[idx],
            prec);

        torus_noise_stats_add(&pvw_lane[lane], pvw_phase->coeffs[idx],
            expected_torus, pvw_val, expected_val);
        torus_noise_stats_add(&scalar_lane[lane], scalar_phase->coeffs[idx],
            expected_torus, scalar_val, expected_val);
        torus_noise_stats_add(&pair_lane[lane], pvw_phase->coeffs[idx],
            scalar_phase->coeffs[idx], pvw_val, scalar_val);
      }
    }
    printf("SAB_PVW_NOISE trial target_full r=%d trial=%" PRIu64
           " complete\n", r, (uint64_t) trial);
  }

  TorusNoiseStats pvw_total = {0, 0, 0, 0};
  TorusNoiseStats scalar_total = {0, 0, 0, 0};
  TorusNoiseStats pair_total = {0, 0, 0, 0};
  for (size_t lane = 0; lane < (size_t) r; lane++){
    torus_noise_stats_merge(&pvw_total, pvw_lane[lane]);
    torus_noise_stats_merge(&scalar_total, scalar_lane[lane]);
    torus_noise_stats_merge(&pair_total, pair_lane[lane]);
    printf("SAB_PVW_NOISE lane target_full r=%d lane=%" PRIu64
           " trials=%d pvw_failures=%" PRIu64
           " scalar_failures=%" PRIu64 " pair_failures=%" PRIu64
           " pvw_log2_sigma_torus=%.3f scalar_log2_sigma_torus=%.3f"
           " pair_log2_sigma_torus=%.3f\n",
           r, (uint64_t) lane, trials, pvw_lane[lane].failures,
           scalar_lane[lane].failures, pair_lane[lane].failures,
           torus_noise_log2_sigma(pvw_lane[lane]),
           torus_noise_log2_sigma(scalar_lane[lane]),
           torus_noise_log2_sigma(pair_lane[lane]));
  }

  const double pvw_log2_sigma = torus_noise_log2_sigma(pvw_total);
  const double scalar_log2_sigma = torus_noise_log2_sigma(scalar_total);
  const double log2_gap = isfinite(pvw_log2_sigma) &&
      isfinite(scalar_log2_sigma) ? pvw_log2_sigma - scalar_log2_sigma : 0.0;
  const bool noise_gap_pass = (!isfinite(pvw_log2_sigma) &&
      !isfinite(scalar_log2_sigma)) ||
      (isfinite(pvw_log2_sigma) && isfinite(scalar_log2_sigma) &&
       log2_gap <= SAB_PVW_NOISE_MAX_LOG2_GAP);
  const bool pass = pvw_total.failures == 0 && scalar_total.failures == 0 &&
      pair_total.failures == 0 && noise_gap_pass;

  printf("SAB_PVW_NOISE summary target_full r=%d trials=%d points=%" PRIu64
         " pvw_failures=%" PRIu64 " scalar_failures=%" PRIu64
         " pair_failures=%" PRIu64
         " pvw_log2_sigma_torus=%.3f scalar_log2_sigma_torus=%.3f"
         " pair_log2_sigma_torus=%.3f pvw_minus_scalar_log2=%.3f"
         " max_allowed_log2_gap=%.3f\n",
         r, trials, pvw_total.count, pvw_total.failures,
         scalar_total.failures, pair_total.failures, pvw_log2_sigma,
         scalar_log2_sigma, torus_noise_log2_sigma(pair_total), log2_gap,
         (double) SAB_PVW_NOISE_MAX_LOG2_GAP);
  print_torus_noise_stats("SAB_PVW_NOISE pvw_total", pvw_total);
  print_torus_noise_stats("SAB_PVW_NOISE scalar_total", scalar_total);
  print_torus_noise_stats("SAB_PVW_NOISE pair_total", pair_total);
  printf("SAB_PVW_NOISE target full bootstrap gate: %s\n",
         pass ? "Pass" : "Fail");
  if(!pass) exit(1);

  free_polynomial(scalar_phase);
  free_polynomial(pvw_phase);
  free_trlwe_array(pvw_out, r);
  free_trlwe_array(scalar_out, r);
  free_trlwe_array(scalar_tvs, r);
  free_pvmtmlwe(pvw_tv);
  free_array_of_polynomials(tv_msg, r);
  free_trlwe(input);
  free_polynomial(input_msg);
  free(luts);
  free(pair_lane);
  free(scalar_lane);
  free(pvw_lane);
  free_sab_pvw_key(pvw_sab);
  for (size_t lane = 0; lane < (size_t) r; lane++){
    free_trgsw_key(scalar_trgsw_keys[lane]);
    free_trlwe_key(scalar_keys[lane]);
  }
  free(scalar_sabs);
  free(scalar_trgsw_keys);
  free(scalar_keys);
  free_pvmtmlwe_key(pvw_key);
  free_trlwe_key(packing_key);
  free_trlwe_key(input_key);
}

static void stage_noise_merge_lanes(TorusNoiseStats * total,
    TorusNoiseStats * lanes, int r){
  memset(total, 0, sizeof(*total));
  for (size_t lane = 0; lane < (size_t) r; lane++){
    torus_noise_stats_merge(total, lanes[lane]);
  }
}

static void print_stage_pair_noise(const char * stage, int r, int trials,
    TorusNoiseStats * lanes){
  TorusNoiseStats total;
  stage_noise_merge_lanes(&total, lanes, r);
  for (size_t lane = 0; lane < (size_t) r; lane++){
    printf("SAB_PVW_STAGE_NOISE lane stage=%s r=%d lane=%" PRIu64
           " trials=%d pair_failures=%" PRIu64
           " pair_log2_sigma_torus=%.3f pair_log2_max_abs_torus=%.3f\n",
           stage, r, (uint64_t) lane, trials, lanes[lane].failures,
           torus_noise_log2_sigma(lanes[lane]),
           torus_noise_log2_max_abs(lanes[lane]));
  }
  printf("SAB_PVW_STAGE_NOISE summary stage=%s r=%d trials=%d"
         " points=%" PRIu64 " pair_failures=%" PRIu64
         " pair_log2_sigma_torus=%.3f pair_log2_max_abs_torus=%.3f\n",
         stage, r, trials, total.count, total.failures,
         torus_noise_log2_sigma(total),
         torus_noise_log2_max_abs(total));
}

static bool stage_pair_noise_pass(TorusNoiseStats * lanes, int r){
  TorusNoiseStats total;
  stage_noise_merge_lanes(&total, lanes, r);
  return total.failures == 0;
}

static void add_stage_noise_pvmtmlwe_coeff0(TorusNoiseStats * lanes, int r,
    int count, int prec, PVW_TMLWE * pvw_arr, PVW_TMLWE_Key pvw_key,
    TRLWE ** scalar_arr, TRLWE_Key * scalar_keys){
  const int N = pvw_arr[0]->b[0]->N;
  TorusPolynomial * pvw_phase = polynomial_new_array_of_torus_polynomials(N, r);
  TorusPolynomial scalar_phase = polynomial_new_torus_polynomial(N);
  for (size_t idx = 0; idx < (size_t) count; idx++){
    pvmtmlwe_phase(pvw_phase, pvw_arr[idx], pvw_key);
    for (size_t lane = 0; lane < (size_t) r; lane++){
      trlwe_phase(scalar_phase, scalar_arr[lane][idx], scalar_keys[lane]);
      const Torus lhs = pvw_phase[lane]->coeffs[0];
      const Torus rhs = scalar_phase->coeffs[0];
      torus_noise_stats_add(&lanes[lane], lhs, rhs, torus2int(lhs, prec),
          torus2int(rhs, prec));
    }
  }
  free_polynomial(scalar_phase);
  free_array_of_polynomials(pvw_phase, r);
}

static void add_stage_noise_pvwtlwe(TorusNoiseStats * lanes, int r,
    int count, int prec, PVW_TLWE * pvw_arr, PVW_TLWE_Key pvw_key,
    TLWE ** scalar_arr, TLWE_Key * scalar_keys){
  Torus * pvw_phase = (Torus *) safe_malloc(sizeof(Torus) * r);
  for (size_t idx = 0; idx < (size_t) count; idx++){
    pvwtlwe_phase(pvw_phase, pvw_arr[idx], pvw_key);
    for (size_t lane = 0; lane < (size_t) r; lane++){
      const Torus rhs = tlwe_phase(scalar_arr[lane][idx],
          scalar_keys[lane]);
      torus_noise_stats_add(&lanes[lane], pvw_phase[lane], rhs,
          torus2int(pvw_phase[lane], prec), torus2int(rhs, prec));
    }
  }
  free(pvw_phase);
}

static void add_stage_noise_tlwe(TorusNoiseStats * lanes, int r, int count,
    int prec, TLWE ** lhs_arr, TLWE_Key * lhs_keys, TLWE ** rhs_arr,
    TLWE_Key * rhs_keys){
  for (size_t idx = 0; idx < (size_t) count; idx++){
    for (size_t lane = 0; lane < (size_t) r; lane++){
      const Torus lhs = tlwe_phase(lhs_arr[lane][idx], lhs_keys[lane]);
      const Torus rhs = tlwe_phase(rhs_arr[lane][idx], rhs_keys[lane]);
      torus_noise_stats_add(&lanes[lane], lhs, rhs, torus2int(lhs, prec),
          torus2int(rhs, prec));
    }
  }
}

static void add_stage_noise_trlwe(TorusNoiseStats * lanes, int lane, int prec,
    TRLWE lhs, TRLWE_Key lhs_key, TRLWE rhs, TRLWE_Key rhs_key){
  const int N = lhs->b->N;
  TorusPolynomial lhs_phase = polynomial_new_torus_polynomial(N);
  TorusPolynomial rhs_phase = polynomial_new_torus_polynomial(N);
  trlwe_phase(lhs_phase, lhs, lhs_key);
  trlwe_phase(rhs_phase, rhs, rhs_key);
  for (size_t coeff = 0; coeff < (size_t) N; coeff++){
    const Torus lhs_value = lhs_phase->coeffs[coeff];
    const Torus rhs_value = rhs_phase->coeffs[coeff];
    torus_noise_stats_add(&lanes[lane], lhs_value, rhs_value,
        torus2int(lhs_value, prec), torus2int(rhs_value, prec));
  }
  free_polynomial(rhs_phase);
  free_polynomial(lhs_phase);
}

void test_sab_pvw_stage_noise(){
  const int r = SAB_PVW_NOISE_R, trials = SAB_PVW_NOISE_TRIALS;
  const SAB_PVW_Target_Params params = sab_pvw_target_params();
  const int in_N = params.in_N, in_k = params.in_k;
  const int out_N = params.out_N, out_k = params.out_k;
  const int l = params.l, bg_bit = params.bg_bit, prec = params.prec;
  const int h = params.h, r_prec = params.r_prec;
  const int h_out = params.h_out, h_packing = params.h_packing;
  const int ell_packing = params.ell_packing;
  const int b_packing = params.b_packing;
  const int ell_hw = params.t_ks, b_hw = params.b_ks;
  const uint64_t lut_size = 1ULL << prec;
  const uint64_t mod_mask = (1ULL << (prec - 1)) - 1;
  uint64_t distances[h];

  if(r < 1 || trials < 1){
    printf("SAB_PVW_STAGE_NOISE invalid config r=%d trials=%d\n", r, trials);
    exit(1);
  }
  sab_pvw_fill_target_distances(distances, &params);

  TRLWE_Key input_key = test_binary_key_from_distances(in_N, in_k,
      distances, h, params.sigma_in);
  TRLWE_Key packing_key = trlwe_new_ternary_key(in_N, in_k, h_packing,
      params.sigma_packing);
  PVW_TMLWE_Key pvw_key = pvmtmlwe_new_ternary_key(out_N, out_k, r, h_out,
      params.sigma_out);
  SAB_PVW_Key pvw_sab = sab_pvw_new_binary_full_key(input_key, packing_key,
      pvw_key, prec, b_packing, ell_packing, ell_hw, b_hw, h, r_prec, l,
      bg_bit);

  SAB_Key * scalar_sabs = (SAB_Key *) safe_malloc(sizeof(SAB_Key) * r);
  TRGSW_Key * scalar_trgsw_keys = (TRGSW_Key *) safe_malloc(sizeof(TRGSW_Key) * r);
  TRLWE_Key * scalar_keys = (TRLWE_Key *) safe_malloc(sizeof(TRLWE_Key) * r);
  TLWE_Key * scalar_extracted_keys = (TLWE_Key *) safe_malloc(sizeof(TLWE_Key) * r);
  TLWE ** pvw_lane_extracted = (TLWE **) safe_malloc(sizeof(TLWE *) * r);

  for (size_t lane = 0; lane < (size_t) r; lane++){
    scalar_keys[lane] = trlwe_key_from_pvmtmlwe_lane(pvw_key, lane);
    scalar_trgsw_keys[lane] = trgsw_new_key(scalar_keys[lane], l, bg_bit);
    scalar_sabs[lane] = new_sparse_amortized_bootstrapping(input_key,
        packing_key, scalar_trgsw_keys[lane], prec, b_packing, ell_packing,
        ell_hw, b_hw, h, r_prec, false, false, false);
    scalar_extracted_keys[lane] = tlwe_alloc_key(out_N * out_k,
        scalar_keys[lane]->sigma);
    trlwe_extract_tlwe_key(scalar_extracted_keys[lane], scalar_keys[lane]);
    pvw_lane_extracted[lane] = tlwe_alloc_sample_array(in_N, out_N * out_k);
  }
  PVW_TLWE_Key pvw_extracted_key = pvwtlwe_alloc_key(out_N * out_k, r,
      pvw_key->sigma);
  pvmtmlwe_extract_pvmtlwe_key(pvw_extracted_key, pvw_key);

  TorusNoiseStats * blind_coeff0 = (TorusNoiseStats *) safe_malloc(
      sizeof(TorusNoiseStats) * r);
  TorusNoiseStats * extracted = (TorusNoiseStats *) safe_malloc(
      sizeof(TorusNoiseStats) * r);
  TorusNoiseStats * materialized = (TorusNoiseStats *) safe_malloc(
      sizeof(TorusNoiseStats) * r);
  TorusNoiseStats * packing = (TorusNoiseStats *) safe_malloc(
      sizeof(TorusNoiseStats) * r);
  TorusNoiseStats * hwks = (TorusNoiseStats *) safe_malloc(
      sizeof(TorusNoiseStats) * r);
  memset(blind_coeff0, 0, sizeof(TorusNoiseStats) * r);
  memset(extracted, 0, sizeof(TorusNoiseStats) * r);
  memset(materialized, 0, sizeof(TorusNoiseStats) * r);
  memset(packing, 0, sizeof(TorusNoiseStats) * r);
  memset(hwks, 0, sizeof(TorusNoiseStats) * r);

  uint64_t * luts = (uint64_t *) safe_malloc(sizeof(uint64_t) * r * lut_size);
  TorusPolynomial input_msg = polynomial_new_torus_polynomial(in_N);
  TRLWE input = trlwe_alloc_new_sample(in_k, in_N);
  TorusPolynomial * tv_msg = polynomial_new_array_of_torus_polynomials(out_N,
      r);
  PVW_TMLWE pvw_tv = pvmtmlwe_alloc_new_sample(out_k, r, out_N);
  TRLWE * scalar_tvs = trlwe_alloc_new_sample_array(r, out_k, out_N);
  TRLWE * pvw_hwks = trlwe_alloc_new_sample_array(r, in_k, in_N);
  TRLWE * scalar_hwks = trlwe_alloc_new_sample_array(r, in_k, in_N);
  TRLWE pvw_packed = trlwe_alloc_new_sample(in_k, in_N);
  TRLWE scalar_packed = trlwe_alloc_new_sample(in_k, in_N);
  TRLWE ** scalar_one = (TRLWE **) safe_malloc(sizeof(TRLWE *) * r);
  TLWE ** scalar_extracted = (TLWE **) safe_malloc(sizeof(TLWE *) * r);
  for (size_t lane = 0; lane < (size_t) r; lane++){
    scalar_extracted[lane] = scalar_sabs[lane]->tmp->extracted_poly;
  }

  for (size_t trial = 0; trial < (size_t) trials; trial++){
    for (size_t idx = 0; idx < (size_t) in_N; idx++){
      input_msg->coeffs[idx] = int2torus((idx + trial) & mod_mask, prec);
    }
    trlwe_sample(input, input_msg, input_key);

    for (size_t lane = 0; lane < (size_t) r; lane++){
      uint64_t * lane_lut = &luts[lane * lut_size];
      for (size_t value = 0; value < lut_size; value++){
        lane_lut[value] = (3 * value + 5 * lane + trial + 1) & mod_mask;
      }
      sab_LUT_packing(scalar_tvs[lane], lane_lut, scalar_sabs[lane]);
      polynomial_copy_torus_polynomial(tv_msg[lane], scalar_tvs[lane]->b);
    }
    pvmtmlwe_noiseless_trivial_sample(pvw_tv, tv_msg);

    sab_pvw_bootstrap_wo_extract_binary(pvw_sab->tmp->acc, input, pvw_tv,
        pvw_sab);
    for (size_t lane = 0; lane < (size_t) r; lane++){
      sab_rlwe_bootstrap_wo_extract(scalar_sabs[lane]->tmp->rlwe_poly1,
          input, scalar_tvs[lane], scalar_sabs[lane]);
    }
    for (size_t idx = 0; idx < (size_t) in_N; idx++){
      PVW_TMLWE pvw_one[1] = {pvw_sab->tmp->acc[idx]};
      for (size_t lane = 0; lane < (size_t) r; lane++){
        scalar_one[lane] = &scalar_sabs[lane]->tmp->rlwe_poly1[idx];
      }
      add_stage_noise_pvmtmlwe_coeff0(blind_coeff0, r, 1, prec, pvw_one,
          pvw_key, scalar_one, scalar_keys);
    }

    sab_pvw_extract_pvwtlwe(pvw_sab->tmp->extracted, pvw_sab->tmp->acc,
        pvw_sab);
    for (size_t lane = 0; lane < (size_t) r; lane++){
      for (size_t idx = 0; idx < (size_t) in_N; idx++){
        trlwe_extract_tlwe(scalar_sabs[lane]->tmp->extracted_poly[idx],
            scalar_sabs[lane]->tmp->rlwe_poly1[idx], 0);
      }
    }
    add_stage_noise_pvwtlwe(extracted, r, in_N, prec,
        pvw_sab->tmp->extracted, pvw_extracted_key, scalar_extracted,
        scalar_extracted_keys);

    for (size_t lane = 0; lane < (size_t) r; lane++){
      for (size_t idx = 0; idx < (size_t) in_N; idx++){
        copy_pvwtlwe_lane_to_tlwe(pvw_lane_extracted[lane][idx],
            pvw_sab->tmp->extracted[idx], lane);
      }
    }
    add_stage_noise_tlwe(materialized, r, in_N, prec, pvw_lane_extracted,
        scalar_extracted_keys, scalar_extracted, scalar_extracted_keys);

    for (size_t lane = 0; lane < (size_t) r; lane++){
      trlwe_full_packing_keyswitch(pvw_packed, pvw_lane_extracted[lane],
          in_N, pvw_sab->packing_keys[lane]);
      trlwe_full_packing_keyswitch(scalar_packed,
          scalar_sabs[lane]->tmp->extracted_poly, in_N,
          pvw_sab->packing_keys[lane]);
      add_stage_noise_trlwe(packing, (int) lane, prec, pvw_packed,
          packing_key, scalar_packed, packing_key);

      trlwe_keyswitch(pvw_hwks[lane], pvw_packed, pvw_sab->hw_reducing_key);
      trlwe_keyswitch(scalar_hwks[lane], scalar_packed,
          pvw_sab->hw_reducing_key);
      add_stage_noise_trlwe(hwks, (int) lane, prec, pvw_hwks[lane],
          input_key, scalar_hwks[lane], input_key);
    }
    printf("SAB_PVW_STAGE_NOISE trial target_full r=%d trial=%" PRIu64
           " complete\n", r, (uint64_t) trial);
  }

  print_stage_pair_noise("blind_rotate_coeff0", r, trials, blind_coeff0);
  print_stage_pair_noise("extract", r, trials, extracted);
  print_stage_pair_noise("materialize_tlwe", r, trials, materialized);
  print_stage_pair_noise("packing_ks", r, trials, packing);
  print_stage_pair_noise("hw_ks", r, trials, hwks);

  const bool pass = stage_pair_noise_pass(blind_coeff0, r) &&
      stage_pair_noise_pass(extracted, r) &&
      stage_pair_noise_pass(materialized, r) &&
      stage_pair_noise_pass(packing, r) &&
      stage_pair_noise_pass(hwks, r);
  printf("SAB_PVW_STAGE_NOISE target full bootstrap stage gate: %s\n",
         pass ? "Pass" : "Fail");
  if(!pass) exit(1);

  free(scalar_extracted);
  free(scalar_one);
  free_trlwe(scalar_packed);
  free_trlwe(pvw_packed);
  free_trlwe_array(scalar_hwks, r);
  free_trlwe_array(pvw_hwks, r);
  free_trlwe_array(scalar_tvs, r);
  free_pvmtmlwe(pvw_tv);
  free_array_of_polynomials(tv_msg, r);
  free_trlwe(input);
  free_polynomial(input_msg);
  free(luts);
  free(hwks);
  free(packing);
  free(materialized);
  free(extracted);
  free(blind_coeff0);
  free_pvwtlwe_key(pvw_extracted_key);
  for (size_t lane = 0; lane < (size_t) r; lane++){
    free_tlwe_array(pvw_lane_extracted[lane], in_N);
    free_tlwe_key(scalar_extracted_keys[lane]);
    free_trgsw_key(scalar_trgsw_keys[lane]);
    free_trlwe_key(scalar_keys[lane]);
  }
  free(pvw_lane_extracted);
  free(scalar_extracted_keys);
  free_sab_pvw_key(pvw_sab);
  free(scalar_sabs);
  free(scalar_trgsw_keys);
  free(scalar_keys);
  free_pvmtmlwe_key(pvw_key);
  free_trlwe_key(packing_key);
  free_trlwe_key(input_key);
}

void test_mat_trgsw_kernel(){
  bool pass = true;
  pass &= check_mat_trgsw_identity_lane(1);
  pass &= check_mat_trgsw_identity_lane(2);
  pass &= check_mat_trgsw_identity_lane(4);
  pass &= check_mat_trgsw_scalar_equivalence();
  pass &= check_pvw_cmux_ncmux_lane_equivalence(1);
  pass &= check_pvw_cmux_ncmux_lane_equivalence(2);
  pass &= check_pvw_cmux_ncmux_lane_equivalence(4);
  pass &= check_pvw_rgsw_monomial_lane_equivalence(1);
  pass &= check_pvw_rgsw_monomial_lane_equivalence(2);
  pass &= check_pvw_rgsw_monomial_lane_equivalence(4);
  printf("MAT_TRGSW/PVW staged kernel test: %s\n", pass ? "Pass" : "Fail");
  if(!pass) exit(1);

  bench_mat_trgsw_kernel_lane(1);
  bench_mat_trgsw_kernel_lane(2);
  bench_mat_trgsw_kernel_lane(4);
  bench_mat_trgsw_vs_scalar_lane(1);
  bench_mat_trgsw_vs_scalar_lane(2);
  bench_mat_trgsw_vs_scalar_lane(4);
  bench_mat_trgsw_vs_scalar_lane_full(1);
  bench_mat_trgsw_vs_scalar_lane_full(2);
  bench_mat_trgsw_vs_scalar_lane_full(4);
  bench_external_product_phase_breakdown(1);
  bench_external_product_phase_breakdown(2);
  bench_external_product_phase_breakdown(4);
}

void test_mat_trgsw_rgt4_kernel(){
  bool pass = true;
  pass &= check_mat_trgsw_identity_lane(6);
  pass &= check_mat_trgsw_identity_lane(8);
  printf("MAT_TRGSW/PVW r>4 kernel test: %s\n", pass ? "Pass" : "Fail");
  if(!pass) exit(1);

  bench_mat_trgsw_kernel_lane(6);
  bench_mat_trgsw_kernel_lane(8);
  bench_mat_trgsw_vs_scalar_lane(6);
  bench_mat_trgsw_vs_scalar_lane(8);
  bench_mat_trgsw_vs_scalar_lane_full(6);
  bench_mat_trgsw_vs_scalar_lane_full(8);
  bench_external_product_phase_breakdown(6);
  bench_external_product_phase_breakdown(8);
}
#endif

int main(int argc, char const *argv[])
{
#if defined(SAB_PVW_TARGET_TEST)
  test_sab_pvw_target_full();
#elif defined(SAB_PVW_RESOURCE_TEST)
  test_sab_pvw_resource();
#elif defined(SAB_PVW_NOISE_TEST)
  test_sab_pvw_noise();
#elif defined(SAB_PVW_STAGE_NOISE_TEST)
  test_sab_pvw_stage_noise();
#elif defined(SAB_PVW_BENCH)
  test_sab_pvw_target_bench();
#elif defined(SAB_PVW_RGT4_KERNEL_TEST)
  test_mat_trgsw_rgt4_kernel();
#elif defined(SAB_PVW_KERNEL_TEST)
  test_mat_trgsw_kernel();
#elif defined(SAB_MICROBENCH)
  test_sab_microbench();
#elif defined(TERNARY)
  test_sab_tern();
#elif defined(ARBITRARY)
  test_sab_arbitrary();
#else
  test_sab();
#endif
  return 0;
}
