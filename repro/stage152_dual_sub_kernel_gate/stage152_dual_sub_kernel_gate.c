#include <errno.h>
#include <immintrin.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef struct {
  uint64_t *a;
  uint64_t **b;
  int r;
  int N;
} sample_t;

static uint64_t splitmix64(uint64_t *x) {
  uint64_t z = (*x += UINT64_C(0x9e3779b97f4a7c15));
  z = (z ^ (z >> 30)) * UINT64_C(0xbf58476d1ce4e5b9);
  z = (z ^ (z >> 27)) * UINT64_C(0x94d049bb133111eb);
  return z ^ (z >> 31);
}

static uint64_t now_us(void) {
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return (uint64_t) ts.tv_sec * UINT64_C(1000000) + (uint64_t) ts.tv_nsec / UINT64_C(1000);
}

static void *aligned_malloc_or_die(size_t bytes) {
  void *p = NULL;
  const int rc = posix_memalign(&p, 64, bytes);
  if (rc != 0 || p == NULL) {
    fprintf(stderr, "posix_memalign failed: %s\n", strerror(rc ? rc : errno));
    exit(2);
  }
  return p;
}

static sample_t sample_alloc(int r, int N) {
  sample_t s;
  s.r = r;
  s.N = N;
  s.a = (uint64_t *) aligned_malloc_or_die((size_t) N * sizeof(uint64_t));
  s.b = (uint64_t **) aligned_malloc_or_die((size_t) r * sizeof(uint64_t *));
  for (int lane = 0; lane < r; lane++) {
    s.b[lane] = (uint64_t *) aligned_malloc_or_die((size_t) N * sizeof(uint64_t));
  }
  return s;
}

static void sample_free(sample_t *s) {
  for (int lane = 0; lane < s->r; lane++) {
    free(s->b[lane]);
  }
  free(s->b);
  free(s->a);
  s->b = NULL;
  s->a = NULL;
}

static void sample_fill(sample_t *s, uint64_t seed) {
  uint64_t x = seed;
  for (int i = 0; i < s->N; i++) {
    s->a[i] = splitmix64(&x);
  }
  for (int lane = 0; lane < s->r; lane++) {
    for (int i = 0; i < s->N; i++) {
      s->b[lane][i] = splitmix64(&x);
    }
  }
}

static uint64_t sample_checksum(const sample_t *s) {
  uint64_t acc = UINT64_C(0x123456789abcdef0);
  for (int i = 0; i < s->N; i += 17) {
    acc ^= s->a[i] + UINT64_C(0x9e3779b97f4a7c15) + (acc << 6) + (acc >> 2);
  }
  for (int lane = 0; lane < s->r; lane++) {
    for (int i = lane; i < s->N; i += 19) {
      acc ^= s->b[lane][i] + UINT64_C(0xbf58476d1ce4e5b9) + (acc << 5) + (acc >> 3);
    }
  }
  return acc;
}

__attribute__((noinline))
static void sample_sub(sample_t *out, const sample_t *in1, const sample_t *in2) {
  const int vecs = in1->N / 8;
  const __m512i *a1 = (const __m512i *) in1->a;
  const __m512i *a2 = (const __m512i *) in2->a;
  __m512i *ao = (__m512i *) out->a;
  for (int i = 0; i < vecs; i++) {
    ao[i] = _mm512_sub_epi64(a1[i], a2[i]);
  }
  for (int lane = 0; lane < in1->r; lane++) {
    const __m512i *b1 = (const __m512i *) in1->b[lane];
    const __m512i *b2 = (const __m512i *) in2->b[lane];
    __m512i *bo = (__m512i *) out->b[lane];
    for (int i = 0; i < vecs; i++) {
      bo[i] = _mm512_sub_epi64(b1[i], b2[i]);
    }
  }
}

__attribute__((noinline))
static void current_pair(sample_t *direct_out, sample_t *ncmux_out,
    const sample_t *shared, const sample_t *direct_rhs, const sample_t *rotated) {
  sample_sub(direct_out, shared, direct_rhs);
  sample_sub(ncmux_out, rotated, shared);
}

