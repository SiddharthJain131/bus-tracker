# Device API Testing Reference

This document provides comprehensive testing instructions for Raspberry Pi device integration with the Bus Tracker backend.

## Table of Contents
- [Overview](#overview)
- [Device Registration](#device-registration)
- [API Key Authentication](#api-key-authentication)
- [Device Endpoints](#device-endpoints)
- [Testing Examples](#testing-examples)

---

## Overview

The Bus Tracker system uses a secure API key-based authentication system for Raspberry Pi devices (buses). Each device must be registered by an admin and provided with a unique API key to access device-specific endpoints.

### Key Concepts

- **Device Registration**: Admin creates device keys for Raspberry Pi units
- **API Key**: 64-character secure token (displayed only once at creation)
- **X-API-Key Header**: Required for all device endpoint requests
- **Bus Linking**: Each device is linked 1:1 with a bus via `bus_id`

---

## Device Registration

### Endpoint: POST /api/device/register

**Description**: Admin-only endpoint to register a new Raspberry Pi device and generate its API key.

**Authentication**: Session-based (Admin only)

**Request Body**:
```json
{
  "bus_id": "550e8400-e29b-41d4-a716-446655440000",
  "device_name": "Raspberry Pi - Bus 001"
}
```

**Response** (Success - 200):
```json
{
  "message": "Device registered successfully",
  "device_id": "650e8400-e29b-41d4-a716-446655440001",
  "bus_id": "550e8400-e29b-41d4-a716-446655440000",
  "bus_number": "BUS-001",
  "device_name": "Raspberry Pi - Bus 001",
  "api_key": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2",
  "warning": "Store this API key securely. It cannot be retrieved later.",
  "created_at": "2025-07-15T10:30:00.000Z"
}
```

**Important**: The `api_key` is displayed **only once**. Store it securely in the Raspberry Pi's environment configuration.

**Testing with curl**:
```bash
# First, login as admin to get session cookie
curl -X POST ${BACKEND_BASE_URL}/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@school.com", "password": "password"}' \
  -c cookies.txt

# Register a device
curl -X POST ${BACKEND_BASE_URL}/api/device/register \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "bus_id": "your-bus-id-here",
    "device_name": "Raspberry Pi - Bus 001"
  }'
```

**Testing with Postman**:
1. POST to `${BACKEND_BASE_URL}/api/auth/login`
   - Body: `{"email": "admin@school.com", "password": "password"}`
   - Save the session cookie
2. POST to `${BACKEND_BASE_URL}/api/device/register`
   - Use saved cookie
   - Body: `{"bus_id": "your-bus-id", "device_name": "Raspberry Pi - Bus 001"}`

---

## API Key Authentication

All device endpoints require the `X-API-Key` header with the device's API key.

### Header Format
```
X-API-Key: <your-64-character-api-key>
```

### Raspberry Pi Configuration

Store the API key in the Raspberry Pi's environment file:

**File**: `/etc/bus-tracker/.env` (or your config location)
```bash
DEVICE_API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
BACKEND_URL=https://your-backend-url.com/api
```

### Error Responses

**403 Forbidden** - Missing or invalid API key:
```json
{
  "detail": "Invalid or expired API key"
}
```

**403 Forbidden** - Missing header:
```json
{
  "detail": "Missing X-API-Key header"
}
```

---

## Device Endpoints

### 1. Scan Event (RFID Scan)

**Endpoint**: `POST /api/scan_event`

**Description**: Records student RFID scan event with yellow (On Board) or green (Reached) status.

**Authentication**: X-API-Key header required

**Request Body**:
```json
{
  "student_id": "750e8400-e29b-41d4-a716-446655440003",
  "tag_id": "RFID-12345678",
  "verified": true,
  "confidence": 0.95,
  "lat": 40.7128,
  "lon": -74.0060,
  "photo_url": "https://storage.example.com/photos/scan_12345.jpg",
  "scan_type": "yellow"
}
```

**Parameters**:
- `student_id` (string, required): Student's unique ID
- `tag_id` (string, required): RFID tag identifier
- `verified` (boolean, required): Whether identity was verified
- `confidence` (float, required): Verification confidence (0.0-1.0)
- `lat` (float, required): GPS latitude
- `lon` (float, required): GPS longitude
- `photo_url` (string, optional): Photo captured during scan
- `scan_type` (string, optional): `"yellow"` for On Board, `"green"` for Reached (default: "yellow")

**Response** (Success - 200):
```json
{
  "status": "success",
  "event_id": "850e8400-e29b-41d4-a716-446655440004",
  "attendance_status": "yellow"
}
```

**Testing with curl**:
```bash
# Yellow scan (On Board)
curl -X POST ${BACKEND_BASE_URL}/api/scan_event \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "student_id": "student-id-here",
    "tag_id": "RFID-12345678",
    "verified": true,
    "confidence": 0.95,
    "lat": 40.7128,
    "lon": -74.0060,
    "scan_type": "yellow"
  }'

# Green scan (Reached destination)
curl -X POST ${BACKEND_BASE_URL}/api/scan_event \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "student_id": "student-id-here",
    "tag_id": "RFID-12345678",
    "verified": true,
    "confidence": 0.98,
    "lat": 40.7589,
    "lon": -73.9851,
    "scan_type": "green"
  }'
```

---

### 2. Update Bus Location

**Endpoint**: `POST /api/update_location`

**Description**: Updates the GPS coordinates of the bus in real-time.

**Authentication**: X-API-Key header required

**Request Body**:
```json
{
  "bus_id": "550e8400-e29b-41d4-a716-446655440000",
  "lat": 40.7128,
  "lon": -74.0060
}
```

**Response** (Success - 200):
```json
{
  "status": "success",
  "timestamp": "2025-07-15T10:35:00.000Z"
}
```

**Testing with curl**:
```bash
curl -X POST ${BACKEND_BASE_URL}/api/update_location \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "bus_id": "your-bus-id-here",
    "lat": 40.7128,
    "lon": -74.0060
  }'
```

---

### 3. Get Bus Location

**Endpoint**: `GET /api/get_bus_location?bus_id={bus_id}`

**Description**: Retrieves current GPS location of a bus.

**Authentication**: X-API-Key header required

**Query Parameters**:
- `bus_id` (string, required): Bus unique identifier

**Response** (Success - 200):
```json
{
  "bus_id": "550e8400-e29b-41d4-a716-446655440000",
  "lat": 40.7128,
  "lon": -74.0060,
  "timestamp": "2025-07-15T10:35:00.000Z"
}
```

**Testing with curl**:
```bash
curl -X GET "${BACKEND_BASE_URL}/api/get_bus_location?bus_id=your-bus-id-here" \
  -H "X-API-Key: your-api-key-here"
```

---

### 4. Get Student Embedding

**Endpoint**: `GET /api/students/{student_id}/embedding`

**Description**: Retrieves student face embedding data for local verification on Raspberry Pi.

**Authentication**: X-API-Key header required

**Path Parameters**:
- `student_id` (string, required): Student unique identifier

**Response** (Success - 200):
```json
{
  "student_id": "750e8400-e29b-41d4-a716-446655440003",
  "name": "Emma Johnson",
  "embedding": "base64_encoded_embedding_data_here...",
  "has_embedding": true
}
```

**Response** (No embedding available):
```json
{
  "student_id": "750e8400-e29b-41d4-a716-446655440003",
  "name": "Emma Johnson",
  "embedding": "",
  "has_embedding": false
}
```

**Testing with curl**:
```bash
curl -X GET "${BACKEND_BASE_URL}/api/students/student-id-here/embedding" \
  -H "X-API-Key: your-api-key-here"
```

---

### 5. Get Student Photo

**Endpoint**: `GET /api/students/{student_id}/photo`

**Description**: Retrieves student photo URL as fallback when embedding is not available.

**Authentication**: X-API-Key header required

**Path Parameters**:
- `student_id` (string, required): Student unique identifier

**Response** (Success - 200):
```json
{
  "student_id": "750e8400-e29b-41d4-a716-446655440003",
  "name": "Emma Johnson",
  "photo_url": "https://storage.example.com/photos/student_12345.jpg",
  "has_photo": true
}
```

**Testing with curl**:
```bash
curl -X GET "${BACKEND_BASE_URL}/api/students/student-id-here/photo" \
  -H "X-API-Key: your-api-key-here"
```

---

## Testing Examples

### Complete Device Workflow Test

This example demonstrates a complete device workflow from registration to scan event.

```bash
#!/bin/bash

# Configuration
BACKEND_URL="${BACKEND_BASE_URL}/api"
ADMIN_EMAIL="admin@school.com"
ADMIN_PASSWORD="password"

# Step 1: Admin login
echo "Step 1: Admin login..."
curl -X POST "${BACKEND_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"${ADMIN_EMAIL}\", \"password\": \"${ADMIN_PASSWORD}\"}" \
  -c cookies.txt

# Step 2: Get a bus_id (assuming you know it or query /api/buses)
BUS_ID="your-bus-id-here"

# Step 3: Register device
echo -e "\n\nStep 2: Register device..."
RESPONSE=$(curl -s -X POST "${BACKEND_URL}/device/register" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d "{\"bus_id\": \"${BUS_ID}\", \"device_name\": \"Raspberry Pi - Test Device\"}")

echo "$RESPONSE" | jq .

# Extract API key from response
API_KEY=$(echo "$RESPONSE" | jq -r '.api_key')
echo -e "\n\n🔑 API Key: ${API_KEY}"
echo "⚠️  SAVE THIS KEY - It will not be shown again!"

# Step 4: Test scan event with API key
echo -e "\n\nStep 3: Test scan event..."
curl -X POST "${BACKEND_URL}/scan_event" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "student_id": "student-id-here",
    "tag_id": "RFID-TEST-001",
    "verified": true,
    "confidence": 0.95,
    "lat": 40.7128,
    "lon": -74.0060,
    "scan_type": "yellow"
  }' | jq .

# Step 5: Update bus location
echo -e "\n\nStep 4: Update bus location..."
curl -X POST "${BACKEND_URL}/update_location" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d "{
    \"bus_id\": \"${BUS_ID}\",
    \"lat\": 40.7589,
    \"lon\": -73.9851
  }" | jq .

# Step 6: Get student embedding
echo -e "\n\nStep 5: Get student embedding..."
curl -X GET "${BACKEND_URL}/students/student-id-here/embedding" \
  -H "X-API-Key: ${API_KEY}" | jq .

# Cleanup
rm cookies.txt

echo -e "\n\n✅ Device workflow test completed!"
```

### Postman Collection

For Postman users, create a collection with the following requests:

#### Environment Variables
```json
{
  "backend_url": "${BACKEND_BASE_URL}/api",
  "api_key": "your-api-key-here",
  "bus_id": "your-bus-id-here",
  "student_id": "your-student-id-here"
}
```

#### Requests

1. **Admin Login**
   - Method: POST
   - URL: `{{backend_url}}/auth/login`
   - Body: `{"email": "admin@school.com", "password": "password"}`
   - Tests: Save cookie for subsequent requests

2. **Register Device**
   - Method: POST
   - URL: `{{backend_url}}/device/register`
   - Body: `{"bus_id": "{{bus_id}}", "device_name": "Test Device"}`
   - Tests: Save `api_key` from response to environment

3. **Scan Event (Yellow)**
   - Method: POST
   - URL: `{{backend_url}}/scan_event`
   - Headers: `X-API-Key: {{api_key}}`
   - Body: See scan event example above

4. **Scan Event (Green)**
   - Method: POST
   - URL: `{{backend_url}}/scan_event`
   - Headers: `X-API-Key: {{api_key}}`
   - Body: Same as above with `"scan_type": "green"`

5. **Update Location**
   - Method: POST
   - URL: `{{backend_url}}/update_location`
   - Headers: `X-API-Key: {{api_key}}`
   - Body: See update location example above

6. **Get Student Embedding**
   - Method: GET
   - URL: `{{backend_url}}/students/{{student_id}}/embedding`
   - Headers: `X-API-Key: {{api_key}}`

7. **Get Student Photo**
   - Method: GET
   - URL: `{{backend_url}}/students/{{student_id}}/photo`
   - Headers: `X-API-Key: {{api_key}}`

---

## Expected Logs

When testing device endpoints, you should see logs like:

```
INFO: Device registered: Raspberry Pi - Bus 001 for bus BUS-001
INFO: Scan event recorded: Student 750e8400-..., Status: yellow, Device: Raspberry Pi - Bus 001
INFO: Location updated for bus 550e8400-... by device Raspberry Pi - Bus 001
```

---

## Troubleshooting

### Common Issues

**1. 403 Forbidden - Invalid API Key**
- Verify the API key is correct (64 characters)
- Ensure the `X-API-Key` header is included in the request
- Check that the device was registered successfully

**2. 404 Not Found - Student/Bus Not Found**
- Verify the student_id or bus_id exists in the database
- Check for typos in the IDs

**3. 403 Forbidden - Device not authorized for this bus**
- Each device can only update location for its assigned bus
- Verify the `bus_id` in the request matches the device's registered bus

**4. Missing X-API-Key header**
- Ensure the header name is exactly `X-API-Key` (case-sensitive)
- Check that the header is being sent with every device request

### Debug Tips

1. **Test with curl verbose mode**:
   ```bash
   curl -v -X POST "http://localhost:8001/api/scan_event" \
     -H "X-API-Key: your-key" \
     -H "Content-Type: application/json" \
     -d '...'
   ```

2. **Check backend logs**:
   ```bash
   tail -f /var/log/supervisor/backend.err.log
   ```

3. **Verify device registration**:
   ```bash
   # Login as admin and check device list
   curl -X GET "http://localhost:8001/api/device/list" \
     -b cookies.txt
   ```

---

## Security Best Practices

1. **Never expose API keys in code repositories**
   - Store keys in environment files
   - Add `.env` to `.gitignore`

2. **Rotate keys periodically**
   - Delete old device registration
   - Register new device with fresh key

3. **Monitor API usage**
   - Check backend logs for suspicious activity
   - Implement rate limiting if needed

4. **Secure the Raspberry Pi**
   - Use strong SSH passwords
   - Restrict file permissions on `.env` files
   - Keep the OS and packages updated

---

## Local Device Simulator

For local testing and development, use the **Local Device Simulator** script to test all device endpoints without needing a physical Raspberry Pi.

### Location
```bash
/backend/tests/local_device_simulator.py
```

### Configuration

Edit the configuration variables at the top of the script:

```python
# Backend API base URL
BASE_URL = "http://localhost:8001"

# Device API Key (obtain from admin panel)
DEVICE_API_KEY = "your_device_api_key_here"

# Bus ID this device is assigned to
BUS_ID = "BUS-001"

# Test Student ID
STUDENT_ID = "c97f5820-e4a2-479e-8112-b156275a8c52"

# Test image path (for scan events)
TEST_IMAGE_PATH = "test_scan_photo.jpg"

# GPS coordinates for testing
TEST_GPS_LAT = 37.7749
TEST_GPS_LON = -122.4194
```

### Getting Your API Key

1. Login as admin: `admin@school.com` / `password`
2. Navigate to **Device Management** (or use API directly)
3. Register a new device for your test bus:
   ```bash
   curl -X POST http://localhost:8001/api/device/register \
        -H 'Cookie: session=<admin_session>' \
        -H 'Content-Type: application/json' \
        -d '{"bus_id":"BUS-001", "device_name":"Test Device"}'
   ```
4. Copy the generated 64-character API key
5. Update `DEVICE_API_KEY` in the simulator script

### Usage

**Interactive Mode** (Recommended):
```bash
cd /app/backend/tests
python3 local_device_simulator.py
```

**Menu Options**:
- `[1]` Get Student Embedding
- `[2]` Get Student Photo  
- `[3]` Send Yellow Scan (On Board)
- `[4]` Send Green Scan (Reached)
- `[5]` Update GPS Location
- `[6]` Run All Tests
- `[0]` Exit

**Non-Interactive Mode** (CI/CD):
```bash
python3 local_device_simulator.py --run-all
```

### Features

✅ **Color-coded output**: Green for success ✅, Red for failure ❌  
✅ **Comprehensive logging**: All responses logged to `device_test_log.txt`  
✅ **Detailed responses**: Full API response bodies and headers  
✅ **Photo upload testing**: Simulates scan events with base64-encoded images  
✅ **GPS simulation**: Tests location updates with configurable coordinates  
✅ **Batch testing**: Run all tests sequentially with summary report

### Test Logs

All test runs are logged to:
```
/backend/tests/device_test_log.txt
```

The log file includes:
- Timestamps for each test
- Request/response details
- API response bodies and headers
- Success/failure indicators

### Example Output

```
🚌 Bus Tracker - Device API Simulator
============================================================

Configuration:
   • Base URL: http://localhost:8001
   • Bus ID: BUS-001
   • Student ID: c97f5820-e4a2-479e-8112-b156275a8c52
   • API Key: Configured ✓

Test Menu:
   [1] Get Student Embedding
   [2] Get Student Photo
   [3] Send Yellow Scan (On Board)
   [4] Send Green Scan (Reached)
   [5] Update GPS Location
   [6] Run All Tests
   [0] Exit

Select option: 6

🚀 Running All Device API Tests
============================================================

🔍 Testing: Get Student Embedding
✅ SUCCESS
   Student: Emma Johnson
   Has Embedding: false

📷 Testing: Get Student Photo
✅ SUCCESS
   Student: Emma Johnson
   Has Photo: false

🎫 Testing: Scan Event - On Board (Yellow)
✅ SUCCESS
   Status: success
   Attendance Status: yellow
   GPS: (37.7749, -122.4194)

📊 Test Summary
============================================================
   get_embedding: ✅ PASSED
   get_photo: ✅ PASSED
   scan_yellow: ✅ PASSED
   scan_green: ✅ PASSED
   update_location: ✅ PASSED

Results: 5/5 tests passed (100%)
```

### Troubleshooting

**Error: "Device API Key not configured"**
- Solution: Follow the "Getting Your API Key" steps above

**Error: "Connection refused"**
- Solution: Ensure backend is running (`sudo supervisorctl status backend`)

**Error: "403 Forbidden"**
- Solution: Verify API key is correct and device is registered for the specified bus

**Error: "422 Unprocessable Entity"**
- Solution: Check that X-API-Key header is being sent with requests

---

## Additional Resources

- [Main API Documentation](./API_DOCUMENTATION.md)
- [Raspberry Pi Integration Guide](./RASPBERRY_PI_INTEGRATION.md)
- [Database Schema](./DATABASE.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)

---

**Last Updated**: November 2025  
**Version**: 1.1.0
