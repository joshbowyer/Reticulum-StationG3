# 20 — BQ/Uniteng Station G3: Hardware Recon (pre-arrival)

Status: pure recon, hardware not yet in hand. Captured before starting
`Reticulum-StationG3` firmware/software work so nothing gets lost. Rep
confirmed **G3 is fully firmware-compatible with G2 at the core LoRa/SPI
level** — verified independently below.

Sources: https://wiki.bqvoy.com/en/devkits/station-g3 (full page HTML
captured to `/tmp/station-g3.html` during recon), rep-provided
`lna_control.sh`/`pa_control.sh` scripts, and a MeshCore firmware commit
that already ports Station G3 support (found via web search — not an
official BQ source, but a real working reference implementation):
https://git.pblr-nyk.pro/mirror/MeshCore/commit/f4be34a99706820a408a34af3b03dd645ac00bd0

## Board architecture

- Motherboard has 3 sockets:
  1. **MCU Daughterboard Socket** — standard Raspberry Pi compatible
     40-pin GPIO header. Officially tested: **BQESP32V1M** (official ESP32-S3
     board) and **Raspberry Pi Zero 2W** (third-party, Linux-native path).
  2. **Primary Slot for RF Daughterboard** — populated by default with the
     **BQ35LORA900V1M** module.
  3. **Secondary Slot for RF Daughterboard** — unpopulated by default.
- RF daughterboard (BQ35LORA900V1M): 850-930MHz band, SX1262 transceiver,
  up to 35dBm PA for TX, LNA with dynamic gain control + impedance matching
  for RX (~5dB adjustable gain range — can saturate in high-noise
  environments; software LNA disable is offered as an alternative to a
  cavity filter).
- Config controlled via 5 motherboard jumpers: PA PL1, PA PL2, LNA P (LNA
  S and EEPROM reserved, not installed by default). PA PL1/LNA P can
  alternatively be controlled entirely via GPIO/software instead of
  physical jumpers (see below) — **this is Station G3's actual new
  feature over G2**, which only has physical jumper control.

### CONFIRMED via official vendor spec page (retrieved directly from the
### user, since the wiki page blocks automated/LLM fetches): PA PL1/PL2
### are NOT independent switches — they're a 2-bit combined level select:

| PL1 | PL2 | PA Operating Mode | Notes |
|---|---|---|---|
| OPEN | OPEN | **Power Level 1** | Default recommended setting. Lowest PA output + lowest power consumption. Min supply 9VDC. |
| OPEN | SHORT | Power Level 2 | Higher than L1. Min supply 9VDC. |
| SHORT | OPEN | Power Level 3 | Higher than L2. Min supply 9VDC. |
| SHORT | SHORT | Power Level 4 (**Boost**) | Highest PA output + highest consumption. Min supply **10VDC**. |

OPEN = jumper NOT installed. SHORT = jumper installed. **There is no GPIO
override for PL2 at all** (confirmed — MeshCore's real shipped G3 config
only defines a GPIO for PL1, nothing for PL2) — PL2 can ONLY be set via
the physical jumper. This means **both** PA-PL1 and PA-PL2 must be
physically OPENED to reach the safe default Level 1; opening only PL1
while PL2 stays shorted lands on Level 3, not Level 1.

