#include "mosfhet.h"

static int mat_trgsw_rows(int l, int k, int r){
  return l * (k + r);
}

static int mat_trgsw_sample_rows(MAT_TRGSW in){
  return mat_trgsw_rows(in->T, in->samples[0]->k, in->samples[0]->r);
}

static int mat_trgsw_DFT_sample_rows(MAT_TRGSW_DFT in){
  return mat_trgsw_rows(in->T, in->samples[0]->k, in->samples[0]->r);
}

MAT_TRGSW_Key mat_trgsw_new_key(PVW_TMLWE_Key trlwe_key, int l, int Bg_bit){
  MAT_TRGSW_Key res = (MAT_TRGSW_Key) safe_malloc(sizeof(*res));
  res->trlwe_key = trlwe_key;
  res->T = l;
  res->Q = Bg_bit;
  return res;
}

void free_mat_trgsw_key(MAT_TRGSW_Key key){
  free(key);
}

MAT_TRGSW mat_trgsw_alloc_new_sample(int l, int Bg_bit, int k, int r, int N){
  MAT_TRGSW res = (MAT_TRGSW) safe_malloc(sizeof(*res));
  const int rows = mat_trgsw_rows(l, k, r);
  res->samples = (PVW_TMLWE *) safe_malloc(sizeof(PVW_TMLWE) * rows);
  for (size_t i = 0; i < rows; i++){
    res->samples[i] = pvmtmlwe_alloc_new_sample(k, r, N);
  }
  res->T = l;
  res->Q = Bg_bit;
  return res;
}

MAT_TRGSW_DFT mat_trgsw_alloc_new_DFT_sample(int l, int Bg_bit, int k, int r, int N){
  MAT_TRGSW_DFT res = (MAT_TRGSW_DFT) safe_malloc(sizeof(*res));
  const int rows = mat_trgsw_rows(l, k, r);
  res->samples = (PVW_TMLWE_DFT *) safe_malloc(sizeof(PVW_TMLWE_DFT) * rows);
  for (size_t i = 0; i < rows; i++){
    res->samples[i] = pvmtmlwe_alloc_new_DFT_sample(k, r, N);
  }
  res->T = l;
  res->Q = Bg_bit;
  return res;
}

void free_mat_trgsw(void * p_v){
  MAT_TRGSW p = (MAT_TRGSW) p_v;
  const int rows = mat_trgsw_sample_rows(p);
  for (size_t i = 0; i < rows; i++){
    free_pvmtmlwe(p->samples[i]);
  }
  free(p->samples);
  free(p);
}

void free_mat_trgsw_DFT(void * p_v){
  MAT_TRGSW_DFT p = (MAT_TRGSW_DFT) p_v;
  const int rows = mat_trgsw_DFT_sample_rows(p);
  for (size_t i = 0; i < rows; i++){
    free_pvmtmlwe_DFT(p->samples[i]);
  }
  free(p->samples);
  free(p);
}

void mat_trgsw_monomial_sample(MAT_TRGSW out, int64_t m, int e, MAT_TRGSW_Key key){
  const int l = key->T;
  const int Bg_bit = key->Q;
  const int k = key->trlwe_key->k;
  const int r = key->trlwe_key->r;
  const int N = key->trlwe_key->s[0][0]->N;

  assert(out->T == l);
  assert(out->Q == Bg_bit);
  assert(out->samples[0]->k == k);
  assert(out->samples[0]->r == r);

  if(e & N) m *= -1;
  e &= (N - 1);

  const int rows = mat_trgsw_rows(l, k, r);
  for (size_t i = 0; i < rows; i++){
    pvmtmlwe_sample(out->samples[i], NULL, key->trlwe_key);
  }

  for (size_t i = 0; i < l; i++){
    const Torus h = 1ULL << (sizeof(Torus) * 8 - (i + 1) * Bg_bit);
    for (size_t j = 0; j < k; j++){
      out->samples[j * l + i]->a[j]->coeffs[e] += m * h;
    }
    for (size_t j = 0; j < r; j++){
      out->samples[(k + j) * l + i]->b[j]->coeffs[e] += m * h;
    }
  }
}

void mat_trgsw_to_DFT(MAT_TRGSW_DFT out, MAT_TRGSW in){
  assert(out->T == in->T);
  assert(out->Q == in->Q);
  assert(out->samples[0]->k == in->samples[0]->k);
  assert(out->samples[0]->r == in->samples[0]->r);

  const int rows = mat_trgsw_sample_rows(in);
  for (size_t i = 0; i < rows; i++){
    pvmtmlwe_to_DFT(out->samples[i], in->samples[i]);
  }
}

void mat_trgsw_monomial_DFT_sample(MAT_TRGSW_DFT out, int64_t m, int e, MAT_TRGSW_Key key){
  const int N = key->trlwe_key->s[0][0]->N;
  MAT_TRGSW tmp = mat_trgsw_alloc_new_sample(out->T, out->Q, out->samples[0]->k, out->samples[0]->r, N);
  mat_trgsw_monomial_sample(tmp, m, e, key);
  mat_trgsw_to_DFT(out, tmp);
  free_mat_trgsw(tmp);
}

