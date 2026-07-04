# Stage228 Counter-Driven Kernel Search Plan

1. Consume Stage226 counters, Stage227 claim boundary, prior Stage183/184 frontier, and current source.
2. Generate candidate code hypotheses with explicit correctness/performance/failure gates.
3. Deny hot-path edits unless a candidate clears the projected complete-SAB threshold.
4. Select parameter generalization when exact same-format code is not justified.
