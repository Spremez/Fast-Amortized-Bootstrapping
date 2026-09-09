# -*- coding: utf-8 -*-
# I-2 noise reconciliation: inside run_single, measure (a) scalar-path noise
# sigma_s = RMS grid residual of oracle phases; (b) single aut-KS noise
# sigma_KS via one eval_automorphism on a trivial sample. Output via two
# extra pointer params; SUMMARY prints M-HT.4 prediction vs measured.
p = 'src/probe_rinput.c'
data = open(p, 'rb').read()
CRLF = b'\x0d\x0a'
BS = b'\x5c'
NL = b'\x0a'
EOL = CRLF if CRLF in data else NL

# 1) extend run_single signature
old_sig = b'static int run_single(int trial, int reps,\n    double *t_int_out, double *t_or_out, uint64_t *pair_out,\n    int *gate_bad){'
if old_sig not in data:
    old_sig = (b'static int run_single(int trial, int reps,' + CRLF +
               b'    double *t_int_out, double *t_or_out, uint64_t *pair_out,' + CRLF +
               b'    int *gate_bad){')
assert old_sig in data, 'sig anchor'
new_sig = old_sig.replace(b'int *gate_bad){', b'int *gate_bad, double *sig_s_out, double *sig_ks_out){')
data = data.replace(old_sig, new_sig)

# 2) measurement block just before the timing outputs line
anchor = b'*t_int_out = t_int; *t_or_out = t_or; *pair_out = pair_dev_max;'
assert anchor in data
block_lines = [
 b'  /* I-2: scalar-path noise (RMS of grid residual; LUT grid = 2^(62-p-1)) */',
 b'  {',
 b'    const int64_t grid = (int64_t) 1 << (62 - prec - 1);',
 b'    double acc = 0; int cnt = 0;',
 b'    for (int t = 0; t < in_N; t++){',
 b'      trlwe_phase(p1, sacc_dummy_null(t), lane_key_dummy());',
 b'    }',
 b'  }',
]
# NOTE: sacc/lane_key are freed inside the loop; simpler to measure inside
# the comparison loop instead. Abandon block; measure residual there.
# -> Instead patch the comparison loop to accumulate scalar residual.
old_cmp = b'      if(v_scalar != v_int){ mism++; lane_mism[lane]++;'
assert old_cmp in data
# insert residual accumulation before the gate check: need sacc phase p1
# already computed (trlwe_phase(p1, sacc[t], lane_key)) in the loop.
acc_line = (b'      { const int64_t grid = (int64_t) 1 << (62 - prec - 1);' + EOL +
            b'        int64_t r = ((int64_t) p1->coeffs[0]) % grid;' + EOL +
            b'        if(r < 0) r = -r; if(r > grid/2) r = grid - r;' + EOL +
            b'        sig_s_acc += (double) r * (double) r; sig_s_cnt++; }' + EOL)
data = data.replace(old_cmp, acc_line + old_cmp)

# declare accumulators at top of the lane loop function scope: put near
# 'int mism = 0, lane_mism[2]'
old_decl = b'  int mism = 0, lane_mism[2] = {0, 0};'
assert old_decl in data
data = data.replace(old_decl, old_decl + EOL +
  b'  double sig_s_acc = 0; long sig_s_cnt = 0;')

# 3) output sig_s before the timing-outs line; KS calibration appended after
anchor2 = b'*t_int_out = t_int; *t_or_out = t_or; *pair_out = pair_dev_max;'
ks_lines = [
 b'  *sig_s_out = sqrt(sig_s_acc / (double) (sig_s_cnt > 0 ? sig_s_cnt : 1));',
 b'  /* I-2: single aut-KS noise: one eval_automorphism(aut_h) on trivial */',
 b'  {',
 b'    PVW_TMLWE triv = pvmtmlwe_alloc_new_sample(1, 1, out_N);',
 b'    PVW_TMLWE rot = pvmtmlwe_alloc_new_sample(1, 1, out_N);',
 b'    TorusPolynomial known = polynomial_new_torus_polynomial(out_N);',
 b'    for (int i = 0; i < out_N; i++)',
 b'      known->coeffs[i] = int2torus((3 * i + 1) & 7, prec + 2);',
 b'    memcpy(triv->b[0]->coeffs, known->coeffs,',
 b'        sizeof(known->coeffs[0]) * out_N);',
 b'    memset(triv->a[0]->coeffs, 0, sizeof(triv->a[0]->coeffs[0]) * out_N);',
 b'    double acc2 = 0;',
 b'    pvmtmlwe_eval_automorphism(rot, triv, 1 + out_N, ri->aut_h);',
 b'    rinput_phase(p2, rot, pvw_key);',
 b'    for (int i = 0; i < out_N; i++){',
 b'      /* expected phase coefficient: sigma_{1+N}(known) = flip odd */',
 b'      int64_t want = (i & 1) ? -(int64_t) known->coeffs[i]',
 b'                             : (int64_t) known->coeffs[i];',
 b'      int64_t dv = (int64_t) p2->coeffs[i] - want;',
 b'      acc2 += (double) dv * (double) dv;',
 b'    }',
 b'    *sig_ks_out = sqrt(acc2 / out_N);',
 b'    free_polynomial(known); free_pvmtmlwe(rot); free_pvmtmlwe(triv);',
 b'  }',
]
data = data.replace(anchor2, EOL.join(ks_lines) + EOL + anchor2)

open(p, 'wb').write(data)
print('noise measurement patched')
