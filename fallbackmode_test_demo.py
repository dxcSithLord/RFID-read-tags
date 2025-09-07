#!/usr/bin/env python3
"""
Fallback Mode Test Demo
Demonstrates RabbitMQ fallback functionality with file storage
"""

import time
import json
import logging
from pathlib import Path
import rabbitmq_etx 
import enhanced_config_manager

def setup_demo_environment():
    """Set up demo configuration and logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create demo configuration
    demo_config = {
        "rabbitmq": {
            "host": "nonexistent-rabbitmq-server.local",  # Intentionally invalid host
            "port": 5672,
            "use_ssl": False,
            "username": None,
            "password": None,
            "virtual_host": "/",
            "exchange": "",
            "queue_name": "demo_fallback_queue",
            "queue_scan_results": "scan_results",
            "queue_location_updates": "location_updates",
            "routing_key_scan": "demo.scan.result",
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
            "read_interval": 1.0,
            "green_flash_duration": 2.0,
            "orange_flash_interval": 0.5
        },
        "statistics": {
            "total_tags": 0,
            "service_starts": 0,
            "last_scan": None
        },
        "rfid_tags": {
            "locations": {
                "DEMO_LOC1": {
                    "name": "Demo Location 1",
                    "description": "Test location for demo"
                },
                "DEMO_LOC2": {
                    "name": "Demo Location 2", 
                    "description": "Another test location"
                }
            },
            "objects": {
                "DEMO_OBJ1": {
                    "name": "Demo Object 1",
                    "category": "Test",
                    "serial": "TEST001",
                    "description": "Test object for demo"
                },
                "DEMO_OBJ2": {
                    "name": "Demo Object 2",
                    "category": "Test",
                    "serial": "TEST002",
                    "description": "Another test object"
                }
            }
        }
    }
    
    # Save demo configuration
    with open('demo_fallback_config.json', 'w') as f:
        json.dump(demo_config, f, indent=2)
    
    print("Demo environment set up successfully!")
    return 'demo_fallback_config.json'

def demo_fallback_messaging():
    """Demonstrate fallback messaging functionality"""
    print("\n" + "=" * 60)
    print("RabbitMQ Fallback Mode Demo")
    print("=" * 60)
    
    # Status tracking
    connection_status = {"connected": False, "changes": 0}
    
    def status_callback(connected: bool):
        """Track connection status changes"""
        connection_status["connected"] = connected
        connection_status["changes"] += 1
        status = "CONNECTED" if connected else "DISCONNECTED (Fallback Mode)"
        print(f"\n🔄 RabbitMQ Status: {status}")
    
    # Create enhanced transmitter with invalid host (to force fallback)
    print("Creating message transmitter with invalid RabbitMQ host...")
    transmitter = rabbitmq_etx.EnhancedMessageTransmitter(
        rabbitmq_host='invalid-host-for-demo.local',
        rabbitmq_port=5672,
        queue_name='demo_fallback_queue',
        status_callback=status_callback,
        connection_timeout=2.0,  # Quick timeout for demo
        retry_interval=5.0,      # Quick retry for demo
        fallback_file_dir='demo_fallback'
    )
    
    # Wait a moment for connection attempt
    time.sleep(3)
    
    # Show initial status
    status = transmitter.get_status()
    print(f"\nInitial Status:")
    print(f"  Connected: {status['connected']}")
    print(f"  Fallback file: {status['fallback_file']}")
    print(f"  Queued messages: {status['fallback_messages']}")
    
    # Send test messages in fallback mode
    print(f"\n📤 Sending messages in fallback mode...")
    
    test_messages = [
        {
            "scan_type": "demo",
            "object_id": "DEMO_OBJ1",
            "location_id": "DEMO_LOC1",
            "action": "object_placement",
            "timestamp": time.time()
        },
        {
            "scan_type": "demo", 
            "object_id": "DEMO_OBJ2",
            "location_id": "DEMO_LOC2",
            "action": "object_movement",
            "timestamp": time.time()
        },
        {
            "scan_type": "demo",
            "alert": "low_battery",
            "scanner_id": "demo_scanner",
            "timestamp": time.time()
        }
    ]
    
    sent_messages = []
    for i, message in enumerate(test_messages):
        try:
            result = transmitter.transmit_message(message)
            sent_messages.append(result)
            method = result.get('_transmission_method', 'unknown')
            print(f"  ✓ Message {i+1} sent via {method}")
            time.sleep(1)  # Small delay between messages
        except Exception as e:
            print(f"  ✗ Error sending message {i+1}: {e}")
    
    # Show fallback file contents
    status = transmitter.get_status()
    print(f"\n📁 Fallback Status:")
    print(f"  Queued messages: {status['fallback_messages']}")
    print(f"  Fallback file: {status['fallback_file']}")
    
    if status['fallback_messages'] > 0:
        fallback_file = Path(status['fallback_file'])
        if fallback_file.exists():
            print(f"  File size: {fallback_file.stat().st_size} bytes")
            
            # Show first few lines of fallback file
            with open(fallback_file, 'r') as f:
                content = f.read()
                lines = content.split('\n')[:10]  # First 10 lines
                print(f"  File preview (first 10 lines):")
                for line in lines:
                    if line.strip():
                        print(f"    {line}")
    
    # Simulate RabbitMQ coming back online (for demo purposes)
    print(f"\n🔧 Simulating RabbitMQ recovery (this would happen automatically)...")
    print("   In real scenarios, the transmitter would detect when RabbitMQ is available")
    print("   and automatically process queued messages from the fallback file.")
    
    # Show final statistics
    print(f"\n📊 Demo Summary:")
    print(f"  Messages sent: {len(sent_messages)}")
    print(f"  Connection status changes: {connection_status['changes']}")
    print(f"  Final connection status: {'Connected' if connection_status['connected'] else 'Disconnected'}")
    print(f"  Fallback messages queued: {status['fallback_messages']}")
    
    # Cleanup
    transmitter.close_connection()
    
    return status

def demo_rfid_scanner_fallback():
    """Demonstrate RFID scanner with fallback mode"""
    print("\n" + "=" * 60)
    print("RFID Scanner Fallback Mode Demo")
    print("=" * 60)
    
    try:
        # Import the updated scanner
        from rfid_rabbitmq_e import RFIDRabbitMQScanner
        
        # Create scanner in test mode with demo config
        print("Creating RFID scanner in test mode...")
        scanner = RFIDRabbitMQScanner(
            config_file='demo_fallback_config.json',
            test_mode=True
        )
        
        # Show scanner status
        status = scanner.get_status()
        print(f"\nScanner Status:")
        print(f"  Test Mode: {status['test_mode']}")
        print(f"  RabbitMQ Connected: {status['rabbitmq_connected']}")
        print(f"  Fallback Messages: {status['fallback_messages']}")
        print(f"  Objects Available: {status['objects_count']}")
        print(f"  Locations Available: {status['locations_count']}")
        
        # Demonstrate LED color behavior
        print(f"\n💡 LED Status Indication:")
        if status['rabbitmq_connected']:
            print("  - Steady WHITE light when waiting for RFID tag (normal operation)")
        else:
            print("  - Flashing ORANGE light when waiting for RFID tag (fallback mode)")
        
        print(f"\n🏷️ Simulating RFID scans...")
        print("  (In test mode, scans are simulated automatically)")
        
        # Run a few scan cycles
        scan_count = 0
        max_scans = 3
        
        print(f"\nRunning {max_scans} scan cycles...")
        while scan_count < max_scans:
            try:
                success = scanner.run_once()
                scan_count += 1
                
                if success:
                    print(f"  ✓ Scan cycle {scan_count}: Message sent successfully")
                else:
                    print(f"  - Scan cycle {scan_count}: Waiting for complete object+location pair")
                
                time.sleep(2)  # Wait between scans
                
            except Exception as e:
                print(f"  ✗ Scan cycle {scan_count} error: {e}")
                break
        
        # Show final status
        final_status = scanner.get_status()
        print(f"\n📊 Final Scanner Status:")
        print(f"  Total scans completed: {scan_count}")
        print(f"  Total tags processed: {final_status['total_tags_scanned']}")
        print(f"  Fallback messages: {final_status['fallback_messages']}")
        print(f"  Last scan: {final_status['last_scan']}")
        
        # Cleanup
        scanner.cleanup()
        
        return final_status
        
    except ImportError as e:
        print(f"Could not import RFID scanner: {e}")
        print("Make sure all required files are in the same directory")
        return None

def demo_file_examination():
    """Examine fallback files created during demo"""
    print("\n" + "=" * 60)
    print("Fallback File Examination")
    print("=" * 60)
    
    fallback_dir = Path('demo_fallback')
    if not fallback_dir.exists():
        print("No fallback directory found.")
        return
    
    print(f"Examining fallback directory: {fallback_dir}")
    
    # List all files in fallback directory
    files = list(fallback_dir.glob('*'))
    if not files:
        print("No fallback files found.")
        return
    
    print(f"Found {len(files)} files:")
    
    for file_path in files:
        print(f"\n📄 File: {file_path.name}")
        print(f"   Size: {file_path.stat().st_size} bytes")
        print(f"   Modified: {time.ctime(file_path.stat().st_mtime)}")
        
        if file_path.suffix == '.json':
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    print(f"   Messages: {len(data)}")
                    
                    # Show summary of first message
                    if data and len(data) > 0:
                        first_msg = data[0]
                        print(f"   First message preview:")
                        print(f"     Timestamp: {first_msg.get('fallback_timestamp', 'N/A')}")
                        print(f"     Reason: {first_msg.get('fallback_reason', 'N/A')}")
                        
                        original = first_msg.get('original_message', {})
                        if original:
                            print(f"     Original message type: {original.get('scan_type', 'N/A')}")
                
            except Exception as e:
                print(f"   Error reading file: {e}")

def cleanup_demo_files():
    """Clean up demo files"""
    print("\n" + "=" * 60)
    print("Cleanup Demo Files")
    print("=" * 60)
    
    files_to_remove = [
        'demo_fallback_config.json',
        Path('demo_fallback')
    ]
    
    for file_path in files_to_remove:
        try:
            if isinstance(file_path, str):
                file_path = Path(file_path)
            
            if file_path.is_file():
                file_path.unlink()
                print(f"✓ Removed file: {file_path}")
            elif file_path.is_dir():
                # Remove directory and all contents
                for child in file_path.rglob('*'):
                    if child.is_file():
                        child.unlink()
                for child in sorted(file_path.rglob('*'), reverse=True):
                    if child.is_dir():
                        child.rmdir()
                file_path.rmdir()
                print(f"✓ Removed directory: {file_path}")
            else:
                print(f"- File not found: {file_path}")
                
        except Exception as e:
            print(f"✗ Error removing {file_path}: {e}")

def main():
    """Run the complete fallback demo"""
    print("RabbitMQ Fallback Mode Demonstration")
    print("=" * 80)
    print("This demo shows how the system handles RabbitMQ service unavailability:")
    print("1. Messages are automatically stored in fallback files")
    print("2. LED indicators show connection status")
    print("3. Normal operation resumes when RabbitMQ is available")
    print("=" * 80)
    
    try:
        # Setup demo environment
        config_file = setup_demo_environment()
        
        # Run demos
        demo_fallback_messaging()
        demo_rfid_scanner_fallback()
        demo_file_examination()
        
        # Ask about cleanup
        response = input("\nWould you like to clean up demo files? (y/N): ").strip().lower()
        if response == 'y':
            cleanup_demo_files()
        else:
            print("Demo files left in place for examination")
            print("Run with --cleanup to remove them later")
        
        print("\n✓ Demo completed successfully!")
        print("\nKey takeaways:")
        print("- System gracefully handles RabbitMQ unavailability")
        print("- Messages are never lost (stored in fallback files)")
        print("- LED colors indicate system status")
        print("- Automatic recovery when service returns")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\nDemo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--cleanup':
        cleanup_demo_files()
    else:
        main()
