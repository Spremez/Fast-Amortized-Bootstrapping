#include <sab_pvw.h>
/* scalar helper reused by blind_rotate_gaussian (defined in sab.c-side TU) */
void mod_switch_a(uint64_t * out, uint64_t * in, uint64_t prec, uint64_t size, bool round_to_odd);
#include <inttypes.h>
#include <string.h>
#include <sys/time.h>

#if defined(SAB_PVW_POSTPROC_PROFILE) || defined(SAB_PVW_BODY_PROFILE)
static uint64_t sab_pvw_now_us(void){
  struct timeval tv;
  gettimeofday(&tv, NULL);
  return (uint64_t) tv.tv_usec + (uint64_t) tv.tv_sec * 1000000ULL;
}
#endif

#ifdef SAB_PVW_POSTPROC_PROFILE
#define SAB_PVW_POSTPROC_TIME_ACC(ACC, CODE) \
  do { \
    const uint64_t __sab_pvw_begin = sab_pvw_now_us(); \
    CODE; \
    (ACC) += sab_pvw_now_us() - __sab_pvw_begin; \
  } while (0)
#else
#define SAB_PVW_POSTPROC_TIME_ACC(ACC, CODE) \
  do { \
    CODE; \
  } while (0)
#endif

#ifdef SAB_PVW_BODY_PROFILE
#define SAB_PVW_BODY_PROFILE_MAX_BITS 64
typedef struct {
  uint64_t setup_tv_xb_us, setup_tv_xb_calls;
  uint64_t blind_rotate_us, blind_rotate_calls;
  uint64_t sparse_mul_us, sparse_mul_calls;
  uint64_t rgsw_monomial_us, rgsw_monomial_calls;
  uint64_t cmux_us, cmux_calls;
  uint64_t ncmux_us, ncmux_calls;
  uint64_t cmux_sub_us, cmux_sub_calls;
  uint64_t cmux_from_dft_us, cmux_from_dft_calls;
  uint64_t cmux_add_us, cmux_add_calls;
  uint64_t ncmux_auto_us, ncmux_auto_calls;
  uint64_t mat_ep_us, mat_ep_calls;
  uint64_t sub_a_us, sub_a_calls;
  uint64_t sub_a_output_fusion_us, sub_a_output_fusion_calls;
  uint64_t sub_a_rotate_us, sub_a_rotate_calls;
  uint64_t sub_a_mul_minus_1_us, sub_a_mul_minus_1_calls;
  uint64_t sub_a_copy_us, sub_a_copy_calls;
  uint64_t sub_a_mat_ep_us, sub_a_mat_ep_calls;
  uint64_t sub_a_from_dft_us, sub_a_from_dft_calls;
  uint64_t sub_a_add_us, sub_a_add_calls;
  uint64_t dual_sub_pair_us, dual_sub_pair_calls;
  uint64_t schedule_fused_cmux_calls, schedule_fused_ncmux_calls;
  uint64_t copyback_us, copyback_calls;
  uint64_t bit_ncmux_us[SAB_PVW_BODY_PROFILE_MAX_BITS];
  uint64_t bit_ncmux_calls[SAB_PVW_BODY_PROFILE_MAX_BITS];
  uint64_t bit_direct_cmux_us[SAB_PVW_BODY_PROFILE_MAX_BITS];
  uint64_t bit_direct_cmux_calls[SAB_PVW_BODY_PROFILE_MAX_BITS];
} SAB_PVW_Body_Profile;

static SAB_PVW_Body_Profile sab_pvw_body_profile;

static void sab_pvw_body_profile_reset(void){
  memset(&sab_pvw_body_profile, 0, sizeof(sab_pvw_body_profile));
}

static void sab_pvw_body_profile_acc(uint64_t * us, uint64_t * calls,
    uint64_t begin_us){
  *us += sab_pvw_now_us() - begin_us;
  (*calls)++;
}

static void sab_pvw_body_profile_print(SAB_PVW_Key sab, uint64_t full_us){
  printf("SAB_PVW_BODY_PROFILE sample lanes=%" PRIu64
         " in_N=%" PRIu64
         " out_N=%" PRIu64
         " h=%" PRIu64
         " r_prec=%" PRIu64
         " full_us=%" PRIu64
         " setup_tv_xb_calls=%" PRIu64
         " setup_tv_xb_us=%" PRIu64
         " blind_rotate_calls=%" PRIu64
         " blind_rotate_us=%" PRIu64
         " sparse_mul_calls=%" PRIu64
         " sparse_mul_us=%" PRIu64
         " rgsw_monomial_calls=%" PRIu64
         " rgsw_monomial_us=%" PRIu64
         " cmux_calls=%" PRIu64
         " cmux_us=%" PRIu64
         " ncmux_calls=%" PRIu64
         " ncmux_us=%" PRIu64
         " cmux_sub_calls=%" PRIu64
         " cmux_sub_us=%" PRIu64
         " cmux_from_dft_calls=%" PRIu64
         " cmux_from_dft_us=%" PRIu64
         " cmux_add_calls=%" PRIu64
         " cmux_add_us=%" PRIu64
         " ncmux_auto_calls=%" PRIu64
         " ncmux_auto_us=%" PRIu64
         " mat_ep_calls=%" PRIu64
         " mat_ep_us=%" PRIu64
         " sub_a_calls=%" PRIu64
         " sub_a_us=%" PRIu64
         " sub_a_output_fusion_calls=%" PRIu64
         " sub_a_output_fusion_us=%" PRIu64
         " sub_a_rotate_calls=%" PRIu64
         " sub_a_rotate_us=%" PRIu64
         " sub_a_mul_minus_1_calls=%" PRIu64
         " sub_a_mul_minus_1_us=%" PRIu64
         " sub_a_copy_calls=%" PRIu64
         " sub_a_copy_us=%" PRIu64
         " sub_a_mat_ep_calls=%" PRIu64
         " sub_a_mat_ep_us=%" PRIu64
         " sub_a_from_dft_calls=%" PRIu64
         " sub_a_from_dft_us=%" PRIu64
         " sub_a_add_calls=%" PRIu64
         " sub_a_add_us=%" PRIu64
         " dual_sub_pair_calls=%" PRIu64
         " dual_sub_pair_us=%" PRIu64
         " schedule_fused_cmux_calls=%" PRIu64
         " schedule_fused_ncmux_calls=%" PRIu64
         " copyback_calls=%" PRIu64
         " copyback_us=%" PRIu64
         " profile_bit_capacity=%u",
         sab->lanes, sab->in_N, sab->out_N, sab->h, sab->r_prec, full_us,
         sab_pvw_body_profile.setup_tv_xb_calls,
         sab_pvw_body_profile.setup_tv_xb_us,
         sab_pvw_body_profile.blind_rotate_calls,
         sab_pvw_body_profile.blind_rotate_us,
         sab_pvw_body_profile.sparse_mul_calls,
         sab_pvw_body_profile.sparse_mul_us,
         sab_pvw_body_profile.rgsw_monomial_calls,
         sab_pvw_body_profile.rgsw_monomial_us,
         sab_pvw_body_profile.cmux_calls,
         sab_pvw_body_profile.cmux_us,
         sab_pvw_body_profile.ncmux_calls,
         sab_pvw_body_profile.ncmux_us,
         sab_pvw_body_profile.cmux_sub_calls,
         sab_pvw_body_profile.cmux_sub_us,
         sab_pvw_body_profile.cmux_from_dft_calls,
         sab_pvw_body_profile.cmux_from_dft_us,
         sab_pvw_body_profile.cmux_add_calls,
         sab_pvw_body_profile.cmux_add_us,
         sab_pvw_body_profile.ncmux_auto_calls,
         sab_pvw_body_profile.ncmux_auto_us,
         sab_pvw_body_profile.mat_ep_calls,
         sab_pvw_body_profile.mat_ep_us,
         sab_pvw_body_profile.sub_a_calls,
         sab_pvw_body_profile.sub_a_us,
         sab_pvw_body_profile.sub_a_output_fusion_calls,
         sab_pvw_body_profile.sub_a_output_fusion_us,
         sab_pvw_body_profile.sub_a_rotate_calls,
         sab_pvw_body_profile.sub_a_rotate_us,
         sab_pvw_body_profile.sub_a_mul_minus_1_calls,
         sab_pvw_body_profile.sub_a_mul_minus_1_us,
         sab_pvw_body_profile.sub_a_copy_calls,
         sab_pvw_body_profile.sub_a_copy_us,
         sab_pvw_body_profile.sub_a_mat_ep_calls,
         sab_pvw_body_profile.sub_a_mat_ep_us,
         sab_pvw_body_profile.sub_a_from_dft_calls,
         sab_pvw_body_profile.sub_a_from_dft_us,
         sab_pvw_body_profile.sub_a_add_calls,
         sab_pvw_body_profile.sub_a_add_us,
         sab_pvw_body_profile.dual_sub_pair_calls,
         sab_pvw_body_profile.dual_sub_pair_us,
         sab_pvw_body_profile.schedule_fused_cmux_calls,
         sab_pvw_body_profile.schedule_fused_ncmux_calls,
         sab_pvw_body_profile.copyback_calls,
         sab_pvw_body_profile.copyback_us,
         (unsigned) SAB_PVW_BODY_PROFILE_MAX_BITS);
  const uint64_t bits = sab->r_prec < SAB_PVW_BODY_PROFILE_MAX_BITS ?
      sab->r_prec : SAB_PVW_BODY_PROFILE_MAX_BITS;
  for (size_t bit = 0; bit < (size_t) bits; bit++){
    const uint64_t total_update_calls =
        sab_pvw_body_profile.bit_ncmux_calls[bit] +
        sab_pvw_body_profile.bit_direct_cmux_calls[bit];
    printf(" bit%zu_ncmux_calls=%" PRIu64
           " bit%zu_ncmux_us=%" PRIu64
           " bit%zu_direct_cmux_calls=%" PRIu64
           " bit%zu_direct_cmux_us=%" PRIu64
           " bit%zu_total_update_calls=%" PRIu64,
           bit, sab_pvw_body_profile.bit_ncmux_calls[bit],
           bit, sab_pvw_body_profile.bit_ncmux_us[bit],
           bit, sab_pvw_body_profile.bit_direct_cmux_calls[bit],
           bit, sab_pvw_body_profile.bit_direct_cmux_us[bit],
           bit, total_update_calls);
  }
  printf("\n");
}
#endif

static void sab_pvw_die(const char * msg){
  fprintf(stderr, "sab_pvw: %s\n", msg);
  exit(1);
}

typedef struct {
  PVW_TMLWE * buffers[2];
  uint64_t active;
  uint64_t in_N;
  uint64_t lanes;
  uint64_t r_prec;
} SAB_PVW_Accumulator_State;

static inline void sab_pvw_accumulator_check(
    const SAB_PVW_Accumulator_State * state, SAB_PVW_Key sab){
  if(state->in_N != sab->in_N || state->lanes != sab->lanes ||
      state->r_prec != sab->r_prec){
    sab_pvw_die("accumulator state metadata mismatch");
  }
}

static inline SAB_PVW_Accumulator_State sab_pvw_accumulator_state(
    PVW_TMLWE * primary, SAB_PVW_Key sab){
  SAB_PVW_Accumulator_State state = {
    {primary, sab->tmp->tmlwe_poly2},
    0,
    sab->in_N,
    sab->lanes,
    sab->r_prec,
  };
  sab_pvw_accumulator_check(&state, sab);
  return state;
}

static inline PVW_TMLWE * sab_pvw_accumulator_active(
    const SAB_PVW_Accumulator_State * state){
  return state->buffers[state->active];
}

static inline PVW_TMLWE * sab_pvw_accumulator_inactive(
    const SAB_PVW_Accumulator_State * state){
  return state->buffers[state->active ^ 1];
}

