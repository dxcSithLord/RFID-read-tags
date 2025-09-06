#!/usr/bin/env python3
"""
Configuration Migration Script
Migrates old rfid_config.json to work with EnhancedConfigManager
"""

import json
import logging
import os
import shutil
from datetime import datetime
from typing import Dict, Any

def backup_config_file(config_file: str) -> str:
    """
    Create a backup of the existing configuration file
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        Path to backup file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{config_file}.backup_{timestamp}"
    
    if os.path.exists(config_file):
        shutil.copy2(config_file, backup_file)
        print(f"Backup created: {backup_file}")
        return backup_file
    else:
        print(f"Config file {config_file} not found - no backup needed")
        return ""

def load_old_config(config_file: str) -> Dict[str, Any]:
    """
    Load the old configuration format
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        Dictionary with old configuration data
    """
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Configuration file {config_file} not found")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing configuration file: {e}")
        return {}

def migrate_config_data(old_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate old configuration format to new enhanced format
    
    Args:
        old_config: Old configuration dictionary
        
    Returns:
        New configuration dictionary
    """
    # Start with default structure
    new_config = {
        "rabbitmq": {
            "host": "localhost",
            "port": 5672,
            "use_ssl": False,
            "username": None,
            "password": None,
            "virtual_host": "/",
            "exchange": "",
            "queue_name": "rfid_messages",
            "queue_scan_results": "scan_results",
            "queue_location_updates": "location_updates",
            "routing_key_scan": "rfid.scan.result",
            "routing_key_update": "asset.location.update"
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(levelname)s - %(message)s",
            "date_format": "%Y-%m-%d %H:%M:%S",
            "file": None
        },
        "hardware": {
            "red_pin": 12,
            "green_pin": 13,
            "blue_pin": 19
        },
        "timing": {
            "read_interval": 2.0,
            "green_flash_duration": 2.0
        },
        "statistics": {
            "total_tags": 0,
            "service_starts": 0,
            "last_scan": None
        },
        "rfid_tags": {
            "locations": {},
            "objects": {}
        }
    }
    
    # Migrate RabbitMQ configuration
    if "rabbitmq" in old_config:
        rabbitmq_old = old_config["rabbitmq"]
        new_config["rabbitmq"].update({
            "host": rabbitmq_old.get("host", "localhost"),
            "port": rabbitmq_old.get("port", 5672),
            "use_ssl": str(rabbitmq_old.get("usr_ssl", "False")).lower() == "true",  # Handle typo
            "username": rabbitmq_old.get("username"),
            "password": rabbitmq_old.get("password"),
            "virtual_host": rabbitmq_old.get("virtual_host", "/"),
            "exchange": rabbitmq_old.get("exchange", ""),
            "queue_name": rabbitmq_old.get("queue_name", "rfid_messages"),
            "queue_scan_results": rabbitmq_old.get("queue_scan_results", "scan_results"),
            "queue_location_updates": rabbitmq_old.get("queue_location_updates", "location_updates"),
            "routing_key_scan": rabbitmq_old.get("routing_key_scan", "rfid.scan.result"),
            "routing_key_update": rabbitmq_old.get("routing_key_update", "asset.location.update")
        })
        print("✓ Migrated RabbitMQ configuration")
    
    # Migrate logging configuration
    if "logging" in old_config:
        logging_old = old_config["logging"]
        new_config["logging"].update({
            "level": logging_old.get("level", "INFO"),
            "format": logging_old.get("format", "%(asctime)s - %(levelname)s - %(message)s"),
            "date_format": logging_old.get("date_format", "%Y-%m-%d %H:%M:%S"),
            "file": logging_old.get("file")
        })
        print("✓ Migrated logging configuration")
    
    # Migrate hardware configuration
    if "hardware" in old_config:
        hardware_old = old_config["hardware"]
        new_config["hardware"].update({
            "red_pin": hardware_old.get("red_pin", 12),
            "green_pin": hardware_old.get("green_pin", 13),
            "blue_pin": hardware_old.get("blue_pin", 19)
        })
        print("✓ Migrated hardware configuration")
    
    # Migrate timing configuration
    if "timing" in old_config:
        timing_old = old_config["timing"]
        new_config["timing"].update({
            "read_interval": timing_old.get("read_interval", 2.0),
            "green_flash_duration": timing_old.get("green_flash_duration", 2.0)
        })
        print("✓ Migrated timing configuration")
    
    # Migrate statistics
    if "statistics" in old_config:
        stats_old = old_config["statistics"]
        new_config["statistics"].update({
            "total_tags": stats_old.get("total_tags", 0),
            "service_starts": stats_old.get("service_starts", 0),
            "last_scan": stats_old.get("last_scan")
        })
        print("✓ Migrated statistics")
    
    # Migrate RFID tags data
    # Check for new format first
    if "rfid_tags" in old_config:
        new_config["rfid_tags"] = old_config["rfid_tags"]
        print("✓ Migrated RFID tags (new format)")
    else:
        # Check for old format with separate objects and locations
        if "objects" in old_config:
            new_config["rfid_tags"]["objects"] = old_config["objects"]
            print("✓ Migrated objects from old format")
        
        if "locations" in old_config:
            new_config["rfid_tags"]["locations"] = old_config["locations"]
            print("✓ Migrated locations from old format")
    
    return new_config

