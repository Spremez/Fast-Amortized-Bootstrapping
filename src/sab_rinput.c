/* sab_rinput.c -- r-input batching + Hom-Tr (stage396), r = 2.
 *
 * Interleaved accumulator: one PVW_TMLWE body (r=1) per slot over
 * R = Z[X]/(X^N+1), lanes at X-exponent residues (Y = X^2, d = N/2).
 * sub_a = U_a (fixed-subgroup trace weights P_w, HT-2'); butterfly wrapped
 * sources get Psi = U_(0,1) o sigma_{-1} (HT-4); per-step rescale with 1
 * guard bit (HT-7/HT-8). Lift theorem HT-5: lane l of slot t equals the
 * scalar pipeline (out ring d, granularity 2d) for input l. */
#include <sab_rinput.h>
#include <sab.h>
#include <inttypes.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>

static void sab_rinput_die(const char * msg){
  fprintf(stderr, "sab_rinput: %s\n", msg);
  exit(1);
}

static void sab_rinput_encrypt_bits(MAT_TRGSW_DFT * out, MAT_TRGSW tmp,
    MAT_TRGSW_Key key, uint64_t in, uint64_t prec){
  for (size_t bit = 0; bit < prec; bit++){
    const uint64_t val = (in >> bit) & 1;
    mat_trgsw_monomial_sample(tmp, (int64_t) val, 0, key);
    mat_trgsw_to_DFT(out[bit], tmp);
  }
}

SAB_RINPUT_Key sab_rinput_new_key(TRLWE_Key input_key,
    PVW_TMLWE_Key output_key, uint64_t b_prec, uint64_t h, uint64_t r_prec,
    uint64_t l, uint64_t bg_bit){
  if(input_key == NULL) sab_rinput_die("input key is NULL");
  if(output_key == NULL) sab_rinput_die("output key is NULL");
  /* r=1: pure r-input; r=r2>1: JOINT r1-input x r2-LUT (HT-10): every
   * operator below (sub_a U_a, Psi, CMUX, butterfly, doubling) is
   * body-generic; only the setup fills bodies. */
  if(r_prec == 0) sab_rinput_die("r_prec must be non-zero");

  SAB_RINPUT_Key res = (SAB_RINPUT_Key) safe_malloc(sizeof(*res));
  const uint64_t in_N = input_key->s[0]->N;
  const uint64_t in_k = input_key->k;
  const uint64_t out_N = output_key->s[0][0]->N;
  const uint64_t out_k = output_key->k;
  const int out_r = output_key->r;
  const uint64_t r_max = 1ULL << r_prec;
  if(out_N % 2) sab_rinput_die("out_N must be even (r=2 interleave)");

  res->output_key = output_key;
  res->mat_key = mat_trgsw_new_key(output_key, (int) l, (int) bg_bit);
  /* wrap automorphism KS (sigma_{-1}) */
  res->aut_minus1 = pvmtmlwe_new_automorphism_KS_key(output_key,
      2 * out_N - 1, (int) l, (int) bg_bit);
  /* Hom-Tr automorphism KS (sigma_{1+N}); index (w-1)/2 = N/2.
   * Shared by sub_a and the Psi micro-correction (one extra key total). */
  res->aut_h = pvmtmlwe_new_automorphism_KS_key(output_key, 1 + out_N,
      (int) l, (int) bg_bit);

  MAT_TRGSW tmp = mat_trgsw_alloc_new_sample((int) l, (int) bg_bit,
      (int) out_k, out_r, (int) out_N);
  res->s = (MAT_TRGSW_DFT ***) safe_malloc(sizeof(MAT_TRGSW_DFT **) * in_k);
  for (size_t key_idx = 0; key_idx < in_k; key_idx++){
    res->s[key_idx] =
        (MAT_TRGSW_DFT **) safe_malloc(sizeof(MAT_TRGSW_DFT *) * (h + 1));
    uint64_t cnt_h = 0;
    uint64_t previous = in_N;
    for (size_t scan = 0; scan < in_N; scan++){
      const uint64_t current = in_N - scan - 1;
      const int64_t coeff = (int64_t) input_key->s[key_idx]->coeffs[current];
      if(coeff == 0) continue;
      if(cnt_h >= h) sab_rinput_die("input key exceeds h");
      const uint64_t r_diff = previous - current;
      if(r_diff >= r_max) sab_rinput_die("input key gap exceeds r_prec");
      res->s[key_idx][cnt_h] = (MAT_TRGSW_DFT *) safe_malloc(
          sizeof(MAT_TRGSW_DFT) * r_prec);
      for (size_t bit = 0; bit < r_prec; bit++){
        res->s[key_idx][cnt_h][bit] = mat_trgsw_alloc_new_DFT_sample(
            (int) l, (int) bg_bit, (int) out_k, out_r, (int) out_N);
      }
      sab_rinput_encrypt_bits(res->s[key_idx][cnt_h], tmp, res->mat_key,
          r_diff, r_prec);
      previous = current;
      cnt_h++;
    }
    if(cnt_h != h) sab_rinput_die("input key has fewer non-zero coefficients than h");
    if(previous >= r_max) sab_rinput_die("final monomial gap exceeds r_prec");
    res->s[key_idx][cnt_h] = (MAT_TRGSW_DFT *) safe_malloc(
        sizeof(MAT_TRGSW_DFT) * r_prec);
    for (size_t bit = 0; bit < r_prec; bit++){
      res->s[key_idx][cnt_h][bit] = mat_trgsw_alloc_new_DFT_sample(
          (int) l, (int) bg_bit, (int) out_k, out_r, (int) out_N);
    }
    sab_rinput_encrypt_bits(res->s[key_idx][cnt_h], tmp, res->mat_key,
        previous, r_prec);
  }
  free_mat_trgsw(tmp);

  res->in_N = in_N;
  res->in_k = in_k;
  res->out_N = out_N;
  res->d = out_N / 2;
  res->lanes = 2;
  res->h = h;
  res->r_prec = r_prec;
  res->b_prec = b_prec;

  res->tmp = (SAB_RINPUT_Tmp) safe_malloc(sizeof(*res->tmp));
  res->tmp->t0 = pvmtmlwe_alloc_new_sample((int) out_k, out_r, (int) out_N);
  res->tmp->t1 = pvmtmlwe_alloc_new_sample((int) out_k, out_r, (int) out_N);
  res->tmp->t2 = pvmtmlwe_alloc_new_sample((int) out_k, out_r, (int) out_N);
  res->tmp->s_plus = pvmtmlwe_alloc_new_sample((int) out_k, out_r, (int) out_N);
  res->tmp->s_minus = pvmtmlwe_alloc_new_sample((int) out_k, out_r, (int) out_N);
  res->tmp->dft = pvmtmlwe_alloc_new_DFT_sample((int) out_k, out_r, (int) out_N);
  /* decompose writes l*(k+r) rows: scratch must cover the body count */
  res->tmp->scratch = mat_trgsw_alloc_mul_scratch(
      (int) ((out_k + out_r) * l), (int) out_N);
  res->tmp->buf2 = pvmtmlwe_alloc_new_sample_array((int) in_N, (int) out_k,
      out_r, (int) out_N);
  res->tmp->a_mod0 = (uint64_t *) safe_malloc(sizeof(uint64_t) * in_N);
  res->tmp->a_mod1 = (uint64_t *) safe_malloc(sizeof(uint64_t) * in_N);
  return res;
}

