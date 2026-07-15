# Stage345 Binary Matrix Synthesis

Decision: `PASS_STAGE345_BINARY_MATRIX_SYNTHESIS_SCOPED_READY`.

The current safe matrix claim is scoped to binary include-zero rows on
`spqlios_avx512`, using complete SAB `T_bootstrap/r` versus repeated scalar SAB.

| case | samples | speedup_mean | speedup_ci95 | noise_trials | noise_pair_failures | evidence_stage |
| --- | --- | --- | --- | --- | --- | --- |
| SET_2_3_2048_r2 | 10 | 1.672200 | 1.651056..1.693344 | 10 | 0 | Stage343 |
| SET_2_3_2048_r4 | 10 | 1.747647 |  | 10 | 0 | Stage331 |
| SET_4_5_2048_r2 | 10 | 1.709700 | 1.673443..1.745957 | 10 | 0 | Stage344 |
| SET_4_5_2048_r4 | 10 | 1.738200 | 1.712133..1.764267 | 10 | 0 | Stage344 |
| SET_2_3_4096_r2 | 10 | 1.612100 | 1.601707..1.622493 | 10 | 0 | Stage344 |
| SET_2_3_4096_r4 | 10 | 1.640600 | 1.578981..1.702219 | 10 | 0 | Stage344 |

Blocked: non-binary support, all-parameter generality, backend generality,
novelty, theoretical optimality, and full resource/key-size dominance.
