# Stage 25 Correctness, Noise, and Resource Matrix

Date: 2026-06-25

## Scope

Stage 25 validates the current best explicit PVW/MAT-SAB body path:

```text
FFT_LIB=spqlios_avx512
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
SAB_PVW_ACTIVE_BUFFER_FUSION=true
KEY=BINARY
PARAM=SET_2_3_2048
```

This stage does not introduce a new optimization. Its purpose is to check
whether the Stage 20/22 promoted experimental path has enough correctness,
noise, and resource evidence to remain the baseline for later Stage 26 and
Stage 27 work.

The runs below are initial smoke-level evidence. They are valid engineering
gates for continuing the loop, but they are not a paper-grade 50+ seed
correctness/noise campaign.

## Final-Output Noise Smoke

Command:

```sh
STAGE25_FINAL_NOISE_SEED_COUNT=1 \
STAGE25_FINAL_NOISE_R_VALUES='1 2 4' \
STAGE25_FINAL_NOISE_OUT_DIR=repro/stage25_final_noise_avx512_seeds1 \
bash scripts/run_stage25_final_noise_sweep.sh
```

Summary:

| r | seeds | points | PVW failures | scalar failures | pair failures | PVW minus scalar log2 sigma | status |
|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 1 | 2048 | 0 | 0 | 0 | -0.626 | PASS |
| 2 | 1 | 4096 | 0 | 0 | 0 | 0.603 | PASS |
| 4 | 1 | 8192 | 0 | 0 | 0 | -0.555 | PASS |

Interpretation:

- The promoted explicit path matches the scalar reference at final output for
  the tested deterministic seed `6862025`.
- The observed PVW-vs-scalar sigma gaps are within the configured
  `4.0` log2 threshold.
- This supports continued use of the active-buffer plus specialized MAT-AVX512
  path for Stage 26 planning, but it must be expanded before final claims.

## Stage-Level Noise Smoke

Command:

```sh
STAGE25_STAGE_NOISE_R_VALUES='1 2 4' \
STAGE25_STAGE_NOISE_OUT_DIR=repro/stage25_stage_noise_avx512_trials1 \
bash scripts/run_stage25_stage_noise_probe.sh
```

Summary:

| r | stage | points | pair failures | pair log2 sigma | pair log2 max abs |
|---:|---|---:|---:|---:|---:|
| 1 | blind_rotate_coeff0 | 2048 | 0 | -14.576 | -12.827 |
| 1 | extract | 2048 | 0 | -14.576 | -12.827 |
| 1 | materialize_tlwe | 2048 | 0 | -14.576 | -12.827 |
| 1 | packing_ks | 2048 | 0 | -14.576 | -12.840 |
| 1 | hw_ks | 2048 | 0 | -8.111 | -6.113 |
| 2 | blind_rotate_coeff0 | 4096 | 0 | -14.861 | -12.748 |
| 2 | extract | 4096 | 0 | -14.861 | -12.748 |
| 2 | materialize_tlwe | 4096 | 0 | -14.861 | -12.748 |
| 2 | packing_ks | 4096 | 0 | -14.859 | -12.747 |
| 2 | hw_ks | 4096 | 0 | -8.048 | -5.954 |
| 4 | blind_rotate_coeff0 | 8192 | 0 | -14.778 | -12.482 |
| 4 | extract | 8192 | 0 | -14.778 | -12.482 |
| 4 | materialize_tlwe | 8192 | 0 | -14.778 | -12.482 |
| 4 | packing_ks | 8192 | 0 | -14.777 | -12.515 |
| 4 | hw_ks | 8192 | 0 | -8.056 | -5.945 |

Interpretation:

- Pairwise stage equivalence held for every probed stage and every tested
  `r` value.
- The larger `hw_ks` pair sigma is expected because it probes the final
  post-HW-key-switch boundary rather than the PVW body only.
- No stage-level evidence currently points to a correctness or noise blocker.

## Resource Matrix

Command:

```sh
STAGE25_RESOURCE_R_VALUES='1 2 4' \
STAGE25_RESOURCE_OUT_DIR=repro/stage25_resource_avx512 \
bash scripts/run_stage25_resource_matrix.sh
```

