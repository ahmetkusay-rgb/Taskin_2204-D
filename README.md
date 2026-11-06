# TAŞKIN — Kentsel su seviyesi izleme

[English](README_EN.md) · [Geliştirici rehberi](docs/DEVELOPMENT.md) · [Bağlantılar](docs/hardware/baglanti_semasi.md) · [Malzeme listesi](docs/hardware/malzeme_listesi.md)

**Yağmur suyu hatlarında neresi daha çok, daha uzun ve daha hızlı doluyor?** TAŞKIN, farklı noktalardan su seviyesi verisi toplayıp bakım ve altyapı önceliklendirmesinde kullanılabilecek karşılaştırmalı bir gösterge üretmeyi amaçlayan bir prototiptir.

![TAŞKIN harita panosu](docs/images/dashboard.jpg)

## Nasıl çalışıyor?

Ultrasonik sensörler doluluk seviyesini ölçer. ESP32 düğümleri ölçümleri ESP-NOW ile merkez birime gönderir. Merkez veriyi SD karta kaydeder; bilgisayardaki Python köprüsü canlı haritaya aktarır. Ayrı analiz aracı beş ölçütü birleştirerek **TAŞKIN Risk İndeksi (TRİ)** hesaplar: ortalama, en yüksek doluluk, %80 ve üzerindeki süre, eşik geçiş sayısı ve 60 saniyelik pencerede artış hızı.

![Sistem mimarisi](docs/images/architecture.png)

## Bu depoda ne var?

| Bölüm | İçerik |
|---|---|
| [Firmware](firmware) | ESP32 sensör düğümü ve ESP32-S3 merkez kodu |
| [Pano ve köprü](software) | Yerel bilgisayarda çalışan harita ve seri port sunucusu |
| [Analiz](analysis/tri_score.py) | CSV’den TRİ hesabı ve grafik üretimi |
| [Ölçüm dosyaları](data/samples) | Saha ölçümlerinin CSV kayıtları |
| [Oturum günlüğü](data/session_log.md) | Ölçüm tarihleri, yerleri ve oturum bilgileri |

## Adana pilotu

Barajyolu, Turgut Özal ve Sinanpaşa noktalarının depodaki verileriyle yeniden hesaplanan sonuçlar:

| Nokta | TRİ (0–100) | Prototip sınıfı |
|---|---:|---|
| Barajyolu | 91,3 | Kritik |
| Turgut Özal | 48,6 | Orta |
| Sinanpaşa | 9,4 | Düşük |

![Saha düğümü](docs/images/field_node1_barajyolu.jpg)

Bu değerler **taşkın olasılığı yüzdesi değildir**. Karşılaştırılan noktalar ve gözlem süreleri sonucu etkiler. Oturumlar farklı gün ve yağış koşullarındadır; sıralama tek başına konumların kalıcı risk farkını kanıtlamaz. Mevcut dosyalar değiştirilmeden hesaplama aracıyla sonuçlar yeniden üretilebilir.

## Denemek veya geliştirmek

Python 3.12 ile, depo klasöründe:

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python analysis/tri_score.py
python analysis/tri_score.py --chart
```

Canlı pano için merkez cihazı USB ile bağlayıp `python software/server.py --port COM12` çalıştırın; port adını kendi cihazınıza göre değiştirin. Ardından [yerel panoyu](http://127.0.0.1:8080/index.html) açın. `--port` verilmezse tanınan USB seri cihazı aranır. **Bu GitHub sayfası canlı pano değildir.** Harita ve dış kütüphaneler için internet gerekir.

Donanımı yeniden kurmadan önce [geliştirici rehberini](docs/DEVELOPMENT.md) ve [güncel pin tablosunu](docs/hardware/baglanti_semasi.md) okuyun. Eski rapor görsellerindeki merkez pinleri S3 için doğrudan kullanılamaz.

## Sınırlar ve sonraki adımlar

- Üç düğümlü prototip; uzun dönem ve farklı yağışlarda doğrulama gerekiyor.
- Canlı pano bilgisayar gerektirir. SD zamanları açılıştan itibaren milisaniyedir; gerçek tarih/saat için oturum başlangıcı gerekir.
- Sensörün kör bölgesi, montaj yüksekliği, köpük ve türbülans ölçümü etkiler. Güncel kodda geçersiz ölçüm yeni veri olarak gönderilmez.
- Pil süresi için eski belgelerde 10–12 ve 13–14 saat gibi farklı değerler bulunuyordu; aynı kurulumda kayıtlı tekrar testi yapılmadan tek bir doğrulanmış süre sunulmuyor.
- TRİ eşit ağırlıklı bir araştırma göstergesidir; sınıf eşikleri bağımsız saha doğrulaması gerektirir. Operasyonel erken uyarı sistemi olarak doğrulanmış değildir.

Geliştirme önerileri ve sorun bildirimleri için [Issues](https://github.com/ahmetkusay-rgb/Taskin_2204-D/issues) kullanılabilir. Kod [MIT lisanslıdır](LICENSE).
