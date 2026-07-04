# Stage239 Reproduction Commands

Stage239 retrieves BibTeX from verified routes where possible:

```bash
python scripts/build_stage239_bibtex_latex_stub.py
```

The generated `.bib` files include only fetched and parsed entries. Unresolved
sources remain in `unresolved_bibtex_todo.csv`.
