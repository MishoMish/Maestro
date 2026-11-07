/* Virtual Маестро: runs the real firmware.elf in simavr, wired however Python says.
 * device.py takes the wiring from tools/guide/wiring.py, the list the build guide is drawn
 * from, so a mistake in the guide shows up here as wrong behaviour.
 * Emulates an HD44780 LCD in 4-bit mode, 8 LEDs and the piezo. A0/A1 voltages come from Python. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "sim_avr.h"
#include "sim_elf.h"
#include "sim_core_decl.h"
#include "avr_ioport.h"
#include "avr_adc.h"
#include "avr_eeprom.h"
#include "avr_uart.h"

#define F_CPU_HZ 16000000UL
#define DDRB 0x24
#define PORTB 0x25
#define DDRC 0x27
#define PORTC 0x28
#define DDRD 0x2A
#define PORTD 0x2B
#define SPL 0x5D
#define SPH 0x5E
#define TONE_GAP_MS 8.0   /* lowest firmware tone is 147 Hz: 3.4 ms between edges */

typedef struct { double t_ms; int kind; int value; } event_t;  /* kind 0 = LEDs, 1 = tone */

static avr_t *avr;
static elf_firmware_t fw;
static event_t *events;
static size_t event_count, event_read;
#define MAX_EVENTS (1u << 21)

static int led_mask = -1;
static char ddram[128];
static int lcd_addr, lcd_8bit = 1, lcd_have_high, lcd_high, lcd_cg;
static uint64_t last_edge, edge_total;
static int tone_on, tone_hz;
static unsigned min_sp;

typedef struct { char port; int bit; } pin_t;
static pin_t led_pins[8], lcd_rs, lcd_e, lcd_d[4], piezo_pin;
static char *uart_buf;
static size_t uart_len, uart_read;
#define UART_MAX (1u << 20)

static int ddr_of(char port) { return port == 'B' ? DDRB : port == 'C' ? DDRC : DDRD; }
static int port_of(char port) { return port == 'B' ? PORTB : port == 'C' ? PORTC : PORTD; }
static int pin_level(pin_t p) { return (avr->data[port_of(p.port)] >> p.bit) & 1; }

static double now_ms(void) { return (double)avr->cycle * 1000.0 / F_CPU_HZ; }

static void log_event(int kind, int value, double t) {
  if (event_count < MAX_EVENTS) { events[event_count++] = (event_t){t, kind, value}; }
}

static int leds_now(void) {
  int mask = 0;
  for (int i = 0; i < 8; i++) {
    if (led_pins[i].port && (avr->data[ddr_of(led_pins[i].port)] & (1 << led_pins[i].bit)) && pin_level(led_pins[i]))
      mask |= 1 << i;
  }
  return mask;
}

static void led_cb(struct avr_irq_t *irq, uint32_t value, void *param) {
  int mask = leds_now();
  if (mask != led_mask) { led_mask = mask; log_event(0, mask, now_ms()); }
}

static void lcd_byte(int rs, int b) {
  if (rs) {
    if (!lcd_cg) { ddram[lcd_addr & 0x7F] = (char)b; lcd_addr = (lcd_addr + 1) & 0x7F; }
  } else if (b & 0x80) { lcd_addr = b & 0x7F; lcd_cg = 0; }
  else if (b & 0x40) { lcd_cg = 1; }
  else if (b & 0x20) { lcd_8bit = (b & 0x10) != 0; }
  else if (b & 0x02) { lcd_addr = 0; }
  else if (b & 0x01) { memset(ddram, ' ', sizeof ddram); lcd_addr = 0; }
}

static void lcd_e_cb(struct avr_irq_t *irq, uint32_t value, void *param) {
  if (value) return;  /* latch on the falling edge of E */
  int nibble = pin_level(lcd_d[0]) | pin_level(lcd_d[1]) << 1 | pin_level(lcd_d[2]) << 2 | pin_level(lcd_d[3]) << 3;
  int rs = pin_level(lcd_rs);
  if (lcd_8bit) { lcd_byte(rs, nibble << 4); lcd_have_high = 0; return; }
  if (!lcd_have_high) { lcd_high = nibble; lcd_have_high = 1; }
  else { lcd_byte(rs, lcd_high << 4 | nibble); lcd_have_high = 0; }
}

static void tone_close(void) {
  if (tone_on) {
    tone_on = 0; tone_hz = 0;
    log_event(1, 0, (double)last_edge * 1000.0 / F_CPU_HZ);
  }
}

/* A tone counts only once two half-periods in a row agree. That filters out the
 * partial period when tone() starts or changes, like a real speaker would. */
static void piezo_cb(struct avr_irq_t *irq, uint32_t value, void *param) {
  static int last_hz;
  uint64_t cycle = avr->cycle;
  double gap_ms = (double)(cycle - last_edge) * 1000.0 / F_CPU_HZ;
  if (edge_total > 0 && gap_ms < TONE_GAP_MS) {
    int hz = (int)((double)F_CPU_HZ / (2.0 * (double)(cycle - last_edge)) + 0.5);
    if (abs(hz - last_hz) * 100 <= hz && (!tone_on || abs(hz - tone_hz) * 100 > tone_hz * 2)) {
      if (tone_on) log_event(1, 0, now_ms());
      tone_on = 1; tone_hz = hz;
      log_event(1, hz, now_ms());
    }
    last_hz = hz;
  } else {
    tone_close();
    last_hz = 0;
  }
  last_edge = cycle;
  edge_total++;
}

