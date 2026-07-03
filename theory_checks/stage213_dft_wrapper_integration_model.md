# Stage213 DFT Wrapper Integration Model

Decision: `PASS_STAGE213_DFT_WRAPPER_COMPONENT_ONLY`.

The wrapper can only improve complete SAB if the MAT-EP combined path retains enough of the Stage212 DFT-row gain after decomposition and addmul costs. Therefore complete-SAB A/B remains a separate Stage214 gate.
