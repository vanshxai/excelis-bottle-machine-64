// 150 RPM Gear System -- INA228 QT fast current streamer (ESP32 side).
//
// v2: switched from 10Hz tagged-ASCII telemetry to paced fast sampling.
// Reason, from this project's own recorded touch-test data (see
// gearsystem_metal_verified_twin.json / constraint_registry_metal.json):
// a real touch on a spinning gear produces a current spike with a 2-3ms
// RISE TIME and under 10ms total duration ("spike_then_partial_recovery").
// At 10Hz (100ms/sample) that event falls between samples essentially every
// time -- not a calibration problem, a sampling-rate problem. This sketch
// exists to actually be fast enough to see it.
//
// v3: dropped bus-voltage entirely (user call: current signature is the only
// thing this project needs, voltage was never asked for). CONT_SHUNT mode
// means the chip's ADC only ever converts the shunt channel, so the same
// COUNT_4/280us settings now update roughly 2x faster than when it was also
// cycling through a bus-voltage conversion every sample.
//
// v4: dropped the binary block protocol (magic bytes/seq/checksum framing)
// in favor of one plain-text integer per line. At ~893Hz the wire only ever
// carries ~1.8KB/s either way (256-sample blocks every ~287ms) -- nowhere
// near enough traffic to need packing into binary, and the block format was
// only there because it was copied from the older ACS712 sketch, not because
// this rate required it. A bad/partial line just fails to parse as an int on
// the Python side and gets skipped -- self-resyncing on the next newline,
// no checksum needed on a wired USB-serial link.
//
// INA228 config for speed: CONT_SHUNT mode, COUNT_4 hardware averaging,
// 280us conversion time -> ~1120us/internal update -> ~893Hz theoretical
// ceiling (measured idle: rock solid, hit target almost exactly; measured
// with the motor running: degrades to 74-450Hz, unstable, gaps up to a few
// seconds -- confirmed via direct A/B test to be motor electrical noise on
// the I2C lines, not a pacing/setting problem. Not solved by this sketch;
// see the app-side gateway's auto-reconnect for how that's handled instead
// of just hanging.
//
// TRANSPORT: plain text, one line per sample -- current in whole mA, signed,
// e.g. "23\n" or "-4\n". gearsystem150_app.py's gateway reads lines and
// batches every 256 of them into one block before handing off to the same
// processing/classification code the old binary protocol fed -- see its
// module comment for the Python-side block handling and touch detection.

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_INA228.h>

const int PIN_SDA = 21;
const int PIN_SCL = 22;
const uint32_t I2C_CLOCK_HZ = 400000; // Fast Mode

const float SHUNT_OHMS = 0.015;   // Adafruit INA228 QT breakout onboard shunt
const float MAX_CURRENT_A = 5.0;  // see prior bring-up note -- adjust to known motor current

// The shunt's IN+/IN- leads read backwards relative to the motor's actual
// current path (confirmed during bring-up: readCurrent() was consistently
// negative running forward). Flipping the sign here is equivalent to
// swapping the two shunt leads physically.
const float CURRENT_SIGN = -1.0;

const uint32_t SAMPLE_PERIOD_US = 1120; // paced target -- COUNT_4 x 280us, shunt-only (see header note)
const uint32_t SERIAL_BAUD = 460800; // proven reliable in this project at much higher throughput than this needs

uint32_t next_sample_us = 0;

Adafruit_INA228 ina228;

void haltBlinking(const char *msg) {
  while (true) {
    Serial.println(msg);
    delay(1000);
  }
}

uint8_t scanI2C() {
  Serial.println("Scanning I2C bus...");
  uint8_t found = 0;
  uint8_t firstAddr = 0;
  for (uint8_t addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      Serial.printf("  device found at 0x%02X\n", addr);
      if (found == 0) firstAddr = addr;
      found++;
    }
  }
  if (found == 0) {
    Serial.println("  nothing found -- check wiring (SDA=GPIO21, SCL=GPIO22, VIN, GND).");
    return 0;
  }
  return firstAddr;
}

void setup() {
  Serial.setTxBufferSize(4096); // oversized so Serial.write() doesn't block mid-block and skew pacing
  Serial.begin(SERIAL_BAUD);
  delay(300);
  Serial.println();
  Serial.println("=== INA228 QT fast current-only streamer -- 150 RPM gear system ===");

  Wire.begin(PIN_SDA, PIN_SCL);
  Wire.setClock(I2C_CLOCK_HZ);
  // Default Wire timeout is 50ms -- measured live, block-fill gaps of up to
  // 6s matched roughly (gap_ms / 50ms) stalled transactions per block almost
  // exactly, meaning a large fraction of I2C reads are stalling against
  // electrical noise from the running motor, each blocking for the full 50ms
  // before giving up. Cutting the timeout to 5ms doesn't fix the underlying
  // noise, but stops one bad transaction from eating 10x its fair share of
  // the block's time budget.
  Wire.setTimeOut(5);

  uint8_t addr = scanI2C();
  if (addr == 0) {
    haltBlinking("No I2C device found. Halting.");
  }

  if (!ina228.begin(addr, &Wire)) {
    Serial.printf("Found an I2C device at 0x%02X but INA228.begin() failed "
                  "-- wrong address for this chip? Halting.\n", addr);
    haltBlinking("INA228 init failed.");
  }
  Serial.printf("INA228 found and initialized at 0x%02X\n", addr);

  ina228.setShunt(SHUNT_OHMS, MAX_CURRENT_A);
  ina228.setAveragingCount(INA228_COUNT_4);
  ina228.setCurrentConversionTime(INA228_TIME_280_us);
  ina228.setMode(INA2XX_MODE_CONT_SHUNT); // current only -- see v3 header note

  Serial.printf("Calibrated: shunt=%.4f ohm, max_current=%.2f A, target %lu us/sample\n",
                SHUNT_OHMS, MAX_CURRENT_A, (unsigned long)SAMPLE_PERIOD_US);

  Serial.println("Self-test samples:");
  for (int i = 0; i < 5; i++) {
    float mA = CURRENT_SIGN * ina228.readCurrent();
    Serial.printf("  I=%.3f mA\n", mA);
    delay(100);
  }
  Serial.println("--- starting fast text stream ---");
  Serial.println();
  next_sample_us = micros();
}

void loop() {
  while ((int32_t)(micros() - next_sample_us) < 0) { /* spin -- absolute scheduling avoids drift */ }
  float mA = CURRENT_SIGN * ina228.readCurrent();
  Serial.println((int16_t)mA); // wire units: whole mA, signed, one per line
  next_sample_us += SAMPLE_PERIOD_US;
}
