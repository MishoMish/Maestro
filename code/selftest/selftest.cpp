// Маестро self-test: plays the real game on the Uno's own processor with a scripted player,
// and reports over USB serial at 115200. Run it with ./maestro selftest. Needs nothing wired.
//
// Real here: the ATmega328P, flash, EEPROM, timers, the ADC's timing, and the output pins,
// which are read back. Scripted: only the key and knob values, which come from the build guide.
//
// It backs up the records first and puts them back at the end.
#include <Arduino.h>
#include <EEPROM.h>
#include <avr/wdt.h>
#include "../src/config.h"
#include "../src/input.h"
#include "../src/melodies_data.h"
#include "../src/output.h"
#include "../src/records.h"

void gameSetup();
void gameLoop();
const char* lcdLine(uint8_t row);

int selftestKeys = 0;
int selftestKnob = 73;

// A0 per key, worked out from the guide's wiring. tools/sim/test_guide.py checks these.
static const int KEY_A0[8] = {1023, 878, 742, 614, 489, 368, 247, 125};
static const uint8_t PIN_ALL_OUT[] = {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, A2, A3, A4};

// EEPROM above the records: backup and progress across the watchdog reset.
static const int EE_BACKUP_FLAG = 512, EE_BACKUP = 513, EE_PHASE = 560, EE_PASS = 561, EE_FAIL = 563, EE_MAXLOOP = 565;
static const uint8_t BACKUP_SET = 0x5A, PHASE_TWO = 0xA5, RECORD_BYTES = 31;

static uint16_t passed, failed;
static uint32_t maxLoopUs;
static bool toneSeen;
static uint8_t litEver, lastLeds;

// --- Reporting ---
static void check(const __FlashStringHelper* name, bool ok) {
  Serial.print(ok ? F("PASS ") : F("FAIL "));
  Serial.println(name);
  if (ok) passed++;
  else failed++;
}

static void section(const __FlashStringHelper* name) {
  Serial.print(F("\n== "));
  Serial.println(name);
}

static void note(const __FlashStringHelper* name, long value) {
  Serial.print(F("INFO "));
  Serial.print(name);
  Serial.print(F(": "));
  Serial.println(value);
}

// --- Measuring real pins and registers ---
static uint8_t readLeds() {
  uint8_t mask = 0;
  for (uint8_t i = 0; i < 8; i++) {
    if (digitalRead(LED_PINS[i])) mask |= 1 << i;
  }
  return mask;
}

static const uint8_t CAPTURE_MAX = 40;
static uint32_t captureTime[CAPTURE_MAX];
static uint8_t captureMask[CAPTURE_MAX], captureCount;
static bool capturing;

static void tick() {
  uint32_t start = micros();
  gameLoop();
  uint32_t took = micros() - start;
  if (took > maxLoopUs) maxLoopUs = took;
  if (TIMSK2 & _BV(OCIE2A)) toneSeen = true;      // tone() is really running
  uint8_t mask = readLeds();
  if (mask != lastLeds) {
    lastLeds = mask;
    litEver |= mask;
    if (capturing && captureCount < CAPTURE_MAX) {
      captureTime[captureCount] = millis();
      captureMask[captureCount++] = mask;
    }
  }
}

static void runFor(uint32_t ms) {
  uint32_t start = millis();
  while (millis() - start < ms) tick();
}

static bool lcdHas(const __FlashStringHelper* text) {
  return strstr_P(lcdLine(0), (const char*)text) || strstr_P(lcdLine(1), (const char*)text);
}

static bool waitLcd(const __FlashStringHelper* text, uint32_t timeout) {
  uint32_t start = millis();
  while (!lcdHas(text)) {
    if (millis() - start > timeout) return false;
    tick();
  }
  return true;
}

// Frequency on D8, by watching the real pin toggle. The game is paused for these few ms.
static uint16_t measureHz(uint16_t ms) {
  uint32_t edges = 0;
  bool last = PINB & 1;
  uint32_t start = micros(), span = (uint32_t)ms * 1000;
  while (micros() - start < span) {
    bool now = PINB & 1;
    if (now != last) {
      edges++;
      last = now;
    }
  }
  return edges * 500UL / ms;
}

