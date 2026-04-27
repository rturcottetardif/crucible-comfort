// Stage 0 Gate 0.2 — Sensor readout smoke test
// Project: ComfortSense  |  Target: Seeed XIAO nRF52840 Sense (SKU 102010469)
// Purpose: verify IMU (LSM6DS3TR-C) power sequencing, I2C comms, and plausible
//          raw readings under the enacted arduino-cli + Seeeduino:nrf52 toolchain.
//
// Primitive traceability (Article I / Amendment 1):
//   P1 (Filter ΔP) — this sketch reads the LSM6DS3TR-C 6-axis IMU, which is
//   the direct sensor for the vibration signals (imu_accel_x/y/z, imu_gyro_x/y/z)
//   that feed the Filter ΔP inference chain. Stage 0 verifies sensor hardware
//   responds correctly; it does NOT introduce any threshold or algorithm decision.
//
// Hardware notes (from docs/toolchain_config.md + [S2] LSM6DS3TR-C datasheet):
//   - IMU power via P1.08 (Arduino pin PIN_LSM6DS3TR_C_POWER = 15, active HIGH).
//   - Wait >=45 ms after asserting power before first I2C transaction [S2 Table 3].
//   - I2C address 0x6A (SDO tied to GND), WHO_AM_I register returns 0x6A.
//   - I2C max speed 400 kHz; library default (100 kHz) is fine for Stage 0.

#include "Adafruit_TinyUSB.h"   // Case 1.1 Condition 1a — Seeeduino:nrf52 Serial CDC stack.
#include <Wire.h>
#include <LSM6DS3.h>

LSM6DS3 imu(I2C_MODE, 0x6A);    // SDO=GND on XIAO Sense; primary I2C address.

static const uint32_t IMU_BOOT_DELAY_MS = 50;   // >=45 ms per LSM6DS3TR-C datasheet [S2 Table 3].
static const uint32_t SAMPLE_PERIOD_MS  = 1000; // 1 Hz — human-readable rate for Stage 0.

void setup() {
  Serial.begin(115200);
  unsigned long t0 = millis();
  while (!Serial && (millis() - t0) < 3000) { ; }

  Serial.println();
  Serial.println("STAGE0_SENSOR: start");
  Serial.println("FQBN: Seeeduino:nrf52:xiaonRF52840Sense");
  Serial.println("Test: Gate 0.2 — IMU readout (LSM6DS3TR-C)");

  // Power-sequence the IMU before any I2C activity.
  pinMode(PIN_LSM6DS3TR_C_POWER, OUTPUT);
  digitalWrite(PIN_LSM6DS3TR_C_POWER, HIGH);
  delay(IMU_BOOT_DELAY_MS);
  Serial.print("IMU_POWER HIGH, waited ms="); Serial.println(IMU_BOOT_DELAY_MS);

  // Bring up the LSM6DS3 library (handles I2C Wire.begin + CTRL register writes).
  if (imu.begin() != 0) {
    Serial.println("IMU_INIT: FAIL — imu.begin() returned non-zero");
    // Keep looping so UART stays readable; Stage 0 will mark gate 0.2 FAIL.
  } else {
    Serial.println("IMU_INIT: OK");
  }

  // Read WHO_AM_I directly for explicit evidence in the Stage 0 record.
  uint8_t whoami = 0;
  imu.readRegister(&whoami, LSM6DS3_ACC_GYRO_WHO_AM_I_REG);
  Serial.print("WHO_AM_I: 0x");
  if (whoami < 0x10) Serial.print("0");
  Serial.println(whoami, HEX);
  Serial.println(whoami == 0x6A ? "WHO_AM_I: PASS" : "WHO_AM_I: FAIL");

  Serial.println("STAGE0_SENSOR: entering loop — printing accel+gyro @ 1 Hz");
  Serial.println("Orient board flat for gravity test (Z axis should read ~1.0 g).");
}

void loop() {
  // Raw floats from the LSM6DS3 library are in physical units: g for accel, dps for gyro.
  float ax = imu.readFloatAccelX();
  float ay = imu.readFloatAccelY();
  float az = imu.readFloatAccelZ();
  float gx = imu.readFloatGyroX();
  float gy = imu.readFloatGyroY();
  float gz = imu.readFloatGyroZ();

  Serial.print("READING ts="); Serial.print(millis());
  Serial.print(" ax="); Serial.print(ax, 3);
  Serial.print(" ay="); Serial.print(ay, 3);
  Serial.print(" az="); Serial.print(az, 3);
  Serial.print(" gx="); Serial.print(gx, 2);
  Serial.print(" gy="); Serial.print(gy, 2);
  Serial.print(" gz="); Serial.print(gz, 2);
  Serial.println();

  delay(SAMPLE_PERIOD_MS);
}
