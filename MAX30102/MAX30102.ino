#include <Wire.h>
#include "MAX30105.h"
#include "DHT.h"

#define DHTPIN 19
#define DHTTYPE DHT11

MAX30105 particleSensor;
DHT dht(DHTPIN, DHTTYPE);

int gasPin = 34;   // MQ9 analog pin

void setup()
{
  Serial.begin(115200);
  Serial.println("ESP32 Multi Sensor Test");

  // Start DHT11
  dht.begin();

  // Start I2C for MAX30102
  Wire.begin(21,22);

  if (!particleSensor.begin(Wire))
  {
    Serial.println("MAX30102 not found. Check wiring.");
    while (1);
  }

  Serial.println("MAX30102 initialized");

  particleSensor.setup();
}

void loop()
{
  // -------- MAX30102 --------
  long irValue = particleSensor.getIR();
  long redValue = particleSensor.getRed();

  // -------- MQ9 Gas Sensor --------
  int gasValue = analogRead(gasPin);

  // -------- DHT11 --------
  float humi  = dht.readHumidity();
  float tempC = dht.readTemperature();
  float tempF = dht.readTemperature(true);

  Serial.println("------------- SENSOR DATA -------------");

  // MAX30102
  Serial.print("IR Value: ");
  Serial.print(irValue);
  Serial.print("  | RED Value: ");
  Serial.println(redValue);

  // MQ9
  Serial.print("Gas Sensor Value: ");
  Serial.println(gasValue);

  // DHT11
  if (isnan(humi) || isnan(tempC) || isnan(tempF)) {
    Serial.println("Failed to read from DHT11 sensor!");
  } else {
    Serial.print("Humidity: ");
    Serial.print(humi);
    Serial.print("%  | Temperature: ");
    Serial.print(tempC);
    Serial.print("°C  ");
    Serial.print(tempF);
    Serial.println("°F");
  }

  Serial.println("---------------------------------------");

  delay(2000);
}