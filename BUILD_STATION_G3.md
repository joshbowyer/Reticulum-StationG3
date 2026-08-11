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

LED GPIOs remain the G2 placeholder values (RX 9, TX 8), which conflict with the confirmed G3 PA GPIO assignment and must be checked on real hardware. LNA gain/GVT values are starting estimates and need calibration. TCXO/current-limit/OCP settings are carried over from G2 and require hardware verification. PA output is intentionally capped conservatively at 27 dBm final output with a 22 dBm host TX-power cap; no unverified gain curve is included.

Do not flash until the Station G3 hardware and these assumptions have been confirmed.
