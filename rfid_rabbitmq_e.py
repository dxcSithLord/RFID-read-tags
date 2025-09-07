#!/usr/bin/env python3
"""
RFID-based RabbitMQ Scanner (Updated to use EnhancedConfigManager)
Reads RFID tags to identify objects and locations, then sends messages via RabbitMQ
"""

import json
import logging
import time
import os
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

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

from rabbitmq_tx import MessageTransmitter
from enhanced_config_manager import EnhancedConfigManager


class ItemType(Enum):
    """Enum for item types"""
    OBJECT = "object"
    LOCATION = "location"


@dataclass
class ScannedItem:
    """Data class for scanned items"""
    item_id: str
    item_type: ItemType
    data: Dict[str, Any]


class RFIDScanner:
    """RFID scanner for reading SimpleMFRC522 tags"""
    
    def __init__(self, led_pins=(12, 13, 19), timing_config=None, test_mode=False):
        """
        Initialize RFID scanner with LED status indicator
        
        Args:
            led_pins: Tuple of (red, green, blue) GPIO pins for RGB LED
            timing_config: Timing configuration object
            test_mode: Enable test/simulation mode
        """
        self.reader = SimpleMFRC522() if SimpleMFRC522 and not test_mode else None
        self.led = RGBLED(*led_pins) if RGBLED else None
        self.led_active = False
        self.timing_config = timing_config
        self.test_mode = test_mode
        self.rabbitmq_connected = True  # Will be updated by status callback
        self._led_flash_thread = None
        self._stop_flashing = False
        
    def set_rabbitmq_status(self, connected: bool):
        """Update RabbitMQ connection status for LED indication"""
        self.rabbitmq_connected = connected
        
    def set_led_color(self, color: str, flash: bool = False, duration: float = None):
        """
        Set LED color with optional flashing
        
        Args:
            color: Color name ('white', 'yellow', 'blue', 'green', 'purple', 'red', 'off', 'orange')
            flash: Whether to flash the LED
            duration: Duration to show color (None for indefinite, uses config default for green)
        """
        if not self.led or not Color:
            return
            
        # Use config default for green flash duration if not specified
        if duration is None and color.lower() == 'green' and self.timing_config:
            duration = self.timing_config.green_flash_duration
            
        color_map = {
            'white': Color('white'),
            'yellow': Color('yellow'), 
            'blue': Color('blue'),
            'green': Color('green'),
            'purple': Color('purple'),
            'red': Color('red'),
            'orange': Color('orange'),
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

    def start_continuous_flash(self, color: str, interval: float = 1.0):
        """
        Start continuous flashing LED in a separate thread
        
        Args:
            color: Color to flash
            interval: Flash interval in seconds
        """
        import threading
        
        self.stop_continuous_flash()  # Stop any existing flash
        
        def flash_led():
            color_obj = Color(color.lower()) if Color else None
            if not color_obj or not self.led:
                return
                
            while not self._stop_flashing:
                self.led.color = color_obj
                time.sleep(interval / 2)
                if self._stop_flashing:
                    break
                self.led.color = Color('black')
                time.sleep(interval / 2)
        
        self._stop_flashing = False
        self._led_flash_thread = threading.Thread(target=flash_led, daemon=True)
        self._led_flash_thread.start()
    
    def stop_continuous_flash(self):
        """Stop continuous LED flashing"""
        self._stop_flashing = True
        if self._led_flash_thread and self._led_flash_thread.is_alive():
            self._led_flash_thread.join(timeout=1)
        self._led_flash_thread = None

    def read_tag(self) -> Optional[Tuple[int, str]]:
        """
        Read an RFID tag with LED status indication

        Returns:
            Tuple of (id, text) if successful, None otherwise
        """
        if not self.reader or self.test_mode:
            # Simulation mode for testing
            return self._simulate_tag_read()

        try:
            # Show appropriate LED while waiting for tag
            if self.rabbitmq_connected:
                # Normal operation - steady white
                self.set_led_color('white')
            else:
                # RabbitMQ unavailable - flashing orange
                flash_interval = self.timing_config.orange_flash_interval if self.timing_config else 1.0
                self.start_continuous_flash('orange', flash_interval)
            
            logging.info("Hold a tag near the reader...")
            
            tag_id, text = self.reader.read()
            
            # Stop any flashing and turn off LED after successful read
            self.stop_continuous_flash()
            self.set_led_color('off')
            
            return tag_id, text.strip()
        except Exception as e:
            logging.error(f"Error reading RFID tag: {e}")
            self.stop_continuous_flash()
            self.set_led_color('off')
            return None

    def _simulate_tag_read(self) -> Optional[Tuple[int, str]]:
        """Simulate tag reading for testing purposes"""
        import random
        
        # Show appropriate LED while simulating
        if self.rabbitmq_connected:
            self.set_led_color('white')
        else:
            flash_interval = self.timing_config.orange_flash_interval if self.timing_config else 1.0
            self.start_continuous_flash('orange', flash_interval)
        
        # Use configured read interval if available
        delay = self.timing_config.read_interval if self.timing_config else 2
        time.sleep(delay)
        
        # Stop flashing and turn off LED
        self.stop_continuous_flash()
        self.set_led_color('off')
        
        # Return simulated data
        sample_objects = ["RFID1", "RFID2", "RFID3", "RFID4", "RFID5"]
        sample_locations = ["OP1", "OP2", "OP3", "OP4", "OP5"]

        if random.choice([True, False]):
            return random.randint(1000, 9999), random.choice(sample_objects)
        else:
            return random.randint(1000, 9999), random.choice(sample_locations)

    def cleanup(self):
        """Clean up GPIO resources"""
        self.stop_continuous_flash()
        if self.led:
            self.led.close()
        if GPIO:
            GPIO.cleanup()_config:
            duration = self.timing_config.green_flash_duration
            
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

    def read_tag(self) -> Optional[Tuple[int, str]]:
        """
        Read an RFID tag with LED status indication

        Returns:
            Tuple of (id, text) if successful, None otherwise
        """
        if not self.reader:
            # Simulation mode for testing
            return self._simulate_tag_read()

        try:
            # Show white LED while waiting for tag
            self.set_led_color('white')
            logging.info("Hold a tag near the reader...")
            
            tag_id, text = self.reader.read()
            
            # Turn off LED after successful read
            self.set_led_color('off')
            
            return tag_id, text.strip()
        except Exception as e:
            logging.error(f"Error reading RFID tag: {e}")
            self.set_led_color('off')
            return None

    def _simulate_tag_read(self) -> Optional[Tuple[int, str]]:
        """Simulate tag reading for testing purposes"""
        import random
        
        # Show white LED while simulating
        self.set_led_color('white')
        
        # Use configured read interval if available
        delay = self.timing_config.read_interval if self.timing_config else 2
        time.sleep(delay)
        
        # Turn off LED
        self.set_led_color('off')
        
        # Return simulated data
        sample_objects = ["RFID1", "RFID2", "RFID3"]
        sample_locations = ["OP1", "OP2", "OP3"]

        if random.choice([True, False]):
            return random.randint(1000, 9999), random.choice(sample_objects)
        else:
            return random.randint(1000, 9999), random.choice(sample_locations)

    def cleanup(self):
        """Clean up GPIO resources"""
        if self.led:
            self.led.close()
        if GPIO:
            GPIO.cleanup()


class RFIDRabbitMQScanner:
    """Main scanner class that coordinates RFID reading and RabbitMQ messaging"""

    def __init__(self, config_file: str = "rfid_config.json"):
        """
        Initialize the RFID scanner using enhanced configuration manager

        Args:
            config_file: Path to JSON configuration file
        """
        # Initialize configuration manager
        self.config_manager = EnhancedConfigManager(config_file)
        
        # Set up logging based on configuration
        log_level = getattr(logging, self.config_manager.logging_config.level.upper(), logging.INFO)
        logging.basicConfig(
            level=log_level,
            format=self.config_manager.logging_config.format,
            datefmt=self.config_manager.logging_config.date_format,
            filename=self.config_manager.logging_config.file
        )
        self.logger = logging.getLogger(__name__)

        # Validate configuration
        validation_errors = self.config_manager.validate_configuration()
        if validation_errors:
            self.logger.warning("Configuration validation errors found:")
            for error in validation_errors:
                self.logger.warning(f"  - {error}")

        # Initialize components with configuration
        self.rfid_scanner = RFIDScanner(
            led_pins=self.config_manager.get_led_pins(),
            timing_config=self.config_manager.timing
        )
        
        # Get RabbitMQ configuration and initialize transmitter
        rabbitmq_config = self.config_manager.get_rabbitmq_config()
        self.message_transmitter = MessageTransmitter(**rabbitmq_config)

        # Track scanned items
        self.scanned_items = []
        self.object_item = None
        self.location_item = None

        # Update service start statistics
        self.config_manager.increment_service_starts()
        
        self.logger.info("RFID RabbitMQ Scanner initialized with enhanced configuration")
        self.logger.info(f"Configuration summary: {self.config_manager.get_summary()}")

    def _determine_item_type(self, item_id: str) -> Optional[ItemType]:
        """
        Determine if an item ID is an object or location

        Args:
            item_id: Item identifier

        Returns:
            ItemType or None if not found
        """
        # Check if it's an object
        if self.config_manager.get_item_data(item_id, "object"):
            return ItemType.OBJECT

        # Check if it's a location
        if self.config_manager.get_item_data(item_id, "location"):
            return ItemType.LOCATION

        return None

    def _create_scanned_item(self, tag_id: int, item_id: str) -> Optional[ScannedItem]:
        """
        Create a ScannedItem from tag data

        Args:
            tag_id: RFID tag ID
            item_id: Item identifier from tag

        Returns:
            ScannedItem or None if invalid
        """
        item_type = self._determine_item_type(item_id)
        if not item_type:
            self.logger.warning(f"Unknown item ID: {item_id}")
            return None

        item_data = self.config_manager.get_item_data(item_id, item_type.value)
        if not item_data:
            self.logger.warning(f"No data found for {item_type.value} {item_id}")
            return None

        return ScannedItem(
            item_id=item_id,
            item_type=item_type,
            data=item_data
        )

    def _create_message(self, object_item: ScannedItem, location_item: ScannedItem) -> Dict[str, Any]:
        """
        Create message content for RabbitMQ

        Args:
            object_item: Scanned object item
            location_item: Scanned location item

        Returns:
            Dictionary with message content
        """
        message = {
            "timestamp": time.time(),
            "scan_type": "rfid",
            "object": {
                "id": object_item.item_id,
                "type": "object",
                "data": object_item.data
            },
            "location": {
                "id": location_item.item_id,
                "type": "location",
                "data": location_item.data
            },
            "action": {
                "type": "object_location_scan",
                "description": f"Object {object_item.data.get('name', object_item.item_id)} scanned at location {location_item.data.get('name', location_item.item_id)}"
            },
            "scanner_info": {
                "service_starts": self.config_manager.statistics.service_starts,
                "config_file": self.config_manager.config_file
            }
        }

        return message

    def _reset_scan_state(self):
        """Reset the scanning state"""
        self.object_item = None
        self.location_item = None
        self.scanned_items = []

    def _process_scanned_item(self, scanned_item: ScannedItem) -> bool:
        """
        Process a newly scanned item with LED status indication

        Args:
            scanned_item: The scanned item

        Returns:
            True if ready to send message, False otherwise
        """
        item_type = scanned_item.item_type
        item_name = scanned_item.data.get('name', scanned_item.item_id)

        if item_type == ItemType.OBJECT:
            if self.object_item:
                self.logger.info(f"Replacing previous object scan with {item_name}")
            self.object_item = scanned_item
            self.logger.info(f"Object scanned: {item_name}")
            # Flash yellow for object
            self.rfid_scanner.set_led_color('yellow', flash=True)

        elif item_type == ItemType.LOCATION:
            if self.location_item:
                self.logger.info(f"Replacing previous location scan with {item_name}")
            self.location_item = scanned_item
            self.logger.info(f"Location scanned: {item_name}")
            # Flash blue for location
            self.rfid_scanner.set_led_color('blue', flash=True)

        # Check if we have both items
        if self.object_item and self.location_item:
            self.logger.info("Both object and location scanned - ready to send message")
            # Flash green when both items are ready (uses configured duration)
            self.rfid_scanner.set_led_color('green', flash=True)
            return True
        else:
            missing = "location" if self.object_item else "object"
            self.logger.info(f"Waiting for {missing} scan...")
            return False

    def run_once(self) -> bool:
        """
        Run one scan cycle

        Returns:
            True if message was sent, False otherwise
        """
        # Read RFID tag
        tag_data = self.rfid_scanner.read_tag()
        if not tag_data:
            # Flash red briefly for read failure, then turn off
            self.rfid_scanner.set_led_color('red', flash=True)
            return False

        tag_id, item_id = tag_data
        self.logger.info(f"Tag read - ID: {tag_id}, Item: {item_id}")

        # Create scanned item
        scanned_item = self._create_scanned_item(tag_id, item_id)
        if not scanned_item:
            # Flash red for unknown item, then turn off
            self.rfid_scanner.set_led_color('red', flash=True)
            return False

        # Process the scanned item
        ready_to_send = self._process_scanned_item(scanned_item)

        if ready_to_send:
            try:
                # Update scan statistics
                self.config_manager.update_last_scan()
                self.config_manager.update_statistics(
                    total_tags=self.config_manager.statistics.total_tags + 1
                )

                # Create and send message
                message = self._create_message(self.object_item, self.location_item)
                self.message_transmitter.transmit_message(message)

                # Show solid purple for 2 seconds after successful transmission
                self.rfid_scanner.set_led_color('purple', duration=2.0)

                self.logger.info("Message sent successfully!")
                self.logger.info(f"Object: {self.object_item.data.get('name')} -> Location: {self.location_item.data.get('name')}")

                # Save updated configuration (statistics)
                self.config_manager.save_configuration()

                # Reset state for next scan pair
                self._reset_scan_state()
                return True

            except Exception as e:
                self.logger.error(f"Error sending message: {e}")
                # Flash red on error
                self.rfid_scanner.set_led_color('red', flash=True)
                return False

        return False

    def run(self):
        """Run the scanner continuously"""
        self.logger.info("Starting RFID scanner...")
        self.logger.info("Scan an object and a location to send a message")

        # Brief startup indication - flash all colors
        if self.rfid_scanner.led:
            self.rfid_scanner.set_led_color('red', duration=0.3)
            self.rfid_scanner.set_led_color('green', duration=0.3)
            self.rfid_scanner.set_led_color('blue', duration=0.3)
            self.rfid_scanner.set_led_color('off')

        try:
            while True:
                try:
                    self.run_once()
                    # Use configured read interval
                    time.sleep(self.config_manager.timing.read_interval)

                except KeyboardInterrupt:
                    self.logger.info("Stopping scanner...")
                    break
                except Exception as e:
                    self.logger.error(f"Unexpected error: {e}")
                    # Flash red for unexpected errors
                    self.rfid_scanner.set_led_color('red', flash=True)
                    time.sleep(1)

        finally:
            # Turn off LED before cleanup
            self.rfid_scanner.set_led_color('off')
            # Save final configuration state
            self.config_manager.save_configuration()
            self.cleanup()

    def add_new_item(self, item_id: str, item_type: str, item_data: Dict[str, Any]) -> bool:
        """
        Add a new item to the configuration
        
        Args:
            item_id: Item identifier
            item_type: Type of item ("object" or "location")
            item_data: Item data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        success = self.config_manager.add_item(item_id, item_type, item_data)
        if success:
            self.config_manager.save_configuration()
            self.logger.info(f"Added new {item_type}: {item_id}")
        return success

    def remove_item(self, item_id: str, item_type: str) -> bool:
        """
        Remove an item from the configuration
        
        Args:
            item_id: Item identifier
            item_type: Type of item ("object" or "location")
            
        Returns:
            True if successful, False otherwise
        """
        success = self.config_manager.remove_item(item_id, item_type)
        if success:
            self.config_manager.save_configuration()
            self.logger.info(f"Removed {item_type}: {item_id}")
        return success

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get current scanner statistics
        
        Returns:
            Dictionary with statistics
        """
        return {
            "total_tags": self.config_manager.statistics.total_tags,
            "service_starts": self.config_manager.statistics.service_starts,
            "last_scan": self.config_manager.statistics.last_scan,
            "objects_count": len(self.config_manager.get_all_items("objects")),
            "locations_count": len(self.config_manager.get_all_items("locations"))
        }

    def list_items(self, item_type: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        List all items of specified type
        
        Args:
            item_type: Type of item ("object", "location", or None for all)
            
        Returns:
            Dictionary with items
        """
        return self.config_manager.get_all_items(item_type)

    def cleanup(self):
        """Clean up resources"""
        self.rfid_scanner.cleanup()
        if hasattr(self.message_transmitter, 'cleanup'):
            self.message_transmitter.cleanup()
        self.logger.info("Scanner cleanup completed")


def main():
    """Main entry point with test mode support"""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='RFID RabbitMQ Scanner')
    parser.add_argument('--config', '-c', default='rfid_config.json',
                        help='Configuration file path (default: rfid_config.json)')
    parser.add_argument('--test', '-t', action='store_true',
                        help='Enable test/simulation mode')
    parser.add_argument('--status', '-s', action='store_true',
                        help='Show status and exit')
    parser.add_argument('--validate', '-v', action='store_true',
                        help='Validate configuration and exit')
    
    args = parser.parse_args()
    
    # Create scanner with configuration file and test mode
    scanner = RFIDRabbitMQScanner(config_file=args.config, test_mode=args.test)
    
    if args.validate:
        # Just validate configuration and exit
        print("Configuration Validation Results:")
        print("=" * 40)
        errors = scanner.config_manager.validate_configuration()
        if errors:
            print("Validation errors found:")
            for error in errors:
                print(f"  ✗ {error}")
            return 1
        else:
            print("✓ Configuration is valid!")
            return 0
    
    if args.status:
        # Show status and exit
        print("RFID Scanner Status:")
        print("=" * 40)
        status = scanner.get_status()
        for key, value in status.items():
            if isinstance(value, dict):
                print(f"{key}:")
                for sub_key, sub_value in value.items():
                    print(f"  {sub_key}: {sub_value}")
            else:
                print(f"{key}: {value}")
        return 0
    
    # Print startup information
    print(f"RFID Scanner Configuration Summary:")
    print("=" * 40)
    status = scanner.get_status()
    
    print(f"Test Mode: {'ENABLED' if status['test_mode'] else 'DISABLED'}")
    print(f"Config File: {status['config_file']}")
    print(f"RabbitMQ: {'CONNECTED' if status['rabbitmq_connected'] else 'DISCONNECTED (Fallback Mode)'}")
    print(f"Queue: {status['queue_name']}")
    print(f"Objects: {status['objects_count']}")
    print(f"Locations: {status['locations_count']}")
    
    if status['fallback_messages'] > 0:
        print(f"Queued Messages: {status['fallback_messages']} (will be sent when RabbitMQ available)")
    
    # Check for validation errors
    errors = scanner.config_manager.validate_configuration()
    if errors:
        print("\nConfiguration validation warnings:")
        for error in errors:
            print(f"  ⚠ {error}")
    
    print("\nStarting scanner...")
    if args.test:
        print("Running in TEST MODE - RFID operations will be simulated")
    
    # Run the scanner
    try:
        scanner.run()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Scanner error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    main()
