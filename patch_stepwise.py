"""Micro test: single sab_operator_ncmux / sab_operator_cmux calls on hand
channel pairs. Verifies A' = tau(B_src), B' = tau(A_src) under mu=1 and the
CMUX pass-through, by decrypting phases."""
PATH = r"D:\codexprograms\whFast-Amortized-Bootstrapping\Fast-Amortized-Bootstrapping\main.c"
NL = chr(10)
BSN = chr(92) + "n"

text = open(PATH, encoding="utf-8").read()

anchor = "  sab_operator_setup(state, in->b->coeffs, opkey);"
probe = [
    "  {",
    "    /* single-call micro test of the operator NCMUX/CMUX wiring */",
    "    TRLWE base[2][2];",
    "    for (int g2 = 0; g2 < 2; g2++)",
    "      for (int s2 = 0; s2 < 2; s2++)",
    "        base[g2][s2] = trlwe_alloc_new_sample(out_k, out_N);",
    "    for (int g2 = 0; g2 < 2; g2++)",
    "      for (int s2 = 0; s2 < 2; s2++){",
    "        for (int cc = 0; cc < out_k; cc++)",
    "          polynomial_zero_torus_polynomial(base[g2][s2]->a[cc]);",
    "        polynomial_zero_torus_polynomial(base[g2][s2]->b);",
    "      }",
    "    /* keep pair: id=1/2 X^10, tau=1/2 X^20 ; src pair: id=1/2 X^30,",
    "     * tau=1/2 X^40 (torus 1/2 = 2^62 scale like the channels) */",
    "    base[0][0]->b->coeffs[10] += (Torus)(1LL << 62);",
    "    base[0][1]->b->coeffs[20] += (Torus)(1LL << 62);",
    "    base[1][0]->b->coeffs[30] += (Torus)(1LL << 62);",
    "    base[1][1]->b->coeffs[40] += (Torus)(1LL << 62);",
    "    TRGSW_DFT * sel = trgsw_alloc_new_DFT_sample_array(r_prec, 1, 23, out_k, out_N);",
    "    RGSW_encrypt_bits(sel, sab->tmp->rgsw, output_key, 1, r_prec);",
    "    TRLWE o_pair[2] = {trlwe_alloc_new_sample(out_k, out_N),",
    "                       trlwe_alloc_new_sample(out_k, out_N)};",
    "    TRLWE keep[2] = {base[0][0], base[0][1]};",
    "    TRLWE src[2] = {base[1][0], base[1][1]};",
    "    TorusPolynomial mp = polynomial_new_torus_polynomial(out_N);",
    "    sab_operator_ncmux(o_pair, keep, src, sel[0], opkey);",
    "    /* mu=1: expect out[0] = -tau(keep_id-> wait: expect tau(src_tau) = X^-40,",
    "     * out[1] = tau(src_id) = X^-30 (negacyclic reflections) */",
    "    trlwe_phase(mp, o_pair[0], output_key->trlwe_key);",
    "    int p0 = -1;",
    "    for (size_t c = 0; c < out_N; c++)",
    "      if(((int64_t)mp->coeffs[c] >> 44) != 0){ p0 = (int)c; break; }",
    '    printf("MICRO ncmux out0 peak at %d (expect %d = N-40, sign %ld)",',
    "           p0, out_N - 40, p0 >= 0 ? (long)((int64_t)mp->coeffs[p0] >> 44) : 0L);",
    '    printf("' + BSN + '");',
    "    trlwe_phase(mp, o_pair[1], output_key->trlwe_key);",
    "    int p1 = -1;",
    "    for (size_t c = 0; c < out_N; c++)",
    "      if(((int64_t)mp->coeffs[c] >> 44) != 0){ p1 = (int)c; break; }",
    '    printf("MICRO ncmux out1 peak at %d (expect %d = N-30, sign %ld)",',
    "           p1, out_N - 30, p1 >= 0 ? (long)((int64_t)mp->coeffs[p1] >> 44) : 0L);",
    '    printf("' + BSN + '");',
    "    sab_operator_cmux(o_pair, keep, src, sel[0], opkey);",
    "    trlwe_phase(mp, o_pair[0], output_key->trlwe_key);",
    "    int p2 = -1;",
    "    for (size_t c = 0; c < out_N; c++)",
    "      if(((int64_t)mp->coeffs[c] >> 44) != 0){ p2 = (int)c; break; }",
    '    printf("MICRO cmux out0 peak at %d (expect 30, sign %ld)",',
    "           p2, p2 >= 0 ? (long)((int64_t)mp->coeffs[p2] >> 44) : 0L);",
    '    printf("' + BSN + '");',
    "    free_polynomial(mp);",
    "    free_trlwe_sample(o_pair[0]); free_trlwe_sample(o_pair[1]);",
    "    free_trlwe_DFT_sample_array(sel, r_prec);",
    "    for (int g2 = 0; g2 < 2; g2++)",
    "      for (int s2 = 0; s2 < 2; s2++)",
    "        free_trlwe(base[g2][s2]);",
    "  }",
    "  sab_operator_setup(state, in->b->coeffs, opkey);"
]
assert anchor in text, "anchor missing"
text = text.replace(anchor, NL.join(probe), 1)
open(PATH, "w", encoding="utf-8").write(text)
print("micro test installed")
