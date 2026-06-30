# Stage101 CB5 Remote Native Perf Log

Date: 2026-06-30

## Purpose

Stage101 resolves CB5 by recording native Linux `perf` hardware-counter
evidence for the complete SAB PVW/MAT path on the remote Xeon platform
authorized by the user. This is evidence for attribution; it is not a
claim that the MAT-AVX512 implementation is theoretically optimal.

## Summary

| gate | status | detail |
|---|---|---|
| stage101_raw_artifacts | PASS | remote raw logs are present |
| stage101_stage28_hardware_counter_gate | PASS | hardware_counter_gate=PASS |
| stage101_complete_sab_correctness | PASS | standard=PASS; attribution=PASS |
| stage101_attribution_events | PASS | load/store/AVX512 FP events supported and recorded |
| stage101_speed_sample | PASS | attribution_speedup_vs_scalar_repeated=1.309x |
| stage101_cb5_decision | PASS_STAGE101_CB5_NATIVE_PERF_COUNTERS_RECORDED | CB5 platform blocker resolved with native perf evidence; theoretical-optimality wording remains review-gated. |

## Key Metrics

| metric | value |
|---|---:|
| standard speedup vs repeated scalar | 1.309x |
| attribution speedup vs repeated scalar | 1.309x |
| attribution loads | 254877142145 |
| attribution stores | 139977326972 |
| attribution 512-bit packed FP ops | 236434492449 |
| attribution cycles | 607952411223 |
| attribution instructions | 1101054109000 |

## Interpretation

The native run confirms that the hardware-counter lane is no longer blocked:
`cycles`, `instructions`, cache events, retired loads/stores, and AVX512
floating-point arithmetic events are available on the target platform.
The complete SAB r=4 correctness gate passed and the measured speedup
remained 1.309x under both the standard Stage28 event set and the wider
attribution event set.

This resolves the external platform blocker for CB5. It does not by itself
justify wording such as theoretical optimality; that wording still requires
a separate model-to-counter interpretation against Stage22 and assembly
evidence.
