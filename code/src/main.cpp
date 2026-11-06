// Маестро: one non-blocking state machine (Q2). The rules are in DECISIONS.md.
#include <Arduino.h>
#include "config.h"
#include "input.h"
#include "melodies_data.h"
#include "output.h"
#include "records.h"

enum State : uint8_t {
  ST_BOOT, ST_MENU, ST_PIECE, ST_RECORDS, ST_YESNO, ST_MESSAGE, ST_FREE, ST_IDLE,
  ST_PROMPT, ST_INPUT, ST_SETTLE, ST_FEEDBACK,
  ST_EAR_INTRO, ST_EAR_PROMPT, ST_EAR_ANSWER,
  ST_ENDING, ST_WIN_PIECE, ST_RESULT
};
enum Mode : uint8_t { MODE_LIGHT, MODE_SOUND, MODE_BOTH, MODE_EAR };
enum MenuItem : uint8_t { ITEM_LIGHT, ITEM_SOUND, ITEM_BOTH, ITEM_EAR, ITEM_FREE, ITEM_RECORDS, ITEM_RESET };
enum YesNo : uint8_t { YN_EASY, YN_RESET, YN_QUIT };
enum After : uint8_t { AFTER_RESUME, AFTER_QUESTION, AFTER_INTRO, AFTER_WIN, AFTER_GAME_OVER };

static const char MENU_NAMES[KNOB_TICKS][14] PROGMEM = {
  "Light only", "Sound only", "Light + sound", "Ear", "Free play", "Records", "Reset records"};
static const char NOTE_NAMES[8][4] PROGMEM = {"Do", "Re", "Mi", "Fa", "Sol", "La", "Si", "Do'"};
static const uint8_t EAR_NOTE_ORDER[8] PROGMEM = {0, 2, 4, 7, 5, 1, 3, 6};  // Q14: До Ми Сол first

static const char MSG_LISTEN[] PROGMEM = "Listen";
static const char MSG_WATCH[] PROGMEM = "Watch";
static const char MSG_PLAY[] PROGMEM = "Play!";
static const char MSG_WRONG[] PROGMEM = "Wrong!";
static const char MSG_RHYTHM[] PROGMEM = "Rhythm";
static const char MSG_GOOD[] PROGMEM = "Good!";
static const char MSG_LEVEL[] PROGMEM = "Up!";

// --- State ---
static State state = ST_BOOT;
static uint32_t now, idleSince, stateSince;
static char line0[17], line1[17];
static uint8_t tick, menuItem;
static bool screenDirty;

// Yes/No screen
static YesNo yesNoKind;
static bool yesNoValue;
static uint8_t yesNoTick;

// Current game
static Mode mode;
static bool easy, gameWon;
static uint8_t piece, lives, level, baseTick, idleReplays, notePos, badGaps, goodGaps;
static uint16_t points, recordAtStart;
static uint32_t lastPressAt, inputSince;
static int8_t echoKey = -1;
static After afterFeedback;
static Song song;
static const char* gameMessage;

// Melody playback
static uint8_t playPos, playTotal;
static bool playNoteOn;
static uint32_t playNext;

// Ear mode
static uint8_t earLevel, earCorrect, earNote, earLastNote;

static bool usesLight() { return mode == MODE_LIGHT || mode == MODE_BOTH; }
static bool usesSound() { return mode != MODE_LIGHT; }
static bool isEar() { return mode == MODE_EAR; }

static uint8_t recordIndex() { return isEar() ? SONG_COUNT * 3 : mode * SONG_COUNT + piece; }
static uint8_t reachedLevel() {
  if (isEar()) return earLevel;
  return level < song.levelCount ? level + 1 : song.levelCount;
}
static void saveRecord() {
  if (!easy) recordUpdate(recordIndex(), points, reachedLevel());
}
static void addPoints(uint16_t amount) {
  points = (uint32_t)points + amount > 65535UL ? 65535U : points + amount;
}

static void setState(State next) {
  state = next;
  stateSince = now;
  screenDirty = true;
  DBG(next);
}

static void stopEcho() {
  if (echoKey >= 0) {
    toneOff();
    ledsSet(0);
    echoKey = -1;
  }
}

