# EKLER

## EK-1: Teknik Malzeme ve Bileşen Listesi

| Grup Adı | Bileşen Adı | Fonksiyon / Açıklama | Miktar |
|---|---|---|---|
| Merkez | ESP32-S3-N16R8 WiFi/BT Board | Merkez İşlemci | 1 |
| Merkez | Micro SD Kart Modülü | Veri Yazma | 1 |
| Merkez | 16 GB Micro SD Kart | Veri Depolama | 1 |
| Node | 3.7V 1800 mAh Li-Po Pil | Node Güç Kaynağı | 3 |
| Node | TP4056 Lityum Şarj Modülü | 3.7V Pili Güvenli Şarj Etme | 3 |
| Node | MT3608 Voltaj Yükseltici | 3.7V -> 5V Voltaj Dönüştürücü | 3 |
| Node | ESP32-WROOM-32U Board | Node İşlemcisi | 3 |
| Node | GSM Anten | Kablosuz Haberleşme Menzil Artırıcı | 3 |
| Node | IPEX - SMA Dişi Kablo | Anteni ESP32'ye Bağlayan Ara Kablo | 3 |
| Node | 11x11x7cm Termoplastik Buat Kutu | Düğümleri Dış Ortamdan Koruma (IP67) | 3 |
| Node | Conta | Düğümlerin Sızdırmazlığını Sağlama | - |
| Node | Silica Jel | Kutu İçi Nemlenmeyi Önleme | - |
| Yardımcı | Plastik Kelepçe | Kutunun Sabitlenmesi | - |
| Yardımcı | 10x10 cm Delikli Plaket | Devre Kurulumu ve Lehimleme Alanı | 4 |

---

## EK-2: Yazılım ve Algoritma Detayları

- Merkez Kodunun SD Karta Yazdırma Kısmından
- Düğümlerin Boardcast ve Peer Ayarlarından
- Bilgisayarda Çalışan Server Kodundan

*(Kodun tamamı bu Github deposunda dijital ek olarak sunulmuştur.)*

---

## EK-3: Saha Testi İstasyon Detayları ve Fotoğraflar

**İstasyon Kurulum Fotoğrafları:** Her bir Node'un (Seyhan, Çukurova, Yüreğir) yerinde nasıl monte edildiğini gösteren geniş ve yakın çekim fotoğraflar. *(Fotoğraflara `docs/` klasöründen ulaşılabilir.)*

**Koordinat Tablosu:**
- **Düğüm 1:** Seyhan/Baraj Yolu Alt Geçidi `[37.022, 35.322]`
- **Düğüm 2:** Çukurova/Turgut Özal Blv. `[37.048, 35.279]`
- **Düğüm 3:** Yüreğir/Sinanpaşa `[37.005, 35.361]`

**Saha Gözlem Notları:** Cihazların yanına gidildiğinde fiziksel bir engel (çöp, bitki vb.) olup olmadığına dair tutulan kısa günlükler.

---

## EK-4: Ham Veri Örnekleri

**Format:** `Zaman Damgası | Mesafe (cm) | Doluluk (%) | Durum (OK/ERROR)`
- 9 Şubat'ta yapılan saha testlerinden kesitler
- 10 ve 11 Şubat'ta yapılan saha testlerinden kesitler

*(Tam veri seti - 14400 saniyelik saha kayıtları - `data/samples/` klasöründe dijital ek olarak sunulmuştur.)*

---

## EK-5: Devre Şeması ve Bağlantı Şeması

### EK-5.1: Merkez Bağlantı Şeması ve Pin Diyagramı

| SD Kart Modülü | Merkez ESP32 S3 Pin (GPIO) | Not |
|---|---|---|
| GND | GND | Şase |
| VCC | 5V | Güç |
| MISO | GPIO 19 | Veri Girişi |
| MOSI | GPIO 23 | Veri Çıkışı |
| SCK | GPIO 18 | Saat Sinyali |
| CS | GPIO 5 | Chip Select |

### EK-5.2: Düğüm Bağlantı Şeması ve Pin Diyagramı

| Bileşen 1 | Bileşen 2 | Not |
|---|---|---|
| Pil (+) | TP4056 (B+) | Pil girişi |
| Pil (-) | TP4056 (B-) | Pil girişi |
| TP4056 (OUT+) | Boost Converter (VIN+) | Şarj modülünden regülatöre |
| Boost Converter (5V Out) | ESP32 (5V / VIN) | Ana güç girişi |
| Boost Converter (5V Out) | HC-SR04 (VCC) | Sensör güç girişi |
| HC-SR04 (Trig) | ESP32 (GPIO 5) | Tetikleme sinyali |
| HC-SR04 (Echo) | Gerilim Bölücü -> ESP32 (GPIO 18) | Voltaj Düşürme |
| Ortak Şase (GND) | Tüm bileşenlerin GND uçları | Şase |

---

## EK-6: Kalibrasyon ve Hata Analizi Tabloları

*(Detaylı tablolar raporun tam metninde yer almaktadır, laboratuvar/saha testi doğrulama verileri içerir.)*
