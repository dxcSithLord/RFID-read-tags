#!/usr/bin/env python3
"""
RFID Tag Writer Script
Writes object and location IDs to RFID tags with LED status indication
"""

import json
import logging
import time
from typing import Dict, List, Any, Optional

try:
    from mfrc522 import SimpleMFRC522
    import RPi.GPIO as GPIO
    from gpiozero import RGBLED
    from colorzero import Color
except ImportError as e:
    print(f"Warning: Required library not found: {e}")
    print("Please install with: pip install mfrc522 gpiozero colorzero")
    print("Running in simulation mode...")
    SimpleMFRC522 = None
    GPIO = None
    RGBLED = None
    Color = None


class RFIDTagWriter:
    """RFID tag writer with LED status indication"""

    def __init__(self, led_pins=(12, 13, 19)):
        """
        Initialize RFID tag writer

        Args:
            led_pins: Tuple of (red, green, blue) GPIO pins for RGB LED
        """
        self.reader = SimpleMFRC522() if SimpleMFRC522 else None
        self.led = RGBLED(*led_pins) if RGBLED else None

        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        if not self.reader:
            self.logger.warning("Running in simulation mode - no actual writing will occur")

    def set_led_color(self, color: str, flash: bool = False, duration: float = 1.0):
        """
        Set LED color with optional flashing

        Args:
            color: Color name ('white', 'yellow', 'blue', 'green', 'purple', 'red', 'off')
            flash: Whether to flash the LED
            duration: Duration to show color (None for indefinite)
        """
        if not self.led or not Color:
            return

        color_map = {
            'white': Color('white'),
            'yellow': Color('yellow'),
            'blue': Color('blue'),
            'green': Color('green'),
            'purple': Color('purple'),
            'red': Color('red'),
            'off': Color('black')
        }

        led_color = color_map.get(color.lower(), Color('white'))

        if flash:
            # Flash the LED 3 times
            for _ in range(3):
                self.led.color = led_color
                time.sleep(0.2)
                self.led.color = Color('black')
                time.sleep(0.2)
            if duration:
                time.sleep(duration)
        else:
            self.led.color = led_color
            if duration:
                time.sleep(duration)
                self.led.color = Color('black')  # Turn off after duration

    def write_tag(self, item_id: str, item_type: str) -> bool:
        """
        Write an item ID to an RFID tag

        Args:
            item_id: Item identifier to write
            item_type: Type of item ('object' or 'location')

        Returns:
            True if successful, False otherwise
        """
        if not self.reader:
            self.logger.info(f"SIMULATION: Would write {item_type} '{item_id}' to tag")
            time.sleep(2)  # Simulate write time
            return True

        try:
            # Show white LED while waiting for tag
            self.set_led_color('white')
            self.logger.info(f"Hold a tag near the reader to write {item_type}: {item_id}")

            # Write to tag
            self.reader.write(item_id)

            # Show appropriate color flash for item type
            if item_type == 'object':
                self.set_led_color('yellow', flash=True)
                self.logger.info(f"Successfully wrote object '{item_id}' to tag")
            else:  # location
                self.set_led_color('blue', flash=True)
                self.logger.info(f"Successfully wrote location '{item_id}' to tag")

            return True

        except Exception as e:
            self.logger.error(f"Error writing to RFID tag: {e}")
            # Flash red on error
            self.set_led_color('red', flash=True)
            return False
        finally:
            # Turn off LED
            self.set_led_color('off')

    def cleanup(self):
        """Clean up GPIO resources"""
        if self.led:
            self.led.close()
        if GPIO:
            GPIO.cleanup()


class ConfigManager:
    """Manages configuration data from JSON file"""

    def __init__(self, config_file: str = "rfid_config.json"):
        self.config_file = config_file
        self.config_data = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"Config file {self.config_file} not found")
            return {}
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing config file: {e}")
            return {}

    def get_all_objects(self) -> Dict[str, Any]:
        """Get all object definitions"""
        return self.config_data.get('objects', {})

    def get_all_locations(self) -> Dict[str, Any]:
        """Get all location definitions"""
        return self.config_data.get('locations', {})