void free_sab_rinput_key(SAB_RINPUT_Key sab){
  if(sab == NULL) return;
  for (size_t key_idx = 0; key_idx < sab->in_k; key_idx++){
    for (size_t step = 0; step <= sab->h; step++){
      for (size_t bit = 0; bit < sab->r_prec; bit++){
        free_mat_trgsw_DFT(sab->s[key_idx][step][bit]);
      }
      free(sab->s[key_idx][step]);
    }
    free(sab->s[key_idx]);
  }
  free(sab->s);
  free_pvmtmlwe_ks_key(sab->aut_minus1);
  free_pvmtmlwe_ks_key(sab->aut_h);
  free_mat_trgsw_key(sab->mat_key);
  free_pvmtmlwe_array(sab->tmp->buf2, (int) sab->in_N);
  free(sab->tmp->a_mod0);
  free(sab->tmp->a_mod1);
  free_mat_trgsw_mul_scratch(sab->tmp->scratch);
  free_pvmtmlwe_DFT(sab->tmp->dft);
  free_pvmtmlwe(sab->tmp->s_minus);
  free_pvmtmlwe(sab->tmp->s_plus);
  free_pvmtmlwe(sab->tmp->t2);
  free_pvmtmlwe(sab->tmp->t1);
  free_pvmtmlwe(sab->tmp->t0);
  free(sab->tmp);
  free(sab);
}

/* I-4: c <- round(c/2) per component (in-place safe). Guard-bit semantics:
 * requires message+noise < 2^63 at entry (HT-8). */
