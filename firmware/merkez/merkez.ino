#include <SD.h>
#include <SPI.h>
#include <WiFi.h>
#include <esp_now.h>
#include <math.h>
#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>


#define SD_CS_PIN 10
#define SD_SCK 12
#define SD_MISO 13
#define SD_MOSI 11

// SD kurtarma ayarlari
#define SD_RETRY_COOLDOWN_MS 5000UL   // basarisiz init sonrasi tekrar denemeden once bekleme
#define LOG_DOSYA "/veri_log.csv"
#define LOG_BASLIK "zaman_ms,node_id,doluluk,alarm"

typedef struct {
  int node_id;
  float doluluk;
  int alarm;
} veri_paketi;
QueueHandle_t paketKuyrugu = nullptr;

// SD durumu - kart cikar/takilirsa veya yazma duserse kurtarma icin izlenir
bool sdHazir = false;
unsigned long sonSdDeneme = 0;

// SD karti baslatir ve baslik satirini garanti eder. Basarili olursa true doner.
bool sdBaslat() {
  SD.end();   // onceki (bozuk) durumu temizle
  if (!SD.begin(SD_CS_PIN)) {
    return false;
  }
  // Baslik satiri yoksa olustur
  if (!SD.exists(LOG_DOSYA)) {
    File dosya = SD.open(LOG_DOSYA, FILE_WRITE);
    if (!dosya) {
      return false;
    }
    size_t yazilan = dosya.println(LOG_BASLIK);
    dosya.close();
    if (yazilan == 0) return false;
  }
  return true;
}

// SD hazir degilse, cooldown gozeterek yeniden baglanmayi dener.
void sdKurtarmaDene() {
  if (sdHazir)
    return;
  unsigned long simdi = millis();
  if (simdi - sonSdDeneme < SD_RETRY_COOLDOWN_MS)
    return;   // cok sik deneme yapma - SD.begin bloklayabilir
  sonSdDeneme = simdi;

  if (sdBaslat()) {
    sdHazir = true;
    Serial.println("SD_RECOVERED");
  }
}

// Tek bir satiri SD'ye yazar. Yazma duserse SD'yi bozuk isaretler.
// Basariyi (true/false) doner.
bool sdSatirYaz(int node_id, float doluluk, int alarm) {
  File dosya = SD.open(LOG_DOSYA, FILE_APPEND);
  if (!dosya) {
    sdHazir = false;   // kart cikarilmis veya FS bozulmus olabilir -> kurtarma tetikle
    return false;
  }
  unsigned long zaman = millis();
  char satir[80];
  int uzunluk = snprintf(satir, sizeof(satir), "%lu,%d,%.1f,%d\n", zaman, node_id, doluluk, alarm);
  size_t yazilan = dosya.print(satir);
  dosya.close();
  if (yazilan != (size_t)uzunluk) sdHazir = false;
  return sdHazir;
}

void sdKartaYaz(int node_id, float doluluk, int alarm) {
  // SD dusmusse once kurtarmayi dene
  if (!sdHazir)
    sdKurtarmaDene();

  if (!sdHazir) {
    Serial.printf("SD_FAIL,%d\n", node_id);   // server.py bu satiri yok sayar
    return;
  }

  if (sdSatirYaz(node_id, doluluk, alarm)) {
    Serial.printf("SD_OK,%d\n", node_id);
  } else {
    // Yazma dustu -> aninda bir kez kurtarip tekrar dene
    sonSdDeneme = millis() - SD_RETRY_COOLDOWN_MS;
    sdKurtarmaDene();
    if (sdHazir && sdSatirYaz(node_id, doluluk, alarm)) {
      Serial.printf("SD_OK,%d\n", node_id);
    } else {
      Serial.printf("SD_FAIL,%d\n", node_id);
    }
  }
}


void OnDataRecv(const esp_now_recv_info *info, const uint8_t *incomingData, int len) {
  if (len != sizeof(veri_paketi))
    return;

  veri_paketi gelen;
  memcpy(&gelen, incomingData, sizeof(gelen));


  if (gelen.node_id < 1 || gelen.node_id > 10)
    return;
  if (!isfinite(gelen.doluluk) || gelen.doluluk < 0 || gelen.doluluk > 100)
    return;

  gelen.doluluk = constrain(gelen.doluluk, 0.0f, 100.0f);

  if (gelen.alarm != 0 && gelen.alarm != 1)
    gelen.alarm = 0;


  // Wi-Fi callback must not block on serial output or SD writes.
  xQueueSend(paketKuyrugu, &gelen, 0);
}

void setup() {
  Serial.begin(115200);
  paketKuyrugu = xQueueCreate(32, sizeof(veri_paketi));
  if (!paketKuyrugu) {
    Serial.println("QUEUE_INIT_FAILED");
    return;
  }

  WiFi.mode(WIFI_STA);
  WiFi.disconnect();


  SPI.begin(SD_SCK, SD_MISO, SD_MOSI, SD_CS_PIN);
  sdHazir = sdBaslat();
  if (sdHazir) {
    Serial.println("SD_READY");
  } else {
    Serial.println("SD_FAIL,0");   // kart yoksa kurtarma loop'ta devreye girer
  }


  if (esp_now_init() != ESP_OK) {
    Serial.println("ESP NOW BASLATILAMADI");
    return;
  }

  esp_now_register_recv_cb(OnDataRecv);
}

void loop() {
  // SD dusmusse arka planda yeniden baglanmayi dene (paket beklemeden)
  if (!sdHazir)
    sdKurtarmaDene();

  veri_paketi gelen;
  if (paketKuyrugu && xQueueReceive(paketKuyrugu, &gelen, pdMS_TO_TICKS(20)) == pdTRUE) {
    Serial.printf("%d,%.1f,%d\n", gelen.node_id, gelen.doluluk, gelen.alarm);
    sdKartaYaz(gelen.node_id, gelen.doluluk, gelen.alarm);
  } else {
    delay(1);
  }
}
