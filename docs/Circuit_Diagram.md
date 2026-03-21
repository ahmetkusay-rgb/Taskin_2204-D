# Devre Şemaları ve Bağlantı Tabloları
# Circuit Diagrams and Connection Tables

*(Wiring diagrams are shown in `docs/sistem_semasi.png`.)*

## 1. Central ESP32 Connection Diagram and Pin Configuration

| SD Card Module | Central ESP32 S3 Pin (GPIO) | Note |
|---|---|---|
| GND | GND | Ground |
| VCC | 5V | Power |
| MISO | GPIO 19 | Data Input |
| MOSI | GPIO 23 | Data Output |
| SCK | GPIO 18 | Clock Signal |
| CS | GPIO 5 | Chip Select |

---

## 2. Sensor Node Connection Diagram and Pin Configuration

| Component 1 End | Component 2 End | Function / Note |
|---|---|---|
| Battery (+) | TP4056 (B+) | Battery input |
| Battery (-) | TP4056 (B-) | Battery input |
| TP4056 (OUT+) | Boost Converter (VIN+) | From charger module to regulator |
| Boost Converter (5V Out) | ESP32 (5V / VIN) | Main power input |
| Boost Converter (5V Out) | HC-SR04 (VCC) | Sensor power input |
| HC-SR04 (Trig) | ESP32 (GPIO 5) | Trigger signal |
| HC-SR04 (Echo) | Voltage Divider -> ESP32 (GPIO 18) | Voltage Reduction |
| Common Ground (GND) | GND pins of all components | Ground |
