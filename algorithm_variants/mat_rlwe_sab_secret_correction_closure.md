# Secret-Correction Closure Candidate

## Summary

- Parent algorithm: compact/shared-output PVW/MAT-SAB proof route.
- Focused module: closed-state repair after compact CMUX/NCMUX.
- Optimization target: complete-SAB `T_bootstrap/r`.
- Status labels: [theory open], [experiment pending], implementation denied.
- Main hypothesis: secret correction or key switching can restore one shared
  PVW_TMLWE mask without erasing compact kernel savings.

## Mathematical Definition

For lane-local compact output `(a_q, b_q)`, choose one shared mask `a*` and set
`b'_q = b_q + (a* - a_q) * s_q`. The evaluator needs an approved mechanism for
the secret-dependent term.

## Pseudocode

```text
Input: lane-local masks a_q, bodies b_q, correction key material
Output: one shared mask a*, corrected bodies b'_q
1. Select public a* from one lane or a structured rule.
2. For every q with a_q != a*, derive an encrypted/key-switched correction for
   (a* - a_q) * s_q.
3. Add the correction to b_q.
4. Continue SAB only if the noise recurrence and key distribution proof pass.
```

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| Standard PVW_TMLWE state | Lane-local compact output plus correction | changes representation | Stage189/191 |
| Dense selector rows | Compact selector plus correction keys | changes key distribution | Stage190/191 |
| Existing noise recurrence | Correction noise recurrence | new proof obligation | Stage191 |

## Complexity Change

- Time: at least `r-1` corrections per CMUX/NCMUX.
- Memory: compact rows plus correction key rows.
- What must be measured: isolated correction latency, key size, noise, and
  full-SAB `T_bootstrap/r`.

## Theory Dependencies

- T1 structured-key proof or standard-distribution replacement.
- T2 closed-state proof after correction.
- T4 noise recurrence and failure-rate bound.

## Required Experiments

- Isolated correction kernel benchmark against the Stage191 per-correction
  budget.
- Multi-seed noise/failure probe over the full SAB schedule.
- Resource/key-size measurement for the correction key format.

## Paper Contribution Candidate

Only safe wording: secret-correction closure is a proof-only candidate with
recorded lower-bound budgets. It is not an implemented compact SAB speedup.