MAT_TRGSW_MUL_SCRATCH mat_trgsw_alloc_mul_scratch(int rows, int N){
  MAT_TRGSW_MUL_SCRATCH res = (MAT_TRGSW_MUL_SCRATCH) safe_malloc(sizeof(*res));
  res->dec = polynomial_new_array_of_torus_polynomials(N, rows);
  res->dec_dft = polynomial_new_array_of_polynomials_DFT(N, rows);
  res->rows = rows;
  return res;
}

void free_mat_trgsw_mul_scratch(MAT_TRGSW_MUL_SCRATCH scratch){
  free_array_of_polynomials(scratch->dec, scratch->rows);
  for (size_t i = 0; i < scratch->rows; i++){
    free_DFT_polynomial(scratch->dec_dft[i]);
  }
  free(scratch->dec_dft);
  free(scratch);
}

#if defined(AVX512_OPT) && defined(MAT_TRGSW_AVX512_SMALLR_SPECIALIZED)
static inline void mat_avx512_complex_mul(__m512d dec_re, __m512d dec_im,
    __m512d sel_re, __m512d sel_im, __m512d * out_re, __m512d * out_im){
  *out_re = _mm512_fmsub_pd(dec_re, sel_re, _mm512_mul_pd(dec_im, sel_im));
  *out_im = _mm512_fmadd_pd(dec_re, sel_im, _mm512_mul_pd(dec_im, sel_re));
}

static inline void mat_avx512_complex_addmul(__m512d dec_re, __m512d dec_im,
    __m512d sel_re, __m512d sel_im, __m512d * acc_re, __m512d * acc_im){
  *acc_re = _mm512_fmadd_pd(dec_re, sel_re, *acc_re);
  *acc_re = _mm512_fnmadd_pd(dec_im, sel_im, *acc_re);
  *acc_im = _mm512_fmadd_pd(dec_im, sel_re, *acc_im);
  *acc_im = _mm512_fmadd_pd(dec_re, sel_im, *acc_im);
}

static void mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r2_avx512(
    PVW_TMLWE_DFT out, MAT_TRGSW_DFT selector, DFT_Polynomial * dec_dft){
  const int N = out->a[0]->N;
  const int vec_half = N / 16;
  __m512d * restrict out_a = (__m512d *) out->a[0]->coeffs;
  __m512d * restrict out_b0 = (__m512d *) out->b[0]->coeffs;
  __m512d * restrict out_b1 = (__m512d *) out->b[1]->coeffs;
  const __m512d * restrict dec0 = (const __m512d *) dec_dft[0]->coeffs;
  const __m512d * restrict dec1 = (const __m512d *) dec_dft[1]->coeffs;
  const __m512d * restrict dec2 = (const __m512d *) dec_dft[2]->coeffs;
  const __m512d * restrict sel0_a =
      (const __m512d *) selector->samples[0]->a[0]->coeffs;
  const __m512d * restrict sel0_b0 =
      (const __m512d *) selector->samples[0]->b[0]->coeffs;
  const __m512d * restrict sel0_b1 =
      (const __m512d *) selector->samples[0]->b[1]->coeffs;
  const __m512d * restrict sel1_a =
      (const __m512d *) selector->samples[1]->a[0]->coeffs;
  const __m512d * restrict sel1_b0 =
      (const __m512d *) selector->samples[1]->b[0]->coeffs;
  const __m512d * restrict sel1_b1 =
      (const __m512d *) selector->samples[1]->b[1]->coeffs;
  const __m512d * restrict sel2_a =
      (const __m512d *) selector->samples[2]->a[0]->coeffs;
  const __m512d * restrict sel2_b0 =
      (const __m512d *) selector->samples[2]->b[0]->coeffs;
  const __m512d * restrict sel2_b1 =
      (const __m512d *) selector->samples[2]->b[1]->coeffs;

  assert(out->k == 1);
  assert(out->r == 2);
  assert(selector->T == 1);

  for (int coeff = 0; coeff < vec_half; coeff++){
    __m512d dec_re = dec0[coeff];
    __m512d dec_im = dec0[coeff + vec_half];
    __m512d acc_a_re, acc_a_im, acc_b0_re, acc_b0_im, acc_b1_re, acc_b1_im;

    mat_avx512_complex_mul(dec_re, dec_im, sel0_a[coeff],
        sel0_a[coeff + vec_half], &acc_a_re, &acc_a_im);
    mat_avx512_complex_mul(dec_re, dec_im, sel0_b0[coeff],
        sel0_b0[coeff + vec_half], &acc_b0_re, &acc_b0_im);
    mat_avx512_complex_mul(dec_re, dec_im, sel0_b1[coeff],
        sel0_b1[coeff + vec_half], &acc_b1_re, &acc_b1_im);

    dec_re = dec1[coeff];
    dec_im = dec1[coeff + vec_half];
    mat_avx512_complex_addmul(dec_re, dec_im, sel1_a[coeff],
        sel1_a[coeff + vec_half], &acc_a_re, &acc_a_im);
    mat_avx512_complex_addmul(dec_re, dec_im, sel1_b0[coeff],
        sel1_b0[coeff + vec_half], &acc_b0_re, &acc_b0_im);
    mat_avx512_complex_addmul(dec_re, dec_im, sel1_b1[coeff],
        sel1_b1[coeff + vec_half], &acc_b1_re, &acc_b1_im);

    dec_re = dec2[coeff];
    dec_im = dec2[coeff + vec_half];
    mat_avx512_complex_addmul(dec_re, dec_im, sel2_a[coeff],
        sel2_a[coeff + vec_half], &acc_a_re, &acc_a_im);
    mat_avx512_complex_addmul(dec_re, dec_im, sel2_b0[coeff],
        sel2_b0[coeff + vec_half], &acc_b0_re, &acc_b0_im);
    mat_avx512_complex_addmul(dec_re, dec_im, sel2_b1[coeff],
        sel2_b1[coeff + vec_half], &acc_b1_re, &acc_b1_im);

    out_a[coeff] = acc_a_re;
    out_a[coeff + vec_half] = acc_a_im;
    out_b0[coeff] = acc_b0_re;
    out_b0[coeff + vec_half] = acc_b0_im;
    out_b1[coeff] = acc_b1_re;
    out_b1[coeff + vec_half] = acc_b1_im;
  }
}

