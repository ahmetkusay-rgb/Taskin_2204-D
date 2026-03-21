# TAŞKIN — Urban Flood Level Monitoring System

<div align="center">

> 🇬🇧 **English** | [🇹🇷 Türkçe için tıklayın → README_TR.md](README_TR.md)

![Platform](https://img.shields.io/badge/Platform-ESP32-blue?logo=espressif)
![Protocol](https://img.shields.io/badge/Wireless-ESP--NOW-orange)
![Python](https://img.shields.io/badge/Bridge-Python%203.8+-3776AB?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Pilot](https://img.shields.io/badge/Pilot%20Site-Adana%2C%20Turkey-red)

**Low-cost, wireless sensor network for real-time urban stormwater level monitoring and flood risk indexing.**

</div>

---

## 1. Project Title

**TAŞKIN: Low-Cost Data Collection and Planning Support System for Urban Stormwater Channels**
*(Kentsel Yağmur Suyu Hatları İçin Düşük Maliyetli Veri Toplama ve Planlama Destek Sistemi)*

---

## 2. Project Overview

### Problem

Urban stormwater drainage systems in cities like Adana, Turkey fail silently. Surface flooding recurs at the same intersections and underpasses after every storm, yet municipalities have **no continuous, local-scale water level data** to prioritize infrastructure repairs. Flood risk management relies on post-incident reports rather than sensor evidence.

### What This System Does

TAŞKIN deploys a multi-node wireless sensor network that continuously measures water fill level (as a percentage of channel depth) at multiple urban measurement points, transmits data wirelessly to a central hub, logs it to an SD card, and streams it live to a map-based web dashboard.

The system's key output is not raw sensor readings — it produces a **TAŞKIN Risk Index (TRİ)**, a composite 0–100 score per measurement point derived from:
- Mean fill rate
- Maximum fill rate
- Time above 80% threshold
- Threshold crossing frequency
- Fill rise speed (20%→80% transition time)

This transforms collected data into **decision-support output** for infrastructure planning.

### Technical Scope

| Parameter | Value |
|---|---|
| Nodes deployed | 3 |
| Sampling rate | 1 Hz (1 sample/second/node) |
| Wireless protocol | ESP-NOW (no WiFi infrastructure required) |
| Measurement accuracy | ±4 cm (HC-SR04) |
| Lab validation | 7,200 seconds (PVC pipe, controlled) |
| Field test | 10,800 seconds over 3 days, Adana, Feb 2026 |
| Battery runtime (measured) | 10–12 hours @ Always-On mode |

---

## 3. System Architecture

The system has four layers:

```
┌────────────────────────────────────────────────────────────────┐
│                        SENSING LAYER                           │
│                                                                │
│  [Node 1 — Barajyolu]  [Node 2 — Turgut Özal]  [Node 3 — Ref] │
│  ESP32-WROOM-32U        ESP32-WROOM-32U          ESP32-WROOM   │
│  HC-SR04                HC-SR04                  HC-SR04       │
│  Li-Po + TP4056 + MT3608                                       │
└────────────────────┬───────────────────────────────────────────┘
                     │ ESP-NOW broadcast
                     │ struct: {node_id, fill_pct, alarm}
                     ▼
┌────────────────────────────────────────────────────────────────┐
│                         HUB LAYER                              │
│              ESP32-S3-N16R8 + SPI SD Card Module               │
│  - Receives and validates ESP-NOW packets                      │
│  - Clamps fill_pct to 0–100, drops malformed packets           │
│  - Logs timestamped CSV to SD card                             │
│  - Outputs comma-delimited lines to USB Serial                 │
└────────────────────┬───────────────────────────────────────────┘
                     │ USB Serial @ 115200 baud
                     │ format: node_id,fill_pct,alarm
                     ▼
┌────────────────────────────────────────────────────────────────┐
│                      BRIDGE LAYER (PC)                         │
│                       server.py (Python)                       │
│  - Reads serial port (auto-detect or --port flag)              │
│  - Parses, validates, and clamps each incoming line            │
│  - Broadcasts JSON over WebSocket (ws://localhost:8765)        │
│  - Serves index.html via HTTP (http://localhost:8080)          │
└────────────────────┬───────────────────────────────────────────┘
                     │ WebSocket JSON stream
                     ▼
┌────────────────────────────────────────────────────────────────┐
│                   VISUALIZATION LAYER                          │
│                       index.html                               │
│  - Leaflet satellite map, color-coded markers per node         │
│  - 60-point sparkline fill history per node                    │
│  - Live log stream, SD write indicator, WS status             │
└────────────────────────────────────────────────────────────────┘
```

> **[IMAGE PLACEHOLDER — Section 3]:** System architecture block diagram (hardware signal flow from sensor to dashboard)

### Data Flow

1. HC-SR04 measures distance to water surface → converted to fill% via `map(distance, MAX_DEPTH, 0, 0, 100)`
2. Node broadcasts `{node_id, fill_pct, alarm}` struct via ESP-NOW to broadcast MAC `FF:FF:FF:FF:FF:FF`
3. Hub ESP32-S3 validates (node_id 1–10, fill_pct 0–100), logs to SD, writes to Serial
4. `server.py` parses Serial, broadcasts `{"type":"data", "node_id":N, "doluluk_pct":X, "alarm":Y, "time":"..."}` over WebSocket
5. `index.html` receives JSON, updates map marker color, sparkline, and log table in real time

---

## 4. Hardware Components

### Hub Unit (1×)

| Component | Part | Technical Role |
|---|---|---|
| Microcontroller | ESP32-S3-N16R8 | Receives ESP-NOW, runs SD logging, outputs USB Serial |
| SD card module | SPI Micro SD Module | Interfaces SD card to ESP32-S3 SPI bus |
| Storage | 16 GB Micro SD Card | Stores `/veri_log.csv` continuously |

### Sensor Nodes (3×, identical)

| Component | Part | Technical Role |
|---|---|---|
| Microcontroller | ESP32-WROOM-32U | Drives HC-SR04, manages ESP-NOW, evaluates alarm |
| Ultrasonic sensor | HC-SR04 | Non-contact distance: 2–400 cm, ±3 mm resolution |
| Battery | 3.7V 1800 mAh Li-Po | Field power — no mains required |
| Charger | TP4056 module | Li-Po charge management with overcharge protection |
| Boost converter | MT3608 | Steps 3.7V → stable 5V for ESP32 and sensor |
| Antenna | GSM external + IPEX–SMA cable | Extends ESP-NOW range through enclosure wall |
| Enclosure | 11×11×7 cm IP67 thermoplastic box | Weatherproofs electronics for outdoor field use |
| Moisture control | Silica gel sachet | Prevents internal condensation |
| Mounting | Plastic cable ties | Fixes enclosure to structure |

### Why ESP-NOW Over WiFi or LoRa?

ESP-NOW is chosen because:
- **No WiFi infrastructure** exists at target locations (street underpasses, drainage inlets)
- **Sub-10ms latency**, adequate for 1 Hz sampling
- **Native to ESP32**, zero additional hardware cost
- **Broadcast mode**: no peer address configuration needed per deployment — any hub receives any node

---

## 5. Physical Design

Each node is enclosed in an **IP67-rated 11×11×7 cm thermoplastic box**. The HC-SR04 sensor is oriented to point **downward into the drainage channel or road underpass** through a sealed port. The antenna exits through a cable gland to ensure RF propagation outside the enclosure.

Internal layout: ESP32 → perforated PCB board → TP4056 → MT3608 → shared GND bus. Wiring kept short to minimize noise on the ECHO signal line.

> **[IMAGE PLACEHOLDER — Section 5a]:** Interior of node enclosure — top-down view, all components visible and labeled
> **[IMAGE PLACEHOLDER — Section 5b]:** HC-SR04 sensor aimed at water surface, showing mounting geometry
> **[IMAGE PLACEHOLDER — Section 5c]:** Sealed IP67 enclosure exterior with antenna and cable gland
> **[IMAGE PLACEHOLDER — Section 5d]:** Node 1 mounted in field at Barajyolu underpass

---

## 6. Wiring / Connections

### Hub: ESP32-S3 ↔ SD Card Module

| SD Module Pin | ESP32-S3 GPIO | Notes |
|---|---|---|
| GND | GND | Common ground |
| VCC | 5V | Module powered from USB |
| MISO | GPIO 13 | SPI data input |
| MOSI | GPIO 11 | SPI data output |
| SCK | GPIO 12 | SPI clock |
| CS | GPIO 10 | Chip select (active LOW) |

> **Note:** These are non-default SPI pins for ESP32-S3. The firmware uses `SPI.begin(12, 13, 11, 10)` explicitly.

### Node: ESP32 ↔ HC-SR04 ↔ Power Chain

| Signal | From | To | Notes |
|---|---|---|---|
| TRIG | GPIO 5 | HC-SR04 TRIG | 10 µs HIGH pulse initiates measurement |
| ECHO | HC-SR04 ECHO | GPIO 18 (via voltage divider) | HC-SR04 outputs 5V logic — divider to 3.3V required |
| VCC (sensor) | MT3608 5V out | HC-SR04 VCC | Sensor requires 5V supply |
| VCC (ESP32) | MT3608 5V out | ESP32 VIN | Same 5V rail |
| GND | Common bus | All components | Single shared ground |
| BAT+ | Li-Po (+) | TP4056 B+ | Charge input |
| OUT+ | TP4056 OUT+ | MT3608 VIN+ | Regulated charge to boost converter |

**Alarm reset button:** GPIO 25 (`INPUT_PULLUP`). Reads LOW during loop → zeros alarm flag for that cycle.

> **[IMAGE PLACEHOLDER — Section 6]:** Wiring diagram (Fritzing export or hand-drawn schematic)
> *(Fritzing source: `docs/şemalar.fzz`)*

---

## 7. Software Structure

```
TASKIN/
├── firmware/
│   ├── node_21.02/
│   │   └── node_21.02.ino       # Sensor node firmware (ESP32-WROOM)
│   └── merkez_10.03/
│       └── merkez_10.03.ino     # Hub firmware (ESP32-S3)
├── server.py                    # Python serial → WebSocket bridge
├── index.html                   # Single-file web dashboard
├── analysis/
│   └── tri_score.py             # TRİ index calculator from CSV data
├── data/
│   └── samples/                 # Field test CSV logs (4 files, ~10,800 rows each)
├── docs/
│   ├── Devre_Semalari.md        # Pin connection tables
│   ├── CODE_REVIEW.md           # Code quality review
│   ├── MISSING.md               # Missing elements checklist
│   └── IMAGE_PLAN.md            # Required photo/visual checklist
├── Malzeme_Listesi.xlsx         # Bill of materials
├── LICENSE
├── requirements.txt
└── README.md / README_TR.md
```

### `node_21.02.ino` — Sensor Node

- Configures HC-SR04 pins, alarm reset button (PULLUP), and ESP-NOW broadcast peer (`FF:FF:FF:FF:FF:FF`)
- `mesafeOlc()`: sends 10 µs TRIG pulse, reads ECHO duration with 60 ms timeout, converts to cm
- `loop()`: measure → map to fill% → evaluate alarm → pack struct → `esp_now_send()` → 1000 ms delay
- Button on GPIO 25: if LOW during loop, sets `alarm = 0` for that cycle

### `merkez_10.03.ino` — Hub

- Custom SPI bus init: `SPI.begin(12, 13, 11, 10)` — non-default pins required
- Creates `/veri_log.csv` with header row on first boot
- `OnDataRecv()` callback: validates node_id ∈ [1,10], clamps fill to [0,100], validates alarm ∈ {0,1}
- Logs `timestamp_ms,node_id,fill_pct,alarm` to SD; prints `node_id,fill_pct,alarm` to Serial
- Prints `SD_OK,node_id` after each successful SD write (consumed by `server.py`)

### `server.py` — Bridge

- `find_esp_port()`: auto-detects ESP32 by "cp210", "ch340", "uart", "esp" in port description
- `serial_reader()`: async coroutine reading Serial lines in thread executor
- Parses `SD_OK,N` → broadcasts `{"type":"sd_log"}` JSON
- Parses `id,pct,alarm` → validates (node_id 1–10, pct −10 to 200) → clamps [0,100] → broadcasts `{"type":"data"}` JSON
- HTTP server on port 8080 serves `index.html` from script directory
- Reconnects to Serial after disconnect with 3-second retry loop

### `index.html` — Dashboard

- Leaflet + ESRI satellite tiles; centered on Adana (37.0°N, 35.32°E)
- Custom colored markers per node: green (<50%), orange (50–80%), red (>80%)
- Hover tooltip with per-node sparkline chart
- Right panel: 3 node cards with fill%, last-packet age, alarm badge
- 60-point rolling sparklines; WebSocket auto-reconnects on disconnect

### `analysis/tri_score.py` — TRİ Calculator

- Reads all CSVs from `data/samples/`
- Computes per-node: mean fill, max fill, std dev, time above 80%, threshold crossings, fill rise duration
- Min-max normalizes all metrics across nodes
- Computes equal-weight composite TRİ score and prints ranked risk table
- Run with: `python analysis/tri_score.py`

---

## 8. Installation & Setup

### 8.1 Arduino Firmware

**Tested environment:**
- Arduino IDE 2.3.x
- ESP32 board package: `esp32 by Espressif Systems v3.x`
- OS: Windows 11

**Board package install:**
- *File → Preferences → Additional Boards Manager URLs:*
  `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
- *Tools → Board Manager* → search "esp32" → install `esp32 by Espressif Systems`

**No external library install required.** All libraries (`WiFi.h`, `esp_now.h`, `SD.h`, `SPI.h`) are included with the ESP32 board package.

**Node firmware upload:**
1. Open `firmware/node_21.02/node_21.02.ino`
2. Set per-device constants:
   ```cpp
   #define NODE_ID              1    // Unique 1–10 per device
   #define TANK_YUKSEKLIK_CM  100    // Channel depth in cm
   #define ALARM_THRESHOLD     80    // Alarm threshold (%)
   ```
3. *Tools → Board* → **ESP32 Dev Module**
4. *Tools → Port* → select device COM port
5. Upload

**Hub firmware upload:**
1. Open `firmware/merkez_10.03/merkez_10.03.ino`
2. Insert formatted SD card into module
3. *Tools → Board* → **ESP32S3 Dev Module**
4. Upload

### 8.2 Python Bridge

```bash
# Python 3.8+ required
pip install -r requirements.txt

# Auto-detect ESP32 port:
python server.py

# Specify port manually:
python server.py --port COM12
python server.py --port /dev/ttyUSB0
```

### 8.3 Dashboard

While `server.py` is running:
```
http://127.0.0.1:8080/index.html
```
No build step. No npm. Single HTML file.

---

## 9. Usage

### Startup Sequence

1. Power all sensor nodes (battery or USB)
2. Connect hub ESP32-S3 to PC via USB
3. `python server.py --port COM12`
4. Open `http://127.0.0.1:8080/index.html`
5. Nodes appear on map within ~5 seconds as ESP-NOW packets arrive

### Runtime Behavior

- Map markers update color in real time: green / orange / red
- SD indicator (top bar) flashes green on each SD write confirmation
- Log stream appends every incoming packet with timestamp and node color
- Sparklines scroll with newest data on the right

### SD Card Data

After session, eject SD card. File `/veri_log.csv` contains:
```
zaman_ms,node_id,doluluk,alarm
12500,1,63.5,0
13510,2,81.2,1
```
**Note:** `zaman_ms` is milliseconds since hub boot — not wall clock time. Correlate with session start time from `server.py` terminal output for absolute timestamps.

---

## 10. Test Results

### Laboratory Validation

**Setup:** 100 cm-deep PVC pipe, water raised and lowered over 2 hours. 7,200 samples per node.

> **[IMAGE PLACEHOLDER — Section 10a]:** PVC pipe lab setup — sensor mounted, ruler for scale

**Sensor accuracy:** ±4 cm from manual reference — within HC-SR04 datasheet spec.

| Node | Mean Fill (%) | Max Fill (%) | Time >60% (s) | Time >80% (s) | Rise 20→80% (s) |
|---|---|---|---|---|---|
| Node 1 — Barajyolu | 51 | 92 | 318 | 102 | 19 |
| Node 2 — Turgut Özal | 36 | 74 | 124 | 39 | 26 |
| Node 3 — Sinanpaşa (Ref.) | 15 | 29 | 0 | 0 | — |

Zero packet loss during 2-hour lab session. Serial reconnection after simulated disconnect: <3 seconds.

### Field Test — Adana, Feb 9–11, 2026

**Conditions:** Real urban drainage locations; rainfall 1.5–9.5 mm/session.

| Date | Node | Location | Rainfall |
|---|---|---|---|
| Feb 9 AM | Node 1 | Seyhan — Barajyolu Alt Geçidi | ~1.5 mm |
| Feb 9 PM | Node 1 | Seyhan — Barajyolu Alt Geçidi | ~4.2 mm |
| Feb 10 | Node 2 | Çukurova — Turgut Özal Blv. | ~5.8 mm |
| Feb 11 | Node 3 | Yüreğir — Sinanpaşa (Ref.) | ~9.5 mm |

| Node | Mean (%) | Max (%) | StdDev | Time >80% (s) | >80% crossings |
|---|---|---|---|---|---|
| Node 1 — Barajyolu | 63 | 94 | 18.5 | 168 | 7 |
| Node 2 — Turgut Özal | 42 | 76 | 14.8 | 52 | 3 |
| Node 3 — Sinanpaşa (Ref.) | 18 | 34 | 6.2 | 0 | 0 |

**TRİ Scores** (equal-weight composite, min-max normalized — computed by `analysis/tri_score.py`):

| Node | TRİ | Risk |
|---|---|---|
| Node 1 — Barajyolu | **81** | 🔴 Critical |
| Node 2 — Turgut Özal | **58** | 🟠 High |
| Node 3 — Sinanpaşa (Ref.) | **22** | 🟢 Low |

> **[IMAGE PLACEHOLDER — Section 10b]:** Live dashboard screenshot during field session — colored markers, active log stream
> **[IMAGE PLACEHOLDER — Section 10c]:** Time-series fill rate chart for all 3 nodes (from CSV data, output of tri_score.py extended with plotting)

---

## 11. Limitations & Future Improvements

### Battery Life

Field operation was conducted in **Always-On mode** to measure system stability and data continuity.

| Component | State | Current Draw (avg.) |
|---|---|---|
| ESP32-S3 | Active (WiFi mode on) | ~80–100 mA |
| HC-SR04 | Continuous measurement | ~15 mA |
| SD card write | Active | ~20–30 mA |
| **Total** | **Always-On** | **~130–150 mA** |

**Measured runtime:** 10–12 hours on 3.7V 1800 mAh Li-Po with MT3608 boost converter, under continuous sampling and logging.

> **Next step:** Deep Sleep optimization (ESP32 light sleep between measurements at 1 Hz) is planned for the next firmware revision. Estimated sleep-mode current: ~10 mA. Projected extended runtime: 60–80 hours.

### Current Weaknesses

| Weakness | Impact |
|---|---|
| HC-SR04 is not weatherproof | Rain droplets on sensor face cause measurement spikes |
| NODE_ID hardcoded per flash | Multiple nodes require separate Arduino upload per device |
| No RTC | CSV timestamps are `millis()` — relative to boot, not wall clock |
| Single-hop ESP-NOW | All nodes must be within ~200 m of hub — no mesh or relay |
| 3-day field test only | No seasonal variability characterized |
| No rain gauge integration | Fill rise rate cannot be correlated with precise precipitation |
| PC required for dashboard | Hub must be USB-connected to a running `server.py` |

### Recommended Improvements

1. Replace HC-SR04 with waterproofed ultrasonic (MaxBotix MB7389) or radar sensor
2. Add DS3231 RTC module to hub for absolute timestamps
3. Implement ESP32 Deep Sleep with 1 Hz wake cycles for multi-day battery operation
4. Add solar panel + charge controller for permanent field deployment
5. Integrate MGM weather API for precipitation correlation
6. Extend field test to full rainy season (October–March in Adana)
7. Add MQTT/HTTP cloud upload to remove dependency on local PC

---

## 12. Conclusion

TAŞKIN demonstrates that a sub-$10 per-node sensor system can produce statistically differentiated, multi-point fill rate data suitable for infrastructure risk prioritization. The composite TRİ metric enables location ranking across multiple parameters — not just peak fill values.

The system correctly identified Node 1 (Barajyolu underpass) as the highest-risk location across all measured parameters, consistent with known local flooding history. Node 3 (Sinanpaşa, reference) showed stable low fill throughout all sessions, validating the comparative measurement design.

Primary constraint is the 3-day field window. The system's planning value increases proportionally with data duration — a minimum 3-month continuous dataset is required for meaningful trend extraction and infrastructure prioritization recommendations.

---

## License

[MIT License](LICENSE) — Copyright (c) 2026 TAŞKIN Project

---

<div align="center">
<sub>TAŞKIN Project · Adana Pilot Site · 2026</sub>
</div>