Summary:

| r | mode | keygen us | lane avg keygen us | estimated public key bytes | key bytes ratio vs repeated scalar | internal VMHWM KB | time max RSS KB |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | PVW | 498853 | 498853.000 | 153358112 | 1.000029 | 203228 | 203608 |
| 1 | scalar repeated | 493691 | 493691.000 | 153353608 | 1.000000 | 194912 | 195192 |
| 2 | PVW | 1147482 | 573741.000 | 310883736 | 1.013617 | 382968 | 383240 |
| 2 | scalar repeated | 1008197 | 504098.500 | 306707216 | 1.000000 | 386900 | 387236 |
| 4 | PVW | 2397860 | 599465.000 | 653500424 | 1.065349 | 769068 | 769388 |
| 4 | scalar repeated | 2050095 | 512523.750 | 613414432 | 1.000000 | 771264 | 771672 |

Interpretation:

- PVW public bootstrap key estimates are close to repeated scalar at `r=1`,
  about `1.36%` larger at `r=2`, and about `6.53%` larger at `r=4`.
- PVW keygen is slower per lane in this smoke run. Any throughput claim must
  therefore report keygen cost rather than only online bootstrapping latency.
- Peak resident memory is comparable between PVW and repeated scalar in this
  measurement; PVW is slightly lower at `r=2` and `r=4`, but this is a smoke
  resource observation, not a statistical memory claim.

## Decision

Status:

```text
PASS_SMOKE_CONTINUE
```

The current best explicit path passes the initial Stage 25 correctness,
stage-noise, final-noise, and resource gates for `r in {1,2,4}` on the target
binary parameter set. It remains the comparison baseline for Stage 26.

The claim level is unchanged:

```text
[correctness supported] and [performance smoke/repeated engineering evidence]
for BINARY SET_2_3_2048 under spqlios_avx512, with Stage 25 smoke-level
noise/resource support.
```

It is not yet a final paper-ready claim because:

- performance evidence is inherited from Stage 20 and Stage 22 rather than
  re-run as a consolidated Stage 25 statistical campaign;
- Stage 26 parameter and branch generalization has not started;
- Stage 27 novelty and related-work validation is still pending.

## 50-Seed Final-Output Expansion

Command:

```sh
STAGE25_FINAL_NOISE_SEED_COUNT=50 \
STAGE25_FINAL_NOISE_R_VALUES='2 4' \
STAGE25_FINAL_NOISE_OUT_DIR=repro/stage25_final_noise_avx512_r2_r4_seeds50 \
bash scripts/run_stage25_final_noise_sweep.sh
```

Summary:

| r | seeds | points | PVW failures | scalar failures | pair failures | min PVW minus scalar log2 sigma | max PVW minus scalar log2 sigma | avg PVW minus scalar log2 sigma | status |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 50 | 204800 | 0 | 0 | 0 | -0.446 | 0.619 | -0.007400 | PASS |
| 4 | 50 | 409600 | 0 | 0 | 0 | -0.555 | 0.682 | -0.029200 | PASS |

Interpretation:

- The promoted `r=2` and `r=4` paths now have 50 deterministic seeds each
  with zero PVW, scalar, and pair failures at final output.
- The PVW-vs-scalar sigma gap stays well below the configured `4.0` log2
  threshold in every seed.
- With zero seed-level failures out of 50 seeds per `r`, the simple rule of
  three gives an approximate 95% upper bound near `6%` per-seed failure under
  this test distribution. This is useful engineering evidence, not a formal
  cryptographic failure-rate proof.
- This closes the Stage 25 final-output noise expansion for the current
  promoted target path. Stage-level noise remains smoke-level and Stage 26
  parameter/branch generalization is still required.

## Next Work

Immediate follow-up:

1. Advance Stage 26 with a smaller smoke parameter and any supported
   non-binary branches that the code can build.
2. Re-run a consolidated repeated full SAB A/B package only if Stage 26 keeps
   the current path as the final promoted variant.
3. Keep Stage 27 novelty claims blocked until Stage 26 scope is known and a
   related-work matrix exists.