static void mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r4_avx512(
    PVW_TMLWE_DFT out, MAT_TRGSW_DFT selector, DFT_Polynomial * dec_dft){
  const int N = out->a[0]->N;
  const int vec_half = N / 16;
  __m512d * out_a = (__m512d *) out->a[0]->coeffs;
  __m512d * out_b0 = (__m512d *) out->b[0]->coeffs;
  __m512d * out_b1 = (__m512d *) out->b[1]->coeffs;
  __m512d * out_b2 = (__m512d *) out->b[2]->coeffs;
  __m512d * out_b3 = (__m512d *) out->b[3]->coeffs;

  assert(out->k == 1);
  assert(out->r == 4);
  assert(selector->T == 1);

  for (int coeff = 0; coeff < vec_half; coeff++){
    __m512d * dec0 = (__m512d *) dec_dft[0]->coeffs;
    __m512d dec_re = dec0[coeff];
    __m512d dec_im = dec0[coeff + vec_half];
    __m512d * sel_a = (__m512d *) selector->samples[0]->a[0]->coeffs;
    __m512d * sel_b0 = (__m512d *) selector->samples[0]->b[0]->coeffs;
    __m512d * sel_b1 = (__m512d *) selector->samples[0]->b[1]->coeffs;
    __m512d * sel_b2 = (__m512d *) selector->samples[0]->b[2]->coeffs;
    __m512d * sel_b3 = (__m512d *) selector->samples[0]->b[3]->coeffs;
    __m512d acc_a_re, acc_a_im, acc_b0_re, acc_b0_im, acc_b1_re, acc_b1_im;
    __m512d acc_b2_re, acc_b2_im, acc_b3_re, acc_b3_im;

    mat_avx512_complex_mul(dec_re, dec_im, sel_a[coeff],
        sel_a[coeff + vec_half], &acc_a_re, &acc_a_im);
    mat_avx512_complex_mul(dec_re, dec_im, sel_b0[coeff],
        sel_b0[coeff + vec_half], &acc_b0_re, &acc_b0_im);
    mat_avx512_complex_mul(dec_re, dec_im, sel_b1[coeff],
        sel_b1[coeff + vec_half], &acc_b1_re, &acc_b1_im);
    mat_avx512_complex_mul(dec_re, dec_im, sel_b2[coeff],
        sel_b2[coeff + vec_half], &acc_b2_re, &acc_b2_im);
    mat_avx512_complex_mul(dec_re, dec_im, sel_b3[coeff],
        sel_b3[coeff + vec_half], &acc_b3_re, &acc_b3_im);

    for (int row = 1; row < 5; row++){
      __m512d * dec = (__m512d *) dec_dft[row]->coeffs;
      dec_re = dec[coeff];
      dec_im = dec[coeff + vec_half];
      sel_a = (__m512d *) selector->samples[row]->a[0]->coeffs;
      sel_b0 = (__m512d *) selector->samples[row]->b[0]->coeffs;
      sel_b1 = (__m512d *) selector->samples[row]->b[1]->coeffs;
      sel_b2 = (__m512d *) selector->samples[row]->b[2]->coeffs;
      sel_b3 = (__m512d *) selector->samples[row]->b[3]->coeffs;
      mat_avx512_complex_addmul(dec_re, dec_im, sel_a[coeff],
          sel_a[coeff + vec_half], &acc_a_re, &acc_a_im);
      mat_avx512_complex_addmul(dec_re, dec_im, sel_b0[coeff],
          sel_b0[coeff + vec_half], &acc_b0_re, &acc_b0_im);
      mat_avx512_complex_addmul(dec_re, dec_im, sel_b1[coeff],
          sel_b1[coeff + vec_half], &acc_b1_re, &acc_b1_im);
      mat_avx512_complex_addmul(dec_re, dec_im, sel_b2[coeff],
          sel_b2[coeff + vec_half], &acc_b2_re, &acc_b2_im);
      mat_avx512_complex_addmul(dec_re, dec_im, sel_b3[coeff],
          sel_b3[coeff + vec_half], &acc_b3_re, &acc_b3_im);
    }

    out_a[coeff] = acc_a_re;
    out_a[coeff + vec_half] = acc_a_im;
    out_b0[coeff] = acc_b0_re;
    out_b0[coeff + vec_half] = acc_b0_im;
    out_b1[coeff] = acc_b1_re;
    out_b1[coeff + vec_half] = acc_b1_im;
    out_b2[coeff] = acc_b2_re;
    out_b2[coeff + vec_half] = acc_b2_im;
    out_b3[coeff] = acc_b3_re;
    out_b3[coeff + vec_half] = acc_b3_im;
  }
}

