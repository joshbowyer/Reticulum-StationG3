# Building RNode Firmware for Station G3

This directory contains the Reticulum/RNS KISS+command protocol firmware port for the Station G3 ESP32-S3 + SX1262 board. It is based on the Station G2 firmware with Station G3 PA/LNA GPIO control.

## Status

ESP32-S3 firmware port in progress. PA/LNA GPIO additions and the Level-1
PA gain curve are sourced from the vendor's official spec (see
`HARDWARE-RECON.md`); full hardware verification still pending on a real
board.

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

LED GPIOs are unverified placeholders (RX 4, TX 3); GPIO4 is suspected to collide with a battery-ADC net and GPIO3 is an ESP32-S3 strapping pin (per vendor recon doc). LED function bodies are no-ops in Utilities.h for G3 until real LED pins are confirmed from the schematic/pinout tool. LNA gain/GVT values are starting estimates and need calibration. TCXO/current-limit/OCP settings are carried over from G2 and require hardware verification.

The PA gain curve in `Boards.h` (`PA_GAIN_VALUES`) and `PA_MAX_OUTPUT=32`
are now derived from the vendor's OFFICIAL conducted-power test table for
PA Operating Level 1 (PA-PL1 and PA-PL2 jumpers both OPEN, see
`HARDWARE-RECON.md` for the source table). The previous flat-20 dB
placeholder and `PA_MAX_OUTPUT=27` were interim conservative values
before real vendor data was available; they are superseded.

## Bring-up checklist (pre-flash)

1. **Open PA-PL1, PA-PL2, and LNA-P jumpers on the motherboard.** These
   are the three jumpers the firmware actually relies on the operator to
   set physically. Per the BQ/Uniteng vendor spec (see `HARDWARE-RECON.md`):
   - **PA-PL1 and PA-PL2** are a 2-bit combined PA Operating Level select,
     NOT independent switches. **Both must be physically OPEN** to reach
     Level 1 (the vendor-recommended safe default this firmware is
     calibrated for). Opening only PL1 while PL2 stays shorted lands on
     Level 3, not Level 1. GPIO9 (`pin_pa1_en`) is the software override
     for PL1 only — there is **no software override for PL2 at all**, so
     PL2 must be set via its physical jumper alongside PL1.
   - **LNA-P**: OPEN = LNA on (with dynamic gain + impedance matching);
     GPIO10 (`pin_lna_en`) provides software override.
   - **LNA-S** and **EEPROM** jumpers are unrelated/reserved; leave them
     as shipped (not installed by default).
   The PA gain curve in `Boards.h` is ONLY valid at Level 1 (both PA
   jumpers OPEN). If a future firmware user sets PL2 to SHORT (Levels
   2/3/4) the curve would be wrong for that configuration — there's no
   software detection of jumper state, so this is a hard physical
   configuration assumption.
2. **Power safety from the vendor spec** (Step 3 — Power the Device):
   - **Never power on without an antenna or dummy load connected** —
     vendor states this can permanently damage the device.
   - Barrel-jack PSU must supply **9-19 VDC** for Levels 1-3 (≥10 VDC
     specifically required for Level 4 / Boost; not relevant at Level 1
     but worth noting for future reference), ≥25 W rated. A plain
     **5 V USB-C connection does NOT meet the 9 VDC minimum for any PA
     level** — by vendor design the MCU daughterboard's own USB-C port is
     comms-only, never power. Power comes from the motherboard's 40-pin
     header.
   - **Power Good Checker**: press the PG button, confirm all 4 LEDs
     (D2-D5) light simultaneously — D2 MCU-daughterboard 3.3 V, D3
     Grove-I2C/GPS 3.3 V, D4 motherboard 5.0 V, D5 LoRa-PA fast-transient
     DC-DC. All four must be on for the board to be within operating
     spec.
3. **Install ≥0.5 m of coax between the SMA port and the antenna** before
   any power-calibration testing above ~2 W. Above ~2 W RF output,
   third-party MCU daughterboards can suffer false over-voltage-protection
   trips from near-field coupling near the SMA connector (see
   `HARDWARE-RECON.md`).
4. **Confirm PRODUCT byte = 0x60 (PRODUCT_STATION_G2)** and **MODEL byte =
   0x63 (MODEL_63)** when provisioning with `rnodeconf`. The G3 board
   reuses G2's PRODUCT byte for now but uses its own distinct MODEL byte.

Do not flash until the Station G3 hardware and these assumptions have been confirmed.
