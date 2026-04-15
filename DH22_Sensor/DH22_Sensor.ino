#include <Wire.h>
#include "MAX30105.h"

MAX30105 particleSensor;

void setup()
{
  Serial.begin(115200);
  Serial.println("MAX30102 Test");

  Wire.begin(21,22);

  if (!particleSensor.begin(Wire))
  {
    Serial.println("MAX30102 not found. Check wiring.");
    while (1);
  }

  Serial.println("Sensor initialized");

  particleSensor.setup(); 
}

void loop()
{
  long irValue = particleSensor.getIR();
  long redValue = particleSensor.getRed();

  Serial.print("IR: ");
  Serial.print(irValue);

  Serial.print("  RED: ");
  Serial.println(redValue);

  delay(500);
}