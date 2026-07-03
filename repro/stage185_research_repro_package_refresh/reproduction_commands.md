# Reproduction Commands

Current package rebuild:

```powershell
python scripts\build_stage185_research_repro_package_refresh.py
```

Evidence-source rebuilds:

```powershell
python scripts\build_stage178_fullmat_perbit_frontier.py
python scripts\build_stage180_mat_ep_split_probe.py
python scripts\build_stage181_sub_decomp_avx512_gate.py
python scripts\build_stage182_exact_path_negative_frontier.py
python scripts\build_stage183_addmul_dataflow_screen.py
python scripts\build_stage184_exact_route_closeout_claim_refresh.py
```

Some source rebuilds require the recorded native/remote environment and
credentials supplied through environment variables; do not write credentials
into artifacts.
