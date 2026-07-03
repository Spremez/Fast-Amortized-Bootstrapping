# Stage169 Native Repeated Stats Scope

Stage169 measures complete bootstrapping throughput on the native target. It
does not isolate MAT EP, from_DFT, or keygen cost; those require split counters
or microbenchmarks. It also does not prove theoretical optimality.

The output is appropriate for engineering throughput claims under the recorded
backend/parameter/platform, provided the confidence interval and minimum sample
do not contradict the claim.
