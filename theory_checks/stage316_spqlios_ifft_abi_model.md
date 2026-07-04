# Stage316 SPQLIOS IFFT ABI Model

Stage316 checks whether the Stage315 backend-IFFT route has a real code-level
entry point.  The current SPQLIOS ABI exposes only `ifft(tables, data)`, and
the AVX512 assembly accepts one row pointer.  The C array wrapper still calls
single-row transforms; Stage310 already rejected wrapper-only batching.

For r=4 and k=1, the direct sub-DTF path has rows=k+r=5.  The only admitted
implementation direction is therefore a new isolated AVX512 symbol:

```c
void ifft_batch5(const void *tables,
    double *row0, double *row1, double *row2, double *row3, double *row4);
```

It must be validated outside SAB against five calls to the existing `ifft`.
No SAB integration is allowed until the isolated benchmark shows at least
0.107769 IFFT component reduction, the threshold inherited from
Stage315 for a projected 1.02 body-level budget.