def interactive_writer():
    """Interactive mode for writing individual tags"""
    writer = RFIDTagWriter()
    config_manager = ConfigManager()

    try:
        while True:
            print("\n" + "="*50)
            print("RFID Tag Writer - Interactive Mode")
            print("="*50)
            print("1. Write Object Tag")
            print("2. Write Location Tag")
            print("3. List Available Objects")
            print("4. List Available Locations")
            print("5. Exit")

            choice = input("\nEnter your choice (1-5): ").strip()

            if choice == '1':
                objects = config_manager.get_all_objects()
                if not objects:
                    print("No objects found in configuration file")
                    continue

                print("\nAvailable Objects:")
                for obj_id, obj_data in objects.items():
                    print(f"  {obj_id}: {obj_data.get('name', 'No name')}")

                obj_id = input("\nEnter object ID to write: ").strip()
                if obj_id in objects:
                    if writer.write_tag(obj_id, 'object'):
                        print(f"✓ Successfully wrote object tag: {obj_id}")
                    else:
                        print(f"✗ Failed to write object tag: {obj_id}")
                else:
                    print(f"Object ID '{obj_id}' not found in configuration")

            elif choice == '2':
                locations = config_manager.get_all_locations()
                if not locations:
                    print("No locations found in configuration file")
                    continue

                print("\nAvailable Locations:")
                for loc_id, loc_data in locations.items():
                    print(f"  {loc_id}: {loc_data.get('name', 'No name')}")

                loc_id = input("\nEnter location ID to write: ").strip()
                if loc_id in locations:
                    if writer.write_tag(loc_id, 'location'):
                        print(f"✓ Successfully wrote location tag: {loc_id}")
                    else:
                        print(f"✗ Failed to write location tag: {loc_id}")
                else:
                    print(f"Location ID '{loc_id}' not found in configuration")

            elif choice == '3':
                objects = config_manager.get_all_objects()
                print(f"\nAvailable Objects ({len(objects)}):")
                for obj_id, obj_data in objects.items():
                    name = obj_data.get('name', 'No name')
                    desc = obj_data.get('description', 'No description')
                    print(f"  {obj_id}: {name}")
                    print(f"    Description: {desc}")
                    print()

            elif choice == '4':
                locations = config_manager.get_all_locations()
                print(f"\nAvailable Locations ({len(locations)}):")
                for loc_id, loc_data in locations.items():
                    name = loc_data.get('name', 'No name')
                    desc = loc_data.get('description', 'No description')
                    print(f"  {loc_id}: {name}")
                    print(f"    Description: {desc}")
                    print()

            elif choice == '5':
                print("Exiting...")
                break

            else:
                print("Invalid choice. Please enter 1-5.")

    except KeyboardInterrupt:
        print("\nStopping writer...")
    finally:
        writer.cleanup()


