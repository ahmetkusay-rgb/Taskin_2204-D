# Bağlantı Şeması (Pin Tabloları)

TAŞKIN merkez birimi ve sensör düğümleri için pin bağlantıları. Pin numaraları firmware ile birebir eşleşir (`firmware/merkez/merkez.ino`, `firmware/node/node.ino`).

> **Sensör notu:** İlk prototipte HC-SR04 kullanılmış, sonra **JSN-SR04T** su geçirmez ultrasonik sensöre geçilmiştir. Pin yerleşimi (TRIG/ECHO) aynıdır; aşağıdaki tablo güncel JSN-SR04T kurulumunu yansıtır.

## Merkez: ESP32-S3 ↔ Micro SD Kart Modülü

Firmware özel SPI başlatma yapar: `SPI.begin(12, 13, 11, 10)` (SCK, MISO, MOSI, CS). Bunlar ESP32-S3 için varsayılan dışı SPI pinleridir.

> **Not:** Rapordaki EK-5.1 Fritzing şeması varsayılan VSPI pinlerini (MISO 19 / MOSI 23 / SCK 18 / CS 5) gösterir. Çalışan firmware bu pinleri aşağıdaki tabloya yeniden atar; bağlantıyı **bu tabloya göre** yapın.

| SD Modül Pini | ESP32-S3 GPIO | Not |
|---|---|---|
| GND | GND | Ortak toprak |
| VCC | 5V | Modül USB'den beslenir |
| MISO | GPIO 13 | SPI veri girişi |
| MOSI | GPIO 11 | SPI veri çıkışı |
| SCK | GPIO 12 | SPI saat sinyali |
| CS | GPIO 10 | Chip Select (aktif-düşük) |

## Düğüm: ESP32-WROOM ↔ JSN-SR04T ↔ Güç Zinciri

| Sinyal | Kaynak | Hedef | Not |
|---|---|---|---|
| TRIG | ESP32 GPIO 5 | JSN-SR04T TRIG | 10 µs HIGH darbe ölçümü başlatır |
| ECHO | JSN-SR04T ECHO | ESP32 GPIO 18 (gerilim bölücü üzerinden) | Modül 5V besleniyorsa ECHO 5V olabilir → 3.3V'a bölücü önerilir |
| VCC (sensör) | MT3608 5V çıkış | JSN-SR04T VCC | Sensör 5V ile beslenir |
| VCC (ESP32) | MT3608 5V çıkış | ESP32 VIN | Aynı 5V hattı |
| GND | Ortak bara | Tüm bileşenler | Tek ortak toprak |
| BAT+ | Li-Po (+) | TP4056 B+ | Şarj girişi |
| OUT+ | TP4056 OUT+ | MT3608 VIN+ | Düzenlenmiş şarj çıkışı |

**Alarm sıfırlama düğmesi:** ESP32 GPIO 25 (`INPUT_PULLUP`). Döngüde LOW okunursa o çevrimde alarm bayrağı sıfırlanır.

## Firmware Pin Sabitleri

### Düğüm (`firmware/node/node.ino`)

```cpp
#define TRIG_PIN   5
#define ECHO_PIN   18
#define BUTTON_PIN 25
```

### Merkez (`firmware/merkez/merkez.ino`)

```cpp
#define SD_CS_PIN 10
#define SD_SCK    12
#define SD_MISO   13
#define SD_MOSI   11
```
