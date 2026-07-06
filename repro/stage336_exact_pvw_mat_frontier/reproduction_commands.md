# Stage336 Reproduction Commands

```powershell
wsl -e bash -lc "cd /mnt/d/codexprograms/whFast-Amortized-Bootstrapping/Fast-Amortized-Bootstrapping && STAGE33_OUT_DIR=repro/stage336_current_head_smoke FFT_LIB=ffnt PARAM=SET_2_3 MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=false STAGE33_TERNARY_BUILD=0 bash scripts/run_stage33_current_smoke.sh"
python scripts\build_stage336_exact_pvw_mat_frontier.py
```

The FFNT smoke is a correctness/build guard only. Performance claims remain
anchored to recorded spqlios_avx512 runs.
