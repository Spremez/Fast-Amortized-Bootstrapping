#pragma once
#ifdef __cplusplus
extern "C" {
#endif
#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <assert.h>
#include <string.h>
#include <stdbool.h>

#ifndef PORTABLE_BUILD
#include <x86intrin.h>
#define AVX2_OPT
#endif

// Optimizations
// key-switching on-the-fly random

/* Torus */
#ifdef TORUS32
typedef uint32_t Torus;
#undef USE_COMPRESSED_TRLWE
#else
typedef uint64_t Torus;
#endif
typedef int16_t Binary;

/* Polynomials */
typedef struct _TorusPolynomial {
  Torus * coeffs;
  int N;
} * TorusPolynomial;

typedef struct _DFT_Polynomial {
  double * coeffs;
  int N;
} * DFT_Polynomial;

typedef struct _BinaryPolynomial {
  Binary * coeffs;
  int N;
} * BinaryPolynomial;

typedef TorusPolynomial IntPolynomial;
typedef Torus Integer;

/* TLWE */
typedef struct _TLWE {
  Torus * a, b;
  int n;
} * TLWE;

typedef struct _TLWE_Key{
  Integer * s;
  int n;
  double sigma;
} * TLWE_Key;

typedef struct _TLWE_KS_Key{
  TLWE *** s;
  int base_bit, t, n;
} * TLWE_KS_Key;

typedef struct _TLWE_KS_Key_m{
  TLWE ** s;
  int base_bit, t, n;
} * TLWE_KS_Key_m;

/* PVWTLWE */
typedef struct _PVW_TLWE {
  Torus * a, * b;
  int n,r;
} * PVW_TLWE;

typedef struct _PVW_TLWE_Key{
  Integer ** s;
  int n,r;
  double sigma;
} * PVW_TLWE_Key;

typedef struct _PVW_TLWE_KS_Key{
  PVW_TLWE *** s;
  int base_bit, t, n,r;
} * PVW_TLWE_KS_Key;

typedef struct _PVW_TLWE_KS_Key_m{
  PVW_TLWE ** s;
  int base_bit, t, n;
} * PVW_TLWE_KS_Key_m;

/* TRLWE */
typedef struct _TRLWE{
  TorusPolynomial * a, b;
  int k;
} * TRLWE;

typedef struct _TRLWE_DFT{
  DFT_Polynomial * a, b;
  int k;
} * TRLWE_DFT;

typedef struct _TRLWE_Key{
  IntPolynomial * s;
  DFT_Polynomial * s_dft;
  int k;
  double sigma;
} * TRLWE_Key;

typedef struct _TRLWE_KS_Key {
  TRLWE_DFT ** s;
  int base_bit, t, k;
} * TRLWE_KS_Key;

typedef struct _LUT_Packing_KS_Key {
  TRLWE **** s;
  int base_bit, t, torus_base, n;
} * LUT_Packing_KS_Key;

typedef struct _Generic_KS_Key {
  TRLWE *** s;
  int base_bit, t, n, include_b;
} * Generic_KS_Key;

/* PVW_TMLWE */
typedef struct _PVW_TMLWE{
  TorusPolynomial * a, * b;
  int r;
  int k;
} * PVW_TMLWE;

typedef struct _PVW_TMLWE_DFT{
  DFT_Polynomial * a, * b;
  int k,r;
} * PVW_TMLWE_DFT;

typedef struct _PVW_TMLWE_Key{
  IntPolynomial ** s;
  DFT_Polynomial ** s_dft;
  int k,r;
  double sigma;
} * PVW_TMLWE_Key;

typedef struct _PVW_TMLWE_KS_Key {
  PVW_TMLWE_DFT ** s;
  int base_bit, t, k;
} * PVW_TMLWE_KS_Key;

typedef struct _PVW_LUT_Packing_KS_Key {
  PVW_TMLWE **** s;
  int base_bit, t, torus_base, n;
} * PVW_LUT_Packing_KS_Key;

typedef struct _PVW_Generic_KS_Key {
  PVW_TMLWE *** s;
  int base_bit, t, n, include_b;
} * PVW_Generic_KS_Key;


/* TRGSW */
typedef struct _TRGSW {
  TRLWE * samples;
  int l, Bg_bit;
} * TRGSW;

typedef struct _TRGSW_DFT{
  TRLWE_DFT * samples;
  int l, Bg_bit;
} * TRGSW_DFT;

typedef struct _TRGSW_Key{
  TRLWE_Key trlwe_key;
  int l, Bg_bit;
} * TRGSW_Key;

/* MAT_TRGSW */
typedef struct _MAT_TRGSW {
  PVW_TMLWE * samples;
  int T,Q;
} * MAT_TRGSW;

typedef struct _MAT_TRGSW_DFT{
  PVW_TMLWE_DFT * samples;
  int T,Q;
} * MAT_TRGSW_DFT;

typedef struct _MAT_TRGSW_Key{
  PVW_TMLWE_Key trlwe_key;
  int T,Q;
} * MAT_TRGSW_Key;

typedef struct _MAT_TRGSW_MUL_SCRATCH{
  TorusPolynomial * dec;
  DFT_Polynomial * dec_dft;
  int rows;
} * MAT_TRGSW_MUL_SCRATCH;

typedef struct _MAT_TRGSW_COMPACT_DFT{
  DFT_Polynomial * shared_a, * shared_b;
  DFT_Polynomial * body_a, * body_b;
  int T,Q,k,r,N;
} * MAT_TRGSW_COMPACT_DFT;

typedef struct _MAT_TRGSW_COMPACT_OUTPUT_DFT{
  DFT_Polynomial * a, * b;
  int r,N;
} * MAT_TRGSW_COMPACT_OUTPUT_DFT;

typedef struct _MAT_TRGSW_COMPACT_MUL_SCRATCH{
  TorusPolynomial dec_shared, dec_body;
  DFT_Polynomial dec_shared_dft, dec_body_dft;
  int N;
} * MAT_TRGSW_COMPACT_MUL_SCRATCH;

/* Registers */

typedef struct _TRGSW_REG{
  TRGSW_DFT positive, negative;
} * TRGSW_REG;

/* MAT_TRGSW Registers */

typedef struct _MAT_TRGSW_REG{
  MAT_TRGSW_DFT positive, negative; 
} * MAT_TRGSW_REG;

/* Bootstrap */

typedef struct _Bootstrap_Key{
  TRGSW_DFT * s;
  TRGSW * su;
  int n, k, N, Bg_bit, l, unfolding;
} * Bootstrap_Key;

typedef struct _Bootstrap_GA_Key{
  TRGSW_DFT * s;
  TRGSW * su;
  TRLWE_KS_Key * ak;
  int n, k, N, Bg_bit, l, unfolding;
} * Bootstrap_GA_Key;

/* BATCH_Bootstrap */

typedef struct _BATCH_Bootstrap_Key{
  TRGSW_DFT * s;
  TRGSW * su;
  int n, k, N, Bg_bit, l, unfolding;
} * BATCH_Bootstrap_Key;

typedef struct _BATCH_Bootstrap_GA_Key{
  TRGSW_DFT * s;
  TRGSW * su;
  TRLWE_KS_Key * ak;
  int n, k, N, Bg_bit, l, unfolding;
} * BATCH_Bootstrap_GA_Key;

/* Functions */

/* Torus */
double torus2double(Torus x);
Torus double2torus(double x);
uint64_t torus2int(Torus x, int log_scale);
Torus int2torus(uint64_t x, int log_scale);

/* util */
uint16_t inverse_mod_2N(uint16_t x, uint16_t N);



/* Functions */

/* Polynomials */ 
void polynomial_zero_torus_polynomial(TorusPolynomial p);
TorusPolynomial polynomial_new_torus_polynomial(int N);
TorusPolynomial * polynomial_new_array_of_torus_polynomials(int N, int size);
DFT_Polynomial polynomial_new_DFT_polynomial(int N);
DFT_Polynomial * polynomial_new_array_of_polynomials_DFT(int N, int size);
BinaryPolynomial polynomial_new_binary_polynomial(int N);
void polynomial_decompose(TorusPolynomial * out, TorusPolynomial in, int Bg_bit, int l);
void polynomial_torus_scale(TorusPolynomial out, TorusPolynomial in, int log_scale);
void polynomial_add_torus_polynomials(TorusPolynomial out, TorusPolynomial in1, TorusPolynomial in2);
void polynomial_addto_torus_polynomial(TorusPolynomial out, TorusPolynomial in);
void polynomial_sub_torus_polynomials(TorusPolynomial out, TorusPolynomial in1, TorusPolynomial in2);
void polynomial_subto_torus_polynomial(TorusPolynomial out, TorusPolynomial in);
void torus_polynomial_mul_by_xai(TorusPolynomial out, TorusPolynomial in, int a);
void torus_polynomial_mul_by_xai_addto(TorusPolynomial out, TorusPolynomial in, int a);
void torus_polynomial_mul_by_xai_minus_1(TorusPolynomial out, TorusPolynomial in, int a);
void polynomial_naive_mul_binary(BinaryPolynomial out, BinaryPolynomial in1, BinaryPolynomial in2);
void polynomial_naive_mul_torus(TorusPolynomial out, TorusPolynomial in1, TorusPolynomial in2);
void polynomial_mul_torus(TorusPolynomial out, TorusPolynomial in1, TorusPolynomial in2);
void polynomial_mul_addto_torus(TorusPolynomial out, TorusPolynomial in1, TorusPolynomial in2);
void polynomial_naive_mul_addto_torus(TorusPolynomial out, TorusPolynomial in1, TorusPolynomial in2);
void polynomial_naive_mul_addto_torus_binary(TorusPolynomial out, TorusPolynomial in1, BinaryPolynomial in2);
void polynomial_DFT_to_torus(TorusPolynomial out, const DFT_Polynomial in);
void polynomial_DFT_to_torus_add(TorusPolynomial out, const DFT_Polynomial in,
    TorusPolynomial addend);
void polynomial_torus_to_DFT(DFT_Polynomial out, TorusPolynomial in);
void polynomial_torus_to_DFT_array(DFT_Polynomial * out,
    TorusPolynomial * in, int rows);
void polynomial_mul_DFT(DFT_Polynomial out, DFT_Polynomial in1, DFT_Polynomial in2);
void polynomial_mul_addto_DFT(DFT_Polynomial out, DFT_Polynomial in1, DFT_Polynomial in2);
void polynomial_sub_DFT_polynomials(DFT_Polynomial out, DFT_Polynomial in1, DFT_Polynomial in2);
void polynomial_copy_torus_polynomial(TorusPolynomial out, TorusPolynomial in);
void polynomial_negate_torus_polynomial(TorusPolynomial out, TorusPolynomial in);
void polynomial_copy_DFT_polynomial(DFT_Polynomial out, DFT_Polynomial in);
void free_polynomial(void * p);
void free_DFT_polynomial(DFT_Polynomial p);
void free_array_of_polynomials(void * p, int size);
void init_fft(int N);
void polynomial_full_mul_with_scale(TorusPolynomial out, TorusPolynomial in1, TorusPolynomial in2, int bit_size, int scale_bit);
void polynomial_permute(TorusPolynomial out, TorusPolynomial in, uint64_t gen);
void polynomial_add_DFT_polynomials(DFT_Polynomial out, DFT_Polynomial in1, DFT_Polynomial in2);
void polynomial_decompose_i(TorusPolynomial out, TorusPolynomial in, int Bg_bit, int l, int i);
void polynomial_torus_scale2(TorusPolynomial out, TorusPolynomial in, uint64_t scale);
void polynomial_scale_and_add_DFT_polynomials(DFT_Polynomial out, DFT_Polynomial in1, DFT_Polynomial in2, uint64_t scale);

/* TLWE */
TLWE_Key tlwe_alloc_key(int n, double sigma);
TLWE_Key tlwe_new_binary_key(int n, double sigma);
TLWE_Key tlwe_new_bounded_key(int n, uint64_t bound, double sigma);
TLWE_Key tlwe_load_new_key(FILE * fd);
TLWE_KS_Key tlwe_load_new_KS_key(FILE * fd);
void tlwe_save_KS_key(FILE * fd, TLWE_KS_Key key);
TLWE tlwe_alloc_sample(int n);
TLWE * tlwe_alloc_sample_array(int count, int n);
void tlwe_save_key(FILE * fd, TLWE_Key key);
TLWE tlwe_new_noiseless_trivial_sample(Torus m, int n);
void tlwe_noiseless_trivial_sample(TLWE out, Torus m);
void tlwe_sample(TLWE out, Torus m, TLWE_Key key);
void tlwe_copy(TLWE out, TLWE in);
TLWE tlwe_new_sample(Torus m, TLWE_Key key);
TLWE tlwe_load_new_sample(FILE * fd, int n);
void tlwe_load_sample(FILE * fd, TLWE c);
void tlwe_save_sample(FILE * fd, TLWE c);
TRLWE_DFT trlwe_load_new_DFT_sample(FILE * fd, int k, int N);
void trlwe_save_DFT_sample(FILE * fd, TRLWE_DFT c);
Torus tlwe_phase(TLWE c, TLWE_Key key);
void tlwe_add(TLWE out, TLWE in1, TLWE in2);
void tlwe_addto(TLWE out, TLWE in);
void tlwe_scale(TLWE out, TLWE in1, Torus in2);
void tlwe_scale_addto(TLWE out, TLWE in1, Torus in2);
void tlwe_sub(TLWE out, TLWE in1, TLWE in2);
void tlwe_subto(TLWE out, TLWE in);
void tlwe_negate(TLWE out, TLWE in);
TLWE_KS_Key tlwe_new_KS_key(TLWE_Key out_key, TLWE_Key in_key, int t, int base_bit);
void tlwe_keyswitch(TLWE out, TLWE in, TLWE_KS_Key ks_key);
void free_tlwe(TLWE p);
void free_tlwe_array(TLWE * p, int count);
void free_tlwe_key(TLWE_Key key);
void free_tlwe_ks_key(TLWE_KS_Key key);
void tlwe_mul(TLWE out, TLWE in1, TLWE in2, int delta, Generic_KS_Key ksk, TRLWE_KS_Key rlk);
void tlwe_scale_subto(TLWE out, TLWE in1, Torus in2);
TLWE_KS_Key_m tlwe_new_KS_key_no_precomp(TLWE_Key out_key, TLWE_Key in_key, int t, int base_bit);
void tlwe_keyswitch_no_precomp(TLWE out, TLWE in, TLWE_KS_Key_m ks_key);



/* TRLWE */
TRLWE_Key trlwe_alloc_key(int N, int k, double sigma);
TRLWE_Key trlwe_new_binary_key(int N, int k, double sigma);
TRLWE_Key trlwe_new_ternary_key(int N, int k, int h, double sigma);
TRLWE_Key trlwe_new_sparse_binary_key(int N, int k, int h, double sigma);
TRLWE_Key trlwe_new_gaussian_key(int N, int k, double key_sigma, double noise_sigma);
TRLWE_Key trlwe_new_bounded_key(int N, int k, uint64_t bound, double sigma);
TRLWE_Key trlwe_load_new_key(FILE * fd);
void trlwe_save_key(FILE * fd, TRLWE_Key key);
TRLWE trlwe_alloc_new_sample(int k, int N);
TRLWE * trlwe_alloc_new_sample_array(int count, int k, int N);
TRLWE_DFT * trlwe_alloc_new_DFT_sample_array(int count, int k, int N);
TRLWE trlwe_load_new_sample(FILE * fd, int k, int N);
void trlwe_load_sample(FILE * fd, TRLWE c);
void trlwe_save_sample(FILE * fd, TRLWE c);
TRLWE trlwe_alloc_new_sample(int k, int N);
TRLWE_DFT trlwe_alloc_new_DFT_sample(int k, int N);
void trlwe_load_DFT_sample(FILE * fd, TRLWE_DFT c);
TRLWE trlwe_new_noiseless_trivial_sample(TorusPolynomial m, int k, int N);
void trlwe_noiseless_trivial_sample(TRLWE out, TorusPolynomial m);
TRLWE trlwe_new_sample(TorusPolynomial m, TRLWE_Key key);
void trlwe_sample(TRLWE out, TorusPolynomial m, TRLWE_Key key);
void trlwe_phase(TorusPolynomial out, TRLWE in, TRLWE_Key key);
void trlwe_DFT_phase(TorusPolynomial out, TRLWE_DFT in, TRLWE_Key key);
void trlwe_from_DFT(TRLWE out, TRLWE_DFT in);
void trlwe_to_DFT(TRLWE_DFT out, TRLWE in);
void trlwe_decompose(TorusPolynomial * out, TRLWE in, int Bg_bit, int l);
void trlwe_add(TRLWE out, TRLWE in1, TRLWE in2);
void trlwe_addto(TRLWE out, TRLWE in);
void trlwe_sub(TRLWE out, TRLWE in1, TRLWE in2);
void trlwe_DFT_sub(TRLWE_DFT out, TRLWE_DFT in1,  TRLWE_DFT in2);
void trgsw_DFT_add(TRGSW_DFT out, TRGSW_DFT in1, TRGSW_DFT in2);
void trlwe_subto(TRLWE out, TRLWE in);
void trlwe_DFT_mul_by_polynomial(TRLWE_DFT out, TRLWE_DFT in, DFT_Polynomial in2);
void trlwe_DFT_mul_addto_by_polynomial(TRLWE_DFT out, TRLWE_DFT in, DFT_Polynomial in2);
void trlwe_mul_by_xai(TRLWE out, TRLWE in, int a);
void trlwe_mul_by_xai_addto(TRLWE out, TRLWE in, int a);
void trlwe_mul_by_xai_minus_1(TRLWE out, TRLWE in, int a);
void trlwe_extract_tlwe(TLWE out, TRLWE in, int idx);
void trlwe_extract_tlwe_key(TLWE_Key out, TRLWE_Key in);
void trlwe_mv_extract_tlwe(TLWE * out, TRLWE in, int amount);
void trlwe_mv_extract_tlwe_scaling(TLWE out, TRLWE in, int scale);
void trlwe_mv_extract_tlwe_scaling_addto(TLWE out, TRLWE in, int scale);
void trlwe_mv_extract_tlwe_scaling_subto(TLWE out, TRLWE in, int scale);
void trlwe_copy(TRLWE out, TRLWE in);
void trlwe_negate(TRLWE out, TRLWE in);
void trlwe_DFT_copy(TRLWE_DFT out, TRLWE_DFT in);
void free_trlwe(void * p_v);
void free_trlwe_array(void * p_v, int count);
void free_trlwe_key(TRLWE_Key key);
void trlwe_DFT_add(TRLWE_DFT out, TRLWE_DFT in1,  TRLWE_DFT in2);
void trlwe_DFT_addto(TRLWE_DFT out, TRLWE_DFT in);
void trlwe_noiseless_trivial_DFT_sample(TRLWE_DFT out, DFT_Polynomial m);
TRLWE_DFT trlwe_new_noiseless_trivial_DFT_sample(DFT_Polynomial m, int k, int N);
void trlwe_tensor_prod(TRLWE out, TRLWE in1, TRLWE in2, int delta, TRLWE_KS_Key rl_key);
void trlwe_tensor_prod_FFT(TRLWE out, TRLWE in1, TRLWE in2, int precision, TRLWE_KS_Key rl_key);
void trlwe_torus_packing_many_LUT(TRLWE out, Torus * in, int lut_size, int n_luts);
void trlwe_eval_automorphism(TRLWE out, TRLWE in, uint64_t gen, TRLWE_KS_Key ks_key);
void trlwe_extract_tlwe_addto(TLWE out, TRLWE in, int idx);
void trlwe_extract_tlwe_subto(TLWE out, TRLWE in, int idx);
TRLWE_Key trlwe_new_sparse_gaussian_key(int N, int k, int h, double key_sigma, double noise_sigma);
TRLWE_Key trlwe_new_sparse_generic_key(int N, int k, int h, uint64_t key_bound, double noise_sigma);

/* TRLWE Compressed */
TRLWE trlwe_new_compressed_sample(TorusPolynomial m, TRLWE_Key key);
TRLWE trlwe_load_new_compressed_sample(FILE * fd, int k, int N);
void trlwe_load_compressed_sample(FILE * fd, TRLWE c);
void trlwe_save_compressed_sample(FILE * fd, TRLWE c);
void trlwe_compressed_subto(TRLWE out, TRLWE in);
void trlwe_compressed_DFT_sample(TRLWE_DFT out, TorusPolynomial m, TRLWE_Key key);
TRLWE_DFT trlwe_new_compressed_DFT_sample(TorusPolynomial m, TRLWE_Key key);
void trlwe_compressed_DFT_mul_addto(TRLWE_DFT out, DFT_Polynomial in1, TRLWE_DFT in2);


/* TRGSW */
TRGSW_Key trgsw_new_key(TRLWE_Key trlwe_key, int l, int Bg_bit);
void trgsw_save_key(FILE * fd, TRGSW_Key key);
TRGSW_Key trgsw_load_new_key(FILE * fd);
TRGSW trgsw_alloc_new_sample(int l, int Bg_bit, int k, int N);
TRGSW * trgsw_alloc_new_sample_array(int count, int l, int Bg_bit, int k, int N);
TRGSW_DFT trgsw_alloc_new_DFT_sample(int l, int Bg_bit, int k, int N);
TRGSW_DFT * trgsw_alloc_new_DFT_sample_array(int count, int l, int Bg_bit, int k, int N);
TRGSW trgsw_new_noiseless_trivial_sample(Torus m, int l, int Bg_bit, int k, int N);
void trgsw_noiseless_trivial_sample(TRGSW out, Torus m, int l, int Bg_bit, int k, int N);
TRGSW trgsw_new_monomial_sample(int64_t m, int e, TRGSW_Key key);
void trgsw_monomial_sample(TRGSW out, int64_t m, int e, TRGSW_Key key);
void trgsw_monomial_DFT_sample(TRGSW_DFT out, int64_t m, int e, TRGSW_Key key);
TRGSW trgsw_new_sample(Torus m, TRGSW_Key key);
TRGSW trgsw_new_exp_sample(int e, TRGSW_Key key);
TRGSW trgsw_load_new_sample(FILE * fd, int l, int Bg_bit, int k, int N);
void trgsw_load_sample(FILE * fd, TRGSW c);
void trgsw_load_DFT_sample(FILE * fd, TRGSW_DFT out);
void trgsw_save_DFT_sample(FILE * fd, TRGSW_DFT c);
TRGSW_DFT trgsw_load_new_DFT_sample(FILE * fd, int l, int Bg_bit, int k, int N);
void trgsw_save_sample(FILE * fd, TRGSW c);
void trgsw_sub(TRGSW out, TRGSW in1, TRGSW in2);
void trgsw_add(TRGSW out, TRGSW in1, TRGSW in2);
void trgsw_DFT_sub(TRGSW_DFT out, TRGSW_DFT in1, TRGSW_DFT in2);
void trgsw_addto(TRGSW out, TRGSW in);
void trgsw_mul_by_xai(TRGSW out, TRGSW in, int a);
void trgsw_mul_by_xai_addto(TRGSW out, TRGSW in, int a);
void trgsw_mul_by_xai_minus_1(TRGSW out, TRGSW in, int a);
void trgsw_to_DFT(TRGSW_DFT out, TRGSW in);
void trgsw_from_DFT(TRGSW out, TRGSW_DFT in);
void trgsw_mul_trlwe_DFT(TRLWE_DFT out, TRLWE in1, TRGSW_DFT in2);
void trgsw_mul_DFT2(TRGSW_DFT out, TRGSW_DFT in1, TRGSW_DFT in2);
void trgsw_mul_DFT(TRGSW_DFT out, TRGSW in1, TRGSW_DFT in2);
void trgsw_naive_mul_trlwe(TRLWE out, TRLWE in1, TRGSW in2);
void trgsw_naive_mul(TRGSW out, TRGSW in1, TRGSW in2);
void trgsw_copy(TRGSW out, TRGSW in);
void trgsw_DFT_copy(TRGSW_DFT out, TRGSW_DFT in);
void free_trgsw(void * p);
void free_trgsw_array(void * p_v, int count);
void free_trgsw_key(TRGSW_Key key);
void trgsw_mul_trlwe_DFT_prefetch(TRLWE_DFT out, TRLWE in1, TRGSW_DFT in2);
void trgsw_DFT_mul_addto_by_polynomial(TRGSW_DFT out, TRGSW_DFT in1, DFT_Polynomial in2);

uint64_t _debug_trgsw_decrypt_exp_sample(TRGSW c, TRGSW_Key key);
uint64_t _debug_trgsw_decrypt_exp_DFT_sample(TRGSW_DFT c, TRGSW_Key key);

/* Registers */
TRGSW_REG trgsw_reg_alloc(int l, int Bg_bit, int k, int N);
TRGSW_REG * trgsw_reg_alloc_array(int count, int l, int Bg_bit, int k, int N);
void trgsw_reg_sample(TRGSW_REG out,  Torus m, TRGSW_Key key);
void trgsw_reg_copy(TRGSW_REG out, TRGSW_REG in);
void trgsw_reg_add(TRGSW_REG out, TRGSW_REG in1, TRGSW_REG in2);
void trgsw_reg_negate(TRGSW_REG reg);
void trgsw_reg_sub(TRGSW_REG out, TRGSW_REG in1, TRGSW_REG in2);
void trgsw_reg_subto(TRGSW_REG out, TRGSW_REG in);
void trgsw_reg_addto(TRGSW_REG out, TRGSW_REG in1);
void free_trgsw_reg(TRGSW_REG p);
void free_trgsw_reg_array(TRGSW_REG * p, int count);

/* Key Switch */
TRLWE_KS_Key trlwe_new_KS_key(TRLWE_Key out_key, TRLWE_Key in_key, int t, int base_bit);
void trlwe_keyswitch(TRLWE out, TRLWE in, TRLWE_KS_Key ks_key);
void free_trlwe_ks_key(TRLWE_KS_Key key);
LUT_Packing_KS_Key trlwe_new_packing_KS_key(TRLWE_Key out_key, TLWE_Key in_key, int t, int base_bit, int torus_base);
void trlwe_packing_keyswitch(TRLWE out, TLWE * in, LUT_Packing_KS_Key ks_key);
LUT_Packing_KS_Key trlwe_load_new_packing_KS_key(FILE * fd);
void trlwe_save_packing_KS_key(FILE * fd, LUT_Packing_KS_Key key);
void trlwe_torus_packing(TRLWE out, Torus * in, int size);
void trlwe_LUT_packing(TRLWE out, uint64_t * in, uint64_t in_prec, uint64_t out_prec);
void free_trlwe_packing_ks_key(LUT_Packing_KS_Key key);
TRLWE_KS_Key trlwe_new_RL_key(TRLWE_Key key, int t, int base_bit);
void trlwe_packing1_keyswitch(TRLWE out, TLWE in, Generic_KS_Key ks_key);
Generic_KS_Key trlwe_new_priv_SK_KS_key(TRLWE_Key out_key, TLWE_Key in_key, int t, int base_bit);
void trlwe_priv_keyswitch(TRLWE out, TLWE in, Generic_KS_Key ks_key);
void free_trlwe_generic_ks_key(Generic_KS_Key key);
Generic_KS_Key trlwe_new_packing1_KS_key(TRLWE_Key out_key, TLWE_Key in_key, int t, int base_bit);
TRLWE_KS_Key * trlwe_new_packing1_KS_key_CDKS21(TRLWE_Key out_key, TLWE_Key in_key, int t, int base_bit);
void trlwe_packing1_keyswitch_CDKS21(TRLWE out, TLWE in, TRLWE_KS_Key * ks_key);
TRLWE_KS_Key * trlwe_new_automorphism_KS_keyset(TRLWE_Key key, bool skip_even, int t, int base_bit);
TRLWE_KS_Key * trlwe_new_automorphism_KS_keyset_2(TRLWE_Key key, uint64_t * gens, uint64_t size, int t, int base_bit);
TRLWE_KS_Key trlwe_new_full_packing_KS_key(TRLWE_Key out_key, TLWE_Key in_key, int t, int base_bit);
void trlwe_full_packing_keyswitch(TRLWE out, TLWE * in, uint64_t size, TRLWE_KS_Key ks_key);
void trlwe_save_generic_ks_key(FILE * fd, Generic_KS_Key key);
Generic_KS_Key trlwe_load_new_generic_ks_key(FILE * fd);
TRLWE_KS_Key * trlwe_new_priv_KS_key(TRLWE_Key out_key, TRLWE_Key in_key, int t, int base_bit);
void trlwe_priv_keyswitch_2(TRLWE out, TRLWE in, TRLWE_KS_Key * ks_key);
void trlwe_save_KS_key(FILE * fd, TRLWE_KS_Key key);
TRLWE_KS_Key trlwe_load_new_KS_key(FILE * fd);




/* Bootstrap */
Bootstrap_Key new_bootstrap_key(TRGSW_Key out_key, TLWE_Key in_key, int unfolding);
void blind_rotate(TRLWE tv, Torus * a, TRGSW_DFT * s, int size);
void blind_rotate_unfolded(TRLWE tv, Torus * a, TRGSW * s, int size, int unfolding);
void functional_bootstrap_wo_extract(TRLWE out, TRLWE tv, TLWE in, Bootstrap_Key s, int torus_base);
void functional_bootstrap(TLWE out, TRLWE tv, TLWE in, Bootstrap_Key s, int torus_base);
void multivalue_bootstrap_phase1(TRLWE * out, TLWE in, Bootstrap_Key s, int torus_base);
void multivalue_bootstrap_phase2(TLWE out, int * in, TRLWE * rotated_tv, int torus_base, int log_torus_base);
void functional_bootstrap_trgsw_phase1(TRGSW_DFT out, TLWE in, Bootstrap_Key s, int torus_base);
void functional_bootstrap_trgsw_phase2(TLWE out, TRGSW_DFT in, TRLWE tv);
void free_bootstrap_key(Bootstrap_Key key);
void save_bootstrap_key(FILE * fd, Bootstrap_Key key);
Bootstrap_Key load_new_bootstrap_key(FILE * fd);
void circuit_bootstrap(TRGSW out, TLWE in, Bootstrap_Key key, Generic_KS_Key kska, Generic_KS_Key kskb);
void circuit_bootstrap_2(TRGSW out, TLWE in, Bootstrap_Key key, Generic_KS_Key kska, Generic_KS_Key kskb);
void circuit_bootstrap_3(TRGSW out, TLWE in, Bootstrap_Key key, TRLWE_KS_Key * kska, Generic_KS_Key kskb);
void public_mux(TRLWE out, TorusPolynomial p0, TorusPolynomial p1, TRLWE_DFT * selector, int l, int Bg_bit);
void multivalue_bootstrap_CLOT21(TLWE * out, TRLWE tv, TLWE in, Bootstrap_Key key, int torus_base, int n_luts);
void programmable_bootstrap(TLWE out, TRLWE tv, TLWE in, Bootstrap_Key key, int precision, int kappa, int theta);
void full_domain_functional_bootstrap(TLWE out, TRLWE tv, TLWE in, Bootstrap_Key key, TLWE_KS_Key tlwe_ksk, int precision);
void full_domain_functional_bootstrap_CLOT21(TLWE out, TRLWE tv[2], TLWE in, Bootstrap_Key key, Generic_KS_Key ksk, TRLWE_KS_Key rlk, int precision);
void full_domain_functional_bootstrap_CLOT21_2(TLWE out, Torus * tv, TLWE in, Bootstrap_Key key, Generic_KS_Key ksk, TRLWE_KS_Key rlk, int precision);
void full_domain_functional_bootstrap_KS21(TLWE out, TorusPolynomial tv, TLWE in, Bootstrap_Key key, Generic_KS_Key ksk, int torus_base);
void full_domain_functional_bootstrap_KS21_2(TLWE out, TorusPolynomial tv, TLWE in, Bootstrap_Key key, Generic_KS_Key ksk, int torus_base);
void multivalue_bootstrap_UBR_phase1(TRGSW_DFT * out, TLWE in, Bootstrap_Key key);
void multivalue_bootstrap_UBR_phase2(TLWE out, TRLWE tv, TLWE in, TRGSW_DFT * sa, Bootstrap_Key key, int torus_base);



/* Misc */ 
void generate_rnd_seed(uint64_t * p);
void generate_random_bytes(uint64_t amount, uint8_t * pointer);
void mosfhet_set_deterministic_seed(uint64_t seed);
double generate_normal_random(double sigma);
void generate_torus_normal_random_array(Torus * out, double sigma, int N);
void * safe_malloc(size_t size);
void * safe_aligned_malloc(size_t size);

// print
void print_trlwe_msg(TRLWE in, uint64_t prec, TRLWE_Key key);

// debug 
uint64_t _debug_trgsw_decrypt_exp_sample(TRGSW c, TRGSW_Key key);
uint64_t _debug_trgsw_decrypt_exp_DFT_sample(TRGSW_DFT c, TRGSW_Key key);
uint64_t _debug_trlwe_decrypt_exp_sample(TRLWE c, uint64_t prec, TRLWE_Key key);

/* Bootstrap using Galois Automorphisms */
Bootstrap_GA_Key new_bootstrap_key_ga(TRGSW_Key out_key, TLWE_Key in_key);
void blind_rotate_ga(TRLWE tv, Torus * a, TRGSW_DFT * s, TRLWE_KS_Key * ak, int size);
void functional_bootstrap_wo_extract_ga(TRLWE out, TRLWE tv, TLWE in, Bootstrap_GA_Key key, int torus_base);
void functional_bootstrap_ga(TLWE out, TRLWE tv, TLWE in, Bootstrap_GA_Key key, int torus_base);
void free_bootstrap_key_ga(Bootstrap_GA_Key key);

/* PVW_TLWE */
PVW_TLWE pvwtlwe_alloc_sample(int n, int r);
PVW_TLWE * pvwtlwe_alloc_sample_array(int count, int n, int r);
PVW_TLWE pvwtlwe_new_noiseless_trivial_sample(Torus * m, int n, int r);
void pvwtlwe_noiseless_trivial_sample(PVW_TLWE out, Torus * m);
void free_pvwtlwe_array(PVW_TLWE * p, int count);
void free_pvwtlwe(PVW_TLWE p);
void pvwtlwe_save_sample(FILE * fd, PVW_TLWE c);
PVW_TLWE pvwtlwe_load_new_sample(FILE * fd, int n, int r);
void pvwtlwe_load_sample(FILE * fd, PVW_TLWE c);
PVW_TLWE_Key pvwtlwe_alloc_key(int n, int r, double sigma);
PVW_TLWE_Key pvwtlwe_new_binary_key(int n, int r, double sigma);
PVW_TLWE_Key pvwtlwe_new_bounded_key(int n, int r, uint64_t bound, double sigma);
void pvwtlwe_save_key(FILE * fd, PVW_TLWE_Key key);
PVW_TLWE_Key pvwtlwe_load_new_key(FILE * fd);
void free_pvwtlwe_key(PVW_TLWE_Key key);
void pvwtlwe_sample(PVW_TLWE out, Torus * m, PVW_TLWE_Key key);
void pvwtlwe_copy(PVW_TLWE out, PVW_TLWE in);
PVW_TLWE pvwtlwe_new_sample(Torus * m, PVW_TLWE_Key key);
void pvwtlwe_phase(Torus * out, PVW_TLWE c, PVW_TLWE_Key key);
void pvwtlwe_add(PVW_TLWE out, PVW_TLWE in1, PVW_TLWE in2);
void pvwtlwe_scale(PVW_TLWE out, PVW_TLWE in1, Torus in2);
void pvwtlwe_scale_addto(PVW_TLWE out, PVW_TLWE in1, Torus in2);
void pvwtlwe_scale_subto(PVW_TLWE out, PVW_TLWE in1, Torus in2);
void pvwtlwe_addto(PVW_TLWE out, PVW_TLWE in);
void pvwtlwe_sub(PVW_TLWE out, PVW_TLWE in1, PVW_TLWE in2);
void pvwtlwe_negate(PVW_TLWE out, PVW_TLWE in);
void pvwtlwe_subto(PVW_TLWE out, PVW_TLWE in);
PVW_TLWE_KS_Key pvwtlwe_new_KS_key(PVW_TLWE_Key out_key, PVW_TLWE_Key in_key, int t, int base_bit);
void free_pvwtlwe_ks_key(PVW_TLWE_KS_Key key);
PVW_TLWE_KS_Key pvwtlwe_load_new_KS_key(FILE * fd, int n_outkey, int r_outkey);
void pvwtlwe_save_KS_key(FILE * fd, PVW_TLWE_KS_Key key);
void pvwtlwe_keyswitch(PVW_TLWE out, PVW_TLWE in, PVW_TLWE_KS_Key ks_key);

/* PVW_TMLWE */
PVW_TMLWE pvmtmlwe_alloc_new_sample(int k, int r, int N);
PVW_TMLWE * pvmtmlwe_alloc_new_sample_array(int count, int k, int r, int N);
void pvmtmlwe_save_sample(FILE * fd, PVW_TMLWE c);
void pvmtmlwe_load_sample(FILE * fd, PVW_TMLWE c);
PVW_TMLWE pvmtmlwe_load_new_sample(FILE * fd, int k, int r, int N);
PVW_TMLWE_DFT * pvmtmlwe_alloc_new_DFT_sample_array(int count, int k, int r, int N);
PVW_TMLWE_DFT pvmtmlwe_alloc_new_DFT_sample(int k, int r, int N);
void pvmtmlwe_save_DFT_sample(FILE * fd, PVW_TMLWE_DFT c);
PVW_TMLWE_DFT pvmtmlwe_load_new_DFT_sample(FILE * fd, int k, int r, int N);
void pvmtmlwe_load_DFT_sample(FILE * fd, PVW_TMLWE_DFT c);
void free_pvmtmlwe(void * p_v);
void free_pvmtmlwe_DFT(void * p_v);
void free_pvmtmlwe_array(void * p_v, int count);
PVW_TMLWE_Key pvmtmlwe_alloc_key(int N, int k, int r, double sigma);
PVW_TMLWE_Key pvmtmlwe_new_bounded_key(int N, int k, int r, uint64_t bound, double sigma);
PVW_TMLWE_Key pvmtmlwe_new_binary_key(int N, int k, int r, double sigma);
void pvwtmlwe_gen_sparse_array(uint64_t * out, uint64_t size, uint64_t h, bool ternary, bool gaussian, double key_sigma);
PVW_TMLWE_Key pvmtmlwe_new_ternary_key(int N, int k, int r, int h, double sigma);
PVW_TMLWE_Key pvmtmlwe_new_sparse_binary_key(int N, int k, int r, int h, double sigma);
PVW_TMLWE_Key pvmtmlwe_new_sparse_gaussian_key(int N, int k, int r, int h, double key_sigma, double noise_sigma);
PVW_TMLWE_Key pvmtmlwe_new_sparse_generic_key(int N, int k, int r, int h, uint64_t key_bound, double noise_sigma);
PVW_TMLWE_Key pvmtmlwe_new_gaussian_key(int N, int k, int r, double key_sigma, double noise_sigma);
void pvmtmlwe_save_key(FILE * fd, PVW_TMLWE_Key key);
PVW_TMLWE_Key pvmtmlwe_load_new_key(FILE * fd);
void free_pvmtmlwe_key(PVW_TMLWE_Key key);
void pvmtmlwe_noiseless_trivial_sample(PVW_TMLWE out, TorusPolynomial * m);
PVW_TMLWE pvmtmlwe_new_noiseless_trivial_sample(TorusPolynomial * m, int k, int r, int N);
void pvmtmlwe_noiseless_trivial_DFT_sample(PVW_TMLWE_DFT out, DFT_Polynomial * m);
PVW_TMLWE_DFT pvmtmlwe_new_noiseless_trivial_DFT_sample(DFT_Polynomial * m, int k, int r, int N);
void pvmtmlwe_sample(PVW_TMLWE out, TorusPolynomial * m, PVW_TMLWE_Key key);
PVW_TMLWE pvmtmlwe_new_sample(TorusPolynomial * m, PVW_TMLWE_Key key);
void pvmtmlwe_phase(TorusPolynomial * out, PVW_TMLWE in, PVW_TMLWE_Key key);
void print_pvmtmlwe_msg(PVW_TMLWE in, uint64_t prec, PVW_TMLWE_Key key);
uint64_t _debug_pvmtmlwe_decrypt_exp_sample(PVW_TMLWE c, uint64_t prec, PVW_TMLWE_Key key);
void pvmtmlwe_DFT_phase(TorusPolynomial * out, PVW_TMLWE_DFT in, PVW_TMLWE_Key key);
void pvmtmlwe_add(PVW_TMLWE out, PVW_TMLWE in1, PVW_TMLWE in2);
void pvmtmlwe_copy(PVW_TMLWE out, PVW_TMLWE in);
void pvmtmlwe_negate(PVW_TMLWE out, PVW_TMLWE in);
void pvmtmlwe_DFT_copy(PVW_TMLWE_DFT out, PVW_TMLWE_DFT in);
void pvmtmlwe_addto(PVW_TMLWE out, PVW_TMLWE in);
void pvmtmlwe_DFT_add(PVW_TMLWE_DFT out, PVW_TMLWE_DFT in1, PVW_TMLWE_DFT in2);
void pvmtmlwe_DFT_sub(PVW_TMLWE_DFT out, PVW_TMLWE_DFT in1, PVW_TMLWE_DFT in2);
void pvmtmlwe_DFT_addto(PVW_TMLWE_DFT out, PVW_TMLWE_DFT in);
void pvmtmlwe_sub(PVW_TMLWE out, PVW_TMLWE in1, PVW_TMLWE in2);
void pvmtmlwe_subto(PVW_TMLWE out, PVW_TMLWE in);
void pvmtmlwe_DFT_mul_by_polynomial(PVW_TMLWE_DFT out, PVW_TMLWE_DFT in, DFT_Polynomial in2);
void pvmtmlwe_DFT_mul_addto_by_polynomial(PVW_TMLWE_DFT out, PVW_TMLWE_DFT in, DFT_Polynomial in2);
void pvmtmlwe_mul_by_xai(PVW_TMLWE out, PVW_TMLWE in, int a);
void pvmtmlwe_mul_by_xai_addto(PVW_TMLWE out, PVW_TMLWE in, int a);
void pvmtmlwe_mul_by_xai_minus_1(PVW_TMLWE out, PVW_TMLWE in, int a);
void pvmtmlwe_extract_pvmtlwe_key(PVW_TLWE_Key out, PVW_TMLWE_Key in);
void pvmtmlwe_extract_pvmtlwe(PVW_TLWE out, PVW_TMLWE in, int idx);
void pvmtmlwe_extract_pvmtlwe_addto(PVW_TLWE out, PVW_TMLWE in, int idx);
void pvmtmlwe_extract_pvmtlwe_subto(PVW_TLWE out, PVW_TMLWE in, int idx);
void pvmtmlwe_mv_extract_pvmtlwe(PVW_TLWE * out, PVW_TMLWE in, int amount);
void pvmtmlwe_mv_extract_pvmtlwe_scaling(PVW_TLWE out, PVW_TMLWE in, int scale);
void pvmtmlwe_mv_extract_pvmtlwe_scaling_addto(PVW_TLWE out, PVW_TMLWE in, int scale);
void pvmtmlwe_mv_extract_pvmtlwe_scaling_subto(PVW_TLWE out, PVW_TMLWE in, int scale);
void pvmtmlwe_to_DFT(PVW_TMLWE_DFT out, PVW_TMLWE in);
void pvmtmlwe_from_DFT(PVW_TMLWE out, PVW_TMLWE_DFT in);
void pvmtmlwe_from_DFT_add(PVW_TMLWE out, PVW_TMLWE_DFT in,
    PVW_TMLWE addend);
PVW_TMLWE_KS_Key pvmtmlwe_new_KS_key(PVW_TMLWE_Key out_key, PVW_TMLWE_Key in_key, int t, int base_bit);
PVW_TMLWE_KS_Key pvmtmlwe_new_automorphism_KS_key(PVW_TMLWE_Key key, uint64_t gen, int t, int base_bit);
void free_pvmtmlwe_ks_key(PVW_TMLWE_KS_Key key);
void pvmtmlwe_decompose(TorusPolynomial * out, PVW_TMLWE in, int Bg_bit, int l);
void pvmtmlwe_keyswitch(PVW_TMLWE out, PVW_TMLWE in, PVW_TMLWE_KS_Key ks_key);
void pvmtmlwe_torus_packing(PVW_TMLWE out, Torus ** in, int size);
void pvmtmlwe_LUT_packing(PVW_TMLWE out, uint64_t ** in, uint64_t in_prec, uint64_t out_prec);
void pvmtmlwe_torus_packing_many_LUT(PVW_TMLWE out, Torus ** in, int lut_size, int n_luts);
void pvmtmlwe_tensor_prod(PVW_TMLWE out, PVW_TMLWE in1, PVW_TMLWE in2, int precision, PVW_TMLWE_KS_Key rl_key);
void pvmtmlwe_tensor_prod_FFT(PVW_TMLWE out, PVW_TMLWE in1, PVW_TMLWE in2, int precision, PVW_TMLWE_KS_Key rl_key);
void pvmtmlwe_eval_automorphism(PVW_TMLWE out, PVW_TMLWE in, uint64_t gen, PVW_TMLWE_KS_Key ks_key);

/* MAT_TRGSW */
MAT_TRGSW_Key mat_trgsw_new_key(PVW_TMLWE_Key trlwe_key, int l, int Bg_bit);
void free_mat_trgsw_key(MAT_TRGSW_Key key);
MAT_TRGSW mat_trgsw_alloc_new_sample(int l, int Bg_bit, int k, int r, int N);
MAT_TRGSW_DFT mat_trgsw_alloc_new_DFT_sample(int l, int Bg_bit, int k, int r, int N);
void free_mat_trgsw(void * p_v);
void free_mat_trgsw_DFT(void * p_v);
void mat_trgsw_monomial_sample(MAT_TRGSW out, int64_t m, int e, MAT_TRGSW_Key key);
void mat_trgsw_to_DFT(MAT_TRGSW_DFT out, MAT_TRGSW in);
void mat_trgsw_monomial_DFT_sample(MAT_TRGSW_DFT out, int64_t m, int e, MAT_TRGSW_Key key);
MAT_TRGSW_MUL_SCRATCH mat_trgsw_alloc_mul_scratch(int rows, int N);
void free_mat_trgsw_mul_scratch(MAT_TRGSW_MUL_SCRATCH scratch);
void mat_trgsw_mul_pvmtmlwe_DFT(PVW_TMLWE_DFT out, PVW_TMLWE in, MAT_TRGSW_DFT selector, MAT_TRGSW_MUL_SCRATCH scratch);
void mat_trgsw_mul_pvmtmlwe_sub_DFT(PVW_TMLWE_DFT out, PVW_TMLWE in1,
    PVW_TMLWE in2, MAT_TRGSW_DFT selector, MAT_TRGSW_MUL_SCRATCH scratch);
MAT_TRGSW_COMPACT_DFT mat_trgsw_compact_alloc_new_DFT_sample(int l, int Bg_bit, int k, int r, int N);
void free_mat_trgsw_compact_DFT(void * p_v);
MAT_TRGSW_COMPACT_OUTPUT_DFT mat_trgsw_compact_alloc_new_output_DFT(int r, int N);
void free_mat_trgsw_compact_output_DFT(void * p_v);
int mat_trgsw_compact_set_row_from_torus(MAT_TRGSW_COMPACT_DFT out, int t, int lane,
    TorusPolynomial shared_a, TorusPolynomial shared_b,
    TorusPolynomial body_a, TorusPolynomial body_b);
MAT_TRGSW_COMPACT_MUL_SCRATCH mat_trgsw_compact_alloc_mul_scratch(int N);
void free_mat_trgsw_compact_mul_scratch(MAT_TRGSW_COMPACT_MUL_SCRATCH scratch);
void mat_trgsw_compact_mul_pvmtmlwe_DFT(MAT_TRGSW_COMPACT_OUTPUT_DFT out, PVW_TMLWE in,
    MAT_TRGSW_COMPACT_DFT selector, MAT_TRGSW_COMPACT_MUL_SCRATCH scratch);

#ifdef __cplusplus
}
#endif
