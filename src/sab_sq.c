/* sab_sq.c -- Scale-Quantized SAB (SQS), stage356 candidate.
 *
 * Algorithm-level transplant of the scale-based ("squared gadget")
 * external product of eprint 2025/1711 into the sparse amortized
 * bootstrapping schedule of eprint 2025/686 (this repository).
 *
 * Torus-u64 formulation (see theory_checks/stage356_sq_scale_sab_model.md):
 *   - accumulator slots are TRLWEs whose coefficients are small signed
 *     integers in [-2^(q-1), 2^(q-1)) (the Q = 2^q quantization of the
 *     torus), stored sign-extended in u64;
 *   - the selector TRGSW is the stock trgsw_monomial_sample with l = 1,
 *     Bg_bit = q, i.e. the bit message enters at raw scale 2^(64-q);
 *   - external product: DFT pointwise rows x raw operand (integer
 *     convolution mod 2^64, the execute_reverse/direct_torus64 contract),
 *     then per-coefficient rescale round(x / 2^(64-q)). No digit
 *     decomposition of the accumulator;
 *   - NCMUX keeps the torus-scale automorphism keyswitch: the operand is
 *     exactly upshifted to torus scale before the KS and rescaled after,
 *     so the KS sees the stock semantics and its noise is unchanged.
 *
 * The Q^2/T = 2^(2q-64) suppression of the key-noise term (Lemma 3.4 of
 * 2025/1711) is the budget that absorbs the sparse-secret isometry
 * hybrid gap of eprint 2026/279 via sigma hardening at iso-speed; see
 * scripts/sq_security_preflight_279.py.
 *
 * Isolation: compiled only behind SAB_SQ_EQUIV_TEST; does not modify the
 * scalar SAB, sab_pvw_* or sab_operator_* paths. Binary secrets only.
 */
#include "sab_sq.h"
#include <sab.h>

/* round-to-nearest arithmetic right shift by (64 - q) on one polynomial */
static inline void sab_sq_round_shift_poly(TorusPolynomial p, uint64_t q){
  const unsigned shift = 64 - q;
  const int64_t half = 1LL << (shift - 1);
  for (size_t i = 0; i < p->N; i++){
    p->coeffs[i] = (Torus) ((((int64_t) p->coeffs[i]) + half) >> shift);
  }
}

/* exact left shift by (64 - q): Q-scale storage -> torus representation */
static void sab_sq_upshift(TRLWE out, TRLWE in, uint64_t q){
  const unsigned shift = 64 - q;
  for (size_t c = 0; c < in->b->N; c++){
    out->b->coeffs[c] = (Torus) (((int64_t) in->b->coeffs[c]) << shift);
    for (size_t j = 0; j < in->k; j++)
      out->a[j]->coeffs[c] = (Torus) (((int64_t) in->a[j]->coeffs[c]) << shift);
  }
}

