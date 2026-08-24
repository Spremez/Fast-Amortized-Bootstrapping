/* SAB operator-state (Candidate D) reference implementation.
 *
 * Admitted by the D0-D3 gates; see docs/d4_implementation_plan.md and
 * theory_checks/candidate_d_operator_closure.md. Implements the channel
 * update laws verified by the D2 exact checker at the ciphertext level by
 * reusing the scalar SAB machinery:
 *
 *   setup     U_j = (X^{b_j}, 0) as public trivial channels;
 *   CMUX      channel-wise scalar CMUX (2g = 4 scalar products per event);
 *   NCMUX    -tau_{-1} with the channel swap: the scalar NCMUX with
 *             generator 2N-1 already applies -tau_{-1} (X^{2N-1} =
 *             -X^{-1} mod X^N + 1), so the operator variant cross-wires the
 *             source channels and calls it per channel;
 *   monomial  the scalar r_prec butterfly applied to channel pairs;
 *   sub_a     the scalar per-slot public monomial rotation (binary plain or
 *             include-zero with the per-coefficient selector), applied to
 *             both channels;
 *   bind      out_j = F * U_id,j + tau_{-1}(F) * U_tau,j via public torus
 *             polynomial products, then the mandatory rerandomization when
 *             a rerandomization key is present.
 *
 * Ownership boundaries hold: sab_rlwe_bootstrap and sab_pvw_* untouched.
 */

#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "sab_b.h"
#include "sab_operator.h"

static void sab_operator_die (const char *msg)
{
  fprintf(stderr, "sab_operator: %s\n", msg);
  exit(1);
}

SAB_Operator_Key
sab_operator_wrap_scalar (SAB_Key sab, TRLWE_KS_Key rerand_ks)
{
  if(sab == NULL) sab_operator_die("scalar key is NULL");
  SAB_Operator_Key key = (SAB_Operator_Key) malloc(sizeof(*key));
  if(key == NULL) sab_operator_die("malloc failed");
  key->in_N = (int) sab->in_N;
  key->h = (int) sab->h;
  key->r_prec = (int) sab->r_prec;
  key->sab = sab;
  key->rerand_ks = rerand_ks; /* NULL for phase-level equivalence tests */
  return key;
}

void
sab_operator_free_key (SAB_Operator_Key key)
{
  free(key); /* the scalar key stays owned by the caller */
}

SAB_Operator_State
sab_operator_new_state (SAB_Operator_Key key)
{
  SAB_Operator_State state = (SAB_Operator_State) malloc(sizeof(*state));
  if(state == NULL) sab_operator_die("malloc failed");
  state->in_N = key->in_N;
  state->channel = (TRLWE **) calloc(
      (size_t) key->in_N, sizeof(TRLWE *));
  if(state->channel == NULL) sab_operator_die("malloc failed");
  for(int j = 0; j < key->in_N; j++)
    state->channel[j] = trlwe_alloc_new_sample_array(
        SAB_OPERATOR_GAMMA, (int) key->sab->out_k, (int) key->sab->out_N);
  return state;
}

void
sab_operator_free_state (SAB_Operator_State state, SAB_Operator_Key key)
{
  if(state == NULL) return;
  for(int j = 0; j < state->in_N; j++)
    free_trlwe_array(state->channel[j], SAB_OPERATOR_GAMMA);
  free(state->channel);
  free(state);
  (void) key;
}

/* U_j = (X^{b_j}, 0): public trivial channels. Mirrors setup_tv_xb's
 * rounding convention: shift = torus2int(b_j + prec_offset, log2(2N)). */