static inline void sab_pvw_accumulator_flip(
    SAB_PVW_Accumulator_State * state){
  state->active ^= 1;
}

static void sab_pvw_encrypt_bits(MAT_TRGSW_DFT * out, MAT_TRGSW tmp,
    MAT_TRGSW_Key key, uint64_t in, uint64_t prec){
  for (size_t bit = 0; bit < prec; bit++){
    const uint64_t val = (in >> bit) & 1;
    mat_trgsw_monomial_sample(tmp, val, 0, key);
    mat_trgsw_to_DFT(out[bit], tmp);
  }
}

#ifdef SAB_PVW_DELTA2_SCHEDULE
static MAT_TRGSW_DFT * sab_pvw_alloc_pair_indicators(uint64_t r_prec,
    uint64_t l, uint64_t bg_bit, uint64_t out_k, uint64_t lanes,
    uint64_t out_N){
  const uint64_t n_pairs = r_prec / 2;
  MAT_TRGSW_DFT * res =
      (MAT_TRGSW_DFT *) safe_malloc(sizeof(MAT_TRGSW_DFT) * 3 * n_pairs);
  for (size_t i = 0; i < 3 * n_pairs; i++){
    res[i] = mat_trgsw_alloc_new_DFT_sample((int) l, (int) bg_bit,
        (int) out_k, (int) lanes, (int) out_N);
  }
  return res;
}

/* Joint indicators of the bit pair (v_{2p}, v_{2p+1}) of d[t]; the (0,0)
 * case is the free torus addend and needs no selector. */
static void sab_pvw_encrypt_pair_indicators(MAT_TRGSW_DFT * out,
    MAT_TRGSW tmp, MAT_TRGSW_Key key, uint64_t in, uint64_t prec){
  for (size_t pair = 0; pair < prec / 2; pair++){
    const uint64_t v0 = (in >> (2 * pair)) & 1;
    const uint64_t v1 = (in >> (2 * pair + 1)) & 1;
    const uint64_t ind[3] = {v0 & (v1 ^ 1), (v0 ^ 1) & v1, v0 & v1};
    for (size_t m = 0; m < 3; m++){
      mat_trgsw_monomial_sample(tmp, (int64_t) ind[m], 0, key);
      mat_trgsw_to_DFT(out[3 * pair + m], tmp);
    }
  }
}
#endif

static inline int sab_pvw_coeff_is_minus_one(uint64_t coeff){
  return coeff == (uint64_t) -1;
}

static MAT_TRGSW_DFT * sab_pvw_alloc_selector_bits(uint64_t r_prec,
    uint64_t l, uint64_t bg_bit, uint64_t out_k, uint64_t lanes,
    uint64_t out_N){
  MAT_TRGSW_DFT * res = (MAT_TRGSW_DFT *) safe_malloc(sizeof(MAT_TRGSW_DFT) * r_prec);
  for (size_t bit = 0; bit < r_prec; bit++){
    res[bit] = mat_trgsw_alloc_new_DFT_sample(l, bg_bit, out_k, lanes, out_N);
  }
  return res;
}

static TRLWE_Key sab_pvw_trlwe_key_from_lane(PVW_TMLWE_Key in, uint64_t lane){
  const int N = in->s[0][lane]->N;
  TRLWE_Key out = trlwe_alloc_key(N, in->k, in->sigma);
  for (size_t idx = 0; idx < (size_t) in->k; idx++){
    polynomial_copy_torus_polynomial(out->s[idx], in->s[idx][lane]);
    polynomial_copy_DFT_polynomial(out->s_dft[idx], in->s_dft[idx][lane]);
  }
  return out;
}

static void sab_pvw_materialize_pvwtlwe_lane(TLWE out, PVW_TLWE in,
    uint64_t lane){
  for (size_t idx = 0; idx < (size_t) in->n; idx++){
    out->a[idx] = in->a[idx];
  }
  out->b = in->b[lane];
}

static void sab_pvw_extract_tlwe_lane(TLWE out, PVW_TMLWE in,
    uint64_t lane, uint64_t idx){
  const uint64_t N = (uint64_t) in->b[0]->N;
  const uint64_t k = (uint64_t) in->k;
  for (size_t key_idx = 0; key_idx < (size_t) k; key_idx++){
    for (size_t coeff = 0; coeff <= (size_t) idx; coeff++){
      out->a[key_idx * N + coeff] =
          in->a[key_idx]->coeffs[idx - coeff];
    }
    for (size_t coeff = (size_t) idx + 1; coeff < (size_t) N; coeff++){
      out->a[key_idx * N + coeff] =
          -in->a[key_idx]->coeffs[N + idx - coeff];
    }
  }
  out->b = in->b[lane]->coeffs[idx];
}

static void sab_pvw_extract_tlwe_lane_array(TLWE * out, PVW_TMLWE * in,
    uint64_t lane, SAB_PVW_Key sab){
  for (size_t idx = 0; idx < (size_t) sab->in_N; idx++){
    sab_pvw_extract_tlwe_lane(out[idx], in[idx], lane, 0);
  }
}

static void sab_pvw_init_full_postproc(SAB_PVW_Key sab, TRLWE_Key input_key,
    TRLWE_Key repacking_key, uint64_t b_packing, uint64_t ell_packing,
    uint64_t t_ks, uint64_t b_ks){
  sab->packing_keys = (TRLWE_KS_Key *) safe_malloc(
      sizeof(TRLWE_KS_Key) * sab->lanes);
  for (size_t lane = 0; lane < sab->lanes; lane++){
    TRLWE_Key lane_key = sab_pvw_trlwe_key_from_lane(sab->output_key, lane);
    TLWE_Key extracted_key = tlwe_alloc_key(sab->out_N * sab->out_k,
        lane_key->sigma);
    trlwe_extract_tlwe_key(extracted_key, lane_key);
    sab->packing_keys[lane] = trlwe_new_full_packing_KS_key(repacking_key,
        extracted_key, ell_packing, b_packing);
    free_tlwe_key(extracted_key);
    free_trlwe_key(lane_key);
  }
  sab->hw_reducing_key = trlwe_new_KS_key(input_key, repacking_key,
      t_ks, b_ks);

  sab->tmp->acc = pvmtmlwe_alloc_new_sample_array(sab->in_N, sab->out_k,
      sab->lanes, sab->out_N);
  sab->tmp->extracted = pvwtlwe_alloc_sample_array(sab->in_N,
      sab->out_N * sab->out_k, sab->lanes);
  sab->tmp->lane_extracted = (TLWE **) safe_malloc(sizeof(TLWE *) * sab->lanes);
  for (size_t lane = 0; lane < sab->lanes; lane++){
    sab->tmp->lane_extracted[lane] = tlwe_alloc_sample_array(sab->in_N,
        sab->out_N * sab->out_k);
  }
  sab->tmp->packed = trlwe_alloc_new_sample(sab->in_k, sab->in_N);
}

SAB_PVW_Key sab_pvw_new_binary_key(TRLWE_Key input_key, PVW_TMLWE_Key output_key,
    uint64_t b_prec, uint64_t h, uint64_t r_prec, uint64_t l, uint64_t bg_bit){
  if(input_key == NULL) sab_pvw_die("input key is NULL");
  if(output_key == NULL) sab_pvw_die("output key is NULL");
  if(r_prec == 0) sab_pvw_die("r_prec must be non-zero");

  SAB_PVW_Key res = (SAB_PVW_Key) safe_malloc(sizeof(*res));
  const uint64_t in_N = input_key->s[0]->N;
  const uint64_t in_k = input_key->k;
  const uint64_t out_N = output_key->s[0][0]->N;
  const uint64_t out_k = output_key->k;
  const uint64_t lanes = output_key->r;
  const uint64_t r_max = 1ULL << r_prec;

  res->output_key = output_key;
  res->mat_key = mat_trgsw_new_key(output_key, l, bg_bit);
  res->aut_minus1 = pvmtmlwe_new_automorphism_KS_key(output_key,
      2 * out_N - 1, l, bg_bit);
  res->packing_keys = NULL;
  res->hw_reducing_key = NULL;
  res->include_zeros = false;
  res->ternary_secret = false;
  res->s_coff = NULL;
  res->s_sign = NULL;
  res->s_pairs = NULL;
  res->gaussian_secret = false;
  res->aut_family = NULL;

  MAT_TRGSW tmp = mat_trgsw_alloc_new_sample(l, bg_bit, out_k, lanes, out_N);
  res->s = (MAT_TRGSW_DFT ***) safe_malloc(sizeof(MAT_TRGSW_DFT **) * in_k);
#ifdef SAB_PVW_DELTA2_SCHEDULE
  res->s_pairs =
      (MAT_TRGSW_DFT ***) safe_malloc(sizeof(MAT_TRGSW_DFT **) * in_k);
#endif
  for (size_t key_idx = 0; key_idx < in_k; key_idx++){
    res->s[key_idx] = (MAT_TRGSW_DFT **) safe_malloc(sizeof(MAT_TRGSW_DFT *) * (h + 1));
#ifdef SAB_PVW_DELTA2_SCHEDULE
    res->s_pairs[key_idx] =
        (MAT_TRGSW_DFT **) safe_malloc(sizeof(MAT_TRGSW_DFT *) * (h + 1));
#endif
    uint64_t cnt_h = 0;
    uint64_t previous = in_N;
    for (size_t scan = 0; scan < in_N; scan++){
      const uint64_t current = in_N - scan - 1;
      const uint64_t coeff = input_key->s[key_idx]->coeffs[current];
      if(coeff == 0) continue;
      if(coeff != 1) sab_pvw_die("only binary sparse input keys are supported");
      if(cnt_h >= h) sab_pvw_die("input key has more non-zero coefficients than h");
      const uint64_t r_diff = previous - current;
      if(r_diff >= r_max) sab_pvw_die("input key monomial gap exceeds r_prec");
      res->s[key_idx][cnt_h] = sab_pvw_alloc_selector_bits(r_prec, l,
          bg_bit, out_k, lanes, out_N);
      sab_pvw_encrypt_bits(res->s[key_idx][cnt_h], tmp, res->mat_key,
          r_diff, r_prec);
#ifdef SAB_PVW_DELTA2_SCHEDULE
      res->s_pairs[key_idx][cnt_h] = sab_pvw_alloc_pair_indicators(r_prec,
          l, bg_bit, out_k, lanes, out_N);
      sab_pvw_encrypt_pair_indicators(res->s_pairs[key_idx][cnt_h], tmp,
          res->mat_key, r_diff, r_prec);
#endif
      previous = current;
      cnt_h++;
    }
    if(cnt_h != h) sab_pvw_die("input key has fewer non-zero coefficients than h");
    if(previous >= r_max) sab_pvw_die("final monomial gap exceeds r_prec");
    res->s[key_idx][cnt_h] = sab_pvw_alloc_selector_bits(r_prec, l,
        bg_bit, out_k, lanes, out_N);
    sab_pvw_encrypt_bits(res->s[key_idx][cnt_h], tmp, res->mat_key,
        previous, r_prec);
#ifdef SAB_PVW_DELTA2_SCHEDULE
    res->s_pairs[key_idx][cnt_h] = sab_pvw_alloc_pair_indicators(r_prec,
        l, bg_bit, out_k, lanes, out_N);
    sab_pvw_encrypt_pair_indicators(res->s_pairs[key_idx][cnt_h], tmp,
        res->mat_key, previous, r_prec);
#endif
  }
  free_mat_trgsw(tmp);

  res->in_N = in_N;
  res->in_k = in_k;
  res->out_N = out_N;
  res->out_k = out_k;
  res->lanes = lanes;
  res->h = h;
  res->r_prec = r_prec;
  res->b_prec = b_prec;

  res->tmp = (sab_pvw_tmp_pool) safe_malloc(sizeof(*res->tmp));
  res->tmp->tmlwe_dft = pvmtmlwe_alloc_new_DFT_sample(out_k, lanes, out_N);
  res->tmp->tmlwe = pvmtmlwe_alloc_new_sample(out_k, lanes, out_N);
  res->tmp->rotated = pvmtmlwe_alloc_new_sample(out_k, lanes, out_N);
  res->tmp->tmlwe_poly2 = pvmtmlwe_alloc_new_sample_array(in_N, out_k, lanes, out_N);
  res->tmp->acc = NULL;
  res->tmp->extracted = NULL;
  res->tmp->lane_extracted = NULL;
  res->tmp->packed = NULL;
  res->tmp->scratch = mat_trgsw_alloc_mul_scratch((out_k + lanes) * l, out_N);
  res->tmp->a_mod = (uint64_t *) safe_malloc(sizeof(uint64_t) * in_N);
  return res;
}

