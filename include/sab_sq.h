/* sab_sq.h -- Scale-Quantized SAB (SQS), stage356 candidate.
 *
 * Isolated algorithm-level variant of the scalar sparse amortized
 * bootstrapping (eprint 2025/686) that swaps the gadget-decomposition
 * external product for the scale-based ("squared gadget") external
 * product of eprint 2025/1711, on the MOSFHET u64 torus:
 *
 *   - the blind-rotation accumulator lives at Q = 2^q scale: every TRLWE
 *     coefficient (mask and body) is a small signed integer, stored
 *     sign-extended in the u64 torus;
 *   - the selector TRGSW is sampled with l = 1, Bg_bit = q, so the
 *     monomial/bit message enters at raw scale 2^(64-q) (the
 *     trgsw_monomial_sample convention) and the external product is the
 *     DFT-domain pointwise product C * c followed by the per-coefficient
 *     rescale round(x / 2^(64-q)) -- no digit decomposition;
 *   - the Q^2/T = 2^(2q-64) factor suppresses the key-noise term of the
 *     product (Lemma 3.4 of 2025/1711). Lowering q below the stock Bg=23
 *     frees a noise budget used to absorb the sparse-secret isometry
 *     hybrid gap of eprint 2026/279 (up to 15 bits) via sigma hardening.
 *
 * Ownership boundaries (isolation contract, mirrors sab_operator.h):
 *   - must not change sab_rlwe_bootstrap / the scalar SAB default path;
 *   - must not replace sab_pvw_* (MAT-SAB) or sab_operator_* (candidate D);
 *   - every entry point is compiled only behind SAB_SQ_EQUIV_TEST;
 *   - binary sparse input secrets only in this revision (ternary and
 *     gaussian selector paths are out of scope for v1).
 */
#ifndef SAB_SQ_H
#define SAB_SQ_H

#include <mosfhet.h>

typedef struct _sab_sq_tmp {
  TRLWE t1, t2;             /* coefficient-form scratch (out ring) */
  DFT_Polynomial da, db;    /* DFT of the CMUX difference */
  DFT_Polynomial oa, ob;    /* DFT accumulator of the product rows */
  TRLWE * slots;            /* internal blind-rotation slot array, in_N slots */
  TRLWE * p2;               /* ping-pong second buffer, in_N slots */
  TRLWE pack;               /* packing keyswitch intermediate */
  TLWE * ext;               /* extracted TLWE per slot */
} * sab_sq_tmp;

typedef struct _SAB_SQ_Key {
  uint64_t in_N, in_k, out_N, out_k, h, r_prec, b_prec, q;
  TRLWE_KS_Key aut_minus1;      /* torus-scale automorphism KS for NCMUX */
  TRGSW_DFT *** s;              /* [in_k][h+1][r_prec] bit selectors, Bg_bit = q */
  TRLWE_KS_Key packing_key;
  TRLWE_KS_Key hw_reducing_key;
  sab_sq_tmp tmp;
} * SAB_SQ_Key;

/* Key material mirrors the scalar constructor; sq_output_key must be
 * created with l = 1 and Bg_bit = q over output_key->trlwe_key. */
SAB_SQ_Key sab_sq_new_key(TRLWE_Key input_key, TRLWE_Key repacking_key,
    TRGSW_Key sq_output_key, uint64_t b_prec, uint64_t b_packing,
    uint64_t ell_packing, uint64_t t_ks, uint64_t b_ks, uint64_t h,
    uint64_t r_prec, uint64_t q);

/* Scale-form external product: out = round_2^q(in * sel); in holds
 * Q-scale small integers, sel is an l=1/Bg_bit=q TRGSW_DFT. */
void sab_sq_external_product(TRLWE out, TRLWE in, TRGSW_DFT sel, SAB_SQ_Key k);

void sab_sq_cmux(TRLWE out, TRLWE in1, TRLWE in2, TRGSW_DFT selector, SAB_SQ_Key k);
void sab_sq_ncmux(TRLWE out, TRLWE in1, TRLWE in2, TRGSW_DFT selector, SAB_SQ_Key k);
void sab_sq_monomial_mul(TRLWE * p0, TRGSW_DFT * e, SAB_SQ_Key k);
void sab_sq_sub_a(TRLWE * p, uint64_t * a, SAB_SQ_Key k);
void sab_sq_sparse_mul(TRLWE * p, uint64_t * a, uint64_t a_idx, SAB_SQ_Key k);
void sab_sq_blind_rotate(TRLWE * out, TRLWE in, SAB_SQ_Key k);
void sab_sq_setup_tv_xb(TRLWE * acc, uint64_t * b, TRLWE tv, SAB_SQ_Key k);
void sab_sq_bootstrap(TRLWE out, TRLWE in, TRLWE tv, SAB_SQ_Key k);

#endif
