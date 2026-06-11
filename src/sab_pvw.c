#include <sab_pvw.h>

static void sab_pvw_die(const char * msg){
  fprintf(stderr, "sab_pvw: %s\n", msg);
  exit(1);
}

static void sab_pvw_encrypt_bits(MAT_TRGSW_DFT * out, MAT_TRGSW tmp,
    MAT_TRGSW_Key key, uint64_t in, uint64_t prec){
  for (size_t bit = 0; bit < prec; bit++){
    const uint64_t val = (in >> bit) & 1;
    mat_trgsw_monomial_sample(tmp, val, 0, key);
    mat_trgsw_to_DFT(out[bit], tmp);
  }
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

  MAT_TRGSW tmp = mat_trgsw_alloc_new_sample(l, bg_bit, out_k, lanes, out_N);
  res->s = (MAT_TRGSW_DFT ***) safe_malloc(sizeof(MAT_TRGSW_DFT **) * in_k);
  for (size_t key_idx = 0; key_idx < in_k; key_idx++){
    res->s[key_idx] = (MAT_TRGSW_DFT **) safe_malloc(sizeof(MAT_TRGSW_DFT *) * (h + 1));
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

void sab_pvw_CMUX(PVW_TMLWE out, PVW_TMLWE in1, PVW_TMLWE in2,
    MAT_TRGSW_DFT selector, SAB_PVW_Key sab){
  pvmtmlwe_sub(sab->tmp->tmlwe, in2, in1);
  mat_trgsw_mul_pvmtmlwe_DFT(sab->tmp->tmlwe_dft, sab->tmp->tmlwe,
      selector, sab->tmp->scratch);
  pvmtmlwe_from_DFT(sab->tmp->tmlwe, sab->tmp->tmlwe_dft);
  pvmtmlwe_add(out, sab->tmp->tmlwe, in1);
}

void sab_pvw_NCMUX(PVW_TMLWE out, PVW_TMLWE in1, PVW_TMLWE in2,
    MAT_TRGSW_DFT selector, SAB_PVW_Key sab){
  pvmtmlwe_eval_automorphism(sab->tmp->rotated, in2,
      2 * in2->b[0]->N - 1, sab->aut_minus1);
  sab_pvw_CMUX(out, in1, sab->tmp->rotated, selector, sab);
}

void sab_pvw_RGSW_monomial_mul(PVW_TMLWE * p0, MAT_TRGSW_DFT * e,
    SAB_PVW_Key sab){
  const uint32_t r_prec = sab->r_prec, in_N = sab->in_N;
  PVW_TMLWE * p[2] = {p0, sab->tmp->tmlwe_poly2};
  for (size_t bit = 0; bit < r_prec; bit++){
    const uint64_t power = 1ULL << bit;
    const uint64_t out = (bit + 1) & 1, in = out ^ 1;
    for (size_t j = 0; j < power; j++){
      sab_pvw_NCMUX(p[out][j], p[in][j], p[in][in_N - power + j],
          e[bit], sab);
    }
    for (size_t j = 0; j < in_N - power; j++){
      sab_pvw_CMUX(p[out][j + power], p[in][j + power], p[in][j],
          e[bit], sab);
    }
  }
  if(p[r_prec & 1] != p0){
    for (size_t idx = 0; idx < in_N; idx++){
      pvmtmlwe_copy(p0[idx], p[r_prec & 1][idx]);
    }
  }
}

void sab_pvw_sub_a_binary(PVW_TMLWE * p, const uint64_t * a, SAB_PVW_Key sab){
  for (size_t idx = 0; idx < sab->in_N; idx++){
    pvmtmlwe_mul_by_xai(sab->tmp->tmlwe, p[idx], a[idx]);
    pvmtmlwe_copy(p[idx], sab->tmp->tmlwe);
  }
}

void sab_pvw_sparse_mul_binary(PVW_TMLWE * p, const uint64_t * a,
    uint64_t a_idx, SAB_PVW_Key sab){
  if(a_idx >= sab->in_k) sab_pvw_die("sparse_mul a_idx out of range");
  for (size_t step = 0; step < sab->h; step++){
    sab_pvw_RGSW_monomial_mul(p, sab->s[a_idx][step], sab);
    sab_pvw_sub_a_binary(p, a, sab);
  }
  sab_pvw_RGSW_monomial_mul(p, sab->s[a_idx][sab->h], sab);
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

void sab_pvw_bootstrap_wo_extract_binary(PVW_TMLWE * out, TRLWE in,
    PVW_TMLWE tv, SAB_PVW_Key sab){
  sab_pvw_setup_tv_xb(out, in->b->coeffs, tv, sab);
  sab_pvw_blind_rotate_binary(out, in, sab);
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
  sab_pvw_bootstrap_wo_extract_binary(sab->tmp->acc, in, tv, sab);
  sab_pvw_extract_pvwtlwe(sab->tmp->extracted, sab->tmp->acc, sab);
  for (size_t lane = 0; lane < sab->lanes; lane++){
    for (size_t idx = 0; idx < sab->in_N; idx++){
      sab_pvw_materialize_pvwtlwe_lane(sab->tmp->lane_extracted[lane][idx],
          sab->tmp->extracted[idx], lane);
    }
    trlwe_full_packing_keyswitch(sab->tmp->packed,
        sab->tmp->lane_extracted[lane], sab->in_N, sab->packing_keys[lane]);
    trlwe_keyswitch(out[lane], sab->tmp->packed, sab->hw_reducing_key);
  }
}
