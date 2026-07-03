#define _POSIX_C_SOURCE 200809L
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

enum { MOD = 12289 };

typedef struct {
  size_t N;
  int64_t *coeffs;
} Poly;

typedef struct {
  size_t N;
  int64_t *evals;
} DftPoly;

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

static int64_t mod_norm(int64_t x) {
  int64_t v = x % MOD;
  if (v < 0) v += MOD;
  return v;
}

static int64_t mod_signed(int64_t x) {
  int64_t v = mod_norm(x);
  if (v > MOD / 2) v -= MOD;
  return v;
}

static int64_t mod_pow(int64_t a, int64_t e) {
  int64_t out = 1;
  int64_t base = mod_norm(a);
  while (e > 0) {
    if (e & 1) out = (out * base) % MOD;
    base = (base * base) % MOD;
    e >>= 1;
  }
  return out;
}

static int64_t mod_inv(int64_t x) {
  return mod_pow(x, MOD - 2);
}

static int64_t primitive_root_mod(void) {
  const int64_t factors[] = {2, 3};
  for (int64_t g = 2; g < MOD; g++) {
    int ok = 1;
    for (size_t i = 0; i < sizeof(factors) / sizeof(factors[0]); i++) {
      if (mod_pow(g, (MOD - 1) / factors[i]) == 1) {
        ok = 0;
        break;
      }
    }
    if (ok) return g;
  }
  return 0;
}

static int64_t negacyclic_root(size_t N, int *ok) {
  const int64_t g = primitive_root_mod();
  if (g == 0 || ((MOD - 1) % (int64_t)(2 * N)) != 0) {
    *ok = 0;
    return 0;
  }
  const int64_t psi = mod_pow(g, (MOD - 1) / (int64_t)(2 * N));
  *ok = (mod_pow(psi, (int64_t)N) == MOD - 1)
      && (mod_pow(psi, (int64_t)(2 * N)) == 1);
  return psi;
}

