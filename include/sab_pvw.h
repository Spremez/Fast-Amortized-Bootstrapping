#pragma once
#include <mosfhet.h>

typedef struct _sab_pvw_tmp_pool{
  PVW_TMLWE_DFT tmlwe_dft;
  PVW_TMLWE tmlwe, rotated, * tmlwe_poly2, * acc;
  PVW_TLWE * extracted;
  TLWE ** lane_extracted;
  TRLWE packed;
  MAT_TRGSW_MUL_SCRATCH scratch;
  uint64_t * a_mod;
} * sab_pvw_tmp_pool;

typedef struct _SAB_PVW_Key{
  uint64_t in_N, in_k, out_N, out_k, lanes, h, r_prec, b_prec;
  PVW_TMLWE_Key output_key;
  MAT_TRGSW_Key mat_key;
  PVW_TMLWE_KS_Key aut_minus1;
  TRLWE_KS_Key * packing_keys;
  TRLWE_KS_Key hw_reducing_key;
  MAT_TRGSW_DFT *** s;
  sab_pvw_tmp_pool tmp;
} * SAB_PVW_Key;

SAB_PVW_Key sab_pvw_new_binary_key(TRLWE_Key input_key, PVW_TMLWE_Key output_key,
    uint64_t b_prec, uint64_t h, uint64_t r_prec, uint64_t l, uint64_t bg_bit);
SAB_PVW_Key sab_pvw_new_binary_full_key(TRLWE_Key input_key,
    TRLWE_Key repacking_key, PVW_TMLWE_Key output_key, uint64_t b_prec,
    uint64_t b_packing, uint64_t ell_packing, uint64_t t_ks, uint64_t b_ks,
    uint64_t h, uint64_t r_prec, uint64_t l, uint64_t bg_bit);
void free_sab_pvw_key(SAB_PVW_Key sab);

void sab_pvw_CMUX(PVW_TMLWE out, PVW_TMLWE in1, PVW_TMLWE in2,
    MAT_TRGSW_DFT selector, SAB_PVW_Key sab);
void sab_pvw_NCMUX(PVW_TMLWE out, PVW_TMLWE in1, PVW_TMLWE in2,
    MAT_TRGSW_DFT selector, SAB_PVW_Key sab);
void sab_pvw_RGSW_monomial_mul(PVW_TMLWE * p0, MAT_TRGSW_DFT * e,
    SAB_PVW_Key sab);
void sab_pvw_sub_a_binary(PVW_TMLWE * p, const uint64_t * a, SAB_PVW_Key sab);
void sab_pvw_sparse_mul_binary(PVW_TMLWE * p, const uint64_t * a,
    uint64_t a_idx, SAB_PVW_Key sab);
void sab_pvw_setup_tv_xb(PVW_TMLWE * acc, const uint64_t * b,
    PVW_TMLWE tv, SAB_PVW_Key sab);
void sab_pvw_blind_rotate_binary(PVW_TMLWE * out, TRLWE in, SAB_PVW_Key sab);
void sab_pvw_bootstrap_wo_extract_binary(PVW_TMLWE * out, TRLWE in,
    PVW_TMLWE tv, SAB_PVW_Key sab);
void sab_pvw_extract_pvwtlwe(PVW_TLWE * out, PVW_TMLWE * in, SAB_PVW_Key sab);
void sab_pvw_bootstrap_binary(TRLWE * out, TRLWE in, PVW_TMLWE tv,
    SAB_PVW_Key sab);