#if defined(MAT_TRGSW_AVX512_R4_UNROLLED_ROWS)
static void mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r4_unrolled_avx512(
    PVW_TMLWE_DFT out, MAT_TRGSW_DFT selector, DFT_Polynomial * dec_dft){
  const int N = out->a[0]->N;
  const int vec_half = N / 16;
  __m512d * restrict out_a = (__m512d *) out->a[0]->coeffs;
  __m512d * restrict out_b0 = (__m512d *) out->b[0]->coeffs;
  __m512d * restrict out_b1 = (__m512d *) out->b[1]->coeffs;
  __m512d * restrict out_b2 = (__m512d *) out->b[2]->coeffs;
  __m512d * restrict out_b3 = (__m512d *) out->b[3]->coeffs;
  const __m512d * restrict dec0 = (const __m512d *) dec_dft[0]->coeffs;
  const __m512d * restrict dec1 = (const __m512d *) dec_dft[1]->coeffs;
  const __m512d * restrict dec2 = (const __m512d *) dec_dft[2]->coeffs;
  const __m512d * restrict dec3 = (const __m512d *) dec_dft[3]->coeffs;
  const __m512d * restrict dec4 = (const __m512d *) dec_dft[4]->coeffs;
  const __m512d * restrict sel0_a =
      (const __m512d *) selector->samples[0]->a[0]->coeffs;
  const __m512d * restrict sel0_b0 =
      (const __m512d *) selector->samples[0]->b[0]->coeffs;
  const __m512d * restrict sel0_b1 =
      (const __m512d *) selector->samples[0]->b[1]->coeffs;
  const __m512d * restrict sel0_b2 =
      (const __m512d *) selector->samples[0]->b[2]->coeffs;
  const __m512d * restrict sel0_b3 =
      (const __m512d *) selector->samples[0]->b[3]->coeffs;
  const __m512d * restrict sel1_a =
      (const __m512d *) selector->samples[1]->a[0]->coeffs;
  const __m512d * restrict sel1_b0 =
      (const __m512d *) selector->samples[1]->b[0]->coeffs;
  const __m512d * restrict sel1_b1 =
      (const __m512d *) selector->samples[1]->b[1]->coeffs;
  const __m512d * restrict sel1_b2 =
      (const __m512d *) selector->samples[1]->b[2]->coeffs;
  const __m512d * restrict sel1_b3 =
      (const __m512d *) selector->samples[1]->b[3]->coeffs;
  const __m512d * restrict sel2_a =
      (const __m512d *) selector->samples[2]->a[0]->coeffs;
  const __m512d * restrict sel2_b0 =
      (const __m512d *) selector->samples[2]->b[0]->coeffs;
  const __m512d * restrict sel2_b1 =
      (const __m512d *) selector->samples[2]->b[1]->coeffs;
  const __m512d * restrict sel2_b2 =
      (const __m512d *) selector->samples[2]->b[2]->coeffs;
  const __m512d * restrict sel2_b3 =
      (const __m512d *) selector->samples[2]->b[3]->coeffs;
  const __m512d * restrict sel3_a =
      (const __m512d *) selector->samples[3]->a[0]->coeffs;
  const __m512d * restrict sel3_b0 =
      (const __m512d *) selector->samples[3]->b[0]->coeffs;
  const __m512d * restrict sel3_b1 =
      (const __m512d *) selector->samples[3]->b[1]->coeffs;
  const __m512d * restrict sel3_b2 =
      (const __m512d *) selector->samples[3]->b[2]->coeffs;
  const __m512d * restrict sel3_b3 =
      (const __m512d *) selector->samples[3]->b[3]->coeffs;
  const __m512d * restrict sel4_a =
      (const __m512d *) selector->samples[4]->a[0]->coeffs;
  const __m512d * restrict sel4_b0 =
      (const __m512d *) selector->samples[4]->b[0]->coeffs;
  const __m512d * restrict sel4_b1 =
      (const __m512d *) selector->samples[4]->b[1]->coeffs;
  const __m512d * restrict sel4_b2 =
      (const __m512d *) selector->samples[4]->b[2]->coeffs;
  const __m512d * restrict sel4_b3 =
      (const __m512d *) selector->samples[4]->b[3]->coeffs;

  assert(out->k == 1);
  assert(out->r == 4);
  assert(selector->T == 1);

  for (int coeff = 0; coeff < vec_half; coeff++){
    __m512d dec_re = dec0[coeff];
    __m512d dec_im = dec0[coeff + vec_half];
    __m512d acc_a_re, acc_a_im, acc_b0_re, acc_b0_im, acc_b1_re, acc_b1_im;
    __m512d acc_b2_re, acc_b2_im, acc_b3_re, acc_b3_im;

    mat_avx512_complex_mul(dec_re, dec_im, sel0_a[coeff],
        sel0_a[coeff + vec_half], &acc_a_re, &acc_a_im);
    mat_avx512_complex_mul(dec_re, dec_im, sel0_b0[coeff],
        sel0_b0[coeff + vec_half], &acc_b0_re, &acc_b0_im);
    mat_avx512_complex_mul(dec_re, dec_im, sel0_b1[coeff],
        sel0_b1[coeff + vec_half], &acc_b1_re, &acc_b1_im);
    mat_avx512_complex_mul(dec_re, dec_im, sel0_b2[coeff],
        sel0_b2[coeff + vec_half], &acc_b2_re, &acc_b2_im);
    mat_avx512_complex_mul(dec_re, dec_im, sel0_b3[coeff],
        sel0_b3[coeff + vec_half], &acc_b3_re, &acc_b3_im);

    dec_re = dec1[coeff];
    dec_im = dec1[coeff + vec_half];
    mat_avx512_complex_addmul(dec_re, dec_im, sel1_a[coeff],
        sel1_a[coeff + vec_half], &acc_a_re, &acc_a_im);
    mat_avx512_complex_addmul(dec_re, dec_im, sel1_b0[coeff],
        sel1_b0[coeff + vec_half], &acc_b0_re, &acc_b0_im);
    mat_avx512_complex_addmul(dec_re, dec_im, sel1_b1[coeff],
        sel1_b1[coeff + vec_half], &acc_b1_re, &acc_b1_im);
    mat_avx512_complex_addmul(dec_re, dec_im, sel1_b2[coeff],
        sel1_b2[coeff + vec_half], &acc_b2_re, &acc_b2_im);
    mat_avx512_complex_addmul(dec_re, dec_im, sel1_b3[coeff],
        sel1_b3[coeff + vec_half], &acc_b3_re, &acc_b3_im);

    dec_re = dec2[coeff];
    dec_im = dec2[coeff + vec_half];
    mat_avx512_complex_addmul(dec_re, dec_im, sel2_a[coeff],
        sel2_a[coeff + vec_half], &acc_a_re, &acc_a_im);
    mat_avx512_complex_addmul(dec_re, dec_im, sel2_b0[coeff],
        sel2_b0[coeff + vec_half], &acc_b0_re, &acc_b0_im);
    mat_avx512_complex_addmul(dec_re, dec_im, sel2_b1[coeff],
        sel2_b1[coeff + vec_half], &acc_b1_re, &acc_b1_im);
    mat_avx512_complex_addmul(dec_re, dec_im, sel2_b2[coeff],
        sel2_b2[coeff + vec_half], &acc_b2_re, &acc_b2_im);
    mat_avx512_complex_addmul(dec_re, dec_im, sel2_b3[coeff],
        sel2_b3[coeff + vec_half], &acc_b3_re, &acc_b3_im);

    dec_re = dec3[coeff];
    dec_im = dec3[coeff + vec_half];
    mat_avx512_complex_addmul(dec_re, dec_im, sel3_a[coeff],
        sel3_a[coeff + vec_half], &acc_a_re, &acc_a_im);
    mat_avx512_complex_addmul(dec_re, dec_im, sel3_b0[coeff],
        sel3_b0[coeff + vec_half], &acc_b0_re, &acc_b0_im);
    mat_avx512_complex_addmul(dec_re, dec_im, sel3_b1[coeff],
        sel3_b1[coeff + vec_half], &acc_b1_re, &acc_b1_im);
    mat_avx512_complex_addmul(dec_re, dec_im, sel3_b2[coeff],
        sel3_b2[coeff + vec_half], &acc_b2_re, &acc_b2_im);
    mat_avx512_complex_addmul(dec_re, dec_im, sel3_b3[coeff],
        sel3_b3[coeff + vec_half], &acc_b3_re, &acc_b3_im);

    dec_re = dec4[coeff];
    dec_im = dec4[coeff + vec_half];
    mat_avx512_complex_addmul(dec_re, dec_im, sel4_a[coeff],
        sel4_a[coeff + vec_half], &acc_a_re, &acc_a_im);
    mat_avx512_complex_addmul(dec_re, dec_im, sel4_b0[coeff],
        sel4_b0[coeff + vec_half], &acc_b0_re, &acc_b0_im);
    mat_avx512_complex_addmul(dec_re, dec_im, sel4_b1[coeff],
        sel4_b1[coeff + vec_half], &acc_b1_re, &acc_b1_im);
    mat_avx512_complex_addmul(dec_re, dec_im, sel4_b2[coeff],
        sel4_b2[coeff + vec_half], &acc_b2_re, &acc_b2_im);
    mat_avx512_complex_addmul(dec_re, dec_im, sel4_b3[coeff],
        sel4_b3[coeff + vec_half], &acc_b3_re, &acc_b3_im);

    out_a[coeff] = acc_a_re;
    out_a[coeff + vec_half] = acc_a_im;
    out_b0[coeff] = acc_b0_re;
    out_b0[coeff + vec_half] = acc_b0_im;
    out_b1[coeff] = acc_b1_re;
    out_b1[coeff + vec_half] = acc_b1_im;
    out_b2[coeff] = acc_b2_re;
    out_b2[coeff + vec_half] = acc_b2_im;
    out_b3[coeff] = acc_b3_re;
    out_b3[coeff + vec_half] = acc_b3_im;
  }
}
#endif

