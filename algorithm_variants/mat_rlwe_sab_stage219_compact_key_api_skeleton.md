# Compact Key API Skeleton

This is a repro-only MOSFHET-adjacent API skeleton.

It verifies:

- dense public row count is preserved;
- active/dummy row roles match Stage203/Stage218;
- real MOSFHET DFT lifecycle works for every generated row;
- invalid input guards are checked;
- hot role scan allocates no skeleton memory.

It does not implement encrypted keygen, security proof, production noise, SAB
integration, or any new complete-SAB speedup.
