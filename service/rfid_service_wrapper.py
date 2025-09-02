#!/opt/rfid-reader/venv/bin/python3
"""
RFID Reader Service Wrapper
Adapted for running as a systemd service without user interaction
"""

import os
import sys
import time
import signal
import logging
import threading
from datetime import datetime
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

# Configuration
SCRIPT_DIR = '/opt/rfid-reader'
CONFIG_FILE = os.path.join(SCRIPT_DIR, 'config.txt')
OUTPUT_FILE = os.path.join(SCRIPT_DIR, 'rfid_tags.txt')
LOG_FILE = os.path.join(SCRIPT_DIR, 'rfid_service.log')

# Default GPIO pins for RGB LED
DEFAULT_RED_PIN = 18
DEFAULT_GREEN_PIN = 19
DEFAULT_BLUE_PIN = 20

class RFIDService:
    def __init__(self):
        self.setup_logging()
        self.load_config()
        self.setup_hardware()
        self.rfid_tags = self.load_existing_tags()
        self.running = False
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOG_FILE),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_config(self):
        """Load configuration from file or create default"""
        self.config = {
            'red_pin': DEFAULT_RED_PIN,
            'green_pin': DEFAULT_GREEN_PIN,
            'blue_pin': DEFAULT_BLUE_PIN,
            'read_interval': 2.0,
            'green_flash_duration': 2.0
        }
        
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    for line in f:
                        if '=' in line and not line.strip().startswith('#'):
                            key, value = line.strip().split('=', 1)
                            if key in self.config:
                                if key.endswith('_pin'):
                                    self.config[key] = int(value)
                                else:
                                    self.config[key] = float(value)
                self.logger.info(f"Configuration loaded from {CONFIG_FILE}")
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")
        else:
            self.create_default_config()
            
    def create_default_config(self):
        """Create default configuration file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                f.write("# RFID Service Configuration\n")
                f.write(f"red_pin={self.config['red_pin']}\n")
                f.write(f"green_pin={self.config['green_pin']}\n")
                f.write(f"blue_pin={self.config['blue_pin']}\n")
                f.write(f"read_interval={self.config['read_interval']}\n")
                f.write(f"green_flash_duration={self.config['green_flash_duration']}\n")
            self.logger.info(f"Default configuration created at {CONFIG_FILE}")
        except Exception as e:
            self.logger.error(f"Error creating config file: {e}")
            
    def setup_hardware(self):
        """Initialize RFID reader and RGB LED"""
        try:
            # Setup RFID reader
            self.reader = SimpleMFRC522()
            
            # Setup RGB LED
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.config['red_pin'], GPIO.OUT)
            GPIO.setup(self.config['green_pin'], GPIO.OUT)
            GPIO.setup(self.config['blue_pin'], GPIO.OUT)
            
            # Create PWM instances
            self.red_pwm = GPIO.PWM(self.config['red_pin'], 1000)
            self.green_pwm = GPIO.PWM(self.config['green_pin'], 1000)
            self.blue_pwm = GPIO.PWM(self.config['blue_pin'], 1000)
            
            # Start PWM
            self.red_pwm.start(0)
            self.green_pwm.start(0)
            self.blue_pwm.start(0)
            
            self.logger.info("Hardware initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing hardware: {e}")
            sys.exit(1)
            
    def load_existing_tags(self):
        """Load existing tags from file"""
        tags = {}
        if os.path.exists(OUTPUT_FILE):
            try:
                with open(OUTPUT_FILE, 'r') as f:
                    for line in f:
                        if ':' in line:
                            tag_id, tag_text = line.strip().split(':', 1)
                            tags[tag_id.strip()] = tag_text.strip()
                self.logger.info(f"Loaded {len(tags)} existing tags from {OUTPUT_FILE}")
            except Exception as e:
                self.logger.error(f"Error loading existing tags: {e}")
        return tags
        
    def set_rgb_color(self, red, green, blue):
        """Set RGB LED color (0-100 for each color)"""
        try:
            self.red_pwm.ChangeDutyCycle(red)
            self.green_pwm.ChangeDutyCycle(green)
            self.blue_pwm.ChangeDutyCycle(blue)
        except Exception as e:
            self.logger.error(f"Error setting LED color: {e}")
            
    def led_white(self):
        """Set LED to white (ready to read)"""
        self.set_rgb_color(100, 100, 100)
        
    def led_green(self):
        """Set LED to green (read OK)"""
        self.set_rgb_color(0, 100, 0)
        
    def led_off(self):
        """Turn LED off"""
        self.set_rgb_color(0, 0, 0)
        
    def green_flash(self):
        """Flash green for configured duration then turn back to white"""
        self.led_green()
        time.sleep(self.config['green_flash_duration'])
        if self.running:  # Only return to white if service is still running
            self.led_white()
            
    def save_tags(self):
        """Save tags to file"""
        try:
            with open(OUTPUT_FILE, 'w') as f:
                for tag_id, tag_text in self.rfid_tags.items():
                    f.write(f"{tag_id}: {tag_text}\n")
            self.logger.info(f"Saved {len(self.rfid_tags)} tags to {OUTPUT_FILE}")
        except Exception as e:
            self.logger.error(f"Error saving tags: {e}")
            
    def read_rfid_loop(self):
        """Main RFID reading loop"""
        self.logger.info("RFID Service started - continuous reading mode")
        self.running = True
        
        while self.running:
            try:
                # Set LED to white (ready to read)
                self.led_white()
                
                # Read RFID tag with timeout
                self.logger.debug("Waiting for RFID tag...")
                id, text = self.reader.read_no_block()
                
                if id:  # Tag was read successfully
                    tag_id_str = str(id)
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    if tag_id_str not in self.rfid_tags:
                        self.rfid_tags[tag_id_str] = text if text else ""
                        self.logger.info(f"New tag added: ID={id}, Text='{text}' at {timestamp}")
                        self.save_tags()
                    else:
                        self.logger.info(f"Duplicate tag detected: ID={id} at {timestamp}")
                    
                    # Flash green LED in separate thread
                    led_thread = threading.Thread(target=self.green_flash)
                    led_thread.daemon = True
                    led_thread.start()
                    
                    # Brief pause after successful read
                    time.sleep(1)
                else:
                    # Brief pause when no tag detected
                    time.sleep(self.config['read_interval'])
                    
            except Exception as e:
                self.logger.error(f"Error in RFID reading loop: {e}")
                time.sleep(5)  # Wait before retrying
                
    def cleanup(self):
        """Cleanup GPIO and save final state"""
        self.logger.info("Cleaning up RFID service...")
        self.running = False
        
        try:
            self.led_off()
            self.red_pwm.stop()
            self.green_pwm.stop()
            self.blue_pwm.stop()
            GPIO.cleanup()
            self.save_tags()
            self.logger.info("Cleanup completed successfully")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.cleanup()
        sys.exit(0)

def main():
    """Main function"""
    # Ensure we're running as root (needed for GPIO access)
    if os.geteuid() != 0:
        print("This service must be run as root for GPIO access")
        sys.exit(1)
        
    # Change to script directory
    os.chdir(SCRIPT_DIR)
    
    # Create service instance
    service = RFIDService()
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, service.signal_handler)
    signal.signal(signal.SIGINT, service.signal_handler)
    
    try:
        # Start the main reading loop
        service.read_rfid_loop()
    except KeyboardInterrupt:
        service.logger.info("Service interrupted by user")
    except Exception as e:
        service.logger.error(f"Unexpected error: {e}")
    finally:
        service.cleanup()

if __name__ == "__main__":
    main()