#if defined(MAT_TRGSW_AVX512_RGT4_FUSED)
#define MAT_RGT4_MAX_OUTPUTS 9
#define MAT_RGT4_TILE_OUTPUTS 4

static inline DFT_Polynomial mat_rgt4_poly_at(PVW_TMLWE_DFT sample, int idx){
  return idx == 0 ? sample->a[0] : sample->b[idx - 1];
}

static void mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_rgt4_tiled_avx512(
    PVW_TMLWE_DFT out, MAT_TRGSW_DFT selector, DFT_Polynomial * dec_dft){
  const int r = out->r;
  const int outputs = r + 1;
  const int rows = r + 1;
  const int N = out->a[0]->N;
  const int vec_half = N / 16;
  __m512d * out_coeffs[MAT_RGT4_MAX_OUTPUTS];
  const __m512d * dec_coeffs[MAT_RGT4_MAX_OUTPUTS];
  const __m512d * sel_coeffs[MAT_RGT4_MAX_OUTPUTS][MAT_RGT4_MAX_OUTPUTS];

  assert(out->k == 1);
  assert(selector->T == 1);
  assert(r == 6 || r == 8);
  assert(outputs <= MAT_RGT4_MAX_OUTPUTS);

  for (int idx = 0; idx < outputs; idx++){
    out_coeffs[idx] = (__m512d *) mat_rgt4_poly_at(out, idx)->coeffs;
  }
  for (int row = 0; row < rows; row++){
    dec_coeffs[row] = (const __m512d *) dec_dft[row]->coeffs;
    for (int idx = 0; idx < outputs; idx++){
      sel_coeffs[row][idx] =
          (const __m512d *) mat_rgt4_poly_at(selector->samples[row], idx)->coeffs;
    }
  }

  for (int coeff = 0; coeff < vec_half; coeff++){
    for (int tile = 0; tile < outputs; tile += MAT_RGT4_TILE_OUTPUTS){
      const int tile_count =
          outputs - tile < MAT_RGT4_TILE_OUTPUTS ? outputs - tile : MAT_RGT4_TILE_OUTPUTS;
      __m512d acc_re[MAT_RGT4_TILE_OUTPUTS];
      __m512d acc_im[MAT_RGT4_TILE_OUTPUTS];

      __m512d dec_re = dec_coeffs[0][coeff];
      __m512d dec_im = dec_coeffs[0][coeff + vec_half];
      for (int i = 0; i < tile_count; i++){
        const __m512d * sel = sel_coeffs[0][tile + i];
        mat_avx512_complex_mul(dec_re, dec_im, sel[coeff],
            sel[coeff + vec_half], &acc_re[i], &acc_im[i]);
      }

      for (int row = 1; row < rows; row++){
        dec_re = dec_coeffs[row][coeff];
        dec_im = dec_coeffs[row][coeff + vec_half];
        for (int i = 0; i < tile_count; i++){
          const __m512d * sel = sel_coeffs[row][tile + i];
          mat_avx512_complex_addmul(dec_re, dec_im, sel[coeff],
              sel[coeff + vec_half], &acc_re[i], &acc_im[i]);
        }
      }

      for (int i = 0; i < tile_count; i++){
        __m512d * dst = out_coeffs[tile + i];
        dst[coeff] = acc_re[i];
        dst[coeff + vec_half] = acc_im[i];
      }
    }
  }
}

