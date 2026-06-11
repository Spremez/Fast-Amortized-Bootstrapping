# Stage 6 PVW Correctness and Noise Log

Date: 2026-06-11

## Objective

Add an initial target-shape correctness/noise gate for the full-output
`sab_pvw_bootstrap_binary(...)` path.

This gate checks the final TRLWE output against an explicit LUT expectation,
not only against repeated scalar SAB. It also reports torus-domain RMS noise
for:

- PVW output versus expected LUT output;
- repeated scalar output versus expected LUT output;
- PVW output versus repeated scalar output.

This is still an engineering gate. It is not a paper-grade failure-rate
experiment because the current recorded campaign is small. A deterministic test
RNG is now available, but the larger multi-seed campaign still needs to be run.

## Code Artifacts

- `SAB_PVW_NOISE_TEST=true`
- `SAB_PVW_NOISE_R`
- `SAB_PVW_NOISE_TRIALS`
- `SAB_PVW_NOISE_MAX_LOG2_GAP`
- `MOSFHET_DETERMINISTIC_RNG`
- `MOSFHET_TEST_RNG_SEED`

The gate uses target-shape binary parameters:

- `r = 2`
- `in_N = 2048`
- `out_N = 2048`
- `h = 39`
- `r_prec = 7`
- message precision `3`
- PVW output key: ternary sparse, `h = 512`, sigma `2^-50`
- scalar packing key: ternary sparse, `h = 256`, sigma `2^-44`
- packing KS: `ell = 2`, `base_bit = 14`
- HW-reducing KS: `ell = 12`, `base_bit = 1`

Each lane uses a valid LUT packed through the existing scalar
`sab_LUT_packing(...)` helper, then copies the packed body into the matching
PVW TV lane. This avoids treating arbitrary TV polynomials as LUTs.

## WSL/Linux `spqlios` Target Run

Command:

```bash
make clean
make FFT_LIB=spqlios SAB_PVW_NOISE_TEST=true SAB_PVW_NOISE_R=2 \
  SAB_PVW_NOISE_TRIALS=3 KEY=BINARY PARAM=SET_2_3_2048 -j$(nproc)
stdbuf -o0 ./main
```

Result:

```text
SAB_PVW_NOISE trial target_full r=2 trial=0 complete
SAB_PVW_NOISE trial target_full r=2 trial=1 complete
SAB_PVW_NOISE trial target_full r=2 trial=2 complete
SAB_PVW_NOISE lane target_full r=2 lane=0 trials=3 pvw_failures=0 scalar_failures=0 pair_failures=0 pvw_log2_sigma_torus=-8.465 scalar_log2_sigma_torus=-8.259 pair_log2_sigma_torus=-7.887
SAB_PVW_NOISE lane target_full r=2 lane=1 trials=3 pvw_failures=0 scalar_failures=0 pair_failures=0 pvw_log2_sigma_torus=-8.472 scalar_log2_sigma_torus=-8.077 pair_log2_sigma_torus=-7.777
SAB_PVW_NOISE summary target_full r=2 trials=3 points=12288 pvw_failures=0 scalar_failures=0 pair_failures=0 pvw_log2_sigma_torus=-8.469 scalar_log2_sigma_torus=-8.162 pair_log2_sigma_torus=-7.830 pvw_minus_scalar_log2=-0.307 max_allowed_log2_gap=4.000
SAB_PVW_NOISE pvw_total count=12288 failures=0 log2_sigma_torus=-8.469 log2_max_abs_torus=-6.587
SAB_PVW_NOISE scalar_total count=12288 failures=0 log2_sigma_torus=-8.162 log2_max_abs_torus=-6.261
SAB_PVW_NOISE pair_total count=12288 failures=0 log2_sigma_torus=-7.830 log2_max_abs_torus=-5.894
SAB_PVW_NOISE target full bootstrap gate: Pass
```

Interpretation:

- PVW final-output correctness: `0 / 12288` quantized failures.
- Scalar final-output correctness: `0 / 12288` quantized failures.
- PVW-vs-scalar final-output equivalence: `0 / 12288` quantized failures.
- PVW aggregate noise was not worse than scalar in this run:
  `pvw_minus_scalar_log2 = -0.307`.
- The loose engineering threshold `SAB_PVW_NOISE_MAX_LOG2_GAP=4.0` passed.

## Windows FFNT Smoke

The same target-shape gate was also run as a portability/correctness smoke
with FFNT and `ARCH_FLAGS=` because this Windows GCC setup generates invalid
SEH/XMM assembly under the default `-march=native`.

Command:

```powershell
make clean
make FFT_LIB=ffnt ARCH_FLAGS= SAB_PVW_NOISE_TEST=true SAB_PVW_NOISE_R=2 `
  SAB_PVW_NOISE_TRIALS=1 KEY=BINARY PARAM=SET_2_3_2048 -j4
