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
- WiFi STA TCP KISS (port 7633) + unpaced RNS `initRadio` / announce
- BLE NUS advertise + bond + RNS-over-BLE announce

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
offline** (`startRadio` gated on `hw_ready`). Confirm with KISS `CMD_HASHES`
`0x01` (target) vs `0x02` (actual), or `rnodeconf -K` / `-L`.

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

## WiFi STA (TCP KISS on port 7633)

Firmware has `HAS_WIFI` + `Remote.h` TCP listener. Configure over USB once:

```bash
rnodeconf /dev/ttyACM0 --ssid "YourSSID" --psk 'YourPSK' -w STATION
rnodeconf /dev/ttyACM0 -i   # note DHCP IP
```

RNS interface block:

```
type = RNodeInterface
port = tcp://10.0.0.57
# NO :7633 — RNS TCPConnection hardcodes TARGET_PORT=7633.
# tcp://IP:7633 is treated as a hostname and fails DNS.
frequency = 915000000
bandwidth = 125000
txpower = 14
spreadingfactor = 7
codingrate = 5
```

**Verified (live G3):** STA join, TCP 7633 open, RNS interface Up, announce
`txb=167` / airtime `1.87` over WiFi.

**G3 PA floor:** with `HAS_LORA_PA`, `setTXPower()` maps target → modem then
rewrites reported `lora_txp` to nearest achievable antenna dBm (floor ~14).
Use **`txpower >= 14`** or RNS `validateRadioState` fails (e.g. request 2 →
radio reports 14).

**TCP KISS drain:** older firmware only pulled 10 bytes/loop from the WiFi
socket (`buffer_serial` `MAX_CYCLES`), so RNS burst `initRadio()` could drop
frames. Current firmware uses `MAX_CYCLES_REMOTE` (512) when a WiFi or BLE
host is connected, and does not tear down the TCP socket on a transient empty
read. Unpaced RNS-over-WiFi is verified after this fix (still requires a
matching firmware hash so `hw_ready` is true).

`rnodeconf --config` may print both `WiFi: Enabled (Station)` and
`WiFi: Disabled` — upstream if/else cosmetic bug; firmware state is fine.

## BLE (Nordic UART)

- `HAS_BLE true`, `HAS_BLUETOOTH false`
- Enable: `rnodeconf /dev/ttyACM0 -b`
- Pair: `rnodeconf /dev/ttyACM0 -p` (interactive TTY) or KISS `CMD_BT_CTRL`
  `0x01` enable / `0x02` pair (~35 s window). Passkey on OLED / `CMD_BT_PIN`.
- Advertise name `RNode XXXX`; BLE MAC = WiFi MAC + 1; NUS UUID
  `6e400001-b5a3-f393-e0a9-e50e24dcca9e`
- RNS: device must be **Bonded** in BlueZ; `port = ble://<MAC>` or
  `ble://RNode XXXX`; needs `bleak`; same `txpower >= 14` rule.

**Verified (live G3):** bond + RNS-over-BLE announce OK.

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
7. Optional WiFi: `rnodeconf --ssid … --psk … -w STATION`, then
   `port = tcp://<ip>` with `txpower >= 14`.
8. Optional BLE: `rnodeconf -b` / `-p`, bond on host, `port = ble://…`.