static void uart_cb(struct avr_irq_t *irq, uint32_t value, void *param) {
  if (uart_len < UART_MAX) uart_buf[uart_len++] = (char)value;
}

static void watch(char port, int bit, avr_irq_notify_t cb) {
  avr_irq_register_notify(avr_io_getirq(avr, AVR_IOCTL_IOPORT_GETIRQ(port), bit), cb, NULL);
}

void sim_close(void) {
  if (avr) { avr_terminate(avr); free(avr); avr = NULL; }
}

int sim_open(const char *elf_path) {
  sim_close();
  memset(&fw, 0, sizeof fw);
  if (elf_read_firmware(elf_path, &fw) != 0) return -1;
  strcpy(fw.mmcu, "atmega328p");
  fw.frequency = F_CPU_HZ;
  fw.vcc = 5000; fw.avcc = 5000; fw.aref = 5000;
  avr = avr_make_mcu_by_name(fw.mmcu);
  if (!avr) return -2;
  avr_init(avr);
  avr->log = LOG_ERROR;
  avr_load_firmware(avr, &fw);
  avr->frequency = F_CPU_HZ;
  avr->vcc = 5000; avr->avcc = 5000; avr->aref = 5000;

  if (!events) events = malloc(MAX_EVENTS * sizeof(event_t));
  event_count = event_read = 0;
  led_mask = -1;
  memset(ddram, ' ', sizeof ddram);
  lcd_addr = 0; lcd_8bit = 1; lcd_have_high = 0; lcd_cg = 0;
  last_edge = 0; edge_total = 0; tone_on = 0; tone_hz = 0;
  min_sp = 0xFFFF;

  memset(led_pins, 0, sizeof led_pins);
  if (!uart_buf) uart_buf = malloc(UART_MAX);
  uart_len = uart_read = 0;
  /* Stop simavr printing the serial output itself, and keep a copy for Python. */
  uint32_t flags = 0;
  avr_ioctl(avr, AVR_IOCTL_UART_GET_FLAGS('0'), &flags);
  flags &= ~(AVR_UART_FLAG_STDIO | AVR_UART_FLAG_POLL_SLEEP);
  avr_ioctl(avr, AVR_IOCTL_UART_SET_FLAGS('0'), &flags);
  avr_irq_register_notify(avr_io_getirq(avr, AVR_IOCTL_UART_GETIRQ('0'), UART_IRQ_OUTPUT), uart_cb, NULL);
  return 0;
}

/* Wiring, from Python. kind: 0 LED (index = key), 1 LCD RS, 2 LCD E, 3 LCD data (index 0-3), 4 piezo. */
void sim_wire(int kind, int index, char port, int bit) {
  pin_t pin = {port, bit};
  switch (kind) {
    case 0: led_pins[index] = pin; watch(port, bit, led_cb); break;
    case 1: lcd_rs = pin; break;
    case 2: lcd_e = pin; watch(port, bit, lcd_e_cb); break;
    case 3: lcd_d[index] = pin; break;
    case 4: piezo_pin = pin; watch(port, bit, piezo_cb); break;
  }
}

size_t sim_uart(char *out, size_t max) {
  size_t n = 0;
  while (uart_read < uart_len && n < max) out[n++] = uart_buf[uart_read++];
  return n;
}

/* Runs the firmware for ms milliseconds. Returns 0, or the CPU state if it stopped. */
int sim_run_ms(double ms) {
  uint64_t target = avr->cycle + (uint64_t)(ms * F_CPU_HZ / 1000.0);
  while (avr->cycle < target) {
    int state = avr_run(avr);
    if (state == cpu_Done || state == cpu_Crashed) return state;
    unsigned sp = avr->data[SPL] | avr->data[SPH] << 8;
    if (sp < min_sp && sp >= 0x100) min_sp = sp;
  }
  if (tone_on && (double)(avr->cycle - last_edge) * 1000.0 / F_CPU_HZ > TONE_GAP_MS) tone_close();
  return 0;
}

void sim_set_adc(int channel, int millivolts) {
  avr_raise_irq(avr_io_getirq(avr, AVR_IOCTL_ADC_GETIRQ, ADC_IRQ_ADC0 + channel), millivolts);
}

double sim_now_ms(void) { return now_ms(); }
int sim_leds(void) { return leds_now(); }
int sim_tone_hz(void) { return tone_on ? tone_hz : 0; }
unsigned sim_min_sp(void) { return min_sp; }

void sim_lcd(int row, char *out) {
  memcpy(out, ddram + (row ? 0x40 : 0), 16);
  out[16] = 0;
}

size_t sim_events(event_t *out, size_t max) {
  size_t n = 0;
  while (event_read < event_count && n < max) out[n++] = events[event_read++];
  return n;
}

int sim_eeprom_get(unsigned addr, unsigned char *out, unsigned size) {
  avr_eeprom_desc_t desc = {out, addr, size};
  return avr_ioctl(avr, AVR_IOCTL_EEPROM_GET, &desc);
}

int sim_eeprom_set(unsigned addr, unsigned char *in, unsigned size) {
  avr_eeprom_desc_t desc = {in, addr, size};
  return avr_ioctl(avr, AVR_IOCTL_EEPROM_SET, &desc);
}

/* Debugging: one byte of the AVR's data memory (registers, I/O and RAM). */
int sim_peek(unsigned addr) { return addr <= 0x8FF ? avr->data[addr] : -1; }
