# Stage318 Intrinsics Gap

Stage317 predicted a possible IFFT component reduction of about 0.120000 in
the trig-loading regions, with a required measured component reduction of
0.107769.  Stage318 shows that simply expressing the tile3+tile2
schedule in C intrinsics is insufficient.

Observed repeated-run mean speedup is 0.657067, with mean
reduction -0.535009.  The gap is not mathematical: the output
is bit-identical.  The gap is implementation-level scheduling.  The generated
function has 492 objdump lines, 37
stack-frame references, and 0 references to
zmm16-zmm31.

Conclusion: for this backend direction, the next admissible optimization is
hand-written assembly that explicitly controls register allocation and loop
shape, or the backend IFFT direction should be closed as not worth further
complexity.
