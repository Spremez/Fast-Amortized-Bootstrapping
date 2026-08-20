# Candidate D D3 Security and Noise

## Security object map

All eight registered objects are existing standard objects or public
linear maps; no new assumption is introduced. The late binder is
`public_bounded_integer_polynomial_multiplication`. The vector-of-outputs object carries the design's
reserved rerandomization hook, which the noise analysis below shows
is mandatory, not optional.

## Noise recurrence

FAB-2025/686 Lemma 4.1 shows the scalar sparse schedule keeps the
accumulator subgaussian with parameter E_out and that plaintext
monomial multiplications do not grow noise (unit monomial norm).
The operator channels undergo the identical schedule, so each
channel inherits the same subgaussian parameter E_out with
independent errors; Sigma_U is diagonal with lambda_max = g * E^2.

## Why direct late binding fails, and the mandatory rerandomization

Late binding computes L_F(U) = F * U_id + tau(F) * U_tau. Multiplying
a ciphertext by the public LUT polynomial F scales the subgaussian
parameter by ||Delta*F||_2, and the two-channel sum contributes a
sqrt(2) factor. For arbitrary 2-bit LUTs at N = 2048 the worst case
is beta^2 = 2 * N * (1/2)^2 = N/2, i.e. beta = 32. Gaussian tail
exponents divide by beta^2: the scalar 2^-120 bound would degrade
to 2^(-120/1024) ~ 2^-0.12, far above the 2^-64 target. Late binding
therefore requires the post-binding rerandomization key switch
registered in the security map, flooded at sigma = 2^-8, after which
the output bound is a Gaussian tail at t = 16:
2^-184 <= 2^-120 (scalar, B1) <= 2^-64 (target).

## Emitted bounds

| case | value | limit |
|---|---|---|
| external_product_lemma | ANCHORED | REQUIRED |
| covariance_lambda_max | 0.000046962729195604 | 0.000088055117241758 |
| deterministic_l1 | 0.071251397013 | 0.088388347648 |
| deterministic_linf | 0.050382345997 | 0.062500000000 |
| decode_margin | 0.062500000000 | 0.003906250000 |
| union_failure_bound | 2.5722093726424038114378018288389933111408193132173E-56 | 7.5231638452626400509999138382223723380394595633414E-37 |
| scalar_failure_bound | 7.5231638452626400509999138382223723380394595633414E-37 | 5.42101086242752217003726400434970855712890625E-20 |
| b1_failure_bound | 7.5231638452626400509999138382223723380394595633414E-37 | 5.42101086242752217003726400434970855712890625E-20 |
| target_failure_bound | 5.42101086242752217003726400434970855712890625E-20 | 5.42101086242752217003726400434970855712890625E-20 |

## Deterministic bounds and decode margin

Linf (12.9-sigma quantile at the 2^-8 flood) and the sqrt(2) two-
channel L1 variant both stay below the 1/16 decoding threshold;
the margin row records threshold >= sigma_flood with a 16x factor.

## Scope

This analysis is at the parameter level of the primary
SET_2_3_2048 row and inherits the 2025/686 subgaussian framing;
it does not authorize any encrypted implementation (D4 owns that).
