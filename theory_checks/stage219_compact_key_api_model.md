# Stage219 Compact Key API Model

The compact key object is represented as dense public DFT rows plus explicit
row-role metadata: active rows and semantic-zero dummy rows. This preserves the
public row count required by the Stage217 pattern-only gate while exposing the
semantic skip set needed by the Stage218 finite key-object prototype.

This model is not a security proof. It only establishes that the object can be
expressed with MOSFHET polynomial allocation/conversion lifecycles and a
no-allocation hot row-role scan. Encrypted keygen, security, production noise,
compact EP integration, and complete-SAB `T_bootstrap/r` remain future gates.
