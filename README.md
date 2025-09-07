# Enhanced RFID RabbitMQ Scanner with Fallback Support

A robust RFID scanning system with RabbitMQ messaging and automatic fallback to file storage when the message service is unavailable.

## 🆕 New Features

### RabbitMQ Fallback Support
- **Automatic Fallback**: When RabbitMQ is unavailable, messages are automatically saved to local files
- **Queue Recovery**: Messages are automatically sent when RabbitMQ becomes available again  
- **No Message Loss**: All scan data is preserved even during service outages
- **Connection Monitoring**: Background monitoring with automatic reconnection attempts

### Enhanced LED Status Indicators
- **Normal Operation**: Steady **WHITE** light when waiting for RFID tag
- **Fallback Mode**: Flashing **ORANGE** light when waiting for RFID tag
- **Object Scanned**: Flash **YELLOW** when object is detected
- **Location Scanned**: Flash **BLUE** when location is detected
- **Message Ready**: Flash **GREEN** when both object and location are scanned
- **Message Sent**: Solid **PURPLE** for 2 seconds after successful transmission
- **Error State**: Flash **RED** for read failures or errors

### Test Mode Support
- **Simulation Mode**: Run without physical RFID hardware for testing
- **Command Line Arguments**: Enable test mode with `--test` flag
- **Configurable Timing**: Adjustable simulation delays and flash intervals

### Enhanced Configuration Management
- **Structured Configuration**: Type-safe configuration with validation
- **Environment Variable Support**: Override config with environment variables
- **Statistics Tracking**: Automatic tracking of scans, service starts, and timestamps
- **Dynamic Item Management**: Add/remove RFID items without code changes

## 📁 File Structure

```
rfid_scanner/
├── enhanced_config_manager.py      # Enhanced configuration management
├── enhanced_rabbitmq_tx.py         # RabbitMQ transmitter with fallback
├── updated_rfid_rabbitmq.py        # Main RFID scanner (updated)
├── config_migration.py             # Migration script for existing configs
├── test_fallback_demo.py          # Fallback functionality demo
├── usage_example.py               # Configuration usage examples
├── rfid_config.json               # Configuration file
└── rabbitmq_fallback/             # Fallback message storage directory
    └── {queue_name}_messages.json  # Queued messages when RabbitMQ unavailable
```

## 🚀 Quick Start

### Installation

```bash
# Install required packages
pip install mfrc522 gpiozero colorzero pika

# Clone or download the enhanced scanner files
# Make sure all Python files are in the same directory
```

### Basic Usage

```bash
# Run in normal mode
python updated_rfid_rabbitmq.py

# Run in test mode (no physical RFID hardware required)
python updated_rfid_rabbitmq.py --test

# Show current status
python updated_rfid_rabbitmq.py --status

# Validate configuration
python updated_rfid_rabbitmq.py --validate
```

### Migration from Old Version

```bash
# Migrate existing configuration (creates backup automatically)
python config_migration.py
```

## ⚙️ Configuration

### Environment Variables

Override configuration with environment variables:

```bash
export RABBITMQ_HOST=production.example.com
export RABBITMQ_PORT=5671
export RABBITMQ_USE_SSL=true
export RABBITMQ_USERNAME=prod_user
export RABBITMQ_PASSWORD=secure_password
export LOG_LEVEL=WARNING
```

### Configuration File Format

```json
{
  "rabbitmq": {
    "host": "localhost",
    "port": 5672,
    "use_ssl": false,
    "username": null,
    "password": null,
    "virtual_host": "/",
    "exchange": "asset_tracking",
    "queue_name": "rfid_scans",
    "routing_key_scan": "rfid.scan.result"
  },
  "hardware": {
    "red_pin": 12,
    "green_pin": 13,
    "blue_pin": 19
  },
  "timing": {
    "read_interval": 2.0,
    "green_flash_duration": 2.0,
    "orange_flash_interval": 1.0
  },
  "rfid_tags": {
    "objects": {
      "RFID1": {
        "name": "Production Widget",
        "category": "Component",
        "serial": "WGT001"
      }
    },
    "locations": {
      "OP1": {
        "name": "Assembly Station 1",
        "description": "Primary assembly workstation"
      }
    }
  }
}
```

