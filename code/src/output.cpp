#include "output.h"
#include <LiquidCrystal.h>
#include "config.h"

static LiquidCrystal lcd(12, 11, 5, 4, 3, 2);  // RS, E, D4, D5, D6, D7

struct Step {
  uint16_t hz;      // 0 = silence
  uint16_t ms;      // 0 = end of the cue
  uint8_t mask;     // LEDs lit during this step, 0 = keep the normal LEDs
};

// Happy cues rise in a major key; sad cues fall in a minor key (Q20).
static const Step S_STARTUP[] PROGMEM = {{262, 70, 1}, {294, 70, 2}, {330, 70, 4}, {349, 70, 8},
  {392, 70, 16}, {440, 70, 32}, {494, 70, 64}, {523, 140, 128}, {0, 0, 0}};
static const Step S_CONFIRM[] PROGMEM = {{523, 60, MASK_GREEN}, {784, 90, MASK_GREEN}, {0, 0, 0}};
static const Step S_BACK[] PROGMEM = {{392, 60, MASK_RED}, {262, 90, MASK_RED}, {0, 0, 0}};
static const Step S_CORRECT[] PROGMEM = {{659, 80, 0}, {988, 140, 0}, {0, 0, 0}};
static const Step S_WRONG[] PROGMEM = {{196, 180, MASK_RED}, {0, 40, 0}, {147, 380, MASK_RED}, {0, 0, 0}};
static const Step S_RHYTHM[] PROGMEM = {{330, 70, MASK_YELLOW}, {370, 70, 0}, {330, 70, MASK_YELLOW},
  {370, 70, 0}, {330, 70, MASK_YELLOW}, {370, 70, 0}, {0, 0, 0}};
static const Step S_LEVEL_UP[] PROGMEM = {{523, 110, MASK_GREEN}, {659, 110, MASK_GREEN},
  {784, 240, MASK_GREEN}, {0, 0, 0}};
static const Step S_GAME_OVER[] PROGMEM = {{494, 130, 0xFF}, {440, 130, 0x7F}, {392, 130, 0x3F},
  {349, 130, 0x1F}, {311, 130, 0x0F}, {294, 130, 0x07}, {262, 130, 0x03}, {233, 300, 0x01}, {0, 0, 0}};
static const Step S_WIN[] PROGMEM = {{523, 90, 1}, {659, 90, 2}, {784, 90, 4}, {1047, 90, 8},
  {784, 90, 16}, {1047, 90, 32}, {1319, 90, 64}, {1568, 240, 128}, {0, 200, 0}, {0, 0, 0}};
static const Step S_HAPPY[] PROGMEM = {{523, 100, MASK_GREEN}, {659, 100, MASK_GREEN},
  {784, 100, MASK_GREEN}, {1047, 260, MASK_GREEN}, {0, 120, 0}, {0, 0, 0}};
static const Step S_SAD[] PROGMEM = {{392, 180, MASK_RED}, {311, 180, MASK_RED},
  {262, 420, MASK_RED}, {0, 120, 0}, {0, 0, 0}};
static const Step S_FANFARE[] PROGMEM = {{784, 110, MASK_GREEN}, {784, 110, 0}, {784, 110, MASK_GREEN},
  {1047, 400, MASK_ALL}, {0, 0, 0}};
static const Step S_BEEP[] PROGMEM = {{880, 90, 0}, {0, 160, 0}, {0, 0, 0}};

static const Step* const CUES[] PROGMEM = {S_STARTUP, S_CONFIRM, S_BACK, S_CORRECT, S_WRONG, S_RHYTHM,
  S_LEVEL_UP, S_GAME_OVER, S_WIN, S_HAPPY, S_SAD, S_FANFARE, S_BEEP};

struct QueueEntry {
  const Step* steps;   // nullptr = a single tone, using the fields below
  uint16_t hz, ms;
  uint8_t mask, repeats;
  bool light, sound;
};

static const uint8_t QUEUE_SIZE = 12;
static QueueEntry queue[QUEUE_SIZE];
static uint8_t queueHead, queueLen;
static bool playing;
static uint8_t stepIndex, repeatsLeft;
static uint32_t stepStart;
static uint16_t stepMs;
static uint8_t cueMask, normalMask, shownMask;
static bool ledsKnown;

