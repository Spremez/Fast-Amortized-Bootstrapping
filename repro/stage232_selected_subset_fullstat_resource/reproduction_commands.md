# Stage232 Reproduction Commands

Performance/noise preflight:

```bash
STAGE26_PERF_RUNS=3 \
STAGE26_NOISE_SEED_COUNT=3 \
STAGE26_PERF_NOISE_R_VALUES='4' \
STAGE26_PERF_NOISE_PARAMS='SET_2_3_4096' \
STAGE26_PERF_NOISE_OUT_DIR=repro/stage232_selected_subset_set_2_3_4096_r4_runs3_seeds3 \
FFT_LIB=spqlios_avx512 \
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
SAB_PVW_ACTIVE_BUFFER_FUSION=true \
JOBS=2 \
bash scripts/run_stage26_parameter_perf_noise.sh
```

Resource preflight:

```bash
STAGE25_RESOURCE_R_VALUES='4' \
STAGE25_RESOURCE_MODES='pvw scalar' \
STAGE25_RESOURCE_OUT_DIR=repro/stage232_selected_subset_set_2_3_4096_r4_resource \
FFT_LIB=spqlios_avx512 \
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
SAB_PVW_ACTIVE_BUFFER_FUSION=true \
KEY=BINARY \
PARAM=SET_2_3_4096 \
JOBS=2 \
bash scripts/run_stage25_resource_matrix.sh
```

Aggregation:

```bash
python scripts/build_stage232_selected_subset_fullstat_resource.py
```
