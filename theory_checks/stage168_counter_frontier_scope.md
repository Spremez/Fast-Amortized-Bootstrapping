# Stage168 Counter Frontier Scope

Native counters help explain a concrete implementation on a concrete CPU. They
do not establish an algorithmic lower bound for PVW/MAT-SAB. In this project,
the lower-bound and algorithmic issues remain separate:

- the current exact dense MAT route needs `(1+r)^2` generic selector terms per
  gadget level;
- same-format materialization-count reduction is closed under the current API;
- generic compact shared-output exactness is blocked by missing cross terms;
- structured compact keygen remains a different algorithmic object, not an
  implementation detail.

Therefore Stage168 uses counters to route experiments, not to certify
optimality.