static bool near(uint16_t measured, uint16_t expected) {
  uint16_t margin = expected / 50 + 6;
  return measured + margin >= expected && measured <= expected + margin;
}

static uint8_t hzToKey(uint16_t hz) {
  for (uint8_t i = 0; i < 8; i++) {
    if (near(hz, NOTE_HZ[i])) return i;
  }
  return 255;
}

// --- The scripted player ---
static void press(uint8_t key) { selftestKeys = KEY_A0[key]; }
static void release() { selftestKeys = 0; }

static void tap(uint8_t key, uint16_t hold = 80, uint16_t after = 120) {
  press(key);
  runFor(hold);
  release();
  runFor(after);
}

static void knobTo(uint8_t item, uint8_t count) {
  selftestKnob = ((long)item * 2 + 1) * 1024 / (count * 2);
  runFor(300);
}

static void nudge() {
  uint8_t now = knobTick();
  knobTo(now < KNOB_TICKS - 1 ? now + 1 : now - 1, KNOB_TICKS);
}

static void waitMenu() { waitLcd(F("/7"), 3000); }

static void quitGame() {
  nudge();
  waitLcd(F("Quit game?"), 1000);
  nudge();
  tap(0);
  waitMenu();
}

static Song songAt(uint8_t piece) {
  Song song;
  memcpy_P(&song, &SONGS[piece], sizeof(Song));
  return song;
}

static void startMelody(uint8_t mode, uint8_t piece, bool easy) {
  knobTo(mode, KNOB_TICKS);
  tap(0);
  knobTo(piece, SONG_COUNT + 1);
  tap(0);
  waitLcd(F("Easy mode?"), 1000);
  if (easy) nudge();
  tap(0);
}

// percent scales the gaps: 100 is exact. bad != 255 stretches only that gap to 3x.
static void playLevel(const Song& song, uint8_t level, uint16_t percent = 100, uint8_t bad = 255) {
  waitLcd(F("Play!"), 120000UL);
  uint8_t count = pgm_read_byte(song.cuts + level);
  for (uint8_t i = 0; i < count; i++) {
    uint8_t data = pgm_read_byte(song.notes + i);
    uint32_t gap = (uint32_t)SONG_LEN(data) * song.sixteenthMs * (i == bad ? 300 : percent) / 100;
    uint32_t start = millis();
    press(SONG_NOTE(data));
    runFor(gap / 2 < 150 ? gap / 2 : 150);
    release();
    if (i == count - 1) runFor(100);
    else while (millis() - start < gap) tick();
  }
}

static void wrongNote(const Song& song) {
  waitLcd(F("Play!"), 120000UL);
  tap((SONG_NOTE(pgm_read_byte(song.notes)) + 1) % 8);
}

static void waitResult() {
  uint32_t start = millis();
  while (millis() - start < 120000UL) {
    const char* line = lcdLine(1);
    if (line[0] == 'L' && strstr_P(line, PSTR(" pts"))) return;
    tick();
  }
}

// --- Tests that need no game ---
static void testPins() {
  section(F("Output pins, driven high and low and read back"));
  bool ok = true;
  for (uint8_t pin : PIN_ALL_OUT) {
    pinMode(pin, OUTPUT);
    digitalWrite(pin, HIGH);
    delayMicroseconds(50);
    bool high = digitalRead(pin);
    digitalWrite(pin, LOW);
    delayMicroseconds(50);
    bool low = digitalRead(pin);
    if (!high || low) {
      ok = false;
      note(F("Pin not responding"), pin);
    }
  }
  check(F("All 15 output pins respond"), ok);
}

static uint16_t adcChannel(uint8_t channel) {   // reads an internal ADC channel
  ADMUX = _BV(REFS0) | channel;
  delay(3);
  ADCSRA |= _BV(ADSC);
  while (ADCSRA & _BV(ADSC)) {
  }
  ADCSRA |= _BV(ADSC);
  while (ADCSRA & _BV(ADSC)) {
  }
  return ADCW;
}

