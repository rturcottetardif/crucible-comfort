/*
 * stage1_algo_usb.ino — Stage 1 algorithm firmware (Bill 4, Case 7).
 *
 * Implements Bills 1–3 vibration-proxy algorithm in C. Emits ALERT events
 * per the Bill 4 UART format. Supports two build targets:
 *
 *   Normal (real hardware):
 *     arduino-cli compile --fqbn Seeeduino:nrf52:xiaonRF52840Sense
 *     Reads LSM6DS3TR-C at 1660 Hz ODR. UART via USB CDC (Serial).
 *
 *   Renode simulation:
 *     arduino-cli compile --fqbn Seeeduino:nrf52:xiaonRF52840Sense \
 *       --build-properties "build.extra_flags=-DCONFIG_CRUCIBLE_RENODE_SIM"
 *     Reads virtual IMU stub at 0x400B0000. UART via UARTE0/Serial1.
 *
 * Constitutional grounding:
 *   Article I  — every constant traces to Amendment 1 P1 (Filter ΔP).
 *   Case 1a    — Adafruit_TinyUSB.h required for Serial CDC on nRF52840.
 *   Bill 1 (Case 2)  — A_FUND_CLEAN, ALPHA, A_Z_DC, RMS_HARM_FACTOR.
 *   Bill 4 (Case 7)  — ALERT UART event; this firmware file.
 *   Amendment 1 P1   — ALERT_THRESH = 1.8 (alert window low edge).
 */

#include "Adafruit_TinyUSB.h"  // Case 1a — required for Serial CDC on nRF52840

#ifndef CONFIG_CRUCIBLE_RENODE_SIM
#include <Wire.h>
#include "LSM6DS3.h"
#endif

// ── Algorithm constants — Bill 1 (Case 2), traces to Amendment 1 P1 ──────
// A_Z_DC: gravity reference. Gate 0.2 az ≈ 0.975 g ≈ 1 g; A1 P1.
#define A_Z_DC          1.0f
// A_FUND_CLEAN: clean-filter vibration amplitude at fundamental. Bill 1; A1 P1.
#define A_FUND_CLEAN    0.05f
// ALPHA: ΔP exponent (linear first-order). Bill 1; A1 P1.
// ALPHA = 1 → dp_ratio = rms_ac / (A_FUND_CLEAN * RMS_HARM_FACTOR) (identity).
#define ALPHA           1.0f
// RMS_HARM_FACTOR: analytic RMS of Bill 1 harmonic stack (1, 1/3, 1/6).
// = √(0.5·(1 + 1/9 + 1/36)) = √(41/72) ≈ 0.7546. Case 3; A1 P1.
#define RMS_HARM_FACTOR 0.7546f
// ALERT_THRESH: Amendment 1 P1 alert window low edge — not a calibration constant.
#define ALERT_THRESH    1.8f

// ── Window — Signal Inventory: IMU at 1660 Hz, 1-second decision window ──
// Traces to Signal Inventory FS_IMU_HZ = 1660 Hz; A1 P1.
#define N_WINDOW  1660

// ── Regime default for IMU-only path ─────────────────────────────────────
// No outside_temp available in Renode bridge (N×6 IMU only). Default =
// "cooling" per Bill 2-A (Case 3) conservative bias for ndarray/IMU-only path.
#define REGIME_DEFAULT  "cooling"

// ── Window accumulation buffer ────────────────────────────────────────────
static float  az_buf[N_WINDOW];
static int    buf_idx      = 0;
static bool   session_done = false;

// Forward declarations
static void push_sample(float az);
static void emit_alert(void);

// ─────────────────────────────────────────────────────────────────────────
// RENODE SIMULATION PATH
// ─────────────────────────────────────────────────────────────────────────
#ifdef CONFIG_CRUCIBLE_RENODE_SIM

// Virtual IMU peripheral (crucible/sim/stubs/sim_imu_stub.py).
// Register map at base 0x400B0000:
//   0x00–0x03  STATUS uint32 LE (1 = sample ready, 0 = exhausted)
//   0x04–0x1B  6 × float32 LE: [ax ay az gx gy gz]
//   0x1C       ACK — write any value to advance to next sample
// Must read starting at offset 0x04 to trigger stub's sample cache load.
#define SIM_IMU_BASE  0x400B0000UL
static volatile uint8_t* const sim_base = (volatile uint8_t*)SIM_IMU_BASE;

static bool sim_sample_ready(void) {
    uint32_t status =
        (uint32_t)sim_base[0]
        | ((uint32_t)sim_base[1] << 8)
        | ((uint32_t)sim_base[2] << 16)
        | ((uint32_t)sim_base[3] << 24);
    return status != 0;
}

