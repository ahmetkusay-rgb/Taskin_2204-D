# MISSING ELEMENTS — What Would Cause Jury Rejection

> This is not a suggestion list. These are gaps that directly undermine reproducibility, credibility, or completeness.

---

## 🔴 Critical (Jury Rejection Risk)

### 1. No LICENSE file
- **README states MIT License** but no `LICENSE` file exists in the repository.
- A jury cannot accept legal status of the code.
- **Fix:** Add `LICENSE` file with MIT License text.

### 2. No photographs of field deployment
- All three field locations are described in text and tables. Zero visual evidence of actual installation.
- The jury has no proof nodes were physically deployed — only that code was written and data files exist.
- **Fix:** See `docs/IMAGE_PLAN.md` for required photos.

### 3. No time-series visualization of field data
- Four CSV files with ~10,800 data points exist. No chart, no plot, no figure shows the actual data shape.
- The TRİ scores (81, 58, 22) are claimed in the README with no supporting visualization.
- **Fix:** Generate a multi-node line chart from the CSV data and include in repo and README.

### 4. No laboratory validation photograph
- Lab test (PVC pipe, 7,200 samples) is described but there is no photo of the setup.
- A claim of "±4 cm accuracy" with no physical setup photo is unverifiable.
- **Fix:** See `docs/IMAGE_PLAN.md` item C5.

### 5. Duplicate data directories (`files/` and `data/samples/`)
- Original CSV files remain in `files/` (untracked, not in repo) while copies exist in `data/samples/`.
- Version history is inconsistent. A reviewer pulling the repo gets only the `data/samples/` copies.
- **Fix:** Remove `files/` from working directory. Add to `.gitignore`. Keep only `data/samples/`.

---

## 🟠 High (Significantly Weakens Credibility)

### 6. No wiring diagram image
- `docs/Devre_Semalari.md` has tables. `docs/semalar.fzz` (Fritzing file) is referenced but not committed to repo.
- A textual pin table is not a wiring diagram.
- **Fix:** Commit `semalar.fzz` to `docs/`. Export a PNG schematic from Fritzing and add to `images/`.

### 7. No RTC — timestamps are `millis()` relative values
- SD card CSV timestamps are milliseconds since boot, not wall clock.
- The report references specific time windows (11:00–14:00, etc.) that cannot be verified from the CSV files directly.
- **Fix:** Document explicitly in README that timestamps are relative. Note that correlation to clock time requires external reference (MGM data, phone camera timestamp during session).

### 8. No reproducibility proof beyond the author's machine
- `server.py` has `SERIAL_PORT = "COM12"` hardcoded. No test on Linux or macOS.
- Arduino board selection requires manual steps not visible to a third party.
- **Fix:** Add a `SETUP.md` quick-start guide. Document tested OS. State Python version tested on.

### 9. Battery life not measured
- Nodes run on 1800 mAh Li-Po. Runtime is never mentioned in the report or README.
- For field deployment credibility, this is a required specification.
- **Fix:** Measure or estimate: `(1800 mAh) / (ESP32 ~240 mA active) ≈ 7.5h`. Document it. If measured, compare.

### 10. No error rate or lost packet count from field sessions
- ESP-NOW reliability in field conditions (buildings, rain interference) is never characterized.
- "Zero packet loss in lab" is not transferable to field.
- **Fix:** Add a packet counter to hub firmware and report field reliability in README section 10.

---

## 🟡 Medium (Documentation Gaps)

### 11. Temp/scratch files committed or in working tree
- `create_bom.py`, `ekler_out.txt`, `docx_output2.txt` exist in working directory.
- **Fix:** Add these patterns to `.gitignore`. Delete from directory.

### 12. Node names inconsistent across files
- README references "Node 1 — Referans" and "Node 1 — Baraj Yolu Geçidi" in different sections.
- `index.html` has `NODE_NAMES = {1: 'Node 1 — Baraj Yolu Geçidi', ...}` but HTML cards say "Node 1 — Referans".
- **Fix:** Standardize node names across all files. In this system, Node 3 is the reference node — not Node 1.

### 13. TRİ formula is documented in README but no code implements it
- The composite scoring algorithm (TRİ) is explained mathematically in the README.
- It is computed manually from CSV data.
- No script in the repository performs this computation.
- **Fix:** Add `analysis/tri_score.py` that reads CSVs from `data/samples/` and outputs TRİ scores. This makes the academic claim reproducible.

### 14. No requirements for Arduino IDE version
- `requirements.txt` only covers Python dependencies.
- Arduino IDE version, ESP32 board package version, and any known incompatibilities are undocumented.
- **Fix:** Add an `ARDUINO_SETUP.md` or expand README section 8.1 with exact version numbers.
