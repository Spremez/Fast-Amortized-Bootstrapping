# Stage325 Reproduction Commands

From WSL/Linux on an AVX512-capable CPU:

```bash
STAGE325_RUNS=7 STAGE325_REPS=20000 bash scripts/run_stage325_selector_transpose_resource_probe.sh
python3 scripts/build_stage325_selector_transpose_resource_probe.py
```

This is an isolated dense-addmul probe. It is not a complete-SAB timing claim.