static float sim_read_az(void) {
    // Read full 24-byte sample starting at offset 4 — triggers stub cache load.
    // az is the 3rd float (index 2, byte offset 8 within the 24-byte block).
    uint8_t buf[24];
    for (int i = 0; i < 24; i++) buf[i] = sim_base[4 + i];
    float az;
    memcpy(&az, buf + 8, 4);
    return az;
}

static void sim_ack(void) {
    sim_base[0x1C] = 1;
}

void setup() {
    // UARTE0/Serial1 captured by sim_uart_stub at 0x40002000. Bill 4 §5.
    Serial1.begin(115200);
}

void loop() {
    if (session_done) return;
    if (!sim_sample_ready()) {
        Serial1.println("SESSION_END");
        session_done = true;
        return;
    }
    float az = sim_read_az();
    sim_ack();
    push_sample(az);
}

// ─────────────────────────────────────────────────────────────────────────
// REAL HARDWARE PATH
// ─────────────────────────────────────────────────────────────────────────
#else  // CONFIG_CRUCIBLE_RENODE_SIM

LSM6DS3 imu(I2C_MODE, 0x6A);  // I2C address 0x6A — Gate 0.2 WHO_AM_I=0x6A

void setup() {
    Serial.begin(115200);
    unsigned long t = millis();
    while (!Serial && (millis() - t < 3000)) {}

    // Power-enable IMU — Gate 0.2 power sequencing (50 ms delay per S2 Table 3).
    pinMode(PIN_LSM6DS3TR_C_POWER, OUTPUT);
    digitalWrite(PIN_LSM6DS3TR_C_POWER, HIGH);
    delay(50);

    // 1660 Hz ODR, ±2 g — Signal Inventory; traces to A1 P1.
    imu.settings.accelSampleRate = 1660;
    imu.settings.accelRange      = 2;
    imu.settings.gyroEnabled     = 0;  // gyro unused by Bills 1-3 algorithm

    if (imu.begin() != IMU_SUCCESS) {
        Serial.println("IMU_INIT: FAILED");
        while (true) {}
    }
    Serial.println("IMU_INIT: OK");
}

void loop() {
    float az = imu.readFloatAccelZ();  // g — traces to A1 P1
    push_sample(az);
}

#endif  // CONFIG_CRUCIBLE_RENODE_SIM

// ─────────────────────────────────────────────────────────────────────────
// ALGORITHM (shared by both paths)
// ─────────────────────────────────────────────────────────────────────────

static void push_sample(float az) {
    az_buf[buf_idx++] = az;
    if (buf_idx >= N_WINDOW) {
        emit_alert();
        buf_idx = 0;
    }
}

static void emit_alert(void) {
    // Step C — gravity-subtract, compute AC RMS. Traces to A1 P1.
    float sum_sq = 0.0f;
    for (int i = 0; i < N_WINDOW; i++) {
        float ac = az_buf[i] - A_Z_DC;
        sum_sq += ac * ac;
    }
    float rms_ac = sqrtf(sum_sq / (float)N_WINDOW);

    // Step D — vibration → ΔP/ΔP₀ inversion. ALPHA=1 identity: see Bill 4 §4.
    // Forward model (Bill 1): rms_ac = A_FUND_CLEAN * dp_ratio * RMS_HARM_FACTOR
    // Inverse (ALPHA=1):       dp_ratio = rms_ac / (A_FUND_CLEAN * RMS_HARM_FACTOR)
    float dp_ratio = (rms_ac > 0.0f)
        ? rms_ac / (A_FUND_CLEAN * RMS_HARM_FACTOR)
        : 1.0f;  // default to clean — traces to A1 P1

    // Step G — alert per Amendment 1 P1 alert window low edge.
    bool alert = (dp_ratio >= ALERT_THRESH);

    // Bill 4 (Case 7) ALERT UART event.
#ifdef CONFIG_CRUCIBLE_RENODE_SIM
    Serial1.print("ALERT ts=");
    Serial1.print(millis());
    Serial1.print(" dp=");
    Serial1.print(dp_ratio, 4);
    Serial1.print(" regime=" REGIME_DEFAULT " alert=");
    Serial1.println(alert ? "1" : "0");
#else
    Serial.print("ALERT ts=");
    Serial.print(millis());
    Serial.print(" dp=");
    Serial.print(dp_ratio, 4);
    Serial.print(" regime=" REGIME_DEFAULT " alert=");
    Serial.println(alert ? "1" : "0");
#endif
}