**Official conducted-power test table for Power Level 1** (BW 125kHz,
SF12, CR4/5, Sync 0xFF, 150-char payload; ±2dB accuracy per SX1262
datasheet spec, ±1dB statistical from BQ's own QC):

| SX1262 TX Setting (dBm) | PA Output @915MHz (dBm) | Real gain (dB) |
|---|---|---|
| 2 | 16.6 | 14.6 |
| 3 | 17.6 | 14.6 |
| 4 | 18.7 | 14.7 |
| 5 | 19.7 | 14.7 |
| 6 | 20.7 | 14.7 |
| 7 | 21.7 | 14.7 |
| 8 | 22.6 | 14.6 |
| 9 | 23.6 | 14.6 |
| 10 | 24.4 | 14.4 |
| 11 | 25.3 | 14.3 |
| 12 | 26.1 | 14.1 |
| 13 | 26.9 | 13.9 |
| 14 | 27.7 | 13.7 |
| 15 | 28.4 | 13.4 |
| 16 | 29.2 | 13.2 |
| 17 | 29.8 | 12.8 |
| 18 | 30.5 | 12.5 |
| 19 | 31.1 | 12.1 |
| 20 | 31.7 | 11.7 |
| 21 | 32.3 | 11.3 |
| 22 | 32.8 | 10.8 |

Real gain at Level 1 DECLINES from ~14.7dB (low drive) to ~10.8dB (max
drive) — NOT flat, and notably lower than the flat-20dB placeholder our
firmware initially used (which was likely calibrated against a *different*
PA level, since MeshCore's own "chip TX=7→~27dBm final" data point does
not match this table's TX=7→21.7dBm at Level 1 at all). No vendor data
exists yet for Levels 2-4.

**Typical power consumption** (ESP32S3-BQ35LORA900V1M, Level 1): RX
0.560W, TX 6.330W. RX dominates in most mesh use (TX airtime << RX time).

**LNA P jumper** (single bit, confirmed unchanged from earlier recon):
OPEN=LNA ON (external LNA w/ dynamic gain+impedance matching enabled,
~5dB RX dynamic-range improvement over G2), SHORT=LNA OFF (useful in
high-noise environments). GPIO10 (`P_PRIMARY_LNA_EN`) does have a real
software override for this one.

**Power/safety warnings from the vendor spec** (Step 3 — Power the
Device):
- **"Operation without an antenna may permanently damage the device."**
  Always have an antenna (or dummy load) connected before powering on.
- Peak input voltage must NOT exceed 19VDC (barrel jack 9-19VDC, ≥25W
  rated, OR USB-C 15VDC PD — note plain 5V USB-C does NOT meet the
  minimum 9VDC requirement for ANY PA level, so the daughterboard's own
  USB-C port is comms-only, never power, by design).
- Level 4 (Boost) specifically requires ≥10VDC and ≥25W supply.
- **Power Good Checker**: press the PG button, all 4 LEDs (D2-D5) must
  light simultaneously for the board to be within operating spec — D2
  MCU-daughterboard 3.3V, D3 Grove-I2C/GPS 3.3V, D4 motherboard 5.0V, D5
  LoRa-PA fast-transient DC-DC. Check this before/during bring-up.
- **Hardware warning worth heeding from day one**: above ~2W RF output,
  third-party MCU daughterboards can suffer FALSE over-voltage-protection
  trips from near-field coupling near the SMA connector (some third-party
  boards use high-impedance op-amps for power-sense voltage sampling that
  are sensitive to this). Not permanent damage, but causes confusing
  random shutdowns requiring a full power cycle. **Mitigation: install at
  least 0.5m of coax between the Station G3's SMA port and the antenna**
  before doing any bring-up testing above ~2W.

## G2/G3 firmware compatibility — confirmed

Station G2's known pinout (ESP32-S3, SX1262): SCLK=GPIO12, MISO=GPIO14,
MOSI=GPIO13, NSS=GPIO11, DIO1=GPIO48, RESET=GPIO21, BUSY=GPIO47 —
**identical** to G3's ESP32-S3 pinout below. Confirms the rep's claim: the
core LoRa/SPI wiring didn't change between G2 and G3. **G3's actual
addition is the software-controllable PA1/LNA enable GPIOs** — G2 only has
physical jumpers for this.

## Complete pin maps (both daughterboard options)

### Option A: ESP32-S3 (BQESP32V1M) daughterboard

Bare-metal firmware path (Arduino/ESP-IDF style — same category as our
RAK4631 firmware work). Confirmed via the MeshCore board port
(`variants/station_g3_esp32`):

```
P_LORA_SCLK      = GPIO12
P_LORA_MISO      = GPIO14
P_LORA_MOSI      = GPIO13
P_LORA_NSS       = GPIO11   (SPI chip-select)
P_LORA_DIO_1     = GPIO48
P_LORA_RESET     = GPIO21
P_LORA_BUSY      = GPIO47

P_PA1_EN         = GPIO9    ; PA PL1 mode. LOW/open=PA low, HIGH/short=PA high.
P_PA1_EN_ACTIVE  = HIGH
P_PRIMARY_LNA_EN = GPIO10   ; Primary Slot LNA mode. LOW/open=LNA on, HIGH/short=LNA off.
P_PRIMARY_LNA_EN_ACTIVE = LOW

PIN_BOARD_SDA    = GPIO5
PIN_BOARD_SCL    = GPIO6
PIN_USER_BTN     = GPIO38
PIN_GPS_RX       = GPIO15
PIN_GPS_TX       = GPIO7

SX126X_DIO2_AS_RF_SWITCH = true
SX126X_DIO3_TCXO_VOLTAGE = 1.8
SX126X_CURRENT_LIMIT     = 140
SX126X_RX_BOOSTED_GAIN   = 0
LORA_TX_POWER    = 7        ; chip-level setting -> ~27dBm/0.5W final output after PA
MAX_LORA_TX_POWER = 22
```

Note: `P_PA1_EN`/`P_PRIMARY_LNA_EN` "LOW/open, HIGH/short" phrasing
describes jumper-equivalent logic — matches the rep's own physical-header
description ("pin 11 PA Mode, pin 16 LNA Mode") once translated through
the RPi-header-pin numbering below; the ESP32 daughterboard's own GPIO9/10
are the *actual chip pins* that get wired to those same physical header
positions on this specific daughterboard.

### Option B: Raspberry Pi Zero 2W daughterboard (Linux-native path)

Confirmed via BQ's own `meshtasticd` YAML config example
(`lora-BQ-SG3-BQ35LORA900V1M-PrimarySlot.yaml`) plus the rep's
`lna_control.sh`/`pa_control.sh` scripts and a live `pinctrl get 7-25`
dump from BQ's own test rig:

```
SPI bus       = hardware SPI0, /dev/spidev0.0
MISO/MOSI/SCLK = GPIO9/10/11   (standard RPi SPI0 pins)
CS            = GPIO8          (default, often left to spidev automatically)
RESET         = GPIO16
BUSY          = GPIO24
DIO1 / IRQ    = GPIO22
DIO2_AS_RF_SWITCH = true
DIO3_TCXO_VOLTAGE = true (voltage unspecified in the yaml snippet - assume
                           1.8V, matching the ESP32-side RF module spec,
                           since it's the same BQ35LORA900V1M module)

PA enable   = GPIO17  (physical header pin 11) - gpiochip0, gpioset,
              ACTIVE-HIGH for PA-high (script: PAHIGH -> gpioset ...=1)
LNA enable  = GPIO23  (physical header pin 16) - gpiochip0, gpioset,
              ACTIVE-LOW for LNA-on (script: LNAON -> gpioset ...=0)

GPIO18-21 reserved for the Secondary RF Slot (unused in standard config;
GPIO19-21 line up with hardware SPI1 - MISO/MOSI/SCLK - if the secondary
slot is ever populated).
```

Boot config requirements (`/boot/firmware/config.txt`):
```ini
dtparam=i2c_arm=on
dtoverlay=spi0-1cs
dtoverlay=spi1-1cs
```

I2C for optional sensors/displays: `/dev/i2c-1`. The `meshtasticd` example
config references an `INA219_MULTIPLIER` setting — suggests the board (or
a commonly-paired accessory) may expose an **INA219** power monitor on
I2C, different from the RAK4631's INA3221 used elsewhere in this project.
Worth confirming once hardware is in hand.

Rep-provided verbatim scripts (both use `gpiochip0`/`gpioset`, i.e.
`libgpiod` — meaning this is specifically the Linux/RPi daughterboard
path, not applicable to the bare-metal ESP32 path):

```bash
#!/bin/bash
# lna_control.sh
GPIO_CHIP="gpiochip0"
GPIO_PIN=23
case "$1" in
  LNAON)  echo "LNA ON";  gpioset ${GPIO_CHIP} ${GPIO_PIN}=0 ;;
  LNAOFF) echo "LNA OFF"; gpioset ${GPIO_CHIP} ${GPIO_PIN}=1 ;;
  *) echo "Usage: $0 {LNAON|LNAOFF}"; exit 1 ;;
esac
```
```bash
#!/bin/bash
# pa_control.sh
GPIO_CHIP="gpiochip0"
GPIO_PIN=17
case "$1" in
  PALOW)  echo "PA LOW LEVEL";  gpioset ${GPIO_CHIP} ${GPIO_PIN}=0 ;;
  PAHIGH) echo "PA HIGH LEVEL"; gpioset ${GPIO_CHIP} ${GPIO_PIN}=1 ;;
  *) echo "Usage: $0 {PAON|PAOFF}"; exit 1 ;;
esac
```

Full `pinctrl get 7-25` reference dump from BQ's own working test rig
(all pins not otherwise claimed show their idle boot-time state):
```
7: input   (unclaimed)
8: output  (SPI0 CE0)
9: SPI0_MISO
10: SPI0_MOSI
11: SPI0_SCLK
12-17: input (idle; 16=RESET and 17=PA_EN once claimed by software)
18: output  (secondary slot related)
19-21: SPI1 (MISO/MOSI/SCLK) - secondary slot, unused by default
22: input (idle; = DIO1/IRQ once claimed)
23: input (idle; = LNA_EN once claimed)
24: input (idle; = BUSY once claimed)
25: input (unclaimed)
```

## Notable connection: Lyra Zero W as a potential G3 MCU daughterboard

BQ's own wiki explicitly calls out the **mPWRD-OS** project (Armbian +
Meshtastic, https://github.com/mPWRD-OS/mPWRD-OS) as supporting a wider
range of Linux daughterboards including the **Luckfox Lyra Zero W** — the
exact board this project has already built a full Reticulum stack for
(gold-image, `reticulum-mesh.service`, I2P, etc. — see docs 15-19).

Since Lyra's own 40-pin header already has a Pi-compatible pinmux overlay
(`lyra-gold-image/dts-overlay/`, built earlier this session), there's a
real chance Lyra could plug directly into the Station G3 motherboard as
its MCU daughterboard, letting us reuse the existing Lyra Reticulum stack
directly instead of building new embedded firmware. **Worth checking pin
compatibility once hardware physically arrives** — not yet verified.

(Aside, for context continuity: the user is directly involved in the
mPWRD-OS/Lyra work alongside `vidplace7` — this Station G3 investigation
isn't happening in isolation from that.)

## Open items to confirm once hardware arrives

- Exact `DIO3_TCXO_VOLTAGE` value for the RPi path (assumed 1.8V by
  analogy with the ESP32 side's confirmed spec — not independently
  verified for the RPi config).
- Whether an INA219 power monitor is actually present/wired (inferred
  from the `meshtasticd` example config referencing `INA219_MULTIPLIER`,
  not explicitly confirmed elsewhere on the wiki).
- Battery-voltage ADC pin, if any (G2 uses ESP32 GPIO4 for this — not yet
  confirmed for G3 on either daughterboard path).
- Full 40-pin header table beyond what's captured here (the interactive
  pinout tool at tools.bqvoy.com is a JS-rendered SPA that didn't extract
  cleanly via automated fetch — screenshot capture attempted but not yet
  successfully retrieved).
- Physical/mechanical fit check for Lyra Zero W as an MCU daughterboard
  (mPWRD-OS compatibility claim, not yet hands-on verified).

## Next step

Firmware/software work starts in a new repo: `Reticulum-StationG3`
(GitHub + Lyra rngit mirror, both to be created next).
