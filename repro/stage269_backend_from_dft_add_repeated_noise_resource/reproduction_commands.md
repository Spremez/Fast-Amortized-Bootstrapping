# Stage269 Reproduction Commands

Repeated timing plus noise/resource:

```bash
bash scripts/run_stage269_backend_from_dft_add_repeated_noise_resource.sh
python3 scripts/build_stage269_backend_from_dft_add_repeated_noise_resource.py
```

To split the long run:

```bash
RUN_NOISE_RESOURCE=0 bash scripts/run_stage269_backend_from_dft_add_repeated_noise_resource.sh
RUN_REPEATED=0 bash scripts/run_stage269_backend_from_dft_add_repeated_noise_resource.sh
```