static void ledsApply() {
  uint8_t mask = cueMask ? cueMask : normalMask;
  if (ledsKnown && mask == shownMask) return;
  for (uint8_t i = 0; i < 8; i++) digitalWrite(LED_PINS[i], (mask >> i) & 1);
  shownMask = mask;
  ledsKnown = true;
}

static void startStep(const QueueEntry& entry, uint16_t hz, uint16_t ms, uint8_t mask, uint32_t now) {
  stepStart = now;
  stepMs = ms;
  cueMask = entry.light ? mask : 0;
  if (hz && entry.sound) tone(PIN_PIEZO, hz);
  else noTone(PIN_PIEZO);
}

// Starts the next step of the current cue. Returns false when the cue has finished.
static bool nextStep(uint32_t now) {
  const QueueEntry& entry = queue[queueHead];
  if (!entry.steps) {
    if (stepIndex > 0) return false;
    stepIndex = 1;
    startStep(entry, entry.hz, entry.ms, entry.mask, now);
    return true;
  }
  Step step;
  memcpy_P(&step, &entry.steps[stepIndex], sizeof(Step));
  if (step.ms == 0) {
    if (--repeatsLeft == 0) return false;
    stepIndex = 0;
    memcpy_P(&step, &entry.steps[0], sizeof(Step));
  }
  stepIndex++;
  startStep(entry, step.hz, step.ms, step.mask, now);
  return true;
}

void outputUpdate(uint32_t now) {
  if (playing && now - stepStart >= stepMs && !nextStep(now)) {
    playing = false;
    queueHead = (queueHead + 1) % QUEUE_SIZE;
    queueLen--;
    cueMask = 0;
    noTone(PIN_PIEZO);
  }
  if (!playing && queueLen > 0) {
    playing = true;
    stepIndex = 0;
    repeatsLeft = queue[queueHead].repeats;
    nextStep(now);
  }
  ledsApply();
}

void outputBegin() {
  for (uint8_t i = 0; i < 8; i++) {
    pinMode(LED_PINS[i], OUTPUT);
    digitalWrite(LED_PINS[i], LOW);
  }
  pinMode(PIN_PIEZO, OUTPUT);
  lcd.begin(16, 2);
  lcd.clear();
}

void ledsSet(uint8_t mask) { normalMask = mask; }
void toneOn(uint16_t hz) { tone(PIN_PIEZO, hz); }
void toneOff() { noTone(PIN_PIEZO); }

static QueueEntry* queueAdd() {
  if (queueLen == QUEUE_SIZE) return nullptr;
  QueueEntry* entry = &queue[(queueHead + queueLen) % QUEUE_SIZE];
  queueLen++;
  return entry;
}

void cuePlay(CueId cue, bool light, bool sound, uint8_t repeats) {
  QueueEntry* entry = queueAdd();
  if (!entry) return;
  entry->steps = (const Step*)pgm_read_ptr(&CUES[cue]);
  entry->repeats = repeats;
  entry->light = light;
  entry->sound = sound;
}

void cueTone(uint16_t hz, uint16_t ms, uint8_t mask, bool light, bool sound) {
  QueueEntry* entry = queueAdd();
  if (!entry) return;
  entry->steps = nullptr;
  entry->hz = hz;
  entry->ms = ms;
  entry->mask = mask;
  entry->repeats = 1;
  entry->light = light;
  entry->sound = sound;
}

void cueStop() {
  queueHead = 0;
  queueLen = 0;
  playing = false;
  stepMs = 0;
  cueMask = 0;
  noTone(PIN_PIEZO);
}

bool cueBusy() { return playing || queueLen > 0; }

static char shown[2][17];
static bool shownValid;

void lcdShow(const char* line0, const char* line1) {
  const char* lines[2] = {line0, line1};
  for (uint8_t row = 0; row < 2; row++) {
    bool atEnd = false;
    int8_t cursor = -1;
    for (uint8_t col = 0; col < 16; col++) {
      if (!atEnd && !lines[row][col]) atEnd = true;
      char c = atEnd ? ' ' : lines[row][col];
      if (shownValid && shown[row][col] == c) continue;
      if (cursor != (int8_t)col) lcd.setCursor(col, row);
      lcd.write(c);
      shown[row][col] = c;
      cursor = col + 1;
    }
  }
  shownValid = true;
}

#ifdef MAESTRO_SELFTEST
const char* lcdLine(uint8_t row) { return shown[row]; }
#endif
