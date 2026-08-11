# Reticulum-StationG3

Reticulum firmware/software for the BQ/Uniteng Station G3 mesh radio devkit.

Station G3 supports two MCU daughterboard options on its Raspberry Pi
compatible 40-pin header:
- **BQESP32V1M** (official ESP32-S3 board) — bare-metal firmware path.
- **Raspberry Pi Zero 2W** (third-party) — Linux-native path.

See [`HARDWARE-RECON.md`](./HARDWARE-RECON.md) for the full pre-arrival
hardware recon: pin maps for both daughterboard options, PA/LNA control
details, and known hardware gotchas.

Status: ESP32-S3 firmware port in progress, based on Station G2 RNode firmware + Station G3 PA/LNA GPIO additions (unverified on real hardware yet).

The `RNode_Firmware_StationG3/` directory contains the Arduino CLI-buildable Reticulum/RNS KISS+command protocol firmware. Build instructions are in [`BUILD_STATION_G3.md`](./BUILD_STATION_G3.md); the firmware target uses board-model byte `0x62`. This is not a MeshCore protocol implementation.
