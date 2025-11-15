# Raspberry Pi Boarding Scanner

This directory contains the Raspberry Pi script for handling student boarding operations with RFID scanning and face verification.

## Overview

The `pi_boarding_scanner.py` script is designed to run on a Raspberry Pi equipped with an RFID reader and camera. It performs the following functions:

1. **Device Registration**: Registers the Pi device with the backend on first run
2. **Boarding IN**: RFID scan → fetch student photo → verify face → send event
3. **Boarding OUT**: RFID scan → send event (auto-marked as destination reached)

## Features

- ✅ Automatic device registration with backend
- ✅ Persistent credential storage (API key saved locally)
- ✅ Face verification using DeepFace (Facenet model)
- ✅ Embedding comparison with backend-stored embeddings
- ✅ Automatic status determination (YELLOW for boarding in, GREEN for boarding out)
- ✅ GPS coordinates tracking
- ✅ Comprehensive error handling
- ✅ Color-coded terminal output for easy monitoring

## Files

- `pi_boarding_scanner.py` - Main scanner script
- `rfid_student_mapping.json` - RFID tag to student ID mapping
- `pi_device_config.json` - Device configuration (auto-generated after registration)

## Installation

### Prerequisites

```bash
# Python 3.7+ required
sudo apt-get update
sudo apt-get install python3 python3-pip

# Install required packages
pip3 install requests numpy
```

### DeepFace Installation

The script will automatically install DeepFace on first run, but you can pre-install it:

```bash
pip3 install deepface tf-keras tensorflow
```

## Configuration

### 1. RFID Mapping File

Create or edit `rfid_student_mapping.json` with your student RFID tags:

```json
[
  {
    "rfid": "RFID-1001",
    "student_id": "abc-123-def-456",
    "name": "John Doe",
    "class": "5",
    "section": "A"
  },
  {
    "rfid": "RFID-1002",
    "student_id": "def-456-ghi-789",
    "name": "Jane Smith",
    "class": "5",
    "section": "B"
  }
]
```

**Important**: 
- The `student_id` must match the student ID in the backend database
- RFID tags must be unique
- This file is required for the scanner to work

### 2. First Run - Device Registration

On first run, the script will prompt for:

1. **Backend URL**: Your backend server URL (e.g., `http://your-server.com:8001`)
2. **Bus ID**: The UUID of the bus this device is assigned to
3. **Device Name**: A friendly name for this device (e.g., "Pi-Bus-001")
4. **Admin Credentials**: Admin email and password to register the device

The script will:
- Authenticate with the backend as admin
- Register the device and receive an API key
- Save the configuration to `pi_device_config.json`

**Note**: The API key is shown only once during registration and is saved locally. Keep this file secure!

## Usage

### Running the Scanner

```bash
python3 pi_boarding_scanner.py
```

### Workflow

#### Boarding IN (First Scan)
1. Student boards the bus
2. RFID tag is scanned
3. Scanner fetches student's profile photo from backend
4. Scanner generates face embedding from photo
5. Scanner compares with stored embedding
6. Scanner sends scan event with verification result
7. Backend marks attendance as YELLOW (boarding in)

#### Boarding OUT (Second Scan)
1. Student exits the bus
2. RFID tag is scanned
3. Scanner sends scan event
4. Backend marks attendance as GREEN (destination reached)

### Simulation Mode

The script runs in simulation mode by default, where you manually enter RFID tags:

```
Enter RFID tag (or 'q' to quit): RFID-1001

Scan type:
  1. Boarding IN (pickup/school entry)
  2. Boarding OUT (school exit/home)
Select scan type [1/2]: 1
```

### Hardware Mode

To integrate with actual RFID hardware, modify the `read_rfid_tag()` function in the script:

```python
def read_rfid_tag(simulation_mode: bool = False):  # Set to False
    if simulation_mode:
        # ... simulation code ...
    else:
        # TODO: Implement your RFID reader interface
        # Example: Read from serial port (RC522 module)
        import serial
        ser = serial.Serial('/dev/ttyUSB0', 9600)
        rfid_data = ser.readline().decode('utf-8').strip()
        return rfid_data
```

## API Endpoints Used

The script automatically discovers and uses these backend endpoints:

