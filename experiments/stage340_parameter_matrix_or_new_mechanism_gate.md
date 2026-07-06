# Stage340 Parameter Matrix Or New Mechanism Gate

Stage340 must choose one route.

## Route A: Current-Head Parameter Matrix

Use this when broader experimental wording is needed.

- rerun complete SAB `T_bootstrap/r` A/B for r=2 and r=4;
- include SET_2_3_2048 and any added binary parameter claimed in the paper;
- record correctness, noise, RSS, key size, keygen time, backend, CPU flags,
  raw logs, and commit;
- mark any unsupported branch explicitly.

## Route B: Verified Related Work

Use this before novelty wording.

- verify real sources and exact claim support;
- cite only what has been source-checked;
- keep broad shared-mask/common-mask novelty blocked unless the literature
  matrix supports a narrower claim.

## Route C: New Mechanism Or Formal Proof

Use this only with a concrete mechanism or proof object.

- mechanism route starts with count/load/store model and isolated gates;
- compact route starts with closed-state/keygen/security/noise proof;
- full SAB hot-path work starts only after those gates pass.
