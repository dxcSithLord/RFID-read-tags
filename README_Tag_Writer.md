# RFID Scanner Setup Guide

## Hardware Requirements

### Components Needed:
- Raspberry Pi (3B+ or 4 recommended)
- MFRC522 RFID Reader Module
- RGB LED (Common Cathode)
- 3x 220Ω Resistors
- Breadboard and jumper wires
- RFID tags (NTAG213/215/216 or Mifare Classic)

## Wiring Diagram

### MFRC522 RFID Reader to Raspberry Pi:
```
MFRC522    Raspberry Pi
--------   ------------
3.3V   ->  Pin 1 (3.3V)
RST    ->  Pin 22 (GPIO25)
GND    ->  Pin 6 (GND)
MISO   ->  Pin 21 (GPIO9)
MOSI   ->  Pin 19 (GPIO10)
SCK    ->  Pin 23 (GPIO11)
SDA    ->  Pin 24 (GPIO8)
```

### RGB LED to Raspberry Pi:
```
RGB LED         Raspberry Pi
---------       ------------
Red   (R)   ->  GPIO12) via 220Ω resistor
Green (G)   ->  GPIO13) via 220Ω resistor
Blue  (B)   ->  GPIO19) via 220Ω resistor
Common Cathode -> Pin 9 (GND)
```

## Software Installation

### 1. Enable SPI Interface:
```bash
sudo raspi-config
# Navigate to: Interface Options -> SPI -> Yes
sudo reboot
```

### 2. Install Python Dependencies:
```bash
pip install -r requirements.txt
```

### 3. Test Hardware:
```bash
# Test RFID reader
python3 -c "from mfrc522 import SimpleMFRC522; print('RFID OK')"

# Test LED
python3 -c "from gpiozero import RGBLED; from colorzero import Color; led = RGBLED(2,3,4); led.color = Color('red'); print('LED OK')"
```

## LED Status Indicators

### Scanner Operation:
- **White Solid**: Waiting for RFID tag
- **Yellow Flash**: Object tag successfully read
- **Blue Flash**: Location tag successfully read
- **Green Flash**: Both object and location read, ready to send message
- **Purple Solid (2s)**: Message successfully sent to RabbitMQ
- **Red Flash**: Error occurred

### Tag Writer Operation:
- **White Solid**: Waiting for tag to write to
- **Yellow Flash**: Object tag successfully written
- **Blue Flash**: Location tag successfully written
- **Green Solid (1s)**: Individual tag write completed
- **Purple Solid (3s)**: Batch writing completed
- **Red Flash**: Write error occurred

## Configuration

### 1. RFID Configuration File (`rfid_config.json`):
The scanner will create a sample configuration file on first run. Customize it with your objects and locations:

```json
{
  "objects": {
    "obj001": {
      "name": "Your Object Name",
      "description": "Object description",
      "category": "component"
    }
  },
  "locations": {
    "loc001": {
      "name": "Your Location Name",
      "description": "Location description",
      "zone": "production"
    }
  }
}
```

### 2. Environment Variables:
Set RabbitMQ connection parameters:

```bash
export RABBITMQ_HOST=localhost
export RABBITMQ_PORT=5672
export RABBITMQ_QUEUE=rfid_messages
export RABBITMQ_USERNAME=your_username
export RABBITMQ_PASSWORD=your_password
export RABBITMQ_USE_SSL="True"
```

To use the SSL, need the Certificate Authority certificate installed on local environment.

## Usage

### 1. Writing Tags:
```bash
# Interactive mode
python3 rfid_tag_writer.py

# Choose option 1 for individual tags or option 2 for batch writing
```

### 2. Running the Scanner:
```bash
python3 complete_rfid_scanner.py
```

### 3. Tag Verification:
```bash
# Run the tag writer in verification mode
python3 rfid_tag_writer.py
# Choose option 3
```

## Operation Workflow

### Normal Scanning Process:
1. **Start Scanner**: White LED indicates waiting for first tag
2. **Scan Object**: Present object tag, yellow flash confirms read
3. **Scan Location**: Present location tag, blue flash confirms read
4. **Message Ready**: Green flash indicates both items scanned
5. **Message Sent**: Purple LED for 2 seconds confirms successful transmission
6. **Reset**: Scanner returns to step 1

### Tag Writing Process:
1. **Select Mode**: Interactive or batch writing
2. **Choose Item**: Select object or location to write
3. **Present Tag**: White LED indicates waiting for blank tag
4. **Write Complete**: Yellow (object) or blue (location) flash confirms write
5. **Verify**: Optionally verify tag content

## Troubleshooting

### Common Issues:

**RFID Not Reading:**
- Check SPI is enabled: `lsmod | grep spi`
- Verify wiring connections
- Try different tags (some may be damaged)

**LED Not Working:**
- Check resistor values (220Ω recommended)
- Verify GPIO pin connections
- Test with simple gpiozero commands

**RabbitMQ Connection Errors:**
- Verify RabbitMQ server is running
- Check network connectivity
- Validate credentials and queue names

**Permission Errors:**
- Add user to gpio group: `sudo usermod -a -G gpio $USER`
- Logout and login again

### Debug Mode:
Enable verbose logging by modifying the script:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Safety Notes

- Always shutdown Pi properly before disconnecting hardware
- Use appropriate resistors to prevent LED damage
- Handle RFID tags carefully to avoid damage
- Keep tags away from strong magnetic fields

## Customization

### Custom LED Pins:
Modify the GPIO pins in the scanner initialization:
```python
scanner = RFIDRabbitMQScanner(
    led_pins=(18, 23, 24),  # (red, green, blue)
    **rabbitmq_config
)
```

### Custom Colors:
Add new colors to the color map in `set_led_color()` method:
```python
color_map = {
    'orange': Color('orange'),
    'cyan': Color('cyan'),
    # ... existing colors
}