// --- Menus ---
// Lights and plays the list item. Queued, so a confirm cue before it still plays.
static void announceItem(uint8_t item, uint8_t count, bool lastIsBack) {
  if (lastIsBack && item == count - 1) {
    ledsSet(MASK_RED);
    cueTone(196, 150, 0, true, true);
  } else {
    ledsSet(1 << item);
    cueTone(NOTE_HZ[item], 150, 0, true, true);
  }
}

static void goMenu() {
  menuItem = tick;
  ledsSet(1 << menuItem);
  cueTone(NOTE_HZ[menuItem], 150, 0, true, true);
  idleSince = now;
  setState(ST_MENU);
}

static void goPieceList() {
  menuItem = knobItem(SONG_COUNT + 1, 255);
  announceItem(menuItem, SONG_COUNT + 1, true);
  idleSince = now;
  setState(ST_PIECE);
}

static void openYesNo(YesNo kind) {
  yesNoKind = kind;
  yesNoValue = false;   // always opens on No (Q9)
  yesNoTick = tick;
  ledsSet(MASK_RED);
  cueTone(196, 150, 0, true, true);
  idleSince = now;
  setState(ST_YESNO);
}

static void drawTitleItem(const __FlashStringHelper* title, uint8_t pos, uint8_t count) {
  snprintf_P(line0, sizeof(line0), PSTR("%-11S %u/%u"), (const char*)title, pos + 1, count);
}

// --- Melody playback ---
static void playStart(uint8_t total, uint16_t lead) {
  playPos = 0;
  playTotal = total;
  playNoteOn = false;
  playNext = now + lead;
}

// Advances the melody. Returns true when it has finished.
static bool playUpdate() {
  if ((int32_t)(now - playNext) < 0) return false;
  if (!playNoteOn && playPos == playTotal) return true;
  uint8_t data = pgm_read_byte(song.notes + playPos);
  uint32_t total = (uint32_t)SONG_LEN(data) * song.sixteenthMs;
  uint32_t sounding = total * SOUND_PERCENT / 100;
  if (playNoteOn) {
    if (usesLight()) ledsSet(0);
    if (usesSound()) toneOff();
    playNoteOn = false;
    playNext += total - sounding;
    playPos++;
  } else {
    uint8_t key = SONG_NOTE(data);
    if (usesLight()) ledsSet(1 << key);
    if (usesSound()) toneOn(NOTE_HZ[key]);
    playNoteOn = true;
    playNext += sounding;
  }
  return false;
}

static void playStop() {
  ledsSet(0);
  toneOff();
  playNoteOn = false;
}

// --- Game ---
static void setMessage(const char* message) {
  gameMessage = message;
  screenDirty = true;
}

static void drawGame() {
  if (isEar()) {
    if (easy) snprintf_P(line0, sizeof(line0), PSTR("Ear L%u EASY"), earLevel);
    else snprintf_P(line0, sizeof(line0), PSTR("Ear L%u Lives:%u"), earLevel, lives);
  } else {
    uint8_t shown = level < song.levelCount ? level + 1 : song.levelCount;
    if (easy) snprintf_P(line0, sizeof(line0), PSTR("L%u/%u EASY"), shown, song.levelCount);
    else snprintf_P(line0, sizeof(line0), PSTR("L%u/%u Lives:%u"), shown, song.levelCount, lives);
  }
  snprintf_P(line1, sizeof(line1), PSTR("Pts %-5u %6S"), points, gameMessage);
  lcdShow(line0, line1);
}

static void beginAttempt() {
  notePos = 0;
  badGaps = 0;
  goodGaps = 0;
  afterFeedback = AFTER_RESUME;
  ledsSet(0);
  playStart(pgm_read_byte(song.cuts + level), PROMPT_LEAD_MS);
  setMessage(usesSound() ? MSG_LISTEN : MSG_WATCH);
  setState(ST_PROMPT);
}

static void startInput(State inputState) {
  keyClearPress();
  inputSince = now;
  setMessage(MSG_PLAY);
  setState(inputState);
}

static void startGameOver() {
  saveRecord();
  gameWon = false;
  ledsSet(0);
  cuePlay(CUE_GAME_OVER, usesLight(), usesSound());
  setState(ST_ENDING);
}

