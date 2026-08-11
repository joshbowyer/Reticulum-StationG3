# Station G2 patches for rnodeconf.py
# This shows the additions needed to support Station G2 in rnodeconf

# In the ROM class, add these constants:
PRODUCT_STATION_G2  = 0x60  # Station G2 devices
MODEL_62            = 0x62  # Station G2, 915 MHz
MODEL_63            = 0x63  # Station G3, 915 MHz

# In the products dictionary, add:
products = {
    # ... existing products ...
    ROM.PRODUCT_STATION_G2: "Station G2",
    # ... rest of existing products ...
}

# In the models dictionary, add:
models = {
    # ... existing models ...
    0x62: [902000000, 928000000, 30, "902 - 928 MHz", "rnode_firmware_station_g2.zip", "SX1262"],
    0x63: [902000000, 928000000, 27, "902 - 928 MHz", "rnode_firmware_station_g3.zip", "SX1262"],
    # ... rest of existing models ...
}

# Station G2 specific details:
# - Frequency range: 902-928 MHz (US915 ISM band)
# - Max TX power: 30 dBm (with external PA)
# - Firmware filename: rnode_firmware_station_g2.zip
# - Radio chip: SX1262

# Station G3 specific details:
# - Frequency range: 902-928 MHz (US915 ISM band)
# - Max TX power: 27 dBm (conservative; BQ35LORA900V1M hardware supports up to 35dBm)
# - Firmware filename: rnode_firmware_station_g3.zip
# - Radio chip: SX1262

# In the autoinstall section, add Station G2 as option [17]:
print("[17] Station G2")

# Add case handler for Station G2:
elif c_dev == 17:
    selected_product = ROM.PRODUCT_STATION_G2
    selected_mcu = ROM.MCU_ESP32
    selected_platform = ROM.PLATFORM_ESP32
    selected_model = ROM.MODEL_62
    fw_filename = "rnode_firmware_station_g2.zip"
    clear()
    print("")
    print("-" * 75)
    print("                     Station G2 RNode Installer")
    print("")
    print("Important! Using RNode firmware on Station G2 devices should currently be")
    print("considered experimental. It is not intended for production or critical use.")
    print("The currently supplied firmware is provided AS-IS as a courtesy to those")
    print("who would like to experiment with it. Hit enter to continue.")
    print("-" * 75)
    input()

# In the autoinstall section, add Station G3 as option [18]:
print("[18] Station G3")

# Add case handler for Station G3:
elif c_dev == 18:
    selected_product = ROM.PRODUCT_STATION_G2  # G3 reuses the G2 product byte for now
    selected_mcu = ROM.MCU_ESP32
    selected_platform = ROM.PLATFORM_ESP32
    selected_model = ROM.MODEL_63
    fw_filename = "rnode_firmware_station_g3.zip"
    clear()
    print("")
    print("-" * 75)
    print("                     Station G3 RNode Installer")
    print("")
    print("Important! Using RNode firmware on Station G3 devices should currently be")
    print("considered experimental. It is not intended for production or critical use.")
    print("The currently supplied firmware is provided AS-IS as a courtesy to those")
    print("who would like to experiment with it. Hit enter to continue.")
    print("-" * 75)
    input()

# In get_flasher_call function, add Station G2 handling:
elif fw_filename == "rnode_firmware_station_g2.zip":
    return [
        sys.executable, flasher,
        "--chip", "esp32s3",
        "--port", args.port,
        "--baud", args.baud_flash,
        "--before", "default_reset",
        "--after", "hard_reset",
        "write_flash", "-z",
        "--flash_mode", "dio",
        "--flash_freq", "80m",
        "--flash_size", "4MB",
        "0xe000", UPD_DIR+"/"+selected_version+"/rnode_firmware_station_g2.boot_app0",
        "0x0", UPD_DIR+"/"+selected_version+"/rnode_firmware_station_g2.bootloader",
        "0x10000", UPD_DIR+"/"+selected_version+"/rnode_firmware_station_g2.bin",
        "0x210000", UPD_DIR+"/"+selected_version+"/console_image.bin",
        "0x8000", UPD_DIR+"/"+selected_version+"/rnode_firmware_station_g2.partitions",
    ]

# In get_flasher_call function, add Station G3 handling:
elif fw_filename == "rnode_firmware_station_g3.zip":
    return [
        sys.executable, flasher,
        "--chip", "esp32s3",
        "--port", args.port,
        "--baud", args.baud_flash,
        "--before", "default_reset",
        "--after", "hard_reset",
        "write_flash", "-z",
        "--flash_mode", "dio",
        "--flash_freq", "80m",
        "--flash_size", "4MB",
        "0xe000", UPD_DIR+"/"+selected_version+"/rnode_firmware_station_g3.boot_app0",
        "0x0", UPD_DIR+"/"+selected_version+"/rnode_firmware_station_g3.bootloader",
        "0x10000", UPD_DIR+"/"+selected_version+"/rnode_firmware_station_g3.bin",
        "0x210000", UPD_DIR+"/"+selected_version+"/console_image.bin",
        "0x8000", UPD_DIR+"/"+selected_version+"/rnode_firmware_station_g3.partitions",
    ]