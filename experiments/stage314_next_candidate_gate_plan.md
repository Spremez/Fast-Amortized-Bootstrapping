# Stage314 Gate Plan

1. Merge Stage309 rowbatch, Stage311 narrow32 microbench, Stage312 full SAB,
   and Stage313 profile attribution.
2. Compute component shares and Amdahl-style projected speedups.
3. Require projected full-SAB budget >=1.02 before implementing another local
   microvariant.
4. Route next work to backend IFFT or schedule-level algorithm candidates.
