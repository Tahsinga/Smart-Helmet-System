#include <Wire.h>
#include "MAX30105.h"
#include "spo2_algorithm.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include "DHT.h"

// ================= DHT =================
#define DHTPIN 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// ================= MPU6050 =================
const int MPU_ADDR = 0x68;

float AccX, AccY, AccZ;
float GyroX, GyroY;

float fusedAngleX = 0, fusedAngleY = 0;
float initialAngleX = 0, initialAngleY = 0;
bool calibrated = false;

float dt;
unsigned long prevTime;

// ================= MAX30102 =================
MAX30105 particleSensor;

uint32_t irBuffer[100];
uint32_t redBuffer[100];

int32_t bufferLength = 100;
int32_t spo2;
int8_t validSPO2;
int32_t heartRate;
int8_t validHeartRate;

// ================= MQ9 =================
int gasPin = 34;

// ================= BUZZER =================
const int buzzerPin = 19;

// ================= WIFI =================
const char* ssid = "TASHINGA";
const char* password = "1234567890";
const char* servername = "http://172.16.13.133:8000/api/sensor-data/";
const char* device_id = "HELMET_001";

// ================= FALL =================
bool fallDetected = false;

void setup() {
  Serial.begin(115200);

  pinMode(2, OUTPUT);
  pinMode(buzzerPin, OUTPUT);
  digitalWrite(buzzerPin, LOW);

  // WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("Connecting...");
  }
  Serial.println("WiFi Connected");

  // I2C
  Wire.begin(21, 22);

  // MPU INIT
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission(true);

  delay(2000);
  prevTime = millis();

  // MAX30102
  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) {
    Serial.println("MAX30102 not found!");
    while (1);
  }
  particleSensor.setup();

  // DHT
  dht.begin();
}

// ===== BETTER DHT READ FUNCTION =====
float readHumiditySafe() {
  float h = dht.readHumidity();
  if (isnan(h)) {
    delay(100);
    h = dht.readHumidity();
  }
  return isnan(h) ? 0 : h;
}

float readTempSafe() {
  float t = dht.readTemperature();
  if (isnan(t)) {
    delay(100);
    t = dht.readTemperature();
  }
  return isnan(t) ? 0 : t;
}

void loop() {

  // ================= MPU =================
  unsigned long currentTime = millis();
  dt = (currentTime - prevTime) / 1000.0;
  prevTime = currentTime;

  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 14, true);

  AccX = (Wire.read() << 8 | Wire.read()) / 16384.0;
  AccY = (Wire.read() << 8 | Wire.read()) / 16384.0;
  AccZ = (Wire.read() << 8 | Wire.read()) / 16384.0;

  Wire.read(); Wire.read();

  GyroX = (Wire.read() << 8 | Wire.read()) / 131.0;
  GyroY = (Wire.read() << 8 | Wire.read()) / 131.0;

  // MOTION (REAL)
  float accMagnitude = sqrt(AccX * AccX + AccY * AccY + AccZ * AccZ);
  float motionValue = abs(accMagnitude - 1.0); // gravity removed

  // FALL DETECTION
  if (motionValue < 1.5) {
    fallDetected = true;
    Serial.println("🚨 FALL DETECTED");
  } else {
    fallDetected = false;
  }

  // ================= MAX30102 =================
  for (byte i = 0; i < bufferLength; i++) {
    while (!particleSensor.available()) particleSensor.check();
    redBuffer[i] = particleSensor.getRed();
    irBuffer[i] = particleSensor.getIR();
    particleSensor.nextSample();
  }

  maxim_heart_rate_and_oxygen_saturation(
    irBuffer, bufferLength, redBuffer,
    &spo2, &validSPO2,
    &heartRate, &validHeartRate);

  // ================= OTHER =================
  int gasValue = analogRead(gasPin);

  float humi = readHumiditySafe();
  float tempC = readTempSafe();

  // ================= DEBUG =================
  Serial.println("------ DATA ------");
  Serial.println("Temp: " + String(tempC));
  Serial.println("Humidity: " + String(humi));
  Serial.println("Motion: " + String(motionValue));

  // ================= ALARM =================
  bool alarmActive = fallDetected || gasValue > 500 || (validSPO2 && spo2 < 90);
  digitalWrite(buzzerPin, alarmActive ? HIGH : LOW);

  // ================= SEND =================
  if (WiFi.status() == WL_CONNECTED) {

    HTTPClient http;
    http.begin(servername);
    http.addHeader("Content-Type", "application/json");

    String jsonData = "{";
    jsonData += "\"device_id\":\"" + String(device_id) + "\",";
    jsonData += "\"heart_rate\":" + String(validHeartRate ? heartRate : 0) + ",";
    jsonData += "\"spo2\":" + String(validSPO2 ? spo2 : 0) + ",";
    jsonData += "\"gas_level\":" + String(gasValue) + ",";
    jsonData += "\"temperature\":" + String(tempC) + ",";
    jsonData += "\"humidity\":" + String(humi) + ",";
    jsonData += "\"motion\":" + String(motionValue) + ",";
    jsonData += "\"fall_detected\":" + String(fallDetected ? 1 : 0);
    jsonData += "}";

    Serial.println(jsonData);

    http.POST(jsonData);
    http.end();
  }

  delay(500); // 🔥 faster loop (important)
}