SAB_PVW_Key sab_pvw_new_nonbinary_key(TRLWE_Key input_key,
    PVW_TMLWE_Key output_key, uint64_t b_prec, uint64_t h,
    uint64_t r_prec, uint64_t l, uint64_t bg_bit, bool include_zeros,
    bool ternary){
  if(input_key == NULL) sab_pvw_die("input key is NULL");
  if(output_key == NULL) sab_pvw_die("output key is NULL");
  if(r_prec == 0) sab_pvw_die("r_prec must be non-zero");
  if(include_zeros && ternary){
    sab_pvw_die("include-zero and ternary PVW modes must be tested separately");
  }
  if(!include_zeros && !ternary){
    return sab_pvw_new_binary_key(input_key, output_key, b_prec, h,
        r_prec, l, bg_bit);
  }

  SAB_PVW_Key res = (SAB_PVW_Key) safe_malloc(sizeof(*res));
  const uint64_t in_N = input_key->s[0]->N;
  const uint64_t in_k = input_key->k;
  const uint64_t out_N = output_key->s[0][0]->N;
  const uint64_t out_k = output_key->k;
  const uint64_t lanes = output_key->r;
  const uint64_t r_max = 1ULL << r_prec;

  res->output_key = output_key;
  res->mat_key = mat_trgsw_new_key(output_key, l, bg_bit);
  res->aut_minus1 = pvmtmlwe_new_automorphism_KS_key(output_key,
      2 * out_N - 1, l, bg_bit);
  res->packing_keys = NULL;
  res->hw_reducing_key = NULL;
  res->include_zeros = include_zeros;
  res->ternary_secret = ternary;
  res->s_coff = include_zeros ?
      (MAT_TRGSW_DFT **) safe_malloc(sizeof(MAT_TRGSW_DFT *) * in_k) :
      NULL;
  res->s_sign = ternary ?
      (MAT_TRGSW_DFT **) safe_malloc(sizeof(MAT_TRGSW_DFT *) * in_k) :
      NULL;
  res->s_pairs = NULL;

  MAT_TRGSW tmp = mat_trgsw_alloc_new_sample(l, bg_bit, out_k, lanes, out_N);
  res->s = (MAT_TRGSW_DFT ***) safe_malloc(sizeof(MAT_TRGSW_DFT **) * in_k);
  for (size_t key_idx = 0; key_idx < in_k; key_idx++){
    res->s[key_idx] = (MAT_TRGSW_DFT **) safe_malloc(sizeof(MAT_TRGSW_DFT *) * (h + 1));
    if(include_zeros){
      res->s_coff[key_idx] = (MAT_TRGSW_DFT *) safe_malloc(sizeof(MAT_TRGSW_DFT) * h);
    }
    if(ternary){
      res->s_sign[key_idx] = (MAT_TRGSW_DFT *) safe_malloc(sizeof(MAT_TRGSW_DFT) * h);
    }
    uint64_t cnt_h = 0;
    uint64_t previous = in_N;
    for (size_t scan = 0; scan < in_N; scan++){
      const uint64_t current = in_N - scan - 1;
      const uint64_t coeff = input_key->s[key_idx]->coeffs[current];
      if(coeff == 0) continue;
      if(include_zeros && coeff != 1){
        sab_pvw_die("include-zero PVW sparse input expects coefficient one");
      }
      if(ternary && coeff != 1 && !sab_pvw_coeff_is_minus_one(coeff)){
        sab_pvw_die("ternary PVW sparse input expects +/-1 coefficients");
      }
      if(cnt_h >= h) sab_pvw_die("input key has more non-zero coefficients than h");
      const uint64_t r_diff = previous - current;
      if(r_diff >= r_max){
        sab_pvw_die("input key monomial gap exceeds r_prec");
      }
      res->s[key_idx][cnt_h] = sab_pvw_alloc_selector_bits(r_prec, l,
          bg_bit, out_k, lanes, out_N);
      sab_pvw_encrypt_bits(res->s[key_idx][cnt_h], tmp, res->mat_key,
          r_diff, r_prec);
      if(include_zeros){
        res->s_coff[key_idx][cnt_h] =
            mat_trgsw_alloc_new_DFT_sample(l, bg_bit, out_k, lanes, out_N);
        mat_trgsw_monomial_DFT_sample(res->s_coff[key_idx][cnt_h],
            1, 0, res->mat_key);
      }
      if(ternary){
        res->s_sign[key_idx][cnt_h] =
            mat_trgsw_alloc_new_DFT_sample(l, bg_bit, out_k, lanes, out_N);
        mat_trgsw_monomial_DFT_sample(res->s_sign[key_idx][cnt_h],
            sab_pvw_coeff_is_minus_one(coeff) ? 1 : 0, 0, res->mat_key);
      }
      previous = current;
      cnt_h++;
    }
    if(cnt_h != h) sab_pvw_die("input key has fewer non-zero coefficients than h");
    if(previous >= r_max) sab_pvw_die("final monomial gap exceeds r_prec");
    res->s[key_idx][cnt_h] = sab_pvw_alloc_selector_bits(r_prec, l,
        bg_bit, out_k, lanes, out_N);
    sab_pvw_encrypt_bits(res->s[key_idx][cnt_h], tmp, res->mat_key,
        previous, r_prec);
  }
  free_mat_trgsw(tmp);

  res->in_N = in_N;
  res->in_k = in_k;
  res->out_N = out_N;
  res->out_k = out_k;
  res->lanes = lanes;
  res->h = h;
  res->r_prec = r_prec;
  res->b_prec = b_prec;

  res->tmp = (sab_pvw_tmp_pool) safe_malloc(sizeof(*res->tmp));
  res->tmp->tmlwe_dft = pvmtmlwe_alloc_new_DFT_sample(out_k, lanes, out_N);
  res->tmp->tmlwe = pvmtmlwe_alloc_new_sample(out_k, lanes, out_N);
  res->tmp->rotated = pvmtmlwe_alloc_new_sample(out_k, lanes, out_N);
  res->tmp->tmlwe_poly2 = pvmtmlwe_alloc_new_sample_array(in_N, out_k, lanes, out_N);
  res->tmp->acc = NULL;
  res->tmp->extracted = NULL;
  res->tmp->lane_extracted = NULL;
  res->tmp->packed = NULL;
  res->tmp->scratch = mat_trgsw_alloc_mul_scratch((out_k + lanes) * l, out_N);
  res->tmp->a_mod = (uint64_t *) safe_malloc(sizeof(uint64_t) * in_N);
  return res;
}

SAB_PVW_Key sab_pvw_new_binary_full_key(TRLWE_Key input_key,
    TRLWE_Key repacking_key, PVW_TMLWE_Key output_key, uint64_t b_prec,
    uint64_t b_packing, uint64_t ell_packing, uint64_t t_ks, uint64_t b_ks,
    uint64_t h, uint64_t r_prec, uint64_t l, uint64_t bg_bit){
  if(repacking_key == NULL) sab_pvw_die("repacking key is NULL");
  SAB_PVW_Key res = sab_pvw_new_binary_key(input_key, output_key, b_prec,
      h, r_prec, l, bg_bit);
  sab_pvw_init_full_postproc(res, input_key, repacking_key, b_packing,
      ell_packing, t_ks, b_ks);
  return res;
}

SAB_PVW_Key sab_pvw_new_nonbinary_full_key(TRLWE_Key input_key,
    TRLWE_Key repacking_key, PVW_TMLWE_Key output_key, uint64_t b_prec,
    uint64_t b_packing, uint64_t ell_packing, uint64_t t_ks, uint64_t b_ks,
    uint64_t h, uint64_t r_prec, uint64_t l, uint64_t bg_bit,
    bool include_zeros, bool ternary){
  if(repacking_key == NULL) sab_pvw_die("repacking key is NULL");
  SAB_PVW_Key res = sab_pvw_new_nonbinary_key(input_key, output_key, b_prec,
      h, r_prec, l, bg_bit, include_zeros, ternary);
  sab_pvw_init_full_postproc(res, input_key, repacking_key, b_packing,
      ell_packing, t_ks, b_ks);
  return res;
}

void free_sab_pvw_key(SAB_PVW_Key sab){
  if(sab == NULL) return;
  for (size_t key_idx = 0; key_idx < sab->in_k; key_idx++){
    for (size_t step = 0; step < sab->h + 1; step++){
      for (size_t bit = 0; bit < sab->r_prec; bit++){
        free_mat_trgsw_DFT(sab->s[key_idx][step][bit]);
      }
      free(sab->s[key_idx][step]);
    }
    free(sab->s[key_idx]);
  }
  free(sab->s);
  if(sab->s_coff != NULL){
    for (size_t key_idx = 0; key_idx < sab->in_k; key_idx++){
      for (size_t step = 0; step < sab->h; step++){
        free_mat_trgsw_DFT(sab->s_coff[key_idx][step]);
      }
      free(sab->s_coff[key_idx]);
    }
    free(sab->s_coff);
  }
  if(sab->s_sign != NULL){
    for (size_t key_idx = 0; key_idx < sab->in_k; key_idx++){
      for (size_t step = 0; step < sab->h; step++){
        free_mat_trgsw_DFT(sab->s_sign[key_idx][step]);
      }
      free(sab->s_sign[key_idx]);
    }
    free(sab->s_sign);
  }
  if(sab->s_coff != NULL){
    for (size_t key_idx = 0; key_idx < sab->in_k; key_idx++){
      for (size_t step = 0; step < sab->h; step++){
        free_mat_trgsw_DFT(sab->s_coff[key_idx][step]);
      }
      free(sab->s_coff[key_idx]);
    }
    free(sab->s_coff);
  }
  if(sab->aut_family != NULL){
    for (size_t w_idx = 0; w_idx < sab->out_N; w_idx++){
      free_pvmtmlwe_ks_key(sab->aut_family[w_idx]);
    }
    free(sab->aut_family);
  }
  if(sab->s_pairs != NULL){
    const uint64_t n_sel = 3 * (sab->r_prec / 2);
    for (size_t key_idx = 0; key_idx < sab->in_k; key_idx++){
      for (size_t step = 0; step <= sab->h; step++){
        for (size_t i = 0; i < n_sel; i++){
          free_mat_trgsw_DFT(sab->s_pairs[key_idx][step][i]);
        }
        free(sab->s_pairs[key_idx][step]);
      }
      free(sab->s_pairs[key_idx]);
    }
    free(sab->s_pairs);
  }
  free_mat_trgsw_mul_scratch(sab->tmp->scratch);
  free(sab->tmp->a_mod);
  if(sab->tmp->packed != NULL) free_trlwe(sab->tmp->packed);
  if(sab->tmp->lane_extracted != NULL){
    for (size_t lane = 0; lane < sab->lanes; lane++){
      free_tlwe_array(sab->tmp->lane_extracted[lane], sab->in_N);
    }
    free(sab->tmp->lane_extracted);
  }
  if(sab->tmp->extracted != NULL){
    free_pvwtlwe_array(sab->tmp->extracted, sab->in_N);
  }
  if(sab->tmp->acc != NULL){
    free_pvmtmlwe_array(sab->tmp->acc, sab->in_N);
  }
  free_pvmtmlwe_array(sab->tmp->tmlwe_poly2, sab->in_N);
  free_pvmtmlwe(sab->tmp->rotated);
  free_pvmtmlwe(sab->tmp->tmlwe);
  free_pvmtmlwe_DFT(sab->tmp->tmlwe_dft);
  free(sab->tmp);
  if(sab->hw_reducing_key != NULL) free_trlwe_ks_key(sab->hw_reducing_key);
  if(sab->packing_keys != NULL){
    for (size_t lane = 0; lane < sab->lanes; lane++){
      free_trlwe_ks_key(sab->packing_keys[lane]);
    }
    free(sab->packing_keys);
  }
  free_pvmtmlwe_ks_key(sab->aut_minus1);
  free_mat_trgsw_key(sab->mat_key);
  free(sab);
}

