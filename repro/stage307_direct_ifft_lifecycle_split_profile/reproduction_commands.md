# Stage307 Reproduction Commands

```bash
FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 \
  bash scripts/run_stage307_direct_ifft_lifecycle_split_profile.sh
python3 scripts/build_stage307_direct_ifft_lifecycle_split_profile.py
```
