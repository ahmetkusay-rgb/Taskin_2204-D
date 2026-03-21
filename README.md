# TAŞKIN — Urban Flood Level Monitoring System

<div align="center">

![Platform](https://img.shields.io/badge/Platform-ESP32-blue?logo=espressif)
![Protocol](https://img.shields.io/badge/Wireless-ESP--NOW-orange)
![Python](https://img.shields.io/badge/Bridge-Python%203.8+-3776AB?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Pilot](https://img.shields.io/badge/Pilot%20Site-Adana%2C%20Turkey-red)

**Low-cost, wireless sensor network for real-time urban stormwater level monitoring and flood risk indexing.**

</div>

---

## 1. Project Title

**TAŞKIN: Kentsel Yağmur Suyu Hatları İçin Düşük Maliyetli Veri Toplama ve Planlama Destek Sistemi**
*(TAŞKIN: Low-Cost Data Collection and Planning Support System for Urban Stormwater Channels)*

---

## 2. Project Overview

### Problem

Urban stormwater drainage systems in cities like Adana, Turkey fail silently — surface flooding recurs at the same intersections and underpasses after every storm, yet municipalities have **no continuous, local-scale water level data** to prioritize infrastructure repairs. Flood risk management relies on post-incident reports rather than sensor evidence.

### What This System Does

TAŞKIN deploys a multi-node wireless sensor network that continuously measures water fill level (as a percentage of channel depth) at multiple urban measurement points, transmits data wirelessly to a central hub, logs it to an SD card, and streams it live to a map-based web dashboard.

The system's output is not raw sensor readings — it produces a **TAŞKIN Risk Index (TRİ)**, a composite 0–100 score per measurement point derived from:
- Mean fill rate
- Maximum fill rate
- Time above 80% threshold
- Threshold crossing frequency
- Fill rise speed (%20→%80 transition time)

This transforms collected data into **decision support output** for infrastructure planning.

### Technical Scope

| Parameter | Value |
|---|---|
| Nodes deployed | 3 |
| Sampling rate | 1 Hz (1 measurement/second/node) |
| Wireless range (ESP-NOW) | ~200 m open air |
| Measurement accuracy | ±4 cm (HC-SR04) |
| Lab validation | 7,200 seconds (PVC tube) |
| Field test | 10,800 seconds over 3 days, Adana, Feb 2026 |

---

## 3. System Architecture

The system has four layers:

```
┌──────────────────────────────────────────────────────────────┐
│                     SENSING LAYER                            │
│                                                              │
│  [Node 1]         [Node 2]         [Node 3]                  │
│  ESP32-WROOM      ESP32-WROOM      ESP32-WROOM               │
│  HC-SR04          HC-SR04          HC-SR04                   │
│  Li-Po + TP4056   Li-Po + TP4056   Li-Po + TP4056           │
└────────────────────────┬─────────────────────────────────────┘
                         │ ESP-NOW broadcast (no WiFi required)
                         │ payload: {node_id, fill_pct, alarm}
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                      HUB LAYER                               │
│                  ESP32-S3 + SD Card                          │
│  - Receives ESP-NOW packets from all nodes                   │
│  - Validates and clamps payload values                       │
│  - Writes timestamped CSV to SD card                         │
│  - Outputs comma-delimited lines via USB Serial              │
└────────────────────────┬─────────────────────────────────────┘
                         │ USB Serial (115200 baud)
                         │ format: node_id,fill_pct,alarm
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                    BRIDGE LAYER (PC)                         │
│                    server.py (Python)                        │
│  - Reads serial port (auto-detect or manual COM port)        │
│  - Parses and validates each line                            │
│  - Broadcasts JSON payload via WebSocket (ws://localhost:8765)│
│  - Serves index.html via HTTP (http://localhost:8080)        │
└────────────────────────┬─────────────────────────────────────┘
                         │ WebSocket JSON stream
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                  VISUALIZATION LAYER                         │
│                    index.html                                │
│  - Leaflet satellite map with color-coded markers           │
│  - Sparkline fill history charts per node                   │
│  - Live log stream with node-specific color coding          │
│  - SD write indicator & WebSocket connection status         │
└──────────────────────────────────────────────────────────────┘
```

> **[IMAGE PLACEHOLDER: System Architecture Block Diagram — full hardware signal flow from sensor to dashboard]**

### Data Flow Summary

1. HC-SR04 measures distance from sensor to water surface → converted to fill % using `map(distance, MAX_DEPTH, 0, 0, 100)`
2. Node broadcasts a 3-field struct over ESP-NOW to all peers (broadcast MAC `FF:FF:FF:FF:FF:FF`)
3. Hub ESP32-S3 receives the struct, validates `node_id` (1–10) and `fill_pct` (0.0–100.0), logs to SD, writes to Serial
4. `server.py` reads Serial, broadcasts JSON `{"type":"data", "node_id":N, "doluluk_pct":X, "alarm":Y, "time":"..."}` over WebSocket
5. `index.html` receives JSON, updates map marker color, sparkline, and log table in real time

---

## 4. Hardware Components

### Hub Unit (1×)

| Component | Part | Role |
|---|---|---|
| Microcontroller | ESP32-S3-N16R8 | Receives ESP-NOW packets, logs to SD, outputs Serial |
| Storage module | SPI Micro SD Card Module | Bridges SD card to ESP32 SPI bus |
| Storage | 16 GB Micro SD Card | Stores timestamped CSV log file |

### Sensor Nodes (3×, identical per node)

| Component | Part | Role |
|---|---|---|
| Microcontroller | ESP32-WROOM-32U | Drives sensor, runs ESP-NOW, manages alarm |
| Ultrasonic sensor | HC-SR04 | Non-contact water surface distance: range 2–400 cm, ±3 mm |
| Battery | 3.7V 1800 mAh Li-Po | Field power source (no mains required) |
| Charger | TP4056 module | Li-Po charge management with overcharge protection |
| Boost converter | MT3608 | Steps 3.7V battery up to stable 5V for ESP32/sensor |
| Antenna | GSM external antenna + IPEX–SMA cable | Extends ESP-NOW range through enclosure wall |
| Enclosure | 11×11×7cm IP67 thermoplastic box | Weatherproofs electronics for outdoor deployment |
| Moisture control | Silica gel sachet | Prevents internal condensation |
| Mounting | Plastic cable ties | Attaches enclosure to structure |

### Why ESP-NOW Instead of WiFi/LoRa?

ESP-NOW is chosen because:
- **No WiFi infrastructure required** in target locations (street underpasses, drainage inlets)
- **Sub-10ms latency**, adequate for 1 Hz sampling
- **Native to ESP32**, no additional hardware cost
- **Broadcast mode** means no peer address configuration per deployment

---

## 5. Physical Design

Each node is enclosed in an **IP67-rated 11×11×7 cm thermoplastic box**. The HC-SR04 sensor is mounted to point **downward into the drainage channel or road underpass** through a sealed port or from above the opening. The antenna exits through a cable gland to ensure RF propagation outside the metal-free plastic enclosure.

Internal layout: ESP32 → breadboard-on-perforated plate → TP4056 → MT3608 → all GNDs common. Wiring kept short to minimize noise on ECHO signal.

> **[IMAGE PLACEHOLDER: Interior of node enclosure — top-down view showing ESP32, TP4056, MT3608, and Li-Po with labeled wire routes]**
> **[IMAGE PLACEHOLDER: Close-up of HC-SR04 sensor mounted and aimed at water surface or drainage inlet]**
> **[IMAGE PLACEHOLDER: Full node enclosure closed, showing cable gland and antenna exiting IP67 box]**
> **[IMAGE PLACEHOLDER: Node mounted in field at Barajyolu underpass — shows real deployment context]**

---

## 6. Wiring / Connections

### Hub: ESP32-S3 ↔ SD Card Module

| SD Module Pin | ESP32-S3 GPIO | Notes |
|---|---|---|
| GND | GND | Common ground |
| VCC | 5V | Module powered from USB |
| MISO | GPIO 13 | SPI data in |
| MOSI | GPIO 11 | SPI data out |
| SCK | GPIO 12 | SPI clock |
| CS | GPIO 10 | Chip select (active LOW) |

> **Note:** Pins differ from the ESP-IDF defaults — custom `SPI.begin(SCK, MISO, MOSI, CS)` call required.

### Node: ESP32 ↔ HC-SR04 ↔ Power Chain

| Signal | From | To | Notes |
|---|---|---|---|
| TRIG | GPIO 5 | HC-SR04 TRIG | 10 µs HIGH pulse |
| ECHO | HC-SR04 ECHO | GPIO 18 via voltage divider | HC-SR04 outputs 5V logic — divider brings to 3.3V |
| VCC (sensor) | Boost 5V out | HC-SR04 VCC | Sensor requires 5V |
| VCC (ESP32) | Boost 5V out | ESP32 VIN | Also 5V |
| GND | Common | All GNDs | Single shared ground bus |
| BAT+ | Li-Po (+) | TP4056 B+ | Charge input |
| OUT+ | TP4056 OUT+ | MT3608 VIN+ | Regulated charge to boost |

**Alarm reset button:** GPIO 25, `INPUT_PULLUP`. When pressed LOW, overrides alarm flag to 0 for current cycle.

> **[IMAGE PLACEHOLDER: Hand-drawn or Fritzing wiring diagram of node — full labeled schematic]**
> *(Fritzing source file: `docs/semalar.fzz`)*

---

## 7. Software Structure

```
TASKIN/
├── firmware/
│   ├── node_21.02/
│   │   └── node_21.02.ino       # Sensor node firmware
│   └── merkez_10.03/
│       └── merkez_10.03.ino     # Hub firmware
├── server.py                    # Python serial→WebSocket bridge
├── index.html                   # Web dashboard (single file)
├── data/
│   └── samples/                 # Field test CSV logs
│       ├── saha_node1_09subat_s1_11-14.csv
│       ├── saha_node1_09subat_s2_16-19.csv
│       ├── saha_node2_10800.csv
│       └── saha_node3_11subat_08-11.csv
├── docs/
│   ├── Devre_Semalari.md        # Pin connection tables
│   └── sistem_semasi.png        # System diagram image
├── Malzeme_Listesi.xlsx         # Bill of materials
├── requirements.txt
├── .gitignore
└── README.md
```

### `node_21.02.ino` — Sensor Node Firmware

Runs on each ESP32-WROOM field unit.

- Configures HC-SR04 pins, button pin (PULLUP), and ESP-NOW broadcast peer
- `mesafeOlc()`: non-blocking ultrasonic pulse, returns distance in cm or −1 on timeout
- `loop()`: measures → maps to fill % → evaluates alarm threshold → packs into `veri_paketi` struct → `esp_now_send()` → 1000 ms delay
- Button (GPIO 25) read in same loop: if LOW, zero the alarm flag for that cycle

### `merkez_10.03.ino` — Hub Firmware

Runs on ESP32-S3 hub connected to PC via USB.

- Initializes SD via custom SPI bus (`SPI.begin(12, 13, 11, 10)`)
- Creates `/veri_log.csv` with header row if file does not exist
- `OnDataRecv()` callback: validates node_id (1–10), clamps fill to 0–100, checks alarm is 0 or 1 — drops malformed packets silently
- Writes `timestamp_ms,node_id,fill_pct,alarm` to SD
- Prints `node_id,fill_pct,alarm` to Serial (read by `server.py`)
- Prints `SD_OK,node_id` line after each successful SD write

### `server.py` — Bridge

Runs on PC, connects hub to browser dashboard.

- `find_esp_port()`: auto-detects ESP32 by matching "cp210", "ch340", "uart", "esp" in port descriptions
- `serial_reader()`: async coroutine reading lines from Serial port in thread executor
- Parses `SD_OK,N` lines → broadcasts `{"type":"sd_log", ...}` JSON
- Parses `id,pct,alarm` lines → validates ranges (node_id 1–10, pct −10 to 200) → clamps pct to 0–100 → broadcasts `{"type":"data", ...}` JSON
- `ws_handler()`: manages WebSocket client set; broadcast to all connected browsers
- HTTP server (port 8080): serves `index.html` from script directory
- Auto-reconnects to Serial after disconnect (3-second retry loop)

### `index.html` — Dashboard

Single-file browser application (no build step required).

- Leaflet + ESRI satellite tiles: interactive map centered on Adana (37.0°N, 35.32°E)
- Custom SVG markers per node, color by fill level: green (<50%), orange (50–80%), red (>80%)
- Hover tooltip with sparkline showing last N readings per node
- Right panel: 3 node cards with live fill %, time-since-last-packet, alarm badge
- Bottom-right sparkline charts (60-point rolling history per node)
- WebSocket reconnects automatically every 3 seconds on disconnect

---

## 8. Installation & Setup

### 8.1 Arduino — Firmware Upload

**Required Board Package:**
- In Arduino IDE: *File → Preferences → Additional Boards Manager URLs* → add:
  `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
- Install: *Tools → Board Manager* → search "esp32" → install `esp32 by Espressif Systems ≥ 2.0`

**Required Libraries:** All included with ESP32 core — no external library install needed.
- `WiFi.h`, `esp_now.h`, `SD.h`, `SPI.h`

**Uploading Node Firmware:**
1. Open `firmware/node_21.02/node_21.02.ino` in Arduino IDE
2. Set `NODE_ID` (1–10, unique per device), `TANK_YUKSEKLIK_CM` (channel depth in cm), `ALARM_THRESHOLD` (default 80)
3. *Tools → Board* → select **ESP32 Dev Module**
4. *Tools → Port* → select the COM port for that ESP32
5. Click **Upload**

**Uploading Hub Firmware:**
1. Open `firmware/merkez_10.03/merkez_10.03.ino`
2. Insert formatted SD card
3. *Tools → Board* → select **ESP32S3 Dev Module**
4. *Tools → Port* → select hub COM port
5. Click **Upload**

### 8.2 Python — Bridge Server

```bash
pip install -r requirements.txt

# Auto-detect COM port:
python server.py

# Manual port:
python server.py --port COM12
python server.py --port /dev/ttyUSB0
```

### 8.3 Dashboard

While `server.py` is running, open in any browser:
```
http://127.0.0.1:8080/index.html
```

No build step. No NPM. No dependencies beyond a browser.

---

## 9. Usage

### Startup Sequence

1. Power all sensor nodes (battery or USB)
2. Connect hub ESP32-S3 to PC via USB
3. Run: `python server.py --port COM12`
4. Open: `http://127.0.0.1:8080/index.html`
5. Observe: nodes appear on map within ~5 seconds as ESP-NOW packets arrive

### Runtime Behavior

- **Map markers** update color in real time: green/orange/red based on fill %
- **SD indicator** (top bar) flashes on every SD write confirmation
- **Log stream** (right panel) appends every incoming packet with timestamp and node color
- **Sparkline graphs** scroll with newest data on the right

### SD Card Data

After a session, eject the SD card. File `/veri_log.csv` contains:
```
zaman_ms,node_id,doluluk,alarm
12500,1,63.5,0
13510,2,81.2,1
SD_OK lines are NOT written to SD — they are bridge status only
```

---

## 10. Test Results

### Laboratory Validation (Controlled)

**Setup:** 100 cm-deep PVC pipe, water level raised and lowered over 2 hours (7,200 samples per node). No wind, no surface turbulence.

**Sensor accuracy:** ±4 cm deviation from manual reference measurements — within HC-SR04 spec. No systematic bias observed.

**Threshold behavior verified:**

| Node | Mean Fill (%) | Max Fill (%) | Time >60% (s) | Time >80% (s) |
|---|---|---|---|---|
| Node 1 | 51 | 92 | 318 | 102 |
| Node 2 | 36 | 74 | 124 | 39 |
| Node 3 (ref.) | 15 | 29 | 0 | 0 |

**Fill rise speed** (20%→80%): Node 1 = 19 s, Node 2 = 26 s, Node 3 = did not reach 60%.

**Connectivity:** Zero packet loss during 2-hour lab session. Reconnection after simulated disconnect: automatic, <3 seconds.

### Field Test (Adana, Feb 9–11, 2026)

**Conditions:** Real urban drainage inlets; variable rainfall from 1.5 mm (light) to 9.5 mm (heavy) per session.

| Date | Node | Location | Rainfall | Duration |
|---|---|---|---|---|
| Feb 9 | Node 1 | Seyhan – Barajyolu | ~1.5 mm | 3 h |
| Feb 9 | Node 1 | Seyhan – Barajyolu | ~4.2 mm | 3 h |
| Feb 10 | Node 2 | Çukurova – Turgut Özal | ~5.8 mm | 3 h |
| Feb 11 | Node 3 | Yüreğir – Sinanpaşa | ~9.5 mm | 3 h |

**Field statistics:**

| Node | Mean (%) | Max (%) | StdDev | Variance | Time >80% (s) | >80% count |
|---|---|---|---|---|---|---|
| Node 1 | 63 | 94 | 18.5 | 342.2 | 168 | 7 crossings |
| Node 2 | 42 | 76 | 14.8 | 219.0 | 52 | 3 crossings |
| Node 3 | 18 | 34 | 6.2 | 38.4 | 0 | 0 |

**TRİ Scores (equal-weight composite, min-max normalized):**

| Node | TRİ Score | Risk Level |
|---|---|---|
| Node 1 — Barajyolu | **81** | 🔴 Critical |
| Node 2 — Turgut Özal | **58** | 🟠 High |
| Node 3 — Sinanpaşa | **22** | 🟢 Low |

> **[IMAGE PLACEHOLDER: Screenshot of live dashboard during field session — map markers colored, log stream active, sparklines showing data]**
> **[IMAGE PLACEHOLDER: Time-series fill rate plot for all 3 nodes from field CSV data]**

---

## 11. Limitations & Future Improvements

### Current Weaknesses

| Weakness | Impact |
|---|---|
| HC-SR04 is not weatherproof | Surface turbulence and rain droplets on sensor face introduce noise spikes |
| NODE_ID is hardcoded per flash | Deploying >1 node requires separate Arduino upload per device — no runtime ID assignment |
| No network timestamp synchronization | Node timestamps are `millis()` — hub has no RTC, so CSV timestamps are relative uptime, not wall clock |
| Battery life not characterized | No measured runtime on 1800 mAh Li-Po at 1 Hz continuous sampling |
| Single-hop ESP-NOW | All nodes must be within ~200 m of hub — no mesh, no relay |
| 3-day field test only | No longitudinal data; seasonal variability uncharacterized |
| No rain gauge integration | Fill rise rate cannot be correlated with precise precipitation data |
| Dashboard requires active PC | No standalone operation — hub must be connected to a running Python process |

### Recommended Next Steps

1. Replace HC-SR04 with waterproofed ultrasonic (e.g. MaxBotix MB7389) or radar sensor (e.g. Vega Puls C 11)
2. Add DS3231 RTC module to hub for absolute timestamps
3. Implement OTA NODE_ID provisioning via BLE or serial command
4. Add solar panel + charge controller for permanent field deployment
5. Integrate MGM (national meteorology) API for rainfall correlation
6. Extend field test to full rainy season (October–March in Adana)
7. Add MQTT or HTTP POST to upload data to cloud without manual SD retrieval

---

## 12. Conclusion

TAŞKIN demonstrates that a sub-$30 per-node sensor system can produce **statistically differentiated, multi-point fill rate data** suitable for infrastructure risk prioritization. The composite TRİ metric enables location ranking beyond single-variable thresholds.

The system correctly identified Node 1 (Barajyolu underpass) as the highest-risk point across all measured parameters — consistent with known local flooding history. The architecture is intentionally modular: nodes are independent, the hub is passive, and the browser dashboard only needs a WebSocket feed.

Primary constraint is the 3-day field window and absence of long-term or multi-season data. The system's value for planning purposes increases proportionally with data duration — a minimum 3-month continuous dataset is required for meaningful trend extraction.

---

## License

MIT License. See [LICENSE](LICENSE).

---

<div align="center">
<sub>TAŞKIN Project · Adana Pilot Site · 2026</sub>
</div>
