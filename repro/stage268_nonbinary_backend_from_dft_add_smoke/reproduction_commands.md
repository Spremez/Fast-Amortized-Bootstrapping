# Stage268 Reproduction Commands

Run on WSL2/Linux or native Linux with AVX512 exposed:

```bash
bash scripts/run_stage268_nonbinary_backend_from_dft_add_smoke.sh
python3 scripts/build_stage268_nonbinary_backend_from_dft_add_smoke.py
```

Stage268 is single-run smoke only. It must not be cited as final performance
evidence without a later repeated/noise/resource gate.
