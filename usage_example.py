#!/usr/bin/env python3
"""
Example usage of the Enhanced Configuration Manager
Demonstrates how to use the new configuration system
"""

import logging
import os
from enhanced_config_manager import EnhancedConfigManager

def setup_logging():
    """Set up basic logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def example_basic_usage():
    """Example 1: Basic usage of the configuration manager"""
    print("=" * 50)
    print("Example 1: Basic Configuration Usage")
    print("=" * 50)
    
    # Create configuration manager
    config = EnhancedConfigManager("example_config.json")
    
    # Get configuration summary
    summary = config.get_summary()
    print("Configuration Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Get specific configurations
    rabbitmq_config = config.get_rabbitmq_config()
    print(f"\nRabbitMQ Host: {rabbitmq_config['rabbitmq_host']}")
    print(f"RabbitMQ Port: {rabbitmq_config['rabbitmq_port']}")
    
    led_pins = config.get_led_pins()
    print(f"LED Pins (R,G,B): {led_pins}")

def example_item_management():
    """Example 2: Managing RFID items"""
    print("\n" + "=" * 50)
    print("Example 2: Item Management")
    print("=" * 50)
    
    config = EnhancedConfigManager("example_config.json")
    
    # Add new objects
    print("Adding new objects...")
    config.add_item("WIDGET_001", "object", {
        "name": "Production Widget A",
        "category": "Component",
        "serial": "WGT001",
        "description": "High-precision production widget",
        "weight": 0.5,
        "dimensions": {"length": 10, "width": 5, "height": 2}
    })
    
    config.add_item("TOOL_001", "object", {
        "name": "Calibration Tool",
        "category": "Tool",
        "serial": "CAL001",
        "description": "Precision calibration instrument",
        "calibration_date": "2024-01-15",
        "accuracy": "±0.001mm"
    })
    
    # Add new locations
    print("Adding new locations...")
    config.add_item("STATION_A", "location", {
        "name": "Assembly Station Alpha",
        "description": "Primary assembly workstation",
        "zone": "Production Floor",
        "capacity": 25,
        "coordinates": {"x": 10.5, "y": 20.3, "z": 0.0},
        "equipment": ["conveyor", "robot_arm", "quality_scanner"]
    })
    
    config.add_item("STORAGE_B1", "location", {
        "name": "Storage Bay B1",
        "description": "Climate controlled storage",
        "zone": "Warehouse",
        "capacity": 100,
        "temperature_controlled": True,
        "humidity_controlled": True
    })
    
    # List all objects
    print("\nAll Objects:")
    objects = config.get_all_items("objects")
    for obj_id, obj_data in objects.items():
        print(f"  {obj_id}: {obj_data.get('name', 'Unknown')}")
    
    # List all locations
    print("\nAll Locations:")
    locations = config.get_all_items("locations")
    for loc_id, loc_data in locations.items():
        print(f"  {loc_id}: {loc_data.get('name', 'Unknown')}")
    
    # Get specific item data
    widget_data = config.get_item_data("WIDGET_001", "object")
    print(f"\nWidget data: {widget_data}")
    
    # Save configuration
    config.save_configuration()
    print("\nConfiguration saved!")

def example_statistics_tracking():
    """Example 3: Statistics tracking"""
    print("\n" + "=" * 50)
    print("Example 3: Statistics Tracking")
    print("=" * 50)
    
    config = EnhancedConfigManager("example_config.json")
    
    # Update statistics
    print("Updating statistics...")
    config.increment_service_starts()
    config.update_last_scan()
    config.update_statistics(total_tags=42)
    
    # Print current statistics
    print(f"Service starts: {config.statistics.service_starts}")
    print(f"Total tags scanned: {config.statistics.total_tags}")
    print(f"Last scan time: {config.statistics.last_scan}")
    
    # Save updated statistics
    config.save_configuration()

def example_environment_variables():
    """Example 4: Using environment variables"""
    print("\n" + "=" * 50)
    print("Example 4: Environment Variable Override")
    print("=" * 50)
    
    # Set some environment variables for demonstration
    os.environ['RABBITMQ_HOST'] = 'production.rabbitmq.com'
    os.environ['RABBITMQ_PORT'] = '5671'
    os.environ['RABBITMQ_USE_SSL'] = 'true'
    os.environ['RABBITMQ_USERNAME'] = 'prod_user'
    os.environ['LOG_LEVEL'] = 'WARNING'
    
    # Create config manager (will automatically apply env overrides)
    config = EnhancedConfigManager("example_config.json", use_env_vars=True)
    
    print("Configuration with environment overrides:")
    print(f"  RabbitMQ Host: {config.rabbitmq.host}")
    print(f"  RabbitMQ Port: {config.rabbitmq.port}")
    print(f"  SSL Enabled: {config.rabbitmq.use_ssl}")
    print(f"  Username: {config.rabbitmq.username}")
    print(f"  Log Level: {config.logging_config.level}")
    
    # Clean up environment variables
    for var in ['RABBITMQ_HOST', 'RABBITMQ_PORT', 'RABBITMQ_USE_SSL', 'RABBITMQ_USERNAME', 'LOG_LEVEL']:
        if var in os.environ:
            del os.environ[var]

def example_validation():
    """Example 5: Configuration validation"""
    print("\n" + "=" * 50)
    print("Example 5: Configuration Validation")
    print("=" * 50)
    
    config = EnhancedConfigManager("example_config.json")
    
    # Validate current configuration
    errors = config.validate_configuration()
    
    if errors:
        print("Validation errors found:")
        for error in errors:
            print(f"  ✗ {error}")
    else:
        print("✓ Configuration is still valid!")

def example_scanner_integration():
    """Example 6: Integration with RFID scanner"""
    print("\n" + "=" * 50)
    print("Example 6: Scanner Integration")
    print("=" * 50)
    
    try:
        # This would normally import your updated scanner
        # from updated_rfid_rabbitmq import RFIDRabbitMQScanner
        
        print("Creating RFID scanner with enhanced configuration...")
        
        # Simulate scanner creation
        config = EnhancedConfigManager("example_config.json")
        
        print("Scanner configuration:")
        rabbitmq_config = config.get_rabbitmq_config()
        led_pins = config.get_led_pins()
        
        print(f"  RabbitMQ: {rabbitmq_config['rabbitmq_host']}:{rabbitmq_config['rabbitmq_port']}")
        print(f"  LED Pins: R={led_pins[0]}, G={led_pins[1]}, B={led_pins[2]}")
        print(f"  Read Interval: {config.timing.read_interval}s")
        print(f"  Flash Duration: {config.timing.green_flash_duration}s")
        
        # Show available items
        objects = config.get_all_items("objects")
        locations = config.get_all_items("locations")
        print(f"  Available Objects: {len(objects)}")
        print(f"  Available Locations: {len(locations)}")
        
        # Would normally create scanner like this:
        # scanner = RFIDRabbitMQScanner(config_file="example_config.json")
        # scanner.run()
        
        print("Scanner would be ready to run!")
        
    except ImportError as e:
        print(f"Scanner import not available (this is expected): {e}")

def example_configuration_comparison():
    """Example 7: Compare old vs new configuration approach"""
    print("\n" + "=" * 50)
    print("Example 7: Old vs New Configuration Approach")
    print("=" * 50)
    
    print("OLD APPROACH:")
    print("""
    # Old way - manual JSON loading and parsing
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    rabbitmq_host = config['rabbitmq']['host']
    rabbitmq_port = config['rabbitmq']['port']
    red_pin = config['hardware']['red_pin']
    
    # No validation, no environment overrides, no type safety
    """)
    
    print("NEW APPROACH:")
    print("""
    # New way - structured configuration with validation
    config = EnhancedConfigManager('config.json')
    
    # Type-safe access with defaults
    rabbitmq_config = config.get_rabbitmq_config()
    led_pins = config.get_led_pins()
    
    # Built-in validation
    errors = config.validate_configuration()
    
    # Automatic environment variable overrides
    # Statistics tracking and item management
    # Automatic backup and migration support
    """)

def example_advanced_usage():
    """Example 8: Advanced configuration features"""
    print("\n" + "=" * 50)
    print("Example 8: Advanced Features")
    print("=" * 50)
    
    config = EnhancedConfigManager("example_config.json")
    
    # Demonstrate dynamic configuration changes
    print("Dynamic configuration changes:")
    
    # Change timing settings
    original_interval = config.timing.read_interval
    config.timing.read_interval = 1.5
    print(f"  Read interval changed from {original_interval}s to {config.timing.read_interval}s")
    
    # Add items programmatically based on conditions
    import random
    for i in range(3):
        item_id = f"AUTO_ITEM_{i:03d}"
        item_data = {
            "name": f"Auto-generated Item {i}",
            "category": "Auto",
            "serial": f"AUTO{i:03d}",
            "description": f"Automatically generated test item #{i}",
            "priority": random.choice(["low", "medium", "high"]),
            "created_timestamp": config.statistics.last_scan or "unknown"
        }
        config.add_item(item_id, "object", item_data)
        print(f"  Added {item_id}")
    
    # Batch operations
    print(f"\nBatch statistics:")
    print(f"  Total objects: {len(config.get_all_items('objects'))}")
    print(f"  Total locations: {len(config.get_all_items('locations'))}")
    
    # Configuration export for debugging
    print(f"\nConfiguration file: {config.config_file}")
    print(f"Service starts: {config.statistics.service_starts}")
    
    # Save all changes
    config.save_configuration()
    print("All changes saved!")

def run_all_examples():
    """Run all examples in sequence"""
    setup_logging()
    
    print("Enhanced Configuration Manager Examples")
    print("=" * 60)
    
    try:
        example_basic_usage()
        example_item_management()
        example_statistics_tracking()
        example_environment_variables()
        example_validation()
        example_scanner_integration()
        example_configuration_comparison()
        example_advanced_usage()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("\nNext steps:")
        print("1. Run the migration script if you have an existing config")
        print("2. Update your imports to use EnhancedConfigManager")
        print("3. Test with your RFID scanner hardware")
        print("4. Customize the configuration for your environment")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()

def interactive_demo():
    """Interactive demonstration of the configuration manager"""
    print("\n" + "=" * 50)
    print("Interactive Configuration Demo")
    print("=" * 50)
    
    config = EnhancedConfigManager("interactive_demo_config.json")
    
    while True:
        print("\nConfiguration Manager Demo Menu:")
        print("1. View configuration summary")
        print("2. Add new object")
        print("3. Add new location")
        print("4. List all items")
        print("5. Update statistics")
        print("6. Validate configuration")
        print("7. Save configuration")
        print("0. Exit")
        
        try:
            choice = input("\nEnter your choice (0-7): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                summary = config.get_summary()
                print("\nConfiguration Summary:")
                for key, value in summary.items():
                    print(f"  {key}: {value}")
            
            elif choice == "2":
                item_id = input("Enter object ID: ").strip()
                name = input("Enter object name: ").strip()
                category = input("Enter category: ").strip()
                description = input("Enter description: ").strip()
                
                item_data = {
                    "name": name,
                    "category": category,
                    "description": description,
                    "serial": f"SER_{item_id}",
                    "added_via": "interactive_demo"
                }
                
                if config.add_item(item_id, "object", item_data):
                    print(f"✓ Added object {item_id}")
                else:
                    print(f"✗ Failed to add object {item_id}")
            
            elif choice == "3":
                item_id = input("Enter location ID: ").strip()
                name = input("Enter location name: ").strip()
                zone = input("Enter zone: ").strip()
                description = input("Enter description: ").strip()
                
                item_data = {
                    "name": name,
                    "description": description,
                    "zone": zone,
                    "capacity": 50,
                    "added_via": "interactive_demo"
                }
                
                if config.add_item(item_id, "location", item_data):
                    print(f"✓ Added location {item_id}")
                else:
                    print(f"✗ Failed to add location {item_id}")
            
            elif choice == "4":
                print("\nAll Objects:")
                objects = config.get_all_items("objects")
                for obj_id, obj_data in objects.items():
                    print(f"  {obj_id}: {obj_data.get('name', 'Unknown')}")
                
                print("\nAll Locations:")
                locations = config.get_all_items("locations")
                for loc_id, loc_data in locations.items():
                    print(f"  {loc_id}: {loc_data.get('name', 'Unknown')}")
            
            elif choice == "5":
                config.increment_service_starts()
                config.update_last_scan()
                print("✓ Statistics updated")
            
            elif choice == "6":
                errors = config.validate_configuration()
                if errors:
                    print("Validation errors:")
                    for error in errors:
                        print(f"  ✗ {error}")
                else:
                    print("✓ Configuration is valid!")
            
            elif choice == "7":
                if config.save_configuration():
                    print("✓ Configuration saved!")
                else:
                    print("✗ Failed to save configuration")
            
            else:
                print("Invalid choice. Please try again.")
                
        except KeyboardInterrupt:
            print("\n\nExiting demo...")
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("Demo completed!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_demo()
    else:
        run_all_examples()
        
        # Offer interactive demo
        response = input("\nWould you like to try the interactive demo? (y/N): ").strip().lower()
        if response == 'y':
            interactive_demo()
    
    if errors:
        print("Validation errors found:")
        for error in errors:
            print(f"  ✗ {error}")
    else:
        print("✓ Configuration is valid!")
    
    # Demonstrate invalid configuration
    print("\nTesting with invalid configuration...")
    config.rabbitmq.port = 99999  # Invalid port
    config.hardware.red_pin = 99  # Invalid GPIO pin
    
    errors = config.validate_configuration()