static void startWin() {
  if (!easy) addPoints((uint16_t)lives * POINTS_PER_LIFE_LEFT);
  saveRecord();
  gameWon = true;
  ledsSet(0);
  cuePlay(CUE_WIN, usesLight(), usesSound());
  setState(ST_ENDING);
}

static void enterResult() {
  stopEcho();
  playStop();
  ledsSet(0);
  bool newRecord = !easy && points > recordAtStart;
  if (gameWon) cuePlay(CUE_HAPPY, true, true);
  else if (mode == MODE_LIGHT) cuePlay(CUE_SAD, true, true);   // Q29: silent play is over
  if (usesSound()) {
    uint8_t beeps = reachedLevel() < MAX_LEVEL_BEEPS ? reachedLevel() : MAX_LEVEL_BEEPS;
    cuePlay(CUE_BEEP, false, true, beeps);   // Q20
  }
  if (newRecord) cuePlay(CUE_FANFARE, true, usesSound());
  idleSince = now;
  setState(ST_RESULT);
}

static void drawResult() {
  bool newRecord = !easy && points > recordAtStart;
  bool flip = newRecord && ((now - stateSince) / RESULT_FLIP_MS) % 2;
  if (flip) strcpy_P(line0, PSTR("NEW RECORD!"));
  else strcpy_P(line0, gameWon ? PSTR("You win!") : PSTR("Game over"));
  snprintf_P(line1, sizeof(line1), PSTR("L%u  %u pts"), reachedLevel(), points);
  lcdShow(line0, line1);
}

static void startGame() {
  points = 0;
  lives = START_LIVES;
  level = 0;
  idleReplays = 0;
  gameWon = false;
  baseTick = tick;
  echoKey = -1;
  recordAtStart = recordGet(recordIndex()).points;
  gameMessage = MSG_LISTEN;
  DBG(F("game start"));
}

static void loseLife() {
  if (!easy && lives > 0) lives--;
}

static void finishFeedback() {
  ledsSet(0);
  switch (afterFeedback) {
    case AFTER_GAME_OVER: startGameOver(); break;
    case AFTER_WIN: startWin(); break;
    default: beginAttempt(); break;
  }
}

static void judgeAttempt() {
  stopEcho();
  uint8_t notes = pgm_read_byte(song.cuts + level);
  uint8_t gaps = notes - 1;
  bool rhythmBad = (uint16_t)badGaps * 3 > gaps;   // Q13
  if (rhythmBad && !easy) {
    cuePlay(CUE_RHYTHM, usesLight(), usesSound());
    afterFeedback = AFTER_RESUME;
    setMessage(MSG_RHYTHM);
    setState(ST_FEEDBACK);
    return;
  }
  addPoints((uint16_t)notes * POINTS_PER_NOTE + (uint16_t)goodGaps * POINTS_PER_GOOD_GAP);
  level++;
  saveRecord();
  if (rhythmBad) cuePlay(CUE_RHYTHM, usesLight(), usesSound());
  if (level == song.levelCount) {
    afterFeedback = AFTER_WIN;
  } else {
    cuePlay(CUE_LEVEL_UP, usesLight(), usesSound());
    afterFeedback = AFTER_RESUME;
  }
  setMessage(MSG_LEVEL);
  setState(ST_FEEDBACK);
}

static void handleMelodyPress(uint8_t key, uint32_t pressedAt) {
  idleReplays = 0;
  inputSince = pressedAt;
  uint8_t data = pgm_read_byte(song.notes + notePos);
  if (key != SONG_NOTE(data)) {
    loseLife();
    cuePlay(CUE_WRONG, usesLight(), usesSound());
    afterFeedback = lives == 0 ? AFTER_GAME_OVER : AFTER_RESUME;
    setMessage(MSG_WRONG);
    setState(ST_FEEDBACK);
    return;
  }
  echoKey = key;
  if (usesLight()) ledsSet(1 << key);
  if (usesSound()) toneOn(NOTE_HZ[key]);
  if (notePos > 0) {   // Q12: compare with the written gap at the real tempo
    uint8_t previous = pgm_read_byte(song.notes + notePos - 1);
    uint32_t written = (uint32_t)SONG_LEN(previous) * song.sixteenthMs;
    uint32_t played = pressedAt - lastPressAt;
    if (played * 2 < written || played > written * 2) badGaps++;
    else goodGaps++;
  }
  lastPressAt = pressedAt;
  notePos++;
  if (notePos == pgm_read_byte(song.cuts + level)) setState(ST_SETTLE);
}

