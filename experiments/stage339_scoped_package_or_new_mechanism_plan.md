# Stage339 Scoped Package Or New Mechanism Plan

Stage339 has two valid entry modes.

## Mode A: Scoped Package Refresh

Use this mode when no new mechanism or formal proof is available.

- update the paper claim matrix;
- bind every timing claim to commit, backend, CPU, parameter set, and raw log;
- include negative ablations from the closed-candidate audit;
- mark theoretical optimality, universal speedup, and compact SAB as not proven.

Gate: the package must not use stronger wording than the evidence supports.

## Mode B: New Mechanism Protocol

Use this mode only after a concrete mechanism is identified.

- write a count/load/store model before code;
- implement an isolated checker or microbench first;
- require equivalence before speed claims;
- run full SAB T_bootstrap/r A/B only after the isolated gate passes.

Gate: failure at isolated equivalence or isolated performance rejects the route
without SAB hot-path integration.
