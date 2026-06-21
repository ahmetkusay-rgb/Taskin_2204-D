# Session Log — TAŞKIN Field Test Sessions

> This file documents the start time, conditions, and metadata for each field data collection session.
> CSV timestamps (`zaman_ms`) are milliseconds since hub boot — use this log to correlate with absolute time.

---

## Session 1 — Node 1, 9 February 2026

| Field | Value |
|---|---|
| Date | 9 February 2026 |
| Start time (approx.) | 11:00 local (UTC+3) |
| End time (approx.) | 14:00 local (UTC+3) |
| Duration | ~3 hours / ~10,800 seconds |
| Node active | Node 1 |
| Location | Seyhan — Barajyolu Alt Geçidi (Underpass) |
| Coordinates | [37.022, 35.322] |
| Weather | Light rain, ~1.5 mm recorded |
| CSV file | `saha_node1_09subat_s1_11-14.csv` |
| Notes | Low-intensity rainfall session; fill stayed below the 80% alarm threshold (baseline behavior) |

---

## Session 2 — Node 1, 9 February 2026

| Field | Value |
|---|---|
| Date | 9 February 2026 |
| Start time (approx.) | 16:00 local (UTC+3) |
| End time (approx.) | 19:00 local (UTC+3) |
| Duration | ~3 hours / ~10,800 seconds |
| Node active | Node 1 |
| Location | Seyhan — Barajyolu Alt Geçidi (Underpass) |
| Coordinates | [37.022, 35.322] |
| Weather | Increasing rain, ~4.2 mm recorded |
| CSV file | `saha_node1_09subat_s2_16-19.csv` |
| Notes | Fill rate increased significantly vs Session 1; 80% alarm threshold crossed 7×, peak fill 94% |

---

## Session 3 — Node 2, 10 February 2026

| Field | Value |
|---|---|
| Date | 10 February 2026 |
| Start time (approx.) | 12:00 local (UTC+3) |
| End time (approx.) | 15:00 local (UTC+3) |
| Duration | ~3 hours / ~10,800 seconds |
| Node active | Node 2 |
| Location | Çukurova — Turgut Özal Bulvarı |
| Coordinates | [37.048, 35.279] |
| Weather | Moderate rain, ~5.8 mm recorded |
| CSV file | `saha_node2_10subat_12-15.csv` |
| Notes | High impervious surface area; frequently exceeds 60%, peak 82% (lower absolute fill than Node 1) |

---

## Session 4 — Node 3 (Reference), 11 February 2026

| Field | Value |
|---|---|
| Date | 11 February 2026 |
| Start time (approx.) | 08:00 local (UTC+3) |
| End time (approx.) | 11:00 local (UTC+3) |
| Duration | ~3 hours / ~10,800 seconds |
| Node active | Node 3 |
| Location | Yüreğir — Sinanpaşa Mahallesi (Reference) |
| Coordinates | [37.005, 35.361] |
| Weather | Heavy rain, ~9.5 mm recorded |
| CSV file | `saha_node3_11subat_08-11.csv` |
| Notes | Reference location. Despite heaviest rainfall session, fill remained <35% — confirms topographic advantage |

---

## Rainfall Source

Rainfall figures sourced from Devlet Meteoroloji İşleri Genel Müdürlüğü (MGM) Adana station records for 9–11 February 2026.