// Handles the wait for a press. Returns true if the attempt must replay.
static bool waitTimedOut() {
  if (keyHeld() >= 0) inputSince = now;
  if (now - inputSince < REPLAY_AFTER_MS) return false;
  stopEcho();
  if (idleReplays >= MAX_IDLE_REPLAYS) {   // Q17: nobody is playing
    saveRecord();
    cuePlay(CUE_BACK, true, true);
    goMenu();
    return false;
  }
  idleReplays++;
  return true;
}

// --- Ear mode ---
static uint8_t earNoteCount() {
  uint8_t count = EAR_START_NOTES + earLevel - 1;
  return count < 8 ? count : 8;
}

static void earDrawNotes() {
  // Names of the possible notes, in key order, over both lines.
  char* out = line0;
  uint8_t room = 16;
  line0[0] = 0;
  line1[0] = 0;
  uint8_t mask = 0;
  for (uint8_t i = 0; i < earNoteCount(); i++) mask |= 1 << pgm_read_byte(&EAR_NOTE_ORDER[i]);
  for (uint8_t key = 0; key < 8; key++) {
    if (!(mask >> key & 1)) continue;
    char name[4];
    strcpy_P(name, NOTE_NAMES[key]);
    uint8_t needed = strlen(name) + (out[0] ? 1 : 0);
    if (needed > room && out == line0) {
      out = line1;
      room = 16;
      needed = strlen(name);
    }
    if (out[0]) strcat(out, " ");
    strcat(out, name);
    room -= needed;
  }
  lcdShow(line0, line1);
}

static void earStartIntro() {
  afterFeedback = AFTER_INTRO;
  uint8_t mask = 0;
  for (uint8_t i = 0; i < earNoteCount(); i++) mask |= 1 << pgm_read_byte(&EAR_NOTE_ORDER[i]);
  cueTone(0, PROMPT_LEAD_MS, 0, false, false);
  for (uint8_t key = 0; key < 8; key++) {
    if (mask >> key & 1) cueTone(NOTE_HZ[key], 320, 1 << key, true, true);
  }
  setState(ST_EAR_INTRO);
}

static void earPlayQuestion() {
  afterFeedback = AFTER_RESUME;
  ledsSet(0);
  cueTone(0, PROMPT_LEAD_MS, 0, false, false);
  cueTone(NOTE_HZ[0], 400, 0, false, true);    // reference: low До
  cueTone(0, 250, 0, false, false);
  cueTone(NOTE_HZ[earNote], 650, 0, false, true);
  setMessage(MSG_LISTEN);
  setState(ST_EAR_PROMPT);
}

static void earNewQuestion() {
  uint8_t next;
  do {
    next = pgm_read_byte(&EAR_NOTE_ORDER[random(earNoteCount())]);
  } while (next == earLastNote);   // no note twice in a row
  earNote = next;
  earLastNote = next;
  earPlayQuestion();
}

static void earHandleAnswer(uint8_t key) {
  idleReplays = 0;
  uint8_t bit = 1 << earNote;
  if (key == earNote) {
    addPoints(POINTS_PER_EAR_ANSWER);
    earCorrect++;
    ledsSet(bit);
    cuePlay(CUE_CORRECT, false, true);
    afterFeedback = AFTER_QUESTION;
    setMessage(MSG_GOOD);
    if (earCorrect == EAR_CORRECT_TO_LEVEL) {
      uint8_t before = earNoteCount();
      earCorrect = 0;
      earLevel++;
      saveRecord();
      cuePlay(CUE_LEVEL_UP, false, true);
      setMessage(MSG_LEVEL);
      if (earNoteCount() != before) afterFeedback = AFTER_INTRO;
    }
  } else {
    loseLife();
    ledsSet(bit);
    cuePlay(CUE_WRONG, false, true);
    cueTone(NOTE_HZ[earNote], 500, 0, false, true);   // teach the right answer
    afterFeedback = lives == 0 ? AFTER_GAME_OVER : AFTER_QUESTION;
    setMessage(MSG_WRONG);
  }
  setState(ST_FEEDBACK);
}

