// High scores in EEPROM (Q19, Q30): one per mode per piece, plus one for Ear.
#pragma once
#include <Arduino.h>

struct Record {
  uint16_t points;
  uint8_t level;
};

void recordsBegin();
Record recordGet(uint8_t index);
void recordUpdate(uint8_t index, uint16_t points, uint8_t level);  // only writes improvements
void recordsClear();
