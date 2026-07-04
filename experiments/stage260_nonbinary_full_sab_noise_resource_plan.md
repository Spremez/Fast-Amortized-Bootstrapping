# Stage260 Experiment Plan

Primary endpoint:

```text
zero final PVW/scalar/pair failures for include-zero and ternary r=1/2/4
```

Secondary endpoints:

```text
zero stage-pair failures and recorded non-binary key resource estimates
```

Executed commands:

```powershell
make clean
make FFT_LIB=ffnt SAB_PVW_NONBINARY_FULL_NOISE_TEST=true SAB_PVW_NONBINARY_FULL_NOISE_TRIALS=3 KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
.\main
make clean
make FFT_LIB=ffnt KEY=BINARY PARAM=SET_2_3_2048 ARCH_FLAGS=
python scripts\build_stage260_nonbinary_full_sab_noise_resource.py
```

Evidence:

- `repro/stage260_nonbinary_full_sab_noise_resource/final_noise_summary.csv`
- `repro/stage260_nonbinary_full_sab_noise_resource/stage_noise_summary.csv`
- `repro/stage260_nonbinary_full_sab_noise_resource/resource_summary.csv`
- `repro/stage260_nonbinary_full_sab_noise_resource/proof_gate.csv`
