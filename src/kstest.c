/* kstest.c -- WS-6 primitive check: trlwe_keyswitch(s,s) phase transport.
 * A fresh binary key (thinned to h~8 nonzeros), encrypt a known message,
 * keyswitch, compare phases. Expected delta ~ KS noise (2^54-56), NOT 2^63. */
#include <mosfhet.h>
#include <stdio.h>
#include <math.h>
int main(void){
  const int n = 256;
  TRLWE_Key k = trlwe_new_binary_key(n, 1, pow(2,-15));
  for(int i=0;i<n;i++) if(i%37!=0) k->s[0]->coeffs[i]=0;
  int h=0; for(int i=0;i<n;i++) if(k->s[0]->coeffs[i]) h++;
  TRLWE_KS_Key ks = trlwe_new_KS_key(k, k, 12, 1);
  TorusPolynomial m = polynomial_new_torus_polynomial(n);
  for(int i=0;i<n;i++) m->coeffs[i] = int2torus((3*i)&7, 3);
  TRLWE c = trlwe_new_sample(m, k);
  TRLWE o = trlwe_alloc_new_sample(1, n);
  trlwe_keyswitch(o, c, ks);
  TorusPolynomial ph_c = polynomial_new_torus_polynomial(n);
  TorusPolynomial ph_o = polynomial_new_torus_polynomial(n);
  trlwe_phase(ph_c, c, k);
  trlwe_phase(ph_o, o, k);
  uint64_t dmax=0; double dsq=0;
  for(int i=0;i<n;i++){
    uint64_t d = ph_o->coeffs[i] - ph_c->coeffs[i];
    if(d > 0x8000000000000000ULL) d = (uint64_t)0 - d;
    if(d>dmax) dmax=d; dsq += (double)d*(double)d;
  }
  printf("KS(s,s) phase-transport delta: max log2=%.1f rms log2=%.1f (h=%d)\n",
      log2((double)dmax+1.0), log2(sqrt(dsq/n)+1.0), h);
  return 0;
}
