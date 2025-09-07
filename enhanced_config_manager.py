#!/usr/bin/env python3
"""
Enhanced Configuration Manager for RFID RabbitMQ Scanner
Provides robust configuration loading, validation, and management
"""

import json
import logging
import os
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import copy


@dataclass
class RabbitMQConfig:
    """Configuration for RabbitMQ connection"""
    host: str = "localhost"
    port: int = 5672
    use_ssl: bool = False
    username: Optional[str] = None
    password: Optional[str] = None
    virtual_host: str = "/"
    exchange: str = ""
    queue_name: str = "rfid_messages"
    queue_scan_results: str = "scan_results"
    queue_location_updates: str = "location_updates"
    routing_key_scan: str = "rfid.scan.result"
    routing_key_update: str = "asset.location.update"


@dataclass
class LoggingConfig:
    """Configuration for logging"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    file: Optional[str] = None


@dataclass
class HardwareConfig:
    """Configuration for hardware pins"""
    red_pin: int = 12
    green_pin: int = 13
    blue_pin: int = 19


@dataclass
class TimingConfig:
    """Configuration for timing parameters"""
    read_interval: float = 2.0
    green_flash_duration: float = 2.0
    orange_flash_interval: float = 2.0


@dataclass
class StatisticsConfig:
    """Configuration for statistics tracking"""
    total_tags: int = 0
    service_starts: int = 0
    last_scan: Optional[str] = None


class EnhancedConfigManager:
    """
    Enhanced configuration manager with validation, defaults, and environment variable support
    """
    
    def __init__(self, config_file: str = "rfid_config.json", 
                 auto_create: bool = True, 
                 use_env_vars: bool = True):
        """
        Initialize the configuration manager
        
        Args:
            config_file: Path to JSON configuration file
            auto_create: Whether to create default config if file doesn't exist
            use_env_vars: Whether to override config with environment variables
        """
        self.config_file = config_file
        self.auto_create = auto_create
        self.use_env_vars = use_env_vars
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Configuration sections
        self.rabbitmq = RabbitMQConfig()
        self.logging_config = LoggingConfig()
        self.hardware = HardwareConfig()
        self.timing = TimingConfig()
        self.statistics = StatisticsConfig()
        
        # Item data storage
        self._rfid_tags = {
            "locations": {},
            "objects": {}
        }
        
        # Load configuration
        self._load_configuration()
        
        # Apply environment variable overrides
        if self.use_env_vars:
            self._apply_env_overrides()

    def _load_configuration(self):
        """Load configuration from JSON file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                self._parse_config_data(config_data)
                self.logger.info(f"Configuration loaded from {self.config_file}")
            else:
                self.logger.warning(f"Config file {self.config_file} not found")
                if self.auto_create:
                    self._create_default_config()
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing config file: {e}")
            if self.auto_create:
                self._create_default_config()
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            if self.auto_create:
                self._create_default_config()

    def _parse_config_data(self, config_data: Dict[str, Any]):
        """Parse configuration data into structured objects"""
        # Parse RabbitMQ configuration
        if "rabbitmq" in config_data:
            rabbitmq_data = config_data["rabbitmq"]
            self.rabbitmq = RabbitMQConfig(
                host=rabbitmq_data.get("host", self.rabbitmq.host),
                port=rabbitmq_data.get("port", self.rabbitmq.port),
                use_ssl=rabbitmq_data.get("usr_ssl", "False").lower() == "true",  # Note: handles "usr_ssl" typo
                username=rabbitmq_data.get("username"),
                password=rabbitmq_data.get("password"),
                virtual_host=rabbitmq_data.get("virtual_host", self.rabbitmq.virtual_host),
                exchange=rabbitmq_data.get("exchange", self.rabbitmq.exchange),
                queue_name=rabbitmq_data.get("queue_name", self.rabbitmq.queue_name),
                queue_scan_results=rabbitmq_data.get("queue_scan_results", self.rabbitmq.queue_scan_results),
                queue_location_updates=rabbitmq_data.get("queue_location_updates", self.rabbitmq.queue_location_updates),
                routing_key_scan=rabbitmq_data.get("routing_key_scan", self.rabbitmq.routing_key_scan),
                routing_key_update=rabbitmq_data.get("routing_key_update", self.rabbitmq.routing_key_update)
            )

        # Parse logging configuration
        if "logging" in config_data:
            logging_data = config_data["logging"]
            self.logging_config = LoggingConfig(
                level=logging_data.get("level", self.logging_config.level),
                format=logging_data.get("format", self.logging_config.format),
                date_format=logging_data.get("date_format", self.logging_config.date_format),
                file=logging_data.get("file", self.logging_config.file)
            )

        # Parse hardware configuration
        if "hardware" in config_data:
            hardware_data = config_data["hardware"]
            self.hardware = HardwareConfig(
                red_pin=hardware_data.get("red_pin", self.hardware.red_pin),
                green_pin=hardware_data.get("green_pin", self.hardware.green_pin),
                blue_pin=hardware_data.get("blue_pin", self.hardware.blue_pin)
            )

        # Parse timing configuration
        if "timing" in config_data:
            timing_data = config_data["timing"]
            self.timing = TimingConfig(
                read_interval=timing_data.get("read_interval", self.timing.read_interval),
                green_flash_duration=timing_data.get("green_flash_duration", self.timing.green_flash_duration),
                orange_flash_interval=timing_data.get("orange_flash_interval", self.timing.orange_flash_interval)
            )

        # Parse statistics
        if "statistics" in config_data:
            stats_data = config_data["statistics"]
            self.statistics = StatisticsConfig(
                total_tags=stats_data.get("total_tags", self.statistics.total_tags),
                service_starts=stats_data.get("service_starts", self.statistics.service_starts),
                last_scan=stats_data.get("last_scan", self.statistics.last_scan)
            )

        # Parse RFID tags data
        if "rfid_tags" in config_data:
            self._rfid_tags = config_data["rfid_tags"]

        # Legacy support - check for "objects" and "locations" at root level
        if "objects" in config_data:
            self._rfid_tags["objects"] = config_data["objects"]
        if "locations" in config_data:
            self._rfid_tags["locations"] = config_data["locations"]

    def _apply_env_overrides(self):
        """Apply environment variable overrides"""
        # RabbitMQ overrides
        if os.getenv('RABBITMQ_HOST'):
            self.rabbitmq.host = os.getenv('RABBITMQ_HOST') or self.rabbitmq.host
        if os.getenv('RABBITMQ_PORT'):
            try:
                self.rabbitmq.port = int(os.getenv('RABBITMQ_PORT') or self.rabbitmq.port)
            except ValueError:
                self.logger.warning("Invalid RABBITMQ_PORT environment variable")
        if os.getenv('RABBITMQ_USE_SSL'):
            self.rabbitmq.use_ssl = bool(os.getenv('RABBITMQ_USE_SSL')) or self.rabbitmq.use_ssl
        if os.getenv('RABBITMQ_USERNAME'):
            self.rabbitmq.username = os.getenv('RABBITMQ_USERNAME') or self.rabbitmq.username
        if os.getenv('RABBITMQ_PASSWORD'):
            self.rabbitmq.password = os.getenv('RABBITMQ_PASSWORD') or self.rabbitmq.password
        if os.getenv('RABBITMQ_VHOST'):
            self.rabbitmq.virtual_host = os.getenv('RABBITMQ_VHOST') or self.rabbitmq.virtual_host
        if os.getenv('RABBITMQ_EXCHANGE'):
            self.rabbitmq.exchange = os.getenv('RABBITMQ_EXCHANGE') or self.rabbitmq.exchange
        if os.getenv('RABBITMQ_QUEUE'):
            self.rabbitmq.queue_name = os.getenv('RABBITMQ_QUEUE') or self.rabbitmq.queue_name

        # Logging overrides
        if os.getenv('LOG_LEVEL'):
            self.logging_config.level = os.getenv('LOG_LEVEL') or self.logging_config.level
        if os.getenv('LOG_FILE'):
            self.logging_config.file = os.getenv('LOG_FILE') or self.logging_config.file

        self.logger.debug("Environment variable overrides applied")

    def _create_default_config(self):
        """Create a default configuration file"""
        default_config = {
            "rabbitmq": asdict(self.rabbitmq),
            "logging": asdict(self.logging_config),
            "hardware": asdict(self.hardware),
            "timing": asdict(self.timing),
            "statistics": asdict(self.statistics),
            "rfid_tags": {
                "locations": {
                    "OP1": {
                        "name": "OP1",
                        "description": "OP1 Description"
                    },
                    "OP2": {
                        "name": "OP2",
                        "description": "OP2 Description"
                    }
                },
                "objects": {
                    "RFID1": {
                        "name": "RFID1",
                        "category": "Electronics",
                        "serial": "EL001",
                        "description": "EL001 Description"
                    },
                    "RFID2": {
                        "name": "RFID2",
                        "category": "Electronics",
                        "serial": "EL002",
                        "description": "EL002 Description"
                    }
                }
            }
        }

        try:
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            self.logger.info(f"Created default config file: {self.config_file}")
            self._rfid_tags = default_config["rfid_tags"]
        except Exception as e:
            self.logger.error(f"Error creating default config: {e}")

    def get_rabbitmq_config(self) -> Dict[str, Any]:
        """
        Get RabbitMQ configuration as dictionary for MessageTransmitter
        
        Returns:
            Dictionary with RabbitMQ configuration parameters
        """
        return {
            'rabbitmq_host': self.rabbitmq.host,
            'rabbitmq_port': self.rabbitmq.port,
            'rabbitmq_vhost': self.rabbitmq.virtual_host,
            'queue_name': self.rabbitmq.queue_name,
            'exchange_name': self.rabbitmq.exchange,
            'routing_key': self.rabbitmq.routing_key_scan,
            'username': self.rabbitmq.username,
            'password': self.rabbitmq.password,
            'use_ssl': self.rabbitmq.use_ssl,
            'log_file': self.logging_config.file,
            'log_level': getattr(logging, self.logging_config.level.upper(), logging.INFO)
        }

    def get_led_pins(self) -> tuple:
        """
        Get LED pin configuration as tuple
        
        Returns:
            Tuple of (red_pin, green_pin, blue_pin)
        """
        return (self.hardware.red_pin, self.hardware.green_pin, self.hardware.blue_pin)

    def get_item_data(self, item_id: str, item_type: str) -> Optional[Dict[str, Any]]:
        """
        Get item data from configuration
        
        Args:
            item_id: Item identifier
            item_type: Type of item ("object" or "location")
        
        Returns:
            Dictionary with item data or None if not found
        """
        # Handle both singular and plural forms
        section_map = {
            "object": "objects",
            "objects": "objects",
            "location": "locations",
            "locations": "locations"
        }
        
        section = section_map.get(item_type.lower())
        if not section:
            return None
            
        return self._rfid_tags.get(section, {}).get(item_id)

    def add_item(self, item_id: str, item_type: str, item_data: Dict[str, Any]) -> bool:
        """
        Add or update an item in the configuration
        
        Args:
            item_id: Item identifier
            item_type: Type of item ("object" or "location")
            item_data: Item data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        section_map = {
            "object": "objects",
            "objects": "objects", 
            "location": "locations",
            "locations": "locations"
        }
        
        section = section_map.get(item_type.lower())
        if not section:
            return False
            
        if section not in self._rfid_tags:
            self._rfid_tags[section] = {}
            
        self._rfid_tags[section][item_id] = item_data
        self.logger.info(f"Added/updated {item_type} {item_id}")
        return True

    def remove_item(self, item_id: str, item_type: str) -> bool:
        """
        Remove an item from the configuration
        
        Args:
            item_id: Item identifier
            item_type: Type of item ("object" or "location")
            
        Returns:
            True if successful, False otherwise
        """
        section_map = {
            "object": "objects",
            "objects": "objects",
            "location": "locations", 
            "locations": "locations"
        }
        
        section = section_map.get(item_type.lower())
        if not section:
            return False
            
        if section in self._rfid_tags and item_id in self._rfid_tags[section]:
            del self._rfid_tags[section][item_id]
            self.logger.info(f"Removed {item_type} {item_id}")
            return True
        return False

    def get_all_items(self, item_type: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get all items of specified type or all items
        
        Args:
            item_type: Type of item ("object" or "location"), or None for all
            
        Returns:
            Dictionary with all items
        """
        if item_type is None:
            return copy.deepcopy(self._rfid_tags)
            
        section_map = {
            "object": "objects",
            "objects": "objects",
            "location": "locations",
            "locations": "locations"
        }
        
        section = section_map.get(item_type.lower())
        if section and section in self._rfid_tags:
            return copy.deepcopy(self._rfid_tags[section])
        return {}

    def update_statistics(self, **kwargs):
        """
        Update statistics data
        
        Args:
            **kwargs: Statistics to update (total_tags, service_starts, etc.)
        """
        for key, value in kwargs.items():
            if hasattr(self.statistics, key):
                setattr(self.statistics, key, value)
                self.logger.debug(f"Updated statistic {key} = {value}")

    def increment_service_starts(self):
        """Increment the service starts counter"""
        self.statistics.service_starts += 1
        self.logger.info(f"Service starts incremented to {self.statistics.service_starts}")

    def update_last_scan(self, timestamp: Optional[str] = None):
        """
        Update the last scan timestamp
        
        Args:
            timestamp: ISO format timestamp, or None to use current time
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        self.statistics.last_scan = timestamp
        self.logger.debug(f"Updated last scan time: {timestamp}")

    def save_configuration(self) -> bool:
        """
        Save current configuration to file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            config_data = {
                "rabbitmq": asdict(self.rabbitmq),
                "logging": asdict(self.logging_config),
                "hardware": asdict(self.hardware),
                "timing": asdict(self.timing),
                "statistics": asdict(self.statistics),
                "rfid_tags": copy.deepcopy(self._rfid_tags)
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.logger.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False

    def validate_configuration(self) -> list:
        """
        Validate the current configuration
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate RabbitMQ config
        if not self.rabbitmq.host:
            errors.append("RabbitMQ host cannot be empty")
        if not (1 <= self.rabbitmq.port <= 65535):
            errors.append("RabbitMQ port must be between 1 and 65535")
        if not self.rabbitmq.queue_name:
            errors.append("RabbitMQ queue name cannot be empty")
            
        # Validate hardware config
        valid_pins = list(range(1, 41))  # Raspberry Pi GPIO pins
        if self.hardware.red_pin not in valid_pins:
            errors.append(f"Invalid red pin: {self.hardware.red_pin}")
        if self.hardware.green_pin not in valid_pins:
            errors.append(f"Invalid green pin: {self.hardware.green_pin}")
        if self.hardware.blue_pin not in valid_pins:
            errors.append(f"Invalid blue pin: {self.hardware.blue_pin}")
            
        # Check for pin conflicts
        pins = [self.hardware.red_pin, self.hardware.green_pin, self.hardware.blue_pin]
        if len(set(pins)) != len(pins):
            errors.append("LED pins must be unique")
            
        # Validate timing config
        if self.timing.read_interval < 0:
            errors.append("Read interval cannot be negative")
        if self.timing.green_flash_duration < 0:
            errors.append("Green flash duration cannot be negative")
            
        return errors

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current configuration
        
        Returns:
            Dictionary with configuration summary
        """
        return {
            "config_file": self.config_file,
            "rabbitmq_host": self.rabbitmq.host,
            "rabbitmq_port": self.rabbitmq.port,
            "use_ssl": self.rabbitmq.use_ssl,
            "objects_count": len(self._rfid_tags.get("objects", {})),
            "locations_count": len(self._rfid_tags.get("locations", {})),
            "total_service_starts": self.statistics.service_starts,
            "last_scan": self.statistics.last_scan,
            "validation_errors": len(self.validate_configuration())
        }


# Example usage
if __name__ == "__main__":
    # Set up logging for the example
    logging.basicConfig(level=logging.INFO)
    
    # Example 1: Basic usage
    print("Example 1: Basic Configuration Loading")
    config = EnhancedConfigManager("rfid_config.json")
    
    # Print summary
    summary = config.get_summary()
    print(f"Configuration Summary: {summary}")
    
    # Example 2: Get configuration for other components
    print("\nExample 2: Get Configuration for Components")
    rabbitmq_config = config.get_rabbitmq_config()
    print(f"RabbitMQ Config: {rabbitmq_config}")
    
    led_pins = config.get_led_pins()
    print(f"LED Pins: {led_pins}")
    
    # Example 3: Item management
    print("\nExample 3: Item Management")
    
    # Get existing item
    rfid1_data = config.get_item_data("RFID1", "object")
    print(f"RFID1 data: {rfid1_data}")
    
    # Add new item
    new_object = {
        "name": "Test Object",
        "category": "Test",
        "serial": "TEST001",
        "description": "Test object for demonstration"
    }
    config.add_item("TEST_RFID", "object", new_object)
    
    # Get all objects
    all_objects = config.get_all_items("objects")
    print(f"All objects count: {len(all_objects)}")
    
    # Example 4: Statistics management
    print("\nExample 4: Statistics Management")
    config.increment_service_starts()
    config.update_last_scan()
    config.update_statistics(total_tags=50)
    
    print(f"Service starts: {config.statistics.service_starts}")
    print(f"Last scan: {config.statistics.last_scan}")
    print(f"Total tags: {config.statistics.total_tags}")
    
    # Example 5: Configuration validation
    print("\nExample 5: Configuration Validation")
    validation_errors = config.validate_configuration()
    if validation_errors:
        print("Validation errors found:")
        for error in validation_errors:
            print(f"  - {error}")
    else:
        print("Configuration is valid")
    
    # Example 6: Save configuration
    print("\nExample 6: Save Configuration")
    if config.save_configuration():
        print("Configuration saved successfully")
    else:
        print("Failed to save configuration")
