# Stage330 Reproduction Commands

```sh
python scripts/build_stage330_highstat_reconciliation.py
```

Inputs:

- `repro/stage296_direct_dft_highstat/perf_summary.csv`
- `repro/stage296_direct_dft_highstat/noise_summary.csv`
- `repro/stage297_direct_dft_resource_sidecondition/linked_resource_summary.csv`
- `repro/stage321_r4_unrolled_fullsab_ab/perf_summary.csv`
- `scripts/run_stage296_direct_dft_highstat.sh`
- `scripts/run_stage321_r4_unrolled_fullsab_ab.sh`

Stage330 is an analysis/reconciliation stage.  It intentionally does not rerun
the heavy complete-SAB benchmark.
