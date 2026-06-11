# Repro Environment

Date: 2026-06-11

Primary performance platform:

- WSL2/Linux, kernel `5.15.167.4-microsoft-standard-WSL2`
- CPU: `11th Gen Intel(R) Core(TM) i7-11700 @ 2.50GHz`
- GCC: `gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`
- Relevant CPU flags include `fma`, `avx2`, and AVX-512 feature flags.

Build policy:

- Use WSL/Linux `FFT_LIB=spqlios` for performance-relevant runs.
- Use `FFT_LIB=ffnt` only for correctness and portability smoke tests.
- Keep scalar `sab_rlwe_bootstrap(...)` as the baseline route.
- Enable PVW/SAB staged tests with `SAB_PVW_KERNEL_TEST=true`.

Current source state:

- Base commit before this stage: `c9a332c`
- This stage adds a working-tree `sab_pvw_*` API skeleton and will be committed
  after verification.