#if defined(MAT_TRGSW_AVX512_R6_FULLTILE)
static void mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r6_fulltile_avx512(
    PVW_TMLWE_DFT out, MAT_TRGSW_DFT selector, DFT_Polynomial * dec_dft){
  const int r = out->r;
  const int outputs = r + 1;
  const int rows = r + 1;
  const int N = out->a[0]->N;
  const int vec_half = N / 16;
  __m512d * out_coeffs[7];
  const __m512d * dec_coeffs[7];
  const __m512d * sel_coeffs[7][7];

  assert(out->k == 1);
  assert(selector->T == 1);
  assert(r == 6);

  for (int idx = 0; idx < outputs; idx++){
    out_coeffs[idx] = (__m512d *) mat_rgt4_poly_at(out, idx)->coeffs;
  }
  for (int row = 0; row < rows; row++){
    dec_coeffs[row] = (const __m512d *) dec_dft[row]->coeffs;
    for (int idx = 0; idx < outputs; idx++){
      sel_coeffs[row][idx] =
          (const __m512d *) mat_rgt4_poly_at(selector->samples[row], idx)->coeffs;
    }
  }

  for (int coeff = 0; coeff < vec_half; coeff++){
    __m512d dec_re = dec_coeffs[0][coeff];
    __m512d dec_im = dec_coeffs[0][coeff + vec_half];
    __m512d acc0_re, acc0_im, acc1_re, acc1_im, acc2_re, acc2_im;
    __m512d acc3_re, acc3_im, acc4_re, acc4_im, acc5_re, acc5_im;
    __m512d acc6_re, acc6_im;

    mat_avx512_complex_mul(dec_re, dec_im, sel_coeffs[0][0][coeff],
        sel_coeffs[0][0][coeff + vec_half], &acc0_re, &acc0_im);
    mat_avx512_complex_mul(dec_re, dec_im, sel_coeffs[0][1][coeff],
        sel_coeffs[0][1][coeff + vec_half], &acc1_re, &acc1_im);
    mat_avx512_complex_mul(dec_re, dec_im, sel_coeffs[0][2][coeff],
        sel_coeffs[0][2][coeff + vec_half], &acc2_re, &acc2_im);
    mat_avx512_complex_mul(dec_re, dec_im, sel_coeffs[0][3][coeff],
        sel_coeffs[0][3][coeff + vec_half], &acc3_re, &acc3_im);
    mat_avx512_complex_mul(dec_re, dec_im, sel_coeffs[0][4][coeff],
        sel_coeffs[0][4][coeff + vec_half], &acc4_re, &acc4_im);
    mat_avx512_complex_mul(dec_re, dec_im, sel_coeffs[0][5][coeff],
        sel_coeffs[0][5][coeff + vec_half], &acc5_re, &acc5_im);
    mat_avx512_complex_mul(dec_re, dec_im, sel_coeffs[0][6][coeff],
        sel_coeffs[0][6][coeff + vec_half], &acc6_re, &acc6_im);

    for (int row = 1; row < rows; row++){
      dec_re = dec_coeffs[row][coeff];
      dec_im = dec_coeffs[row][coeff + vec_half];
      mat_avx512_complex_addmul(dec_re, dec_im, sel_coeffs[row][0][coeff],
          sel_coeffs[row][0][coeff + vec_half], &acc0_re, &acc0_im);
      mat_avx512_complex_addmul(dec_re, dec_im, sel_coeffs[row][1][coeff],
          sel_coeffs[row][1][coeff + vec_half], &acc1_re, &acc1_im);
      mat_avx512_complex_addmul(dec_re, dec_im, sel_coeffs[row][2][coeff],
          sel_coeffs[row][2][coeff + vec_half], &acc2_re, &acc2_im);
      mat_avx512_complex_addmul(dec_re, dec_im, sel_coeffs[row][3][coeff],
          sel_coeffs[row][3][coeff + vec_half], &acc3_re, &acc3_im);
      mat_avx512_complex_addmul(dec_re, dec_im, sel_coeffs[row][4][coeff],
          sel_coeffs[row][4][coeff + vec_half], &acc4_re, &acc4_im);
      mat_avx512_complex_addmul(dec_re, dec_im, sel_coeffs[row][5][coeff],
          sel_coeffs[row][5][coeff + vec_half], &acc5_re, &acc5_im);
      mat_avx512_complex_addmul(dec_re, dec_im, sel_coeffs[row][6][coeff],
          sel_coeffs[row][6][coeff + vec_half], &acc6_re, &acc6_im);
    }

    out_coeffs[0][coeff] = acc0_re;
    out_coeffs[0][coeff + vec_half] = acc0_im;
    out_coeffs[1][coeff] = acc1_re;
    out_coeffs[1][coeff + vec_half] = acc1_im;
    out_coeffs[2][coeff] = acc2_re;
    out_coeffs[2][coeff + vec_half] = acc2_im;
    out_coeffs[3][coeff] = acc3_re;
    out_coeffs[3][coeff + vec_half] = acc3_im;
    out_coeffs[4][coeff] = acc4_re;
    out_coeffs[4][coeff + vec_half] = acc4_im;
    out_coeffs[5][coeff] = acc5_re;
    out_coeffs[5][coeff + vec_half] = acc5_im;
    out_coeffs[6][coeff] = acc6_re;
    out_coeffs[6][coeff + vec_half] = acc6_im;
  }
}
#endif

