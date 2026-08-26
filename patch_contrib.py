"""Instrument the bind to dump each (g,d) layer's partial contribution at
the key positions, isolating which layer loses its weight."""
PATH = r"D:\codexprograms\whFast-Amortized-Bootstrapping\Fast-Amortized-Bootstrapping\src\sab_operator.c"
NL = chr(10)
BSN = chr(92) + "n"

text = open(PATH, encoding="utf-8").read()

old = """          polynomial_torus_to_DFT(dft[0], dig);
          DFT_Polynomial mult = dft[4 + (g ? layers : 0) + d];
          if(used == 0)
            polynomial_mul_DFT(dft[1], dft[0], mult);
          else
            polynomial_mul_addto_DFT(dft[1], dft[0], mult);
          used++;"""
new = """          polynomial_torus_to_DFT(dft[0], dig);
          DFT_Polynomial mult = dft[4 + (g ? layers : 0) + d];
          if(used == 0)
            polynomial_mul_DFT(dft[1], dft[0], mult);
          else
            polynomial_mul_addto_DFT(dft[1], dft[0], mult);
          used++;
#ifdef SAB_OPERATOR_LAYER_DEBUG
          if(j == 0 && c == target_sample->k)
          {
            static __thread TorusPolynomial dp = NULL;
            if(!dp) dp = polynomial_new_torus_polynomial(out_N);
            polynomial_DFT_to_torus(dp, dft[1]);
            printf("LAYERP j0 b g=%d d=%d: [31]=%ld [35]=%ld [39]=%ld",
                   g, d,
                   (long)((int64_t)dp->coeffs[31] >> 44),
                   (long)((int64_t)dp->coeffs[35] >> 44),
                   (long)((int64_t)dp->coeffs[39] >> 44));
            printf("PCNL");
          }
#endif"""
assert old in text, "main loop anchor missing"
text = text.replace(old, new, 1)
text = text.replace('printf("PCNL");', 'printf("' + BSN + '");')
if "#define SAB_OPERATOR_LAYER_DEBUG 1" not in text:
    text = text.replace('#include <stdlib.h>', '#include <stdlib.h>\n#define SAB_OPERATOR_LAYER_DEBUG 1', 1)
open(PATH, "w", encoding="utf-8").write(text)
print("layer-contribution debug installed")