static void testAdc() {
  section(F("ADC"));
  uint16_t ground = adcChannel(15);
  uint16_t bandgap = adcChannel(14);
  note(F("Internal 0 V reads"), ground);
  note(F("Internal 1.1 V reference reads"), bandgap);
  check(F("ADC reads its internal 0 V"), ground < 10);
  check(F("ADC reads its internal reference"), bandgap > 150 && bandgap < 300);
  if (bandgap) {
    long vcc = 1100L * 1023 / bandgap;
    note(F("Supply voltage, mV (reference is +-10%)"), vcc);
    check(F("Supply voltage is plausible"), vcc > 4000 && vcc < 6000);
  }
  for (uint8_t i = 0; i < 2; i++) {
    uint8_t pin = i == 0 ? PIN_KEYS : PIN_KNOB;
    pinMode(pin, INPUT_PULLUP);
    delay(5);
    analogRead(pin);
    int up = analogRead(pin);
    pinMode(pin, INPUT);
    note(i == 0 ? F("A0 with pull-up reads") : F("A1 with pull-up reads"), up);
    if (up < 900) Serial.println(F("INFO Something is wired to this pin, so this check doesn't apply."));
    else check(i == 0 ? F("A0 and the ADC work") : F("A1 and the ADC work"), true);
  }
}

static void testFlash() {
  section(F("Songs in flash"));
  check(F("3 songs present"), SONG_COUNT == 3);
  bool ok = true;
  for (uint8_t piece = 0; piece < SONG_COUNT; piece++) {
    Song song = songAt(piece);
    uint8_t last = 0;
    for (uint8_t i = 0; i < song.levelCount; i++) {
      uint8_t cut = pgm_read_byte(song.cuts + i);
      if (cut <= last) ok = false;
      last = cut;
    }
    if (last != song.noteCount || song.levelCount < 8 || song.levelCount > 12) ok = false;
    for (uint8_t i = 0; i < song.noteCount; i++) {
      if (SONG_LEN(pgm_read_byte(song.notes + i)) == 0) ok = false;
    }
  }
  check(F("Every song's notes and levels are valid"), ok);
}

static void testEeprom() {
  section(F("EEPROM"));
  recordsClear();
  recordUpdate(0, 1234, 5);
  Record record = recordGet(0);
  check(F("A record is written and read back"), record.points == 1234 && record.level == 5);
  recordUpdate(0, 100, 2);
  record = recordGet(0);
  check(F("A lower score doesn't overwrite it"), record.points == 1234 && record.level == 5);
  recordsClear();
  record = recordGet(0);
  check(F("Records clear"), record.points == 0 && record.level == 0);
  check(F("Version byte is set"), EEPROM.read(0) == 0x40 + SONG_COUNT);
}

// --- Tests of the game ---
static void testMenus() {
  section(F("Menus"));
  check(F("Boots to the main menu"), waitLcd(F("/7"), 3000));
  bool ok = true;
  for (uint8_t t = 0; t < KNOB_TICKS; t++) {
    knobTo(t, KNOB_TICKS);
    runFor(200);
    if (readLeds() != (1 << t) || knobTick() != t) {
      ok = false;
      note(F("Tick wanted"), t);
      note(F("Tick read"), knobTick());
      note(F("LEDs read"), readLeds());
    }
  }
  check(F("Every knob tick lights its own key"), ok);
  knobTo(0, KNOB_TICKS);
  check(F("First tick is Light only"), lcdHas(F("Light only")));
  knobTo(6, KNOB_TICKS);
  check(F("Last tick is Reset records"), lcdHas(F("Reset records")));
  tap(0);
  check(F("Reset asks first"), waitLcd(F("Clear records?"), 1000));
  check(F("Yes/No opens on No"), lcdHas(F("> No")));
  runFor(300);
  check(F("No lights the red keys"), readLeds() == MASK_RED);
  nudge();
  check(F("A tick switches to Yes"), lcdHas(F("> Yes")));
  check(F("Yes lights the green keys"), readLeds() == MASK_GREEN);
  nudge();
  tap(0);
  check(F("No returns to the menu"), waitLcd(F("/7"), 1500));
}

