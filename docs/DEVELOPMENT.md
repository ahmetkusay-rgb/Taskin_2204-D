# Geliştirici rehberi

## Ortam ve ilk çalıştırma

Depoyu indirin veya `git clone https://github.com/ahmetkusay-rgb/Taskin_2204-D.git` çalıştırın; depo klasörüne geçin. Python 3.12 kullanın. `python -m venv .venv` ile ortam kurun; Windows'ta `.venv\Scripts\activate`, macOS/Linux'ta `source .venv/bin/activate` ile etkinleştirin. Ardından `python -m pip install -r requirements.txt` çalıştırın.

```sh
python analysis/tri_score.py
python analysis/tri_score.py --method minmax
python analysis/tri_score.py --data-dir data/samples --chart --out chart.png
python -m unittest discover -s tests -v
python software/server.py --port COM12
```

Linux port örneği `/dev/ttyUSB0`, macOS örneği `/dev/cu.usbserial-...`. Portun başka bir seri monitörde açık olmadığından emin olun. Otomatik algılama başarısızsa portu elle belirtin. Linux'ta seri port erişimi için işletim sisteminizin grup izinlerini kontrol edin. HTTP 8080 ve WebSocket 8765 yalnızca `127.0.0.1` adresinde dinler; aynı portlarda başka program çalışmamalı. Pano `http://127.0.0.1:8080/index.html` adresindedir; HTML dosyasına çift tıklamak yerine sunucuyu çalıştırın.

## Firmware

Bu çalışma sırasında kullanılan Python paket sürümleri `requirements-lock.txt` dosyasındadır. Aynı ortamı kurmak için Python 3.12 ile `python -m pip install -r requirements-lock.txt` çalıştırın.

Arduino ESP32 kart paketi 3.3.10 hedeflenir; 2.x alım callback API'si desteklenmez. IDE'de `firmware/node/node.ino` için **ESP32 Dev Module**, `firmware/merkez/merkez.ino` için **ESP32S3 Dev Module** seçin. S3 kartının USB bağlantı türüne göre USB CDC ayarını ve portunu doğrulayın. SD, SPI, WiFi ve ESP-NOW kart paketiyle gelir.

```sh
arduino-cli compile --fqbn esp32:esp32:esp32 firmware/node
arduino-cli compile --fqbn esp32:esp32:esp32s3 firmware/merkez
```

Her düğümün `NODE_ID` değeri farklı olmalı (pano için 1–3). `TANK_YUKSEKLIK_CM` gerçek kanal derinliğidir. `SENSOR_OFFSET_CM`, probun tam dolu yüzeyden yüksekliğidir; 25 cm yalnızca başlangıç örneğidir. Sensörün kör bölgesinin üzerinde montaj payı bırakın. Güncel S3 SD pinleri **12/13/11/10** (SCK/MISO/MOSI/CS); [pin tablosu](hardware/baglanti_semasi.md) esas alınmalıdır. Görseldeki eski 18/19/23/5 eşlemesini kopyalamayın.

ESP-NOW alım callback'i paketi kuyruğa aktarır; SD ve seri yazma ana döngüdedir. 32 paketlik kuyruk dolarsa yeni paket düşebilir; kalıcı teslimat garantisi yoktur. Gönderici ve merkez aynı Wi-Fi kanalında olmalıdır; başka ağa bağlanacak şekilde değiştirilirse kanal ayarları birlikte ele alınmalıdır. Broadcast paketleri şifreli değildir. Node kimliği 1–10 kabul edilir, mevcut pano yalnızca 1–3'ü çizer; yeni düğüm eklerken kart/harita tanımlarını genişletin.

Başarısız sensör okuması gönderilmez; tekrarlayan başarısızlıklarda pano zaman aşımıyla offline olur. Nominal çevrim 1 saniyedir, timeout ve çalışma yükü nedeniyle kesin 1 Hz garantisi yoktur. Merkez seri satırı `node_id,doluluk,alarm`; SD durumları `SD_OK,N`, `SD_FAIL,N`, `SD_RECOVERED`. Başarılı dosya yazması ani güç kaybına karşı kalıcılık garantisi değildir.

## CSV ve hesaplama sözleşmesi

Her ölçüm oturumunu ayrı CSV olarak saklayın. Kabul edilen başlıklar:

```text
timestamp,node_id,konum,mesafe_cm,doluluk_pct,durum
zaman_ms,node_id,doluluk,alarm
```

`timestamp` tarih/saat, `zaman_ms` açılıştan geçen milisaniyedir. Saat dilimsiz zamanlar analizde UTC kabul edilir; yalnızca oturum içi farklar kullanılır. Yerel saatle eşleştirme için [oturum günlüğü](../data/session_log.md) gerekir. Farklı formatlı dosyalar birlikte okunabilir. Saat sıfırlanmaları yeni oturum başlatır. `KAYIP`, sayısal olmayan/sonsuz veya 0–100 dışı okumalar atılır; aynı oturum/düğüm/zaman için son satır tutulur. Ham dosyaları değiştirmeden ayrı bir klasörde çalışın.

E metriği, %80 ve üzerindeki örneğin bir sonraki geçerli örneğe kadar sürdüğü varsayımıyla saniye olarak hesaplanır. Beş saniyeden büyük boşluklar ve oturum sınırları süreye/geçişe katılmaz; son örnek sonrasına süre eklenmez. Artış hızı tam 60 saniyelik pencere gerektirir. Ortalama ve maksimum fiziksel ölçekte, diğer üç ölçüt noktalar arasında min-maks normalize edilir; her birinin ağırlığı 0,20'dir. Eşit değerlerde min-maks katkısı sıfırdır. Tek düğümle göreli indeks anlamlı değildir. E ve F toplam süreye duyarlıdır; adil karşılaştırma için benzer gözlem süresi ve koşullar gerekir. Normalizasyon karşılaştırması ağırlık seçimini veya risk sınıflarını tek başına doğrulamaz.

## Değişiklikleri doğrulama

Python testlerini ve iki firmware derlemesini çalıştırın. Ardından gerçek donanımla boş/tam seviye kalibrasyonu, prob bağlantısının kesilmesi, SD çıkarma/takma, USB koparma ve çoklu düğüm akışını deneyin. Derleme başarısı fiziksel kablolama ve sensör doğruluğunu kanıtlamaz. Harita Leaflet ve uydu haritasını internetten yükler; çevrimdışı kullanım ayrıca geliştirilmelidir.

Kaynaklar: [S3 GPIO](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/gpio.html), [ESP-NOW callback çalışma modeli](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/network/esp_now.html).
