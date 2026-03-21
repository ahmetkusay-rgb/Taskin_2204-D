# Devre Şemaları ve Bağlantı Tabloları

*(Kablolama diyagramları `docs/sistem_semasi.png` içerisinde gösterilmektedir.)*

## 1. Merkez ESP32 Bağlantı Şeması ve Pin Diyagramı

| SD Kart Modülü | Merkez ESP32 S3 Pin (GPIO) | Not |
|---|---|---|
| GND | GND | Şase |
| VCC | 5V | Güç |
| MISO | GPIO 19 | Veri Girişi |
| MOSI | GPIO 23 | Veri Çıkışı |
| SCK | GPIO 18 | Saat Sinyali |
| CS | GPIO 5 | Chip Select |

---

## 2. Sensör Düğümü (Node) Bağlantı Şeması ve Pin Diyagramı

| Komponent 1 Ucu | Komponent 2 Ucu | Fonksiyon / Not |
|---|---|---|
| Pil (+) | TP4056 (B+) | Pil girişi |
| Pil (-) | TP4056 (B-) | Pil girişi |
| TP4056 (OUT+) | Boost Converter (VIN+) | Şarj modülünden regülatöre |
| Boost Converter (5V Out) | ESP32 (5V / VIN) | Ana güç girişi |
| Boost Converter (5V Out) | HC-SR04 (VCC) | Sensör güç girişi |
| HC-SR04 (Trig) | ESP32 (GPIO 5) | Tetikleme sinyali |
| HC-SR04 (Echo) | Gerilim Bölücü -> ESP32 (GPIO 18) | Voltaj Düşürme |
| Ortak Şase (GND) | Tüm bileşenlerin GND uçları | Şase |
