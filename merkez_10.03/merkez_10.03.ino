#include <SD.h>
#include <SPI.h>
#include <WiFi.h>
#include <esp_now.h>


#define SD_CS_PIN 10
#define SD_SCK 12
#define SD_MISO 13
#define SD_MOSI 11

typedef struct {
  int node_id;
  float doluluk;
  int alarm;
} veri_paketi;

void sdKartaYaz(int node_id, float doluluk, int alarm) {
  File dosya = SD.open("/veri_log.csv", FILE_APPEND);
  if (!dosya)
    return;

  unsigned long zaman = millis();
  dosya.printf("%lu,%d,%.1f,%d\n", zaman, node_id, doluluk, alarm);
  dosya.close();

  
  Serial.printf("SD_OK,%d\n", node_id);
}


void OnDataRecv(const esp_now_recv_info *info, const uint8_t *incomingData, int len) {
  if (len != sizeof(veri_paketi))
    return;

  veri_paketi gelen;
  memcpy(&gelen, incomingData, sizeof(gelen));

  
  if (gelen.node_id < 1 || gelen.node_id > 10)
    return;
    
  gelen.doluluk = constrain(gelen.doluluk, 0.0f, 100.0f);
  
  if (gelen.alarm != 0 && gelen.alarm != 1)
    gelen.alarm = 0;

  
  Serial.printf("%d,%.1f,%d\n", gelen.node_id, gelen.doluluk, gelen.alarm);

  sdKartaYaz(gelen.node_id, gelen.doluluk, gelen.alarm);
}

void setup() {
  Serial.begin(115200);

  WiFi.mode(WIFI_STA);
  WiFi.disconnect();

 
  SPI.begin(SD_SCK, SD_MISO, SD_MOSI, SD_CS_PIN);
  if (SD.begin(SD_CS_PIN)) {
    if (!SD.exists("/veri_log.csv")) {
      File dosya = SD.open("/veri_log.csv", FILE_WRITE);
      if (dosya) {
        dosya.println("zaman_ms,node_id,doluluk,alarm");
        dosya.close();
      }
    }
  }

  
  if (esp_now_init() != ESP_OK) {
    Serial.println("ESP NOW BASLATILAMADI");
    return;
  }

  esp_now_register_recv_cb(OnDataRecv);
}

void loop() {
  
  delay(1000); 
}
