# CODE QUALITY REVIEW — TAŞKIN Repository

> Strict technical analysis. Issues are listed without softening.

---

## `node_21.02.ino` — Sensor Node Firmware

### Issues

**1. NODE_ID is a hardcoded define — no runtime identity.**
```cpp
#define NODE_ID 3
```
Every node requires a separate compiled binary. No label, no EEPROM-stored ID, no provisioning.
**Fix:** Store ID in ESP32 EEPROM or NVS. Read at boot. Allow serial command to set it.

**2. `mesafeOlc()` uses `pulseIn` with a hard 60 ms timeout but no averaging.**
A single ultrasonic reading is highly susceptible to noise from rain droplets, floating debris, or surface turbulence. One bad echo = one wrong packet sent.
**Fix:** Take 3–5 readings, discard outliers (median filter), return median.

```cpp
// Replace:
long sure = pulseIn(ECHO_PIN, HIGH, 60000);

// With: take 5 readings, return median
```

**3. `map()` used on integer `mesafe` for `float doluluk` — lossy cast.**
```cpp
float doluluk = map(mesafe, TANK_YUKSEKLIK_CM, 0, 0, 100);
```
`map()` returns `long`, implicitly cast to `float`. For a 100 cm tank this gives 1% resolution — technically acceptable but not documented.
**Fix:** Use explicit float arithmetic: `float doluluk = ((float)(TANK_YUKSEKLIK_CM - mesafe) / TANK_YUKSEKLIK_CM) * 100.0f;`

**4. No send callback — packet loss is invisible.**
`esp_now_send()` is called but no `OnDataSent` callback is registered. The node prints "Gonderildi Basarili" from the return code of `esp_now_send()`, which only indicates the send was initiated — not that the hub received it.
**Fix:** Register `esp_now_register_send_cb()` and log actual delivery status.

**5. Button debounce is a blocking `delay(300)`.**
```cpp
if (digitalRead(BUTTON_PIN) == LOW) {
    alarm = 0;
    delay(300);
}
```
Blocks the entire loop for 300 ms every button press. Minor for this use case, but incorrect pattern.
**Fix:** Track last press time with `millis()` for non-blocking debounce.

**6. No comments. Zero function-level documentation.**
A reviewer or maintainer cannot understand the intent of `mesafeOlc()` or the alarm logic without running it.
**Fix:** Add at minimum: function purpose, return value meaning, and unit (cm, %, ms).

---

## `merkez_10.03.ino` — Hub Firmware

### Issues

**1. SD pin assignments conflict with ESP-IDF SPI defaults — not documented in code.**
```cpp
#define SD_CS_PIN 10
#define SD_SCK 12
#define SD_MISO 13
#define SD_MOSI 11
```
These are non-default SPI pins for ESP32-S3. The custom `SPI.begin(SD_SCK, SD_MISO, SD_MOSI, SD_CS_PIN)` call is the only reason it works. This is not commented.
**Fix:** Add comment explaining that default SPI pins on ESP32-S3 conflict with the board layout and that custom SPI is intentional.

**2. SD failure is silent — `setup()` continues even if SD.begin() fails.**
```cpp
if (SD.begin(SD_CS_PIN)) {
    // create file
}
```
If this block is skipped (SD init failed), `sdKartaYaz()` opens a null file handle silently. No error output, no LED, no Serial warning.
**Fix:** Print `Serial.println("SD HATA")` and optionally halt if SD is required.

**3. `sdKartaYaz()` calls `SD.open()` and `dosya.close()` on every single write.**
At 1 Hz × 3 nodes = 3 file open/close cycles per second. Repeated open/close is slow and shortens SD flash lifespan.
**Fix:** Keep file handle open. Flush periodically with `dosya.flush()`.

**4. `OnDataRecv` silently drops packets without any indication.**
```cpp
if (len != sizeof(veri_paketi)) return;
if (gelen.node_id < 1 || gelen.node_id > 10) return;
```
No Serial print, no counter. In a live deployment, if a node stops transmitting, there is no visible indication at the hub.
**Fix:** Count dropped packets and print periodic diagnostic summary.