SAB_SQ_Key sab_sq_new_key(TRLWE_Key input_key, TRLWE_Key repacking_key,
    TRGSW_Key sq_output_key, uint64_t b_prec, uint64_t b_packing,
    uint64_t ell_packing, uint64_t t_ks, uint64_t b_ks, uint64_t h,
    uint64_t r_prec, uint64_t q){
  assert(sq_output_key->l == 1);
  assert((uint64_t) sq_output_key->Bg_bit == q);
  assert(q >= 8 && q <= 40);
  SAB_SQ_Key res = (SAB_SQ_Key) safe_malloc(sizeof(*res));
  const uint64_t in_N = input_key->s[0]->N;
  const uint64_t in_k = input_key->k;
  const uint64_t out_N = sq_output_key->trlwe_key->s[0]->N;
  const uint64_t out_k = sq_output_key->trlwe_key->k;
  const uint64_t r_max = 1ULL << r_prec;
  TRGSW tmp = trgsw_alloc_new_sample(1, q, out_k, out_N);

  // automorphism key for -1, torus-scale gadget (independent of q)
  uint64_t m1[1] = {2*out_N - 1};
  TRLWE_KS_Key * aut_ks = trlwe_new_automorphism_KS_keyset_2(sq_output_key->trlwe_key, m1, 1, 1, 23);
  res->aut_minus1 = aut_ks[0];
  free(aut_ks);

  // packing + HW reducing keys over the output ring
  TLWE_Key extracted_key = tlwe_alloc_key(out_N*out_k, sq_output_key->trlwe_key->sigma);
  trlwe_extract_tlwe_key(extracted_key, sq_output_key->trlwe_key);
  res->packing_key = trlwe_new_full_packing_KS_key(repacking_key, extracted_key, ell_packing, b_packing);
  res->hw_reducing_key = trlwe_new_KS_key(input_key, repacking_key, t_ks, b_ks);
  // extracted_key is retained by the KS keys; repo convention frees at exit

  // encrypt the sparse representation of the input secret (binary only)
  uint64_t previous = in_N;
  res->s = (TRGSW_DFT ***) safe_malloc(sizeof(TRGSW_DFT ***) * in_k);
  for (size_t i = 0; i < in_k; i++){
    res->s[i] = (TRGSW_DFT **) safe_malloc(sizeof(TRGSW_DFT **) * (h+1));
    uint64_t cnt_h = 0;
    for (size_t j = 0; j < in_N; j++){
      const uint64_t coeff = input_key->s[i]->coeffs[in_N - j - 1];
      if(coeff != 0){
        const uint64_t current = in_N - j - 1;
        const uint64_t r_diff = previous - current;
        /* v1 scope: binary secrets with gaps under the r_prec bound
         * (include_zeros unsupported); fail fast instead of the scalar
         * NDEBUG'd asserts so misconfiguration is observable. */
        if(r_diff >= r_max || coeff != 1) exit(3);
        res->s[i][cnt_h] = trgsw_alloc_new_DFT_sample_array(r_prec, 1, q, out_k, out_N);
        RGSW_encrypt_bits(res->s[i][cnt_h], tmp, sq_output_key, r_diff, r_prec);
        previous = current;
        cnt_h++;
      }
    }
    if(cnt_h != h) exit(3);
    res->s[i][cnt_h] = trgsw_alloc_new_DFT_sample_array(r_prec, 1, q, out_k, out_N);
    RGSW_encrypt_bits(res->s[i][cnt_h], tmp, sq_output_key, previous, r_prec);
  }
  free_trgsw(tmp);

  res->in_N = in_N;
  res->in_k = in_k;
  res->out_N = out_N;
  res->out_k = out_k;
  res->h = h;
  res->r_prec = r_prec;
  res->b_prec = b_prec;
  res->q = q;

  res->tmp = (sab_sq_tmp) safe_malloc(sizeof(*res->tmp));
  res->tmp->t1 = trlwe_alloc_new_sample(out_k, out_N);
  res->tmp->t2 = trlwe_alloc_new_sample(out_k, out_N);
  res->tmp->da = polynomial_new_DFT_polynomial(out_N);
  res->tmp->db = polynomial_new_DFT_polynomial(out_N);
  res->tmp->oa = polynomial_new_DFT_polynomial(out_N);
  res->tmp->ob = polynomial_new_DFT_polynomial(out_N);
  res->tmp->slots = trlwe_alloc_new_sample_array(in_N, out_k, out_N);
  res->tmp->p2 = trlwe_alloc_new_sample_array(in_N, out_k, out_N);
  res->tmp->pack = trlwe_alloc_new_sample(in_k, in_N);
  res->tmp->ext = tlwe_alloc_sample_array(in_N, out_N*out_k);
  return res;
}

/* out = round_2^q(in * sel): the scale-based external product */
void sab_sq_external_product(TRLWE out, TRLWE in, TRGSW_DFT sel, SAB_SQ_Key k){
  assert(sel->l == 1);
  assert(in->k == 1);
  sab_sq_tmp t = k->tmp;
  // raw integer spectra of the Q-scale operand
  polynomial_torus_to_DFT(t->da, in->a[0]);
  polynomial_torus_to_DFT(t->db, in->b);
  // 2x2 key rows x (b, a): samples[0] = a-row, samples[1] = b-row at l = 1
  polynomial_mul_DFT(t->oa, t->da, sel->samples[0]->a[0]);
  polynomial_mul_DFT(t->ob, t->da, sel->samples[0]->b);
  polynomial_mul_addto_DFT(t->oa, t->db, sel->samples[1]->a[0]);
  polynomial_mul_addto_DFT(t->ob, t->db, sel->samples[1]->b);
  // back to coefficients and rescale by Q/T = 2^(q-64)
  polynomial_DFT_to_torus(out->a[0], t->oa);
  polynomial_DFT_to_torus(out->b, t->ob);
  sab_sq_round_shift_poly(out->a[0], k->q);
  sab_sq_round_shift_poly(out->b, k->q);
}

void sab_sq_cmux(TRLWE out, TRLWE in1, TRLWE in2, TRGSW_DFT selector, SAB_SQ_Key k){
  trlwe_sub(k->tmp->t1, in2, in1);
  sab_sq_external_product(k->tmp->t2, k->tmp->t1, selector, k);
  trlwe_add(out, k->tmp->t2, in1);
}

void sab_sq_ncmux(TRLWE out, TRLWE in1, TRLWE in2, TRGSW_DFT selector, SAB_SQ_Key k){
  // torus-scale roundtrip around the stock automorphism keyswitch
  sab_sq_upshift(k->tmp->t1, in2, k->q);
  trlwe_eval_automorphism(k->tmp->t2, k->tmp->t1, 2*in2->b->N - 1, k->aut_minus1);
  sab_sq_round_shift_poly(k->tmp->t2->a[0], k->q);
  sab_sq_round_shift_poly(k->tmp->t2->b, k->q);
  sab_sq_cmux(out, in1, k->tmp->t2, selector, k);
}

