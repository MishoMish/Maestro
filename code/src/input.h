// Key ladder and knob reading. Non-blocking: call inputUpdate() from loop().
#pragma once
#include <Arduino.h>

void inputBegin();
void inputUpdate(uint32_t now);

// Returns true once per press. time = when the press first appeared, for rhythm.
bool keyTakePress(uint8_t& key, uint32_t& time);
void keyClearPress();
int8_t keyHeld();   // the key counted as pressed, or -1 after a full release

uint8_t knobTick();                                 // 0 ... KNOB_TICKS-1
uint8_t knobItem(uint8_t count, uint8_t current);   // position in a list of count items
