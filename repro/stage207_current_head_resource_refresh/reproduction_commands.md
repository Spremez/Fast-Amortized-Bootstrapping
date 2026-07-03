# Stage207 Reproduction Commands

```bash
STAGE25_RESOURCE_R_VALUES='2 4' \
STAGE25_RESOURCE_OUT_DIR=repro/stage207_current_head_resource_refresh \
FFT_LIB=spqlios_avx512 \
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
SAB_PVW_ACTIVE_BUFFER_FUSION=true \
KEY=BINARY PARAM=SET_2_3_2048 \
bash scripts/run_stage25_resource_matrix.sh

python3 scripts/build_stage207_current_head_resource_refresh.py
```
