"""UNIT4: both channels trivial simultaneously."""
PATH = r"D:\codexprograms\whFast-Amortized-Bootstrapping\Fast-Amortized-Bootstrapping\main.c"
NL = chr(10)
BSN = chr(92) + "n"

text = open(PATH, encoding="utf-8").read()

anchor = "  sab_operator_setup(state, in->b->coeffs, opkey);"
probe = [
    "  {",
    "    /* UNIT4: BOTH channels trivial (id=1/4 X^30, tau=1/4 X^40):",
    "     * full bind = F*X^30 + tauF*X^40:",
    "     * expect [31]=+65536, [35]=0, [39]=-65536 */",
    "    SAB_Operator_State ust4 = sab_operator_new_state(opkey);",
    "    for (size_t jj = 0; jj < in_N; jj++)",
    "      for (int gg = 0; gg < 2; gg++){",
    "        for (int cc = 0; cc < ust4->channel[jj][gg]->k; cc++)",
    "          polynomial_zero_torus_polynomial(ust4->channel[jj][gg]->a[cc]);",
    "        polynomial_zero_torus_polynomial(ust4->channel[jj][gg]->b);",
    "      }",
    "    ust4->channel[0][0]->b->coeffs[30] += (Torus)(1LL << 62);",
    "    ust4->channel[0][1]->b->coeffs[40] += (Torus)(1LL << 62);",
    "    TRLWE * ub4 = trlwe_alloc_new_sample_array(in_N, out_k, out_N);",
    "    sab_operator_bind(ub4, ust4, tv->b, opkey);",
    "    TorusPolynomial p4 = polynomial_new_torus_polynomial(out_N);",
    "    trlwe_phase(p4, ub4[0], output_key->trlwe_key);",
    '    printf("UNIT4 both-trivial: [31]=%ld(exp+65536) [35]=%ld(exp0) [39]=%ld(exp-65536) [29]=%ld [41]=%ld [25]=%ld [45]=%ld",',
    "           (long)((int64_t)p4->coeffs[31] >> 44),",
    "           (long)((int64_t)p4->coeffs[35] >> 44),",
    "           (long)((int64_t)p4->coeffs[39] >> 44),",
    "           (long)((int64_t)p4->coeffs[29] >> 44),",
    "           (long)((int64_t)p4->coeffs[41] >> 44),",
    "           (long)((int64_t)p4->coeffs[25] >> 44),",
    "           (long)((int64_t)p4->coeffs[45] >> 44));",
    '    printf("' + BSN + '");',
    "    free_polynomial(p4);",
    "    free_trlwe_array(ub4, in_N);",
    "    sab_operator_free_state(ust4, opkey);",
    "  }",
    "  sab_operator_setup(state, in->b->coeffs, opkey);"
]
assert anchor in text, "anchor missing"
text = text.replace(anchor, NL.join(probe), 1)
open(PATH, "w", encoding="utf-8").write(text)
print("UNIT4 installed")
