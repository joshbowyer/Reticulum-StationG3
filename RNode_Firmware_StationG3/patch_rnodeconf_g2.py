#!/usr/bin/env python3
"""
Patch script to add Station G2 support to locally installed rnodeconf
This modifies the installed rnodeconf.py to recognize Station G2 devices
"""

import os
import sys


def patch_rnodeconf():
    """Add Station G2 support to the installed rnodeconf module"""
    try:
        # Try to import RNS to get the rnodeconf path
        import RNS.Utilities.rnodeconf as rnodeconf_module

        rnodeconf_path = rnodeconf_module.__file__

        print(f"Found rnodeconf at: {rnodeconf_path}")

        # Read the current file
        with open(rnodeconf_path, "r") as f:
            content = f.read()

        # Check if Station G2 is already added
        if "PRODUCT_STATION_G2" in content:
            print("Station G2 support already present in rnodeconf")
            return True

        # Make backup
        backup_path = rnodeconf_path + ".backup"
        with open(backup_path, "w") as f:
            f.write(content)
        print(f"Created backup at: {backup_path}")

        # Apply patches

        # 1. Add ROM constants after existing products
        product_insertion_point = "PRODUCT_XIAO_S3     = 0xEB"
        if product_insertion_point in content:
            content = content.replace(
                product_insertion_point,
                product_insertion_point + "\n    PRODUCT_STATION_G2  = 0x60",
            )

        # Add model constant after existing models
        model_insertion_point = (
            "MODEL_DD            = 0xDD # Xiao ESP32S3 with Wio-SX1262 module, 868 MHz"
        )
        if model_insertion_point in content:
            content = content.replace(
                model_insertion_point,
                model_insertion_point + "\n    MODEL_62            = 0x62",
            )

        # 2. Add to products dictionary
        products_insertion_point = (
            'ROM.PRODUCT_XIAO_S3: "Seeed XIAO ESP32S3 Wio-SX1262",'
        )
        if products_insertion_point in content:
            content = content.replace(
                products_insertion_point,
                products_insertion_point
                + '\n    ROM.PRODUCT_STATION_G2: "Station G2",',
            )

        # 3. Add to models dictionary
        models_insertion_point = '0xDD: [850000000, 950000000, 22, "850 - 950 MHz", "rnode_firmware_xiao_esp32s3.zip", "SX1262"],'
        if models_insertion_point in content:
            content = content.replace(
                models_insertion_point,
                models_insertion_point
                + '\n    0x62: [902000000, 928000000, 37, "902 - 928 MHz (Station G2, 5W)", "rnode_firmware_station_g2.zip", "SX1262"],',
            )

        # Write the modified content
        with open(rnodeconf_path, "w") as f:
            f.write(content)

        print("Successfully patched rnodeconf with Station G2 support")
        print("Added:")
        print("  - PRODUCT_STATION_G2 = 0x60")
        print("  - MODEL_62 = 0x62")
        print("  - Product name mapping")
        print("  - Model capabilities (902-928 MHz, 37 dBm max, SX1262)")
        return True

    except ImportError:
        print("ERROR: RNS module not found. Is rnodeconf installed?")
        return False
    except Exception as e:
        print(f"ERROR patching rnodeconf: {e}")
        return False


if __name__ == "__main__":
    if patch_rnodeconf():
        print("\nTo provision a Station G2 with blank EEPROM:")
        print("  rnodeconf /dev/ttyACM0 -r --product 60 --model 62 --hwrev 1")
        print("\nTo verify after provisioning:")
        print("  rnodeconf /dev/ttyACM0 -i")
    else:
        sys.exit(1)
