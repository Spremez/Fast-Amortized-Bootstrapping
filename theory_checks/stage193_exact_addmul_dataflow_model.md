# Stage193 Addmul Dataflow Model

For r=6, k=1, l=1 exact full-MAT addmul has seven input rows and seven output
polynomials. The current tile4 kernel updates four outputs at a time, so it
loads each decomposed DFT row once per output tile.

Candidate: cache the decomposed row registers across output tiles. Static
memory-op model:

```text
selector vector loads = rows * outputs * 2
current dec loads     = rows * tiles * 2
cached dec loads      = rows * 2
output stores         = outputs * 2
```

For r=6 and tile size 4, this removes only 14 vector dec loads per coefficient
out of 140 modeled load/store ops. The optimistic component speedup is
`1.111111`, below the Stage180 addmul component speedup required for a 3%
complete-SAB gain. This is an upper bound because it ignores register spills
from holding 14 dec vectors plus accumulators.
