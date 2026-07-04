# Stage264 Reproduction Commands

Current local route, from repository root:

```powershell
New-Item -ItemType Directory -Force repro/stage264_mat_avx512_counter_preflight/raw
# In WSL/Linux from the same repository:
nm -C build/mattrgsw.o > repro/stage264_mat_avx512_counter_preflight/raw/mattrgsw_nm.log 2>&1
objdump -d -M intel build/mattrgsw.o > repro/stage264_mat_avx512_counter_preflight/raw/mattrgsw_objdump.log 2>&1
perf stat -e cycles,instructions,cache-references,cache-misses,branches,branch-misses -- true > repro/stage264_mat_avx512_counter_preflight/raw/perf_probe.log 2>&1
python3 scripts/build_stage264_mat_avx512_counter_preflight.py
```

If `perf` is unavailable, keep the result as proxy-only. Do not use this stage
to upgrade MAT-AVX512 theoretical-optimality wording.
