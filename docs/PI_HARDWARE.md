# Raspberry Pi Hardware Setup Guide

## Overview

This guide covers the complete setup and configuration of the Raspberry Pi hardware module (`pi_hardware_mod.py`) for the Bus Tracker system.

## Table of Contents

1. [Hardware Requirements](#hardware-requirements)
2. [System Setup](#system-setup)
3. [Software Installation](#software-installation)
4. [Hardware Connections](#hardware-connections)
5. [Configuration](#configuration)
6. [Troubleshooting](#troubleshooting)
7. [GPS Fallback Handling](#gps-fallback-handling)

---

## Hardware Requirements

### Required Components

1. **Raspberry Pi** (Model 3B+ or 4 recommended)
2. **RFID Reader**: MFRC522 module
3. **LEDs**: 
   - 1x LED for scan indicator (GPIO 22)
   - 3x LEDs for binary counter display (GPIO 23, 24, 25)
   - Appropriate resistors (220Ω recommended)
4. **Power Supply**: 5V 3A USB-C (Pi 4) or Micro-USB (Pi 3)
5. **MicroSD Card**: 16GB+ (Class 10 recommended)

### Optional Components

- **Android Phone**: For camera via ADB (as alternative to Pi Camera)
- **GPS Module**: If not using ADB-based GPS
- **Pi Camera Module**: If not using ADB camera

---

## System Setup

### 1. Install Raspberry Pi OS

```bash
# Use Raspberry Pi Imager to flash OS to SD card
# Recommended: Raspberry Pi OS (64-bit) Lite or Desktop
```

### 2. Enable Required Interfaces

```bash
sudo raspi-config
```

Navigate and enable:
- **Interface Options > SPI** → Enable
- **Interface Options > I2C** → Enable
- **Interface Options > Camera** → Enable (if using Pi Camera)

Reboot after changes:
```bash
sudo reboot
```

### 3. System Updates

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

---

## Software Installation

### 1. Install System Dependencies

```bash
# Python development tools
sudo apt-get install -y python3-dev python3-pip python3-venv

# ADB for Android camera integration
sudo apt-get install -y android-tools-adb

# OpenCV dependencies
sudo apt-get install -y libopencv-dev python3-opencv

# Additional libraries
sudo apt-get install -y libatlas-base-dev libhdf5-dev
```

### 2. Install Python Packages

```bash
# Navigate to tests directory
cd /app/tests

# Install Pi-specific requirements
pip3 install -r pi_requirements.txt
```

### 3. Verify GPIO Installation

```bash
python3 -c "import RPi.GPIO as GPIO; print('GPIO OK')"
```

---

## Hardware Connections

### RFID MFRC522 Wiring

| MFRC522 Pin | Raspberry Pi Pin | GPIO Number |
|-------------|------------------|-------------|
| SDA         | Pin 24           | GPIO 8 (CE0)|
| SCK         | Pin 23           | GPIO 11     |
| MOSI        | Pin 19           | GPIO 10     |
| MISO        | Pin 21           | GPIO 9      |
| GND         | Pin 6            | GND         |
| RST         | Pin 22           | GPIO 25     |
| 3.3V        | Pin 1            | 3.3V        |

### LED Connections

| LED Function      | Raspberry Pi Pin | GPIO Number | Resistor |
|-------------------|------------------|-------------|----------|
| Scan Indicator    | Pin 15           | GPIO 22     | 220Ω     |
| Binary Display 0  | Pin 16           | GPIO 23     | 220Ω     |
| Binary Display 1  | Pin 18           | GPIO 24     | 220Ω     |
| Binary Display 2  | Pin 22           | GPIO 25     | 220Ω     |

**Note**: All LEDs should have their cathode (shorter leg) connected to GND through the resistor.

---

## Configuration

### 1. Environment Setup

Create `.env` file in `/app/tests/`:

```bash
# Backend Configuration
BACKEND_URL=http://your-backend-url.com:8001
DEVICE_ID=your-device-id
DEVICE_NAME=Pi-Bus-001
BUS_NUMBER=BUS-001
API_KEY=your-api-key-here
REGISTERED_AT=2025-01-01T00:00:00Z

# Hardware Mode
PI_MODE=hardware

# ADB Camera Configuration (if using Android phone)
ADB_DEVICE_IP=192.168.1.100
```

### 2. ADB Camera Setup (Optional)

If using Android phone as camera:

1. **Enable USB Debugging** on Android:
   - Settings → About Phone → Tap "Build Number" 7 times
   - Settings → Developer Options → Enable USB Debugging
   - Settings → Developer Options → Enable Wireless Debugging

2. **Connect ADB**:
```bash
# Connect to phone over WiFi
adb connect 192.168.1.100:5555

# Verify connection
adb devices
```

3. **Configure in pi_hardware_mod.py**:
Update the `DEVICE_IP` variable to match your phone's IP.

---

## GPS Fallback Handling

### How GPS Works in pi_hardware_mod.py

The module provides automatic GPS fallback with the following priority:

1. **ADB GPS** (Primary): Extracts GPS from connected Android device
2. **Hardware GPS** (Optional): Can be added via GPS module
3. **Null Coordinates** (Fallback): Returns `{"lat": None, "lon": None}` when GPS unavailable

### get_gps() Function

```python
def get_gps() -> Optional[Dict[str, Optional[float]]]:
    """
    Get GPS location with automatic fallback.
    Returns dict with 'lat' and 'lon' keys.
    Values are None if GPS unavailable.
    """
    try:
        lat, lon = get_gps_location_adb()
        return {"lat": lat, "lon": lon}
    except Exception as e:
        print(f"[WARN] GPS error: {e}")
        return {"lat": None, "lon": None}
```

### Frontend Handling

When GPS returns null coordinates:
- Map shows question mark indicator (🔴❓) on last known position
- Bus marker becomes gray with red "uncertain location" badge
- No map centering or bounds extension attempted
- Smooth transition when GPS becomes available again

### Backend Handling

The backend accepts null coordinates:
```python
class BusLocation(BaseModel):
    bus_number: str
    lat: Optional[float] = None  # Allows None
    lon: Optional[float] = None  # Allows None
    timestamp: str
```

Location updates with null coordinates are stored and flagged as `is_missing: true`.

---

## Troubleshooting

### GPIO Errors

**Error**: `RuntimeError: Not running on a RPi!`

**Solution**: This error occurs when running on non-Pi hardware. The module now handles this gracefully by:
- Warning that GPIO is unavailable
- Continuing without LED controls
- All core functionality remains operational

### RFID Not Reading

**Check**:
1. Verify SPI is enabled: `lsmod | grep spi`
2. Check wiring connections
3. Test RFID module:
```python
from mfrc522 import SimpleMFRC522
reader = SimpleMFRC522()
print("Hold card near reader...")
id, text = reader.read()
print(f"ID: {id}")
```

### ADB Camera Issues

**Error**: `device offline` or `no devices found`

**Solution**:
```bash
# Restart ADB server
adb kill-server
adb start-server

# Reconnect to device
adb connect <DEVICE_IP>:5555

# Check device status
adb devices
```

### DeepFace Installation Fails

**Error**: TensorFlow installation errors

**Solution**:
```bash
# Use lighter TensorFlow version
pip3 install tensorflow-lite

# Or use reduced TensorFlow
pip3 install tensorflow==2.13.0
```

### GPS Returns Null Coordinates

**Expected Behavior**: This is normal when:
- Android device GPS is disabled
- Location services are off
- No GPS fix yet
- Running indoors without clear sky view

**The system handles this gracefully by**:
- Sending null coordinates to backend
- Backend marks location as `is_missing: true`
- Frontend shows "GPS Unavailable" indicator
- No crashes or errors

---

## Running the Scanner

### Start in Hardware Mode

```bash
cd /app/tests
export PI_MODE=hardware
python3 pi_server.py
```

### Expected Output

```
======================================================================
RASPBERRY PI BOARDING SCANNER
======================================================================
Mode: HARDWARE

[OK] Loaded HARDWARE backend module
-> Initializing HARDWARE mode
[OK] GPIO initialized
[OK] RFID reader initialized
[OK] Camera initialized (ADB)
[OK] Face detector initialized
[OK] DeepFace available

[OK] All critical hardware components initialized
[OK] Device configuration loaded
  Device: Pi-Bus-001
  Backend: http://your-backend.com:8001

[OK] RFID mapping loaded (20 students)
  Cached embeddings: 15/20

[OK] Location updater started
[OK] Initial location sent

Scanner ready!

-> [HW] Waiting for RFID scan...
```

---

## Advanced Configuration

### Adding Hardware GPS Module

If using a GPS module (e.g., NEO-6M, NEO-7M):

1. **Install GPS libraries**:
```bash
pip3 install gpsd-py3
sudo apt-get install gpsd gpsd-clients
```

2. **Update pi_hardware_mod.py**:
```python
def get_gps_hardware() -> Tuple[Optional[float], Optional[float]]:
    """Get GPS from hardware module"""
    try:
        from gpsdclient import GPSDClient
        client = GPSDClient(host="127.0.0.1")
        for result in client.dict_stream(convert_datetime=True):
            if result.get("class") == "TPV":
                lat = result.get("lat")
                lon = result.get("lon")
                if lat and lon:
                    return lat, lon
        return None, None
    except Exception as e:
        print(f"[WARN] Hardware GPS error: {e}")
        return None, None
```

### Graceful Degradation

The hardware module is designed with graceful degradation:

- ✅ **Critical Failures**: RFID, Camera, Face detector - will stop initialization
- ⚠️ **Non-Critical Failures**: GPIO LEDs - warns but continues
- 🔄 **Automatic Fallback**: GPS unavailable - sends null coordinates

This ensures the system remains operational even with partial hardware failures.

---

## Support

For issues or questions:
1. Check `/var/log/syslog` for system errors
2. Review pi_server.py output for specific error messages
3. Verify all hardware connections
4. Test components individually using provided test commands

---

## Updates and Maintenance

### Keeping System Updated

```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Update Python packages
pip3 install --upgrade -r pi_requirements.txt

# Update bus tracker code
cd /app
git pull origin main
```

### Backup Configuration

```bash
# Backup environment file
cp /app/tests/.env /app/tests/.env.backup

# Backup RFID mapping
cp /app/tests/rfid_student_mapping.json /app/tests/rfid_student_mapping.json.backup
```

---

**Last Updated**: January 2025
**Compatible with**: Raspberry Pi 3B+, 4B, 5
**OS**: Raspberry Pi OS (Debian 11/12)