__attribute__((noinline))
static void fused_pair(sample_t *direct_out, sample_t *ncmux_out,
    const sample_t *shared, const sample_t *direct_rhs, const sample_t *rotated) {
  const int vecs = shared->N / 8;
  const __m512i *sa = (const __m512i *) shared->a;
  const __m512i *da = (const __m512i *) direct_rhs->a;
  const __m512i *ra = (const __m512i *) rotated->a;
  __m512i *doa = (__m512i *) direct_out->a;
  __m512i *noa = (__m512i *) ncmux_out->a;
  for (int i = 0; i < vecs; i++) {
    const __m512i x = sa[i];
    doa[i] = _mm512_sub_epi64(x, da[i]);
    noa[i] = _mm512_sub_epi64(ra[i], x);
  }
  for (int lane = 0; lane < shared->r; lane++) {
    const __m512i *sb = (const __m512i *) shared->b[lane];
    const __m512i *db = (const __m512i *) direct_rhs->b[lane];
    const __m512i *rb = (const __m512i *) rotated->b[lane];
    __m512i *dob = (__m512i *) direct_out->b[lane];
    __m512i *nob = (__m512i *) ncmux_out->b[lane];
    for (int i = 0; i < vecs; i++) {
      const __m512i x = sb[i];
      dob[i] = _mm512_sub_epi64(x, db[i]);
      nob[i] = _mm512_sub_epi64(rb[i], x);
    }
  }
}

static int samples_equal(const sample_t *x, const sample_t *y) {
  if (memcmp(x->a, y->a, (size_t) x->N * sizeof(uint64_t)) != 0) {
    return 0;
  }
  for (int lane = 0; lane < x->r; lane++) {
    if (memcmp(x->b[lane], y->b[lane], (size_t) x->N * sizeof(uint64_t)) != 0) {
      return 0;
    }
  }
  return 1;
}

int main(int argc, char **argv) {
  const int r = argc > 1 ? atoi(argv[1]) : 6;
  const int N = argc > 2 ? atoi(argv[2]) : 2048;
  const int reps = argc > 3 ? atoi(argv[3]) : 20000;
  if (r <= 0 || N <= 0 || (N % 8) != 0 || reps <= 0) {
    fprintf(stderr, "invalid args r=%d N=%d reps=%d\n", r, N, reps);
    return 2;
  }

  sample_t shared = sample_alloc(r, N);
  sample_t direct_rhs = sample_alloc(r, N);
  sample_t rotated = sample_alloc(r, N);
  sample_t cur_direct = sample_alloc(r, N);
  sample_t cur_ncmux = sample_alloc(r, N);
  sample_t fused_direct = sample_alloc(r, N);
  sample_t fused_ncmux = sample_alloc(r, N);

  sample_fill(&shared, UINT64_C(0x15200001));
  sample_fill(&direct_rhs, UINT64_C(0x15200002));
  sample_fill(&rotated, UINT64_C(0x15200003));

  current_pair(&cur_direct, &cur_ncmux, &shared, &direct_rhs, &rotated);
  fused_pair(&fused_direct, &fused_ncmux, &shared, &direct_rhs, &rotated);
  const int ok = samples_equal(&cur_direct, &fused_direct) &&
      samples_equal(&cur_ncmux, &fused_ncmux);

  uint64_t checksum_current = 0;
  uint64_t checksum_fused = 0;
  const uint64_t current_begin = now_us();
  for (int rep = 0; rep < reps; rep++) {
    current_pair(&cur_direct, &cur_ncmux, &shared, &direct_rhs, &rotated);
  }
  const uint64_t current_us = now_us() - current_begin;
  checksum_current = sample_checksum(&cur_direct) +
      (sample_checksum(&cur_ncmux) << 1) + (uint64_t) reps;

  const uint64_t fused_begin = now_us();
  for (int rep = 0; rep < reps; rep++) {
    fused_pair(&fused_direct, &fused_ncmux, &shared, &direct_rhs, &rotated);
  }
  const uint64_t fused_us = now_us() - fused_begin;
  checksum_fused = sample_checksum(&fused_direct) +
      (sample_checksum(&fused_ncmux) << 1) + (uint64_t) reps;

  printf("STAGE152_DUAL_SUB r=%d N=%d reps=%d current_us=%" PRIu64
         " fused_us=%" PRIu64 " speedup=%.6f correctness=%s"
         " checksum_current=%" PRIu64 " checksum_fused=%" PRIu64 "\n",
         r, N, reps, current_us, fused_us,
         fused_us ? (double) current_us / (double) fused_us : 0.0,
         ok ? "PASS" : "FAIL", checksum_current, checksum_fused);

  sample_free(&shared);
  sample_free(&direct_rhs);
  sample_free(&rotated);
  sample_free(&cur_direct);
  sample_free(&cur_ncmux);
  sample_free(&fused_direct);
  sample_free(&fused_ncmux);
  return ok ? 0 : 1;
}
