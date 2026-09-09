# -*- coding: utf-8 -*-
# Upgrade probe_rinput.c to a 6-trial benchmark + noise reconciliation (I-2/I-3):
#   - REP loop (env SAB_RINPUT_REPS, default 6): fresh inputs per trial,
#     same keys; per-trial gate check, pair noise, timings
#   - KS calibration: single eval_automorphism(aut_h) on a trivial sample
#     -> sigma_KS estimate
#   - scalar-path noise via oracle phases vs quantized grid
#   - M-HT.4 prediction: pair_pred = sqrt(sig_s^2 + h*sig_KS^2/4);
#     gate: measured/predicted < 1.3 (RMS over trials)
import re

p = 'src/probe_rinput.c'
data = open(p, 'rb').read()
BS = b'\x5c'

# 1) wrap the two-inputs generation + arm A + arm B comparison in a REP loop.
# Strategy: rename existing main flow pieces into a trial function is too
# invasive; instead: keep structure, add an outer loop by transforming the
# section between "/* two distinct inputs */" and the final prints.
# Simpler robust approach: append the REP logic as a NEW main section by
# renaming current main -> main_single, and add a new main() that loops.

data = data.replace(b'int main(void){\n  setvbuf', b'static int run_single(int trial, int reps,\n    double *t_int_out, double *t_or_out, uint64_t *pair_out,\n    int *gate_bad){\n  setvbuf', 1)
if b'static int run_single' not in data:
    # CRLF variant
    data = data.replace(b'int main(void){' + b'\r\n' + b'  setvbuf',
        b'static int run_single(int trial, int reps,\n    double *t_int_out, double *t_or_out, uint64_t *pair_out,\n    int *gate_bad){\n  setvbuf', 1)
assert b'run_single' in data

# 2) inside run_single: return code instead of exit-style; replace the final
#    'return 0;' of the old main with cleanup return, and strip the debug
#    prints that would spam (t<6 dumps, slot map) unless trial==0.
data = data.replace(b'if(t < 6 && lane == 0)', b'if(t < 6 && lane == 0 && trial == 0 && reps == 1)')
data = data.replace(b"if(lane == 0 && t < 32) printf(\"%c\", 'X');", b"if(lane == 0 && t < 32 && trial == 0 && reps == 1) printf(\"%c\", 'X');")
data = data.replace(b"else if(lane == 0 && t < 32) printf(\"%c\", '.');", b"else if(lane == 0 && t < 32 && trial == 0 && reps == 1) printf(\"%c\", '.');")

# 3) timing outputs -> pointers
data = data.replace(b'printf("RINPUT TIMING: interleaved=%.0f us  2x-scalar=%.0f us  "\n      "ratio(inter/2xscalar)=%.2fx\\n", t_int, t_or, t_int / t_or);',
  b'*t_int_out = t_int; *t_or_out = t_or; *pair_out = pair_dev_max;\n  *gate_bad = mism;')
data = data.replace(b'printf("RINPUT TIMING: interleaved=%.0f us  2x-scalar=%.0f us  "\r\n      "ratio(inter/2xscalar)=%.2fx\\n", t_int, t_or, t_int / t_or);',
  b'*t_int_out = t_int; *t_or_out = t_or; *pair_out = pair_dev_max;\n  *gate_bad = mism;')

open(p, 'wb').write(data)
print('phase 1 done: main->run_single')
