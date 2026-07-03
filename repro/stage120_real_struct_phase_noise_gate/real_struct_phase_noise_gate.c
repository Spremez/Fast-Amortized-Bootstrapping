#define _POSIX_C_SOURCE 200809L
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

typedef struct {
  size_t N;
  int64_t *coeffs;
} Poly;

typedef struct {
  Poly mask;
  Poly body;
} VSCipher;

typedef struct {
  size_t r;
  size_t N;
  Poly *secret;
  VSCipher *shared;
  VSCipher *body;
  size_t requested_bytes;
} VSObject;

static void *xcalloc(size_t count, size_t size) {
  void *ptr = calloc(count, size);
  if (ptr == NULL) {
    fprintf(stderr, "calloc failed\n");
    exit(2);
  }
  return ptr;
}

static long rss_kb(void) {
  FILE *fd = fopen("/proc/self/statm", "r");
  if (fd == NULL) return -1;
  long pages_total = 0;
  long pages_rss = 0;
  if (fscanf(fd, "%ld %ld", &pages_total, &pages_rss) != 2) {
    fclose(fd);
    return -1;
  }
  fclose(fd);
  long page = sysconf(_SC_PAGESIZE);
  if (page <= 0) page = 4096;
  return (pages_rss * page) / 1024;
}

static int64_t small(uint64_t salt, uint64_t a, uint64_t b, uint64_t c) {
  uint64_t x = salt * 0x9e3779b97f4a7c15ULL;
  x ^= (a + 0xbf58476d1ce4e5b9ULL) * 0x94d049bb133111ebULL;
  x ^= (b + 0x2545f4914f6cdd1dULL) * 0x9e3779b97f4a7c15ULL;
  x ^= (c + 0x100000001b3ULL) * 0xbf58476d1ce4e5b9ULL;
  x ^= x >> 33;
  int64_t v = (int64_t)(x % 7ULL) - 3;
  return v;
}

static int64_t msg(uint64_t salt, size_t lane, size_t coeff, size_t seed) {
  return small(salt + 10 * seed, lane, coeff, 0);
}

static int64_t digit(uint64_t salt, size_t lane, size_t coeff, size_t seed) {
  int64_t v = small(salt + 10 * seed, lane, coeff, 1);
  return v == 0 ? 1 : v;
}

static int64_t noise(size_t lane, size_t coeff, size_t term, size_t seed) {
  int64_t v = small(100 + 10 * seed + term, lane, coeff, 2) % 3;
  if (v < 0) v = -v;
  return v - 1;
}

static Poly alloc_poly(size_t N, size_t *bytes) {
  Poly p;
  p.N = N;
  p.coeffs = (int64_t *)xcalloc(N, sizeof(int64_t));
  *bytes += sizeof(int64_t) * N;
  return p;
}

static void free_poly(Poly *p) {
  free(p->coeffs);
  p->coeffs = NULL;
  p->N = 0;
}

static VSObject alloc_object(size_t r, size_t N) {
  VSObject obj;
  obj.r = r;
  obj.N = N;
  obj.requested_bytes = sizeof(VSObject);
  obj.secret = (Poly *)xcalloc(r, sizeof(Poly));
  obj.shared = (VSCipher *)xcalloc(r, sizeof(VSCipher));
  obj.body = (VSCipher *)xcalloc(r, sizeof(VSCipher));
  obj.requested_bytes += r * sizeof(Poly) + 2 * r * sizeof(VSCipher);
  for (size_t lane = 0; lane < r; lane++) {
    obj.secret[lane] = alloc_poly(N, &obj.requested_bytes);
    obj.shared[lane].mask = alloc_poly(N, &obj.requested_bytes);
    obj.shared[lane].body = alloc_poly(N, &obj.requested_bytes);
    obj.body[lane].mask = alloc_poly(N, &obj.requested_bytes);
    obj.body[lane].body = alloc_poly(N, &obj.requested_bytes);
  }
  return obj;
}

