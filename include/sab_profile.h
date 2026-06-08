#ifndef SAB_PROFILE_H
#define SAB_PROFILE_H

#include <stdint.h>

#ifdef SAB_PROFILE

#include <sys/time.h>

typedef enum {
  SAB_PROF_TRGSW_MUL_TRLWE_DFT = 0,
  SAB_PROF_CMUX,
  SAB_PROF_NCMUX,
  SAB_PROF_RGSW_MONOMIAL_MUL,
  SAB_PROF_SUB_A,
  SAB_PROF_SUB_A_GA,
  SAB_PROF_SPARSE_MUL,
  SAB_PROF_SETUP_TV_XB,
  SAB_PROF_BLIND_ROTATE,
  SAB_PROF_BOOTSTRAP_WO_EXTRACT,
  SAB_PROF_EXTRACT,
  SAB_PROF_PACKING_KS,
  SAB_PROF_HW_KS,
  SAB_PROF_BOOTSTRAP,
  SAB_PROF_COUNT
} SAB_Profile_Event;

static inline uint64_t sab_profile_now_us(void) {
  struct timeval tv;
  gettimeofday(&tv, 0);
  return (uint64_t) tv.tv_usec + (uint64_t) tv.tv_sec * 1000000ULL;
}

void sab_profile_reset(void);
void sab_profile_add(SAB_Profile_Event event, uint64_t elapsed_us);
void sab_profile_print(void);

#define SAB_PROFILE_TIME(EVENT, ...) \
  do { \
    uint64_t __sab_profile_begin_us = sab_profile_now_us(); \
    __VA_ARGS__; \
    sab_profile_add((EVENT), sab_profile_now_us() - __sab_profile_begin_us); \
  } while (0)

#define SAB_PROFILE_RESET() sab_profile_reset()
#define SAB_PROFILE_PRINT() sab_profile_print()

#else

#define SAB_PROFILE_TIME(EVENT, ...) do { __VA_ARGS__; } while (0)
#define SAB_PROFILE_RESET() ((void) 0)
#define SAB_PROFILE_PRINT() ((void) 0)

#endif

#endif