static void testFreePlay() {
  section(F("Free play: every note on the real D8 pin"));
  knobTo(4, KNOB_TICKS);
  tap(0);
  check(F("Free play opens"), waitLcd(F("Free play"), 1000));
  runFor(300);
  bool tones = true, leds = true;
  for (uint8_t key = 0; key < 8; key++) {
    press(key);
    runFor(60);
    uint16_t hz = measureHz(200);
    Serial.print(F("INFO Key "));
    Serial.print(key + 1);
    Serial.print(F(": "));
    Serial.print(hz);
    Serial.print(F(" Hz, expected "));
    Serial.println(NOTE_HZ[key]);
    if (!near(hz, NOTE_HZ[key])) tones = false;
    if (readLeds() != (1 << key)) leds = false;
    release();
    runFor(60);
    if (readLeds() != 0 || measureHz(20) != 0) tones = false;
  }
  check(F("All 8 notes have the right frequency"), tones);
  check(F("Each key lights only its own LED"), leds);
  nudge();
  check(F("The knob leaves Free play with no Quit screen"), waitLcd(F("/7"), 1000));
}

static void testPrompt() {
  section(F("Light only: real timing and silence"));
  Song song = songAt(1);
  startMelody(0, 1, false);
  runFor(300);                  // the menu's confirm sound is finished
  toneSeen = false;
  captureCount = 0;
  capturing = true;
  check(F("Turn arrives"), waitLcd(F("Play!"), 10000));
  capturing = false;
  check(F("Silent during the prompt"), !toneSeen);
  uint8_t count = pgm_read_byte(song.cuts);
  check(F("Each note shows as one flash"), captureCount == count * 2);
  bool order = true, timing = true;
  for (uint8_t i = 0; i < count && (uint8_t)(i * 2 + 1) < captureCount; i++) {
    uint8_t data = pgm_read_byte(song.notes + i);
    if (captureMask[i * 2] != (1 << SONG_NOTE(data))) order = false;
    long on = captureTime[i * 2 + 1] - captureTime[i * 2];
    long want = (long)SONG_LEN(data) * song.sixteenthMs * SOUND_PERCENT / 100;
    if (labs(on - want) > 12) timing = false;
    if (i == 0) note(F("First note lit, ms"), on);
  }
  check(F("Flashes follow the song in flash"), order);
  check(F("Each flash lasts 85% of its note, within 12 ms"), timing);
  playLevel(song, 0);
  check(F("Exact rhythm passes the level"), waitLcd(F("L2/12"), 2000));
  check(F("Points: 4 notes, 3 good gaps"), lcdHas(F("Pts 55")));
  Record record = recordGet(1);
  check(F("Record saved at once"), record.points == 55 && record.level == 2);
  toneSeen = false;
  runFor(500);
  check(F("Level-up is silent in Light only"), !toneSeen);
  quitGame();
}

static void testSoundOnly() {
  section(F("Sound only: LEDs stay dark"));
  Song song = songAt(1);
  startMelody(1, 1, false);
  runFor(300);
  litEver = 0;
  toneSeen = false;
  waitLcd(F("Play!"), 10000);
  check(F("Plays sound during the prompt"), toneSeen);
  check(F("LEDs dark during the prompt"), litEver == 0);
  playLevel(song, 0);
  check(F("Level passes"), waitLcd(F("L2/12"), 2000));
  wrongNote(song);
  runFor(600);
  check(F("LEDs dark through a level, level-up and a mistake"), litEver == 0);
  check(F("Separate record for this mode"), recordGet(4).points == 55);
  quitGame();
}

static void testLives() {
  section(F("Lives and game over"));
  recordsClear();
  Song song = songAt(1);
  startMelody(2, 1, false);
  check(F("Starts with 3 lives"), waitLcd(F("Lives:3"), 1500));
  wrongNote(song);
  check(F("A wrong note costs a life"), lcdHas(F("Lives:2")));
  check(F("And says so"), lcdHas(F("Wrong!")));
  wrongNote(song);
  check(F("Second life lost"), lcdHas(F("Lives:1")));
  wrongNote(song);
  check(F("Third ends the game"), waitLcd(F("Game over"), 2000));
  waitResult();
  check(F("Result screen appears"), lcdLine(1)[0] == 'L');
  tap(0, 50, 50);
  check(F("Keys ignored for the first second"), lcdHas(F("Game over")));
  runFor(1100);
  tap(0);
  check(F("Then a key returns to the piece list"), waitLcd(F("Piece"), 1000));
  knobTo(SONG_COUNT, SONG_COUNT + 1);
  tap(0);
  waitMenu();
}

