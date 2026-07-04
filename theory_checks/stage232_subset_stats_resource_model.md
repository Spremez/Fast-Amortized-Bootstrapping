# Stage232 Stats/Resource Model

The selected subset tests one falsifiable statement:

```text
For binary SET_2_3_4096, r=4, exact dense PVW/MAT-SAB reduces amortized
complete-SAB time per plaintext lane, T_bootstrap/r, relative to running scalar
SAB r times under the same backend.
```

This is an amortized algorithm-level endpoint, not a raw kernel endpoint. The
measurement includes full SAB setup used by the benchmark path, CMUX/NCMUX,
RGSW monomial flow, extract/post-processing in that path, and correctness gate.

The 3-run t interval in `repro/stage232_selected_subset_fullstat_resource/performance_stats.csv` is a preflight interval. It is useful
for deciding whether the route is still alive at current head, but it is not a
final statistical claim. The 3-seed noise run is also a preflight; the 20-seed
gate remains the minimum for promotion.

Resource interpretation:

- `estimated_key_bytes_ratio_vs_scalar_repeated` compares PVW/MAT public
  bootstrap-key estimate against r scalar repeated keys.
- RSS ratios are process-level measurements from `/usr/bin/time -v` and internal
  VMHWM probes.
- A speedup is not promoted unless resource growth is reported beside it.