#if defined(MAT_TRGSW_AVX512_R6_BODYMAJOR)
static void mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r6_bodymajor_avx512(
    PVW_TMLWE_DFT out, MAT_TRGSW_DFT selector, DFT_Polynomial * dec_dft){
  const int r = out->r;
  const int outputs = r + 1;
  const int rows = r + 1;
  const int N = out->a[0]->N;
  const int vec_half = N / 16;
  __m512d * out_coeffs[7];
  const __m512d * dec_coeffs[7];
  const __m512d * sel_coeffs[7][7];

  assert(out->k == 1);
  assert(selector->T == 1);
  assert(r == 6);

  for (int idx = 0; idx < outputs; idx++){
    out_coeffs[idx] = (__m512d *) mat_rgt4_poly_at(out, idx)->coeffs;
  }
  for (int row = 0; row < rows; row++){
    dec_coeffs[row] = (const __m512d *) dec_dft[row]->coeffs;
    for (int idx = 0; idx < outputs; idx++){
      sel_coeffs[row][idx] =
          (const __m512d *) mat_rgt4_poly_at(selector->samples[row], idx)->coeffs;
    }
  }

  for (int idx = 0; idx < outputs; idx++){
    __m512d * restrict dst = out_coeffs[idx];
    for (int coeff = 0; coeff < vec_half; coeff++){
      __m512d dec_re = dec_coeffs[0][coeff];
      __m512d dec_im = dec_coeffs[0][coeff + vec_half];
      const __m512d * restrict sel = sel_coeffs[0][idx];
      __m512d acc_re, acc_im;

      mat_avx512_complex_mul(dec_re, dec_im, sel[coeff],
          sel[coeff + vec_half], &acc_re, &acc_im);

      for (int row = 1; row < rows; row++){
        dec_re = dec_coeffs[row][coeff];
        dec_im = dec_coeffs[row][coeff + vec_half];
        sel = sel_coeffs[row][idx];
        mat_avx512_complex_addmul(dec_re, dec_im, sel[coeff],
            sel[coeff + vec_half], &acc_re, &acc_im);
      }

      dst[coeff] = acc_re;
      dst[coeff + vec_half] = acc_im;
    }
  }
}
#endif
#endif
#endif

