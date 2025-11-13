# Device Testing Tools

This directory contains tools for testing the Raspberry Pi device API integration.

## Local Device Simulator

**File**: `local_device_simulator.py`

A comprehensive testing tool that simulates a registered Raspberry Pi device for testing all device-only API endpoints without physical hardware.

### Quick Start

1. **Register a Device** (as admin):
   ```bash
   # Login and get bus_id
   curl -X GET http://localhost:8001/api/buses \
     -H 'Cookie: session=<admin_session>' | jq '.[0].bus_id'
   
   # Register device
   curl -X POST http://localhost:8001/api/device/register \
     -H 'Cookie: session=<admin_session>' \
     -H 'Content-Type: application/json' \
     -d '{"bus_id":"<BUS_ID>","device_name":"Test Device"}'
   
   # Copy the returned api_key
   ```

2. **Configure Simulator**:
   - Open `local_device_simulator.py`
   - Update configuration section with:
     - `DEVICE_API_KEY` - API key from step 1
     - `BUS_ID` - Bus UUID from database
     - `STUDENT_ID` - Student UUID for testing
   - See `simulator_config.example.py` for reference

3. **Run Simulator**:
   ```bash
   python3 local_device_simulator.py
   ```

### Features

✅ **Interactive Menu**: Test individual endpoints or run all tests  
✅ **Color Output**: Green ✅ for success, Red ❌ for failure  
✅ **Detailed Logging**: All requests/responses saved to `device_test_log.txt`  
✅ **Photo Upload**: Tests scan events with base64-encoded images  
✅ **GPS Simulation**: Tests location updates with configurable coordinates  

### Menu Options

```
[1] Get Student Embedding   - Retrieves face recognition data
[2] Get Student Photo        - Retrieves student photo URL
[3] Send Yellow Scan         - Simulates "On Board" scan event
[4] Send Green Scan          - Simulates "Reached" scan event  
[5] Update GPS Location      - Updates bus location
[6] Run All Tests            - Executes all tests sequentially
[0] Exit
```

### Non-Interactive Mode

For CI/CD or automated testing:
```bash
python3 local_device_simulator.py --run-all
```

### Test Endpoints

The simulator tests these device API endpoints:

1. **GET** `/api/students/{id}/embedding` - Retrieve face embedding
2. **GET** `/api/students/{id}/photo` - Retrieve photo URL
3. **POST** `/api/scan_event` - Record attendance scan (yellow/green)
4. **POST** `/api/update_location` - Update bus GPS coordinates

### Logs

All test runs are logged to:
- **File**: `device_test_log.txt`
- **Location**: Same directory as simulator script
- **Contents**: Timestamps, requests, responses, success/failure status

### Example Output

```
🚌 Bus Tracker - Device API Simulator
============================================================

Configuration:
   • Base URL: http://localhost:8001
   • Bus ID: 3ca09d6a-2650-40e7-a874-5b2879025aff
   • Student ID: 9afb783f-7952-476d-8626-0143fdbbc2a1
   • API Key: Configured ✓

🔍 Testing: Get Student Embedding
✅ SUCCESS
   Student: Emma Johnson
   Has Embedding: false

📊 Test Summary
============================================================
Results: 5/5 tests passed (100%)
```

### Troubleshooting

**"Device API Key not configured"**
- Update `DEVICE_API_KEY` in the script with your actual API key

**"403 Forbidden"**
- Verify API key is correct
- Check device is registered for the specified bus_id

**"Connection refused"**
- Ensure backend is running: `sudo supervisorctl status backend`

**"422 Unprocessable Entity"**
- Check X-API-Key header is being sent
- Verify request body format matches API requirements

## Pi Real-Time Scanner (NEW - RECOMMENDED)

**File**: `pi_realtime_scanner.py`

A **real-time scanning simulator** that mimics an actual Raspberry Pi device with RFID scanner.

### Key Features

✅ **Zero Configuration**: Auto-registers device and starts scanning  
✅ **Continuous Scanning Thread**: Simulates RFID scans one by one  
✅ **Face Verification**: Uses DeepFace to verify each scan  
✅ **API Integration**: Fetches embeddings and sends results via API  
✅ **Realistic Simulation**: Mimics actual Pi device behavior  
✅ **Automatic AM/PM Cycling**: Switches from morning to afternoon boarding  

### Quick Start (No Config Needed!)

```bash
# Just run it - everything is automatic!
python3 pi_realtime_scanner.py
```

**What it does:**
1. Logs in as admin automatically
2. Registers device and gets API key
3. Starts continuous scanning thread
4. For each RFID scan:
   - Fetches student embedding from backend API
   - Generates embedding from profile photo
   - Compares and verifies
   - Sends result to backend

See [REALTIME_SCANNER_GUIDE.md](./REALTIME_SCANNER_GUIDE.md) for complete documentation.

---

## Pi Boarding Simulator (Batch Mode)

**File**: `pi_simulator_boarding.py`

A batch processing tool for testing multiple students at once.

### Key Features

✅ **Batch Processing**: Process all students in one run  
✅ **Real Face Recognition**: Uses DeepFace (Facenet model) to generate embeddings  
✅ **Profile Photo Management**: Loads from `backend/photos/students/<student_id>/profile.jpg`  
✅ **Placeholder Generation**: Downloads from thispersondoesnotexist.com if photo missing  
✅ **Embedding Comparison**: Compares with backend using cosine similarity  
✅ **Attendance Photos**: Saves photos to attendance folder with proper naming  

### Quick Start

```bash
# Run AM boarding simulation (batch)
python3 pi_simulator_boarding.py --scan-type AM

# Run PM boarding simulation (batch)
python3 pi_simulator_boarding.py --scan-type PM
```

See [PI_BOARDING_SIMULATOR_README.md](./PI_BOARDING_SIMULATOR_README.md) for complete documentation.

## Files in This Directory

| File | Description |
|------|-------------|
| `pi_realtime_scanner.py` | **NEW** - Real-time RFID scanner simulator (RECOMMENDED) |
| `REALTIME_SCANNER_GUIDE.md` | **NEW** - Real-time scanner complete guide |
| `pi_simulator_boarding.py` | **NEW** - Batch boarding simulator with face recognition |
| `students_boarding.json` | **NEW** - Student data for boarding simulation |
| `PI_BOARDING_SIMULATOR_README.md` | **NEW** - Batch simulator documentation |
| `USAGE_EXAMPLE.md` | **NEW** - Practical usage examples |
| `local_device_simulator.py` | Device API testing simulator |
| `simulator_config.py` | Configuration for simulators |
| `test_scan_photo.txt` | Sample image for scan event testing |
| `device_test_log.txt` | Auto-generated test log file |
| `README.md` | This file |

## Additional Resources

- [Device API Documentation](../../docs/API_TEST_DEVICE.md)
- [Raspberry Pi Integration Guide](../../docs/RASPBERRY_PI_INTEGRATION.md)
- [Main API Documentation](../../docs/API_DOCUMENTATION.md)

---

**Last Updated**: November 2025
