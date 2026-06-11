# Stage 9 Statistical Evidence Check

Date: 2026-06-12

## Objective

Interpret the clear-elision deterministic seed sweeps without overstating the
failure-rate evidence.

Machine-readable table:

- `repro/stage9_failure_rate_summary.csv`

Related stage-local smoke evidence:

- `docs/stage9_stage_noise_probe.md`
- `repro/stage9_stage_noise_summary.csv`

## Inputs

| variant | backend | r | seeds | points | PVW/scalar/pair failures | gap range | avg gap |
|---|---|---:|---:|---:|---:|---:|---:|
| clear-elision | spqlios | 2 | 50 | 204,800 | 0 / 0 / 0 | -0.470 to 0.636 | -0.0039 |
| clear-elision | spqlios | 4 | 50 | 409,600 | 0 / 0 / 0 | -0.541 to 0.636 | -0.0313 |

## Zero-Failure Bounds

The table uses a one-sided 95% zero-failure binomial upper bound:

```text
upper = 1 - 0.05^(1/n)
```

| r | unit | n | failures | 95% one-sided upper bound |
|---:|---|---:|---:|---:|
| 2 | output point | 204,800 | 0 | 1.462749e-05 |
| 2 | seed | 50 | 0 | 5.815508e-02 |
| 4 | output point | 409,600 | 0 | 7.313773e-06 |
| 4 | seed | 50 | 0 | 5.815508e-02 |

Interpretation:

- The point-level bounds are useful as an engineering stress summary, but they
  assume output points can be treated as independent Bernoulli observations.
  That assumption is too strong for a paper-level failure-rate claim.
- The seed-level bound is the conservative headline: with 0 failures in 50
  deterministic seeds, the one-sided 95% upper bound is about `5.816%` per seed
  for both `r=2` and `r=4`.
- Therefore the current evidence supports the Stage 8 correctness/noise gate,
  but should still be labeled statistical evidence insufficient for a formal
  failure-rate theorem or paper-grade empirical failure-rate claim.

## Claim Labels

Supported:

```text
[engineering gate passed] clear-elision r=2 and r=4 deterministic 50-seed
target-shape sweeps produced no PVW, scalar, or pair failures.
```

Not supported:

```text
[paper-grade failure-rate proven] the optimized path has a quantified failure
rate below a cryptographic target.
```

Required before a stronger paper claim:

- specify the intended failure-rate target;
- define the statistical unit, preferably independent key/seed trials rather
  than correlated output points from the same run;
- run enough independent trials to make the one-sided upper bound meaningful
  for that target;
- keep stage-level noise probes separate from final-output correctness. The
  current stage-level probe is useful engineering evidence, but its `trials=1`
  smoke configuration does not change the failure-rate bounds above.
