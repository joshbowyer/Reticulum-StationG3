# Station G2 Support for rnodeconf.py
# ====================================
# 
# To add Station G2 support to rnodeconf.py, the following changes are needed:
#
# 1. Add ROM constants in the ROM class:
#    PRODUCT_STATION_G2  = 0x60
#    MODEL_62            = 0x62
#
# 2. Add to products dictionary:
#    ROM.PRODUCT_STATION_G2: "Station G2",
#
# 3. Add to models dictionary:
#    0x62: [902000000, 928000000, 30, "902 - 928 MHz", "rnode_firmware_station_g2.zip", "SX1262"],
#
# 4. Add autoinstall option (increment existing numbers by 1):
#    print("[17] Station G2")
#
# 5. Add autoinstall case handler:
#    elif c_dev == 17:
#        selected_product = ROM.PRODUCT_STATION_G2
#        selected_mcu = ROM.MCU_ESP32
#        selected_platform = ROM.PLATFORM_ESP32
#        selected_model = ROM.MODEL_62
#        fw_filename = "rnode_firmware_station_g2.zip"
#        # Add installation warning message
#
# 6. Add ESP32-S3 flasher support in get_flasher_call():
#    elif fw_filename == "rnode_firmware_station_g2.zip":
#        return [
#            sys.executable, flasher,
#            "--chip", "esp32s3",
#            "--port", args.port,
#            "--baud", args.baud_flash,
#            "--before", "default_reset",
#            "--after", "hard_reset",
#            "write_flash", "-z",
#            "--flash_mode", "dio",
#            "--flash_freq", "80m",
#            "--flash_size", "4MB",
#            "0xe000", UPD_DIR+"/"+selected_version+"/rnode_firmware_station_g2.boot_app0",
#            "0x0", UPD_DIR+"/"+selected_version+"/rnode_firmware_station_g2.bootloader",
#            "0x10000", UPD_DIR+"/"+selected_version+"/rnode_firmware_station_g2.bin",
#            "0x210000", UPD_DIR+"/"+selected_version+"/console_image.bin",
#            "0x8000", UPD_DIR+"/"+selected_version+"/rnode_firmware_station_g2.partitions",
#        ]
#
# The main issue is that rnodeconf doesn't recognize Station G2 as a valid product,
# so when the device reports PRODUCT_STATION_G2 (0x60) and MODEL_62 (0x62), 
# rnodeconf fails to identify it properly.
#
# After these changes are made to the upstream rnodeconf.py in the Reticulum 
# repository, Station G2 devices should work properly with the standard 
# rnodeconf tool.

# Current Status:
# - Station G2 firmware builds and uploads successfully
# - Device boots with upstream firmware
# - rnodeconf doesn't recognize the device (needs these patches)
# - Need to test actual radio functionality once rnodeconf works

# Testing Process:
# 1. Apply patches to local rnodeconf installation
# 2. Test device recognition: rnodeconf /dev/cu.usbmodem101 --info
# 3. Test provisioning if device is blank EEPROM
# 4. Test radio functionality and PA/LNA operation
# 5. Submit patches to upstream Reticulum repository