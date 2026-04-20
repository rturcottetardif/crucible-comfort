// Stage 0 Gate 0.3 — Algorithm over USB smoke test
// Project: ComfortSense  |  Target: Seeed XIAO nRF52840 Sense (SKU 102010469)
// Purpose: prove the sensor → algorithm → UART pipeline end-to-end.
//
// Algorithm (intentionally minimal):
//   Sample accel X/Y/Z at 100 Hz. Over a sliding 500 ms window (50 samples),
//   compute RMS of the accel-magnitude series. Emit a METRIC line every
//   500 ms with the current RMS.
//
// Article I note: no thresholds are introduced. RMS is a raw derived
//   quantity, not a detection decision. Gate 0.3 validates that the
//   sensor → algorithm → UART path works; it does NOT implement the
//   Filter ΔP detection logic (that is Stage 1+ work, Bill-governed).
//
// Primitive traceability (Amendment 1):
//   Derived from P1 (Filter ΔP) sensor chain — vibration is one of the
//   three signals that will later feed the Filter ΔP inference.
//   RMS of accel magnitude is the simplest scalar summary of vibration
//   energy and is used here only as a Stage 0 liveness metric.
//
// Expected behaviour on validated hardware:
//   - Stationary board: rms_g ≈ 1.000 ± 0.002 (gravity + sensor noise floor).
//   - Moved / tapped board: rms_g measurably higher (sensitivity to motion
//     is what Gate 0.3 specifically checks for — the "zero-when-should-be-
//     nonzero" trap from /session 0 Stage 0 Smoke Test 3).

#include "Adafruit_TinyUSB.h"   // Case 1.1 Condition 1a.
#include <Wire.h>
#include <LSM6DS3.h>
#include <math.h>

LSM6DS3 imu(I2C_MODE, 0x6A);

static const uint32_t IMU_BOOT_DELAY_MS = 50;     // >=45 ms per [S2 Table 3].
static const uint32_t SAMPLE_PERIOD_MS  = 10;     // 100 Hz sampling (LSM6DS3 ODR=104 Hz nearest).
static const uint32_t WINDOW_SAMPLES    = 50;     // 500 ms sliding window at 100 Hz.
static const uint32_t REPORT_PERIOD_MS  = 500;    // 2 Hz METRIC emission — practical basis:
                                                  // fast enough to confirm liveness in a ~10 s
                                                  // Gate 0.3 observation window without saturating
                                                  // UART; no P1/P2 detection logic here (Stage 0
                                                  // liveness only, per sketch header Article I note).

static float magsq_buf[WINDOW_SAMPLES];
static size_t buf_idx  = 0;
static bool   buf_full = false;

static uint32_t last_sample_ms = 0;
static uint32_t last_report_ms = 0;

void setup() {
  Serial.begin(115200);
  unsigned long t0 = millis();
  while (!Serial && (millis() - t0) < 3000) { ; }

  Serial.println();
  Serial.println("STAGE0_ALGO_USB: start");
  Serial.println("FQBN: Seeeduino:nrf52:xiaonRF52840Sense");
  Serial.println("Test: Gate 0.3 — accel RMS over 500 ms window, 100 Hz sampling");

  pinMode(PIN_LSM6DS3TR_C_POWER, OUTPUT);
  digitalWrite(PIN_LSM6DS3TR_C_POWER, HIGH);
  delay(IMU_BOOT_DELAY_MS);

  if (imu.begin() != 0) {
    Serial.println("IMU_INIT: FAIL — halting algorithm loop");
    while (true) { delay(1000); }
  }
  Serial.println("IMU_INIT: OK");

  for (size_t i = 0; i < WINDOW_SAMPLES; i++) magsq_buf[i] = 0.0f;

  Serial.println("STAGE0_ALGO_USB: entering loop — METRIC @ 2 Hz");
  Serial.println("Expect rms_g ≈ 1.000 when still; higher when moved.");
}

void loop() {
  uint32_t now = millis();

  // 100 Hz sampling.
  if (now - last_sample_ms >= SAMPLE_PERIOD_MS) {
    last_sample_ms = now;
    float ax = imu.readFloatAccelX();
    float ay = imu.readFloatAccelY();
    float az = imu.readFloatAccelZ();
    magsq_buf[buf_idx] = (ax * ax) + (ay * ay) + (az * az);
    buf_idx = (buf_idx + 1) % WINDOW_SAMPLES;
    if (buf_idx == 0) buf_full = true;
  }

  // 2 Hz METRIC emission.
  if (now - last_report_ms >= REPORT_PERIOD_MS) {
    last_report_ms = now;
    size_t n = buf_full ? WINDOW_SAMPLES : buf_idx;
    if (n > 0) {
      float sum_magsq = 0.0f;
      for (size_t i = 0; i < n; i++) sum_magsq += magsq_buf[i];
      float mean_magsq = sum_magsq / (float)n;
      float rms = sqrtf(mean_magsq);
      Serial.print("METRIC ts="); Serial.print(now);
      Serial.print(" rms_g=");    Serial.print(rms, 4);
      Serial.print(" n=");        Serial.println(n);
    }
  }
}
