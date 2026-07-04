# Stage312 Experiment Plan

1. Build direct baseline and narrow32 variants with the same backend and SAB flags.
2. Run five complete SAB target benchmark samples per variant.
3. Use `T_bootstrap/r` as the primary endpoint.
4. Require correctness and mean speedup >= 1.01 before opening noise/resource.
5. Do not claim final acceleration until noise/resource/high-stat pass.
