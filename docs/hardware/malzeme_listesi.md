# Malzeme Listesi (Bill of Materials)

TAŞKIN sistemi için kullanılan tüm donanım bileşenleri. Toplam: 1 merkez birim + 3 sensör düğümü.

> **Sensör notu:** İlk prototip aşamasında **HC-SR04** ultrasonik sensör kullanılmış, ardından su geçirmez gövdesi ve daha kararlı saha performansı nedeniyle **JSN-SR04T** sensöre geçilmiştir. Güncel kurulumda ve aşağıdaki listede sensör **JSN-SR04T**'dir.

## Merkez Birim (1 adet)

| Grup | Bileşen | Fonksiyon / Açıklama | Miktar |
|---|---|---|---|
| Merkez | ESP32-S3-N16R8 WiFi/BT Board | Merkez işlemci | 1 |
| Merkez | Micro SD Kart Modülü | Veri yazma (SPI) | 1 |
| Merkez | 16 GB Micro SD Kart | Veri depolama | 1 |

## Sensör Düğümleri (3 adet, özdeş)

| Grup | Bileşen | Fonksiyon / Açıklama | Miktar |
|---|---|---|---|
| Node | ESP32-WROOM-32U Board | Node işlemcisi | 3 |
| Node | **JSN-SR04T Su Geçirmez Ultrasonik Sensör** | Suya temassız mesafe ölçümü (su geçirmez prob) | 3 |
| Node | 3.7V 1800 mAh Li-Po Pil | Node güç kaynağı | 3 |
| Node | TP4056 Lityum Şarj Modülü | 3.7V pili güvenli şarj etme | 3 |
| Node | MT3608 Voltaj Yükseltici | 3.7V → 5V voltaj dönüştürücü | 3 |
| Node | GSM Anten | Kablosuz haberleşme menzil artırıcı | 3 |
| Node | IPEX – SMA Dişi Kablo | Anteni ESP32'ye bağlayan ara kablo | 3 |
| Node | 11×11×7 cm Termoplastik Buat Kutu | Düğümleri dış ortamdan koruma (IP67) | 3 |
| Node | Conta | Düğümlerin sızdırmazlığını sağlama | — |
| Node | Silica Jel | Kutu içi nemlenmeyi önleme | — |

## Yardımcı Malzemeler

| Grup | Bileşen | Fonksiyon / Açıklama | Miktar |
|---|---|---|---|
| Yardımcı | Plastik Kelepçe | Kutunun sabitlenmesi | — |
| Yardımcı | 10×10 cm Delikli Plaket | Devre kurulumu ve lehimleme alanı | 4 |

> "—" ile gösterilen kalemler ihtiyaca göre/sarf malzeme olarak temin edilir.