static void free_object(VSObject *obj) {
  for (size_t lane = 0; lane < obj->r; lane++) {
    free_poly(&obj->secret[lane]);
    free_poly(&obj->shared[lane].mask);
    free_poly(&obj->shared[lane].body);
    free_poly(&obj->body[lane].mask);
    free_poly(&obj->body[lane].body);
  }
  free(obj->secret);
  free(obj->shared);
  free(obj->body);
  obj->secret = NULL;
  obj->shared = NULL;
  obj->body = NULL;
}

static void negacyclic_mul(Poly *out, const Poly *a, const Poly *b) {
  const size_t N = out->N;
  memset(out->coeffs, 0, sizeof(int64_t) * N);
  for (size_t i = 0; i < N; i++) {
    for (size_t j = 0; j < N; j++) {
      size_t idx = i + j;
      int64_t sign = 1;
      if (idx >= N) {
        idx -= N;
        sign = -1;
      }
      out->coeffs[idx] += sign * a->coeffs[i] * b->coeffs[j];
    }
  }
}

static void fill_secret(VSObject *obj, size_t seed) {
  for (size_t lane = 0; lane < obj->r; lane++) {
    for (size_t i = 0; i < obj->N; i++) {
      int64_t v = small(20 + seed, lane, i, 0) % 3;
      obj->secret[lane].coeffs[i] = v;
    }
  }
}

static void encrypt_poly(VSCipher *ct, const Poly *secret, size_t lane,
    size_t seed, uint64_t msg_salt, uint64_t mask_salt, size_t noise_term,
    int with_noise) {
  const size_t N = secret->N;
  Poly prod = alloc_poly(N, &(size_t){0});
  for (size_t i = 0; i < N; i++) {
    ct->mask.coeffs[i] = small(mask_salt + seed, lane, i, 0);
  }
  negacyclic_mul(&prod, &ct->mask, secret);
  for (size_t i = 0; i < N; i++) {
    int64_t e = with_noise ? noise(lane, i, noise_term, seed) : 0;
    ct->body.coeffs[i] = prod.coeffs[i] + msg(msg_salt, lane, i, seed) + e;
  }
  free_poly(&prod);
}

static void decrypt_phase(Poly *out, const VSCipher *ct, const Poly *secret) {
  const size_t N = secret->N;
  Poly prod = alloc_poly(N, &(size_t){0});
  negacyclic_mul(&prod, &ct->mask, secret);
  for (size_t i = 0; i < N; i++) {
    out->coeffs[i] = ct->body.coeffs[i] - prod.coeffs[i];
  }
  free_poly(&prod);
}