void
sab_operator_setup (SAB_Operator_State state, const uint64_t *b,
                    SAB_Operator_Key key)
{
  const SAB_Key sab = key->sab;
  const int in_N = (int) sab->in_N;
  const int out_N = (int) sab->out_N;
  const int log_N2 = (int) log2((double) (out_N * 2));
  const uint64_t prec_offset = 1ULL << (64 - sab->b_prec - 1);
  for(int j = 0; j < in_N; j++)
  {
    TRLWE id_channel = state->channel[j][0];
    TRLWE tau_channel = state->channel[j][1];
    for(int c = 0; c < id_channel->k; c++)
    {
      polynomial_zero_torus_polynomial(id_channel->a[c]);
      polynomial_zero_torus_polynomial(tau_channel->a[c]);
    }
    polynomial_zero_torus_polynomial(id_channel->b);
    polynomial_zero_torus_polynomial(tau_channel->b);
    /* Negacyclic monomial at the torus scale 1/4. Scale 1/2 cannot encode
     * the negacyclic sign because +1/2 and -1/2 are the same torus value
     * (2^63 == -2^63 mod 2^64); at 1/4 they are distinct (2^62 vs -2^62).
     * The binder correspondingly multiplies by 4F via exact digit-layer
     * decomposition (see sab_operator_bind), which never forms the
     * unrepresentable polynomial 4F itself. */
    const int64_t s = (int64_t) torus2int(b[j] + prec_offset, log_N2);
    const int pos = (int) (s % out_N);
    id_channel->b->coeffs[pos] +=
        (s >= out_N) ? (Torus)(-(1LL << 62)) : (Torus)(1LL << 62);
  }
}

/* Channel-wise CMUX with the scalar TRGSW selector. */
void
sab_operator_cmux (TRLWE out[2], TRLWE in0[2], TRLWE in1[2],
                   TRGSW_DFT selector, SAB_Operator_Key key)
{
  CMUX(out[0], in0[0], in1[0], selector, key->sab);
  CMUX(out[1], in0[1], in1[1], selector, key->sab);
}

/* Wrapped-source NCMUX: -tau_{-1} swaps the channels (the D2 law); the
 * scalar NCMUX already applies -tau_{-1} through generator 2N-1, so the
 * operator variant only cross-wires the sources. */
void
sab_operator_ncmux (TRLWE out[2], TRLWE in0[2], TRLWE in1[2],
                    TRGSW_DFT selector, SAB_Operator_Key key)
{
  NCMUX(out[0], in0[0], in1[1], selector, key->sab);
  NCMUX(out[1], in0[1], in1[0], selector, key->sab);
}

/* The scalar r_prec butterfly over channel pairs: whole pairs move between
 * slots; wrapped sources go through the channel-swapping NCMUX, non-wrapped
 * sources through the aligned CMUX. */
void
sab_operator_rgsw_monomial_mul (SAB_Operator_State state,
                                TRGSW_DFT *e, SAB_Operator_Key key)
{
  const SAB_Key sab = key->sab;
  const int r_prec = (int) sab->r_prec, in_N = (int) sab->in_N;
  TRLWE * buf[SAB_OPERATOR_GAMMA][2];
  int cur[SAB_OPERATOR_GAMMA] = {0, 0};
  for(int g = 0; g < SAB_OPERATOR_GAMMA; g++)
  {
    buf[g][0] = (TRLWE *) calloc((size_t) in_N, sizeof(TRLWE));
    buf[g][1] = trlwe_alloc_new_sample_array(
        in_N, (int) sab->out_k, (int) sab->out_N);
    if(buf[g][0] == NULL || buf[g][1] == NULL) sab_operator_die("malloc failed");
    for(int j = 0; j < in_N; j++)
      buf[g][0][j] = state->channel[j][g];
  }
  for(int i = 0; i < r_prec; i++)
  {
    TRLWE * src[SAB_OPERATOR_GAMMA];
    TRLWE * dst[SAB_OPERATOR_GAMMA];
    for(int g = 0; g < SAB_OPERATOR_GAMMA; g++)
    {
      src[g] = buf[g][cur[g]];
      dst[g] = buf[g][cur[g] ^ 1];
    }
    const int power = 1 << i;
    for(int j = 0; j < power; j++)
    {
      TRLWE keep[2] = {src[0][j], src[1][j]};
      TRLWE wrapped[2] = {src[0][in_N - power + j], src[1][in_N - power + j]};
      TRLWE out_pair[2] = {dst[0][j], dst[1][j]};
      sab_operator_ncmux(out_pair, keep, wrapped, e[i], key);
    }
    for(int j = 0; j < in_N - power; j++)
    {
      TRLWE keep[2] = {src[0][j + power], src[1][j + power]};
      TRLWE shifted[2] = {src[0][j], src[1][j]};
      TRLWE out_pair[2] = {dst[0][j + power], dst[1][j + power]};
      sab_operator_cmux(out_pair, keep, shifted, e[i], key);
    }
    for(int g = 0; g < SAB_OPERATOR_GAMMA; g++)
      cur[g] ^= 1;
  }
  for(int g = 0; g < SAB_OPERATOR_GAMMA; g++)
  {
    TRLWE * final = buf[g][cur[g]];
    for(int j = 0; j < in_N; j++)
    {
      if(state->channel[j][g] != final[j])
        trlwe_copy(state->channel[j][g], final[j]);
    }
    free(buf[g][0]);
    free_trlwe_array(buf[g][1], in_N);
  }
}