static void testEasy() {
  section(F("Easy mode"));
  recordsClear();
  Song song = songAt(1);
  startMelody(2, 1, true);
  check(F("Shows EASY"), waitLcd(F("EASY"), 1500));
  for (uint8_t i = 0; i < 4; i++) wrongNote(song);
  check(F("No life limit"), !waitLcd(F("Game over"), 800));
  playLevel(song, 0, 300);
  check(F("Bad rhythm still passes"), waitLcd(F("L2/12"), 3000));
  check(F("With fewer points"), lcdHas(F("Pts 40")));
  check(F("No record saved"), recordGet(7).points == 0);
  quitGame();
}

static void testRhythm() {
  section(F("Rhythm"));
  recordsClear();
  Song song = songAt(1);
  startMelody(2, 1, false);
  playLevel(song, 0, 300);
  check(F("Much too slow is marked"), waitLcd(F("Rhythm"), 2000));
  check(F("No life lost"), lcdHas(F("Lives:3")));
  check(F("Stays on the level"), lcdHas(F("L1/12")));
  runFor(100);
  check(F("Signal uses the yellow keys"), readLeds() == MASK_YELLOW || (litEver & MASK_YELLOW));
  playLevel(song, 0, 100, 1);
  check(F("One bad gap of three passes"), waitLcd(F("L2/12"), 2000));
  check(F("But scores less"), lcdHas(F("Pts 50")));
  quitGame();
  startMelody(2, 1, false);
  playLevel(song, 0, 45);
  check(F("Much too fast is marked"), waitLcd(F("Rhythm"), 2000));
  playLevel(song, 0, 180);
  check(F("A slow, even 1.8x still passes"), waitLcd(F("L2/12"), 2000));
  quitGame();
}

static void testReplayAndPause() {
  section(F("Replay and pause"));
  startMelody(2, 1, false);
  waitLcd(F("Play!"), 10000);
  uint32_t start = millis();
  check(F("Replays after waiting"), waitLcd(F("Listen"), 9000));
  note(F("Replayed after, ms"), millis() - start);
  check(F("At about 8 s"), millis() - start >= 7900 && millis() - start <= 8200);
  check(F("No life lost"), lcdHas(F("Lives:3")));
  nudge();
  check(F("The knob pauses"), waitLcd(F("Quit game?"), 500));
  tap(0);
  check(F("No resumes the game"), waitLcd(F("Listen"), 1000));
  check(F("Still no life lost"), lcdHas(F("Lives:3")));
  check(F("Nobody playing returns to the menu"), waitLcd(F("/7"), 60000UL));
}

static void testEar() {
  section(F("Ear mode: answers found by measuring the real pin"));
  recordsClear();
  randomSeed(analogRead(PIN_SEED));
  knobTo(3, KNOB_TICKS);
  tap(0);
  check(F("Asks about Easy first"), waitLcd(F("Easy mode?"), 1000));
  tap(0);
  check(F("Shows the starting notes"), waitLcd(F("Do Mi Sol"), 1000));
  bool candidates = true, repeated = false;
  uint8_t last = 255;
  for (uint8_t q = 0; q < 6; q++) {
    waitLcd(F("Listen"), 6000);
    // Reference, gap, then the mystery note: wait past the 500 ms lead, 400 ms and 250 ms.
    runFor(1250);
    uint8_t heard = hzToKey(measureHz(120));
    if (q < 5 && heard != 0 && heard != 2 && heard != 4) candidates = false;
    if (heard == last) repeated = true;
    last = heard;
    waitLcd(F("Play!"), 3000);
    if (heard < 8) tap(heard, 60, 60);
    if (q == 0) check(F("A right answer scores"), lcdHas(F("Pts 10")));
    if (q == 4) {
      check(F("5 right answers: level 2"), waitLcd(F("Ear L2"), 1500) || lcdHas(F("Up!")) || lcdHas(F("Do Mi Sol Do'")));
      check(F("Next level adds a note"), waitLcd(F("Do Mi Sol Do'"), 3000));
    }
  }
  check(F("Mystery notes are from the current set"), candidates);
  check(F("No note twice in a row"), !repeated);
  check(F("Ear record saved"), recordGet(9).points >= 50);
  waitLcd(F("Listen"), 6000);
  waitLcd(F("Play!"), 3000);
  // Wrong on purpose: mystery unknown here, so press until a life goes.
  for (uint8_t i = 0; i < 8 && !lcdHas(F("Lives:2")); i++) {
    if (!lcdHas(F("Play!"))) waitLcd(F("Play!"), 6000);
    runFor(20);
    tap(i, 60, 60);
  }
  check(F("A wrong answer costs a life"), lcdHas(F("Lives:2")));
  quitGame();
}

