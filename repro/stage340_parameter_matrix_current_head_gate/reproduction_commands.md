# Stage340 Reproduction Commands

Dry-run gate:

```powershell
bash scripts/run_stage340_parameter_matrix_current_head.sh
```

Execute on WSL/Linux performance platform:

```sh
STAGE340_EXECUTE=1 STAGE340_PERF_RUNS=10 STAGE340_NOISE_TRIALS=10 FFT_LIB=spqlios_avx512 bash scripts/run_stage340_parameter_matrix_current_head.sh
```

Parse existing logs only:

```powershell
python scripts\build_stage340_parameter_matrix_execution_gate.py
```
