# RFID Reader Service Setup Guide

This guide will help you convert your RFID reader script to run as a systemd service at startup on Debian-based Linux systems.

## Prerequisites

- Debian-based Linux system (Ubuntu, Raspberry Pi OS, etc.)
- Python3 and pip installed
- Your RFID reader script working in a virtual environment

## Step 1: Prepare Directory Structure

Create a dedicated directory for your service:

```bash
sudo mkdir -p /opt/rfid-reader
sudo chown $USER:$USER /opt/rfid-reader
cd /opt/rfid-reader
```

## Step 2: Copy Your Script

Copy your RFID reader script to the service directory:

```bash
cp /path/to/your/rfid_reader.py /opt/rfid-reader/
```

## Step 3: Create Python Virtual Environment

```bash
cd /opt/rfid-reader
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install mfrc522 RPi.GPIO
deactivate
```

## Step 4: Create Service Wrapper Script

Create a wrapper script that handles the virtual environment and service logic:

```bash
nano /opt/rfid-reader/rfid_service.py
```

**Copy the service wrapper code from the artifact below.**

## Step 5: Create Systemd Service File

Create the systemd service configuration:

```bash
sudo nano /etc/systemd/system/rfid-reader.service
```

**Copy the systemd service configuration from the artifact below.**

## Step 6: Set Permissions

```bash
sudo chown -R root:root /opt/rfid-reader
sudo chmod +x /opt/rfid-reader/rfid_service.py
sudo chmod 644 /etc/systemd/system/rfid-reader.service
```

## Step 7: Enable and Start Service

```bash
# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start at boot
sudo systemctl enable rfid-reader.service

# Start the service immediately
sudo systemctl start rfid-reader.service
```

## Service Management Commands

```bash
# Check service status
sudo systemctl status rfid-reader.service

# Stop the service
sudo systemctl stop rfid-reader.service

# Restart the service
sudo systemctl restart rfid-reader.service

# View service logs
sudo journalctl -u rfid-reader.service -f

# View recent logs
sudo journalctl -u rfid-reader.service --since "1 hour ago"

# Disable service from starting at boot
sudo systemctl disable rfid-reader.service
```

## Configuration Files

The service creates a configuration file at `/opt/rfid-reader/config.txt` where you can adjust:
- GPIO pin assignments for RGB LED
- File output location
- Service behavior settings

## Output Files

- RFID tags are saved to: `/opt/rfid-reader/rfid_tags.txt`
- Service logs available via: `journalctl -u rfid-reader.service`
- Configuration: `/opt/rfid-reader/config.txt`

## Troubleshooting

1. **Permission Issues**: Ensure the service runs as root (needed for GPIO access)
2. **GPIO Conflicts**: Check if other services are using the same GPIO pins
3. **Module Issues**: Verify all Python modules are installed in the virtual environment
4. **Hardware Issues**: Test RFID reader manually before running as service

## Testing the Service

1. Check if service is running: `sudo systemctl is-active rfid-reader.service`
2. Monitor logs in real-time: `sudo journalctl -u rfid-reader.service -f`
3. Test RFID reading by placing a tag near the reader
4. Check output file: `cat /opt/rfid-reader/rfid_tags.txt`

## Uninstall Service

To remove the service:

```bash
sudo systemctl stop rfid-reader.service
sudo systemctl disable rfid-reader.service
sudo rm /etc/systemd/system/rfid-reader.service
sudo systemctl daemon-reload
sudo rm -rf /opt/rfid-reader
```