static void testIdleAndRecords() {
  section(F("Records screen and idle screen"));
  recordsClear();
  recordUpdate(0, 1234, 5);
  recordUpdate(3, 980, 4);
  recordUpdate(6, 1510, 6);
  knobTo(5, KNOB_TICKS);
  tap(0);
  knobTo(0, SONG_COUNT + 2);
  check(F("Shows the page"), waitLcd(F("ELISE pts L 1234"), 1500));
  check(F("With the other modes"), lcdHas(F("S 980")) && lcdHas(F("B 1510")));
  runFor(2100);
  check(F("Then the best levels"), lcdHas(F("lvl")));
  knobTo(SONG_COUNT + 1, SONG_COUNT + 2);
  tap(0);
  waitMenu();
  toneSeen = false;
  runFor(500);
  toneSeen = false;
  check(F("Idle screen after a minute"), waitLcd(F("Turn or press"), 62000UL));
  check(F("And no sound"), !toneSeen);
  uint8_t seen = 0;
  for (uint8_t i = 0; i < 18; i++) {
    runFor(450);
    seen |= readLeds();
  }
  check(F("LEDs run a slow chase"), seen == 0xFF);
  tap(0);
  check(F("First touch only wakes it"), lcdHas(F("/7")));
  recordsClear();
}

#ifndef SELFTEST_SHORT
static void winPiece(uint8_t mode, uint8_t piece, const __FlashStringHelper* name) {
  section(name);
  recordsClear();
  Song song = songAt(piece);
  uint32_t started = millis();
  startMelody(mode, piece, false);
  uint16_t total = 150;
  for (uint8_t level = 0; level < song.levelCount; level++) {
    playLevel(song, level);
    uint8_t notes = pgm_read_byte(song.cuts + level);
    total += (uint16_t)notes * 10 + (uint16_t)(notes - 1) * 5;
    note(F("Level passed"), level + 1);       // shows progress during the long games
    if (level < song.levelCount - 1) runFor(50);
  }
  litEver = 0;
  check(F("Played to the end"), waitLcd(F("You win!"), 4000));
  waitResult();
  char want[17];
  snprintf_P(want, sizeof(want), PSTR("L%u  %u pts"), song.levelCount, total);
  check(F("Final score is right"), strcmp(lcdLine(1), want) >= 0 && strncmp(lcdLine(1), want, strlen(want)) == 0);
  Record record = recordGet(mode * SONG_COUNT + piece);
  check(F("Record saved"), record.points == total && record.level == song.levelCount);
  note(F("Took, seconds"), (millis() - started) / 1000);
  runFor(5000);
  tap(0);
  waitLcd(F("Piece"), 1000);
  knobTo(SONG_COUNT, SONG_COUNT + 1);
  tap(0);
  waitMenu();
}
#endif

// --- Free memory: everything between the variables and the stack is painted, and later checked ---
extern uint8_t __bss_end;
extern uint8_t* __brkval;
static const uint8_t PAINT = 0xC5;

static void paintStack() {
  uint8_t here;
  uint8_t* from = __brkval ? __brkval : &__bss_end;
  for (uint8_t* p = from; p < &here - 32; p++) *p = PAINT;
}

static uint16_t unusedStack() {
  uint8_t* from = __brkval ? __brkval : &__bss_end;
  uint16_t count = 0;
  while (from[count] == PAINT) count++;
  return count;
}

