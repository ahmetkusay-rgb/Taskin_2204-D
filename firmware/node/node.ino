#include <WiFi.h>
#include <esp_now.h>


#define NODE_ID 1
#define TRIG_PIN 5
#define ECHO_PIN 18
#define BUTTON_PIN 25
#define TANK_YUKSEKLIK_CM 100
#define SENSOR_OFFSET_CM 25  // Probe height above the maximum water surface
#define ALARM_THRESHOLD 80

// JSN-SR04T ayarlari
#define ECHO_TIMEOUT 150000UL   // 150 ms - JSN yankisi HC-SR04'ten gec doner
#define OLCUM_SAYISI 5          // medyan icin alinacak ornek sayisi
#define SENSOR_MIN_CM 20        // JSN-SR04T ~20 cm altini guvenilir olcemez

typedef struct {
  int node_id;
  float doluluk;
  int alarm;
} veri_paketi;

veri_paketi gonderilecek;

uint8_t broadcastAddress[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

// Son gecerli doluluk - kotu okuma gelince buna geri donulur
bool radyoHazir = false;

// Tek bir mesafe olcumu. Basarisizsa -1 doner.
long tekOlcum() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(4);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  unsigned long sure = pulseIn(ECHO_PIN, HIGH, ECHO_TIMEOUT);
  if (sure == 0)
    return -1;                       // yanki yok / timeout

  long mesafe = (long)(sure * 0.0343 / 2.0);

  // Fiziksel olarak imkansiz okumalari ele
  if (mesafe < SENSOR_MIN_CM || mesafe > 600)
    return -1;

  return mesafe;
}

// Birden fazla olcum alir, medyanini doner. Tum olcumler basarisizsa -1.
long mesafeOlc() {
  long okumalar[OLCUM_SAYISI];
  int gecerli = 0;

  for (int i = 0; i < OLCUM_SAYISI; i++) {
    long o = tekOlcum();
    if (o > 0) {
      okumalar[gecerli] = o;
      gecerli++;
    }
    delay(60);   // JSN olcumler arasi en az ~50-60 ms ister
  }

  if (gecerli == 0)
    return -1;   // hicbir olcum tutmadi

  // Basit kabarcik siralama (kucuk dizi, sorun degil) -> medyan
  for (int i = 0; i < gecerli - 1; i++) {
    for (int j = 0; j < gecerli - 1 - i; j++) {
      if (okumalar[j] > okumalar[j + 1]) {
        long t = okumalar[j];
        okumalar[j] = okumalar[j + 1];
        okumalar[j + 1] = t;
      }
    }
  }
  return okumalar[gecerli / 2];
}

void setup() {
  Serial.begin(115200);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  digitalWrite(TRIG_PIN, LOW);

  WiFi.mode(WIFI_STA);
  WiFi.disconnect();

  if (esp_now_init() != ESP_OK) {
    Serial.println("ESP NOW BASLATILAMADI");
    return;
  }

  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, broadcastAddress, 6);
  peerInfo.channel = 0;
  peerInfo.encrypt = false;

  if (esp_now_add_peer(&peerInfo) != ESP_OK) {
    Serial.println("PEER EKLENEMEDI");
    return;
  }
  radyoHazir = true;
}

// =======================
void loop() {
  unsigned long baslangic = millis();
  if (!radyoHazir) { delay(1000); return; }
  long mesafe = mesafeOlc();

  float doluluk;
  if (mesafe < 0) {
    // Do not present a stale value as a fresh measurement.
    Serial.println("OLCUM HATASI - veri gonderilmedi");
    delay(1000);
    return;
  } else {

    // float aritmetigi - map() yerine. Bos boru = %0, dolu = %100
    doluluk = (float)(TANK_YUKSEKLIK_CM + SENSOR_OFFSET_CM - mesafe) / TANK_YUKSEKLIK_CM * 100.0;

    if (doluluk < 0)   doluluk = 0.0;
    if (doluluk > 100) doluluk = 100.0;

  }

  int alarm = (doluluk >= ALARM_THRESHOLD) ? 1 : 0;
  if (digitalRead(BUTTON_PIN) == LOW) {
    alarm = 0;
    delay(300);
  }

  // Hata ayiklama: olcumu seri porta yaz
  Serial.print("Mesafe: ");
  Serial.print(mesafe);
  Serial.print(" cm  ->  Doluluk: ");
  Serial.print(doluluk);
  Serial.println(" %");

  // Paketi Doldur
  gonderilecek.node_id = NODE_ID;
  gonderilecek.doluluk = doluluk;
  gonderilecek.alarm = alarm;

  // Gönder
  esp_err_t result = esp_now_send(broadcastAddress, (uint8_t *)&gonderilecek,
                                  sizeof(gonderilecek));

  if (result == ESP_OK) {
    Serial.println("Gonderildi Basarili");
  } else {
    Serial.println("Gonderim Hatasi");
  }

  unsigned long gecen = millis() - baslangic;
  if (gecen < 1000) delay(1000 - gecen);
}
