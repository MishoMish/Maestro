// LEDs, piezo cues and the LCD. Cues are non-blocking: call outputUpdate() from loop().
#pragma once
#include <Arduino.h>

enum CueId : uint8_t {
  CUE_STARTUP, CUE_CONFIRM, CUE_BACK, CUE_CORRECT, CUE_WRONG, CUE_RHYTHM, CUE_LEVEL_UP,
  CUE_GAME_OVER, CUE_WIN, CUE_HAPPY, CUE_SAD, CUE_FANFARE, CUE_BEEP
};

void outputBegin();
void outputUpdate(uint32_t now);

void ledsSet(uint8_t mask);   // shown whenever no cue is lighting the LEDs
void toneOn(uint16_t hz);
void toneOff();

// Cues play one after another. light/sound choose the channels allowed (Q8).
void cuePlay(CueId cue, bool light, bool sound, uint8_t repeats = 1);
void cueTone(uint16_t hz, uint16_t ms, uint8_t mask, bool light, bool sound);
void cueStop();
bool cueBusy();

// Shows both lines, padded to 16 characters. Only changed characters are sent.
void lcdShow(const char* line0, const char* line1);