static void sab_pvw_CMUX_materialize_internal(PVW_TMLWE out,
    PVW_TMLWE addend, SAB_PVW_Key sab, int prefer_fused_from_dft_add){
#ifdef SAB_PVW_BODY_PROFILE
  const uint64_t cmux_from_dft_begin = sab_pvw_now_us();
#endif
  if(prefer_fused_from_dft_add && out != addend){
    pvmtmlwe_from_DFT_add(out, sab->tmp->tmlwe_dft, addend);
#ifdef SAB_PVW_BODY_PROFILE
    sab_pvw_body_profile_acc(&sab_pvw_body_profile.cmux_from_dft_us,
        &sab_pvw_body_profile.cmux_from_dft_calls, cmux_from_dft_begin);
    sab_pvw_body_profile.cmux_add_calls++;
#endif
  }else{
    pvmtmlwe_from_DFT(sab->tmp->tmlwe, sab->tmp->tmlwe_dft);
#ifdef SAB_PVW_BODY_PROFILE
    sab_pvw_body_profile_acc(&sab_pvw_body_profile.cmux_from_dft_us,
        &sab_pvw_body_profile.cmux_from_dft_calls, cmux_from_dft_begin);
    const uint64_t cmux_add_begin = sab_pvw_now_us();
#endif
    pvmtmlwe_add(out, sab->tmp->tmlwe, addend);
#ifdef SAB_PVW_BODY_PROFILE
    sab_pvw_body_profile_acc(&sab_pvw_body_profile.cmux_add_us,
        &sab_pvw_body_profile.cmux_add_calls, cmux_add_begin);
#endif
  }
}

static void sab_pvw_CMUX_from_sub_internal(PVW_TMLWE out, PVW_TMLWE addend,
    PVW_TMLWE sub, MAT_TRGSW_DFT selector, SAB_PVW_Key sab,
    int prefer_fused_from_dft_add){
#ifdef SAB_PVW_BODY_PROFILE
  const uint64_t mat_ep_begin = sab_pvw_now_us();
#endif
  mat_trgsw_mul_pvmtmlwe_DFT(sab->tmp->tmlwe_dft, sub,
      selector, sab->tmp->scratch);
#ifdef SAB_PVW_BODY_PROFILE
  sab_pvw_body_profile_acc(&sab_pvw_body_profile.mat_ep_us,
      &sab_pvw_body_profile.mat_ep_calls, mat_ep_begin);
#endif
  sab_pvw_CMUX_materialize_internal(out, addend, sab,
      prefer_fused_from_dft_add);
}

#ifdef SAB_PVW_SUB_DECOMP_FUSION
static void sab_pvw_CMUX_from_diff_internal(PVW_TMLWE out, PVW_TMLWE addend,
    PVW_TMLWE in1, PVW_TMLWE in2, MAT_TRGSW_DFT selector, SAB_PVW_Key sab,
    int prefer_fused_from_dft_add){
#ifdef SAB_PVW_BODY_PROFILE
  sab_pvw_body_profile.cmux_sub_calls++;
  const uint64_t mat_ep_begin = sab_pvw_now_us();
#endif
  mat_trgsw_mul_pvmtmlwe_sub_DFT(sab->tmp->tmlwe_dft, in1, in2,
      selector, sab->tmp->scratch);
#ifdef SAB_PVW_BODY_PROFILE
  sab_pvw_body_profile_acc(&sab_pvw_body_profile.mat_ep_us,
      &sab_pvw_body_profile.mat_ep_calls, mat_ep_begin);
#endif
  sab_pvw_CMUX_materialize_internal(out, addend, sab,
      prefer_fused_from_dft_add);
}
#endif

static void sab_pvw_CMUX_internal(PVW_TMLWE out, PVW_TMLWE in1,
    PVW_TMLWE in2, MAT_TRGSW_DFT selector, SAB_PVW_Key sab,
    int prefer_fused_from_dft_add){
#ifdef SAB_PVW_BODY_PROFILE
  const uint64_t cmux_begin = sab_pvw_now_us();
#endif
#ifdef SAB_PVW_SUB_DECOMP_FUSION
  sab_pvw_CMUX_from_diff_internal(out, in1, in1, in2, selector, sab,
      prefer_fused_from_dft_add);
#else
#ifdef SAB_PVW_BODY_PROFILE
  const uint64_t cmux_sub_begin = sab_pvw_now_us();
#endif
  pvmtmlwe_sub(sab->tmp->tmlwe, in2, in1);
#ifdef SAB_PVW_BODY_PROFILE
  sab_pvw_body_profile_acc(&sab_pvw_body_profile.cmux_sub_us,
      &sab_pvw_body_profile.cmux_sub_calls, cmux_sub_begin);
#endif
  sab_pvw_CMUX_from_sub_internal(out, in1, sab->tmp->tmlwe,
      selector, sab, prefer_fused_from_dft_add);
#endif
#ifdef SAB_PVW_BODY_PROFILE
  sab_pvw_body_profile_acc(&sab_pvw_body_profile.cmux_us,
      &sab_pvw_body_profile.cmux_calls, cmux_begin);
#endif
}

void sab_pvw_CMUX(PVW_TMLWE out, PVW_TMLWE in1, PVW_TMLWE in2,
    MAT_TRGSW_DFT selector, SAB_PVW_Key sab){
#if defined(SAB_PVW_FUSED_FROM_DFT_ADD)
  sab_pvw_CMUX_internal(out, in1, in2, selector, sab, 1);
#else
  sab_pvw_CMUX_internal(out, in1, in2, selector, sab, 0);
#endif
}

void sab_pvw_NCMUX(PVW_TMLWE out, PVW_TMLWE in1, PVW_TMLWE in2,
    MAT_TRGSW_DFT selector, SAB_PVW_Key sab){
#ifdef SAB_PVW_BODY_PROFILE
  const uint64_t ncmux_begin = sab_pvw_now_us();
  const uint64_t ncmux_auto_begin = sab_pvw_now_us();
#endif
  pvmtmlwe_eval_automorphism(sab->tmp->rotated, in2,
      2 * in2->b[0]->N - 1, sab->aut_minus1);
#ifdef SAB_PVW_BODY_PROFILE
  sab_pvw_body_profile_acc(&sab_pvw_body_profile.ncmux_auto_us,
      &sab_pvw_body_profile.ncmux_auto_calls, ncmux_auto_begin);
#endif
  sab_pvw_CMUX(out, in1, sab->tmp->rotated, selector, sab);
#ifdef SAB_PVW_BODY_PROFILE
  sab_pvw_body_profile_acc(&sab_pvw_body_profile.ncmux_us,
      &sab_pvw_body_profile.ncmux_calls, ncmux_begin);
#endif
}

static void sab_pvw_schedule_CMUX(PVW_TMLWE out, PVW_TMLWE in1,
    PVW_TMLWE in2, MAT_TRGSW_DFT selector, SAB_PVW_Key sab){
#ifdef SAB_PVW_BODY_PROFILE
  sab_pvw_body_profile.schedule_fused_cmux_calls++;
#endif
  sab_pvw_CMUX_internal(out, in1, in2, selector, sab, 1);
}

static void sab_pvw_schedule_NCMUX(PVW_TMLWE out, PVW_TMLWE in1,
    PVW_TMLWE in2, MAT_TRGSW_DFT selector, SAB_PVW_Key sab){
#ifdef SAB_PVW_BODY_PROFILE
  const uint64_t ncmux_begin = sab_pvw_now_us();
  const uint64_t ncmux_auto_begin = sab_pvw_now_us();
  sab_pvw_body_profile.schedule_fused_ncmux_calls++;
#endif
  pvmtmlwe_eval_automorphism(sab->tmp->rotated, in2,
      2 * in2->b[0]->N - 1, sab->aut_minus1);
#ifdef SAB_PVW_BODY_PROFILE
  sab_pvw_body_profile_acc(&sab_pvw_body_profile.ncmux_auto_us,
      &sab_pvw_body_profile.ncmux_auto_calls, ncmux_auto_begin);
#endif
  sab_pvw_CMUX_internal(out, in1, sab->tmp->rotated, selector, sab, 1);
#ifdef SAB_PVW_BODY_PROFILE
  sab_pvw_body_profile_acc(&sab_pvw_body_profile.ncmux_us,
      &sab_pvw_body_profile.ncmux_calls, ncmux_begin);
#endif
}

#ifdef SAB_PVW_DUAL_SUB_CMUX
static void sab_pvw_dual_sub_shared(PVW_TMLWE out_rot_minus_shared,
    PVW_TMLWE out_shared_minus_direct, PVW_TMLWE rotated_tail,
    PVW_TMLWE shared, PVW_TMLWE direct_rhs){
  const int N = shared->b[0]->N;
#if defined(AVX512_OPT) && !defined(TORUS32)
  const size_t blocks = (size_t) N / 8;
  for (size_t idx = 0; idx < (size_t) shared->k; idx++){
    const __m512i * rot = (const __m512i *) rotated_tail->a[idx]->coeffs;
    const __m512i * sh = (const __m512i *) shared->a[idx]->coeffs;
    const __m512i * rhs = (const __m512i *) direct_rhs->a[idx]->coeffs;
    __m512i * out_n = (__m512i *) out_rot_minus_shared->a[idx]->coeffs;
    __m512i * out_d = (__m512i *) out_shared_minus_direct->a[idx]->coeffs;
    for (size_t block = 0; block < blocks; block++){
      const __m512i v_rot = rot[block];
      const __m512i v_shared = sh[block];
      const __m512i v_rhs = rhs[block];
      out_n[block] = _mm512_sub_epi64(v_rot, v_shared);
      out_d[block] = _mm512_sub_epi64(v_shared, v_rhs);
    }
  }
  for (size_t lane = 0; lane < (size_t) shared->r; lane++){
    const __m512i * rot = (const __m512i *) rotated_tail->b[lane]->coeffs;
    const __m512i * sh = (const __m512i *) shared->b[lane]->coeffs;
    const __m512i * rhs = (const __m512i *) direct_rhs->b[lane]->coeffs;
    __m512i * out_n = (__m512i *) out_rot_minus_shared->b[lane]->coeffs;
    __m512i * out_d = (__m512i *) out_shared_minus_direct->b[lane]->coeffs;
    for (size_t block = 0; block < blocks; block++){
      const __m512i v_rot = rot[block];
      const __m512i v_shared = sh[block];
      const __m512i v_rhs = rhs[block];
      out_n[block] = _mm512_sub_epi64(v_rot, v_shared);
      out_d[block] = _mm512_sub_epi64(v_shared, v_rhs);
    }
  }
#else
  for (size_t idx = 0; idx < (size_t) shared->k; idx++){
    for (size_t coeff = 0; coeff < (size_t) N; coeff++){
      const Torus v_rot = rotated_tail->a[idx]->coeffs[coeff];
      const Torus v_shared = shared->a[idx]->coeffs[coeff];
      const Torus v_rhs = direct_rhs->a[idx]->coeffs[coeff];
      out_rot_minus_shared->a[idx]->coeffs[coeff] = v_rot - v_shared;
      out_shared_minus_direct->a[idx]->coeffs[coeff] = v_shared - v_rhs;
    }
  }
  for (size_t lane = 0; lane < (size_t) shared->r; lane++){
    for (size_t coeff = 0; coeff < (size_t) N; coeff++){
      const Torus v_rot = rotated_tail->b[lane]->coeffs[coeff];
      const Torus v_shared = shared->b[lane]->coeffs[coeff];
      const Torus v_rhs = direct_rhs->b[lane]->coeffs[coeff];
      out_rot_minus_shared->b[lane]->coeffs[coeff] = v_rot - v_shared;
      out_shared_minus_direct->b[lane]->coeffs[coeff] = v_shared - v_rhs;
    }
  }
#endif
}

