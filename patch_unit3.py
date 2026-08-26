"""Split test: bind id-only and tau-only on the REAL o3 ciphertexts."""
PATH = r"D:\codexprograms\whFast-Amortized-Bootstrapping\Fast-Amortized-Bootstrapping\main.c"
NL = chr(10)
BSN = chr(92) + "n"

text = open(PATH, encoding="utf-8").read()

anchor = "    free_polynomial(p3);"
split_probe = [
    "    /* split: id-only and tau-only binds on the same real ciphertexts */",
    "    for (int half = 0; half < 2; half++){",
    "      SAB_Operator_State tmpH = sab_operator_new_state(opkey);",
    "      for (size_t jj = 0; jj < in_N; jj++)",
    "        for (int gg = 0; gg < 2; gg++){",
    "          for (int cc = 0; cc < tmpH->channel[jj][gg]->k; cc++)",
    "            polynomial_zero_torus_polynomial(tmpH->channel[jj][gg]->a[cc]);",
    "          polynomial_zero_torus_polynomial(tmpH->channel[jj][gg]->b);",
    "        }",
    "      /* half=0: id only (copy o3[0]); half=1: tau only (copy o3[1]) */",
    "      for (int cc = 0; cc < out_k; cc++)",
    "        polynomial_copy_torus_polynomial(",
    "            tmpH->channel[0][half]->a[cc], o3[half]->a[cc]);",
    "      polynomial_copy_torus_polynomial(tmpH->channel[0][half]->b, o3[half]->b);",
    "      TRLWE * ubH = trlwe_alloc_new_sample_array(in_N, out_k, out_N);",
    "      sab_operator_bind(ubH, tmpH, tv->b, opkey);",
    "      TorusPolynomial pH = polynomial_new_torus_polynomial(out_N);",
    "      trlwe_phase(pH, ubH[0], output_key->trlwe_key);",
    '      printf("UNIT3-SPLIT half=%d: [31]=%ld [35]=%ld [39]=%ld [29]=%ld [41]=%ld [45]=%ld [25]=%ld",',
    "             half,",
    "             (long)((int64_t)pH->coeffs[31] >> 44),",
    "             (long)((int64_t)pH->coeffs[35] >> 44),",
    "             (long)((int64_t)pH->coeffs[39] >> 44),",
    "             (long)((int64_t)pH->coeffs[29] >> 44),",
    "             (long)((int64_t)pH->coeffs[41] >> 44),",
    "             (long)((int64_t)pH->coeffs[45] >> 44),",
    "             (long)((int64_t)pH->coeffs[25] >> 44));",
    '      printf("' + BSN + '");',
    "      free_polynomial(pH);",
    "      free_trlwe_array(ubH, in_N);",
    "      sab_operator_free_state(tmpH, opkey);",
    "    }",
    "    free_polynomial(p3);"
]
assert anchor in text, "anchor missing"
text = text.replace(anchor, NL.join(split_probe), 1)
open(PATH, "w", encoding="utf-8").write(text)
print("split test installed")