static int64_t small(uint64_t salt, uint64_t a, uint64_t b, uint64_t c) {
  uint64_t x = salt * 0x9e3779b97f4a7c15ULL;
  x ^= (a + 0xbf58476d1ce4e5b9ULL) * 0x94d049bb133111ebULL;
  x ^= (b + 0x2545f4914f6cdd1dULL) * 0x9e3779b97f4a7c15ULL;
  x ^= (c + 0x100000001b3ULL) * 0xbf58476d1ce4e5b9ULL;
  x ^= x >> 33;
  return (int64_t)(x % 7ULL) - 3;
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

static DftPoly alloc_dft(size_t N, size_t *bytes) {
  DftPoly p;
  p.N = N;
  p.evals = (int64_t *)xcalloc(N, sizeof(int64_t));
  *bytes += sizeof(int64_t) * N;
  return p;
}

static void free_poly(Poly *p) {
  free(p->coeffs);
  p->coeffs = NULL;
  p->N = 0;
}

static void free_dft(DftPoly *p) {
  free(p->evals);
  p->evals = NULL;
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

static void forward_dft(DftPoly *out, const Poly *in, int64_t psi) {
  const size_t N = in->N;
  for (size_t j = 0; j < N; j++) {
    const int64_t root = mod_pow(psi, (int64_t)(2 * j + 1));
    int64_t power = 1;
    int64_t acc = 0;
    for (size_t i = 0; i < N; i++) {
      acc = mod_norm(acc + mod_norm(in->coeffs[i]) * power);
      power = (power * root) % MOD;
    }
    out->evals[j] = acc;
  }
}

static void inverse_dft(Poly *out, const DftPoly *in, int64_t psi) {
  const size_t N = out->N;
  const int64_t n_inv = mod_inv((int64_t)N);
  for (size_t i = 0; i < N; i++) {
    int64_t acc = 0;
    for (size_t j = 0; j < N; j++) {
      const int64_t root = mod_pow(psi, (int64_t)(2 * j + 1));
      const int64_t inv_root = mod_inv(root);
      const int64_t factor = mod_pow(inv_root, (int64_t)i);
      acc = mod_norm(acc + in->evals[j] * factor);
    }
    out->coeffs[i] = mod_signed(acc * n_inv);
  }
}

static void dft_phase(DftPoly *out, const DftPoly *body, const DftPoly *mask,
    const DftPoly *secret) {
  for (size_t i = 0; i < out->N; i++) {
    out->evals[i] = mod_norm(body->evals[i] - mask->evals[i] * secret->evals[i]);
  }
}

static void fill_secret(VSObject *obj, size_t seed) {
  for (size_t lane = 0; lane < obj->r; lane++) {
    for (size_t i = 0; i < obj->N; i++) {
      obj->secret[lane].coeffs[i] = small(20 + seed, lane, i, 0) % 3;
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
    const int64_t e = with_noise ? noise(lane, i, noise_term, seed) : 0;
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

static uint64_t roundtrip_check(const Poly *p, int64_t psi, size_t *bytes) {
  DftPoly d = alloc_dft(p->N, bytes);
  Poly back = alloc_poly(p->N, bytes);
  uint64_t mismatches = 0;
  forward_dft(&d, p, psi);
  inverse_dft(&back, &d, psi);
  for (size_t i = 0; i < p->N; i++) {
    if (back.coeffs[i] != p->coeffs[i]) mismatches++;
  }
  free_dft(&d);
  free_poly(&back);
  return mismatches;
}

static uint64_t dft_decrypt_phase(Poly *out, const VSCipher *ct,
    const Poly *secret, int64_t psi, size_t *bytes) {
  DftPoly mask_d = alloc_dft(secret->N, bytes);
  DftPoly body_d = alloc_dft(secret->N, bytes);
  DftPoly secret_d = alloc_dft(secret->N, bytes);
  DftPoly phase_d = alloc_dft(secret->N, bytes);
  forward_dft(&mask_d, &ct->mask, psi);
  forward_dft(&body_d, &ct->body, psi);
  forward_dft(&secret_d, secret, psi);
  dft_phase(&phase_d, &body_d, &mask_d, &secret_d);
  inverse_dft(out, &phase_d, psi);
  free_dft(&mask_d);
  free_dft(&body_d);
  free_dft(&secret_d);
  free_dft(&phase_d);
  return 0;
}

static int run_case(size_t r, size_t N, size_t seed) {
  int root_ok = 0;
  const int64_t psi = negacyclic_root(N, &root_ok);
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

  size_t transient_bytes = 0;
  Poly phase_shared = alloc_poly(N, &transient_bytes);
  Poly phase_body = alloc_poly(N, &transient_bytes);
  Poly noisy_shared = alloc_poly(N, &transient_bytes);
  Poly noisy_body = alloc_poly(N, &transient_bytes);
  Poly dft_phase_shared = alloc_poly(N, &transient_bytes);
  Poly dft_phase_body = alloc_poly(N, &transient_bytes);
  Poly dft_noisy_shared = alloc_poly(N, &transient_bytes);
  Poly dft_noisy_body = alloc_poly(N, &transient_bytes);

  uint64_t roundtrip_mismatches = 0;
  uint64_t phase_mismatches = 0;
  uint64_t noisy_phase_mismatches = 0;
  uint64_t noise_violations = 0;
  int64_t max_phase_error = 0;
  int64_t max_noisy_phase_error = 0;
  int64_t max_noise = 0;
  int64_t max_bound = 0;

  if (root_ok) {
    for (size_t lane = 0; lane < r; lane++) {
      roundtrip_mismatches += roundtrip_check(&clean.secret[lane], psi, &transient_bytes);
      roundtrip_mismatches += roundtrip_check(&clean.shared[lane].mask, psi, &transient_bytes);
      roundtrip_mismatches += roundtrip_check(&clean.shared[lane].body, psi, &transient_bytes);
      roundtrip_mismatches += roundtrip_check(&clean.body[lane].mask, psi, &transient_bytes);
      roundtrip_mismatches += roundtrip_check(&clean.body[lane].body, psi, &transient_bytes);

      decrypt_phase(&phase_shared, &clean.shared[lane], &clean.secret[lane]);
      decrypt_phase(&phase_body, &clean.body[lane], &clean.secret[lane]);
      decrypt_phase(&noisy_shared, &noisy.shared[lane], &noisy.secret[lane]);
      decrypt_phase(&noisy_body, &noisy.body[lane], &noisy.secret[lane]);

      dft_decrypt_phase(&dft_phase_shared, &clean.shared[lane], &clean.secret[lane], psi, &transient_bytes);
      dft_decrypt_phase(&dft_phase_body, &clean.body[lane], &clean.secret[lane], psi, &transient_bytes);
      dft_decrypt_phase(&dft_noisy_shared, &noisy.shared[lane], &noisy.secret[lane], psi, &transient_bytes);
      dft_decrypt_phase(&dft_noisy_body, &noisy.body[lane], &noisy.secret[lane], psi, &transient_bytes);

      for (size_t i = 0; i < N; i++) {
        int64_t err_s = dft_phase_shared.coeffs[i] - phase_shared.coeffs[i];
        int64_t err_b = dft_phase_body.coeffs[i] - phase_body.coeffs[i];
        int64_t nerr_s = dft_noisy_shared.coeffs[i] - noisy_shared.coeffs[i];
        int64_t nerr_b = dft_noisy_body.coeffs[i] - noisy_body.coeffs[i];
        if (err_s < 0) err_s = -err_s;
        if (err_b < 0) err_b = -err_b;
        if (nerr_s < 0) nerr_s = -nerr_s;
        if (nerr_b < 0) nerr_b = -nerr_b;
        if (err_s != 0 || err_b != 0) phase_mismatches++;
        if (nerr_s != 0 || nerr_b != 0) noisy_phase_mismatches++;
        if (err_s > max_phase_error) max_phase_error = err_s;
        if (err_b > max_phase_error) max_phase_error = err_b;
        if (nerr_s > max_noisy_phase_error) max_noisy_phase_error = nerr_s;
        if (nerr_b > max_noisy_phase_error) max_noisy_phase_error = nerr_b;

        const int64_t ds = digit(51, lane, i, seed);
        const int64_t db = digit(61, lane, i, seed);
        const int64_t clean_combined = ds * phase_shared.coeffs[i] + db * phase_body.coeffs[i];
        const int64_t noisy_combined = ds * noisy_shared.coeffs[i] + db * noisy_body.coeffs[i];
        int64_t combined_noise = noisy_combined - clean_combined;
        if (combined_noise < 0) combined_noise = -combined_noise;
        int64_t bound = (ds < 0 ? -ds : ds) + (db < 0 ? -db : db);
        if (combined_noise > bound) noise_violations++;
        if (combined_noise > max_noise) max_noise = combined_noise;
        if (bound > max_bound) max_bound = bound;
      }
    }
  }

  const size_t requested = clean.requested_bytes + noisy.requested_bytes + transient_bytes;
  const long rss = rss_kb();
  const int ok = root_ok && roundtrip_mismatches == 0 && phase_mismatches == 0
      && noisy_phase_mismatches == 0 && noise_violations == 0;
  printf("CONVERT,%zu,%zu,%zu,%d,%s,%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRId64 ",%" PRId64 ",%" PRId64 ",%" PRId64
         ",%zu,%ld,%s\n",
      r, N, seed, MOD, root_ok ? "PASS_ROOT" : "FAIL_ROOT",
      roundtrip_mismatches, phase_mismatches, noisy_phase_mismatches,
      noise_violations, max_phase_error, max_noisy_phase_error, max_noise,
      max_bound, requested, rss, ok ? "PASS_DFT_CONVERSION" : "FAIL");

  free_poly(&phase_shared);
  free_poly(&phase_body);
  free_poly(&noisy_shared);
  free_poly(&noisy_body);
  free_poly(&dft_phase_shared);
  free_poly(&dft_phase_body);
  free_poly(&dft_noisy_shared);
  free_poly(&dft_noisy_body);
  free_object(&clean);
  free_object(&noisy);
  return ok ? 0 : 1;
}

static int layout_case(size_t r, size_t N) {
  VSObject obj = alloc_object(r, N);
  const uint64_t dense_dft_polys = (1 + (uint64_t)r) + (uint64_t)(r + 1) * (uint64_t)(r + 1);
  const uint64_t vector_dft_polys = 4 * (uint64_t)r;
  const uint64_t conversion_input_polys = 5 * (uint64_t)r;
  const double ratio = (double)vector_dft_polys / (double)dense_dft_polys;
  const int ok = vector_dft_polys <= dense_dft_polys && conversion_input_polys > vector_dft_polys;
  printf("LAYOUT,%zu,%zu,%" PRIu64 ",%" PRIu64 ",%.6f,%" PRIu64
         ",%zu,%s\n",
      r, N, dense_dft_polys, vector_dft_polys, ratio,
      conversion_input_polys, obj.requested_bytes, ok ? "PASS_LAYOUT" : "FAIL");
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
