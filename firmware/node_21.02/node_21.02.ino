#include <WiFi.h>
#include <esp_now.h>


#define NODE_ID 3
#define TRIG_PIN 5
#define ECHO_PIN 18
#define BUTTON_PIN 25
#define TANK_YUKSEKLIK_CM 100
#define ALARM_THRESHOLD 80

typedef struct {
  int node_id;
  float doluluk;
  int alarm;
} veri_paketi;

veri_paketi gonderilecek;

uint8_t broadcastAddress[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

long mesafeOlc() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long sure = pulseIn(ECHO_PIN, HIGH, 60000);
  if (sure == 0)
    return -1;
  return sure * 0.034 / 2;
}

void setup() {
  Serial.begin(115200);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);

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
}

// =======================
void loop() {
  long mesafe = mesafeOlc();
  if (mesafe < 0 || mesafe > TANK_YUKSEKLIK_CM)
    mesafe = TANK_YUKSEKLIK_CM;

  float doluluk = map(mesafe, TANK_YUKSEKLIK_CM, 0, 0, 100);
  if (doluluk < 0)
    doluluk = 0.0;
  if (doluluk > 100)
    doluluk = 100.0;

  int alarm = (doluluk > ALARM_THRESHOLD) ? 1 : 0;
  if (digitalRead(BUTTON_PIN) == LOW) {
    alarm = 0;
    delay(300);
  }

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

  delay(1000);
}