.\main
```

Result:

```text
SAB_PVW_NOISE trial target_full r=2 trial=0 complete
SAB_PVW_NOISE lane target_full r=2 lane=0 trials=1 pvw_failures=0 scalar_failures=0 pair_failures=0 pvw_log2_sigma_torus=-6.570 scalar_log2_sigma_torus=-7.648 pair_log2_sigma_torus=-6.078
SAB_PVW_NOISE lane target_full r=2 lane=1 trials=1 pvw_failures=0 scalar_failures=0 pair_failures=0 pvw_log2_sigma_torus=-6.570 scalar_log2_sigma_torus=-6.085 pair_log2_sigma_torus=-5.329
SAB_PVW_NOISE summary target_full r=2 trials=1 points=4096 pvw_failures=0 scalar_failures=0 pair_failures=0 pvw_log2_sigma_torus=-6.570 scalar_log2_sigma_torus=-6.507 pair_log2_sigma_torus=-5.611 pvw_minus_scalar_log2=-0.063 max_allowed_log2_gap=4.000
SAB_PVW_NOISE pvw_total count=4096 failures=0 log2_sigma_torus=-6.570 log2_max_abs_torus=-5.317
SAB_PVW_NOISE scalar_total count=4096 failures=0 log2_sigma_torus=-6.507 log2_max_abs_torus=-4.905
SAB_PVW_NOISE pair_total count=4096 failures=0 log2_sigma_torus=-5.611 log2_max_abs_torus=-4.303
SAB_PVW_NOISE target full bootstrap gate: Pass
```

FFNT remains a correctness/portability smoke only.

## Deterministic Seed Smoke

`MOSFHET_DETERMINISTIC_RNG=true` replaces the normal entropy source with a
test-only SplitMix64 stream seeded by `MOSFHET_TEST_RNG_SEED`. The option is
off by default and is intended only for reproducible correctness/noise runs.

Command:

```bash
make clean
make FFT_LIB=spqlios MOSFHET_DETERMINISTIC_RNG=true \
  MOSFHET_TEST_RNG_SEED=6862025 SAB_PVW_NOISE_TEST=true \
  SAB_PVW_NOISE_R=2 SAB_PVW_NOISE_TRIALS=1 \
  KEY=BINARY PARAM=SET_2_3_2048 -j$(nproc)
stdbuf -o0 ./main > /tmp/sab_seed_6862025_run1.log
stdbuf -o0 ./main > /tmp/sab_seed_6862025_run2.log
diff -u /tmp/sab_seed_6862025_run1.log /tmp/sab_seed_6862025_run2.log
cat /tmp/sab_seed_6862025_run1.log
```

The `diff` command produced no output, so the two process-level reruns were
byte-for-byte identical.

Result:

```text
SAB_PVW_NOISE trial target_full r=2 trial=0 complete
SAB_PVW_NOISE lane target_full r=2 lane=0 trials=1 pvw_failures=0 scalar_failures=0 pair_failures=0 pvw_log2_sigma_torus=-7.721 scalar_log2_sigma_torus=-8.457 pair_log2_sigma_torus=-7.478
SAB_PVW_NOISE lane target_full r=2 lane=1 trials=1 pvw_failures=0 scalar_failures=0 pair_failures=0 pvw_log2_sigma_torus=-7.721 scalar_log2_sigma_torus=-8.220 pair_log2_sigma_torus=-7.174
SAB_PVW_NOISE summary target_full r=2 trials=1 points=4096 pvw_failures=0 scalar_failures=0 pair_failures=0 pvw_log2_sigma_torus=-7.721 scalar_log2_sigma_torus=-8.328 pair_log2_sigma_torus=-7.311 pvw_minus_scalar_log2=0.608 max_allowed_log2_gap=4.000
SAB_PVW_NOISE pvw_total count=4096 failures=0 log2_sigma_torus=-7.721 log2_max_abs_torus=-6.041
SAB_PVW_NOISE scalar_total count=4096 failures=0 log2_sigma_torus=-8.328 log2_max_abs_torus=-6.491
SAB_PVW_NOISE pair_total count=4096 failures=0 log2_sigma_torus=-7.311 log2_max_abs_torus=-5.648
SAB_PVW_NOISE target full bootstrap gate: Pass
```

Interpretation:

- The deterministic seed path is reproducible across process restarts for the
  same binary and command line.
- This is a seed-mechanism check, not a statistical campaign. It covers one
  seed and one target-shape trial.
- In this seed, PVW final-output noise is higher than scalar by
  `0.608` log2 units, but still within the current engineering threshold and
  with no quantized failures.

## Scalar Baseline After Stage 6 Gate

Command:

```bash
make clean
make FFT_LIB=spqlios KEY=BINARY PARAM=SET_2_3 -j$(nproc)
./main
```

Result:

```text
Sparse bootstrapping with binary keys
Message precision: 3 - Repetitions: 3
Max monomial distance (log B): 7
Rejection Sampling Attempts: 344
Bootstrapping time: 12,665,925 us +- 550,777.619969
Pass
```

After adding the deterministic RNG switch, the default scalar path was checked
again without the deterministic flag:

```text
Sparse bootstrapping with binary keys
Message precision: 3 - Repetitions: 3
Max monomial distance (log B): 7
Rejection Sampling Attempts: 110
Bootstrapping time: 12,429,735 us +- 769,196.335812
Pass
```

The default scalar build still does not link `sab_pvw.o`.

## Failed/Non-Claim Runs

These are platform/toolchain observations, not algorithm failures:

- Windows `FFT_LIB=spqlios` still fails while assembling the SPQLIOS FMA
  assembly and AES RNG object. This matches the prior decision that Windows is
  not the performance platform.
- Windows `FFT_LIB=ffnt` with default `ARCH_FLAGS=-march=native` failed in
  `ffnt.o` due invalid `.seh_savexmm` assembly. Re-running with `ARCH_FLAGS=`
  fixed the portable smoke.

## Remaining Work

- Run a larger correctness/noise campaign with recorded deterministic seeds,
  starting with at least 50 seeds for engineering signal.
- Repeat Stage 6 for `r=4` after confirming memory and runtime are acceptable.
- Add stage-level noise probes before/after blind rotation, extract, packing
  KS, and HW KS if a final paper claim needs more than final-output noise.