static void sab_pvw_schedule_dual_sub_pair(PVW_TMLWE out_ncmux,
    PVW_TMLWE out_direct, PVW_TMLWE shared, PVW_TMLWE ncmux_rhs,
    PVW_TMLWE direct_rhs, MAT_TRGSW_DFT selector, SAB_PVW_Key sab){
#ifdef SAB_PVW_BODY_PROFILE
  const uint64_t ncmux_begin = sab_pvw_now_us();
  const uint64_t ncmux_auto_begin = sab_pvw_now_us();
  sab_pvw_body_profile.schedule_fused_ncmux_calls++;
  sab_pvw_body_profile.schedule_fused_cmux_calls++;
#endif
  pvmtmlwe_eval_automorphism(sab->tmp->rotated, ncmux_rhs,
      2 * ncmux_rhs->b[0]->N - 1, sab->aut_minus1);
#ifdef SAB_PVW_BODY_PROFILE
  sab_pvw_body_profile_acc(&sab_pvw_body_profile.ncmux_auto_us,
      &sab_pvw_body_profile.ncmux_auto_calls, ncmux_auto_begin);
  const uint64_t dual_sub_begin = sab_pvw_now_us();
#endif
  sab_pvw_dual_sub_shared(sab->tmp->tmlwe, sab->tmp->rotated,
      sab->tmp->rotated, shared, direct_rhs);
#ifdef SAB_PVW_BODY_PROFILE
  const uint64_t dual_sub_elapsed = sab_pvw_now_us() - dual_sub_begin;
  sab_pvw_body_profile.cmux_sub_us += dual_sub_elapsed;
  sab_pvw_body_profile.cmux_sub_calls += 2;
  sab_pvw_body_profile.dual_sub_pair_us += dual_sub_elapsed;
  sab_pvw_body_profile.dual_sub_pair_calls++;
  const uint64_t ncmux_cmux_begin = sab_pvw_now_us();
#endif
  sab_pvw_CMUX_from_sub_internal(out_ncmux, shared, sab->tmp->tmlwe,
      selector, sab, 1);
#ifdef SAB_PVW_BODY_PROFILE
  sab_pvw_body_profile_acc(&sab_pvw_body_profile.cmux_us,
      &sab_pvw_body_profile.cmux_calls, ncmux_cmux_begin);
  sab_pvw_body_profile_acc(&sab_pvw_body_profile.ncmux_us,
      &sab_pvw_body_profile.ncmux_calls, ncmux_begin);
  const uint64_t direct_cmux_begin = sab_pvw_now_us();
#endif
  sab_pvw_CMUX_from_sub_internal(out_direct, direct_rhs, sab->tmp->rotated,
      selector, sab, 1);
#ifdef SAB_PVW_BODY_PROFILE
  sab_pvw_body_profile_acc(&sab_pvw_body_profile.cmux_us,
      &sab_pvw_body_profile.cmux_calls, direct_cmux_begin);
#endif
}
#endif

static uint64_t sab_pvw_RGSW_monomial_mul_state(PVW_TMLWE * p[2],
    uint64_t active, MAT_TRGSW_DFT * e, SAB_PVW_Key sab){
#ifdef SAB_PVW_BODY_PROFILE
  const uint64_t rgsw_begin = sab_pvw_now_us();
#endif
  const uint32_t r_prec = sab->r_prec, in_N = sab->in_N;
  for (size_t bit = 0; bit < r_prec; bit++){
    const uint64_t power = 1ULL << bit;
    const uint64_t in = active ^ (bit & 1);
    const uint64_t out = in ^ 1;
    size_t direct_start = 0;
#ifdef SAB_PVW_BODY_PROFILE
    const uint64_t ncmux_loop_begin = sab_pvw_now_us();
#endif
#ifdef SAB_PVW_DUAL_SUB_CMUX
    if(2 * power <= in_N){
      for (size_t j = 0; j < power; j++){
        sab_pvw_schedule_dual_sub_pair(p[out][j], p[out][j + power],
            p[in][j], p[in][in_N - power + j], p[in][j + power],
            e[bit], sab);
      }
      direct_start = power;
    }else
#endif
    {
      for (size_t j = 0; j < power; j++){
#ifdef SAB_PVW_SCHEDULE_FUSED_CMUX
        sab_pvw_schedule_NCMUX(p[out][j], p[in][j], p[in][in_N - power + j],
            e[bit], sab);
#else
        sab_pvw_NCMUX(p[out][j], p[in][j], p[in][in_N - power + j],
            e[bit], sab);
#endif
      }
    }
#ifdef SAB_PVW_BODY_PROFILE
    if(bit < SAB_PVW_BODY_PROFILE_MAX_BITS){
      sab_pvw_body_profile.bit_ncmux_us[bit] +=
          sab_pvw_now_us() - ncmux_loop_begin;
      sab_pvw_body_profile.bit_ncmux_calls[bit] += power;
    }
    const uint64_t direct_cmux_loop_begin = sab_pvw_now_us();
#endif
    for (size_t j = direct_start; j < in_N - power; j++){
#ifdef SAB_PVW_SCHEDULE_FUSED_CMUX
      sab_pvw_schedule_CMUX(p[out][j + power], p[in][j + power], p[in][j],
          e[bit], sab);
#else
      sab_pvw_CMUX(p[out][j + power], p[in][j + power], p[in][j],
          e[bit], sab);
#endif
    }
#ifdef SAB_PVW_BODY_PROFILE
    if(bit < SAB_PVW_BODY_PROFILE_MAX_BITS){
      sab_pvw_body_profile.bit_direct_cmux_us[bit] +=
          sab_pvw_now_us() - direct_cmux_loop_begin;
      sab_pvw_body_profile.bit_direct_cmux_calls[bit] += in_N - power;
    }
#endif
  }
  active ^= r_prec & 1;
#ifdef SAB_PVW_BODY_PROFILE
  sab_pvw_body_profile_acc(&sab_pvw_body_profile.rgsw_monomial_us,
      &sab_pvw_body_profile.rgsw_monomial_calls, rgsw_begin);
#endif
  return active;
}

SAB_PVW_Key sab_pvw_new_gaussian_key(TRLWE_Key input_key,
    PVW_TMLWE_Key output_key, uint64_t b_prec, uint64_t h, uint64_t r_prec,
    uint64_t l, uint64_t bg_bit){
  if(input_key == NULL) sab_pvw_die("input key is NULL");
  if(output_key == NULL) sab_pvw_die("output key is NULL");
  if(r_prec == 0) sab_pvw_die("r_prec must be non-zero");

  SAB_PVW_Key res = (SAB_PVW_Key) safe_malloc(sizeof(*res));
  const uint64_t in_N = input_key->s[0]->N;
  const uint64_t in_k = input_key->k;
  const uint64_t out_N = output_key->s[0][0]->N;
  const uint64_t out_k = output_key->k;
  const uint64_t lanes = output_key->r;
  const uint64_t r_max = 1ULL << r_prec;

  res->output_key = output_key;
  res->mat_key = mat_trgsw_new_key(output_key, l, bg_bit);
  res->aut_minus1 = pvmtmlwe_new_automorphism_KS_key(output_key,
      2 * out_N - 1, (int) l, (int) bg_bit);
  res->packing_keys = NULL;
  res->hw_reducing_key = NULL;
  res->include_zeros = false;
  res->ternary_secret = false;
  res->s_pairs = NULL;
  res->gaussian_secret = true;
  res->s_coff = (MAT_TRGSW_DFT **) safe_malloc(sizeof(MAT_TRGSW_DFT *) * in_k);
  res->aut_family = (PVW_TMLWE_KS_Key *) safe_malloc(
      sizeof(PVW_TMLWE_KS_Key) * out_N);
  for (size_t w_idx = 0; w_idx < out_N; w_idx++){
    res->aut_family[w_idx] = pvmtmlwe_new_automorphism_KS_key(output_key,
        2 * w_idx + 1, (int) l, (int) bg_bit);
  }

  MAT_TRGSW tmp = mat_trgsw_alloc_new_sample(l, bg_bit, out_k, lanes, out_N);
  res->s = (MAT_TRGSW_DFT ***) safe_malloc(sizeof(MAT_TRGSW_DFT **) * in_k);
  for (size_t key_idx = 0; key_idx < in_k; key_idx++){
    res->s[key_idx] = (MAT_TRGSW_DFT **) safe_malloc(
        sizeof(MAT_TRGSW_DFT *) * (h + 1));
    res->s_coff[key_idx] =
        (MAT_TRGSW_DFT *) safe_malloc(sizeof(MAT_TRGSW_DFT) * h);
    uint64_t cnt_h = 0;
    uint64_t previous = in_N;
    for (size_t scan = 0; scan < in_N; scan++){
      const uint64_t current = in_N - scan - 1;
      const int64_t coeff = (int64_t) input_key->s[key_idx]->coeffs[current];
      if(coeff == 0) continue;
      if(cnt_h >= h) sab_pvw_die("gaussian input key exceeds h");
      const uint64_t r_diff = previous - current;
      if(r_diff >= r_max) sab_pvw_die("gaussian key gap exceeds r_prec");
      res->s[key_idx][cnt_h] = sab_pvw_alloc_selector_bits(r_prec, l,
          bg_bit, out_k, lanes, out_N);
      sab_pvw_encrypt_bits(res->s[key_idx][cnt_h], tmp, res->mat_key,
          r_diff, r_prec);
      /* first gate uses positive coefficients; negative-exponent convention
       * check pending before the negative-coefficient gate */
      if(coeff < 0) sab_pvw_die("gaussian keygen: negative coefficients not yet gated");
      res->s_coff[key_idx][cnt_h] = mat_trgsw_alloc_new_DFT_sample(
          (int) l, (int) bg_bit, (int) out_k, (int) lanes, (int) out_N);
      mat_trgsw_monomial_DFT_sample(res->s_coff[key_idx][cnt_h], 1,
          (int) coeff, res->mat_key);
      previous = current;
      cnt_h++;
    }
    if(cnt_h != h) sab_pvw_die("gaussian key has fewer non-zero coefficients than h");
    if(previous >= r_max) sab_pvw_die("final monomial gap exceeds r_prec");
    res->s[key_idx][cnt_h] = sab_pvw_alloc_selector_bits(r_prec, l,
        bg_bit, out_k, lanes, out_N);
    sab_pvw_encrypt_bits(res->s[key_idx][cnt_h], tmp, res->mat_key,
        previous, r_prec);
  }
  free_mat_trgsw(tmp);

  res->in_N = in_N;
  res->in_k = in_k;
  res->out_N = out_N;
  res->out_k = out_k;
  res->lanes = lanes;
  res->h = h;
  res->r_prec = r_prec;
  res->b_prec = b_prec;

  res->tmp = (sab_pvw_tmp_pool) safe_malloc(sizeof(*res->tmp));
  res->tmp->tmlwe_dft = pvmtmlwe_alloc_new_DFT_sample(out_k, lanes, out_N);
  res->tmp->tmlwe = pvmtmlwe_alloc_new_sample(out_k, lanes, out_N);
  res->tmp->rotated = pvmtmlwe_alloc_new_sample(out_k, lanes, out_N);
  res->tmp->tmlwe_poly2 = pvmtmlwe_alloc_new_sample_array(in_N, out_k, lanes, out_N);
  res->tmp->acc = NULL;
  res->tmp->extracted = NULL;
  res->tmp->lane_extracted = NULL;
  res->tmp->packed = NULL;
  res->tmp->scratch = mat_trgsw_alloc_mul_scratch((out_k + lanes) * l, out_N);
  res->tmp->a_mod = (uint64_t *) safe_malloc(sizeof(uint64_t) * in_N);
  return res;
}

