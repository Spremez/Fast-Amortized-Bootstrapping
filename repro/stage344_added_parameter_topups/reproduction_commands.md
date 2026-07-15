# Stage344 Reproduction Commands

```sh
STAGE344_PERF_RUNS=10 STAGE344_NOISE_TRIALS=10 FFT_LIB=spqlios_avx512 bash scripts/run_stage344_added_parameter_topups.sh
```

Parse existing logs only:

```powershell
python scripts\build_stage344_added_parameter_topups.py
```
