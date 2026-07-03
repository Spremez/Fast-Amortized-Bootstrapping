# Addmul Dataflow Screen Variant

This variant is a no-code screen.

Rejected or blocked routes:

- r=6 fulltile: already implemented and not promoted.
- r=6 bodymajor: complete-SAB negative.
- row streaming: exact-output microbench negative.
- more coefficient unrolling: no mechanism yet and likely register-pressure
  limited.
- selector transpose or sparse skip: key-format/security/resource gates first.

No new `mattrgsw.c` hot-path code is authorized by this stage.
