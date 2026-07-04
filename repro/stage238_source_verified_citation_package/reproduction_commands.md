# Stage238 Reproduction Commands

Stage238 aggregates and probes citation/source evidence:

```bash
python scripts/build_stage238_source_verified_citation_package.py
```

Network access is used only for `source_access_probe.csv`. If a URL probe fails,
the source is not upgraded; Stage230 source verification remains the citation
policy authority until a manual/full-text check is performed.