**5. `loop()` contains only `delay(1000)` — pointless.**
Hub does nothing in loop. All work is in the `OnDataRecv` callback. The delay adds artificial latency for no reason.
**Fix:** Remove delay or replace with task-appropriate logic (e.g., periodic status print).

**6. No version string, no build date, no system serial print on boot.**
A deployed device gives no indication of firmware version when connected.
**Fix:** `Serial.println("TASKIN Hub v1.0 - " + String(__DATE__));` in `setup()`.

---

## `server.py` — Python Bridge

### Issues

**1. `SERIAL_PORT = "COM12"` hardcoded at line 16.**
```python
SERIAL_PORT = "COM12"
```
Any developer on a different machine or OS fails immediately. Auto-detection exists (`find_esp_port()`) but the hardcoded fallback overrides it.
**Fix:** Default to `None`. Document that `--port` flag is the recommended path.

**2. `connected_clients` is a bare `set()` — no thread safety.**
The WebSocket handler modifies `connected_clients` from async coroutines while `broadcast()` iterates it. In Python 3.10+ this raises `RuntimeError: Set changed size during iteration` under concurrent connections.
**Fix:** Use `asyncio.Lock()` or copy the set before iteration: `await asyncio.gather(*[c.send(msg) for c in set(connected_clients)], ...)`.

**3. Doluluk validation accepts -10 to 200 before clamping to 0–100.**
```python
if doluluk_pct < -10 or doluluk_pct > 200:
```
Why accept −10? Why accept 200? Documenting the intent (absorb small sensor noise before clamping) is necessary. The current code will silently pass values like −9.5% to the dashboard.
**Fix:** Document the rationale. Consider tightening to −5 / 110 with a comment.

**4. No logging to file — all output is `print()` to stdout.**
In field deployment, server output is lost when terminal closes.
**Fix:** Use Python `logging` module with both stream and file handlers. Rotate daily.

**5. `find_esp_port()` returns the first available port if no ESP keyword matches.**
```python
if ports:
    return ports[0].device
```
On a machine with any other USB serial device, this may return the wrong port silently.
**Fix:** Return `None` if no ESP-matching port found. Print warning. Do not guess.

---

## `index.html` — Dashboard

### Issues

**1. `NODE_COORDS` and `NODE_NAMES` are hardcoded — Adana-specific.**
```javascript
const MAP_CENTER = [37.0, 35.32];
const NODE_COORDS = { 1: [37.022, 35.322], ... };
```
Redeploying in a different city requires editing HTML source.
**Fix:** Move to a config object read from a JSON file served alongside `index.html`, or expose via server.py startup.

**2. No error boundary for malformed WebSocket messages.**
If the WebSocket sends anything non-JSON (e.g., debug print from firmware), `JSON.parse()` throws and the entire message handler crashes silently.
**Fix:** Wrap `JSON.parse()` in `try/catch`.

**3. `MAX_LOG_ROWS = 200` but no indication in UI when log is being trimmed.**
The log silently drops old rows. A jury reviewer watching the dashboard sees no indication of scroll or trim.
**Fix:** Add a small "(trimmed)" label or row counter to the log panel.

**4. Sparklines are drawn on `<canvas>` without axis labels or scale.**
A reviewer cannot determine whether the y-axis is 0–100% or some other scale.
**Fix:** Draw dashed 50% and 80% reference lines on the sparkline canvas.

---

## General Repository Issues

| Issue | Severity |
|---|---|
| `create_bom.py`, `ekler_out.txt`, `docx_output2.txt` are in root — should not exist | Medium |
| `files/` directory contains original CSVs, `data/samples/` has copies — duplicate data | Medium |
| `TAŞKIN-ProjeBilgilendirme.docx` and `TASKIN_RAPOR_v5.docx` not in repo but referenced — broken references | High |
| `node_21.02` and `merkez_10.03` folder name convention inconsistent with standard Arduino folder naming | Low |
| No `LICENSE` file — README mentions MIT but file does not exist | High |
| No `CHANGELOG.md` or version tags | Low |