/* Multi-body rho-SAB step (T4): per coefficient k,
 * y = Auto_{a_k^{-1}}(C_k); W = V (x) y; C_k = Auto_{a_k}(W), mirroring the
 * scalar sub_a_ga oracle (sparse_amortized_bootstrap.c:248-259). Requires
 * odd a_k (round-to-odd mod switch in blind_rotate_gaussian). */
void sab_pvw_sub_a_ga(PVW_TMLWE * p, const uint64_t * a,
    MAT_TRGSW_DFT selector, SAB_PVW_Key sab){
  for (size_t i = 0; i < sab->in_N; i++){
    const uint64_t w_inv = inverse_mod_2N((uint16_t) a[i],
        (uint16_t) sab->out_N);
    pvmtmlwe_eval_automorphism(sab->tmp->tmlwe, p[i], w_inv,
        sab->aut_family[(w_inv - 1) >> 1]);
    mat_trgsw_mul_pvmtmlwe_DFT(sab->tmp->tmlwe_dft, sab->tmp->tmlwe,
        selector, sab->tmp->scratch);
    pvmtmlwe_from_DFT(sab->tmp->tmlwe, sab->tmp->tmlwe_dft);
    pvmtmlwe_eval_automorphism(p[i], sab->tmp->tmlwe, a[i],
        sab->aut_family[(a[i] - 1) >> 1]);
  }
}

void sab_pvw_sparse_mul_gaussian(PVW_TMLWE * p, const uint64_t * a,
    uint64_t a_idx, SAB_PVW_Key sab){
  if(a_idx >= sab->in_k) sab_pvw_die("gaussian sparse_mul a_idx out of range");
  if(sab->aut_family == NULL){
    sab_pvw_die("gaussian sparse_mul requires sab_pvw_new_gaussian_key");
  }
  for (size_t step = 0; step < sab->h; step++){
    sab_pvw_RGSW_monomial_mul(p, sab->s[a_idx][step], sab);
    sab_pvw_sub_a_ga(p, a, sab->s_coff[a_idx][step], sab);
  }
  sab_pvw_RGSW_monomial_mul(p, sab->s[a_idx][sab->h], sab);
}

void sab_pvw_blind_rotate_gaussian(PVW_TMLWE * out, TRLWE in, SAB_PVW_Key sab){
  if(sab->in_k != 1) sab_pvw_die("only in_k=1 is supported");
  const uint64_t log_N2 = (uint64_t) log2(2 * sab->out_N);
  for (size_t key_idx = 0; key_idx < sab->in_k; key_idx++){
    /* odd coefficients are required by the T4 automorphism inverses */
    mod_switch_a(sab->tmp->a_mod, in->a[key_idx]->coeffs, log_N2,
        sab->in_N, true);
    sab_pvw_sparse_mul_gaussian(out, sab->tmp->a_mod, key_idx, sab);
  }
}

static inline void sab_pvw_accumulator_normalize(
    SAB_PVW_Accumulator_State * state, SAB_PVW_Key sab);

#ifdef SAB_PVW_DELTA2_SCHEDULE
/* delta=2 identity-addend MPmul (Lemma F1-1' / G1' checker / T2 model):
 * per bit pair, every slot runs out_j = U_j + sum_{m in {a,b,ab}}
 * (Src_m(j) - U_j) (x) M_m with wrapped sources via tau_{-1}; 2^delta - 1 = 3
 * MV-EPs per slot per pair, the (0,0) digit is the free addend. A trailing
 * odd bit (r_prec odd) runs one standard radix-2 round on e_last_odd. */
static uint64_t sab_pvw_RGSW_monomial_mul_pairs_state(PVW_TMLWE * p[2],
    uint64_t active, MAT_TRGSW_DFT * e_pairs, MAT_TRGSW_DFT e_last_odd,
    SAB_PVW_Key sab){
  const uint32_t r_prec = sab->r_prec, in_N = sab->in_N;
  const uint32_t n_pairs = r_prec / 2;
  for (size_t pair = 0; pair < n_pairs; pair++){
    const uint64_t off_a = 1ULL << (2 * pair);
    const uint64_t off_b = 1ULL << (2 * pair + 1);
    const uint64_t offs[3] = {off_a, off_b, off_a + off_b};
    const uint64_t in = active ^ (pair & 1);
    const uint64_t out = in ^ 1;
    for (size_t j = 0; j < in_N; j++){
      pvmtmlwe_copy(p[out][j], p[in][j]);
      for (size_t m = 0; m < 3; m++){
        const uint64_t off = offs[m];
        if(j >= off){
          pvmtmlwe_sub(sab->tmp->tmlwe, p[in][j - off], p[in][j]);
        }else{
          pvmtmlwe_eval_automorphism(sab->tmp->rotated,
              p[in][in_N - off + j], 2 * sab->out_N - 1, sab->aut_minus1);
          pvmtmlwe_sub(sab->tmp->tmlwe, sab->tmp->rotated, p[in][j]);
        }
        mat_trgsw_mul_pvmtmlwe_DFT(sab->tmp->tmlwe_dft, sab->tmp->tmlwe,
            e_pairs[3 * pair + m], sab->tmp->scratch);
        pvmtmlwe_from_DFT(sab->tmp->tmlwe, sab->tmp->tmlwe_dft);
        pvmtmlwe_add(p[out][j], p[out][j], sab->tmp->tmlwe);
      }
    }
  }
  active ^= n_pairs & 1;
  if(r_prec & 1){
    const uint64_t power = 1ULL << (r_prec - 1);
    const uint64_t in = active;
    const uint64_t out = active ^ 1;
    for (size_t j = 0; j < power; j++){
      sab_pvw_NCMUX(p[out][j], p[in][j], p[in][in_N - power + j],
          e_last_odd, sab);
    }
    for (size_t j = power; j < in_N; j++){
      sab_pvw_CMUX(p[out][j], p[in][j], p[in][j - power], e_last_odd, sab);
    }
    active ^= 1;
  }
  return active;
}

void sab_pvw_RGSW_monomial_mul_pairs(PVW_TMLWE * p0,
    MAT_TRGSW_DFT * e_pairs, MAT_TRGSW_DFT e_last_odd, SAB_PVW_Key sab){
  SAB_PVW_Accumulator_State state = sab_pvw_accumulator_state(p0, sab);
  state.active = sab_pvw_RGSW_monomial_mul_pairs_state(state.buffers,
      state.active, e_pairs, e_last_odd, sab);
  sab_pvw_accumulator_normalize(&state, sab);
}

void sab_pvw_sparse_mul_binary_pairs(PVW_TMLWE * p, const uint64_t * a,
    uint64_t a_idx, SAB_PVW_Key sab){
  if(a_idx >= sab->in_k) sab_pvw_die("delta2 sparse_mul a_idx out of range");
  if(sab->s_pairs == NULL){
    sab_pvw_die("delta2 sparse_mul requires SAB_PVW_DELTA2_SCHEDULE keygen");
  }
  for (size_t step = 0; step < sab->h; step++){
    sab_pvw_RGSW_monomial_mul_pairs(p, sab->s_pairs[a_idx][step],
        sab->s[a_idx][step][sab->r_prec - 1], sab);
    sab_pvw_sub_a_binary(p, a, sab);
  }
  sab_pvw_RGSW_monomial_mul_pairs(p, sab->s_pairs[a_idx][sab->h],
      sab->s[a_idx][sab->h][sab->r_prec - 1], sab);
}

void sab_pvw_blind_rotate_binary_pairs(PVW_TMLWE * out, TRLWE in,
    SAB_PVW_Key sab){
  if(sab->in_k != 1) sab_pvw_die("only in_k=1 is supported");
  const uint64_t log_N2 = (uint64_t) log2(2 * sab->out_N);
  for (size_t key_idx = 0; key_idx < sab->in_k; key_idx++){
    for (size_t idx = 0; idx < sab->in_N; idx++){
      sab->tmp->a_mod[idx] = torus2int(in->a[key_idx]->coeffs[idx], log_N2);
    }
    sab_pvw_sparse_mul_binary_pairs(out, sab->tmp->a_mod, key_idx, sab);
  }
}

void sab_pvw_bootstrap_binary_pairs(TRLWE * out, TRLWE in, PVW_TMLWE tv,
    SAB_PVW_Key sab){
  if(sab->packing_keys == NULL || sab->hw_reducing_key == NULL){
    sab_pvw_die("delta2 bootstrap requires sab_pvw_new_binary_full_key");
  }
  sab_pvw_setup_tv_xb(sab->tmp->acc, in->b->coeffs, tv, sab);
  sab_pvw_blind_rotate_binary_pairs(sab->tmp->acc, in, sab);
  for (size_t lane = 0; lane < sab->lanes; lane++){
    sab_pvw_extract_tlwe_lane_array(sab->tmp->lane_extracted[lane],
        sab->tmp->acc, lane, sab);
    trlwe_full_packing_keyswitch(sab->tmp->packed,
        sab->tmp->lane_extracted[lane], sab->in_N, sab->packing_keys[lane]);
    trlwe_keyswitch(out[lane], sab->tmp->packed, sab->hw_reducing_key);
  }
}
#endif

static void sab_pvw_copy_accumulator_array(PVW_TMLWE * out, PVW_TMLWE * in,
    SAB_PVW_Key sab){
#ifdef SAB_PVW_BODY_PROFILE
  const uint64_t copyback_begin = sab_pvw_now_us();
#endif
  for (size_t idx = 0; idx < sab->in_N; idx++){
    pvmtmlwe_copy(out[idx], in[idx]);
  }
#ifdef SAB_PVW_BODY_PROFILE
  sab_pvw_body_profile_acc(&sab_pvw_body_profile.copyback_us,
      &sab_pvw_body_profile.copyback_calls, copyback_begin);
#endif
}

static inline void sab_pvw_accumulator_normalize(
    SAB_PVW_Accumulator_State * state, SAB_PVW_Key sab){
  sab_pvw_accumulator_check(state, sab);
  if(state->active != 0){
    sab_pvw_copy_accumulator_array(state->buffers[0],
        sab_pvw_accumulator_active(state), sab);
    state->active = 0;
  }
}

void sab_pvw_RGSW_monomial_mul(PVW_TMLWE * p0, MAT_TRGSW_DFT * e,
    SAB_PVW_Key sab){
  SAB_PVW_Accumulator_State state = sab_pvw_accumulator_state(p0, sab);
  state.active = sab_pvw_RGSW_monomial_mul_state(state.buffers,
      state.active, e, sab);
  sab_pvw_accumulator_normalize(&state, sab);
}

