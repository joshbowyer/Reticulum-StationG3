#!/usr/bin/env python3
"""
Configure WiFi on RNode devices with HAS_WIFI (e.g. Station G2).
Sends KISS commands to set SSID, password, and enable STA mode.
Usage: python3 configure_wifi.py /dev/ttyACM0 "MySSID" "MyPassword"
"""

import sys
import time
import serial

FEND = 0xC0
FESC = 0xDB
TFEND = 0xDC
TFESC = 0xDD

CMD_WIFI_MODE = 0x6A
CMD_WIFI_SSID = 0x6B
CMD_WIFI_PSK = 0x6C

WR_WIFI_OFF = 0x00
WR_WIFI_STA = 0x01  # Connect to existing network
WR_WIFI_AP = 0x02   # Create hotspot


def escape(data: bytes) -> bytes:
    data = data.replace(bytes([FESC]), bytes([FESC, TFESC]))
    data = data.replace(bytes([FEND]), bytes([FESC, TFEND]))
    return data


def send_kiss_wifi(ser: serial.Serial, cmd: int, data: bytes) -> None:
    """Send a KISS WiFi command. Data is null-terminated for SSID/PSK."""
    frame = bytes([FEND, cmd]) + escape(data) + bytes([FEND])
    ser.write(frame)
    time.sleep(0.05)


def configure_wifi(port: str, ssid: str, password: str, mode: int = WR_WIFI_STA) -> bool:
    if len(ssid) > 32:
        print("SSID must be 32 characters or fewer")
        return False
    if len(password) > 32:
        print("Password must be 32 characters or fewer")
        return False

    try:
        ser = serial.Serial(port, 115200, timeout=2)
    except serial.SerialException as e:
        print(f"Failed to open {port}: {e}")
        return False

    print("Configuring WiFi...")
    time.sleep(0.5)

    # 1. Set SSID (null-terminated; firmware pads to 32 bytes)
    ssid_data = ssid.encode("utf-8") + b"\x00"
    send_kiss_wifi(ser, CMD_WIFI_SSID, ssid_data)
    print(f"  SSID set: {ssid}")

    # 2. Set password (null-terminated; firmware pads to 32 bytes)
    psk_data = password.encode("utf-8") + b"\x00"
    send_kiss_wifi(ser, CMD_WIFI_PSK, psk_data)
    print("  Password set")

    # 3. Enable STA mode (connect to network)
    send_kiss_wifi(ser, CMD_WIFI_MODE, bytes([mode]))
    mode_name = "STA (connect to network)" if mode == WR_WIFI_STA else "AP (hotspot)" if mode == WR_WIFI_AP else "off"
    print(f"  WiFi mode: {mode_name}")

    ser.close()
    print("\nDone. The RNode will connect to your network.")
    print("Check the display for the assigned IP, or use rnodeconf -i after reconnecting.")
    return True


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        print("Arguments: PORT SSID PASSWORD")
        print('Example:   python3 configure_wifi.py /dev/ttyACM0 "MyNetwork" "MySecretPass"')
        sys.exit(1)

    port = sys.argv[1]
    ssid = sys.argv[2]
    password = sys.argv[3]

    if not configure_wifi(port, ssid, password):
        sys.exit(1)


if __name__ == "__main__":
    main()
