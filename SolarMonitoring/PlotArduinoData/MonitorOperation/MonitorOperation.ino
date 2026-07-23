
// This program reads the voltage at given Arduino Uno R3 input pins.
// For the Arduino Uno R3, the input voltage
// to those pins cannot exceed 5vdc.

#define voltageReference 5.0f

// Identify the input pins.
#define inputPin_A A1
#define inputPin_B A2

void setup()
{
  Serial.begin(9600); // match this speed in your Python script
  while(!Serial) Wait(100); // make sure Serial is ready
  
  // Configure analog input pins.
  pinMode(inputPin_A, INPUT);
  pinMode(inputPin_B, INPUT);

  // Burn the first reading to allow the reference voltage to stabilize
  analogRead(inputPin_A);
  Wait(100);
  analogRead(inputPin_B);
  Wait(100);
}

void loop()
{
  // Get the ADC values for each input pin.
  float adcValue_A = analogRead(inputPin_A);
  float adcValue_B = analogRead(inputPin_B);

  // Convert the 10-bit ADC reading to actual voltage.
  // Arduino Uno R3 is limited to 10-bit ADC.
  float actualVoltage_A = (adcValue_A / 1023.0f) * voltageReference;
  float actualVoltage_B = (adcValue_B / 1023.0f) * voltageReference;
  
  // Convert actual voltage to unfiltered input voltage.
  // In this case, we are reducing input voltage by 5.
  // This is completely different from Arduino Uno R3 reference voltage.
  // The raw input voltage can be as high as 25vdc.
  float inputVoltage_A = actualVoltage_A * 5.0f;
  float inputVoltage_B = actualVoltage_B * 5.0f;
  
  // Print data separated by a space or comma (required for plotter and easy for Python)
  Serial.print(inputVoltage_A);
  Serial.print(",");
  Serial.println(inputVoltage_B); 
  
  Wait(1000); // Control the data rate
}


// Wait for a specific number of milliseconds.
// delay() is blocking so we do not use that.
// This approach does not use hardware-specific timers.
void Wait(long milliseconds)
{
  long beginTime = millis();
  uint8_t doSomething = 00;
  while ((millis() - beginTime) <= milliseconds) doSomething++;
}
