# Stage343 Reproduction Commands

```sh
STAGE343_PERF_RUNS=9 STAGE343_NOISE_TRIALS=9 FFT_LIB=spqlios_avx512 bash scripts/run_stage343_target_r2_current_head_topup.sh
```

Parse existing logs only:

```powershell
python scripts\build_stage343_target_r2_current_head_topup.py
```