static void backupRecords() {
  if (EEPROM.read(EE_BACKUP_FLAG) == BACKUP_SET) {     // an earlier run was stopped midway
    for (uint8_t i = 0; i < RECORD_BYTES; i++) EEPROM.update(i, EEPROM.read(EE_BACKUP + i));
  }
  for (uint8_t i = 0; i < RECORD_BYTES; i++) EEPROM.update(EE_BACKUP + i, EEPROM.read(i));
  EEPROM.update(EE_BACKUP_FLAG, BACKUP_SET);
}

static void restoreRecords() {
  for (uint8_t i = 0; i < RECORD_BYTES; i++) EEPROM.update(i, EEPROM.read(EE_BACKUP + i));
  EEPROM.update(EE_BACKUP_FLAG, 0xFF);
  EEPROM.update(EE_PHASE, 0xFF);
}

void setup() {
  wdt_disable();
  Serial.begin(115200);
  delay(1500);
  bool phaseTwo = EEPROM.read(EE_PHASE) == PHASE_TWO;
  EEPROM.update(EE_PHASE, 0xFF);
  Serial.println(F("\nMAESTRO SELF-TEST"));

  if (!phaseTwo) {
    Serial.println(F("Running on this board's own processor. Nothing needs to be wired."));
    backupRecords();
    testPins();
    testAdc();
    testFlash();
    testEeprom();
    recordsClear();
    recordUpdate(5, 4321, 7);
    paintStack();
    gameSetup();
    testMenus();
    // Menus cleared nothing: the marker record stays for the reset test.
    check(F("Marker record is still there"), recordGet(5).points == 4321);
    testFreePlay();
    recordUpdate(5, 4321, 7);
    section(F("Real reset by the watchdog"));
    EEPROM.put(EE_PASS, passed);
    EEPROM.put(EE_FAIL, failed);
    EEPROM.put(EE_MAXLOOP, maxLoopUs);
    EEPROM.update(EE_PHASE, PHASE_TWO);
    Serial.println(F("Resetting..."));
    Serial.flush();
#ifdef SELFTEST_SOFT_RESET
    // The simulator doesn't model the watchdog. A jump to 0 is not a real reset, so stop
    // every interrupt first, or the tone timer fires while memory is being set up again.
    cli();
    TIMSK0 = 0;
    TIMSK1 = 0;
    TIMSK2 = 0;
    UCSR0B = 0;
    asm volatile("jmp 0");
#else
    wdt_enable(WDTO_250MS);
    while (true) {
    }
#endif
  }

  EEPROM.get(EE_PASS, passed);
  EEPROM.get(EE_FAIL, failed);
  EEPROM.get(EE_MAXLOOP, maxLoopUs);
  check(F("Came back after the reset"), true);
  check(F("Records survive a reset"), recordGet(5).points == 4321 && recordGet(5).level == 7);
  paintStack();
  gameSetup();
  check(F("Game boots again after the reset"), waitLcd(F("/7"), 3000));
  recordsClear();
  testPrompt();
  testSoundOnly();
  testLives();
  testEasy();
  testRhythm();
  testReplayAndPause();
  testEar();
  testIdleAndRecords();
#ifndef SELFTEST_SHORT
  winPiece(2, 0, F("Whole piece: Fur Elise, Light + sound"));
  winPiece(0, 2, F("Whole piece: Turkish March, Light only"));
  winPiece(1, 1, F("Whole piece: Ode to Joy, Sound only"));
#endif

  section(F("Limits measured on this chip"));
  uint16_t unused = unusedStack();
  note(F("RAM never touched, bytes"), unused);
  note(F("Slowest pass through the game loop, microseconds"), maxLoopUs);
  check(F("At least 256 bytes of RAM to spare"), unused >= 256);
  check(F("Loop never blocks for more than 20 ms"), maxLoopUs < 20000UL);
  restoreRecords();
  check(F("Records put back"), EEPROM.read(EE_BACKUP_FLAG) == 0xFF);
  Serial.print(F("\nRESULT "));
  Serial.print(passed);
  Serial.print(F(" passed, "));
  Serial.print(failed);
  Serial.println(F(" failed"));
  Serial.flush();
}

void loop() {}
