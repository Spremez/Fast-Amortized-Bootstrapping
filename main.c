#include <sab_b.h>
//#include <sab.h>
#include <benchmark_util.h>
#include <sab_profile.h>
#include <inttypes.h>

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

#if defined(SAB_PVW_KERNEL_TEST)
static TRLWE_Key trlwe_key_from_pvmtmlwe_lane(PVW_TMLWE_Key in, int lane){
  const int N = in->s[0][lane]->N;
  TRLWE_Key out = trlwe_alloc_key(N, in->k, in->sigma);
  for (size_t i = 0; i < in->k; i++){
    polynomial_copy_torus_polynomial(out->s[i], in->s[i][lane]);
    polynomial_copy_DFT_polynomial(out->s_dft[i], in->s_dft[i][lane]);
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

void test_mat_trgsw_kernel(){
  bool pass = true;
  pass &= check_mat_trgsw_identity_lane(1);
  pass &= check_mat_trgsw_identity_lane(2);
  pass &= check_mat_trgsw_identity_lane(4);
  pass &= check_mat_trgsw_scalar_equivalence();
  printf("MAT_TRGSW kernel test: %s\n", pass ? "Pass" : "Fail");
  if(!pass) exit(1);

  bench_mat_trgsw_kernel_lane(1);
  bench_mat_trgsw_kernel_lane(2);
  bench_mat_trgsw_kernel_lane(4);
}
#endif

int main(int argc, char const *argv[])
{
#if defined(SAB_PVW_KERNEL_TEST)
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