/* The scalar sub_a semantics applied to both channels: plain binary is a
 * public monomial rotation; include-zero adds the coefficient-selector
 * external product with the same selector the scalar path uses. */
void
sab_operator_sub_a (SAB_Operator_State state, const uint64_t *a,
                    SAB_Operator_Key key)
{
  const SAB_Key sab = key->sab;
  const int in_N = (int) sab->in_N;
  for(int j = 0; j < in_N; j++)
  {
    for(int g = 0; g < SAB_OPERATOR_GAMMA; g++)
    {
      TRLWE p = state->channel[j][g];
      if(sab->include_zeros)
      {
        trlwe_mul_by_xai_minus_1(sab->tmp->rlwe, p, a[j]);
        trgsw_mul_trlwe_DFT(sab->tmp->rlwe_dft, sab->tmp->rlwe,
                            sab->s_coff[0][0]);
        trlwe_from_DFT(sab->tmp->rlwe, sab->tmp->rlwe_dft);
        trlwe_addto(p, sab->tmp->rlwe);
      }
      else
      {
        trlwe_mul_by_xai(sab->tmp->rlwe, p, a[j]);
        trlwe_copy(p, sab->tmp->rlwe);
      }
    }
  }
}

/* Late binding: out_j = F * U_id,j + tau_{-1}(F) * U_tau,j with
 * tau_{-1}(F)_0 = F_0 and tau_{-1}(F)_{N-j} = -F_j, then the mandatory
 * rerandomization when a key is present. */
