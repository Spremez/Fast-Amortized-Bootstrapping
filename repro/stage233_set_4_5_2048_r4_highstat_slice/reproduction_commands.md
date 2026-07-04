# Stage233 Reproduction Commands

Performance/noise high-stat slice:

```bash
STAGE26_PERF_RUNS=10 \
STAGE26_NOISE_SEED_COUNT=20 \
STAGE26_PERF_NOISE_R_VALUES='4' \
STAGE26_PERF_NOISE_PARAMS='SET_4_5_2048' \
STAGE26_PERF_NOISE_OUT_DIR=repro/stage233_set_4_5_2048_r4_runs10_seeds20 \
FFT_LIB=spqlios_avx512 \
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
SAB_PVW_ACTIVE_BUFFER_FUSION=true \
JOBS=2 \
bash scripts/run_stage26_parameter_perf_noise.sh
```

Resource slice:

```bash
STAGE25_RESOURCE_R_VALUES='4' \
STAGE25_RESOURCE_MODES='pvw scalar' \
STAGE25_RESOURCE_OUT_DIR=repro/stage233_set_4_5_2048_r4_resource \
FFT_LIB=spqlios_avx512 \
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
SAB_PVW_ACTIVE_BUFFER_FUSION=true \
KEY=BINARY \
PARAM=SET_4_5_2048 \
JOBS=2 \
bash scripts/run_stage25_resource_matrix.sh
```

Aggregation:

```bash
python scripts/build_stage233_highstat_slice.py
```
