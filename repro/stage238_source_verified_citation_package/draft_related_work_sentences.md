# Stage238 Draft Related-Work Sentences

- `D1_target_baseline` [FAB686_2025]: The baseline target is 2025/686-style sparse amortized bootstrapping.
  Support: exact_for_identity_and_target_scope. Allowed use: Use as the target SAB baseline identity and repository/source route.
  Guard: Do not cite it as proving our PVW/MAT optimization or our measurements.

- `D2_post_686_transform` [INCNTT25_696]: Incomplete-NTT acceleration is adjacent post-686 transform/backend work and must be separated from PVW/MAT lane batching.
  Support: partial_for_adjacent_direction. Allowed use: Use as adjacent acceleration context and a reason to separate backend/transform effects.
  Guard: Do not use it to claim PVW/MAT-SAB novelty or performance.

- `D3_common_mask_prior_art` [SHAREMASK25_2112]: Common-mask or shared-mask packed-message TFHE creates high prior-art risk for broad shared-mask novelty.
  Support: exact_for_prior_art_risk. Allowed use: Use to block broad shared-mask novelty language.
  Guard: Do not say our work is first shared-mask batching.

- `D4_batch_simd_prior_art` [MS2018_532;GPVL2023_014;DKMS2024_112;LW2023_910;LW23A_B;BATCHBOOT26]: Amortized, batch, SIMD, and systems-level bootstrapping are established prior-art axes.
  Support: exact_for_related_work_axis. Allowed use: Use to position the project as scoped 2025/686 PVW/MAT-SAB integration.
  Guard: Do not claim amortization, batching, or SIMD bootstrapping itself is new.

- `D5_pvw_and_external_product_background` [BGH2012_565;CGGI2018_421]: PVW packing and TFHE external products are background building blocks, not new contributions here.
  Support: exact_for_background_only. Allowed use: Use as background for the ciphertext/object and external-product terminology.
  Guard: Do not claim PVW packing or TFHE external products as new.

- `D6_local_selected_binary_result` [LOCAL_STAGE233_236]: Exact dense PVW/MAT-SAB improves complete-SAB T_bootstrap/r on the selected binary rows.
  Support: exact_for_recorded_binary_rows. Allowed use: Use with parameter, r, backend, run count, seed count, CI, and resource side costs.
  Guard: Do not generalize to all parameters, non-binary branches, compact route, novelty, or optimality.