void sab_pvw_sub_a_binary(PVW_TMLWE * p, const uint64_t * a, SAB_PVW_Key sab){
#ifdef SAB_PVW_BODY_PROFILE
  const uint64_t sub_a_begin = sab_pvw_now_us();
#endif
  for (size_t idx = 0; idx < sab->in_N; idx++){
#ifdef SAB_PVW_BODY_PROFILE
    const uint64_t rotate_begin = sab_pvw_now_us();
#endif
    pvmtmlwe_mul_by_xai(sab->tmp->tmlwe, p[idx], a[idx]);
#ifdef SAB_PVW_BODY_PROFILE
    sab_pvw_body_profile_acc(&sab_pvw_body_profile.sub_a_rotate_us,
        &sab_pvw_body_profile.sub_a_rotate_calls, rotate_begin);
    const uint64_t copy_begin = sab_pvw_now_us();
#endif
    pvmtmlwe_copy(p[idx], sab->tmp->tmlwe);
#ifdef SAB_PVW_BODY_PROFILE
    sab_pvw_body_profile_acc(&sab_pvw_body_profile.sub_a_copy_us,
        &sab_pvw_body_profile.sub_a_copy_calls, copy_begin);
#endif
  }
#ifdef SAB_PVW_BODY_PROFILE
  sab_pvw_body_profile_acc(&sab_pvw_body_profile.sub_a_us,
      &sab_pvw_body_profile.sub_a_calls, sub_a_begin);
#endif
}

void sab_pvw_sub_a_include_zero(PVW_TMLWE * p, const uint64_t * a,
    MAT_TRGSW_DFT selector, SAB_PVW_Key sab){
#ifdef SAB_PVW_BODY_PROFILE
  const uint64_t sub_a_begin = sab_pvw_now_us();
#endif
#ifdef SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST
  (void) selector;
  for (size_t idx = 0; idx < sab->in_N; idx++){
#ifdef SAB_PVW_BODY_PROFILE
    const uint64_t rotate_begin = sab_pvw_now_us();
#endif
    pvmtmlwe_mul_by_xai(sab->tmp->tmlwe, p[idx], a[idx]);
#ifdef SAB_PVW_BODY_PROFILE
    sab_pvw_body_profile_acc(&sab_pvw_body_profile.sub_a_rotate_us,
        &sab_pvw_body_profile.sub_a_rotate_calls, rotate_begin);
    const uint64_t copy_begin = sab_pvw_now_us();
#endif
    pvmtmlwe_copy(p[idx], sab->tmp->tmlwe);
#ifdef SAB_PVW_BODY_PROFILE
    sab_pvw_body_profile_acc(&sab_pvw_body_profile.sub_a_copy_us,
        &sab_pvw_body_profile.sub_a_copy_calls, copy_begin);
#endif
  }
#else
  for (size_t idx = 0; idx < sab->in_N; idx++){
#ifdef SAB_PVW_BODY_PROFILE
    const uint64_t mul_minus_1_begin = sab_pvw_now_us();
#endif
    pvmtmlwe_mul_by_xai_minus_1(sab->tmp->tmlwe, p[idx], a[idx]);
#ifdef SAB_PVW_BODY_PROFILE
    sab_pvw_body_profile_acc(&sab_pvw_body_profile.sub_a_mul_minus_1_us,
        &sab_pvw_body_profile.sub_a_mul_minus_1_calls, mul_minus_1_begin);
    const uint64_t mat_ep_begin = sab_pvw_now_us();
#endif
    mat_trgsw_mul_pvmtmlwe_DFT(sab->tmp->tmlwe_dft, sab->tmp->tmlwe,
        selector, sab->tmp->scratch);
#ifdef SAB_PVW_BODY_PROFILE
    sab_pvw_body_profile_acc(&sab_pvw_body_profile.sub_a_mat_ep_us,
        &sab_pvw_body_profile.sub_a_mat_ep_calls, mat_ep_begin);
    const uint64_t from_dft_begin = sab_pvw_now_us();
#endif
#ifdef SAB_PVW_SUBA_FUSED_FROM_DFT_ADD
    pvmtmlwe_from_DFT_add(p[idx], sab->tmp->tmlwe_dft, p[idx]);
#ifdef SAB_PVW_BODY_PROFILE
    sab_pvw_body_profile_acc(&sab_pvw_body_profile.sub_a_from_dft_us,
        &sab_pvw_body_profile.sub_a_from_dft_calls, from_dft_begin);
#endif
#else
    pvmtmlwe_from_DFT(sab->tmp->tmlwe, sab->tmp->tmlwe_dft);
#ifdef SAB_PVW_BODY_PROFILE
    sab_pvw_body_profile_acc(&sab_pvw_body_profile.sub_a_from_dft_us,
        &sab_pvw_body_profile.sub_a_from_dft_calls, from_dft_begin);
    const uint64_t add_begin = sab_pvw_now_us();
#endif
    pvmtmlwe_addto(p[idx], sab->tmp->tmlwe);
#ifdef SAB_PVW_BODY_PROFILE
    sab_pvw_body_profile_acc(&sab_pvw_body_profile.sub_a_add_us,
        &sab_pvw_body_profile.sub_a_add_calls, add_begin);
#endif
#endif
  }
#endif
#ifdef SAB_PVW_BODY_PROFILE
  sab_pvw_body_profile_acc(&sab_pvw_body_profile.sub_a_us,
      &sab_pvw_body_profile.sub_a_calls, sub_a_begin);
#endif
}

void sab_pvw_sub_a_ternary(PVW_TMLWE * p, const uint64_t * a,
    MAT_TRGSW_DFT selector, SAB_PVW_Key sab){
#ifdef SAB_PVW_BODY_PROFILE
  const uint64_t sub_a_begin = sab_pvw_now_us();
#endif
  for (size_t idx = 0; idx < sab->in_N; idx++){
#ifdef SAB_PVW_BODY_PROFILE
    const uint64_t rotate_begin = sab_pvw_now_us();
#endif
    pvmtmlwe_mul_by_xai(sab->tmp->rotated, p[idx], a[idx]);
#ifdef SAB_PVW_BODY_PROFILE
    sab_pvw_body_profile_acc(&sab_pvw_body_profile.sub_a_rotate_us,
        &sab_pvw_body_profile.sub_a_rotate_calls, rotate_begin);
    const uint64_t copy_begin = sab_pvw_now_us();
#endif
    pvmtmlwe_copy(p[idx], sab->tmp->rotated);
#ifdef SAB_PVW_BODY_PROFILE
    sab_pvw_body_profile_acc(&sab_pvw_body_profile.sub_a_copy_us,
        &sab_pvw_body_profile.sub_a_copy_calls, copy_begin);
    const uint64_t mul_minus_1_begin = sab_pvw_now_us();
#endif
    pvmtmlwe_mul_by_xai_minus_1(sab->tmp->tmlwe, p[idx],
        -2 * (int64_t) a[idx]);
#ifdef SAB_PVW_BODY_PROFILE
    sab_pvw_body_profile_acc(&sab_pvw_body_profile.sub_a_mul_minus_1_us,
        &sab_pvw_body_profile.sub_a_mul_minus_1_calls, mul_minus_1_begin);
    const uint64_t mat_ep_begin = sab_pvw_now_us();
#endif
    mat_trgsw_mul_pvmtmlwe_DFT(sab->tmp->tmlwe_dft, sab->tmp->tmlwe,
        selector, sab->tmp->scratch);
#ifdef SAB_PVW_BODY_PROFILE
    sab_pvw_body_profile_acc(&sab_pvw_body_profile.sub_a_mat_ep_us,
        &sab_pvw_body_profile.sub_a_mat_ep_calls, mat_ep_begin);
    const uint64_t from_dft_begin = sab_pvw_now_us();
#endif
#ifdef SAB_PVW_SUBA_FUSED_FROM_DFT_ADD
    pvmtmlwe_from_DFT_add(p[idx], sab->tmp->tmlwe_dft, p[idx]);
#ifdef SAB_PVW_BODY_PROFILE
    sab_pvw_body_profile_acc(&sab_pvw_body_profile.sub_a_from_dft_us,
        &sab_pvw_body_profile.sub_a_from_dft_calls, from_dft_begin);
#endif
#else
    pvmtmlwe_from_DFT(sab->tmp->tmlwe, sab->tmp->tmlwe_dft);
#ifdef SAB_PVW_BODY_PROFILE
    sab_pvw_body_profile_acc(&sab_pvw_body_profile.sub_a_from_dft_us,
        &sab_pvw_body_profile.sub_a_from_dft_calls, from_dft_begin);
    const uint64_t add_begin = sab_pvw_now_us();
#endif
    pvmtmlwe_addto(p[idx], sab->tmp->tmlwe);
#ifdef SAB_PVW_BODY_PROFILE
    sab_pvw_body_profile_acc(&sab_pvw_body_profile.sub_a_add_us,
        &sab_pvw_body_profile.sub_a_add_calls, add_begin);
#endif
#endif
  }
#ifdef SAB_PVW_BODY_PROFILE
  sab_pvw_body_profile_acc(&sab_pvw_body_profile.sub_a_us,
      &sab_pvw_body_profile.sub_a_calls, sub_a_begin);
#endif
}

static void sab_pvw_sub_a_binary_to(PVW_TMLWE * out, PVW_TMLWE * in,
    const uint64_t * a, SAB_PVW_Key sab){
#ifdef SAB_PVW_BODY_PROFILE
  const uint64_t sub_a_begin = sab_pvw_now_us();
#endif
  for (size_t idx = 0; idx < sab->in_N; idx++){
#ifdef SAB_PVW_BODY_PROFILE
    const uint64_t rotate_begin = sab_pvw_now_us();
#endif
    pvmtmlwe_mul_by_xai(out[idx], in[idx], a[idx]);
#ifdef SAB_PVW_BODY_PROFILE
    sab_pvw_body_profile_acc(&sab_pvw_body_profile.sub_a_rotate_us,
        &sab_pvw_body_profile.sub_a_rotate_calls, rotate_begin);
#endif
  }
#ifdef SAB_PVW_BODY_PROFILE
  const uint64_t elapsed = sab_pvw_now_us() - sub_a_begin;
  sab_pvw_body_profile.sub_a_us += elapsed;
  sab_pvw_body_profile.sub_a_calls++;
  sab_pvw_body_profile.sub_a_output_fusion_us += elapsed;
  sab_pvw_body_profile.sub_a_output_fusion_calls++;
#endif
}

void sab_pvw_sparse_mul_binary(PVW_TMLWE * p, const uint64_t * a,
    uint64_t a_idx, SAB_PVW_Key sab){
#ifdef SAB_PVW_BODY_PROFILE
  const uint64_t sparse_mul_begin = sab_pvw_now_us();
#endif
  if(a_idx >= sab->in_k) sab_pvw_die("sparse_mul a_idx out of range");
#ifdef SAB_PVW_ACTIVE_BUFFER_FUSION
  SAB_PVW_Accumulator_State state = sab_pvw_accumulator_state(p, sab);
  for (size_t step = 0; step < sab->h; step++){
    state.active = sab_pvw_RGSW_monomial_mul_state(state.buffers,
        state.active,
        sab->s[a_idx][step], sab);
#ifdef SAB_PVW_SUBA_OUTPUT_FUSION
    sab_pvw_sub_a_binary_to(sab_pvw_accumulator_inactive(&state),
        sab_pvw_accumulator_active(&state), a, sab);
    sab_pvw_accumulator_flip(&state);
#else
    sab_pvw_sub_a_binary(sab_pvw_accumulator_active(&state), a, sab);
#endif
  }
  state.active = sab_pvw_RGSW_monomial_mul_state(state.buffers,
      state.active,
      sab->s[a_idx][sab->h], sab);
  sab_pvw_accumulator_normalize(&state, sab);
#else
  for (size_t step = 0; step < sab->h; step++){
    sab_pvw_RGSW_monomial_mul(p, sab->s[a_idx][step], sab);
    sab_pvw_sub_a_binary(p, a, sab);
  }
  sab_pvw_RGSW_monomial_mul(p, sab->s[a_idx][sab->h], sab);
#endif
#ifdef SAB_PVW_BODY_PROFILE
  sab_pvw_body_profile_acc(&sab_pvw_body_profile.sparse_mul_us,
      &sab_pvw_body_profile.sparse_mul_calls, sparse_mul_begin);
#endif
}

