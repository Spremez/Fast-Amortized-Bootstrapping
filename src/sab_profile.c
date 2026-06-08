#include <sab_profile.h>

#ifdef SAB_PROFILE

#include <inttypes.h>
#include <stddef.h>
#include <stdio.h>

typedef struct {
  const char * name;
  uint64_t calls;
  uint64_t total_us;
} SAB_Profile_Counter;

static SAB_Profile_Counter sab_profile_counters[SAB_PROF_COUNT] = {
  [SAB_PROF_TRGSW_MUL_TRLWE_DFT] = {"trgsw_mul_trlwe_DFT", 0, 0},
  [SAB_PROF_CMUX] = {"CMUX", 0, 0},
  [SAB_PROF_NCMUX] = {"NCMUX", 0, 0},
  [SAB_PROF_RGSW_MONOMIAL_MUL] = {"RGSW_monomial_mul", 0, 0},
  [SAB_PROF_SUB_A] = {"sub_a", 0, 0},
  [SAB_PROF_SUB_A_GA] = {"sub_a_ga", 0, 0},
  [SAB_PROF_SPARSE_MUL] = {"sparse_mul", 0, 0},
  [SAB_PROF_SETUP_TV_XB] = {"setup_tv_xb", 0, 0},
  [SAB_PROF_BLIND_ROTATE] = {"sab_blind_rotate", 0, 0},
  [SAB_PROF_BOOTSTRAP_WO_EXTRACT] = {"sab_rlwe_bootstrap_wo_extract", 0, 0},
  [SAB_PROF_EXTRACT] = {"extract_tlwe_loop", 0, 0},
  [SAB_PROF_PACKING_KS] = {"trlwe_full_packing_keyswitch", 0, 0},
  [SAB_PROF_HW_KS] = {"trlwe_keyswitch_hw_reduce", 0, 0},
  [SAB_PROF_BOOTSTRAP] = {"sab_rlwe_bootstrap", 0, 0},
};

void sab_profile_reset(void) {
  for (size_t i = 0; i < SAB_PROF_COUNT; i++) {
    sab_profile_counters[i].calls = 0;
    sab_profile_counters[i].total_us = 0;
  }
}

void sab_profile_add(SAB_Profile_Event event, uint64_t elapsed_us) {
  if (event >= SAB_PROF_COUNT) return;
  sab_profile_counters[event].calls++;
  sab_profile_counters[event].total_us += elapsed_us;
}

void sab_profile_print(void) {
  const uint64_t total = sab_profile_counters[SAB_PROF_BOOTSTRAP].total_us;
  printf("\nSAB profile (inclusive time, accumulated over measured repetitions)\n");
  printf("%-32s %12s %16s %16s %10s\n", "event", "calls", "total_us", "avg_us", "pct_total");
  for (size_t i = 0; i < SAB_PROF_COUNT; i++) {
    SAB_Profile_Counter * counter = &sab_profile_counters[i];
    if (counter->calls == 0) continue;
    const double avg_us = ((double) counter->total_us) / ((double) counter->calls);
    const double pct = total == 0 ? 0.0 : (100.0 * (double) counter->total_us) / ((double) total);
    printf("%-32s %12" PRIu64 " %16" PRIu64 " %16.3f %9.2f%%\n",
           counter->name, counter->calls, counter->total_us, avg_us, pct);
  }
}

#endif
