#include "input.h"
#include "config.h"

static uint32_t lastKeyScan, lastKnobScan, candidateSince;
static int8_t candidate = -1, held = -1, pendingKey = -1;
static uint8_t candidateReads;
static uint32_t pendingTime;
static uint16_t knobValue;
static uint8_t tick;

static int8_t decodeKey(int value) {
  int level = (value + KEY_STEP / 2) / KEY_STEP;  // 0 = none, 8 = key 1
  if (level < 1) return -1;
  if (level > 8) level = 8;
  return 8 - level;
}

static uint16_t readKnobRaw() {
  int value = analogRead(PIN_KNOB);
  return KNOB_REVERSED ? 1023 - value : value;
}

// Zone of value among count equal zones, sticking to current near a boundary.
static uint8_t zoneOf(uint16_t value, uint8_t count, uint8_t current) {
  if (current < count) {
    int16_t low = (uint32_t)current * 1024 / count;
    int16_t high = (uint32_t)(current + 1) * 1024 / count;
    if ((int16_t)value >= low - KNOB_HYSTERESIS && (int16_t)value < high + KNOB_HYSTERESIS) return current;
  }
  return (uint32_t)value * count / 1024;
}

void inputBegin() {
  knobValue = readKnobRaw();
  tick = zoneOf(knobValue, KNOB_TICKS, 255);
}

void inputUpdate(uint32_t now) {
  if (now - lastKeyScan >= KEY_SCAN_MS) {
    lastKeyScan = now;
    int8_t key = decodeKey(analogRead(PIN_KEYS));
    if (key == candidate) {
      if (candidateReads < 255) candidateReads++;
    } else {
      candidate = key;
      candidateReads = 1;
      candidateSince = now;
    }
    if (candidateReads == KEY_STABLE_READS) {
      if (candidate < 0) {
        held = -1;
      } else if (held < 0) {       // a new press needs a full release first
        held = candidate;
        pendingKey = candidate;
        pendingTime = candidateSince;
      }
    }
  }
  if (now - lastKnobScan >= KNOB_SCAN_MS) {
    lastKnobScan = now;
    knobValue = (knobValue * 3 + readKnobRaw() + 2) / 4;
    tick = zoneOf(knobValue, KNOB_TICKS, tick);
  }
}

bool keyTakePress(uint8_t& key, uint32_t& time) {
  if (pendingKey < 0) return false;
  key = pendingKey;
  time = pendingTime;
  pendingKey = -1;
  return true;
}

void keyClearPress() { pendingKey = -1; }
int8_t keyHeld() { return held; }
uint8_t knobTick() { return tick; }
uint8_t knobItem(uint8_t count, uint8_t current) { return zoneOf(knobValue, count, current); }
