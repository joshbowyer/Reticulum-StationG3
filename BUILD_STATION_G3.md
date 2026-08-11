# Building RNode Firmware for Station G3

This directory contains the Reticulum/RNS KISS+command protocol firmware port for the Station G3 ESP32-S3 + SX1262 board. It is based on the Station G2 firmware with Station G3 PA/LNA GPIO control.

## Status

ESP32-S3 firmware port in progress. PA/LNA GPIO additions are unverified on real hardware.

## Prerequisites

- `arduino-cli`
- ESP32 Core 2.0.17 (ESP32 Core 3.x can cause undefined-reference errors)
- Python 3

## Build environment

From `RNode_Firmware_StationG3/`, prepare the toolchain with:

```bash
make prep-esp32
```

The build uses the same Arduino CLI invocation as Station G2, with board model byte `0x62`:

```bash
make firmware-station_g3
```

Equivalent direct command:

```bash
arduino-cli compile --log --fqbn "esp32:esp32:esp32s3:CDCOnBoot=cdc" -e --build-property "build.partitions=no_ota" --build-property "upload.maximum_size=2097152" --build-property "compiler.cpp.extra_flags=\"-DBOARD_MODEL=0x62\""
```

The compiled firmware is written to `build/esp32.esp32.esp32s3/RNode_Firmware_StationG3.ino.bin`.

## Hardware verification items

LED GPIOs are unverified placeholders (RX 4, TX 3); GPIO4 is suspected to collide with a battery-ADC net and GPIO3 is an ESP32-S3 strapping pin (per vendor recon doc). LED function bodies are no-ops in Utilities.h for G3 until real LED pins are confirmed from the schematic/pinout tool. LNA gain/GVT values are starting estimates and need calibration. TCXO/current-limit/OCP settings are carried over from G2 and require hardware verification. PA output is intentionally capped conservatively at 27 dBm final output with a 22 dBm host TX-power cap. The flat `+20 dB` PA gain curve is a vendor-corroborated estimate (chip-level `LORA_TX_POWER=7` → ~27 dBm final output per recon doc); replace with a real measured curve once conducted-power testing is done.

### Bring-up checklist (pre-flash)

1. **Verify PA PL1 / LNA P jumpers are OPEN.** Per the BQ pinout, `P_PA1_EN` (GPIO9) and `P_PRIMARY_LNA_EN` (GPIO10) share the same net as the physical PA PL1 and LNA P motherboard jumpers respectively. If either jumper is shorted/closed, it will override the GPIO software control (LOW/open = "low/no-jumper" state, HIGH/short = "high/jumpered" state). For software GPIO control to work, both jumpers must be left OPEN.
2. **Install ≥0.5 m of coax between the SMA port and the antenna** before any power-calibration testing above ~2 W. Above ~2 W RF output, third-party MCU daughterboards can suffer false over-voltage-protection trips from near-field coupling near the SMA connector (see HARDWARE-RECON.md).
3. **Confirm PRODUCT byte = 0x60 (PRODUCT_STATION_G2)** and **MODEL byte = 0x63 (MODEL_63)** when provisioning with `rnodeconf`. The G3 board reuses G2's PRODUCT byte for now but uses its own distinct MODEL byte.

Do not flash until the Station G3 hardware and these assumptions have been confirmed.
