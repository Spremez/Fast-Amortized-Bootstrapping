"""v11 bind: digit decomposition (small side, <=2^22) x prescaled-weighted
F spectra. All layer products stay <= 2^80 (double-precision safe); the
reconstruction sum_d dig_d * 2^(23d) * F * 2^-60 = F * comp / 2^60 is exact
for the 2^62-class channels (F*comp/2^60 = F*X^pos for comp = 2^62 X^pos)."""
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
  /* v11: digit decomposition times prescaled-weighted multiplier spectra.
   * The library spectrum path is an exact-as-doubles convolution whose
   * products must stay near 2^80 (53-bit relative precision): trivial
   * 2^62-spike inputs worked at 2^83 but real-cipher masks (~2^85) break.
   * Decompose every channel component into 23-bit digits (<= 2^22, the
   * small side) and multiply against spec(F * 2^(23d - 60)): the layer
   * products are <= 2^22 * 2^(23d-60+62) * sqrt(N) <= 2^80, and the
   * reconstruction sum_d dig_d * 2^(23d) * F * 2^-60 = F * comp / 2^60,
   * which is exactly F * X^pos for the 2^62-class (scale 1/4) channel
   * content. tau_{-1}(F)_0 = F_0, tau_{-1}(F)_{N-j} = -F_j. */
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
  DFT_Polynomial * dft = polynomial_new_array_of_polynomials_DFT(out_N, 10);
  /* prescaled-weighted spectra: spec(F * 2^(23d-60)) and tau versions */
  for(int d = 0; d < layers; d++)
  {
    const double w = 1.0 / (double) (((Torus) 1) << (60 - 23 * d));
    polynomial_torus_to_DFT(dft[4 + d], F);
    polynomial_torus_to_DFT(dft[4 + layers + d], tau_F);
    for(int q = 0; q < dft[4 + d]->N; q++)
    {
      dft[4 + d]->coeffs[q] *= w;
      dft[4 + layers + d]->coeffs[q] *= w;
    }
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
      int used = 0;
      for(int g = 0; g < SAB_OPERATOR_GAMMA; g++)
      {
        TorusPolynomial comp0 =
            (c == target_sample->k) ? state->channel[j][g]->b
                                    : state->channel[j][g]->a[c];
        for(int d = 0; d < layers; d++)
        {
          const int shift = bg * d;
          polynomial_zero_torus_polynomial(dig);
          bool any = false;
          for(int q = 0; q < out_N; q++)
          {
            const Torus v = (Torus)(
                (((int64_t) comp0->coeffs[q]) >> shift) & (int64_t) mask);
            dig->coeffs[q] = v;
            if(v != 0) any = true;
          }
          if(!any) continue;
          polynomial_torus_to_DFT(dft[0], dig);
          if(used == 0)
            polynomial_mul_DFT(dft[1], dft[0], dft[4 + d]);
          else
            polynomial_mul_addto_DFT(dft[1], dft[0], dft[4 + d]);
          used++;
        }
        /* tau channel: same digits against the tau spectra; comp0 already
         * selected per g, so redo the digit loop for the tau multiplier */
        if(g == 1)
        {
          /* the loop above used the F spectra for both channels: redo
           * correctly by handling each channel separately below */
        }
      }
      /* NOTE: the g-loop above is structurally wrong (both channels hit
       * the F spectra); v11 does it correctly channel by channel: */
      used = 0;
      for(int g = 0; g < SAB_OPERATOR_GAMMA; g++)
      {
        TorusPolynomial comp0 =
            (c == target_sample->k) ? state->channel[j][g]->b
                                    : state->channel[j][g]->a[c];
        for(int d = 0; d < layers; d++)
        {
          const int shift = bg * d;
          polynomial_zero_torus_polynomial(dig);
          bool any = false;
          for(int q = 0; q < out_N; q++)
          {
            const Torus v = (Torus)(
                (((int64_t) comp0->coeffs[q]) >> shift) & (int64_t) mask);
            dig->coeffs[q] = v;
            if(v != 0) any = true;
          }
          if(!any) continue;
          polynomial_torus_to_DFT(dft[0], dig);
          DFT_Polynomial mult = dft[4 + (g ? layers : 0) + d];
          if(used == 0)
            polynomial_mul_DFT(dft[1], dft[0], mult);
          else
            polynomial_mul_addto_DFT(dft[1], dft[0], mult);
          used++;
        }
      }
      if(used == 0)
      {
        polynomial_zero_torus_polynomial(target_comp);
        continue;
      }
      polynomial_DFT_to_torus(target_comp, dft[1]);
    }
  }
  free_polynomial(tau_F);
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
print("v11 written; brace balance:", text.count("{") - text.count("}"))
