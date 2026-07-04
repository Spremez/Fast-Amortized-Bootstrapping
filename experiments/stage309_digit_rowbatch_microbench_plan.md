# Stage309 Experiment Plan

1. Build direct baseline and rowbatch-digit variants with direct DFT profile.
2. Run paired MAT_SUB_DFT microbench repetitions.
3. Require correctness for every run.
4. Promote only if digit_us and sub-DTF latency improve in every paired run.
5. If neutral, keep the current direct-DFT implementation unchanged.