## 🔄 Fallback Mode Operation

### When RabbitMQ is Unavailable

1. **Automatic Detection**: System detects RabbitMQ unavailability within 5 seconds
2. **LED Indication**: Orange flashing light indicates fallback mode
3. **File Storage**: Messages saved to `rabbitmq_fallback/{queue_name}_messages.json`
4. **Continued Operation**: Scanner continues to work normally
5. **Background Monitoring**: System checks for RabbitMQ recovery every 30 seconds

### When RabbitMQ Returns

1. **Automatic Detection**: System detects RabbitMQ availability
2. **LED Indication**: Returns to steady white light
3. **Message Processing**: Queued messages are automatically sent
4. **Normal Operation**: System resumes normal RabbitMQ messaging

### Fallback File Format

```json
[
  {
    "original_message": {
      "timestamp": 1703001234.567,
      "scan_type": "rfid",
      "object": {...},
      "location": {...}
    },
    "fallback_timestamp": "2024-12-19T15:30:45.123456",
    "fallback_reason": "rabbitmq_unavailable",
    "queue_name": "rfid_scans",
    "routing_key": "rfid.scan.result"
  }
]
```

## 🧪 Testing and Demo

### Run Fallback Demo

```bash
# Demonstrate fallback functionality
python test_fallback_demo.py

# Clean up demo files
python test_fallback_demo.py --cleanup
```

### Test Mode Features

- **No Hardware Required**: Simulates RFID tag reads
- **Configurable Delays**: Uses timing settings from configuration
- **Full Functionality**: Tests all scanner features including fallback mode
- **Safe Testing**: No GPIO operations, safe to run on any system

## 📊 Status Monitoring

### Command Line Status

```bash
# Show comprehensive status
python updated_rfid_rabbitmq.py --status
```

Example output:
```
RFID Scanner Status:
========================================
scanner_ready: True
test_mode: False
rabbitmq_connected: True
rabbitmq_host: localhost
rabbitmq_port: 5672
queue_name: rfid_scans
fallback_messages: 0
objects_count: 5
locations_count: 3
service_starts: 15
total_tags_scanned: 42
current_scan_state:
  object_scanned: False
  location_scanned: False
  ready_to_send: False
```

### Programmatic Status

```python
from updated_rfid_rabbitmq import RFIDRabbitMQScanner

scanner = RFIDRabbitMQScanner()
status = scanner.get_status()

print(f"RabbitMQ Connected: {status['rabbitmq_connected']}")
print(f"Fallback Messages: {status['fallback_messages']}")
```

## 🔧 Advanced Usage

### Custom Status Callback

```python
def my_status_callback(connected: bool):
    if connected:
        print("✅ RabbitMQ connected - normal operation")
    else:
        print("⚠️ RabbitMQ disconnected - fallback mode active")

# Use with enhanced transmitter
from enhanced_rabbitmq_tx import EnhancedMessageTransmitter

transmitter = EnhancedMessageTransmitter(
    status_callback=my_status_callback,
    # ... other config
)
```

### Dynamic Item Management

```python
from enhanced_config_manager import EnhancedConfigManager

config = EnhancedConfigManager()

# Add new object
config.add_item("NEW_ITEM", "object", {
    "name": "New Component",
    "category": "Electronics",
    "serial": "NEW001"
})

# Save configuration
config.save_configuration()
```

## 🚨 Error Handling

### Common Issues and Solutions

1. **RabbitMQ Connection Failed**
   - Check host and port settings
   - Verify credentials
   - Ensure RabbitMQ service is running
   - System automatically switches to fallback mode

2. **RFID Hardware Not Found**
   - Use `--test` mode for testing without hardware
   - Check GPIO pin connections
   - Verify mfrc522 library installation

