# Stage161 Post-Fusion Attribution Model

Date: 2026-07-03

Stage160 shows the fused MAT EP/decompose block is the largest component. Stage161 tests what can be concluded about that block from the current platform.

Proxy evidence can verify that the compiled path uses AVX512/FMA-family instructions. It cannot prove the kernel is theoretically optimal, FMA-bound, memory-bound, or spill-bound. Those require native hardware counters for the current r=6 post-fusion build.
