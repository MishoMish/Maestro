// Маестро - hardware test. Upload, then:
//  * every LED lights once at start (До..До)
//  * pressing a key lights its LED, plays its note and shows it on the LCD
//  * the knob value is shown on line 2
// If a key shows the wrong name, read the "A0=" value and adjust KEY_STEP.
#include <LiquidCrystal.h>

LiquidCrystal lcd(12, 11, 5, 4, 3, 2);          // RS, E, D4, D5, D6, D7 (kit wiring)
const int PIEZO = 8;
const int KEYS  = A0;                             // all 8 buttons, resistor ladder
const int KNOB  = A1;
const int LEDS[8] = {6, 7, 9, 10, 13, A2, A3, A4};
const int NOTE_HZ[8] = {262, 294, 330, 349, 392, 440, 494, 523};  // C4..C5
const char* NAMES[8] = {"Do", "Re", "Mi", "Fa", "Sol", "La", "Si", "Do'"};
const int KEY_STEP = 128;   // ladder: key1 ~1023, key2 ~895 ... key8 ~128

int readKey() {             // returns 0..7, or -1 if nothing is pressed
  int v = analogRead(KEYS);
  int level = (v + KEY_STEP / 2) / KEY_STEP;   // 0 = none, 8 = key 1
  if (level < 1) return -1;
  if (level > 8) level = 8;
  return 8 - level;
}

void setup() {
  lcd.begin(16, 2);
  lcd.print("MAESTRO test");
  for (int i = 0; i < 8; i++) pinMode(LEDS[i], OUTPUT);
  for (int i = 0; i < 8; i++) { digitalWrite(LEDS[i], HIGH); delay(150); digitalWrite(LEDS[i], LOW); }
}

void loop() {
  int k = readKey();
  for (int i = 0; i < 8; i++) digitalWrite(LEDS[i], i == k ? HIGH : LOW);
  if (k >= 0) tone(PIEZO, NOTE_HZ[k]); else noTone(PIEZO);

  lcd.setCursor(0, 0);
  lcd.print(k >= 0 ? NAMES[k] : "-   ");
  lcd.print("   A0=");
  lcd.print(analogRead(KEYS));
  lcd.print("    ");
  lcd.setCursor(0, 1);
  lcd.print("knob=");
  lcd.print(analogRead(KNOB));
  lcd.print("      ");
  delay(30);
}