def save_migrated_config(new_config: Dict[str, Any], config_file: str) -> bool:
    """
    Save the migrated configuration to file
    
    Args:
        new_config: New configuration dictionary
        config_file: Path to configuration file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(config_file, 'w') as f:
            json.dump(new_config, f, indent=2)
        print(f"✓ Migrated configuration saved to {config_file}")
        return True
    except Exception as e:
        print(f"✗ Error saving migrated configuration: {e}")
        return False

def validate_migration(config_file: str) -> bool:
    """
    Validate the migrated configuration
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Try to import and use the enhanced config manager
        from enhanced_config_manager import EnhancedConfigManager
        
        config = EnhancedConfigManager(config_file, auto_create=False)
        errors = config.validate_configuration()
        
        if errors:
            print("⚠ Validation warnings found:")
            for error in errors:
                print(f"    - {error}")
        else:
            print("✓ Configuration validation passed")
        
        # Print summary
        summary = config.get_summary()
        print("\nMigration Summary:")
        print(f"  Objects: {summary['objects_count']}")
        print(f"  Locations: {summary['locations_count']}")
        print(f"  RabbitMQ Host: {summary['rabbitmq_host']}")
        print(f"  RabbitMQ Port: {summary['rabbitmq_port']}")
        print(f"  SSL Enabled: {summary['use_ssl']}")
        
        return len(errors) == 0
        
    except ImportError:
        print("⚠ Cannot validate migration - enhanced_config_manager not found")
        return False
    except Exception as e:
        print(f"✗ Validation error: {e}")
        return False

def main():
    """Main migration function"""
    print("RFID Configuration Migration Tool")
    print("=" * 40)
    
    # Configuration file path
    config_file = input("Enter config file path (default: rfid_config.json): ").strip()
    if not config_file:
        config_file = "rfid_config.json"
    
    if not os.path.exists(config_file):
        print(f"Configuration file {config_file} not found!")
        return
    
    print(f"\nMigrating configuration file: {config_file}")
    
    # Create backup
    backup_file = backup_config_file(config_file)
    
    # Load old configuration
    print("\nLoading old configuration...")
    old_config = load_old_config(config_file)
    if not old_config:
        print("No configuration data found to migrate")
        return
    
    # Migrate configuration
    print("\nMigrating configuration...")
    new_config = migrate_config_data(old_config)
    
    # Ask for confirmation before saving
    print(f"\nReady to save migrated configuration to {config_file}")
    if backup_file:
        print(f"Original backed up as: {backup_file}")
    
    confirm = input("Continue? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Migration cancelled")
        return
    
    # Save migrated configuration
    if save_migrated_config(new_config, config_file):
        print("\n" + "=" * 40)
        print("Migration completed successfully!")
        
        # Validate migration
        print("\nValidating migrated configuration...")
        validate_migration(config_file)
        
        print("\nMigration Notes:")
        print("- The old configuration has been backed up")
        print("- You can now use EnhancedConfigManager with your existing code")
        print("- Update your imports to use the new configuration manager")
        print("- Test the migrated configuration thoroughly")
        
    else:
        print("Migration failed!")
        if backup_file and os.path.exists(backup_file):
            print(f"Restoring from backup: {backup_file}")
            shutil.copy2(backup_file, config_file)

if __name__ == "__main__":
    main()
