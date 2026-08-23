/* SAB operator-state (Candidate D) public API.
 *
 * Isolated encrypted-operator implementation admitted by the D0-D3 gates
 * (ADMIT_CANDIDATE_D_TO_ISOLATED_ENCRYPTED_OPERATOR_IMPLEMENTATION; see
 * docs/d4_implementation_plan.md). Ownership boundaries (design section 11):
 * this header and its implementation must not change the default behavior
 * of sab_rlwe_bootstrap, must not replace or remove sab_pvw_*, and must not
 * reintroduce the (k+r)^2 MAT state. All entry points live behind explicit
 * compile-time modes.
 *
 * The operator state U = (U_id, U_tau) per accumulator slot realizes the
 * LUT-independent linear operator O = U_id*id + U_tau*tau_{-1}; the update
 * laws are the ones verified by the D2 exact checker (channel-wise CMUX,
 * negated tau_{-1} with channel swap on wrapped sources, public monomial
 * rotations for sub_a) and late binding L_F(U) = F*U_id + tau_{-1}(F)*U_tau
 * is public bounded integer polynomial multiplication followed by the
 * MANDATORY rerandomization key switch (D3: binding amplifies the noise
 * parameter by sqrt(2)*||Delta*F||_2 and is not decodable without it).
 */
#ifndef SAB_OPERATOR_H
#define SAB_OPERATOR_H

#include <stdint.h>
#include <stdbool.h>
#include "mosfhet.h"
#include "sab.h"

#define SAB_OPERATOR_GAMMA 2 /* |Gamma| = {identity, tau_minus_one}, D2 evidence */

typedef struct _SAB_Operator_Key
{
  int in_N;      /* accumulator ring dimension */
  int h;         /* input secret Hamming weight */
  int r_prec;    /* position-difference decomposition length */
  /* Embedded scalar SAB machinery: the scalar TRGSW selector samples
   * (security map: existing scalar TRGSW samples), the X -> -X^{-1}
   * automorphism key switch used by the scalar NCMUX (gen = 2N-1, which is
   * exactly -tau_{-1} in the negacyclic ring), and the shared tmp pool. */
  SAB_Key sab;
  /* Rerandomization key switch applied after late binding (mandatory per
   * the D3 noise gate). May be NULL in phase-level equivalence tests. */
  TRLWE_KS_Key rerand_ks;
} * SAB_Operator_Key;

typedef struct _SAB_Operator_State
{
  int in_N;
  /* per-slot operator channels: channel[slot][gamma], gamma in
   * {0: identity, 1: tau_minus_one}; each an ordinary TRLWE sample. */
  TRLWE **channel;
} * SAB_Operator_State;

/* Wrap a fully built scalar SAB key (selector samples, -tau_{-1}
 * automorphism key switch, tmp pool) into the operator key. The scalar key
 * stays owned by the caller. rerand_ks may be NULL for phase-level tests. */
SAB_Operator_Key sab_operator_wrap_scalar (SAB_Key sab,
                                           TRLWE_KS_Key rerand_ks);
void sab_operator_free_key (SAB_Operator_Key key);

SAB_Operator_State sab_operator_new_state (SAB_Operator_Key key);
void sab_operator_free_state (SAB_Operator_State state, SAB_Operator_Key key);

/* U_j = (X^{b_j}, 0): public trivial encoding, no encryption work. */
void sab_operator_setup (SAB_Operator_State state, const uint64_t *b,
                         SAB_Operator_Key key);

/* Channel-wise CMUX with the SCALAR TRGSW selector. */
void sab_operator_cmux (TRLWE out[2], TRLWE in0[2], TRLWE in1[2],
                        TRGSW_DFT selector, SAB_Operator_Key key);

/* Wrapped-source NCMUX: -tau_{-1} acts by swapping the channels, applying
 * the automorphism to each, and negating; then CMUX. */
void sab_operator_ncmux (TRLWE out[2], TRLWE in0[2], TRLWE in1[2],
                         TRGSW_DFT selector, SAB_Operator_Key key);

/* One r_prec monomial butterfly: conditional negacyclic rotation by 2^i
 * per selector bit, non-wrapped slots take CMUX sources, wrapped slots
 * take NCMUX sources. */
void sab_operator_rgsw_monomial_mul (SAB_Operator_State state,
                                     TRGSW_DFT *e, SAB_Operator_Key key);

/* Public monomial rotation X^{-a_j} per slot: coefficient permutation
 * only; no noise, no keys. */
void sab_operator_sub_a (SAB_Operator_State state, const uint64_t *a,
                         SAB_Operator_Key key);

/* Late binding: out_j = F * U_id,j + tau_{-1}(F) * U_tau,j for the public
 * torus LUT polynomial F, followed by the mandatory rerandomization. */
void sab_operator_bind (TRLWE *out, SAB_Operator_State state,
                        TorusPolynomial F, SAB_Operator_Key key);

#endif /* SAB_OPERATOR_H */
