#pragma once
#include <mosfhet.h>

/* r-input batching + Hom-Tr (stage396): interleaved accumulator over
 * R = Z[X]/(X^N+1) with N = r*d, r = 2 lanes packed at X-exponent residues
 * (Y = X^2), ONE body (PVW_TMLWE r=1) per slot. Math reference:
 * theory_checks/stage396_rinput_homtr_math.md (HT-2' U_a identity, HT-4
 * Psi wrap correction, HT-5 lift theorem, HT-8 guard-bit rescale);
 * machine-verified by scripts/check_rinput_homtr_gf257.py (C4 2560/2560). */

typedef struct _SAB_RINPUT_Tmp{
  PVW_TMLWE t0, t1, t2, s_plus, s_minus;
  PVW_TMLWE_DFT dft;
  MAT_TRGSW_MUL_SCRATCH scratch;
  PVW_TMLWE *buf2; /* ping-pong second accumulator array (in_N slots) */
  uint64_t *a_mod0, *a_mod1; /* per-input mod-switched a (granularity 2d) */
} * SAB_RINPUT_Tmp;

typedef struct _SAB_RINPUT_Key{
  uint64_t in_N, in_k, out_N, d, lanes, h, r_prec, b_prec;
  PVW_TMLWE_Key output_key; /* r = 1: single secret s over R */
  MAT_TRGSW_Key mat_key;
  MAT_TRGSW_DFT ***s; /* [in_k][h+1][r_prec] gap-bit selectors */
  PVW_TMLWE_KS_Key aut_minus1; /* w = 2N-1: wrap part of Psi */
  PVW_TMLWE_KS_Key aut_h; /* w = 1+N: Hom-Tr sigma; shared by sub_a & Psi */
  SAB_RINPUT_Tmp tmp;
} * SAB_RINPUT_Key;

/* output_key must have r = 1 and N = out ring dim (r-input accumulator). */
SAB_RINPUT_Key sab_rinput_new_key(TRLWE_Key input_key,
    PVW_TMLWE_Key output_key, uint64_t b_prec, uint64_t h, uint64_t r_prec,
    uint64_t l, uint64_t bg_bit);
void free_sab_rinput_key(SAB_RINPUT_Key sab);

/* I-4: per-step rescale c <- round(c/2) (guard-bit semantics, lemma HT-7). */
void sab_rinput_rescale2(PVW_TMLWE out, PVW_TMLWE in);

/* I-5: Hom-Tr sub_a, U_a = Y^{a0}(C+sigma C) + Y^{a1}(C-sigma C), /2.
 * a0/a1: mod-switched masks of the two inputs at granularity 2d. */
void sab_rinput_sub_a_homtr(PVW_TMLWE * p, const uint64_t * a0,
    const uint64_t * a1, SAB_RINPUT_Key sab);
void sab_rinput_sub_a_homtr_opt(PVW_TMLWE * p, const uint64_t * a0,
    const uint64_t * a1, SAB_RINPUT_Key sab, int rescale);

/* Psi = U_(0,1) o sigma_{-1}: wrapped-source correction (lemma HT-4). */
void sab_rinput_wrap_psi(PVW_TMLWE out, PVW_TMLWE in, SAB_RINPUT_Key sab);

/* CMUX primitive (exposed for unit testing). */
void sab_rinput_CMUX(PVW_TMLWE out, PVW_TMLWE in1, PVW_TMLWE in2,
    MAT_TRGSW_DFT selector, SAB_RINPUT_Key sab);

/* I-1: interleaved plaintext setup: slot t body = Phi((Y^{bbar_l[t]} TV_l)_l)
 * with lane l at positions l + 2q; mask zero (trivial). tv0/tv1 have d
 * coefficients, quantized with 1 guard bit (v << (63-p)). */
void sab_rinput_setup_tv(PVW_TMLWE * acc, TRLWE in0, TRLWE in1,
    TorusPolynomial tv0, TorusPolynomial tv1, SAB_RINPUT_Key sab);

/* butterfly with Psi-corrected wrapped sources (direct CMUX identical to
 * the matrix path). */
void sab_rinput_RGSW_monomial_mul(PVW_TMLWE * p, MAT_TRGSW_DFT * e,
    SAB_RINPUT_Key sab);

/* I-6: full r-input blind rotation (h steps + final rotation). */
void sab_rinput_blind_rotate(PVW_TMLWE * out, TRLWE in0, TRLWE in1,
    SAB_RINPUT_Key sab);
void sab_rinput_bootstrap_wo_extract(PVW_TMLWE * out, TRLWE in0, TRLWE in1,
    TorusPolynomial tv0, TorusPolynomial tv1, SAB_RINPUT_Key sab);