3. **Configuration Validation Errors**
   - Run `--validate` to check configuration
   - Check GPIO pin numbers (1-40)
   - Verify RabbitMQ settings

4. **Permission Errors**
   - Ensure user has GPIO access (add to gpio group)
   - Check file system permissions for fallback directory

## 📈 Performance and Reliability

### Features for Production Use

- **Connection Pooling**: Efficient RabbitMQ connection management
- **Message Persistence**: Durable queues and persistent messages
- **Error Recovery**: Automatic reconnection with exponential backoff
- **Resource Cleanup**: Proper GPIO and connection cleanup
- **Logging**: Comprehensive logging with configurable levels

### Monitoring Recommendations

1. Monitor fallback file sizes
2. Track connection status changes
3. Set up alerts for extended fallback periods
4. Monitor scan frequency and success rates

## 🔄 Migration Guide

### From Original Version

1. **Backup** your existing configuration:
   ```bash
   cp rfid_config.json rfid_config.json.backup
   ```

2. **Run migration script**:
   ```bash
   python config_migration.py
   ```

3. **Update imports** in your code:
   ```python
   # Old
   from rfid_rabbitmq import RFIDRabbitMQScanner
   
   # New
   from updated_rfid_rabbitmq import RFIDRabbitMQScanner
   ```

4. **Test thoroughly** with `--test` mode

### Configuration Changes

- `rabbitmq.usr_ssl` → `rabbitmq.use_ssl` (typo fixed)
- Added `timing.orange_flash_interval`
- Enhanced `statistics` section
- Restructured `rfid_tags` section

## 🔐 Security Considerations

### Production Deployment

1. **Use SSL/TLS**: Set `use_ssl: true` for production
2. **Environment Variables**: Store credentials in environment, not config files
3. **File Permissions**: Secure fallback directory permissions
4. **Network Security**: Use VPNs or secure networks for RabbitMQ communication

### Example Production Config

```bash
export RABBITMQ_HOST=secure-rabbitmq.company.com
export RABBITMQ_PORT=5671
export RABBITMQ_USE_SSL=true
export RABBITMQ_USERNAME=rfid_scanner
export RABBITMQ_PASSWORD=secure_random_password
export RABBITMQ_VHOST=/production
```

## 🐛 Troubleshooting

### Debug Mode

Enable detailed logging:

```json
{
  "logging": {
    "level": "DEBUG",
    "file": "rfid_debug.log"
  }
}
```

### Common Log Messages

- `"RabbitMQ connection established"` - Normal startup
- `"Operating in fallback mode"` - RabbitMQ unavailable
- `"Processing X fallback messages"` - Recovery in progress
- `"Configuration validation errors"` - Check configuration

### Support Information

When reporting issues, include:
1. Scanner status output (`--status`)
2. Configuration validation results (`--validate`)
3. Log files (if configured)
4. Hardware setup details
5. RabbitMQ server information

## 📚 API Reference

### Enhanced Configuration Manager

```python
class EnhancedConfigManager:
    def get_rabbitmq_config() -> Dict
    def get_led_pins() -> Tuple
    def add_item(item_id, item_type, item_data) -> bool
    def validate_configuration() -> List[str]
    def save_configuration() -> bool
```

### Enhanced Message Transmitter

```python
class EnhancedMessageTransmitter:
    def transmit_message(message_data) -> Dict
    def get_status() -> Dict
    def is_connected() -> bool
    def get_fallback_message_count() -> int
```

### RFID Scanner

```python
class RFIDRabbitMQScanner:
    def __init__(config_file, test_mode=False)
    def run_once() -> bool
    def get_status() -> Dict
    def add_new_item(item_id, item_type, item_data) -> bool
```

## 🎯 Next Steps

1. **Test in your environment** with `--test` mode
2. **Migrate existing configuration** using migration script  
3. **Configure monitoring** for production deployment
4. **Set up environment variables** for secure credential management
5. **Document your specific RFID tags and locations**

