# Stage191 Plan

Goal: evaluate whether secret correction/key-switch closure can pass the T4
noise/resource precondition before any compact SAB implementation.

Rules:

- no `sab_pvw_*` hot-path changes;
- use Stage138 compact-kernel savings as the available latency budget;
- use Stage124 selector row counts as the public resource budget;
- report normalized noise sensitivity only, not a measured noise proof;
- deny implementation unless latency, resource, and noise gates all pass.
