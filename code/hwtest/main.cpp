// Маестро hardware test: pio run -e hwtest -t upload
//  * every LED lights once at start (До..До')
//  * pressing a key lights its LED, plays its note and shows it on the LCD
//  * the LCD and Serial (115200) show the raw A0 and A1 values
#include <Arduino.h>
#include <LiquidCrystal.h>

LiquidCrystal lcd(12, 11, 5, 4, 3, 2);
const int PIEZO = 8;
const int KEYS = A0;
const int KNOB = A1;
const int LEDS[8] = {6, 7, 9, 10, 13, A2, A3, A4};
const int NOTE_HZ[8] = {262, 294, 330, 349, 392, 440, 494, 523};
const char* NAMES[8] = {"Do", "Re", "Mi", "Fa", "Sol", "La", "Si", "Do'"};
const int KEY_STEP = 128;

int readKey(int value) {
  int level = (value + KEY_STEP / 2) / KEY_STEP;
  if (level < 1) return -1;
  if (level > 8) level = 8;
  return 8 - level;
}

void setup() {
  Serial.begin(115200);
  lcd.begin(16, 2);
  lcd.print("MAESTRO test");
  for (int i = 0; i < 8; i++) pinMode(LEDS[i], OUTPUT);
  for (int i = 0; i < 8; i++) {
    digitalWrite(LEDS[i], HIGH);
    delay(150);
    digitalWrite(LEDS[i], LOW);
  }
}

void loop() {
  int keys = analogRead(KEYS);
  int knob = analogRead(KNOB);
  int key = readKey(keys);
  for (int i = 0; i < 8; i++) digitalWrite(LEDS[i], i == key ? HIGH : LOW);
  if (key >= 0) tone(PIEZO, NOTE_HZ[key]);
  else noTone(PIEZO);

  lcd.setCursor(0, 0);
  lcd.print(key >= 0 ? NAMES[key] : "-  ");
  lcd.print("  A0=");
  lcd.print(keys);
  lcd.print("    ");
  lcd.setCursor(0, 1);
  lcd.print("knob=");
  lcd.print(knob);
  lcd.print(" tick=");
  lcd.print(knob * 7L / 1024 + 1);
  lcd.print(" ");

  Serial.print("A0=");
  Serial.print(keys);
  Serial.print(" key=");
  Serial.print(key >= 0 ? NAMES[key] : "-");
  Serial.print(" A1=");
  Serial.print(knob);
  Serial.print(" tick=");
  Serial.println(knob * 7L / 1024 + 1);
  delay(100);
}
