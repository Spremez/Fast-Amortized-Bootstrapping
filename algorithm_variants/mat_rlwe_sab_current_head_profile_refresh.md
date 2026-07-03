# Current-Head Profile Attribution For Exact PVW/MAT-SAB

The current exact active-buffer PVW/MAT-SAB path still spends almost all time
in the body/CMUX schedule. Active-buffer copyback is eliminated for the target
profile, post-processing remains below the implementation threshold, and the
next bounded engineering work should target MAT EP/from_DFT dataflow or native
counter attribution.