static void resumeAfterPause() {
  baseTick = tick;
  stopEcho();
  switch (afterFeedback) {
    case AFTER_GAME_OVER: startGameOver(); break;
    case AFTER_WIN: startWin(); break;
    case AFTER_QUESTION: earNewQuestion(); break;
    case AFTER_INTRO: earStartIntro(); break;
    default:
      if (isEar()) earPlayQuestion();
      else beginAttempt();
      break;
  }
}

static void beginGameAfterEasy() {
  randomSeed((uint32_t)analogRead(PIN_SEED) * 31 + micros() + now);
  startGame();
  if (isEar()) {
    earLevel = 1;
    earCorrect = 0;
    earLastNote = 255;
    earStartIntro();
  } else {
    beginAttempt();
  }
}

// --- Screens ---
static void draw() {
  switch (state) {
    case ST_BOOT:
      lcdShow("    MAESTRO", "Ear and memory");
      break;
    case ST_MENU:
      drawTitleItem(F("MAESTRO"), menuItem, KNOB_TICKS);
      strcpy_P(line1, MENU_NAMES[menuItem]);
      lcdShow(line0, line1);
      break;
    case ST_PIECE:
      drawTitleItem(F("Piece"), menuItem, SONG_COUNT + 1);
      if (menuItem == SONG_COUNT) {
        strcpy_P(line1, PSTR("Back"));
      } else {
        Song item;
        memcpy_P(&item, &SONGS[menuItem], sizeof(Song));
        strcpy_P(line1, item.title);
      }
      lcdShow(line0, line1);
      break;
    case ST_YESNO:
      strcpy_P(line0, yesNoKind == YN_EASY ? PSTR("Easy mode?")
                      : yesNoKind == YN_RESET ? PSTR("Clear records?") : PSTR("Quit game?"));
      strcpy_P(line1, yesNoValue ? PSTR("  No      > Yes") : PSTR("> No        Yes"));
      lcdShow(line0, line1);
      break;
    case ST_RECORDS: {
      bool showLevels = ((now - stateSince) / RECORD_FLIP_MS) % 2;
      if (menuItem == SONG_COUNT + 1) {
        lcdShow("Records", "Back");
      } else if (menuItem == SONG_COUNT) {
        Record record = recordGet(SONG_COUNT * 3);
        snprintf_P(line0, sizeof(line0), PSTR("EAR %u pts"), record.points);
        snprintf_P(line1, sizeof(line1), PSTR("Best level %u"), record.level);
        lcdShow(line0, line1);
      } else {
        Song item;
        memcpy_P(&item, &SONGS[menuItem], sizeof(Song));
        uint16_t value[3];
        for (uint8_t m = 0; m < 3; m++) {
          Record record = recordGet(m * SONG_COUNT + menuItem);
          value[m] = showLevels ? record.level : record.points;
        }
        snprintf_P(line0, sizeof(line0), PSTR("%-5S %3S L %u"), item.shortName,
                   showLevels ? PSTR("lvl") : PSTR("pts"), value[0]);
        snprintf_P(line1, sizeof(line1), PSTR("S %-6u B %u"), value[1], value[2]);
        lcdShow(line0, line1);
      }
      break;
    }
    case ST_MESSAGE:
      lcdShow("Records cleared", "");
      break;
    case ST_FREE:
      strcpy_P(line0, PSTR("Free play"));
      if (keyHeld() >= 0) strcpy_P(line1, NOTE_NAMES[keyHeld()]);
      else strcpy_P(line1, PSTR("Press the keys"));
      lcdShow(line0, line1);
      break;
    case ST_IDLE:
      lcdShow("    MAESTRO", "Turn or press");
      break;
    case ST_EAR_INTRO:
      earDrawNotes();
      break;
    case ST_ENDING:
      lcdShow(gameWon ? "You win!" : "Game over", "");
      break;
    case ST_WIN_PIECE:
      lcdShow("You win!", "");
      break;
    case ST_RESULT:
      drawResult();
      break;
    default:
      drawGame();
      break;
  }
}

static bool inGame() {
  return state >= ST_PROMPT && state <= ST_EAR_ANSWER;
}

static bool isMenuLike() {
  return state <= ST_FREE && state != ST_BOOT;
}

