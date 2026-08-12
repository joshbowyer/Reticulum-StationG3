# Building RNode Firmware for Station G3

Reticulum/RNS KISS+command protocol firmware for the Station G3 ESP32-S3 +
SX1262 board (BQ/Uniteng BQESP32V1M + BQ35LORA900V1M). Based on Station G2
firmware with G3 PA/LNA GPIO control, SPI pin map, and SH1106 OLED support.

## Status

**Hardware-verified on a live Station G3** (PA Level 1, jumpers OPEN):

- SPI SX1262 path working (pins SCK=12 MISO=14 MOSI=13 NSS=11)
- OLED SH1106 I2C working (SDA=5 SCL=6 addr 0x3C, column offset 0)
- EEPROM product `0x60` / model `0x63` / board `0x62` provisioned
- TX power ladder 2→32 dBm with Lyra RSSI correlation (monotonic; Level 1)
- Healthy provisioned boot is KISS-clean (no plaintext on serial)

This repo is **ESP32 RNode firmware only**. Pi/Lyra host-side drivers belong
in `reticulum-hat-mod` as a `radio_board` profile (not here).

## Prerequisites

- `arduino-cli`
- ESP32 Core 2.0.17 (ESP32 Core 3.x can cause undefined-reference errors)
- Python 3
- Libraries: Adafruit SH110X, Adafruit GFX (pulled by arduino-cli on compile)

## Build

From `RNode_Firmware_StationG3/`:

```bash
make prep-esp32
make firmware-station_g3
```

Equivalent direct command (verified FQBN):

```bash
arduino-cli compile --log --fqbn "esp32:esp32:esp32s3:CDCOnBoot=cdc" -e \
  --build-property "build.partitions=no_ota" \
  --build-property "upload.maximum_size=2097152" \
  --build-property "compiler.cpp.extra_flags=\"-DBOARD_MODEL=0x62\""
```

Output: `build/esp32.esp32.esp32s3/RNode_Firmware_StationG3.ino.bin`

Upload example:

```bash
arduino-cli upload -p /dev/ttyACM0 --fqbn "esp32:esp32:esp32s3:CDCOnBoot=cdc" .
```

### Post-flash firmware hash (required for radio online)

G3 uses the normal `hw_ready` path (`device_init()`). That compares the EEPROM
**target** firmware hash to `esp_partition_get_sha256()` of the running app
partition — **not** `sha256sum` of the `.bin` file.

After every flash:

```bash
# Read the device-calculated partition hash (hidden rnodeconf flags)
rnodeconf /dev/ttyACM0 -L    # actual hash
rnodeconf /dev/ttyACM0 -K    # target currently in EEPROM

# Set target = actual, then reboot so device_init() re-runs
rnodeconf /dev/ttyACM0 -H <actual_hash_from_-L>
# power-cycle or DTR reset the board
rnodeconf /dev/ttyACM0 -i    # Normal host-controlled, signature OK
```

If target ≠ actual, RNS will report params OK but **Radio reporting state is
offline** (startRadio gated on `hw_ready`). Serial DEBUG on G3 prints
`device_init() FAILED ... fw_ok=0` in that case.

`stat_tx` increments on successful TX; KISS `CMD_STAT_TX` (0x22) returns the
count after a packet.

## Board identity

| Field   | Value  | Notes                          |
|---------|--------|--------------------------------|
| BOARD   | `0x62` | `BOARD_STATION_G3`             |
| PRODUCT | `0x60` | Reuses G2 product byte         |
| MODEL   | `0x63` | Distinct G3 model              |

## Proven pin map (ESP32-S3 path)

| Function     | GPIO | Notes                                      |
|--------------|------|--------------------------------------------|
| SX1262 SCK   | 12   | SPI                                        |
| SX1262 MISO  | 14   | SPI                                        |
| SX1262 MOSI  | 13   | SPI                                        |
| SX1262 NSS   | 11   | SPI CS                                     |
| OLED SDA     | 5    | I2C SH1106                                 |
| OLED SCL     | 6    | I2C SH1106                                 |
| OLED addr    | 0x3C | `StationG3_SH1106G` zeros page-start offset|

Display: landscape rotation 0. Adafruit default `_page_start_offset=2` wraps
two columns on this glass; G3 subclass forces offset 0.

## PA / power (Level 1)

Firmware PA curve (`PA_GAIN_VALUES`, `PA_MAX_OUTPUT=32`) is for **PA Operating
Level 1 only**:

- **PA-PL1 OPEN, PA-PL2 OPEN, LNA-P OPEN** (physical jumpers)
- Antenna or dummy load **required** before power-on
- Barrel PSU 9–19 VDC (≥10 VDC only needed for Level 4 Boost)
- Live RSSI ladder (short link to Lyra MeshAdv, 915 MHz / 125 kHz / SF7 / CR5):
  config TX 2→32 dBm → Lyra RSSI −51→−30 dBm, monotonic, never ≥3 dB hot vs step

See `HARDWARE-RECON.md` for the vendor conducted-power table and jumper matrix.

## Still unverified / deferred

- LED GPIOs (RX/TX placeholders; bodies no-op until schematic confirm)
- LNA gain/GVT fine calibration
- TCXO/current-limit/OCP beyond G2 carry-over defaults
- PA Levels 2–4 (different jumper states; curve not valid)
- Bidirectional RF matrix / long-range tests

## Bring-up checklist

1. Open PA-PL1, PA-PL2, and LNA-P jumpers (Level 1 + LNA on).
2. Antenna connected; PG button all 4 LEDs on; adequate PSU.
3. Flash firmware; provision PRODUCT `0x60` MODEL `0x63` if needed.
4. `rnodeconf -i` → Normal host-controlled, EEPROM OK, signature OK.
5. RNS interface Up at mesh params; OLED shows RNode status UI.
6. Optional: single announce + peer RSSI check before raising TX power.
