# -*- coding: utf-8 -*-
p = 'src/probe_rinput.c'
data = open(p, 'rb').read()
CRLF = b'\x0d\x0a'
BS = b'\x5c'

anchor = (b'  free_polynomial(msg0); free_polynomial(msg1);' + CRLF +
          b'  free_trlwe_key(input_key); free_trlwe_key(packing_key);' + CRLF +
          b'  return 0;' + CRLF + b'}' + CRLF)
assert anchor in data, 'CRLF anchor missing'

lines = [
 b'/* ---- I-2/I-3 driver: REP trials + summary (KS calibration separate) */',
 b'int main(void){',
 b'  setvbuf(stdout, NULL, _IONBF, 0);',
 b'  int reps = 6;',
 b'  { const char *e = getenv("SAB_RINPUT_REPS");',
 b'    if(e) reps = atoi(e); if(reps < 1) reps = 1; if(reps > 64) reps = 64; }',
 b'  double t_ints[64], t_ors[64];',
 b'  uint64_t pairs[64];',
 b'  int bads[64];',
 b'  for (int rep = 0; rep < reps; rep++){',
 b'    printf("== trial %d/%d ==' + BS + b'n", rep + 1, reps);',
 b'    int rc = run_single(rep, reps, &t_ints[rep], &t_ors[rep],',
 b'        &pairs[rep], &bads[rep]);',
 b'    if(rc != 0){ printf("trial %d aborted (rc=%d)' + BS + b'n", rep, rc); return 1; }',
 b'  }',
 b'  int all_ok = 1;',
 b'  uint64_t max_pair = 0;',
 b'  double sum_sq_pair = 0;',
 b'  for (int rep = 0; rep < reps; rep++){',
 b'    if(bads[rep] != 0) all_ok = 0;',
 b'    if(pairs[rep] > max_pair) max_pair = pairs[rep];',
 b'    double d = (double) pairs[rep];',
 b'    sum_sq_pair += d * d;',
 b'  }',
 b'  for (int i = 1; i < reps; i++){',
 b'    double k = t_ints[i], k2 = t_ors[i]; int j = i - 1;',
 b'    while (j >= 0 && t_ints[j] > k){ t_ints[j+1] = t_ints[j]; t_ors[j+1] = t_ors[j]; j--; }',
 b'    t_ints[j+1] = k; t_ors[j+1] = k2;',
 b'  }',
 b'  double rms = sqrt(sum_sq_pair / reps);',
 b'  printf("SUMMARY: gates %s (%d trials), pair max log2 = %.2f, pair rms log2 = %.2f' + BS + b'n",',
 b'      all_ok ? "ALL PASS" : "FAIL", reps,',
 b'      log2((double) max_pair + 1.0), log2(rms + 1.0));',
 b'  printf("BENCH(median of %d): interleaved = %.0f us, 2x-scalar = %.0f us, ratio = %.3fx' + BS + b'n",',
 b'      reps, t_ints[reps/2], t_ors[reps/2], t_ints[reps/2] / t_ors[reps/2]);',
 b'  return all_ok ? 0 : 1;',
 b'}',
]
data = data.replace(anchor, anchor + CRLF.join(lines) + CRLF)
open(p, 'wb').write(data)
print('phase 2 done')