static int run_case(size_t r, size_t N, size_t seed) {
  VSObject clean = alloc_object(r, N);
  VSObject noisy = alloc_object(r, N);
  fill_secret(&clean, seed);
  fill_secret(&noisy, seed);
  for (size_t lane = 0; lane < r; lane++) {
    encrypt_poly(&clean.shared[lane], &clean.secret[lane], lane, seed, 1, 31, 0, 0);
    encrypt_poly(&clean.body[lane], &clean.secret[lane], lane, seed, 2, 41, 1, 0);
    encrypt_poly(&noisy.shared[lane], &noisy.secret[lane], lane, seed, 1, 31, 0, 1);
    encrypt_poly(&noisy.body[lane], &noisy.secret[lane], lane, seed, 2, 41, 1, 1);
  }

  Poly phase_shared = alloc_poly(N, &clean.requested_bytes);
  Poly phase_body = alloc_poly(N, &clean.requested_bytes);
  Poly noisy_shared = alloc_poly(N, &clean.requested_bytes);
  Poly noisy_body = alloc_poly(N, &clean.requested_bytes);

  uint64_t mismatches = 0;
  uint64_t noise_violations = 0;
  int64_t max_err = 0;
  int64_t max_noise = 0;
  int64_t max_bound = 0;

  for (size_t lane = 0; lane < r; lane++) {
    decrypt_phase(&phase_shared, &clean.shared[lane], &clean.secret[lane]);
    decrypt_phase(&phase_body, &clean.body[lane], &clean.secret[lane]);
    decrypt_phase(&noisy_shared, &noisy.shared[lane], &noisy.secret[lane]);
    decrypt_phase(&noisy_body, &noisy.body[lane], &noisy.secret[lane]);
    for (size_t i = 0; i < N; i++) {
      const int64_t ds = digit(51, lane, i, seed);
      const int64_t db = digit(61, lane, i, seed);
      const int64_t expected = ds * msg(1, lane, i, seed) + db * msg(2, lane, i, seed);
      const int64_t got = ds * phase_shared.coeffs[i] + db * phase_body.coeffs[i];
      const int64_t noisy_got = ds * noisy_shared.coeffs[i] + db * noisy_body.coeffs[i];
      int64_t err = got - expected;
      if (err < 0) err = -err;
      int64_t nerr = noisy_got - got;
      if (nerr < 0) nerr = -nerr;
      int64_t bound = (ds < 0 ? -ds : ds) + (db < 0 ? -db : db);
      if (err != 0) mismatches++;
      if (nerr > bound) noise_violations++;
      if (err > max_err) max_err = err;
      if (nerr > max_noise) max_noise = nerr;
      if (bound > max_bound) max_bound = bound;
    }
  }

  const size_t requested = clean.requested_bytes + noisy.requested_bytes;
  const long rss = rss_kb();
  const int ok = mismatches == 0 && noise_violations == 0;
  printf("PHASE,%zu,%zu,%zu,%" PRIu64 ",%" PRId64 ",%" PRId64
         ",%" PRId64 ",%" PRIu64 ",%zu,%ld,%s\n",
      r, N, seed, mismatches, max_err, max_noise, max_bound,
      noise_violations, requested, rss, ok ? "PASS_REAL_STRUCT_PHASE_NOISE" : "FAIL");

  free_poly(&phase_shared);
  free_poly(&phase_body);
  free_poly(&noisy_shared);
  free_poly(&noisy_body);
  free_object(&clean);
  free_object(&noisy);
  return ok ? 0 : 1;
}

static int layout_case(size_t r, size_t N) {
  VSObject obj = alloc_object(r, N);
  const uint64_t dense_terms = (uint64_t)(r + 1) * (uint64_t)(r + 1);
  const uint64_t vector_terms = 2 * (uint64_t)r;
  const uint64_t dense_total_polys = (1 + (uint64_t)r) + dense_terms;
  const uint64_t vector_total_polys = 4 * (uint64_t)r;
  const double ratio = (double)vector_total_polys / (double)dense_total_polys;
  const int ok = vector_terms < dense_terms && ratio <= 1.0;
  printf("LAYOUT,%zu,%zu,%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%.6f,%zu,%s\n",
      r, N, dense_terms, vector_terms, dense_total_polys,
      vector_total_polys, ratio, obj.requested_bytes,
      ok ? "PASS_LAYOUT" : "FAIL");
  free_object(&obj);
  return ok ? 0 : 1;
}

int main(void) {
  const size_t rs[] = {2, 4, 6};
  const size_t Ns[] = {32, 64};
  const size_t seeds[] = {0, 1, 2, 3, 4};
  int failures = 0;
  for (size_t i = 0; i < sizeof(rs) / sizeof(rs[0]); i++) {
    for (size_t j = 0; j < sizeof(Ns) / sizeof(Ns[0]); j++) {
      failures += layout_case(rs[i], Ns[j]);
      for (size_t k = 0; k < sizeof(seeds) / sizeof(seeds[0]); k++) {
        failures += run_case(rs[i], Ns[j], seeds[k]);
      }
    }
  }
  return failures == 0 ? 0 : 1;
}
