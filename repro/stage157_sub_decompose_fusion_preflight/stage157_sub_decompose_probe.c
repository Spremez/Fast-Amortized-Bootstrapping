
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static uint64_t xs64(uint64_t *s) {
  uint64_t x = *s;
  x ^= x << 13;
  x ^= x >> 7;
  x ^= x << 17;
  *s = x;
  return x;
}

static double now_seconds(void) {
  return (double) clock() / (double) CLOCKS_PER_SEC;
}

static uint64_t dense_offset(int bg_bit, int l) {
  const int word_size = 64;
  uint64_t offset = 0;
  for (int i = 0; i < l; i++) {
    offset += (1ULL << (word_size - i * bg_bit - 1));
  }
  return offset;
}

static uint64_t decomp_dense_coeff(uint64_t x, int bg_bit, int l, int level) {
  const int word_size = 64;
  const uint64_t half_bg = (1ULL << (bg_bit - 1));
  const uint64_t h_mask = (1ULL << bg_bit) - 1;
  const uint64_t h_bit = (uint64_t)(word_size - (level + 1) * bg_bit);
  const uint64_t coeff_off = x + dense_offset(bg_bit, l);
  return ((coeff_off >> h_bit) & h_mask) - half_bg;
}

static uint64_t separate_sub_then_decompose(
    uint64_t *dec, uint64_t *sub, const uint64_t *in1, const uint64_t *in2,
    int components, int n, int bg_bit, int l) {
  uint64_t checksum = 0;
  const int total = components * n;
  for (int i = 0; i < total; i++) {
    sub[i] = in2[i] - in1[i];
  }
  for (int level = 0; level < l; level++) {
    for (int comp = 0; comp < components; comp++) {
      for (int c = 0; c < n; c++) {
        const int idx = comp * n + c;
        const int out_idx = (comp * l + level) * n + c;
        dec[out_idx] = decomp_dense_coeff(sub[idx], bg_bit, l, level);
        checksum += dec[out_idx] + (uint64_t)(out_idx + 1);
      }
    }
  }
  return checksum;
}

static uint64_t fused_sub_decompose(
    uint64_t *dec, const uint64_t *in1, const uint64_t *in2,
    int components, int n, int bg_bit, int l) {
  uint64_t checksum = 0;
  for (int level = 0; level < l; level++) {
    for (int comp = 0; comp < components; comp++) {
      for (int c = 0; c < n; c++) {
        const int idx = comp * n + c;
        const int out_idx = (comp * l + level) * n + c;
        const uint64_t diff = in2[idx] - in1[idx];
        dec[out_idx] = decomp_dense_coeff(diff, bg_bit, l, level);
        checksum += dec[out_idx] + (uint64_t)(out_idx + 1);
      }
    }
  }
  return checksum;
}

static int run_case(const char *name, int components, int n, int bg_bit, int l, int reps) {
  const int total = components * n;
  const int dec_total = components * l * n;
  uint64_t *in1 = (uint64_t *) malloc((size_t) total * sizeof(uint64_t));
  uint64_t *in2 = (uint64_t *) malloc((size_t) total * sizeof(uint64_t));
  uint64_t *sub = (uint64_t *) malloc((size_t) total * sizeof(uint64_t));
  uint64_t *dec_sep = (uint64_t *) malloc((size_t) dec_total * sizeof(uint64_t));
  uint64_t *dec_fused = (uint64_t *) malloc((size_t) dec_total * sizeof(uint64_t));
  if (!in1 || !in2 || !sub || !dec_sep || !dec_fused) {
    fprintf(stderr, "allocation failed\n");
    return 2;
  }

  uint64_t seed = 0x5354414745313537ULL;
  for (int i = 0; i < total; i++) {
    in1[i] = xs64(&seed);
    in2[i] = xs64(&seed);
  }

  uint64_t c1 = separate_sub_then_decompose(dec_sep, sub, in1, in2, components, n, bg_bit, l);
  uint64_t c2 = fused_sub_decompose(dec_fused, in1, in2, components, n, bg_bit, l);
  int mismatches = 0;
  int first = -1;
  for (int i = 0; i < dec_total; i++) {
    if (dec_sep[i] != dec_fused[i]) {
      mismatches++;
      if (first < 0) first = i;
    }
  }

  volatile uint64_t sink = c1 ^ c2;
  double start = now_seconds();
  for (int r = 0; r < reps; r++) {
    sink ^= separate_sub_then_decompose(dec_sep, sub, in1, in2, components, n, bg_bit, l);
  }
  double sep_s = now_seconds() - start;

  start = now_seconds();
  for (int r = 0; r < reps; r++) {
    sink ^= fused_sub_decompose(dec_fused, in1, in2, components, n, bg_bit, l);
  }
  double fused_s = now_seconds() - start;

  const double sep_ns = (sep_s * 1000000000.0) / (double) reps;
  const double fused_ns = (fused_s * 1000000000.0) / (double) reps;
  const double speedup = fused_ns > 0.0 ? sep_ns / fused_ns : 0.0;
  printf("%s,%d,%d,%d,%d,%d,%d,%d,%.3f,%.3f,%.6f,%" PRIu64 "\n",
      name, components, n, bg_bit, l, reps, mismatches, first,
      sep_ns, fused_ns, speedup, sink);

  free(in1);
  free(in2);
  free(sub);
  free(dec_sep);
  free(dec_fused);
  return mismatches ? 1 : 0;
}

int main(void) {
  printf("case,components,N,Bg_bit,l,reps,mismatches,first_mismatch,separate_ns,fused_ns,speedup,sink\n");
  int rc = 0;
  rc |= run_case("target_r6_N2048_l1_bg23", 7, 2048, 23, 1, 8000);
  rc |= run_case("control_r4_N2048_l1_bg23", 5, 2048, 23, 1, 10000);
  rc |= run_case("control_r6_N2048_l2_bg8", 7, 2048, 8, 2, 5000);
  return rc;
}
