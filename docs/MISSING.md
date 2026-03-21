# MISSING ELEMENTS — What Would Cause Jury Rejection

> These gaps directly undermine reproducibility, credibility, or completeness.

---

## 🔴 Critical (Jury Rejection Risk)

### 1. No photographs of field deployment
- All three field locations are text-described only. Zero visual evidence of installation.
- The jury cannot verify nodes were physically deployed.
- **Where in README:** Section 5 (Physical Design) — `> [IMAGE PLACEHOLDER]` markers already in place.
- **What to add:** At minimum — Node 1 at Barajyolu underpass (IP67 box on structure), and one shot showing sensor aimed at water surface.

### 2. No time-series visualization of field data
- Four CSV files (~10,800 data points) exist. No line chart shows actual fill rate trends.
- TRİ scores (81, 58, 22) are claimed with no supporting visual.
- **Where in README:** Section 10 (Test Results) — image placeholder present.
- **What to add:** 3-node fill rate line chart with 60% and 80% reference lines. Run `python analysis/tri_score.py` and extend it to output a plot.

### 3. No laboratory validation photograph
- "±4 cm accuracy" claim is unverifiable without a photo of the PVC pipe test setup.
- **Where in README:** Section 10 (Test Results) — image placeholder present.
- **What to add:** PVC pipe with sensor mounted, ruler visible for scale.

### 4. Duplicate data directories (`files/` and `data/samples/`)
- `files/` exists locally but is not committed. `data/samples/` has the committed copies.
- **Fix:** Add `files/` to `.gitignore` explicitly.

---

## 🟠 High (Significantly Weakens Credibility)

### 5. No wiring diagram image
- `docs/Devre_Semalari.md` has tables only. `şemalar.fzz` is in the working directory but not committed.
- **Where in README:** Section 6 (Wiring) — image placeholder present.
- **Fix:** Commit `şemalar.fzz` to `docs/`. Export PNG from Fritzing and place in `images/`.

### 6. No RTC — timestamps are `millis()` relative values
- CSV timestamps are ms since boot, not wall clock. Cannot verify "11:00–14:00" claims from CSV directly.
- **Fix:** Document explicitly in README Section 9 (Usage → SD Card Data). *(Already noted in current README.)*

### 7. No reproducibility proof beyond Windows/author's machine
- `SERIAL_PORT = "COM12"` is hardcoded in `server.py`. No Linux/macOS test documented.
- **Fix:** Document tested OS and Python version in README Section 8.

### 8. No error rate or packet loss count from field sessions
- ESP-NOW reliability in field conditions (buildings, rain) is never characterized.
- **Fix:** Add packet counter to hub firmware. Report drop rate in README Section 10.

---

## 🟡 Medium (Documentation Gaps)

### 9. Node names were inconsistent — FIXED
- Node 1 = Barajyolu, Node 3 = Referans/Sinanpaşa now consistent across all docs.

### 10. TRİ had no reproducible implementation — FIXED
- `analysis/tri_score.py` added. Reads CSVs, computes and prints TRİ scores.

### 11. No requirements for Arduino IDE version
- `requirements.txt` only covers Python. Arduino IDE version, ESP32 board package version undocumented.
- **Fix:** Expand README Section 8.1 with exact Arduino IDE version (2.x) and board package version tested.

### 12. Battery life was undocumented — FIXED
- Runtime characterized from field test and added to README Section 11.