static void enterPause() {
  DBG(F("pause"));
  cueStop();
  playStop();
  stopEcho();
  openYesNo(YN_QUIT);
}

static void handleYesNoChoice() {
  ledsSet(0);
  cueStop();
  switch (yesNoKind) {
    case YN_EASY:
      easy = yesNoValue;
      cuePlay(CUE_CONFIRM, true, true);
      beginGameAfterEasy();
      break;
    case YN_RESET:
      if (yesNoValue) {
        recordsClear();
        cuePlay(CUE_CONFIRM, true, true);
        setState(ST_MESSAGE);
      } else {
        cuePlay(CUE_BACK, true, true);
        goMenu();
      }
      break;
    case YN_QUIT:
      if (yesNoValue) {
        saveRecord();
        cuePlay(CUE_BACK, true, true);
        goMenu();
      } else {
        cuePlay(CUE_CONFIRM, true, true);
        resumeAfterPause();
      }
      break;
  }
}

static void handleMenuPress() {
  cueStop();
  ledsSet(0);
  cuePlay(CUE_CONFIRM, true, true);
  switch (menuItem) {
    case ITEM_LIGHT:
    case ITEM_SOUND:
    case ITEM_BOTH:
      mode = (Mode)menuItem;
      goPieceList();
      break;
    case ITEM_EAR:
      mode = MODE_EAR;
      openYesNo(YN_EASY);   // Q34
      break;
    case ITEM_FREE:
      setState(ST_FREE);
      baseTick = tick;
      idleSince = now;
      break;
    case ITEM_RECORDS:
      menuItem = knobItem(SONG_COUNT + 2, 255);
      announceItem(menuItem, SONG_COUNT + 2, true);
      idleSince = now;
      setState(ST_RECORDS);
      break;
    case ITEM_RESET:
      openYesNo(YN_RESET);
      break;
  }
}

void setup() {
  DBG_BEGIN();
  outputBegin();
  recordsBegin();
  inputBegin();
  now = millis();
  tick = knobTick();
  cuePlay(CUE_STARTUP, true, true);
  draw();
}

