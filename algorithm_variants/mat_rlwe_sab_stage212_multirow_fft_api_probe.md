# Stage212 Multirow FFT API Probe Variant

Decision: `PASS_STAGE212_MULTIROW_WRAPPER_PROMOTE_STAGE213`.

This is a standalone backend API probe. It defines no production SAB variant.

Tested shapes:

- `current_execute_loop`: current row loop over `execute_reverse_torus64`.
- `multirow_interleaved_scratch`: explicit per-row scratch, convert/ifft/copy
  for each row.
- `multirow_two_phase_scratch`: convert all rows, run ifft for all rows, then
  copy all rows.

Only a promoted result may enter a later flag-only SAB preflight.
