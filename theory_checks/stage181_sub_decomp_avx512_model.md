# Stage181 AVX512 Sub-Decompose Model

The Stage180 split estimates sub-decompose at full-SAB share
`0.103963271`. A pure sub-decompose improvement must therefore be very
large to move complete SAB. Stage181 also measures the combined current block;
promotion to full-SAB is allowed only if the combined block projection reaches
at least 3% complete-SAB speedup.