---

## 📞 Support

For questions or issues:
1. Check the troubleshooting section
2. Validate your configuration with `--validate`
3. Review log files for error details
4. Test with `--test` mode to isolate hardware issues

**Version**: Enhanced v2.0 with Fallback Support  
**Last Updated**: December 2024

Reference - generated code from Claude.ai

Initial question:

using the following code as a starting point, extend the code to read RFID tags and store the RFID tag id into a python list, prompting the user between each tag read, until the user enters "n" to stop the loop.  On exit from the loop, the contents of the RFID tag id python list is written to a text file, with one id per line.

code (from https://pimylifeup.com/raspberry-pi-rfid-rc522/):
from time import sleep
import sys
from mfrc522 import SimpleMFRC522
reader = SimpleMFRC522()
try:
    while True:
        print("Hold a tag near the reader")
        id, text = reader.read()
        print("ID: %s\nText: %s" % (id,text))
        sleep(5)
except KeyboardInterrupt:
    GPIO.cleanup()
    raise

Claude.ai response:

This code provides a complete framework that:

RFID ID Storage: Added rfid_tags = [] list to store tag IDs
User Prompting: Added input prompt between each tag read - user presses Enter to continue or 'n' to stop
Loop Control: User-controlled loop that exits when 'n' is entered
File Output: On exit, writes all collected tag IDs to rfid_tags.txt with one ID per line
Error Handling: Added proper GPIO cleanup in finally block
User Feedback: Shows running count of collected tags and final summary

How it works:

Program starts and prompts user to press Enter to read a tag
When Enter is pressed, it reads the RFID tag and displays ID/text
The tag ID is automatically added to the rfid_tags list
Process repeats until user enters 'n'
On exit (normal or Ctrl+C), all collected tag IDs are written to rfid_tags.txt

Sample output file (rfid_tags.txt):

```
123456789012
987654321098
555666777888
```
The code maintains all your original functionality while adding the requested features for collecting multiple tags and saving them to a file.

After a few other questions - see commits:

Now the code has been completely rewritten with all the LED functionality properly integrated throughout. Here's a summary of all the LED features that are now included:
Complete LED Status System:
LED Color Definitions:

White: Waiting for RFID tag
Yellow Flash: Object tag successfully read
Blue Flash: Location tag successfully read
Green Flash: Both items scanned, ready to send message
Purple Solid (2s): Message successfully sent to RabbitMQ
Red Flash: Error conditions (read failure, unknown item, send failure)

LED Integration Points:

Initialization: RGB LED setup with configurable GPIO pins
Tag Reading: White LED while waiting, turns off after read
Item Processing:

Yellow flash for objects
Blue flash for locations
Green flash when both items ready


Message Transmission: Purple solid for 2 seconds on success
Error Handling: Red flash for all error conditions
Startup Sequence: Brief RGB cycle on scanner startup
Cleanup: LED turns off before shutdown

Error Scenarios with LED Feedback:

RFID Read Failure: Red flash
Unknown Item ID: Red flash
Message Send Error: Red flash
System Exceptions: Red flash

Key Features:

Simulation Mode: LED works in simulation mode for testing
Proper Resource Management: LED cleanup on shutdown
Configurable GPIO Pins: Easy to change LED pin assignments
Comprehensive Error Handling: All error states have visual feedback

The scanner now provides complete visual feedback for every operational state, making it easy for users to understand the system status without needing to watch console output.

Additional question:
when rabbitmq service is not available
1. add error handling to switch to simulation of the service.
1. set the led colour used when waiting for rfid tag to indicate the service is not available from steady "white" to flashing "orange". 
2. send messages to a rabbitmq file with the name of the queue.  Add an argument to enable testing of rfid_rabbitmq.py

# Enhanced RFID RabbitMQ Scanner with Fallback Support

A robust RFID scanning system with RabbitMQ messaging and automatic fallback to file storage when the message service is unavailable.

## 🆕 New Features

### RabbitMQ Fallback Support
- **Automatic Fallback**: When RabbitMQ is unavailable, messages are automatically saved to local files
- **Queue Recovery**: Messages are automatically sent when RabbitMQ becomes available again  
- **No Message Loss**: All scan data is preserved even during service outages
- **Connection Monitoring**: Background monitoring with automatic reconnection attempts

### Enhanced LED Status Indicators
- **Normal Operation**: Steady **WHITE** light when waiting for RFID tag
- **Fallback Mode**: Flashing **ORANGE** light when waiting for RFID tag
- **Object Scanned**: Flash **YELLOW** when object is detected
- **Location Scanned**: Flash **BLUE** when location is detected
- **Message Ready**: Flash **GREEN** when both object and location are scanned
- **Message Sent**: Solid **PURPLE** for 2 seconds after successful transmission
- **Error State**: Flash **RED** for read failures or errors

### Test Mode Support
- **Simulation Mode**: Run without physical RFID hardware for testing
- **Command Line Arguments**: Enable test mode with `--test` flag
- **Configurable Timing**: Adjustable simulation delays and flash intervals

### Enhanced Configuration Management
- **Structured Configuration**: Type-safe configuration with validation
- **Environment Variable Support**: Override config with environment variables
- **Statistics Tracking**: Automatic tracking of scans, service starts, and timestamps
- **Dynamic Item Management**: Add/remove RFID items without code changes

## 📁 File Structure

```
rfid_scanner/
├── enhanced_config_manager.py      # Enhanced configuration management
├── enhanced_rabbitmq_tx.py         # RabbitMQ transmitter with fallback
├── updated_rfid_rabbitmq.py        # Main RFID scanner (updated)
├── config_migration.py             # Migration script for existing configs
├── test_fallback_demo.py          # Fallback functionality demo
├── usage_example.py               # Configuration usage examples
├── rfid_config.json               # Configuration file
└── rabbitmq_fallback/             # Fallback message storage directory
    └── {queue_name}_messages.json  # Queued messages when RabbitMQ unavailable
```

## 🚀 Quick Start

### Installation

```bash
# Install required packages
pip install mfrc522 gpiozero colorzero pika

# Clone or download the enhanced scanner files
# Make sure all Python files are in the same directory
```

### Basic Usage

```bash
# Run in normal mode
python updated_rfid_rabbitmq.py

# Run in test mode (no physical RFID hardware required)
python updated_rfid_rabbitmq.py --test

# Show current status
python updated_rfid_rabbitmq.py --status

# Validate configuration
python updated_rfid_rabbitmq.py --validate
```

### Migration from Old Version

```bash
# Migrate existing configuration (creates backup automatically)
python config_migration.py
```

## ⚙️ Configuration

### Environment Variables

Override configuration with environment variables:

```bash
export RABBITMQ_HOST=production.example.com
export RABBITMQ_PORT=5671
export RABBITMQ_USE_SSL=true
export RABBITMQ_USERNAME=prod_user
export RABBITMQ_PASSWORD=secure_password
export LOG_LEVEL=WARNING
```

### Configuration File Format

```json
{
  "rabbitmq": {
    "host": "localhost",
    "port": 5672,
    "use_ssl": false,
    "username": null,
    "password": null,
    "virtual_host": "/",
    "exchange": "asset_tracking",
    "queue_name": "rfid_scans",
    "routing_key_scan": "rfid.scan.result"
  },
  "hardware": {
    "red_pin": 12,
    "green_pin": 13,
    "blue_pin": 19
  },
  "timing": {
    "read_interval": 2.0,
    "green_flash_duration": 2.0,
    "orange_flash_interval": 1.0
  },
  "rfid_tags": {
    "objects": {
      "RFID1": {
        "name": "Production Widget",
        "category": "Component",
        "serial": "WGT001"
      }
    },
    "locations": {
      "OP1": {
        "name": "Assembly Station 1",
        "description": "Primary assembly workstation"
      }
    }
  }
}
```

## 🔄 Fallback Mode Operation

### When RabbitMQ is Unavailable

1. **Automatic Detection**: System detects RabbitMQ unavailability within 5 seconds
2. **LED Indication**: Orange flashing light indicates fallback mode
3. **File Storage**: Messages saved to `rabbitmq_fallback/{queue_name}_messages.json`
4. **Continued Operation**: Scanner continues to work normally
5. **Background Monitoring**: System checks for RabbitMQ recovery every 30 seconds

### When RabbitMQ Returns

1. **Automatic Detection**: System detects RabbitMQ availability
2. **LED Indication**: Returns to steady white light
3. **Message Processing**: Queued messages are automatically sent
4. **Normal Operation**: System resumes normal RabbitMQ messaging

### Fallback File Format

```json
[
  {
    "original_message": {
      "timestamp": 1703001234.567,
      "scan_type": "rfid",
      "object": {...},
      "location": {...}
    },
    "fallback_timestamp": "2024-12-19T15:30:45.123456",
    "fallback_reason": "rabbitmq_unavailable",
    "queue_name": "rfid_scans",
    "routing_key": "rfid.scan.result"
  }
]
```

## 🧪 Testing and Demo

### Run Fallback Demo

```bash
# Demonstrate fallback functionality
python test_fallback_demo.py

# Clean up demo files
python test_fallback_demo.py --cleanup
```

### Test Mode Features

- **No Hardware Required**: Simulates RFID tag reads
- **Configurable Delays**: Uses timing settings from configuration
- **Full Functionality**: Tests all scanner features including fallback mode
- **Safe Testing**: No GPIO operations, safe to run on any system

## 📊 Status Monitoring

### Command Line Status

```bash
# Show comprehensive status
python updated_rfid_rabbitmq.py --status
```

Example output:
```
RFID Scanner Status:
========================================
scanner_ready: True
test_mode: False
rabbitmq_connected: True
rabbitmq_host: localhost
rabbitmq_port: 5672
queue_name: rfid_scans
fallback_messages: 0
objects_count: 5
locations_count: 3
service_starts: 15
total_tags_scanned: 42
current_scan_state:
  object_scanned: False
  location_scanned: False
  ready_to_send: False
```

### Programmatic Status

```python
from updated_rfid_rabbitmq import RFIDRabbitMQScanner

scanner = RFIDRabbitMQScanner()
status = scanner.get_status()

print(f"RabbitMQ Connected: {status['rabbitmq_connected']}")
print(f"Fallback Messages: {status['fallback_messages']}")
```

## 🔧 Advanced Usage

### Custom Status Callback

```python
def my_status_callback(connected: bool):
    if connected:
        print("✅ RabbitMQ connected - normal operation")
    else:
        print("⚠️ RabbitMQ disconnected - fallback mode active")

# Use with enhanced transmitter
from enhanced_rabbitmq_tx import EnhancedMessageTransmitter

transmitter = EnhancedMessageTransmitter(
    status_callback=my_status_callback,
    # ... other config
)
```

### Dynamic Item Management

```python
from enhanced_config_manager import EnhancedConfigManager

config = EnhancedConfigManager()

# Add new object
config.add_item("NEW_ITEM", "object", {
    "name": "New Component",
    "category": "Electronics",
    "serial": "NEW001"
})

# Save configuration
config.save_configuration()
```

## 🚨 Error Handling

### Common Issues and Solutions

1. **RabbitMQ Connection Failed**
   - Check host and port settings
   - Verify credentials
   - Ensure RabbitMQ service is running
   - System automatically switches to fallback mode

2. **RFID Hardware Not Found**
   - Use `--test` mode for testing without hardware
   - Check GPIO pin connections
   - Verify mfrc522 library installation

3. **Configuration Validation Errors**
   - Run `--validate` to check configuration
   - Check GPIO pin numbers (1-40)
   - Verify RabbitMQ settings

4. **Permission Errors**
   - Ensure user has GPIO access (add to gpio group)
   - Check file system permissions for fallback directory

## 📈 Performance and Reliability

### Features for Production Use

- **Connection Pooling**: Efficient RabbitMQ connection management
- **Message Persistence**: Durable queues and persistent messages
- **Error Recovery**: Automatic reconnection with exponential backoff
- **Resource Cleanup**: Proper GPIO and connection cleanup
- **Logging**: Comprehensive logging with configurable levels

### Monitoring Recommendations

1. Monitor fallback file sizes
2. Track connection status changes
3. Set up alerts for extended fallback periods
4. Monitor scan frequency and success rates

## 🔄 Migration Guide

### From Original Version

1. **Backup** your existing configuration:
   ```bash
   cp rfid_config.json rfid_config.json.backup
   ```

2. **Run migration script**:
   ```bash
   python config_migration.py
   ```

3. **Update imports** in your code:
   ```python
   # Old
   from rfid_rabbitmq import RFIDRabbitMQScanner
   
   # New
   from updated_rfid_rabbitmq import RFIDRabbitMQScanner
   ```

4. **Test thoroughly** with `--test` mode

### Configuration Changes

- `rabbitmq.usr_ssl` → `rabbitmq.use_ssl` (typo fixed)
- Added `timing.orange_flash_interval`
- Enhanced `statistics` section
- Restructured `rfid_tags` section

## 🔐 Security Considerations

### Production Deployment

1. **Use SSL/TLS**: Set `use_ssl: true` for production
2. **Environment Variables**: Store credentials in environment, not config files
3. **File Permissions**: Secure fallback directory permissions
4. **Network Security**: Use VPNs or secure networks for RabbitMQ communication

### Example Production Config

```bash
export RABBITMQ_HOST=secure-rabbitmq.company.com
export RABBITMQ_PORT=5671
export RABBITMQ_USE_SSL=true
export RABBITMQ_USERNAME=rfid_scanner
export RABBITMQ_PASSWORD=secure_random_password
export RABBITMQ_VHOST=/production
```

## 🐛 Troubleshooting

### Debug Mode

Enable detailed logging:

```json
{
  "logging": {
    "level": "DEBUG",
    "file": "rfid_debug.log"
  }
}
```

### Common Log Messages

- `"RabbitMQ connection established"` - Normal startup
- `"Operating in fallback mode"` - RabbitMQ unavailable
- `"Processing X fallback messages"` - Recovery in progress
- `"Configuration validation errors"` - Check configuration

### Support Information

When reporting issues, include:
1. Scanner status output (`--status`)
2. Configuration validation results (`--validate`)
3. Log files (if configured)
4. Hardware setup details
5. RabbitMQ server information

## 📚 API Reference

### Enhanced Configuration Manager

```python
class EnhancedConfigManager:
    def get_rabbitmq_config() -> Dict
    def get_led_pins() -> Tuple
    def add_item(item_id, item_type, item_data) -> bool
    def validate_configuration() -> List[str]
    def save_configuration() -> bool
```

### Enhanced Message Transmitter

```python
class EnhancedMessageTransmitter:
    def transmit_message(message_data) -> Dict
    def get_status() -> Dict
    def is_connected() -> bool
    def get_fallback_message_count() -> int
```

### RFID Scanner

```python
class RFIDRabbitMQScanner:
    def __init__(config_file, test_mode=False)
    def run_once() -> bool
    def get_status() -> Dict
    def add_new_item(item_id, item_type, item_data) -> bool
```

## 🎯 Next Steps

1. **Test in your environment** with `--test` mode
2. **Migrate existing configuration** using migration script  
3. **Configure monitoring** for production deployment
4. **Set up environment variables** for secure credential management
5. **Document your specific RFID tags and locations**

---

## 📞 Support

For questions or issues:
1. Check the troubleshooting section
2. Validate your configuration with `--validate`
3. Review log files for error details
4. Test with `--test` mode to isolate hardware issues

**Version**: Enhanced v2.0 with Fallback Support  
**Last Updated**: December 2024
