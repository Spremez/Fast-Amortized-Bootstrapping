"""v8 bind: EP-structure bind. Decompose channel components into 23-bit
digits; the digit weight 2^(23d+2) is applied by PRE-WRAPPING the public
multiplier in the time domain: F_d = (F << (23d+2)) mod 2^64 (exactly what
encrypted TRGSW rows do implicitly). Products stay in the 2^95 class
(error ~2^-21 torus); accumulate in DFT; single inverse; result =
(4F * comp) mod 2^64 exactly the desired phase-rescaled product."""
PATH = r"D:\codexprograms\whFast-Amortized-Bootstrapping\Fast-Amortized-Bootstrapping\src\\sab_operator.c"
NL = chr(10)

text = open(PATH, encoding="utf-8").read()

start = text.index("void" + NL + "sab_operator_bind")
end_marker = "trlwe_keyswitch(out[j], out[j], key->rerand_ks);"
end = text.index(end_marker)
end = text.index("}", end) + 1

new_fn = """void
sab_operator_bind (TRLWE *out, SAB_Operator_State state,
                   TorusPolynomial F, SAB_Operator_Key key)
{
  /* v8: external-product structure. The library DFT is an integer
   * convolution; products must stay near the 2^95 class. Decompose each
   * channel component into 23-bit digits (the small side, like the EP)
   * and apply the reconstruction weight 2^(23d+2) by pre-wrapping the
   * public multiplier in the time domain: F_d = (F << (23d+2)) mod 2^64,
   * whose spectrum is an ordinary full-scale torus spectrum (the wrap is
   * exactly how encrypted gadget rows carry their scale). Accumulate all
   * layer products in one DFT buffer, take a single inverse: the result
   * is (4F * comp) mod 2^64, i.e. the channel scale 1/4 is undone
   * exactly. tau_{-1}(F)_0 = F_0, tau_{-1}(F)_{N-j} = -F_j. */
  const SAB_Key sab = key->sab;
  const int in_N = (int) sab->in_N;
  const int out_N = (int) sab->out_N;
  const int bg = 23;
  const int layers = 3;
  init_fft(out_N);
  TorusPolynomial tau_F = polynomial_new_torus_polynomial(out_N);
  tau_F->coeffs[0] = F->coeffs[0];
  for(int j = 1; j < out_N; j++)
    tau_F->coeffs[out_N - j] = -F->coeffs[j];
  DFT_Polynomial * dft = polynomial_new_array_of_polynomials_DFT(out_N, 8);
  /* F_d and tauF_d spectra for d = 0..layers-1 */
  TorusPolynomial wrap = polynomial_new_torus_polynomial(out_N);
  for(int d = 0; d < layers; d++)
  {
    const int shift = 23 * d + 2;
    for(int q = 0; q < out_N; q++)
      wrap->coeffs[q] = (Torus)(((uint64_t) F->coeffs[q]) << shift);
    polynomial_torus_to_DFT(dft[4 + d], wrap);
    for(int q = 0; q < out_N; q++)
      wrap->coeffs[q] = (Torus)(((uint64_t) tau_F->coeffs[q]) << shift);
    polynomial_torus_to_DFT(dft[4 + layers + d], wrap);
  }
  TorusPolynomial dig = polynomial_new_torus_polynomial(out_N);
  const Torus mask = (((Torus) 1) << bg) - 1;
  for(int j = 0; j < in_N; j++)
  {
    TRLWE target_sample = out[j];
    for(int c = 0; c <= target_sample->k; c++)
    {
      TorusPolynomial target_comp =
          (c == target_sample->k) ? target_sample->b : target_sample->a[c];
      for(int g = 0; g < SAB_OPERATOR_GAMMA; g++)
      {
        TorusPolynomial comp =
            (c == target_sample->k) ? state->channel[j][g]->b
                                    : state->channel[j][g]->a[c];
        int used = 0;
        for(int d = 0; d < layers; d++)
        {
          const int shift = bg * d;
          polynomial_zero_torus_polynomial(dig);
          bool any = false;
          for(int q = 0; q < out_N; q++)
          {
            const Torus v = (Torus)(
                (((int64_t) comp->coeffs[q]) >> shift) & (int64_t) mask);
            dig->coeffs[q] = v;
            if(v != 0) any = true;
          }
          if(!any) continue;
          polynomial_torus_to_DFT(dft[0], dig);
          DFT_Polynomial mult_dft =
              dft[4 + (g ? layers : 0) + d];
          if(used == 0)
            polynomial_mul_DFT(dft[1], dft[0], mult_dft);
          else
            polynomial_mul_addto_DFT(dft[1], dft[0], mult_dft);
          used++;
        }
        if(used == 0)
        {
          polynomial_zero_torus_polynomial(target_comp);
          continue;
        }
        polynomial_DFT_to_torus(target_comp, dft[1]);
      }
    }
  }
  free_polynomial(tau_F);
  free_polynomial(wrap);
  free_polynomial(dig);
  free_polynomial(dft);
  if(key->rerand_ks != NULL)
  {
    for(int j = 0; j < in_N; j++)
      trlwe_keyswitch(out[j], out[j], key->rerand_ks);
  }
}"""

text = text[:start] + new_fn + text[end:]
open(PATH, "w", encoding="utf-8").write(text)
print("v8 written; brace balance:", text.count("{") - text.count("}"))
