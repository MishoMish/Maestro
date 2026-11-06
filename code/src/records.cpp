#include "records.h"
#include <EEPROM.h>
#include "melodies_data.h"

// Layout: 1 version byte, then 3 bytes per record. The version depends on the
// number of songs, so a different layout clears the records instead of misreading them.
static const uint8_t RECORD_COUNT = SONG_COUNT * 3 + 1;
static const uint8_t RECORD_VERSION = 0x40 + SONG_COUNT;

static int addressOf(uint8_t index) { return 1 + index * 3; }

void recordsBegin() {
  if (EEPROM.read(0) != RECORD_VERSION) recordsClear();
}

Record recordGet(uint8_t index) {
  Record record;
  uint8_t low = EEPROM.read(addressOf(index));
  uint8_t high = EEPROM.read(addressOf(index) + 1);
  record.points = low | (uint16_t)high << 8;
  record.level = EEPROM.read(addressOf(index) + 2);
  return record;
}

void recordUpdate(uint8_t index, uint16_t points, uint8_t level) {
  Record best = recordGet(index);
  if (points > best.points) {
    EEPROM.update(addressOf(index), points & 0xFF);
    EEPROM.update(addressOf(index) + 1, points >> 8);
  }
  if (level > best.level) EEPROM.update(addressOf(index) + 2, level);
}

void recordsClear() {
  for (uint8_t i = 0; i < RECORD_COUNT * 3; i++) EEPROM.update(1 + i, 0);
  EEPROM.update(0, RECORD_VERSION);
}
