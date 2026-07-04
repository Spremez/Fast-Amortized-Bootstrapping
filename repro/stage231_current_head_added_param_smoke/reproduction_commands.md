# Stage231 Reproduction Commands

```powershell
bash -lc "STAGE26_PERF_RUNS=1 STAGE26_NOISE_SEED_COUNT=1 STAGE26_PERF_NOISE_R_VALUES='2 4' STAGE26_PERF_NOISE_PARAMS='SET_4_5_2048 SET_2_3_4096' STAGE26_PERF_NOISE_OUT_DIR=repro/stage231_current_head_added_param_smoke FFT_LIB=spqlios_avx512 MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true SAB_PVW_ACTIVE_BUFFER_FUSION=true JOBS=2 bash scripts/run_stage26_parameter_perf_noise.sh"
python scripts\build_stage231_current_head_added_param_refresh.py
```
