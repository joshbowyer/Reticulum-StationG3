# Building RNode Firmware for Station G2

This document describes how to build and flash RNode firmware for the Station G2 LoRa base station.

## Prerequisites

- **arduino-cli** (or Arduino IDE with ESP32 board support)
- **ESP32 Core 2.0.15–2.0.17** (critical: 3.x causes `undefined reference` errors)
- **Python 3** (for esptool)

## Build Environment Setup

1. **Install arduino-cli** (if not already installed):
   ```bash
   curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
   ```

2. **Prepare ESP32 toolchain** (uses ESP32 Core 2.0.17):

   Note: The unsigned.io board index URL in `arduino-cli.yaml` may return 404 and is commented out. This does not affect Station G2 builds.
   ```bash
   make prep-esp32
   ```

3. **Verify build** with an existing target first:
   ```bash
   make firmware-tbeam_supreme
   ```

## Building Station G2 Firmware

```bash
make firmware-station_g2
```

The compiled firmware will be in `build/esp32.esp32.esp32s3/RNode_Firmware_CE_G2.ino.bin`.

## Flashing

**Option A: Full upload (firmware + console + rnodeconf provisioning)**
```bash
make firmware-station_g2
make console-site spiffs-image
make upload-station_g2 DEVICE_PORT=/dev/ttyACM0
```

Override `DEVICE_PORT` for your system (e.g. `/dev/ttyUSB0` on Linux, `/dev/cu.usbmodem*` on macOS).

**Option B: Firmware only**
```bash
arduino-cli upload -p /dev/ttyACM0 --fqbn esp32:esp32:esp32s3
```

## rnodeconf Integration

rnodeconf does not yet recognize Station G2 out-of-the-box. Apply the patch:

```bash
cd RNode_Firmware_CE_G2   # or pass the full path to the script
python3 patch_rnodeconf_g2.py
```

The script imports `RNS`; if `python3` is not the same environment as `pipx install rns`, use that venv’s interpreter (e.g. `~/.local/share/pipx/venvs/rns/bin/python patch_rnodeconf_g2.py`). See the repo root [README.md](../README.md) section **Host-side patches**.

See [STATION_G2_RNODECONF_CHANGES.md](STATION_G2_RNODECONF_CHANGES.md) for manual steps.

## Provisioning Blank EEPROM

When the device has valid firmware but **blank or invalid EEPROM**, `rnodeconf -i` will fail with "EEPROM is invalid". Use **ROM bootstrap** instead:

1. **Create signing key** (only needed once, if you have no key yet):
   ```bash
   rnodeconf -k
   ```

2. **Bootstrap EEPROM** (use `-r`, not `-i`):
   ```bash
   rnodeconf /dev/ttyACM0 -r --product 60 --model 62 --hwrev 1
   ```
   - `-r` / `--rom`: Bootstrap EEPROM without flashing firmware  
   - `--product 60`: Station G2 (hex 0x60)  
   - `--model 62`: Model 0x62 (902–928 MHz, 37 dBm)  
   - `--hwrev 1`: Hardware revision (required; 1–255)

3. **Verify** after provisioning:
   ```bash
   rnodeconf /dev/ttyACM0 -i
   ```

Replace `/dev/ttyACM0` with your port (e.g. `/dev/ttyUSB0` on Linux, `/dev/cu.usbmodem*` on macOS).

## WiFi Configuration

Station G2 has WiFi and can connect to your network for remote serial access (TCP port 7633). rnodeconf does not support WiFi; use the helper script:

```bash
cd /home/kraven/applications/g2_rnode/RNode_Firmware_CE_G2
python3 configure_wifi.py /dev/ttyACM0 "YourSSID" "YourPassword"
```

- Ensure the RNode is connected via USB and not in use by another program.
- Replace `/dev/ttyACM0` with your port.
- After configuration, the device connects at boot. The display cycles and may show the assigned IP.
- Connect remotely via TCP to the RNode’s IP on port **7633** (KISS over TCP).

Optional static IP: the script can be extended to send `CMD_WIFI_IP` and `CMD_WIFI_NM` for fixed addressing.

## Validation with rnsd

1. Provision the device (see [Provisioning Blank EEPROM](#provisioning-blank-eeprom) if EEPROM was blank)
2. Configure Reticulum to use the RNode interface
3. Start rnsd and check for "Radio state mismatch" – if present, see [Reticulum Discussion #558](https://github.com/markqvist/Reticulum/discussions/558)

## Station G2 Pin Mapping (from Meshtastic variant)

| Function        | GPIO |
|-----------------|------|
| SX1262 SPI SCK  | 12   |
| SX1262 SPI MISO | 14   |
| SX1262 SPI MOSI | 13   |
| SX1262 SPI CS   | 11   |
| SX1262 Reset    | 21   |
| SX1262 Busy     | 47   |
| SX1262 DIO1     | 48   |
| I2C SDA (Display)| 5   |
| I2C SCL (Display)| 6   |
| TX LED          | 8    |
| RX LED          | 9    |
| User Button     | 38   |

## References

- [RNode Firmware for Station G2](../RNode%20Firmware%20for%20Station%20G2.md)
- [Reticulum Discussion #558](https://github.com/markqvist/Reticulum/discussions/558)
- [Unit Engineering Station G2 Wiki](https://wiki.uniteng.com/en/meshtastic/station-g2)
