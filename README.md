# Reticulum-StationG3

Reticulum firmware/software for the BQ/Uniteng Station G3 mesh radio devkit.

Station G3 supports two MCU daughterboard options on its Raspberry Pi
compatible 40-pin header:
- **BQESP32V1M** (official ESP32-S3 board) — bare-metal firmware path.
- **Raspberry Pi Zero 2W** (third-party) — Linux-native path.

See [`HARDWARE-RECON.md`](./HARDWARE-RECON.md) for the full pre-arrival
hardware recon: pin maps for both daughterboard options, PA/LNA control
details, and known hardware gotchas.

Status: **Hardware-verified on a live Station G3** (ESP32-S3 / BQESP32V1M
daughterboard, PA Level 1). SPI radio, SH1106 OLED, EEPROM provisioning,
KISS/RNS bring-up, and a TX power ladder (2→32 dBm) with peer RSSI
correlation have all been confirmed working. See `BUILD_STATION_G3.md` for
the full verified-facts list.

The `RNode_Firmware_StationG3/` directory contains the Arduino CLI-buildable Reticulum/RNS KISS+command protocol firmware. Build instructions are in [`BUILD_STATION_G3.md`](./BUILD_STATION_G3.md); the firmware target uses board-model byte `0x62`. This is not a MeshCore protocol implementation.

## Hardware prerequisites before powering on

Station G3's PA/LNA path is controlled by **physical motherboard jumpers**
(PA-PL1, PA-PL2, LNA-P). This firmware's PA gain curve is calibrated for
**PA Operating Level 1 only**:

- **PA-PL1 jumper: OPEN (not installed)**
- **PA-PL2 jumper: OPEN (not installed)**
- **LNA-P jumper: OPEN (not installed)**
- Antenna or dummy load connected **before** powering on — never key the
  radio with an open RF path.
- Barrel PSU 9–19 VDC is sufficient for Level 1 (Level 4 Boost needs ≥10 VDC).

Other jumper combinations select PA Levels 2–4, which use different gain
curves that this firmware does **not** currently calibrate for — see
[`HARDWARE-RECON.md`](./HARDWARE-RECON.md) for the full jumper matrix and
vendor conducted-power table.

This repo is **ESP32 RNode firmware only**. The Raspberry Pi Zero 2W /
Lyra-class host-driver path lives separately in `reticulum-hat-mod` as a
`radio_board` profile.

## Host paths (USB / WiFi / BLE)

Three ways to run RNS against the ESP32 G3 RNode. Mesh params and
`txpower` rules are the same on all three.

### USB serial (default)

```
port = /dev/ttyACM0
```

### WiFi STA → TCP KISS (port 7633)

Configure once over USB, then use the LAN IP:

```bash
rnodeconf /dev/ttyACM0 \
  --ssid "YourSSID" \
  --psk 'YourPSK' \
  -w STATION
# rnodeconf -i  → note the DHCP IP (e.g. 10.0.0.57)
```

RNS config (bare host, **no** `:7633` — RNS `TCPConnection` hardcodes port 7633):

```
type = RNodeInterface
port = tcp://10.0.0.57
frequency = 915000000
bandwidth = 125000
txpower = 14
spreadingfactor = 7
codingrate = 5
```

- `txpower` must be **≥ 14** on G3 (PA gain floor). Lower values make the
  radio rewrite reported TX power and RNS `validateRadioState` fails.
- After the WiFi TCP RX drain fix in this firmware, RNS can burst-init over
  TCP without host-side pacing. Older builds may need ~150–200 ms gaps
  between KISS set commands.
- After every flash: `rnodeconf -L` then `-H <hash>` and reboot — target ≠
  actual leaves `hw_ready` false (radio stays OFF even if params echo OK).

### BLE (Nordic UART)

```bash
rnodeconf /dev/ttyACM0 -b    # enable BT in EEPROM
rnodeconf /dev/ttyACM0 -p    # pair mode (interactive; enter PIN on host)
```

Device advertises as `RNode XXXX` (BLE MAC = WiFi MAC + 1). RNS needs the
device **bonded** in BlueZ (`bleak` required in the Python env):

```
port = ble://98:A3:16:CE:CC:D5
# or: ble://RNode 0C65
txpower = 14
```

Same `txpower ≥ 14` rule as WiFi. Pairing uses a static 6-digit passkey
shown on the OLED / KISS `CMD_BT_PIN` while in pair mode.

See `BUILD_STATION_G3.md` for full verified facts and bring-up checklist.
