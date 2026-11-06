// Pin map and tuning constants. See HANDOFF_FOR_SOFTWARE_AGENT.md and DECISIONS.md.
#pragma once
#include <Arduino.h>

// --- Pins (fixed by the wiring in the case) ---
static const uint8_t PIN_KEYS = A0;   // all 8 keys, resistor ladder
static const uint8_t PIN_KNOB = A1;
static const uint8_t PIN_SEED = A5;   // left unconnected, used for randomness
static const uint8_t PIN_PIEZO = 8;
static const uint8_t LED_PINS[8] = {6, 7, 9, 10, 13, A2, A3, A4};  // До ... До'

// --- Notes ---
static const uint16_t NOTE_HZ[8] = {262, 294, 330, 349, 392, 440, 494, 523};

// --- LED colours: signals light only the keys that have that colour (Q23) ---
static const uint8_t MASK_RED = 0b10000001;     // До, До'
static const uint8_t MASK_YELLOW = 0b00100010;  // Ре, Ла
static const uint8_t MASK_GREEN = 0b01000100;   // Ми, Си
static const uint8_t MASK_ALL = 0xFF;

// --- Keys (Q24) ---
static const uint16_t KEY_STEP = 128;           // ladder: key 1 ~1023 ... key 8 ~128
static const uint8_t KEY_SCAN_MS = 5;
static const uint8_t KEY_STABLE_READS = 3;

// --- Knob (Q25). Set KNOB_REVERSED to true if turning right moves the menu left. ---
static const bool KNOB_REVERSED = false;
static const uint8_t KNOB_SCAN_MS = 20;
static const uint8_t KNOB_HYSTERESIS = 20;
static const uint8_t KNOB_TICKS = 7;

// --- Game rules ---
static const uint8_t START_LIVES = 3;           // Q5
static const uint16_t REPLAY_AFTER_MS = 8000;   // Q6
static const uint8_t MAX_IDLE_REPLAYS = 3;      // Q17
static const uint8_t SOUND_PERCENT = 85;        // Q22
static const uint8_t POINTS_PER_NOTE = 10;      // Q18
static const uint8_t POINTS_PER_GOOD_GAP = 5;
static const uint8_t POINTS_PER_LIFE_LEFT = 50;
static const uint8_t POINTS_PER_EAR_ANSWER = 10;
static const uint8_t EAR_START_NOTES = 3;       // Q14
static const uint8_t EAR_CORRECT_TO_LEVEL = 5;
static const uint8_t MAX_LEVEL_BEEPS = 20;

// --- Timing ---
static const uint16_t PROMPT_LEAD_MS = 500;     // pause before a melody starts
static const uint16_t SETTLE_MIN_MS = 200;      // let the last note sound before judging
static const uint16_t SETTLE_MAX_MS = 500;
static const uint16_t RESULT_IGNORE_MS = 1000;  // Q21
static const uint16_t RESULT_FLIP_MS = 1500;
static const uint16_t RECORD_FLIP_MS = 2000;
static const uint16_t MESSAGE_MS = 1500;
static const uint16_t IDLE_AFTER_MS = 60000U;   // Q27
static const uint16_t IDLE_CHASE_MS = 400;

// --- Debug log, only in the "debug" build ---
#ifdef MAESTRO_DEBUG
#define DBG_BEGIN() Serial.begin(115200)
#define DBG(...) do { Serial.print(millis()); Serial.print(F(" ")); Serial.println(__VA_ARGS__); } while (0)
#else
#define DBG_BEGIN()
#define DBG(...)
#endif
