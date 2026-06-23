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
static void mat_trgsw_mul_row_outputs_avx512(DFT_Polynomial * outs,
    DFT_Polynomial dec, DFT_Polynomial * sels, int out_count, bool init){
  const int N = dec->N;
  const int vec_half = N / 16;
  __m512d * dec_coeffs = (__m512d *) dec->coeffs;

  for (int coeff = 0; coeff < vec_half; coeff++){
    const __m512d dec_re = dec_coeffs[coeff];
    const __m512d dec_im = dec_coeffs[coeff + vec_half];
    for (int out_idx = 0; out_idx < out_count; out_idx++){
      __m512d * sel_coeffs = (__m512d *) sels[out_idx]->coeffs;
      __m512d * out_coeffs = (__m512d *) outs[out_idx]->coeffs;
      const __m512d sel_re = sel_coeffs[coeff];
      const __m512d sel_im = sel_coeffs[coeff + vec_half];
      const __m512d re = _mm512_fmsub_pd(dec_re, sel_re,
          _mm512_mul_pd(dec_im, sel_im));
      const __m512d im = _mm512_fmadd_pd(dec_re, sel_im,
          _mm512_mul_pd(dec_im, sel_re));
      if(init){
        out_coeffs[coeff] = re;
        out_coeffs[coeff + vec_half] = im;
      }else{
        out_coeffs[coeff] = _mm512_add_pd(out_coeffs[coeff], re);
        out_coeffs[coeff + vec_half] = _mm512_add_pd(
            out_coeffs[coeff + vec_half], im);
      }
    }
  }
}

static void mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_smallr_avx512(
    PVW_TMLWE_DFT out, MAT_TRGSW_DFT selector, DFT_Polynomial * dec_dft){
  const int r = out->r;
  DFT_Polynomial outs[5];
  DFT_Polynomial sels[5];
  const int out_count = 1 + r;

  assert(out->k == 1);
  assert(selector->T == 1);
  assert(r == 2 || r == 4);

  outs[0] = out->a[0];
  for (int lane = 0; lane < r; lane++){
    outs[1 + lane] = out->b[lane];
  }

  for (int row = 0; row < out_count; row++){
    sels[0] = selector->samples[row]->a[0];
    for (int lane = 0; lane < r; lane++){
      sels[1 + lane] = selector->samples[row]->b[lane];
    }
    mat_trgsw_mul_row_outputs_avx512(outs, dec_dft[row], sels, out_count,
        row == 0);
  }
}
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
  if(k == 1 && l == 1 && (r == 2 || r == 4)){
    mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_smallr_avx512(out, selector,
        scratch->dec_dft);
    return;
  }
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
