# Stage309 Digit Rowbatch Model

For k=1, l=1, r=4, direct sub-DTF materializes five gadget rows: the shared
mask row and four body rows. The baseline direct path processes one row at a
time as digit-to-double followed by `ifft`.

The Stage309 candidate computes the five digit rows inside one coefficient
block loop, hoisting common gadget constants and reducing loop/control overhead.
It then calls the same single-row SPQLIOS `ifft` for each row. This does not
change the external-product algebra, selector layout, or scalar SAB path.

The candidate is promoted only if digit_us and sub-DTF microbench latency both
improve; otherwise it remains a negative/neutral ablation.
