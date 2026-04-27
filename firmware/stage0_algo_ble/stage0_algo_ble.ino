// Stage 0 Gate 0.4 — Algorithm over Wireless smoke test
// Project: ComfortSense  |  Target: Seeed XIAO nRF52840 Sense (SKU 102010469)
// Purpose: prove the sensor → algorithm → BLE NUS pipeline end-to-end.
//
// Algorithm: identical to firmware/stage0_algo_usb/stage0_algo_usb.ino —
//   100 Hz accel sampling, 500 ms sliding window, RMS of accel magnitude,
//   2 Hz METRIC emission. Gate 0.4 validates the WIRELESS TRANSPORT only;
//   algorithm behaviour was already validated at Gate 0.3 (see Test Results).
//
// Advertised BLE name: ComfortSense — matches the active toolchain
//   wireless_receiver contract in docs/toolchain_config.md
//   (host connects via BleConsole(device_name="ComfortSense") over Nordic UART
//   Service, UUIDs 6E400001/2/3-B5A3-F393-E0A9-E50E24DCCA9E).
//
// Article I note: no thresholds introduced. RMS is a raw derived quantity.
//   Primitive trace identical to Gate 0.3 sketch — P1 (Filter ΔP) sensor chain,
//   Stage 0 liveness only.
//
// Known issues from docs/toolchain_config.md guarded against:
//   - Name truncation in ADV packet → name in ScanResponse, NUS UUID in ADV.
//   - "Write gated on connected()" silent drop → bleuart.write called unconditionally.
//   - MTU fragmentation → METRIC line kept short (< 40 bytes, within default MTU chunk).
//
// Also emits METRIC lines over USB Serial so the host can compare wired vs
// wireless streams line-for-line in the same run (parity check for Gate 0.4).

#include "Adafruit_TinyUSB.h"   // Case 1.1 Condition 1a.
#include <Wire.h>
#include <LSM6DS3.h>
#include <bluefruit.h>
#include <math.h>

LSM6DS3 imu(I2C_MODE, 0x6A);
BLEUart bleuart;

static const uint32_t IMU_BOOT_DELAY_MS = 50;     // >=45 ms per [S2 Table 3].
static const uint32_t SAMPLE_PERIOD_MS  = 10;     // 100 Hz sampling (LSM6DS3 ODR=104 Hz nearest).
static const uint32_t WINDOW_SAMPLES    = 50;     // 500 ms sliding window at 100 Hz.
static const uint32_t REPORT_PERIOD_MS  = 500;    // 2 Hz METRIC emission — practical basis:
                                                  // fast enough to confirm liveness in a ~15 s
                                                  // Gate 0.4 observation window without saturating
                                                  // BLE NUS; no P1/P2 detection logic here.

static float magsq_buf[WINDOW_SAMPLES];
static size_t buf_idx  = 0;
static bool   buf_full = false;

static uint32_t last_sample_ms = 0;
static uint32_t last_report_ms = 0;

void startAdv() {
  Bluefruit.Advertising.addFlags(BLE_GAP_ADV_FLAGS_LE_ONLY_GENERAL_DISC_MODE);
  Bluefruit.Advertising.addTxPower();
  Bluefruit.Advertising.addService(bleuart);     // 128-bit NUS UUID in ADV packet.
  Bluefruit.ScanResponse.addName();              // Name in scan response (no room in ADV).
  Bluefruit.Advertising.restartOnDisconnect(true);
  Bluefruit.Advertising.setInterval(32, 244);    // Units of 0.625 ms: 20 ms fast / 152.5 ms slow.
  Bluefruit.Advertising.setFastTimeout(30);
  Bluefruit.Advertising.start(0);                // 0 = advertise forever until connected.
}

void setup() {
  Serial.begin(115200);
  unsigned long t0 = millis();
  while (!Serial && (millis() - t0) < 3000) { ; }

  Serial.println();
  Serial.println("STAGE0_ALGO_BLE: start");
  Serial.println("FQBN: Seeeduino:nrf52:xiaonRF52840Sense");
  Serial.println("Test: Gate 0.4 — accel RMS over BLE NUS (name=ComfortSense)");

  pinMode(PIN_LSM6DS3TR_C_POWER, OUTPUT);
  digitalWrite(PIN_LSM6DS3TR_C_POWER, HIGH);
  delay(IMU_BOOT_DELAY_MS);

  if (imu.begin() != 0) {
    Serial.println("IMU_INIT: FAIL — halting algorithm loop");
    while (true) { delay(1000); }
  }
  Serial.println("IMU_INIT: OK");

  for (size_t i = 0; i < WINDOW_SAMPLES; i++) magsq_buf[i] = 0.0f;

  // BANDWIDTH_MAX + fast conn interval — required to sustain the METRIC byte rate
  // over BLE NUS. Without configPrphBandwidth, the default SoftDevice TX buffer is
  // too small to carry a 34-byte METRIC line per 500 ms window; tail bytes drop
  // silently (observed at Gate 0.4 first flash: ~23 of 34 bytes delivered per line).
  // Must be called BEFORE Bluefruit.begin() per Bluefruit52Lib contract.
  Bluefruit.configPrphBandwidth(BANDWIDTH_MAX);
  Bluefruit.begin();
  Bluefruit.Periph.setConnInterval(6, 24);       // min=7.5 ms, max=30 ms — drains TX FIFO fast.
  Bluefruit.setName("ComfortSense");
  Bluefruit.setTxPower(4);                       // +4 dBm; range covers a rooftop-side HVAC gateway.
  bleuart.begin();
  startAdv();
  Serial.println("BLE_INIT: OK — advertising as 'ComfortSense'");

  Serial.println("STAGE0_ALGO_BLE: entering loop — METRIC @ 2 Hz over BLE NUS + USB serial");
}

void loop() {
  uint32_t now = millis();

  if (now - last_sample_ms >= SAMPLE_PERIOD_MS) {
    last_sample_ms = now;
    float ax = imu.readFloatAccelX();
    float ay = imu.readFloatAccelY();
    float az = imu.readFloatAccelZ();
    magsq_buf[buf_idx] = (ax * ax) + (ay * ay) + (az * az);
    buf_idx = (buf_idx + 1) % WINDOW_SAMPLES;
    if (buf_idx == 0) buf_full = true;
  }

  if (now - last_report_ms >= REPORT_PERIOD_MS) {
    last_report_ms = now;
    size_t n = buf_full ? WINDOW_SAMPLES : buf_idx;
    if (n > 0) {
      float sum_magsq = 0.0f;
      for (size_t i = 0; i < n; i++) sum_magsq += magsq_buf[i];
      float mean_magsq = sum_magsq / (float)n;
      float rms = sqrtf(mean_magsq);

      char line[64];
      int len = snprintf(line, sizeof(line),
                         "METRIC ts=%lu rms_g=%.4f n=%u\n",
                         (unsigned long)now, rms, (unsigned)n);
      if (len > 0 && len < (int)sizeof(line)) {
        Serial.write((const uint8_t*)line, len);
        bleuart.write((const uint8_t*)line, len);   // unconditional — do not gate on connected().
      }
    }
  }
}