void mat_trgsw_mul_pvmtmlwe_DFT(PVW_TMLWE_DFT out, PVW_TMLWE in, MAT_TRGSW_DFT selector, MAT_TRGSW_MUL_SCRATCH scratch){
  const int k = in->k;
  const int r = in->r;
  const int l = selector->T;
  const int rows = mat_trgsw_rows(l, k, r);

  assert(out->k == k);
  assert(out->r == r);
  assert(selector->samples[0]->k == k);
  assert(selector->samples[0]->r == r);
  assert(scratch != NULL);
  assert(scratch->rows >= rows);

  pvmtmlwe_decompose(scratch->dec, in, selector->Q, l);
  for (size_t i = 0; i < rows; i++){
    polynomial_torus_to_DFT(scratch->dec_dft[i], scratch->dec[i]);
  }

#if defined(AVX512_OPT) && defined(MAT_TRGSW_AVX512_SMALLR_SPECIALIZED)
  if(k == 1 && l == 1 && r == 2){
    mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r2_avx512(out, selector,
        scratch->dec_dft);
    return;
  }
  if(k == 1 && l == 1 && r == 4){
#if defined(MAT_TRGSW_AVX512_R4_UNROLLED_ROWS)
    mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r4_unrolled_avx512(out, selector,
        scratch->dec_dft);
#else
    mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r4_avx512(out, selector,
        scratch->dec_dft);
#endif
    return;
  }
#if defined(MAT_TRGSW_AVX512_RGT4_FUSED)
  #if defined(MAT_TRGSW_AVX512_R6_BODYMAJOR)
  if(k == 1 && l == 1 && r == 6){
    mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r6_bodymajor_avx512(out, selector,
        scratch->dec_dft);
    return;
  }
  #endif
  #if defined(MAT_TRGSW_AVX512_R6_FULLTILE)
  if(k == 1 && l == 1 && r == 6){
    mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r6_fulltile_avx512(out, selector,
        scratch->dec_dft);
    return;
  }
  #endif
  if(k == 1 && l == 1 && (r == 6 || r == 8)){
    mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_rgt4_tiled_avx512(out, selector,
        scratch->dec_dft);
    return;
  }
#endif
#endif

  for (size_t j = 0; j < k; j++){
    polynomial_mul_DFT(out->a[j], scratch->dec_dft[0], selector->samples[0]->a[j]);
  }
  for (size_t j = 0; j < r; j++){
    polynomial_mul_DFT(out->b[j], scratch->dec_dft[0], selector->samples[0]->b[j]);
  }

  for (size_t row = 1; row < rows; row++){
    for (size_t j = 0; j < k; j++){
      polynomial_mul_addto_DFT(out->a[j], scratch->dec_dft[row], selector->samples[row]->a[j]);
    }
    for (size_t j = 0; j < r; j++){
      polynomial_mul_addto_DFT(out->b[j], scratch->dec_dft[row], selector->samples[row]->b[j]);
    }
  }
}
