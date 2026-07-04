# Stage241 Reproduction Commands

```bash
python scripts/build_stage241_latex_compile_package.py
```

Manual equivalent inside `repro/stage241_latex_compile_package/build/`:

```bash
pdflatex -interaction=nonstopmode -halt-on-error pvw_mat_sab_scoped_draft.tex
bibtex pvw_mat_sab_scoped_draft
pdflatex -interaction=nonstopmode -halt-on-error pvw_mat_sab_scoped_draft.tex
pdflatex -interaction=nonstopmode -halt-on-error pvw_mat_sab_scoped_draft.tex
```

Decision: `PASS_STAGE241_LATEX_COMPILE_PACKAGE_READY`.
Input head: `fe28338`.