/* p0 <- p0 * X^e (same butterfly schedule as the scalar RGSW_monomial_mul) */
void sab_sq_monomial_mul(TRLWE * p0, TRGSW_DFT * e, SAB_SQ_Key k){
  const uint32_t r_prec = k->r_prec, in_N = k->in_N;
  TRLWE * p[2] = {p0, k->tmp->p2};
  for (size_t i = 0; i < r_prec; i++){
    const uint64_t power = 1ULL << i;
    const uint64_t out = (i+1)&1, in = out^1;
    for (size_t j = 0; j < power; j++){
      sab_sq_ncmux(p[out][j], p[in][j], p[in][in_N - power + j], e[i], k);
    }
    for (size_t j = 0; j < in_N - power; j++){
      sab_sq_cmux(p[out][j + power], p[in][j + power], p[in][j], e[i], k);
    }
  }
  if(p[r_prec&1]!=p0){
    for (size_t i = 0; i < in_N; i++){
      trlwe_copy(p0[i], p[r_prec&1][i]);
    }
  }
}

/* p = p * x^{-as} (binary path: plain negacyclic rotation) */
void sab_sq_sub_a(TRLWE * p, uint64_t * a, SAB_SQ_Key k){
  for (size_t i = 0; i < k->in_N; i++){
    trlwe_mul_by_xai(k->tmp->t1, p[i], a[i]);
    trlwe_copy(p[i], k->tmp->t1);
  }
}

void sab_sq_sparse_mul(TRLWE * p, uint64_t * a, uint64_t a_idx, SAB_SQ_Key k){
  for (size_t i = 0; i < k->h; i++){
    sab_sq_monomial_mul(p, k->s[a_idx][i], k);
    sab_sq_sub_a(p, a, k);
  }
  sab_sq_monomial_mul(p, k->s[a_idx][k->h], k);
}

static void sab_sq_mod_switch(uint64_t * out, uint64_t * in, uint64_t prec, uint64_t size){
  for (size_t j = 0; j < size; j++){
    out[j] = torus2int(in[j], prec);
  }
}

void sab_sq_blind_rotate(TRLWE * out, TRLWE in, SAB_SQ_Key k){
  uint64_t * a = (uint64_t *) safe_malloc(sizeof(uint64_t) * k->in_N);
  const uint64_t log_N2 = (uint64_t) log2(2 * k->out_N);
  assert(k->in_k == 1);
  for (size_t i = 0; i < k->in_k; i++){
    sab_sq_mod_switch(a, in->a[i]->coeffs, log_N2, k->in_N);
    sab_sq_sparse_mul(out, a, i, k);
  }
  free(a);
}

/* acc[i] = quantize_q(tv * X^{b_i}): the test vector enters at Q-scale */
void sab_sq_setup_tv_xb(TRLWE * acc, uint64_t * b, TRLWE tv, SAB_SQ_Key k){
  const uint64_t N = k->out_N, log_N2 = (uint64_t) log2(N*2);
  const uint64_t prec_offset = 1ULL << (64 - k->b_prec - 1);
  const unsigned shift = 64 - k->q;
  const int64_t half = 1LL << (shift - 1);
  for (size_t i = 0; i < k->in_N; i++){
    trlwe_mul_by_xai(k->tmp->t1, tv, torus2int(b[i] + prec_offset, log_N2));
    for (size_t c = 0; c < N; c++){
      acc[i]->b->coeffs[c] = (Torus) ((((int64_t) k->tmp->t1->b->coeffs[c]) + half) >> shift);
      for (size_t j = 0; j < k->out_k; j++)
        acc[i]->a[j]->coeffs[c] = (Torus) ((((int64_t) k->tmp->t1->a[j]->coeffs[c]) + half) >> shift);
    }
  }
}

void sab_sq_bootstrap(TRLWE out, TRLWE in, TRLWE tv, SAB_SQ_Key k){
  sab_sq_setup_tv_xb(k->tmp->slots, in->b->coeffs, tv, k);
  sab_sq_blind_rotate(k->tmp->slots, in, k);
  // lift each slot back to torus scale, then the stock extract/pack/HW chain
  for (size_t i = 0; i < k->in_N; i++){
    sab_sq_upshift(k->tmp->slots[i], k->tmp->slots[i], k->q);
    trlwe_extract_tlwe(k->tmp->ext[i], k->tmp->slots[i], 0);
  }
  trlwe_full_packing_keyswitch(k->tmp->pack, k->tmp->ext, k->in_N, k->packing_key);
  trlwe_keyswitch(out, k->tmp->pack, k->hw_reducing_key);
}