void sab_pvw_sparse_mul_nonbinary(PVW_TMLWE * p, const uint64_t * a,
    uint64_t a_idx, SAB_PVW_Key sab){
#ifdef SAB_PVW_BODY_PROFILE
  const uint64_t sparse_mul_begin = sab_pvw_now_us();
#endif
  if(a_idx >= sab->in_k) sab_pvw_die("sparse_mul a_idx out of range");
  if(sab->include_zeros && sab->s_coff == NULL){
    sab_pvw_die("include-zero sparse_mul selector family is missing");
  }
  if(sab->ternary_secret && sab->s_sign == NULL){
    sab_pvw_die("ternary sparse_mul selector family is missing");
  }
  if(!sab->include_zeros && !sab->ternary_secret){
    sab_pvw_die("nonbinary sparse_mul requires include-zero or ternary mode");
  }

  SAB_PVW_Accumulator_State state = sab_pvw_accumulator_state(p, sab);
  for (size_t step = 0; step < sab->h; step++){
    state.active = sab_pvw_RGSW_monomial_mul_state(state.buffers,
        state.active, sab->s[a_idx][step], sab);
    if(sab->include_zeros){
      sab_pvw_sub_a_include_zero(sab_pvw_accumulator_active(&state),
          a, sab->s_coff[a_idx][step], sab);
    }else{
      sab_pvw_sub_a_ternary(sab_pvw_accumulator_active(&state),
          a, sab->s_sign[a_idx][step], sab);
    }
  }
  state.active = sab_pvw_RGSW_monomial_mul_state(state.buffers,
      state.active, sab->s[a_idx][sab->h], sab);
  sab_pvw_accumulator_normalize(&state, sab);
#ifdef SAB_PVW_BODY_PROFILE
  sab_pvw_body_profile_acc(&sab_pvw_body_profile.sparse_mul_us,
      &sab_pvw_body_profile.sparse_mul_calls, sparse_mul_begin);
#endif
}

void sab_pvw_setup_tv_xb(PVW_TMLWE * acc, const uint64_t * b,
    PVW_TMLWE tv, SAB_PVW_Key sab){
  const int log_N2 = (int) log2(2 * sab->out_N);
  const uint64_t prec_offset = 1ULL << (64 - sab->b_prec - 1);
  for (size_t idx = 0; idx < sab->in_N; idx++){
    pvmtmlwe_mul_by_xai(acc[idx], tv, torus2int(b[idx] + prec_offset, log_N2));
  }
}

void sab_pvw_blind_rotate_binary(PVW_TMLWE * out, TRLWE in, SAB_PVW_Key sab){
  if(sab->in_k != 1) sab_pvw_die("only in_k=1 is supported");
  const uint64_t log_N2 = (uint64_t) log2(2 * sab->out_N);
  for (size_t key_idx = 0; key_idx < sab->in_k; key_idx++){
    for (size_t idx = 0; idx < sab->in_N; idx++){
      sab->tmp->a_mod[idx] = torus2int(in->a[key_idx]->coeffs[idx], log_N2);
    }
    sab_pvw_sparse_mul_binary(out, sab->tmp->a_mod, key_idx, sab);
  }
}

void sab_pvw_blind_rotate_nonbinary(PVW_TMLWE * out, TRLWE in,
    SAB_PVW_Key sab){
  if(sab->in_k != 1) sab_pvw_die("only in_k=1 is supported");
  if(!sab->include_zeros && !sab->ternary_secret){
    sab_pvw_die("nonbinary blind rotate requires include-zero or ternary mode");
  }
  const uint64_t log_N2 = (uint64_t) log2(2 * sab->out_N);
  for (size_t key_idx = 0; key_idx < sab->in_k; key_idx++){
    for (size_t idx = 0; idx < sab->in_N; idx++){
      sab->tmp->a_mod[idx] = torus2int(in->a[key_idx]->coeffs[idx],
          log_N2);
    }
    sab_pvw_sparse_mul_nonbinary(out, sab->tmp->a_mod, key_idx, sab);
  }
}

void sab_pvw_bootstrap_wo_extract_binary(PVW_TMLWE * out, TRLWE in,
    PVW_TMLWE tv, SAB_PVW_Key sab){
#ifdef SAB_PVW_BODY_PROFILE
  sab_pvw_body_profile_reset();
  const uint64_t full_begin = sab_pvw_now_us();
  const uint64_t setup_begin = sab_pvw_now_us();
#endif
  sab_pvw_setup_tv_xb(out, in->b->coeffs, tv, sab);
#ifdef SAB_PVW_BODY_PROFILE
  sab_pvw_body_profile_acc(&sab_pvw_body_profile.setup_tv_xb_us,
      &sab_pvw_body_profile.setup_tv_xb_calls, setup_begin);
  const uint64_t blind_rotate_begin = sab_pvw_now_us();
#endif
  sab_pvw_blind_rotate_binary(out, in, sab);
#ifdef SAB_PVW_BODY_PROFILE
  sab_pvw_body_profile_acc(&sab_pvw_body_profile.blind_rotate_us,
      &sab_pvw_body_profile.blind_rotate_calls, blind_rotate_begin);
  sab_pvw_body_profile_print(sab, sab_pvw_now_us() - full_begin);
#endif
}

void sab_pvw_bootstrap_wo_extract_nonbinary(PVW_TMLWE * out, TRLWE in,
    PVW_TMLWE tv, SAB_PVW_Key sab){
#ifdef SAB_PVW_BODY_PROFILE
  sab_pvw_body_profile_reset();
  const uint64_t full_begin = sab_pvw_now_us();
  const uint64_t setup_begin = sab_pvw_now_us();
#endif
  sab_pvw_setup_tv_xb(out, in->b->coeffs, tv, sab);
#ifdef SAB_PVW_BODY_PROFILE
  sab_pvw_body_profile_acc(&sab_pvw_body_profile.setup_tv_xb_us,
      &sab_pvw_body_profile.setup_tv_xb_calls, setup_begin);
  const uint64_t blind_rotate_begin = sab_pvw_now_us();
#endif
  sab_pvw_blind_rotate_nonbinary(out, in, sab);
#ifdef SAB_PVW_BODY_PROFILE
  sab_pvw_body_profile_acc(&sab_pvw_body_profile.blind_rotate_us,
      &sab_pvw_body_profile.blind_rotate_calls, blind_rotate_begin);
  sab_pvw_body_profile_print(sab, sab_pvw_now_us() - full_begin);
#endif
}

void sab_pvw_extract_pvwtlwe(PVW_TLWE * out, PVW_TMLWE * in, SAB_PVW_Key sab){
  for (size_t idx = 0; idx < sab->in_N; idx++){
    pvmtmlwe_extract_pvmtlwe(out[idx], in[idx], 0);
  }
}

void sab_pvw_bootstrap_binary(TRLWE * out, TRLWE in, PVW_TMLWE tv,
    SAB_PVW_Key sab){
  if(sab->packing_keys == NULL || sab->hw_reducing_key == NULL){
    sab_pvw_die("full binary bootstrap requires sab_pvw_new_binary_full_key");
  }
#ifdef SAB_PVW_POSTPROC_PROFILE
  uint64_t bootstrap_wo_extract_us = 0;
  uint64_t direct_extract_us = 0;
  uint64_t packing_ks_us = 0;
  uint64_t hw_ks_us = 0;
  const uint64_t full_begin = sab_pvw_now_us();
#endif
  SAB_PVW_POSTPROC_TIME_ACC(bootstrap_wo_extract_us,
      sab_pvw_bootstrap_wo_extract_binary(sab->tmp->acc, in, tv, sab));
  for (size_t lane = 0; lane < sab->lanes; lane++){
    SAB_PVW_POSTPROC_TIME_ACC(direct_extract_us,
        sab_pvw_extract_tlwe_lane_array(sab->tmp->lane_extracted[lane],
            sab->tmp->acc, lane, sab));
    SAB_PVW_POSTPROC_TIME_ACC(packing_ks_us,
        trlwe_full_packing_keyswitch(sab->tmp->packed,
            sab->tmp->lane_extracted[lane], sab->in_N,
            sab->packing_keys[lane]));
    SAB_PVW_POSTPROC_TIME_ACC(hw_ks_us,
        trlwe_keyswitch(out[lane], sab->tmp->packed,
            sab->hw_reducing_key));
  }
#ifdef SAB_PVW_POSTPROC_PROFILE
  const uint64_t full_us = sab_pvw_now_us() - full_begin;
  printf("SAB_PVW_POSTPROC_PROFILE sample lanes=%" PRIu64
         " bootstrap_wo_extract_us=%" PRIu64
         " direct_extract_us=%" PRIu64
         " packing_ks_us=%" PRIu64
         " hw_ks_us=%" PRIu64
         " full_us=%" PRIu64 "\n",
         sab->lanes, bootstrap_wo_extract_us, direct_extract_us,
         packing_ks_us, hw_ks_us, full_us);
#endif
}

void sab_pvw_bootstrap_nonbinary(TRLWE * out, TRLWE in, PVW_TMLWE tv,
    SAB_PVW_Key sab){
  if(sab->packing_keys == NULL || sab->hw_reducing_key == NULL){
    sab_pvw_die("full nonbinary bootstrap requires sab_pvw_new_nonbinary_full_key");
  }
  if(!sab->include_zeros && !sab->ternary_secret){
    sab_pvw_die("nonbinary bootstrap requires include-zero or ternary mode");
  }
#ifdef SAB_PVW_POSTPROC_PROFILE
  uint64_t bootstrap_wo_extract_us = 0;
  uint64_t direct_extract_us = 0;
  uint64_t packing_ks_us = 0;
  uint64_t hw_ks_us = 0;
  const uint64_t full_begin = sab_pvw_now_us();
#endif
  SAB_PVW_POSTPROC_TIME_ACC(bootstrap_wo_extract_us,
      sab_pvw_bootstrap_wo_extract_nonbinary(sab->tmp->acc, in, tv, sab));
  for (size_t lane = 0; lane < sab->lanes; lane++){
    SAB_PVW_POSTPROC_TIME_ACC(direct_extract_us,
        sab_pvw_extract_tlwe_lane_array(sab->tmp->lane_extracted[lane],
            sab->tmp->acc, lane, sab));
    SAB_PVW_POSTPROC_TIME_ACC(packing_ks_us,
        trlwe_full_packing_keyswitch(sab->tmp->packed,
            sab->tmp->lane_extracted[lane], sab->in_N,
            sab->packing_keys[lane]));
    SAB_PVW_POSTPROC_TIME_ACC(hw_ks_us,
        trlwe_keyswitch(out[lane], sab->tmp->packed,
            sab->hw_reducing_key));
  }
#ifdef SAB_PVW_POSTPROC_PROFILE
  const uint64_t full_us = sab_pvw_now_us() - full_begin;
  printf("SAB_PVW_POSTPROC_PROFILE sample lanes=%" PRIu64
         " bootstrap_wo_extract_us=%" PRIu64
         " direct_extract_us=%" PRIu64
         " packing_ks_us=%" PRIu64
         " hw_ks_us=%" PRIu64
         " full_us=%" PRIu64 "\n",
         sab->lanes, bootstrap_wo_extract_us, direct_extract_us,
         packing_ks_us, hw_ks_us, full_us);
#endif
}
