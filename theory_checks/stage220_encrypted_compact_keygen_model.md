# Stage220 Encrypted Compact Keygen Model

The prototype models each compact selector row as an encryption-like object:

```text
b = a * s_lane + semantic(row) + noise(row)
```

Active rows carry deterministic finite semantic payloads. Dummy rows keep
random-looking public masks and bodies but have semantic payload zero. This is
the first gate that checks the compact route after row-role API skeletoning
with production MOSFHET polynomial and DFT functions.

This remains a deterministic prototype. It does not prove standard security,
parameterized noise recurrence, compact EP integration, or complete-SAB
`T_bootstrap/r`.
