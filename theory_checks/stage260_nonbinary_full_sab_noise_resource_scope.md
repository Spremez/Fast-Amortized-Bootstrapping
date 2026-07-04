# Stage260 Non-Binary Full SAB Noise/Resource Scope

Stage260 checks the following invariant under a small FFNT full-path gate:

```text
decode(phase(PVW_lane_q)) == decode(phase(scalar_reference_q))
```

at the final output and at selected intermediate boundaries:

```text
blind_rotate_coeff0, extract, materialize_tlwe, packing_ks, hw_ks
```

The resource model includes one additional non-binary selector family
(`s_coff` or `s_sign`) for both scalar and PVW/MAT keys. It is still a static
estimate, not a measured peak-memory proof on Windows because `/proc` RSS is
not available there.

Open proof obligation: target-parameter `T_bootstrap/r` under a fair backend.
