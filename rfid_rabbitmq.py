#!/usr/bin/env python3
"""
RFID-based RabbitMQ Scanner
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
    
    def __init__(self, led_pins=(12, 13, 19)):
        """
        Initialize RFID scanner with LED status indicator
        
        Args:
            led_pins: Tuple of (red, green, blue) GPIO pins for RGB LED
        """
        self.reader = SimpleMFRC522() if SimpleMFRC522 else None
        self.led = RGBLED(*led_pins) if RGBLED else None
        self.led_active = False
        
    def set_led_color(self, color: str, flash: bool = False, duration: float = None):
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
        
        # Simulate some delay
        time.sleep(2)
        
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
            logging.warning(f"Config file {self.config_file} not found. Creating sample config...")
            return self._create_sample_config()
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing config file: {e}")
            return {}

    def _create_sample_config(self) -> Dict[str, Any]:
        """Create a sample configuration file"""
        sample_config = {
            "objects": {
                "obj001": {
                    "name": "Widget A",
                    "description": "Standard widget for assembly line",
                    "category": "component",
                    "weight": 0.5,
                    "dimensions": {"length": 10, "width": 5, "height": 2}
                },
                "obj002": {
                    "name": "Tool B",
                    "description": "Precision measurement tool",
                    "category": "tool",
                    "weight": 1.2,
                    "calibration_date": "2024-01-15"
                },
                "obj003": {
                    "name": "Component C",
                    "description": "Electronic component",
                    "category": "electronics",
                    "weight": 0.1,
                    "voltage": 5.0
                }
            },
            "locations": {
                "loc001": {
                    "name": "Assembly Station 1",
                    "description": "Primary assembly workstation",
                    "zone": "production",
                    "capacity": 50,
                    "coordinates": {"x": 10, "y": 20, "z": 0}
                },
                "loc002": {
                    "name": "Quality Control",
                    "description": "Quality inspection station",
                    "zone": "quality",
                    "capacity": 20,
                    "equipment": ["scanner", "scale", "calipers"]
                },
                "loc003": {
                    "name": "Storage Rack A1",
                    "description": "Primary storage location",
                    "zone": "warehouse",
                    "capacity": 100,
                    "temperature_controlled": True
                }
            }
        }

        # Save sample config
        try:
            with open(self.config_file, 'w') as f:
                json.dump(sample_config, f, indent=2)
            logging.info(f"Created sample config file: {self.config_file}")
        except Exception as e:
            logging.error(f"Error creating sample config: {e}")

        return sample_config

    def get_item_data(self, item_id: str, item_type: ItemType) -> Optional[Dict[str, Any]]:
        """
        Get item data from configuration

        Args:
            item_id: Item identifier
            item_type: Type of item (object or location)

        Returns:
            Dictionary with item data or None if not found
        """
        section = item_type.value + "s"  # "objects" or "locations"
        return self.config_data.get(section, {}).get(item_id)


class RFIDRabbitMQScanner:
    """Main scanner class that coordinates RFID reading and RabbitMQ messaging"""

    def __init__(self, config_file: str = "rfid_config.json",
                 led_pins: Tuple = (12, 13, 19), **rabbitmq_kwargs):
        """
        Initialize the RFID scanner

        Args:
            config_file: Path to JSON configuration file
            led_pins: Tuple of (red, green, blue) GPIO pins for RGB LED
            **rabbitmq_kwargs: Arguments for MessageTransmitter
        """
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.rfid_scanner = RFIDScanner(led_pins)
        self.config_manager = ConfigManager(config_file)
        self.message_transmitter = MessageTransmitter(**rabbitmq_kwargs)

        # Track scanned items
        self.scanned_items = []
        self.object_item = None
        self.location_item = None

        self.logger.info("RFID RabbitMQ Scanner initialized")

    def _determine_item_type(self, item_id: str) -> Optional[ItemType]:
        """
        Determine if an item ID is an object or location

        Args:
            item_id: Item identifier

        Returns:
            ItemType or None if not found
        """
        # Check if it's an object
        if self.config_manager.get_item_data(item_id, ItemType.OBJECT):
            return ItemType.OBJECT

        # Check if it's a location
        if self.config_manager.get_item_data(item_id, ItemType.LOCATION):
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

        item_data = self.config_manager.get_item_data(item_id, item_type)
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
            # Flash green when both items are ready
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
                # Create and send message
                message = self._create_message(self.object_item, self.location_item)
                self.message_transmitter.transmit_message(message)

                # Show solid purple for 2 seconds after successful transmission
                self.rfid_scanner.set_led_color('purple', duration=2.0)

                self.logger.info("Message sent successfully!")
                self.logger.info(f"Object: {self.object_item.data.get('name')} -> Location: {self.location_item.data.get('name')}")

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
                    time.sleep(0.5)  # Small delay between scans

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
            self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        self.rfid_scanner.cleanup()
        if hasattr(self.message_transmitter, 'cleanup'):
            self.message_transmitter.cleanup()
        self.logger.info("Scanner cleanup completed")


def main():
    """Main entry point"""
    # RabbitMQ configuration
    rabbitmq_config = {
        'log_level': logging.INFO,
        'rabbitmq_host': os.getenv('RABBITMQ_HOST', 'localhost'),
        'rabbitmq_port': int(os.getenv('RABBITMQ_PORT', '5672')),
        'rabbitmq_vhost': os.getenv('RABBITMQ_VHOST', '/'),
        'queue_name': os.getenv('RABBITMQ_QUEUE', 'rfid_messages'),
        'exchange_name': os.getenv('RABBITMQ_EXCHANGE', ''),
        'routing_key': os.getenv('RABBITMQ_ROUTING_KEY', ''),
        'username': os.getenv('RABBITMQ_USERNAME'),
        'password': os.getenv('RABBITMQ_PASSWORD'),
        'use_ssl': os.getenv('RABBITMQ_USE_SSL', 'false').lower() == 'true'
    }

    # Create and run scanner
    scanner = RFIDRabbitMQScanner(
        config_file="rfid_config.json",
        led_pins=(12, 13, 19),  # GPIO pins for RGB LED (red, green, blue)
        **rabbitmq_config
    )

    scanner.run()


if __name__ == "__main__":
    main()