void
sab_operator_bind (TRLWE *out, SAB_Operator_State state,
                   TorusPolynomial F, SAB_Operator_Key key)
{
  /* out_j = F * U_id,j + tau_{-1}(F) * U_tau,j with the channels carried
   * at scale 1/4. Writing the multiplier as 4F directly overflows the
   * torus for full-scale LUT coefficients, so 4F is applied as exact
   * digit layers: each layer multiplies the channel by a small-digit
   * polynomial through the FFT product and is then shifted left by an
   * exact power of two. Because LUT coefficients carry only
   * msg_prec-ish significant bits, only a couple of layers are nonzero.
   * tau_{-1}(F)_0 = F_0 and tau_{-1}(F)_{N-j} = -F_j. */
  const SAB_Key sab = key->sab;
  const int in_N = (int) sab->in_N;
  const int out_N = (int) sab->out_N;
  const int layer_bits = 8;
  const int layers = 64 / layer_bits + 1;
  /* Decompose F itself (never the overflowing 4F): the factor 4 from the
   * channel scale 1/4 enters only as the exact per-layer rescale
   * 2^(shift+2), reduced mod 2^64 once. */
  TorusPolynomial scratch = polynomial_new_torus_polynomial(out_N);
  TorusPolynomial F4 = polynomial_new_torus_polynomial(out_N);
  TorusPolynomial tau_F4 = polynomial_new_torus_polynomial(out_N);
  for(int j = 0; j < out_N; j++)
    F4->coeffs[j] = F->coeffs[j];
  tau_F4->coeffs[0] = F->coeffs[0];
  for(int j = 1; j < out_N; j++)
    tau_F4->coeffs[out_N - j] = -F->coeffs[j];
  /* digit layers of the 4F multipliers: layer d holds signed chunks of
   * layer_bits bits, shifted back by (4x prefactor >> (64 - 62)) = 2 bits;
   * the exact reconstruction is 4F = sum_d layer_d * 2^(d*layer_bits - 2)
   * in real torus units, i.e. layer coefficients carry the raw integer
   * chunks so the shift happens on the integer torus. */
  for(int j = 0; j < in_N; j++)
  {
    TRLWE target = out[j];
    for(int c = 0; c <= target->k; c++)
    {
      TorusPolynomial comp_id =
          (c == target->k) ? state->channel[j][0]->b
                           : state->channel[j][0]->a[c];
      TorusPolynomial comp_tau =
          (c == target->k) ? state->channel[j][1]->b
                           : state->channel[j][1]->a[c];
      TorusPolynomial target_comp =
          (c == target->k) ? target->b : target->a[c];
      for(int g = 0; g < SAB_OPERATOR_GAMMA; g++)
      {
        TorusPolynomial mult_poly = (g == 0) ? F4 : tau_F4;
        TorusPolynomial comp = (g == 0) ? comp_id : comp_tau;
        bool first = true;
        for(int d = 0; d < layers; d++)
        {
          const int shift = d * layer_bits;
          bool any = false;
          for(int q = 0; q < out_N; q++)
          {
            int64_t chunk =
                (((int64_t) mult_poly->coeffs[q]) >> shift)
                & ((1LL << layer_bits) - 1);
            if(chunk & (1LL << (layer_bits - 1)))
              chunk -= (1LL << layer_bits);
            scratch->coeffs[q] = (Torus) chunk;
            if(chunk != 0) any = true;
          }
          if(!any) continue;
          /* layer_d * 2^(shift+2-64) in real units: integer chunk times
           * the channel at 2^-2 gives 2^(shift-62) scale; accumulate the
           * product shifted so the total reconstructs chunk*2^shift * U/4
           * = mult_coeff * U/4 exactly on the integer torus. */
          const int scale = shift + 2 - layer_bits; /* leftover 2s cancel:
                                                       chunk<2^lb, U<2^62 */
          (void) scale;
          TorusPolynomial prod = polynomial_new_torus_polynomial(out_N);
          polynomial_mul_torus(prod, comp, scratch);
          for(int q = 0; q < out_N; q++)
          {
            Torus v = (Torus)((int64_t) prod->coeffs[q] << (shift + 2 - 64 + 64 - 64 + 0));
            /* shift left by (shift+2) is wrong for high layers; do the
             * exact integer rescale: prod holds chunk*U (int64 product of
             * |chunk|<2^8 and |U|<2^62 fits int64 with room), so multiply
             * by 2^(shift+2) mod 2^64 */
            v = (Torus)((( __int128) prod->coeffs[q])
                        * ((( __int128) 1) << (shift + 2)));
            if(first){ target_comp->coeffs[q] = v; }
            else { target_comp->coeffs[q] += v; }
          }
          first = false;
          free_polynomial(prod);
        }
        if(first) polynomial_zero_torus_polynomial(target_comp);
      }
    }
  }
  free_polynomial(scratch);
  free_polynomial(F4);
  free_polynomial(tau_F4);
  if(key->rerand_ks != NULL)
  {
    for(int j = 0; j < in_N; j++)
      trlwe_keyswitch(out[j], out[j], key->rerand_ks);
  }
}

