#include <immintrin.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define ROWS 5
#define OUTS 5
#define N 2048
#define LANES 8
#define BLOCKS (N / 16)

static volatile double stage325_sink = 0.0;

static double now_sec(void) {
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

static void *aligned_checked_alloc(size_t bytes) {
  void *ptr = NULL;
  if (posix_memalign(&ptr, 64, bytes) != 0 || ptr == NULL) {
    fprintf(stderr, "allocation failed for %zu bytes\n", bytes);
    exit(2);
  }
  memset(ptr, 0, bytes);
  return ptr;
}

static uint64_t xorshift64(uint64_t *state) {
  uint64_t x = *state;
  x ^= x << 13;
  x ^= x >> 7;
  x ^= x << 17;
  *state = x;
  return x;
}

static void fill_random(double *dst, size_t count, uint64_t *state) {
  for (size_t i = 0; i < count; i++) {
    const uint64_t x = xorshift64(state);
    const double unit = (double)(x & 0xffffu) / 65536.0;
    dst[i] = unit - 0.5;
  }
}

static inline void complex_mul(__m512d dec_re, __m512d dec_im,
    __m512d sel_re, __m512d sel_im, __m512d *out_re, __m512d *out_im) {
  *out_re = _mm512_fmsub_pd(dec_re, sel_re, _mm512_mul_pd(dec_im, sel_im));
  *out_im = _mm512_fmadd_pd(dec_re, sel_im, _mm512_mul_pd(dec_im, sel_re));
}

static inline void complex_addmul(__m512d dec_re, __m512d dec_im,
    __m512d sel_re, __m512d sel_im, __m512d *acc_re, __m512d *acc_im) {
  const __m512d re_tmp = _mm512_fmsub_pd(dec_im, sel_im, *acc_re);
  *acc_re = _mm512_fmsub_pd(dec_re, sel_re, re_tmp);
  const __m512d im_tmp = _mm512_fmadd_pd(dec_im, sel_re, *acc_im);
  *acc_im = _mm512_fmadd_pd(dec_re, sel_im, im_tmp);
}

static void build_transposed_selector(double *restrict packed,
    double *restrict sel[ROWS][OUTS]) {
  for (int coeff = 0; coeff < BLOCKS; coeff++) {
    for (int row = 0; row < ROWS; row++) {
      for (int out = 0; out < OUTS; out++) {
        double *dst = packed + (((coeff * ROWS + row) * OUTS + out) * 16);
        const double *src = sel[row][out];
        memcpy(dst, src + coeff * LANES, sizeof(double) * LANES);
        memcpy(dst + LANES, src + (BLOCKS + coeff) * LANES,
            sizeof(double) * LANES);
      }
    }
  }
}

__attribute__((noinline))
static void current_rowpoly_kernel(double *restrict out[OUTS],
    double *restrict dec[ROWS], double *restrict sel[ROWS][OUTS]) {
  const __m512d *restrict decv[ROWS];
  const __m512d *restrict selv[ROWS][OUTS];
  __m512d *restrict outv[OUTS];
  for (int row = 0; row < ROWS; row++) {
    decv[row] = (const __m512d *)dec[row];
    for (int idx = 0; idx < OUTS; idx++) {
      selv[row][idx] = (const __m512d *)sel[row][idx];
    }
  }
  for (int idx = 0; idx < OUTS; idx++) {
    outv[idx] = (__m512d *)out[idx];
  }

  for (int coeff = 0; coeff < BLOCKS; coeff++) {
    __m512d acc_re[OUTS], acc_im[OUTS];
    __m512d dec_re = decv[0][coeff];
    __m512d dec_im = decv[0][coeff + BLOCKS];
    for (int idx = 0; idx < OUTS; idx++) {
      complex_mul(dec_re, dec_im, selv[0][idx][coeff],
          selv[0][idx][coeff + BLOCKS], &acc_re[idx], &acc_im[idx]);
    }
    for (int row = 1; row < ROWS; row++) {
      dec_re = decv[row][coeff];
      dec_im = decv[row][coeff + BLOCKS];
      for (int idx = 0; idx < OUTS; idx++) {
        complex_addmul(dec_re, dec_im, selv[row][idx][coeff],
            selv[row][idx][coeff + BLOCKS], &acc_re[idx], &acc_im[idx]);
      }
    }
    for (int idx = 0; idx < OUTS; idx++) {
      outv[idx][coeff] = acc_re[idx];
      outv[idx][coeff + BLOCKS] = acc_im[idx];
    }
  }
}

__attribute__((noinline))
static void coeffblocked_kernel(double *restrict out[OUTS],
    double *restrict dec[ROWS], const double *restrict packed) {
  const __m512d *restrict decv[ROWS];
  __m512d *restrict outv[OUTS];
  for (int row = 0; row < ROWS; row++) {
    decv[row] = (const __m512d *)dec[row];
  }
  for (int idx = 0; idx < OUTS; idx++) {
    outv[idx] = (__m512d *)out[idx];
  }

  for (int coeff = 0; coeff < BLOCKS; coeff++) {
    __m512d acc_re[OUTS], acc_im[OUTS];
    __m512d dec_re = decv[0][coeff];
    __m512d dec_im = decv[0][coeff + BLOCKS];
    for (int idx = 0; idx < OUTS; idx++) {
      const __m512d *sel = (const __m512d *)(packed +
          (((coeff * ROWS + 0) * OUTS + idx) * 16));
      complex_mul(dec_re, dec_im, sel[0], sel[1], &acc_re[idx],
          &acc_im[idx]);
    }
    for (int row = 1; row < ROWS; row++) {
      dec_re = decv[row][coeff];
      dec_im = decv[row][coeff + BLOCKS];
      for (int idx = 0; idx < OUTS; idx++) {
        const __m512d *sel = (const __m512d *)(packed +
            (((coeff * ROWS + row) * OUTS + idx) * 16));
        complex_addmul(dec_re, dec_im, sel[0], sel[1], &acc_re[idx],
            &acc_im[idx]);
      }
    }
    for (int idx = 0; idx < OUTS; idx++) {
      outv[idx][coeff] = acc_re[idx];
      outv[idx][coeff + BLOCKS] = acc_im[idx];
    }
  }
}

static double checksum(double *out[OUTS]) {
  double s = 0.0;
  for (int idx = 0; idx < OUTS; idx++) {
    for (int i = 0; i < N; i += 17) {
      s += out[idx][i];
    }
  }
  return s;
}

static double max_abs_diff(double *a[OUTS], double *b[OUTS]) {
  double max_diff = 0.0;
  for (int idx = 0; idx < OUTS; idx++) {
    for (int i = 0; i < N; i++) {
      const double diff = fabs(a[idx][i] - b[idx][i]);
      if (diff > max_diff) {
        max_diff = diff;
      }
    }
  }
  return max_diff;
}

int main(int argc, char **argv) {
  const int reps = argc > 1 ? atoi(argv[1]) : 20000;
  const int build_reps = argc > 2 ? atoi(argv[2]) : 200;
  const size_t poly_bytes = sizeof(double) * N;
  const size_t selector_bytes = (size_t)ROWS * OUTS * poly_bytes;
  const size_t packed_bytes = (size_t)BLOCKS * ROWS * OUTS * 16 * sizeof(double);

  double *dec[ROWS];
  double *sel[ROWS][OUTS];
  double *out_current[OUTS];
  double *out_packed[OUTS];
  double *packed = aligned_checked_alloc(packed_bytes);
  uint64_t state = 0x3253253253253251ull;

  for (int row = 0; row < ROWS; row++) {
    dec[row] = aligned_checked_alloc(poly_bytes);
    fill_random(dec[row], N, &state);
    for (int idx = 0; idx < OUTS; idx++) {
      sel[row][idx] = aligned_checked_alloc(poly_bytes);
      fill_random(sel[row][idx], N, &state);
    }
  }
  for (int idx = 0; idx < OUTS; idx++) {
    out_current[idx] = aligned_checked_alloc(poly_bytes);
    out_packed[idx] = aligned_checked_alloc(poly_bytes);
  }

  double build_start = now_sec();
  for (int i = 0; i < build_reps; i++) {
    build_transposed_selector(packed, sel);
  }
  const double build_sec = now_sec() - build_start;

  current_rowpoly_kernel(out_current, dec, sel);
  coeffblocked_kernel(out_packed, dec, packed);
  const double max_diff = max_abs_diff(out_current, out_packed);

  for (int i = 0; i < 50; i++) {
    current_rowpoly_kernel(out_current, dec, sel);
    coeffblocked_kernel(out_packed, dec, packed);
  }

  double start = now_sec();
  for (int i = 0; i < reps; i++) {
    current_rowpoly_kernel(out_current, dec, sel);
  }
  const double current_sec = now_sec() - start;

  start = now_sec();
  for (int i = 0; i < reps; i++) {
    coeffblocked_kernel(out_packed, dec, packed);
  }
  const double packed_sec = now_sec() - start;

  stage325_sink += checksum(out_current) + checksum(out_packed);

  const double current_avg_ns = current_sec * 1e9 / (double)reps;
  const double packed_avg_ns = packed_sec * 1e9 / (double)reps;
  const double build_avg_ns = build_sec * 1e9 / (double)build_reps;
  const double speedup = current_avg_ns / packed_avg_ns;

  printf("stage325_selector_transpose_microbench,"
         "rows=%d,outputs=%d,N=%d,blocks=%d,reps=%d,build_reps=%d,"
         "current_avg_ns=%.3f,packed_avg_ns=%.3f,speedup=%.9f,"
         "build_avg_ns=%.3f,max_abs_diff=%.17g,"
         "selector_bytes=%zu,packed_bytes=%zu,duplicate_probe_bytes=%zu,"
         "checksum=%.17g\n",
         ROWS, OUTS, N, BLOCKS, reps, build_reps, current_avg_ns,
         packed_avg_ns, speedup, build_avg_ns, max_diff, selector_bytes,
         packed_bytes, selector_bytes + packed_bytes, (double)stage325_sink);

  for (int row = 0; row < ROWS; row++) {
    free(dec[row]);
    for (int idx = 0; idx < OUTS; idx++) {
      free(sel[row][idx]);
    }
  }
  for (int idx = 0; idx < OUTS; idx++) {
    free(out_current[idx]);
    free(out_packed[idx]);
  }
  free(packed);
  return max_diff == 0.0 ? 0 : 1;
}