def batch_writer():
    """Batch mode for writing all objects and locations"""
    writer = RFIDTagWriter()
    config_manager = ConfigManager()

    try:
        objects = config_manager.get_all_objects()
        locations = config_manager.get_all_locations()

        print("\n" + "="*50)
        print("RFID Tag Writer - Batch Mode")
        print("="*50)
        print(f"Objects to write: {len(objects)}")
        print(f"Locations to write: {len(locations)}")
        print(f"Total tags needed: {len(objects) + len(locations)}")

        input("\nPress Enter to start batch writing...")

        # Write all objects
        print(f"\n--- Writing {len(objects)} Object Tags ---")
        for i, (obj_id, obj_data) in enumerate(objects.items(), 1):
            name = obj_data.get('name', 'No name')
            print(f"\n[{i}/{len(objects)}] Writing object: {obj_id} ({name})")

            success = False
            while not success:
                success = writer.write_tag(obj_id, 'object')
                if not success:
                    retry = input("Write failed. Retry? (y/n): ").strip().lower()
                    if retry != 'y':
                        break

            if success:
                print(f"✓ Object tag written successfully")
                # Show green LED briefly after successful write
                writer.set_led_color('green', duration=1.0)
            else:
                print(f"✗ Skipped object tag: {obj_id}")

        print(f"\n--- Writing {len(locations)} Location Tags ---")
        for i, (loc_id, loc_data) in enumerate(locations.items(), 1):
            name = loc_data.get('name', 'No name')
            print(f"\n[{i}/{len(locations)}] Writing location: {loc_id} ({name})")

            success = False
            while not success:
                success = writer.write_tag(loc_id, 'location')
                if not success:
                    retry = input("Write failed. Retry? (y/n): ").strip().lower()
                    if retry != 'y':
                        break

            if success:
                print(f"✓ Location tag written successfully")
                # Show green LED briefly after successful write
                writer.set_led_color('green', duration=1.0)
            else:
                print(f"✗ Skipped location tag: {loc_id}")

        print("\n" + "="*50)
        print("Batch writing completed!")
        # Show purple LED for 3 seconds when all done
        writer.set_led_color('purple', duration=3.0)
        print("="*50)

    except KeyboardInterrupt:
        print("\nBatch writing interrupted...")
    finally:
        writer.cleanup()


def verify_tags():
    """Verify written tags by reading them back"""
    writer = RFIDTagWriter()
    config_manager = ConfigManager()

    try:
        print("\n" + "="*50)
        print("RFID Tag Verification Mode")
        print("="*50)
        print("Hold tags near the reader to verify their contents")
        print("Press Ctrl+C to exit")

        while True:
            try:
                # Show white LED while waiting
                writer.set_led_color('white')
                print("\nHold a tag near the reader to verify...")

                if writer.reader:
                    tag_id, text = writer.reader.read()
                    item_id = text.strip()
                else:
                    # Simulation
                    time.sleep(2)
                    item_id = "simulated_item"
                    tag_id = 1234

                writer.set_led_color('off')
                print(f"Tag ID: {tag_id}")
                print(f"Item ID: {item_id}")

                # Check if it's a valid object or location
                objects = config_manager.get_all_objects()
                locations = config_manager.get_all_locations()

                if item_id in objects:
                    obj_data = objects[item_id]
                    print(f"✓ Valid OBJECT: {obj_data.get('name', 'No name')}")
                    print(f"  Description: {obj_data.get('description', 'No description')}")
                    writer.set_led_color('yellow', flash=True)
                elif item_id in locations:
                    loc_data = locations[item_id]
                    print(f"✓ Valid LOCATION: {loc_data.get('name', 'No name')}")
                    print(f"  Description: {loc_data.get('description', 'No description')}")
                    writer.set_led_color('blue', flash=True)
                else:
                    print(f"✗ Unknown item ID: {item_id}")
                    writer.set_led_color('red', flash=True)

                time.sleep(1)

            except Exception as e:
                logging.error(f"Error reading tag: {e}")
                writer.set_led_color('red', flash=True)
                time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping verification...")
    finally:
        writer.cleanup()


def main():
    """Main entry point"""
    print("RFID Tag Writer")
    print("===============")
    print("1. Interactive Mode - Write individual tags")
    print("2. Batch Mode - Write all objects and locations")
    print("3. Verification Mode - Read and verify tags")
    print("4. Exit")

    choice = input("\nEnter your choice (1-4): ").strip()

    if choice == '1':
        interactive_writer()
    elif choice == '2':
        batch_writer()
    elif choice == '3':
        verify_tags()
    elif choice == '4':
        print("Goodbye!")
    else:
        print("Invalid choice. Please run again and select 1-4.")


if __name__ == "__main__":
    main()
