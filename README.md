# TAŞKIN — Kentsel Yağmur Suyu Hatları İçin Düşük Maliyetli Veri Toplama ve Planlama Destek Sistemi

<div align="center">

![Platform](https://img.shields.io/badge/Platform-ESP32-blue?logo=espressif)
![Language](https://img.shields.io/badge/Arduino-C%2B%2B-00979D?logo=arduino)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python)
![Protocol](https://img.shields.io/badge/Protocol-ESP--NOW-orange)
![Pilot](https://img.shields.io/badge/Pilot%20Saha-Adana-red)

**Kentsel taşkın riskini gerçek zamanlı, çok parametreli ve düşük maliyetle izleme sistemi**

[Sistem Mimarisi](#sistem-mimarisi) · [Donanım](#donanım-gereksinimleri) · [Kurulum](#kurulum) · [Kullanım](#kullanım) · [Veri & İndeks](#taşkın-risk-i̇ndeksi-tri) · [Dashboard](#web-dashboard) · [Saha Bulguları](#saha-test-bulguları)

</div>

---

## İçindekiler

- [Proje Özeti](#proje-özeti)
- [Araştırma Problemi ve Önemi](#araştırma-problemi-ve-önemi)
- [Sistem Mimarisi](#sistem-mimarisi)
- [Donanım Gereksinimleri](#donanım-gereksinimleri)
- [Dosya Yapısı](#dosya-yapısı)
- [Kurulum](#kurulum)
- [Kullanım](#kullanım)
- [Veri Formatı](#veri-formatı)
- [TAŞKIN Risk İndeksi (TRİ)](#taşkın-risk-i̇ndeksi-tri)
- [Web Dashboard](#web-dashboard)
- [Laboratuvar Bulguları](#laboratuvar-bulguları)
- [Saha Test Bulguları](#saha-test-bulguları)
- [Kaynakça](#kaynakça)

---

## Proje Özeti

**TAŞKIN**, kentsel alanlarda sağanak yağış dönemlerinde oluşan su birikmeleri ve taşkın risklerinin **yerel ölçekte sürekli ve karşılaştırılabilir verilerle izlenebilmesi** amacıyla geliştirilmiş, düşük maliyetli sensör tabanlı bir veri toplama ve karar destek sistemidir.

> **Pilot saha:** Adana ili — Seyhan, Çukurova ve Yüreğir ilçeleri (Şubat 2026)

### Temel Özellikler

| Özellik | Açıklama |
|---|---|
| 🛜 **Kablosuz ESP-NOW** | Wi-Fi altyapısına gerek olmadan < 100 ms gecikmeli P2P iletişim |
| 📡 **Çoklu Node** | 10 adede kadar bağımsız ölçüm noktası desteği |
| 💾 **SD Kart Arşivi** | Merkez birimde zaman damgalı otomatik CSV kaydı |
| 🗺️ **Canlı Dashboard** | Leaflet uydu haritası + gerçek zamanlı sparkline grafikler |
| ⚠️ **Alarm Sistemi** | %80 doluluk eşiği aşımında anında görsel uyarı |
| 📊 **TRİ Modeli** | Çok parametreli bileşik risk skoru (0–100) |
| 🔌 **Python Köprüsü** | Seri port → WebSocket bridge, otomatik yeniden bağlanma |

---

## Araştırma Problemi ve Önemi

Kentsel taşkın riskleri çoğunlukla fiziksel altyapı müdahaleleriyle ele alınmakta; ancak **hangi bölgelerde, ne sıklıkta ve hangi şiddette** su birikmesi yaşandığına dair sürekli yerel veri eksikliği önemli bir problem oluşturmaktadır. Bu eksiklik, altyapı yatırımlarının önceliklendirilmesini güçleştirmektedir.

**TAŞKIN**, bu veri boşluğunu doldurmak için tasarlanmıştır. Sistem;
- anlık müdahale veya alarm üretmek amacıyla **değil**,
- zaman içinde **karşılaştırılabilir, analiz edilebilir** ve altyapı planlamasına karar destek girdisi sağlayabilecek bir veri seti oluşturmak amacıyla geliştirilmiştir.

**Hipotez:** Düşük maliyetli sensör tabanlı bir sistem ile elde edilen sürekli su seviyesi verisi; riskli bölgelerin referans noktalarla karşılaştırmalı olarak belirlenmesine, tekrar eden taşkın eğilimlerinin sayısal olarak ortaya konmasına ve altyapı planlama süreçlerine anlamlı karar destek girdisi sağlanmasına katkı sağlayabilir.

---

## Sistem Mimarisi

```
[Node 1 – Seyhan]────┐
[Node 2 – Çukurova]──┤  ESP-NOW broadcast   ┌─────────────────┐    USB Serial    ┌──────────────┐
[Node 3 – Yüreğir]───┘ ────────────────────▶ │   Merkez ESP32  │ ───────────────▶ │  server.py   │
                                              │   + SD Kart     │                  │  WS Bridge   │
                                              └─────────────────┘                  └──────┬───────┘
                                                                                          │ ws://127.0.0.1:8765
                                                                                          ▼
                                                                                 ┌──────────────────┐
                                                                                 │   index.html     │
                                                                                 │   Dashboard      │
                                                                                 └──────────────────┘
```

### Sistem Bileşenleri

| Bileşen | Dosya | Görev |
|---|---|---|
| **Sensör Nodu** | `node_21.02/node_21.02.ino` | HC-SR04 ile su mesafesi → doluluk %, ESP-NOW broadcast |
| **Merkez Birim** | `merkez_10.03/merkez_10.03.ino` | ESP-NOW alım, SD CSV kaydı, seri port çıkışı |
| **WS Köprüsü** | `server.py` | Seri port okuma, JSON parse, WebSocket yayını |
| **Dashboard** | `index.html` | Leaflet harita, canlı grafik, log akışı |

---

## Donanım Gereksinimleri

### Sensör Nodu *(her ölçüm noktası için)*

| Grup | Bileşen | Fonksiyon | Adet |
|---|---|---|---|
| İşlemci | ESP32-WROOM-32U | Mikrodenetleyici + kablosuz | 1 |
| Sensör | HC-SR04 | Ultrasonik mesafe ölçümü | 1 |
| Güç | 3.7V 1800 mAh Li-Po Pil | Node güç kaynağı | 1 |
| Güç | TP4056 Lityum Şarj Modülü | 3.7V pili güvenli şarj | 1 |
| Güç | MT3608 Voltaj Yükseltici | 3.7V → 5V dönüştürücü | 1 |
| Muhafaza | 11×11×7 cm IP67 Termoplastik Buat | Dış ortam koruma | 1 |
| Diğer | GSM Anten + IPEX/SMA Kablo | Menzil artırıcı | 1 |

**Pin Bağlantıları (Node):**
```
HC-SR04 TRIG  → GPIO 5
HC-SR04 ECHO  → GPIO 18
ALARM RESET   → GPIO 25  (INPUT_PULLUP)
```

### Merkez Birim

| Grup | Bileşen | Fonksiyon | Adet |
|---|---|---|---|
| İşlemci | ESP32-S3-N16R8 | WiFi/BT Board, merkez işlemci | 1 |
| Depolama | Micro SD Kart Modülü (SPI) | Veri yazma | 1 |
| Depolama | 16 GB Micro SD Kart | Veri depolama | 1 |

**Pin Bağlantıları (Merkez):**
```
SD CS   → GPIO 10
SD SCK  → GPIO 12
SD MISO → GPIO 13
SD MOSI → GPIO 11
```

> **Not:** Ek olarak 4 adet 10×10 cm delikli plaket devre kurulumu için kullanılmıştır.

---

## Dosya Yapısı

```
TASKIN/
├── README.md                                  # Bu dosya
├── .gitignore
├── requirements.txt                           # Python bağımlılıkları (pyserial, websockets)
│
├── node_21.02/
│   └── node_21.02.ino                         # Sensör nodu firmware (ESP32-WROOM)
│
├── merkez_10.03/
│   └── merkez_10.03.ino                       # Merkez birim firmware (ESP32-S3)
│
├── server.py                                  # Python serial → WebSocket köprüsü
├── index.html                                 # Web dashboard (Leaflet + Canvas sparklines)
│
├── docs/
│   ├── sistem_semasi.png                      # Sistem bağlantı şeması
│   └── ekran_goruntusu.png                    # Dashboard ekran görüntüsü
│
└── data/
    └── samples/
        ├── saha_node1_09subat_s1_11-14.csv    # Node 1 saha verisi — 9 Şub 11:00–14:00
        ├── saha_node1_09subat_s2_16-19.csv    # Node 1 saha verisi — 9 Şub 16:00–19:00
        ├── saha_node2_10800.csv               # Node 2 saha verisi — 10 Şubat
        └── saha_node3_11subat_08-11.csv       # Node 3 saha verisi — 11 Şub 08:00–11:00
```

---

## Kurulum

### 1. Arduino Firmware

**Gereksinimler:**
- Arduino IDE 2.x
- ESP32 Board Package (`espressif/arduino-esp32 ≥ 2.0`)
- Kütüphaneler: `SD`, `SPI`, `WiFi`, `esp_now` *(tümü ESP32 core ile birlikte gelir)*

#### Sensör Nodu Yükleme

1. `node_21.02/node_21.02.ino` dosyasını aç
2. Her node için benzersiz `NODE_ID` ve saha derinliğini ayarla:
   ```cpp
   #define NODE_ID              1    // Her cihaz için 1–10 arası benzersiz
   #define TANK_YUKSEKLIK_CM  100    // Kanal/rögar derinliği (cm)
   #define ALARM_THRESHOLD     80    // Kritik doluluk eşiği (%)
   ```
3. Board: **ESP32 Dev Module** → Upload

#### Merkez Birim Yükleme

1. `merkez_10.03/merkez_10.03.ino` dosyasını aç
2. SD kart modülünün bağlı olduğunu doğrula
3. Board: **ESP32S3 Dev Module** → Upload

### 2. Python Sunucusu

```bash
pip install -r requirements.txt

# Port otomatik bulunur
python server.py

# Manuel port belirtme
python server.py --port COM12 --baud 115200
```

### 3. Dashboard

`server.py` çalışırken tarayıcıda aç:

```
http://127.0.0.1:8080/index.html
```

---

## Kullanım

```bash
# 1. Merkez ESP32'yi USB ile PC'ye bağla
# 2. Sensör nodlarını güç kaynaklarına bağla
# 3. Python sunucusunu başlat:
python server.py --port COM12

# 4. Dashboard'u aç:
# http://127.0.0.1:8080/index.html
```

### Yapılandırma

`server.py` sabitleri:
```python
SERIAL_PORT  = "COM12"      # Merkez ESP32'nin portu
DEFAULT_BAUD = 115200
WS_PORT      = 8765
HTTP_PORT    = 8080
```

`index.html` içindeki node koordinatlarını güncelle:
```javascript
const NODE_COORDS = {
  1: [37.022, 35.322],  // Seyhan – Barajyolu Alt Geçidi
  2: [37.048, 35.279],  // Çukurova – Turgut Özal Blv.
  3: [37.005, 35.361],  // Yüreğir – Sinanpaşa
};
```

---

## Veri Formatı

### ESP-NOW Paketi (C struct)
```cpp
typedef struct {
  int   node_id;   // 1–10
  float doluluk;   // 0.0–100.0 (%)
  int   alarm;     // 0 = normal, 1 = kritik (>%80)
} veri_paketi;
```

### Seri Port Çıktısı (Merkez → PC)
```
1,63.5,0          ← node_id, doluluk%, alarm
2,82.1,1
SD_OK,2           ← SD kart yazma bildirimi
```

### WebSocket JSON Mesajı
```json
{
  "type":        "data",
  "node_id":     1,
  "doluluk_pct": 63.5,
  "alarm":       0,
  "time":        "14:32:10.456",
  "raw":         "1,63.5,0"
}
```

### SD Kart CSV Formatı
```
zaman_ms,node_id,doluluk,alarm
12500,1,63.5,0
13502,2,82.1,1
```

### Saha CSV Örneği (data/samples/)
```
Zaman Damgası | Mesafe (cm) | Doluluk (%) | Durum
```
Tam veri seti ~10.800 saniyelik saha kayıtlarını içermektedir.

---

## TAŞKIN Risk İndeksi (TRİ)

Bu projede çok parametreli bir bileşik risk skoru modeli geliştirilmiştir. Her ölçüm noktası için TRİ şu formülle hesaplanır:

```
TRI_i = 0.20·O* + 0.20·M* + 0.20·E* + 0.20·F* + 0.20·A*
```

| Parametre | Açıklama |
|---|---|
| **O*** | Normalize edilmiş **ortalama** doluluk oranı |
| **M*** | Normalize edilmiş **maksimum** doluluk oranı |
| **E*** | Normalize edilmiş **%80 eşik aşım süresi** |
| **F*** | Normalize edilmiş **eşik aşım frekansı** |
| **A*** | Normalize edilmiş **doluluk artış hızı** (%20→%80 süresi) |

Tüm parametreler **min-max normalizasyonu** ile 0–100 arasına ölçeklenir. Eşit ağırlık (w = 0.20) uygulanır.

### Risk Sınıflandırması

| TRİ Skoru | Seviye |
|---|---|
| 0–25 | 🟢 Düşük Risk |
| 26–50 | 🟡 Orta Risk |
| 51–75 | 🟠 Yüksek Risk |
| 76–100 | 🔴 Kritik Risk |

### Pilot Saha TRİ Sonuçları (Şubat 2026)

| Ölçüm Noktası | TRİ Skoru | Seviye |
|---|---|---|
| Node 1 — Seyhan, Barajyolu Alt Geçidi | **81** | 🔴 Kritik |
| Node 2 — Çukurova, Turgut Özal Blv. | **58** | 🟠 Yüksek |
| Node 3 — Yüreğir, Sinanpaşa (Referans) | **22** | 🟢 Düşük |

---

## Web Dashboard

Dashboard şu bileşenleri içerir:

- 🗺️ **ESRI Uydu Haritası** — Node konumları doluluk oranına göre renk kodlu interaktif işaretçilerle
- 📊 **Sparkline Grafikler** — Her node için son 60 ölçümün geçmişi
- 📋 **Canlı Log Akışı** — Node bazlı, renkli, zaman damgalı veri akışı
- 💾 **SD Göstergesi** — SD kart yazma durumu (flash animasyonu)
- ⚡ **WebSocket Durumu** — Bağlantı sağlığı (yeşil/kırmızı nokta)

### Doluluk → Renk Kodu

| Aralık | Renk | Durum |
|---|---|---|
| %0–50 | 🟢 Yeşil | Normal |
| %50–80 | 🟡 Turuncu | Yüksek |
| %80+ | 🔴 Kırmızı | Kritik + Alarm |

---

## Laboratuvar Bulguları

Kontrollü test ortamı: **100 cm derin PVC boru**, kademeli dolum-boşaltım, 7.200 saniyelik (2 saat) veri.

### Ortalama & Maksimum Doluluk

| Node | Ort. Doluluk (%) | Maks. Doluluk (%) |
|---|---|---|
| Node 1 | 51 | 92 |
| Node 2 | 36 | 74 |
| Node 3 (Referans) | 15 | 29 |

### Kritik Eşik Aşım Süreleri

| Node | %60 Üzeri (sn) | %80 Üzeri (sn) |
|---|---|---|
| Node 1 | 318 | 102 |
| Node 2 | 124 | 39 |
| Node 3 | 0 | 0 |

### %20 → %80 Doluluk Artış Süresi

| Node | Süre (sn) |
|---|---|
| Node 1 | **19** |
| Node 2 | 26 |
| Node 3 | Kritik seviyeye ulaşmadı |

**Ölçüm doğruluğu:** ±4 cm — HC-SR04 teknik tolerans sınırları içinde.

---

## Saha Test Bulguları

**Saha testi:** Adana ili, 9–11 Şubat 2026, 3 günlük mobil test, 10.800 veri noktası.

### Test Programı

| Tarih | Lokasyon | Saat | Yağış (mm) |
|---|---|---|---|
| 9 Şubat | Seyhan – Barajyolu | 11:00–14:00 | ~1.5 |
| 9 Şubat | Seyhan – Barajyolu | 16:00–19:00 | ~4.2 |
| 10 Şubat | Çukurova – Turgut Özal | 12:00–15:00 | ~5.8 |
| 11 Şubat | Yüreğir – Sinanpaşa | 08:00–11:00 | ~9.5 |

### Tanımlayıcı İstatistikler

| Node | Ort. (%) | Maks. (%) | Std. Sapma | Varyans |
|---|---|---|---|---|
| Node 1 — Barajyolu | 63 | 94 | 18.5 | 342.2 |
| Node 2 — Turgut Özal | 42 | 76 | 14.8 | 219.0 |
| Node 3 — Sinanpaşa (Ref.) | 18 | 34 | 6.2 | 38.4 |

### Kritik Eşik Aşımları

| Node | %60 Üzeri (sn) | %80 Üzeri (sn) | %80 Aşım Sayısı |
|---|---|---|---|
| Node 1 | 427 | 168 | 7 |
| Node 2 | 186 | 52 | 3 |
| Node 3 | 0 | 0 | 0 |

> Node 1'de doluluk artış hızı Node 2'ye göre **~%82 daha yüksek** hesaplanmıştır.

### Ölçüm Noktaları

| Node | İlçe | Konum | Özellik |
|---|---|---|---|
| **Node 1** | Seyhan | Barajyolu Alt Geçidi | Düşük kot, su birikme eğilimi yüksek |
| **Node 2** | Çukurova | Turgut Özal Bulvarı | Yoğun yapılaşma, geçirimsiz yüzey |
| **Node 3** | Yüreğir | Sinanpaşa Mah. | Yüksek kot — **Referans nokta** |

---

## Kaynakça

> Raporun tamamı için ilgili DOC dosyasına bakınız.

- Ashley et al. (2005). *Flooding in the future.* Water Science and Technology.
- Batty et al. (2012). *Smart cities of the future.* EPJST.
- Chen et al. (2020). *Urban inundation response to rainstorm patterns.* J. Hydrology.
- Fletcher et al. (2015). *SUDS, LID, BMPs, WSUD.* Urban Water Journal.
- IPCC (2023). *Climate Change 2023: Synthesis Report.* IPCC.
- Mishra & Coulibaly (2010). *Hydrometric network evaluation.* J. Hydrology.
- O'Donnell & Thorne (2020). *Drivers of future urban flood risk.* Phil. Trans. R. Soc. A.
- Tauro et al. (2016). *MOXXI: Innovation and multi-disciplinarity.* Hydrological Sciences Journal.
- Zanella et al. (2014). *IoT for smart cities.* IEEE IoT Journal.

---

## Lisans

Bu proje MIT Lisansı kapsamında lisanslanmıştır.

---

<div align="center">
  <sub>TAŞKIN Projesi · Adana Pilot Sahası · 2026</sub>
</div>
