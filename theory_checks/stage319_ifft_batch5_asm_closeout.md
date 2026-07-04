# Stage319 IFFT Batch5 Closeout

Both C/intrinsics and hand-written assembly implementations are correct but
slower than the existing scalar-row SPQLIOS AVX512 IFFT baseline.

The decisive metric is isolated IFFT component reduction.  Stage319 mean
reduction is -0.631581 while the required reduction is
0.107769.  Since the candidate fails before SAB
integration, it cannot improve complete `T_bootstrap/r`.

The backend batch5 IFFT direction is closed.  Further work should return to
SAB schedule, MAT external product, selector layout, or complete pipeline
budget items where full-SAB evidence can justify implementation risk.
