# Stage229 Parameter Generalization Plan

## Objective

Record what the current exact PVW/MAT-SAB route can and cannot claim across
parameters before any further optimization or manuscript wording.

## Loop Controls

1. Evidence first: consume only registered logs or rerun commands.
2. Metric lock: every performance row uses complete-SAB `T_bootstrap/r`.
3. Claim split: current-head evidence, historical high-stat evidence, and
   unsupported branches are separate rows.
4. Stop rule: a missing parameter/branch gate creates a future stage, not a
   theoretical assertion.
5. Next action: source-verified literature audit is selected before novelty
   wording; implementation work needs an explicit design/preflight route.

## Execution

Run:

```powershell
python scripts\build_stage229_parameter_generalization_matrix.py
```
