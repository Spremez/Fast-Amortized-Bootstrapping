# Stage312 Digit Narrow32 Full-SAB Model

Stage311 only proved an isolated direct sub-DTF microbench effect. Stage312
checks the complete SAB endpoint `T_bootstrap/r`, comparing the current
direct-DFT baseline against the same path plus
`MAT_TRGSW_DIRECT_DFT_DIGIT_NARROW32=true`.

The algorithmic semantics remain unchanged: the candidate only changes how
signed gadget digits are converted to double when the digit range fits int32.
Promotion requires complete SAB correctness and a positive full-SAB preflight.
Noise/resource and high-stat campaigns remain separate gates.