### Authentication & Registration
- `POST /api/auth/login` - Admin login for device registration
- `POST /api/device/register` - Register device and get API key

### Device Operations (require X-API-Key header)
- `GET /api/students/{student_id}/photo` - Fetch student photo
- `GET /api/students/{student_id}/embedding` - Fetch stored face embedding
- `POST /api/scan_event` - Send boarding scan event

## Backend Communication

All device API requests include authentication via the `X-API-Key` header:

```python
headers = {"X-API-Key": config['api_key']}
```

The backend automatically:
- Validates the API key
- Associates scans with the correct bus
- Determines attendance status (YELLOW/GREEN) based on scan sequence
- Stores scan events and attendance records

## Face Verification

The script uses **DeepFace** with the **Facenet** model for face verification:

1. **Embedding Generation**: Extracts 128-dimensional face embedding from photo
2. **Cosine Similarity**: Compares current and stored embeddings
3. **Threshold**: Similarity ≥ 60% = verified, < 60% = not verified
4. **Confidence Score**: Reported as decimal (0.0 to 1.0)

### Verification Outcomes

| Similarity | Status | Action |
|------------|--------|--------|
| ≥ 60% | ✓ Verified | Normal boarding |
| < 60% | ✗ Not Verified | Logged but flagged for review |
| No embedding | ⚠ Warning | Boarding allowed with lower confidence |
| No photo | ⚠ Warning | Unverified scan sent |

## Troubleshooting

### Device Registration Fails

**Problem**: Cannot register device

**Solutions**:
- Verify backend URL is correct and accessible
- Ensure admin credentials are correct
- Check that the bus ID exists in the backend
- Verify network connectivity

### RFID Tag Not Found

**Problem**: "Unknown RFID tag" error

**Solutions**:
- Check that `rfid_student_mapping.json` exists
- Verify the RFID tag is in the mapping file
- Ensure student ID matches backend database

### Face Verification Fails

**Problem**: Low similarity scores or verification failures

**Solutions**:
- Ensure student has a clear profile photo in backend
- Check that DeepFace is installed correctly
- Verify network connection for photo download
- Review face detection settings (lighting, angle)

### API Key Invalid

**Problem**: "Invalid or expired API key" error

**Solutions**:
- Delete `pi_device_config.json` and re-register
- Verify the device hasn't been removed from backend
- Check with admin that device is still active

### DeepFace Installation Fails

**Problem**: Cannot install DeepFace

**Solutions**:
```bash
# Install system dependencies first
sudo apt-get install python3-dev libhdf5-dev

# Then install DeepFace
pip3 install deepface tf-keras tensorflow
```

## Configuration Files

### pi_device_config.json (auto-generated)

```json
{
  "backend_url": "http://your-server.com:8001",
  "device_id": "abc-123-def-456",
  "device_name": "Pi-Bus-001",
  "bus_id": "bus-uuid-here",
  "api_key": "your-secret-api-key",
  "registered_at": "2025-01-15T10:30:00.000Z",
  "gps": {
    "lat": 37.7749,
    "lon": -122.4194
  }
}
```

**Security Note**: Keep this file secure! The API key provides device-level access to the backend.

## Hardware Integration

### RFID Reader (RC522)

Example integration with RC522 RFID module:

```python
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

reader = SimpleMFRC522()

def read_rfid_tag(simulation_mode=False):
    if not simulation_mode:
        try:
            rfid_id, rfid_text = reader.read()
            return f"RFID-{rfid_id}"
        finally:
            GPIO.cleanup()
    # ... simulation code ...
```

### Camera Integration

The script uses existing student photos from the backend. If you want to capture live photos during scanning:

```python
import cv2

def capture_photo(student_id):
    camera = cv2.VideoCapture(0)
    ret, frame = camera.read()
    photo_path = f"temp_photos/{student_id}_scan.jpg"
    cv2.imwrite(photo_path, frame)
    camera.release()
    return photo_path
```

## Performance Notes

- **Face embedding generation**: ~2-3 seconds per scan
- **Network requests**: ~500ms total for photo + embedding fetch
- **Total scan time**: ~3-5 seconds per student

## Support

For backend API documentation, see `/app/docs/API_DOCUMENTATION.md`

For Raspberry Pi hardware setup, see `/app/docs/RASPBERRY_PI_INTEGRATION.md`
