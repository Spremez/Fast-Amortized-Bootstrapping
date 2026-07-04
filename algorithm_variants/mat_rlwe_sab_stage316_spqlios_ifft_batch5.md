# Stage316 Candidate: Isolated AVX512 `ifft_batch5`

Status: `PASS_STAGE316_BACKEND_IFFT_ABI_PREFLIGHT_SELECT_ASM_BATCH5_SKETCH`.

The admitted candidate is an isolated backend symbol for the rows=5 direct
sub-DTF case.  It should share trig-table loads and loop schedule across five
independent rows while producing exactly the same output as five single-row
`ifft` calls.

Non-goals:

- no SAB integration in Stage317;
- no C-wrapper-only implementation;
- no scalar default change;
- no final bootstrapping speed claim before complete SAB `T_bootstrap/r` A/B.
