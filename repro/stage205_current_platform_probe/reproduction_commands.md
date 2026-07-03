# Stage205 Reproduction Commands

```powershell
wsl --cd /mnt/d/codexprograms/whFast-Amortized-Bootstrapping/Fast-Amortized-Bootstrapping bash -lc 'STAGE28_PERF_GATE_OUT_DIR=repro/stage205_current_platform_probe/stage28_perf_smoke bash scripts/run_stage28_native_perf_counter_gate.sh'
wsl --cd /mnt/d/codexprograms/whFast-Amortized-Bootstrapping/Fast-Amortized-Bootstrapping bash -lc 'STAGE98_OUT_DIR=repro/stage205_current_platform_probe/stage98_current_smoke FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage98_current_smoke_refresh.sh'
wsl --cd /mnt/d/codexprograms/whFast-Amortized-Bootstrapping/Fast-Amortized-Bootstrapping bash -lc 'STAGE20_ACTIVE_BENCH_RUNS=3 SAB_PVW_BENCH_R=2 SAB_PVW_BENCH_REPS=1 STAGE20_ACTIVE_BENCH_OUT_DIR=repro/stage205_current_platform_probe/full_sab_ab_r2_runs3_sequential FFT_LIB=spqlios_avx512 bash scripts/run_stage20_active_buffer_bench.sh'
wsl --cd /mnt/d/codexprograms/whFast-Amortized-Bootstrapping/Fast-Amortized-Bootstrapping bash -lc 'STAGE20_ACTIVE_BENCH_RUNS=3 SAB_PVW_BENCH_R=4 SAB_PVW_BENCH_REPS=1 STAGE20_ACTIVE_BENCH_OUT_DIR=repro/stage205_current_platform_probe/full_sab_ab_r4_runs3_sequential FFT_LIB=spqlios_avx512 bash scripts/run_stage20_active_buffer_bench.sh'
python scripts\build_stage205_current_platform_probe.py
```