void sab_rinput_rescale2(PVW_TMLWE out, PVW_TMLWE in){
  const int N = in->b[0]->N;
  for (size_t idx = 0; idx < (size_t) in->k; idx++){
    for (size_t c = 0; c < (size_t) N; c++){
      out->a[idx]->coeffs[c] =
          (in->a[idx]->coeffs[c] + 1) >> 1;
    }
  }
  for (size_t lane = 0; lane < (size_t) in->r; lane++){
    for (size_t c = 0; c < (size_t) N; c++){
      out->b[lane]->coeffs[c] =
          (in->b[lane]->coeffs[c] + 1) >> 1;
    }
  }
}

static void sab_rinput_zero(PVW_TMLWE c){
  const int N = c->b[0]->N;
  for (size_t idx = 0; idx < (size_t) c->k; idx++){
    memset(c->a[idx]->coeffs, 0, sizeof(c->a[idx]->coeffs[0]) * N);
  }
  for (size_t lane = 0; lane < (size_t) c->r; lane++){
    memset(c->b[lane]->coeffs, 0, sizeof(c->b[lane]->coeffs[0]) * N);
  }
}

/* I-5: Hom-Tr sub_a per slot. U_a = Y^{a0}(C + sigma_h C) + Y^{a1}(C - sigma_h C),
 * then /2 (HT-2' with weights P_id = Y^{a0}+Y^{a1}, P_h = Y^{a0}-Y^{a1};
 * target lane l -> Y^{+a_l} matching mul_by_xai(+a) semantics).
 * rescale=false keeps the structural x2 (used on the LAST sub_a: the final
 * division by 2 moves to the extraction, where signed division is exact --
 * intermediate rescale wrap errors (+-2^63) cancel at the next U_a doubling,
 * but the last one would survive into the output; see stage396 HT-7). */
void sab_rinput_sub_a_homtr_opt(PVW_TMLWE * p, const uint64_t * a0,
    const uint64_t * a1, SAB_RINPUT_Key sab, int rescale){
  const uint64_t twoN = 2 * sab->out_N;
  for (size_t t = 0; t < sab->in_N; t++){
    PVW_TMLWE c = p[t];
    pvmtmlwe_eval_automorphism(sab->tmp->t0, c, 1 + sab->out_N, sab->aut_h);
    pvmtmlwe_add(sab->tmp->s_plus, c, sab->tmp->t0);
    pvmtmlwe_sub(sab->tmp->s_minus, c, sab->tmp->t0);
    sab_rinput_zero(sab->tmp->t1);
    pvmtmlwe_mul_by_xai_addto(sab->tmp->t1, sab->tmp->s_plus,
        (int) ((2 * a0[t]) % twoN));
    pvmtmlwe_mul_by_xai_addto(sab->tmp->t1, sab->tmp->s_minus,
        (int) ((2 * a1[t]) % twoN));
    if(rescale){
      sab_rinput_rescale2(c, sab->tmp->t1);
    }else{
      pvmtmlwe_copy(c, sab->tmp->t1);
    }
  }
}

void sab_rinput_sub_a_homtr(PVW_TMLWE * p, const uint64_t * a0,
    const uint64_t * a1, SAB_RINPUT_Key sab){
  sab_rinput_sub_a_homtr_opt(p, a0, a1, sab, 1);
}

/* Minimal wo-extract oracle key: selectors + aut_minus1 + tmp pool only
 * (avoids new_sparse_amortized_bootstrapping's packing/hw KS construction,
 * which is not exercised by sab_rlwe_bootstrap_wo_extract and which crashes
 * in the LOCAL MinGW build for some dims). Semantics identical to the
 * stock binary-key oracle path. */
