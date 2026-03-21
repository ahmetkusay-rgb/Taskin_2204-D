# TAŞKIN — Kentsel Su Baskını Seviyesi İzleme Sistemi

<div align="center">

> 🇹🇷 **Türkçe** | [🇬🇧 For English → README.md](README.md)

![Platform](https://img.shields.io/badge/Platform-ESP32-blue?logo=espressif)
![Protokol](https://img.shields.io/badge/Kablosuz-ESP--NOW-orange)
![Python](https://img.shields.io/badge/Köprü-Python%203.8+-3776AB?logo=python)
![Lisans](https://img.shields.io/badge/Lisans-MIT-green)
![Pilot](https://img.shields.io/badge/Pilot%20Saha-Adana-red)

**Kentsel yağmur suyu hatlarında gerçek zamanlı su seviyesi izleme ve taşkın riski endeksleme sistemi.**

</div>

---

## 1. Proje Başlığı

**TAŞKIN: Kentsel Yağmur Suyu Hatları İçin Düşük Maliyetli Veri Toplama ve Planlama Destek Sistemi**

---

## 2. Projenin Özeti ve Önemi

### Problem

Adana gibi şehirlerde kentsel yağmur suyu drenaj sistemleri sessizce çökmektedir. Aynı kavşaklarda ve alt geçitlerde yağmur sonrası su taşkınları tekrarlamakta; ancak belediyelerin elinde bu tehlikeli noktaları önceliklendirmek için **sürekli ve yerel ölçekte su seviyesi verisi bulunmamaktadır.** Taşkın risk yönetimi, sensör kanıtına değil olay sonrası raporlamaya dayanmaktadır.

### Sistemin İşlevi

TAŞKIN, birden fazla kentsel ölçüm noktasında su doluluk düzeyini sürekli ölçen, verileri kablosuz olarak merkez birime aktaran, SD karta kaydeden ve web tabanlı bir harita arayüzüne canlı olarak yayınlayan çok düğümlü bir sensör ağıdır.

Sistemin temel çıktısı ham sensör okumaları değil; her ölçüm noktası için aşağıdaki bileşenlerden hesaplanan **TAŞKIN Risk İndeksi (TRİ)** modelidir:
- Ortalama doluluk oranı
- Maksimum doluluk oranı
- %80 eşiğinin üzerinde kalınan süre
- Eşik aşım sayısı
- Doluluk artış hızı (%20'den %80'e geçiş süresi)

Bu yaklaşım, toplanan ham verileri altyapı planlaması için **karar destek çıktısına** dönüştürmektedir.

### Teknik Kapsam

| Parametre | Değer |
|---|---|
| Aktif düğüm sayısı | 3 |
| Örnekleme hızı | 1 Hz (1 ölçüm/saniye/düğüm) |
| Kablosuz protokol | ESP-NOW (WiFi altyapısı gerektirmez) |
| Ölçüm doğruluğu | ±4 cm (HC-SR04) |
| Laboratuvar testi | 7.200 saniye (PVC boru, kontrollü ortam) |
| Saha testi | 10.800 saniye, Adana, Şubat 2026 |
| Batarya ömrü (ölçülen) | Sürekli-Açık modda 10–12 saat |

---

## 3. Sistem Mimarisi

Sistem dört katmandan oluşmaktadır:

```
┌────────────────────────────────────────────────────────────────┐
│                      SENSÖR KATMANI                            │
│                                                                │
│  [Düğüm 1 — Barajyolu] [Düğüm 2 — Turgut Özal] [Düğüm 3 — Ref]│
│   ESP32-WROOM-32U        ESP32-WROOM-32U         ESP32-WROOM   │
│   HC-SR04                HC-SR04                 HC-SR04       │
│   Li-Po + TP4056 + MT3608                                      │
└────────────────────┬───────────────────────────────────────────┘
                     │ ESP-NOW yayın (broadcast)
                     │ paket: {node_id, doluluk_pct, alarm}
                     ▼
┌────────────────────────────────────────────────────────────────┐
│                      MERKEZ KATMANI                            │
│           ESP32-S3-N16R8 + SPI SD Kart Modülü                  │
│  - ESP-NOW paketlerini alır ve doğrular                        │
│  - Doluluk değerini 0–100 aralığına kısıtlar                  │
│  - SD karta zaman damgalı CSV kaydeder                         │
│  - USB Seri porta virgülle ayrılmış satır yazar               │
└────────────────────┬───────────────────────────────────────────┘
                     │ USB Seri @ 115200 baud
                     │ biçim: node_id,doluluk_pct,alarm
                     ▼
┌────────────────────────────────────────────────────────────────┐
│                    KÖPRÜ KATMANI (Bilgisayar)                  │
│                       server.py (Python)                       │
│  - Seri portu okur (otomatik algılama veya --port bayrağı)     │
│  - Her satırı ayrıştırır, doğrular ve kısıtlar                │
│  - WebSocket üzerinden JSON paket yayınlar (ws://localhost:8765)│
│  - index.html'yi HTTP ile sunar (http://localhost:8080)        │
└────────────────────┬───────────────────────────────────────────┘
                     │ WebSocket JSON akışı
                     ▼
┌────────────────────────────────────────────────────────────────┐
│                  GÖRSELLEŞTİRME KATMANI                       │
│                       index.html                               │
│  - Leaflet uydu haritası, renk kodlu düğüm işaretçileri        │
│  - Düğüm başına 60 noktalı kıvılcım grafik (sparkline)         │
│  - Canlı olay akışı, SD göstergesi, WebSocket bağlantı durumu │
└────────────────────────────────────────────────────────────────┘
```

> **[GÖRSEL YERİ — Bölüm 3]:** Sistem mimarisi blok diyagramı (sensörden panele kadar donanım sinyal akışı)

### Veri Akışı

1. HC-SR04, su yüzeyine olan mesafeyi ölçer → `map(mesafe, MAX_DERINLIK, 0, 0, 100)` ile doluluk %'ye dönüştürülür
2. Düğüm, `{node_id, doluluk_pct, alarm}` yapısını ESP-NOW broadcast MAC `FF:FF:FF:FF:FF:FF` adresine gönderir
3. Merkez ESP32-S3, paketi doğrular (node_id 1–10, doluluk 0–100), SD'ye kaydeder, Seri porta yazar
4. `server.py`, Seri portu okur ve WebSocket üzerinden JSON paketi yayınlar
5. `index.html`, JSON'u alır, harita işaretçisinin rengini, kıvılcım grafiğini ve log tablosunu günceller

---

## 4. Donanım Bileşenleri

### Merkez Birim (1 adet)

| Bileşen | Model | Teknik Görev |
|---|---|---|
| Mikrodenetleyici | ESP32-S3-N16R8 | ESP-NOW alım, SD kaydı, USB Seri çıkış |
| SD Kart Modülü | SPI Micro SD Modülü | SD kartı ESP32-S3 SPI veri yoluna bağlar |
| Depolama | 16 GB Micro SD Kart | `/veri_log.csv` dosyasını sürekli tutar |

### Sensör Düğümleri (3 adet, özdeş)

| Bileşen | Model | Teknik Görev |
|---|---|---|
| Mikrodenetleyici | ESP32-WROOM-32U | HC-SR04 sürücüsü, ESP-NOW, alarm yönetimi |
| Ultrasonik Sensör | HC-SR04 | Temassız mesafe ölçümü: 2–400 cm, ±3 mm çözünürlük |
| Batarya | 3,7V 1800 mAh Li-Po | Şebeke bağlantısı gerektirmeyen saha güç kaynağı |
| Şarj Modülü | TP4056 | Aşırı şarja karşı korumalı Li-Po şarj yönetimi |
| Gerilim Yükseltici | MT3608 | 3,7V → 5V kararlı çıkış (ESP32 ve sensör için) |
| Anten | GSM Harici + IPEX–SMA Kablo | ESP-NOW menzilini kutu dışına taşır |
| Muhafaza | 11×11×7 cm IP67 Termoplastik Buat | Elektroniği dış ortam koşullarına karşı korur |
| Nem Kontrolü | Silica Jel | Kutu içi yoğuşmayı önler |
| Montaj | Plastik Kelepçe | Muhafazayı yapıya sabitler |

### Neden ESP-NOW?

- Hedef konumlarda (alt geçitler, drenaj ızgaraları) **WiFi altyapısı yoktur**
- **10 ms altı gecikme** — 1 Hz örnekleme için yeterlidir
- **ESP32'ye yerel**: ek donanım maliyeti yoktur
- **Yayın modu**: merkez, istasyon MAC adresi yapılandırması gerektirmeden tüm düğümlerden veri alır

---

## 5. Fiziksel Tasarım

Her düğüm **IP67 sertifikalı 11×11×7 cm termoplastik buat** içine yerleştirilmiştir. HC-SR04 sensörü, drenaj kanalına veya alt geçide **yukarıdan aşağı bakacak biçimde** ayarlanmıştır. Anten, RF sinyalinin kutunun dışına taşınmasını sağlamak için kablo rakoru ile dışarı çıkarılmıştır.

İç düzen: ESP32 → delikli plaket → TP4056 → MT3608 → ortak GND barası. ECHO sinyal kablosu kısa tutulmuştur.

> **[GÖRSEL YERİ — Bölüm 5a]:** Düğüm muhafazasının içi — tüm bileşenler etiketli, yukarıdan çekim
> **[GÖRSEL YERİ — Bölüm 5b]:** HC-SR04 sensörünün su yüzeyine yönlendirilmiş hali, montaj geometrisi
> **[GÖRSEL YERİ — Bölüm 5c]:** Kapalı IP67 muhafaza dışarıdan — anten ve kablo rakoru görünür
> **[GÖRSEL YERİ — Bölüm 5d]:** Barajyolu alt geçidinde sahaya kurulmuş Düğüm 1

---

## 6. Kablolama ve Bağlantılar

### Merkez: ESP32-S3 ↔ SD Kart Modülü

| SD Modül Pini | ESP32-S3 GPIO | Not |
|---|---|---|
| GND | GND | Ortak toprak |
| VCC | 5V | USB'den güç |
| MISO | GPIO 13 | SPI veri girişi |
| MOSI | GPIO 11 | SPI veri çıkışı |
| SCK | GPIO 12 | SPI saat sinyali |
| CS | GPIO 10 | Chip Select (aktif-düşük) |

> **Not:** ESP32-S3 varsayılan SPI pinleri farklıdır. Firmware `SPI.begin(12, 13, 11, 10)` ile özel pin ataması yapar.

### Düğüm: ESP32 ↔ HC-SR04 ↔ Güç Zinciri

| Sinyal | Kaynak | Hedef | Not |
|---|---|---|---|
| TRIG | GPIO 5 | HC-SR04 TRIG | 10 µs HIGH darbe ölçümü başlatır |
| ECHO | HC-SR04 ECHO | GPIO 18 (gerilim bölücü üzerinden) | HC-SR04 çıkışı 5V — bölücü ile 3,3V'a düşürülür |
| VCC (sensör) | MT3608 5V çıkış | HC-SR04 VCC | Sensör 5V gerektirir |
| VCC (ESP32) | MT3608 5V çıkış | ESP32 VIN | Aynı 5V hattı |
| GND | Ortak bara | Tüm bileşenler | Tek ortak toprak |
| BAT+ | Li-Po (+) | TP4056 B+ | Şarj girişi |
| OUT+ | TP4056 OUT+ | MT3608 VIN+ | Düzenlenmiş şarj çıkışı |

**Alarm sıfırlama düğmesi:** GPIO 25 (`INPUT_PULLUP`). Döngüde LOW okunursa o çevrimde alarm bayrağı sıfırlanır.

> **[GÖRSEL YERİ — Bölüm 6]:** Kablolama şeması (Fritzing dışa aktarım veya elle çizilmiş şema)
> *(Fritzing kaynak dosyası: `docs/şemalar.fzz`)*

---

## 7. Yazılım Yapısı

```
TASKIN/
├── firmware/
│   ├── node_21.02/
│   │   └── node_21.02.ino       # Sensör düğümü firmware (ESP32-WROOM)
│   └── merkez_10.03/
│       └── merkez_10.03.ino     # Merkez birim firmware (ESP32-S3)
├── server.py                    # Python seri port → WebSocket köprüsü
├── index.html                   # Tek dosya web panosu
├── analysis/
│   └── tri_score.py             # CSV verilerinden TRİ hesaplama scripti
├── data/
│   └── samples/                 # Saha testi CSV kayıtları (4 dosya)
├── docs/
│   ├── Devre_Semalari.md        # Pin bağlantı tabloları
│   ├── CODE_REVIEW.md           # Kod kalitesi incelemesi
│   ├── MISSING.md               # Eksik öğeler listesi
│   └── IMAGE_PLAN.md            # Gerekli görsel/fotoğraf planı
├── Malzeme_Listesi.xlsx         # Malzeme listesi
├── LICENSE
├── requirements.txt
└── README.md / README_TR.md
```

### `node_21.02.ino` — Sensör Düğümü

- HC-SR04 pinleri, alarm sıfırlama düğmesi (PULLUP) ve ESP-NOW broadcast peer'i yapılandırır
- `mesafeOlc()`: 10 µs TRIG darbesi gönderir, 60 ms zaman aşımıyla ECHO süresini okur, cm'ye çevirir
- `loop()`: ölç → doluluk %'ye dönüştür → alarm değerlendir → struct paketini oluştur → `esp_now_send()` → 1000 ms bekle
- GPIO 25 butonu döngüde LOW ise o çevrimde `alarm = 0` atanır

### `merkez_10.03.ino` — Merkez Birim

- Özel SPI başlatma: `SPI.begin(12, 13, 11, 10)` — varsayılan dışı pinler zorunludur
- İlk açılışta başlık satırıyla `/veri_log.csv` oluşturur
- `OnDataRecv()` geri çağrısı: node_id [1,10] aralığını, doluluk [0,100] kısıtını, alarm {0,1} geçerliliğini denetler
- SD'ye `zaman_ms,node_id,doluluk,alarm` kaydeder; Seri porta `node_id,doluluk,alarm` yazar
- Başarılı her SD yazımından sonra `SD_OK,node_id` satırı çıkarır

### `server.py` — Köprü

- `find_esp_port()`: "cp210", "ch340", "uart", "esp" anahtar sözcükleriyle ESP32'yi otomatik tespit eder
- `serial_reader()`: thread yürütücüsünde Seri port satırlarını okuyan async coroutine
- `SD_OK,N` satırlarını ayrıştırır → `{"type":"sd_log"}` JSON paketi yayınlar
- `id,pct,alarm` satırlarını ayrıştırır → doğrular → kısıtlar → `{"type":"data"}` JSON paketi yayınlar
- 8080 portunda `index.html`'yi HTTP ile sunar; bağlantı kesilince 3 saniyede yeniden bağlanır

### `index.html` — Web Panosu

- Leaflet + ESRI uydu haritası; Adana merkezi (37,0°K, 35,32°D)
- Renk kodlu özel işaretçiler: yeşil (<%50), turuncu (%50–80), kırmızı (>%80)
- Fareyle üzerine gelindiğinde düğüm başına kıvılcım grafik ipucu
- Sağ panel: 3 düğüm kartı — doluluk %, son paket zamanı, kritik uyarı rozeti
- 60 noktalı kayan kıvılcım grafikler; WebSocket bağlantı kesilince otomatik yeniden bağlanır

### `analysis/tri_score.py` — TRİ Hesaplayıcı

- `data/samples/` içindeki tüm CSV dosyalarını okur
- Düğüm başına hesaplar: ortalama doluluk, maksimum doluluk, standart sapma, %80 üzeri süre, eşik aşım sayısı, artış süresi
- Min-maks normalizasyonuyla tüm metrikleri 0–100 arasına ölçekler
- Eşit ağırlıklı bileşik TRİ skorunu hesaplar ve sıralı risk tablosunu yazdırır
- Çalıştırma: `python analysis/tri_score.py`

---

## 8. Kurulum ve Yapılandırma

### 8.1 Arduino Firmware

**Test edilen ortam:**
- Arduino IDE 2.3.x
- ESP32 kart paketi: `esp32 by Espressif Systems v3.x`
- İşletim sistemi: Windows 11

**Kart paketi kurulumu:**
- *Dosya → Tercihler → Ek Kart Yöneticisi URL'leri:*
  `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
- *Araçlar → Kart Yöneticisi* → "esp32" ara → `esp32 by Espressif Systems` yükle

**Harici kütüphane kurulumu gerekmez.** `WiFi.h`, `esp_now.h`, `SD.h`, `SPI.h` kütüphanelerinin tamamı ESP32 kart paketiyle birlikte gelir.

**Düğüm firmware yükleme:**
1. `firmware/node_21.02/node_21.02.ino` dosyasını aç
2. Cihaza özgü sabitleri ayarla:
   ```cpp
   #define NODE_ID              1    // Her cihaz için benzersiz 1–10
   #define TANK_YUKSEKLIK_CM  100    // Kanal derinliği (cm)
   #define ALARM_THRESHOLD     80    // Alarm eşiği (%)
   ```
3. *Araçlar → Kart* → **ESP32 Dev Module**
4. *Araçlar → Port* → ilgili COM portunu seç
5. Yükle

**Merkez firmware yükleme:**
1. `firmware/merkez_10.03/merkez_10.03.ino` dosyasını aç
2. Formatlanmış SD kartı modüle takılı olduğundan emin ol
3. *Araçlar → Kart* → **ESP32S3 Dev Module**
4. Yükle

### 8.2 Python Köprüsü

```bash
# Python 3.8+ gereklidir
pip install -r requirements.txt

# Portu otomatik algılamayla:
python server.py

# Portu elle belirterek:
python server.py --port COM12
```

### 8.3 Web Panosu

`server.py` çalışırken tarayıcıda şu adresi aç:
```
http://127.0.0.1:8080/index.html
```
Derleme adımı yoktur. Tek bir HTML dosyasıdır.

---

## 9. Kullanım

### Başlangıç Sırası

1. Tüm sensör düğümlerini güce bağla (batarya veya USB)
2. Merkez ESP32-S3'ü USB ile bilgisayara bağla
3. `python server.py --port COM12` komutunu çalıştır
4. `http://127.0.0.1:8080/index.html` adresini tarayıcıda aç
5. ESP-NOW paketleri gelmeye başladıkça düğümler haritada ~5 saniye içinde görünür

### Çalışma Zamanı Davranışı

- Harita işaretçileri gerçek zamanlı renk değiştirir: yeşil / turuncu / kırmızı
- SD göstergesi (üst çubuk) her SD yazımında yeşil yanıp söner
- Olay akışı her gelen paketi zaman damgası ve düğüm rengiyle ekler
- Kıvılcım grafikler en yeni veriye göre sağa kayar

### SD Kart Verisi

Oturum sonrasında SD kart çıkarılır. `/veri_log.csv` dosyası şu biçimi içerir:
```
zaman_ms,node_id,doluluk,alarm
12500,1,63.5,0
13510,2,81.2,1
```
**Not:** `zaman_ms`, duvar saatini değil önyüklemeden geçen süreyi (ms) gösterir. Mutlak saatlerle eşleştirmek için `server.py` terminal çıktısındaki oturum başlangıç zamanını referans al.

---

## 10. Test Sonuçları

### Laboratuvar Doğrulaması

**Düzenek:** 100 cm derinliğinde PVC boru, 2 saat boyunca su seviyesi kademeli artırılıp düşürüldü. Düğüm başına 7.200 örnek.

> **[GÖRSEL YERİ — Bölüm 10a]:** PVC boru laboratuvar düzeneği — sensör monte edilmiş, ölçek için cetvel görünür

**Sensör doğruluğu:** Manuel referans ölçümlerle karşılaştırmada ±4 cm sapma — HC-SR04 teknik tolerans sınırları içinde.

| Düğüm | Ort. Doluluk (%) | Maks. Doluluk (%) | >%60 Süresi (sn) | >%80 Süresi (sn) | %20→%80 Artışı (sn) |
|---|---|---|---|---|---|
| Düğüm 1 — Barajyolu | 51 | 92 | 318 | 102 | 19 |
| Düğüm 2 — Turgut Özal | 36 | 74 | 124 | 39 | 26 |
| Düğüm 3 — Sinanpaşa (Ref.) | 15 | 29 | 0 | 0 | — |

2 saatlik laboratuvar oturumunda sıfır paket kaybı gözlemlendi. Simulasyon kesintisi sonrası Seri bağlantı yeniden kurulumu < 3 saniye.

### Saha Testi — Adana, 9–11 Şubat 2026

**Koşullar:** Gerçek kentsel drenaj konumları; oturum başına 1,5–9,5 mm yağış.

| Tarih | Düğüm | Konum | Yağış |
|---|---|---|---|
| 9 Şubat Sabah | Düğüm 1 | Seyhan — Barajyolu Alt Geçidi | ~1,5 mm |
| 9 Şubat Öğleden Sonra | Düğüm 1 | Seyhan — Barajyolu Alt Geçidi | ~4,2 mm |
| 10 Şubat | Düğüm 2 | Çukurova — Turgut Özal Bulvarı | ~5,8 mm |
| 11 Şubat | Düğüm 3 | Yüreğir — Sinanpaşa (Ref.) | ~9,5 mm |

| Düğüm | Ort. (%) | Maks. (%) | Std. Sapma | >%80 Süresi (sn) | >%80 Aşım Sayısı |
|---|---|---|---|---|---|
| Düğüm 1 — Barajyolu | 63 | 94 | 18,5 | 168 | 7 |
| Düğüm 2 — Turgut Özal | 42 | 76 | 14,8 | 52 | 3 |
| Düğüm 3 — Sinanpaşa (Ref.) | 18 | 34 | 6,2 | 0 | 0 |

**TRİ Skorları** (eşit ağırlıklı bileşik, min-maks normalize — `analysis/tri_score.py` çalıştırılarak üretilmiştir):

| Düğüm | TRİ | Risk Seviyesi |
|---|---|---|
| Düğüm 1 — Barajyolu | **81** | 🔴 Kritik |
| Düğüm 2 — Turgut Özal | **58** | 🟠 Yüksek |
| Düğüm 3 — Sinanpaşa (Ref.) | **22** | 🟢 Düşük |

> **[GÖRSEL YERİ — Bölüm 10b]:** Saha oturumu sırasında canlı pano ekran görüntüsü — renk kodlu işaretçiler, aktif olay akışı
> **[GÖRSEL YERİ — Bölüm 10c]:** 3 düğüm için zaman serisi doluluk eğrisi grafiği (CSV verisinden üretilmiş)

---

## 11. Sınırlılıklar ve İyileştirme Önerileri

### Batarya Ömrü

Saha testleri aşamasında sistemin kararlılığını ve veri sürekliliğini ölçmek amacıyla cihaz **Sürekli Açık (Always-On)** modunda çalıştırılmıştır.

| Bileşen | Durum | Akım Tüketimi (Ort.) |
|---|---|---|
| ESP32-S3 | Aktif (WiFi açık) | ~80–100 mA |
| HC-SR04 | Sürekli ölçüm | ~15 mA |
| SD Kart Yazma | Aktif | ~20–30 mA |
| **Toplam** | **Sürekli Aktif** | **~130–150 mA** |

**Test Sonucu:** 3,7V 1800 mAh Li-Po batarya ve MT3608 yükseltici modül ile yapılan testlerde, kesintisiz veri gönderimi ve kaydı altında ortalama **10–12 saat çalışma süresi** gözlemlenmiştir.

> **Not:** Pil ömrünü aylara yaymak için yazılımsal olarak **Derin Uyku (Deep Sleep)** optimizasyonu bir sonraki güncelleme aşaması olarak planlanmaktadır. ESP32'nin ölçümler arasında uyku moduna alınmasıyla tahmini tüketim ~10 mA'e düşecek; bu da 60–80 saatlik sürekli çalışmayı mümkün kılacaktır.

### Mevcut Zayıf Noktalar

| Zayıflık | Etkisi |
|---|---|
| HC-SR04 su geçirmez değildir | Yağmur damlacıkları ölçüm gürültüsüne yol açar |
| NODE_ID yükleme sırasında sabit kodlanmıştır | Birden fazla düğüm için ayrı Arduino yüklemesi gerekir |
| Gerçek zamanlı saat (RTC) yoktur | CSV zaman damgaları `millis()` — başlangıçtan geçen süre, duvar saati değil |
| Tek atlama ESP-NOW | Tüm düğümler merkezin ~200 m yakınında olmalıdır |
| Yalnızca 3 günlük saha testi | Mevsimsel değişkenlik belirsizdir |
| Yağış ölçer entegrasyonu yoktur | Doluluk artış hızı kesin yağış verisiyle ilişkilendirilememektedir |
| Pano için bilgisayar gereklidir | Merkez, çalışan bir `server.py`'ye USB ile bağlı olmalıdır |

### Önerilen Geliştirmeler

1. HC-SR04 yerine su geçirmez ultrasonik (MaxBotix MB7389) veya radar sensör kullanılması
2. Mutlak zaman damgaları için merkeze DS3231 RTC modülü eklenmesi
3. Çok günlük batarya çalışması için ESP32 Derin Uyku ile 1 Hz uyandırma döngüsü uygulanması
4. Kalıcı saha kurulumu için güneş paneli + şarj kontrolcüsü eklenmesi
5. Yağış korelasyonu için MGM hava durumu API'si entegrasyonu
6. Saha testinin tam yağış mevsimine (Adana'da Ekim–Mart) genişletilmesi
7. Yerel bilgisayara bağımlılığı ortadan kaldırmak için MQTT/HTTP bulut yüklemesi eklenmesi

---

## 12. Sonuç

TAŞKIN, düğüm başına 30 dolar altı maliyetle altyapı risk önceliklendirmesine uygun, istatistiksel açıdan farklılaştırılmış çok noktalı doluluk verisi üretebildiğini göstermektedir. Bileşik TRİ metriği, konumları yalnızca anlık tepe değerleriyle değil; birden fazla parametre üzerinden sıralamayı mümkün kılmaktadır.

Sistem, Düğüm 1'i (Barajyolu alt geçidi) tüm ölçülen parametreler açısından en yüksek riskli konum olarak doğru biçimde belirlemiştir — bu sonuç, bilinen yerel taşkın geçmişiyle örtüşmektedir. Referans düğüm olan Düğüm 3 (Sinanpaşa), tüm oturumlarda kararlı ve düşük doluluk sergileyerek karşılaştırmalı ölçüm tasarımını doğrulamıştır.

Temel kısıt, yalnızca 3 günlük saha penceresidir. Sistemin planlama açısından değeri, veri süresiyle orantılı olarak artar — anlamlı eğilim çıkarımı ve altyapı önceliklendirme önerileri için en az 3 aylık sürekli veri gereklidir.

---

## Lisans

[MIT Lisansı](LICENSE) — Telif Hakkı (c) 2026 TAŞKIN Projesi

---

<div align="center">
<sub>TAŞKIN Projesi · Adana Pilot Sahası · 2026</sub>
</div>
