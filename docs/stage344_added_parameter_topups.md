# Stage344 Added-Parameter Current-Head Top-Ups

Decision: `PASS_STAGE344_ADDED_PARAMETER_CURRENT_HEAD_MATRIX`.

This stage covers only the binary added-parameter rows:
`SET_4_5_2048` and `SET_2_3_4096`, with r=2 and r=4. It does not claim
non-binary support, all-parameter generality, novelty, or theoretical
optimality.

| case | samples | speedup_mean | speedup_ci95 | noise_trials | noise_pair_failures | status |
| --- | --- | --- | --- | --- | --- | --- |
| SET_4_5_2048_r2 | 10 | 1.709700 | 1.673443..1.745957 | 10 | 0 | PASS_CASE |
| SET_4_5_2048_r4 | 10 | 1.738200 | 1.712133..1.764267 | 10 | 0 | PASS_CASE |
| SET_2_3_4096_r2 | 10 | 1.612100 | 1.601707..1.622493 | 10 | 0 | PASS_CASE |
| SET_2_3_4096_r4 | 10 | 1.640600 | 1.578981..1.702219 | 10 | 0 | PASS_CASE |