SAB_Key min_oracle_key(TRLWE_Key input_key, TRGSW_Key skey,
    uint64_t b_prec, uint64_t h, uint64_t r_prec){
  SAB_Key res = (SAB_Key) calloc(1, sizeof(*res));
  res->in_N = input_key->s[0]->N;
  res->in_k = input_key->k;
  res->out_N = skey->trlwe_key->s[0]->N;
  res->out_k = skey->trlwe_key->k;
  res->h = h;
  res->r_prec = r_prec;
  res->b_prec = b_prec;
  uint64_t gens[1] = {2 * res->out_N - 1};
  res->aut_minus1 = trlwe_new_automorphism_KS_keyset_2(skey->trlwe_key, gens,
      1, skey->l, skey->Bg_bit)[0];
  TRGSW tmp = trgsw_alloc_new_sample(skey->l, skey->Bg_bit, (int) res->out_k,
      (int) res->out_N);
  res->s = (TRGSW_DFT ***) safe_malloc(sizeof(TRGSW_DFT **) * res->in_k);
  for (size_t ki = 0; ki < res->in_k; ki++){
    res->s[ki] = (TRGSW_DFT **) safe_malloc(sizeof(TRGSW_DFT *) * (h + 1));
    uint64_t cnt = 0, prev = res->in_N;
    for (size_t scan = 0; scan < res->in_N; scan++){
      const uint64_t cur = res->in_N - scan - 1;
      if(input_key->s[ki]->coeffs[cur] == 0) continue;
      res->s[ki][cnt] = trgsw_alloc_new_DFT_sample_array((int) r_prec,
          skey->l, skey->Bg_bit, (int) res->out_k, (int) res->out_N);
      RGSW_encrypt_bits(res->s[ki][cnt], tmp, skey, prev - cur, r_prec);
      prev = cur;
      cnt++;
    }
    res->s[ki][cnt] = trgsw_alloc_new_DFT_sample_array((int) r_prec, skey->l,
        skey->Bg_bit, (int) res->out_k, (int) res->out_N);
    RGSW_encrypt_bits(res->s[ki][cnt], tmp, skey, prev, r_prec);
  }
  free_trgsw(tmp);
  res->tmp = (tmp_pool) calloc(1, sizeof(*res->tmp));
  res->tmp->rlwe_dft = trlwe_alloc_new_DFT_sample((int) res->out_k,
      (int) res->out_N);
  res->tmp->rlwe = trlwe_alloc_new_sample((int) res->out_k, (int) res->out_N);
  res->tmp->rlwe_poly1 = trlwe_alloc_new_sample_array((int) res->in_N,
      (int) res->out_k, (int) res->out_N);
  res->tmp->rlwe_poly2 = trlwe_alloc_new_sample_array((int) res->in_N,
      (int) res->out_k, (int) res->out_N);
  return res;
}

/* Psi = U_(0,1) o sigma_{-1} (HT-4): t = sigma_{-1}(in);
 * out = (t + sigma_h t) + Y*(t - sigma_h t), /2. */
void sab_rinput_wrap_psi(PVW_TMLWE out, PVW_TMLWE in, SAB_RINPUT_Key sab){
  pvmtmlwe_eval_automorphism(sab->tmp->t0, in, 2 * sab->out_N - 1,
      sab->aut_minus1);
  pvmtmlwe_eval_automorphism(sab->tmp->t2, sab->tmp->t0, 1 + sab->out_N,
      sab->aut_h);
  pvmtmlwe_add(sab->tmp->s_plus, sab->tmp->t0, sab->tmp->t2);
  pvmtmlwe_sub(sab->tmp->s_minus, sab->tmp->t0, sab->tmp->t2);
  pvmtmlwe_copy(sab->tmp->t1, sab->tmp->s_plus);
  pvmtmlwe_mul_by_xai_addto(sab->tmp->t1, sab->tmp->s_minus, 2);
  sab_rinput_rescale2(out, sab->tmp->t1);
}

/* CMUX: out = in1 + selector ⊡ (in2 - in1); in2 has had Psi applied. */
void sab_rinput_CMUX(PVW_TMLWE out, PVW_TMLWE in1, PVW_TMLWE in2,
    MAT_TRGSW_DFT selector, SAB_RINPUT_Key sab){
  pvmtmlwe_sub(sab->tmp->t2, in2, in1);
  mat_trgsw_mul_pvmtmlwe_DFT(sab->tmp->dft, sab->tmp->t2, selector,
      sab->tmp->scratch);
  pvmtmlwe_from_DFT(sab->tmp->t2, sab->tmp->dft);
  pvmtmlwe_add(out, in1, sab->tmp->t2);
}

void sab_rinput_RGSW_monomial_mul(PVW_TMLWE * p, MAT_TRGSW_DFT * e,
    SAB_RINPUT_Key sab){
  const uint64_t in_N = sab->in_N;
  PVW_TMLWE * buf[2] = {p, sab->tmp->buf2};
  uint64_t active = 0;
  for (size_t bit = 0; bit < sab->r_prec; bit++){
    const uint64_t power = 1ULL << bit;
    const uint64_t in = active;
    const uint64_t out = active ^ 1;
    /* wrapped slots j < power: source gets Psi (HT-4) */
    for (size_t j = 0; j < power; j++){
      sab_rinput_wrap_psi(sab->tmp->s_plus, buf[in][in_N - power + j], sab);
      sab_rinput_CMUX(buf[out][j], buf[in][j], sab->tmp->s_plus, e[bit], sab);
    }
    /* direct slots: plain data movement */
    for (size_t j = power; j < in_N; j++){
      sab_rinput_CMUX(buf[out][j], buf[in][j], buf[in][j - power], e[bit],
          sab);
    }
    active = out;
  }
  if(active != 0){
    for (size_t j = 0; j < in_N; j++) pvmtmlwe_copy(p[j], buf[1][j]);
  }
}

