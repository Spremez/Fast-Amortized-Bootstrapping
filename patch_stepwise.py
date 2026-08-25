"""UNIT3: bind on a REAL ciphertext channel. Take hand channels through one
CMUX (mu=1) so they carry a real mask, then bind: expect F * X^30."""
PATH = r"D:\codexprograms\whFast-Amortized-Bootstrapping\Fast-Amortized-Bootstrapping\main.c"
NL = chr(10)
BSN = chr(92) + "n"

text = open(PATH, encoding="utf-8").read()

anchor = "  sab_operator_setup(state, in->b->coeffs, opkey);"
probe = [
    "  {",
    "    /* UNIT3: bind after one CMUX -> channels become REAL ciphertexts */",
    "    SAB_Operator_State ust3 = sab_operator_new_state(opkey);",
    "    for (size_t jj = 0; jj < in_N; jj++)",
    "      for (int gg = 0; gg < 2; gg++){",
    "        for (int cc = 0; cc < ust3->channel[jj][gg]->k; cc++)",
    "          polynomial_zero_torus_polynomial(ust3->channel[jj][gg]->a[cc]);",
    "        polynomial_zero_torus_polynomial(ust3->channel[jj][gg]->b);",
    "      }",
    "    ust3->channel[0][0]->b->coeffs[10] += (Torus)(1LL << 62);",
    "    ust3->channel[0][1]->b->coeffs[20] += (Torus)(1LL << 62);",
    "    TRLWE k3[2] = {ust3->channel[0][0], ust3->channel[0][1]};",
    "    TRLWE s3[2] = {trlwe_alloc_new_sample(out_k, out_N),",
    "                   trlwe_alloc_new_sample(out_k, out_N)};",
    "    for (int cc = 0; cc < out_k; cc++){",
    "      polynomial_zero_torus_polynomial(s3[0]->a[cc]);",
    "      polynomial_zero_torus_polynomial(s3[1]->a[cc]);",
    "    }",
    "    polynomial_zero_torus_polynomial(s3[0]->b);",
    "    polynomial_zero_torus_polynomial(s3[1]->b);",
    "    s3[0]->b->coeffs[30] += (Torus)(1LL << 62);",
    "    s3[1]->b->coeffs[40] += (Torus)(1LL << 62);",
    "    TRGSW_DFT * sel3 = trgsw_alloc_new_DFT_sample_array(r_prec, 1, 23, out_k, out_N);",
    "    RGSW_encrypt_bits(sel3, sab->tmp->rgsw, output_key, 1, r_prec);",
    "    TRLWE o3[2] = {trlwe_alloc_new_sample(out_k, out_N),",
    "                   trlwe_alloc_new_sample(out_k, out_N)};",
    "    sab_operator_cmux(o3, k3, s3, sel3[0], opkey);",
    "    /* o3 is now a REAL ciphertext pair encrypting 1/4 X^30 / 1/4 X^40 */",
    "    TRLWE * ub3 = trlwe_alloc_new_sample_array(in_N, out_k, out_N);",
    "    SAB_Operator_State tmp3 = sab_operator_new_state(opkey);",
    "    for (int cc = 0; cc < out_k; cc++){",
    "      polynomial_copy_torus_polynomial(tmp3->channel[0][0]->a[cc], o3[0]->a[cc]);",
    "      polynomial_copy_torus_polynomial(tmp3->channel[0][1]->a[cc], o3[1]->a[cc]);",
    "    }",
    "    polynomial_copy_torus_polynomial(tmp3->channel[0][0]->b, o3[0]->b);",
    "    polynomial_copy_torus_polynomial(tmp3->channel[0][1]->b, o3[1]->b);",
    "    sab_operator_bind(ub3, tmp3, tv->b, opkey);",
    "    TorusPolynomial p3 = polynomial_new_torus_polynomial(out_N);",
    "    trlwe_phase(p3, ub3[0], output_key->trlwe_key);",
    "    int64_t u3m = 0; int u3p = -1;",
    "    for (size_t c = 0; c < out_N; c++){",
    "      int64_t v = (int64_t)p3->coeffs[c]; int64_t a9 = v < 0 ? -v : v;",
    "      if(a9 > u3m){ u3m = a9; u3p = (int)c; }",
    "    }",
    '    printf("UNIT3 real-cipher bind: max=%ld@%d sign=%ld (expect 65536@31 and 196608@35)",',
    "           (long)(u3m >> 44), u3p,",
    "           u3p >= 0 ? (long)((int64_t)p3->coeffs[u3p] >> 44) : 0L);",
    '    printf("' + BSN + '");',
    "    int64_t v31 = (int64_t)p3->coeffs[31] >> 44;",
    "    int64_t v35 = (int64_t)p3->coeffs[35] >> 44;",
    '    printf("UNIT3 detail: [31]=%ld (expect 65536) [35]=%ld (expect 196608)",',
    "           (long)v31, (long)v35);",
    '    printf("' + BSN + '");',
    "    free_polynomial(p3);",
    "    free_trlwe_array(ub3, in_N);",
    "    sab_operator_free_state(tmp3, opkey);",
    "    free_trlwe(o3[0]); free_trlwe(o3[1]);",
    "    free_trlwe(s3[0]); free_trlwe(s3[1]);",
    "    sab_operator_free_state(ust3, opkey);",
    "  }",
    "  sab_operator_setup(state, in->b->coeffs, opkey);"
]
assert anchor in text, "anchor missing"
text = text.replace(anchor, NL.join(probe), 1)
open(PATH, "w", encoding="utf-8").write(text)
print("UNIT3 installed")
