# Stage282 Reproduction Commands

```bash
bash scripts/run_stage282_cmux_residual_noise_resource.sh
python3 scripts/build_stage282_cmux_residual_noise_resource.py
```

This is a small full-path include-zero noise/resource gate using `ffnt` as a
correctness/resource proxy; it is not target-parameter AVX512 performance
evidence.
