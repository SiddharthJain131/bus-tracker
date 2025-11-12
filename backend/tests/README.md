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

## Files in This Directory

| File | Description |
|------|-------------|
| `local_device_simulator.py` | Main device simulator script |
| `simulator_config.example.py` | Example configuration reference |
| `test_scan_photo.jpg` | Sample image for scan event testing |
| `device_test_log.txt` | Auto-generated test log file |
| `README.md` | This file |

## Additional Resources

- [Device API Documentation](../../docs/API_TEST_DEVICE.md)
- [Raspberry Pi Integration Guide](../../docs/RASPBERRY_PI_INTEGRATION.md)
- [Main API Documentation](../../docs/API_DOCUMENTATION.md)

---

**Last Updated**: November 2025
