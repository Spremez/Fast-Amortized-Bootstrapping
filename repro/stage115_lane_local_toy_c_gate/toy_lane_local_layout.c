#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>

typedef struct {
  size_t n;
  double *coeffs;
} ToyPoly;

static volatile double toy_sink = 0.0;

static void die(const char *msg) {
  fprintf(stderr, "%s\n", msg);
  exit(2);
}

static size_t page_size(void) {
  long p = sysconf(_SC_PAGESIZE);
  return p > 0 ? (size_t)p : (size_t)4096;
}

static long current_rss_kb(void) {
  FILE *fd = fopen("/proc/self/statm", "r");
  if (fd != NULL) {
    long total_pages = 0;
    long rss_pages = 0;
    if (fscanf(fd, "%ld %ld", &total_pages, &rss_pages) == 2) {
      fclose(fd);
      return (long)((rss_pages * (long)page_size()) / 1024L);
    }
    fclose(fd);
  }
  struct rusage usage;
  if (getrusage(RUSAGE_SELF, &usage) == 0) {
    return usage.ru_maxrss;
  }
  return -1;
}

static uint64_t now_us(void) {
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return (uint64_t)ts.tv_sec * 1000000ULL + (uint64_t)(ts.tv_nsec / 1000ULL);
}

static void *xaligned(size_t bytes) {
  void *ptr = NULL;
  if (posix_memalign(&ptr, 64, bytes) != 0 || ptr == NULL) {
    fprintf(stderr, "posix_memalign failed for %zu bytes: %s\n", bytes, strerror(errno));
    exit(2);
  }
  return ptr;
}

static ToyPoly *alloc_polys(size_t count, size_t N, size_t *requested_bytes) {
  ToyPoly *polys = (ToyPoly *)xaligned(sizeof(ToyPoly) * count);
  *requested_bytes += sizeof(ToyPoly) * count;
  for (size_t i = 0; i < count; i++) {
    polys[i].n = N;
    polys[i].coeffs = (double *)xaligned(sizeof(double) * N);
    *requested_bytes += sizeof(double) * N;
  }
  return polys;
}

static void touch_polys(ToyPoly *polys, size_t count) {
  for (size_t i = 0; i < count; i++) {
    for (size_t j = 0; j < polys[i].n; j++) {
      polys[i].coeffs[j] = (double)(i + 1) * 0.125 + (double)(j & 7);
    }
    toy_sink += polys[i].coeffs[polys[i].n - 1];
  }
}

static void free_polys(ToyPoly *polys, size_t count) {
  if (polys == NULL) return;
  for (size_t i = 0; i < count; i++) {
    free(polys[i].coeffs);
  }
  free(polys);
}

typedef struct {
  const char *layout;
  size_t r;
  size_t N;
  size_t acc_polys;
  size_t selector_polys;
  size_t scratch_torus_polys;
  size_t scratch_dft_polys;
  size_t product_terms;
} LayoutSpec;

static LayoutSpec spec_for(const char *layout, size_t r, size_t N) {
  LayoutSpec spec;
  spec.layout = layout;
  spec.r = r;
  spec.N = N;
  if (strcmp(layout, "current") == 0) {
    spec.acc_polys = 1 + r;
    spec.selector_polys = (1 + r) * (1 + r);
    spec.scratch_torus_polys = 1 + r;
    spec.scratch_dft_polys = 1 + r;
    spec.product_terms = (1 + r) * (1 + r);
    return spec;
  }
  if (strcmp(layout, "lane_local") == 0) {
    spec.acc_polys = 2 * r;
    spec.selector_polys = 2 * (1 + 2 * r);
    spec.scratch_torus_polys = 1 + 2 * r;
    spec.scratch_dft_polys = 1 + 2 * r;
    spec.product_terms = 1 + 2 * r;
    return spec;
  }
  die("layout must be current or lane_local");
  return spec;
}

int main(int argc, char **argv) {
  if (argc != 4) {
    fprintf(stderr, "usage: %s current|lane_local r N\n", argv[0]);
    return 2;
  }

  const char *layout = argv[1];
  size_t r = (size_t)strtoull(argv[2], NULL, 10);
  size_t N = (size_t)strtoull(argv[3], NULL, 10);
  if (r == 0 || N == 0) die("r and N must be non-zero");

  LayoutSpec spec = spec_for(layout, r, N);
  size_t requested_bytes = 0;
  uint64_t begin = now_us();
  ToyPoly *acc = alloc_polys(spec.acc_polys, N, &requested_bytes);
  ToyPoly *selector = alloc_polys(spec.selector_polys, N, &requested_bytes);
  ToyPoly *scratch_torus = alloc_polys(spec.scratch_torus_polys, N, &requested_bytes);
  ToyPoly *scratch_dft = alloc_polys(spec.scratch_dft_polys, N, &requested_bytes);

  touch_polys(acc, spec.acc_polys);
  touch_polys(selector, spec.selector_polys);
  touch_polys(scratch_torus, spec.scratch_torus_polys);
  touch_polys(scratch_dft, spec.scratch_dft_polys);
  uint64_t touch_us = now_us() - begin;
  long rss = current_rss_kb();

  printf("%s,%zu,%zu,%zu,%zu,%zu,%zu,%zu,%zu,%ld,%llu\n",
      spec.layout, spec.r, spec.N, spec.acc_polys, spec.selector_polys,
      spec.scratch_torus_polys, spec.scratch_dft_polys, spec.product_terms,
      requested_bytes, rss, (unsigned long long)touch_us);
  fflush(stdout);

  free_polys(scratch_dft, spec.scratch_dft_polys);
  free_polys(scratch_torus, spec.scratch_torus_polys);
  free_polys(selector, spec.selector_polys);
  free_polys(acc, spec.acc_polys);
  return toy_sink < 0.0 ? 1 : 0;
}
