# IMAGE PLAN — TAŞKIN Repository

> Required visuals for jury-credible documentation. Each entry specifies what to show, how to frame it, and why it is necessary. Empty placeholder = jury cannot verify the claim.

---

## Category A: Hardware & Physical Build

### A1 — Node Enclosure Interior (Top-Down)
- **Show:** Open IP67 box from directly above; all components labeled (ESP32, TP4056, MT3608, Li-Po, wiring, perforated board)
- **Angle:** Directly overhead, all labels readable
- **Why:** Proves engineering quality; jury can verify BOM matches actual build
- **Filename:** `images/node_interior_topdown.jpg`

### A2 — Node Enclosure Closed (Exterior)
- **Show:** Sealed IP67 box; antenna cable gland visible; mounting points visible
- **Angle:** 3/4 perspective
- **Why:** Proves weatherproofing design; shows finished packaged unit
- **Filename:** `images/node_enclosure_exterior.jpg`

### A3 — HC-SR04 Sensor Mounted and Aimed
- **Show:** Sensor face pointing downward (or toward water surface); mounting bracket or holder visible
- **Angle:** Side view showing sensor direction relative to target surface
- **Why:** Proves correct sensor orientation; without this, jury cannot confirm measurement geometry
- **Filename:** `images/sensor_mounting.jpg`

### A4 — Hub Unit (ESP32-S3 + SD Module)
- **Show:** Hub board with SD module wired correctly; SD card inserted
- **Angle:** 3/4 perspective showing SPI wiring and SD card slot
- **Why:** Proves hub hardware matches documented wiring table
- **Filename:** `images/hub_interior.jpg`

### A5 — Wiring Close-Up: Node Power Chain
- **Show:** TP4056 → MT3608 → ESP32 connection with all wires labeled (or color-coded)
- **Angle:** Close-up macro shot, wires distinguishable
- **Why:** Proves voltage step-up chain is correctly implemented (Li-Po → 5V)
- **Filename:** `images/node_power_wiring.jpg`

---

## Category B: Field Deployment

### B1 — Node 1 in Field: Seyhan / Barajyolu Underpass
- **Show:** Installed node box; visible drainage channel or underpass; sensor aimed at water level
- **Angle:** Wide shot showing environmental context, then close-up of box on structure
- **Why:** Critical — without this, jury has no evidence that system was actually deployed. This is the highest-TRI location.
- **Filename:** `images/field_node1_barajyolu.jpg`

### B2 — Node 2 in Field: Çukurova / Turgut Özal Blv.
- **Show:** Node installed at measurement point; street-level context visible
- **Angle:** Medium shot showing both node mount and surrounding urban surface
- **Why:** Context for "impervious surface" claim in the report
- **Filename:** `images/field_node2_turgutokal.jpg`

### B3 — Node 3 in Field: Yüreğir / Sinanpaşa (Reference)
- **Show:** Reference node installed; visibly different topography than Node 1
- **Angle:** Medium shot showing higher elevation context
- **Why:** Proves reference point is physically distinct from risk nodes
- **Filename:** `images/field_node3_sinanpasa.jpg`

### B4 — Active Measurement: Water Visible Below Sensor
- **Show:** Sensor aimed at a water surface during or after rain; fill level clearly visible
- **Angle:** Sensor included in frame with water surface below
- **Why:** Direct visual proof of operational measurement context
- **Filename:** `images/sensor_measuring_water.jpg`

---

## Category C: Software & Data

### C1 — Live Dashboard Screenshot During Field Session
- **Show:** `index.html` in browser — map with colored markers, at least one node showing >50% fill, log stream active, sparklines with data
- **Angle:** Full browser window screenshot
- **Why:** Proves dashboard works in real conditions, not just localhost demo
- **Filename:** `images/dashboard_live_field.png`

### C2 — Serial Monitor During Data Reception (Arduino IDE or terminal)
- **Show:** Terminal output with `server.py` running — lines like `[Data] Node 1 → 63.5% alarm=0 @ 14:32:10`
- **Angle:** Terminal window screenshot
- **Why:** Proves serial pipeline is functional end-to-end
- **Filename:** `images/serial_bridge_output.png`

### C3 — SD Card CSV File Contents (First 20 Rows)
- **Show:** `/veri_log.csv` opened in text editor or Excel — timestamps, node IDs, fill values, alarm column
- **Angle:** Screenshot of file content
- **Why:** Proves SD logging works; validates data format claimed in README
- **Filename:** `images/sd_csv_sample.png`

### C4 — Time-Series Plot of Fill Rate per Node (All 3 Nodes, Same Axes)
- **Show:** Line chart with 3 colored lines (Node 1, 2, 3), x-axis = time, y-axis = fill %, dashed lines at 60% and 80%
- **Angle:** Full-width chart, legible legend
- **Why:** Key result visualization. Currently absent. Jury needs this to evaluate TRI claims visually.
- **Filename:** `images/field_timeseries_fill_rate.png`

### C5 — Laboratory Test Setup Photo
- **Show:** PVC pipe, HC-SR04 mounted on top, water at measured level, ruler visible
- **Angle:** Full setup in frame; ruler for scale
- **Why:** Without this, lab calibration results are unverifiable claims
- **Filename:** `images/lab_pvc_setup.jpg`

---

## Summary Checklist

| Image | Status | Critical? |
|---|---|---|
| A1 — Node interior | ☐ Missing | Yes |
| A2 — Node exterior | ☐ Missing | Yes |
| A3 — Sensor mount | ☐ Missing | Yes |
| A4 — Hub unit | ☐ Missing | Yes |
| A5 — Power chain wiring | ☐ Missing | No |
| B1 — Node 1 field (Barajyolu) | ☐ Missing | **Critical** |
| B2 — Node 2 field (Turgut Özal) | ☐ Missing | Yes |
| B3 — Node 3 field (Sinanpaşa) | ☐ Missing | Yes |
| B4 — Water visible under sensor | ☐ Missing | Yes |
| C1 — Dashboard live screenshot | ☐ Missing | **Critical** |
| C2 — Serial bridge output | ☐ Missing | No |
| C3 — CSV file contents | ☐ Missing | No |
| C4 — Time-series fill plot | ☐ Missing | **Critical** |
| C5 — Lab setup photo | ☐ Missing | Yes |

> **11 of 14 images are missing.** Without B1, B4, C1, and C4 specifically, the jury has no visual evidence of real-world operation.
