# Stage335 Reproduction Commands

```powershell
curl.exe -L -A "Mozilla/5.0" -o references\stage335_fulltext_acquisition\pdf\sharing_mask_2025_2112_tches.html https://tches.iacr.org/index.php/TCHES/article/view/12434
curl.exe -L -A "Mozilla/5.0" -o references\stage335_fulltext_acquisition\pdf\sharing_mask_2025_2112_tches.pdf https://tches.iacr.org/index.php/TCHES/article/download/12434/12162
wsl -e bash -lc "pdftotext '/mnt/d/codexprograms/whFast-Amortized-Bootstrapping/Fast-Amortized-Bootstrapping/references/stage335_fulltext_acquisition/pdf/sharing_mask_2025_2112_tches.pdf' '/mnt/d/codexprograms/whFast-Amortized-Bootstrapping/Fast-Amortized-Bootstrapping/references/stage335_fulltext_acquisition/text/sharing_mask_2025_2112_tches.txt'"
python scripts\build_stage335_source_and_compact_route.py
```

Full-text PDFs and extracted text are ignored by Git. The committed pack records
hashes, source URLs, line anchors, and claim gates only.