/* I-1: interleaved plaintext setup (granularity 2d mod switch on b).
 * r=1 form: one TV per input lane. */
void sab_rinput_setup_tv(PVW_TMLWE * acc, TRLWE in0, TRLWE in1,
    TorusPolynomial tv0, TorusPolynomial tv1, SAB_RINPUT_Key sab){
  TRLWE ins[2] = {in0, in1};
  const TorusPolynomial tv[2] = {tv0, tv1};
  sab_rinput_setup_tv_mb(acc, ins, tv, 1, sab);
}

/* joint form: r2 bodies, tv[lane][body]; body b carries LUT b for both
 * inputs (same bbar placement per input lane, per body). */
void sab_rinput_setup_tv_mb(PVW_TMLWE * acc, TRLWE * ins,
    const TorusPolynomial * tv /* [lane][body] */, uint64_t bodies,
    SAB_RINPUT_Key sab){
  const int log_2d = (int) log2(2 * sab->d);
  const uint64_t prec_offset = 1ULL << (64 - sab->b_prec - 1);
  const uint64_t two_d = 2 * sab->d;
  for (size_t t = 0; t < sab->in_N; t++){
    PVW_TMLWE c = acc[t];
    sab_rinput_zero(c);
    for (size_t lane = 0; lane < 2; lane++){
      const uint64_t bbar = torus2int(
          ins[lane]->b->coeffs[t] + prec_offset, log_2d);
      for (size_t q = 0; q < sab->d; q++){
        const uint64_t pos = (q + bbar) % two_d;
        for (size_t body = 0; body < bodies && body < (size_t) c->r;
            body++){
          const TorusPolynomial tvb = tv[lane * bodies + body];
          if(pos < sab->d)
            c->b[body]->coeffs[lane + 2 * pos] += tvb->coeffs[q];
          else
            c->b[body]->coeffs[lane + 2 * (pos - sab->d)] -= tvb->coeffs[q];
        }
      }
    }
  }
}

void sab_rinput_blind_rotate(PVW_TMLWE * out, TRLWE in0, TRLWE in1,
    SAB_RINPUT_Key sab){
  if(sab->in_k != 1) sab_rinput_die("only in_k=1 is supported");
  const int log_2d = (int) log2(2 * sab->d);
  for (size_t t = 0; t < sab->in_N; t++){
    sab->tmp->a_mod0[t] = torus2int(in0->a[0]->coeffs[t], log_2d);
    sab->tmp->a_mod1[t] = torus2int(in1->a[0]->coeffs[t], log_2d);
  }
  for (size_t step = 0; step < sab->h; step++){
    sab_rinput_RGSW_monomial_mul(out, sab->s[0][step], sab);
    /* all sub_as rescale; the uniform final x2 (below) cancels every
     * remaining rescale-wrap spurious and leaves a consistent x2 scale */
    sab_rinput_sub_a_homtr_opt(out, sab->tmp->a_mod0, sab->tmp->a_mod1, sab,
        1);
  }
  sab_rinput_RGSW_monomial_mul(out, sab->s[0][sab->h], sab);
  /* final identity Hom-Tr (U_(0,0), P_h = 0, no KS): double every slot.
   * The x2 cancels ALL remaining +-2^63 rescale-wrap spuria (the +/-
   * trace-weight doubling maps them to 2^64 multiples; see stage396 HT-7),
   * including the ones left by the final butterfly's Psi rescales, which
   * have no subsequent U_a. Extraction divides by 2 in the clear. */
  for (size_t t = 0; t < sab->in_N; t++){
    PVW_TMLWE c = out[t];
    const int N = c->b[0]->N;
    for (size_t idx = 0; idx < (size_t) c->k; idx++){
      for (size_t q = 0; q < (size_t) N; q++)
        c->a[idx]->coeffs[q] += c->a[idx]->coeffs[q];
    }
    for (size_t lane = 0; lane < (size_t) c->r; lane++){
      for (size_t q = 0; q < (size_t) N; q++)
        c->b[lane]->coeffs[q] += c->b[lane]->coeffs[q];
    }
  }
}

void sab_rinput_bootstrap_wo_extract(PVW_TMLWE * out, TRLWE in0, TRLWE in1,
    TorusPolynomial tv0, TorusPolynomial tv1, SAB_RINPUT_Key sab){
  sab_rinput_setup_tv(out, in0, in1, tv0, tv1, sab);
  sab_rinput_blind_rotate(out, in0, in1, sab);
}