void loop() {
  now = millis();
  inputUpdate(now);
  outputUpdate(now);
  tick = knobTick();

  uint8_t key = 0;
  uint32_t pressedAt = 0;
  bool pressed = keyTakePress(key, pressedAt);

  // Q9: one knob tick during a game pauses it.
  if (inGame() && tick != baseTick) {
    enterPause();
    pressed = false;
  }

  // Q27: back to the idle screen after a minute with no input.
  if (isMenuLike()) {
    if (pressed || keyHeld() >= 0) idleSince = now;
    if (now - idleSince >= IDLE_AFTER_MS) {
      if (state == ST_YESNO && yesNoKind == YN_QUIT) saveRecord();   // a paused game was left behind
      cueStop();
      stopEcho();
      toneOff();
      ledsSet(0);
      baseTick = tick;
      setState(ST_IDLE);
      pressed = false;
    }
  }

  switch (state) {
    case ST_BOOT:
      if (!cueBusy()) goMenu();
      break;

    case ST_MENU:
      if (tick != menuItem) {
        menuItem = tick;
        cueStop();
        announceItem(menuItem, KNOB_TICKS, false);
        idleSince = now;
        screenDirty = true;
      }
      if (pressed) handleMenuPress();
      break;

    case ST_PIECE: {
      uint8_t item = knobItem(SONG_COUNT + 1, menuItem);
      if (item != menuItem) {
        menuItem = item;
        cueStop();
        announceItem(item, SONG_COUNT + 1, true);
        idleSince = now;
        screenDirty = true;
      }
      if (pressed) {
        cueStop();
        ledsSet(0);
        if (menuItem == SONG_COUNT) {
          cuePlay(CUE_BACK, true, true);
          goMenu();
        } else {
          piece = menuItem;
          memcpy_P(&song, &SONGS[piece], sizeof(Song));
          cuePlay(CUE_CONFIRM, true, true);
          openYesNo(YN_EASY);
        }
      }
      break;
    }

    case ST_RECORDS: {
      uint8_t item = knobItem(SONG_COUNT + 2, menuItem);
      if (item != menuItem) {
        menuItem = item;
        cueStop();
        announceItem(item, SONG_COUNT + 2, true);
        idleSince = now;
        stateSince = now;
        screenDirty = true;
      }
      if ((now - stateSince) % RECORD_FLIP_MS < 25) screenDirty = true;
      if (pressed && menuItem == SONG_COUNT + 1) {
        cueStop();
        ledsSet(0);
        cuePlay(CUE_BACK, true, true);
        goMenu();
      }
      break;
    }

    case ST_YESNO:
      if (tick != yesNoTick) {
        yesNoTick = tick;
        yesNoValue = !yesNoValue;
        cueStop();
        ledsSet(yesNoValue ? MASK_GREEN : MASK_RED);
        cueTone(yesNoValue ? 880 : 196, 150, 0, true, true);
        idleSince = now;
        screenDirty = true;
      }
      if (pressed) handleYesNoChoice();
      break;

    case ST_MESSAGE:
      if (now - stateSince >= MESSAGE_MS) goMenu();
      break;

    case ST_FREE: {
      static int8_t freeKey = -1;
      int8_t held = keyHeld();
      if (held != freeKey) {
        freeKey = held;
        if (held >= 0) {
          ledsSet(1 << held);
          toneOn(NOTE_HZ[held]);
        } else {
          ledsSet(0);
          toneOff();
        }
        screenDirty = true;
      }
      if (tick != baseTick) {   // Q33: nothing to lose, so no "Quit?" screen
        ledsSet(0);
        toneOff();
        freeKey = -1;
        cuePlay(CUE_BACK, true, true);
        goMenu();
      }
      break;
    }

    case ST_IDLE: {
      ledsSet(1 << ((now - stateSince) / IDLE_CHASE_MS % 8));
      if (pressed || tick != baseTick) {
        keyClearPress();
        ledsSet(0);
        goMenu();
      }
      break;
    }

    case ST_PROMPT:
      if (playUpdate()) startInput(ST_INPUT);
      break;

    case ST_INPUT:
      if (pressed) {
        stopEcho();
        handleMelodyPress(key, pressedAt);
      } else {
        if (echoKey >= 0 && keyHeld() < 0) stopEcho();
        if (waitTimedOut()) beginAttempt();
      }
      break;

    case ST_SETTLE: {
      uint32_t age = now - lastPressAt;
      if (age >= SETTLE_MAX_MS || (age >= SETTLE_MIN_MS && keyHeld() < 0)) judgeAttempt();
      break;
    }

    case ST_FEEDBACK:
      if (!cueBusy()) {
        if (afterFeedback == AFTER_QUESTION) {
          ledsSet(0);
          earNewQuestion();
        } else if (afterFeedback == AFTER_INTRO) {
          ledsSet(0);
          earStartIntro();
        } else if (isEar() && afterFeedback == AFTER_RESUME) {
          earPlayQuestion();
        } else {
          finishFeedback();
        }
      }
      break;

    case ST_EAR_INTRO:
      if (!cueBusy()) earNewQuestion();
      break;

    case ST_EAR_PROMPT:
      if (!cueBusy()) startInput(ST_EAR_ANSWER);
      break;

    case ST_EAR_ANSWER:
      if (pressed) earHandleAnswer(key);
      else if (waitTimedOut()) earPlayQuestion();
      break;

    case ST_ENDING:
      if (!cueBusy()) {
        if (gameWon) {
          playStart(song.noteCount, 300);
          setState(ST_WIN_PIECE);
        } else {
          enterResult();
        }
      }
      break;

    case ST_WIN_PIECE:
      if (pressed || playUpdate()) enterResult();
      break;

    case ST_RESULT:
      if ((now - stateSince) % RESULT_FLIP_MS < 25) screenDirty = true;
      if (pressed && now - stateSince >= RESULT_IGNORE_MS) {
        cueStop();
        ledsSet(0);
        cuePlay(CUE_CONFIRM, true, true);
        if (isEar()) goMenu();
        else goPieceList();
      }
      if (now - idleSince >= IDLE_AFTER_MS) {
        cueStop();
        ledsSet(0);
        baseTick = tick;
        setState(ST_IDLE);
      }
      break;
  }

  if (screenDirty) {
    screenDirty = false;
    draw();
  }
}
