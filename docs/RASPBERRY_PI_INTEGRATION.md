# 🛰️ Raspberry Pi Integration Guide

Complete guide for integrating Raspberry Pi devices with RFID readers and cameras to upload attendance data to the Bus Tracker backend.

## Overview

This document explains how Raspberry Pi devices equipped with RFID readers and cameras communicate with the Bus Tracker server via the SIM800 GSM module to record student attendance in real-time.

---

## 🎯 Purpose

The attendance upload API endpoint enables Raspberry Pi devices to:
- Send attendance records as students board (AM) and deboard (PM) buses
- Upload captured photos of students during RFID scans
- Transmit scan metadata including timestamps and confidence scores
- Update the server with device location and status information

This system provides real-time student tracking and automated attendance recording without requiring WiFi connectivity.

---

## 📡 Communication Architecture

```
┌─────────────────┐      ┌──────────────┐      ┌─────────────────┐
│  Raspberry Pi   │      │   SIM800     │      │   Backend       │
│  + RFID Reader  │─────>│   GSM/GPRS   │─────>│   Server        │
│  + Camera       │      │   Module     │      │   (FastAPI)     │
└─────────────────┘      └──────────────┘      └─────────────────┘
        │                                               │
        │                                               │
        ▼                                               ▼
  ┌──────────┐                                  ┌──────────────┐
  │ Local    │                                  │  MongoDB     │
  │ Buffer   │                                  │  Database    │
  └──────────┘                                  └──────────────┘
```

---

## 📋 Request Data Requirements

### Required Fields

When uploading attendance data, the request must contain the following information:

#### Student & School Information

**Student Identifiers:**
- `student_id` (UUID) - Unique student identifier from database
- `tag_id` (String) - RFID tag identifier (e.g., "RFID-1234")
- `roll_number` (String) - Student roll number (e.g., "G5A-001")
- `class_name` (String) - Student's class (e.g., "Grade 5")
- `section` (String) - Student's section (e.g., "A")
- `name` (String) - Student full name for verification

**Purpose:** Ensures correct student identification and prevents identity mismatches.

#### Transport Details

**Bus Information:**
- `bus_id` (UUID) - Unique bus identifier
- `bus_number` (String) - Human-readable bus number (e.g., "BUS-001")
- `driver_name` (String) - Current driver name
- `driver_phone` (String) - Driver contact number

**Stop Information:**
- `stop_id` (UUID) - Unique stop identifier
- `stop_name` (String) - Stop name (e.g., "Main Gate North")
- `order_index` (Integer) - Stop sequence number in route

**GPS Coordinates:**
- `lat` (Float or null) - Latitude of scan location
- `lon` (Float or null) - Longitude of scan location
- **Note**: Both fields support `null` values when GPS is unavailable
- **Fallback behavior**: System continues operating normally with null coordinates
- **Frontend handling**: Map shows "GPS Unavailable" indicator with question mark (🔴❓)

**Purpose:** Tracks student location and verifies they boarded at correct stop. GPS unavailability does not prevent scan recording.

#### Scan Metadata

**Timing Information:**
- `timestamp` (String, ISO 8601) - Exact scan time
  - Format: `2025-01-15T07:58:23.456Z`
  - Must be UTC timezone
- `trip` (String) - Trip type
  - `"AM"` for morning boarding
  - `"PM"` for afternoon deboarding

**Verification Data:**
- `verified` (Boolean) - Whether RFID scan matched student
- `confidence` (Float) - Match confidence score (0.0 to 1.0)
  - 0.95+ : High confidence match
  - 0.75-0.94 : Medium confidence
  - Below 0.75 : Low confidence (triggers alert)

**Purpose:** Enables attendance tracking and identity mismatch detection.

#### Photo Data

**Image Information:**
- `photo_url` (String, Optional) - Photo file reference or Base64 data
- `photo_format` (String) - Image format (e.g., "JPEG", "PNG")
- `photo_size` (Integer) - File size in bytes
- `photo_timestamp` (String, ISO 8601) - When photo was captured

**Camera Metadata:**
- `camera_device_id` (String) - Camera identifier
- `camera_resolution` (String) - Resolution (e.g., "640x480")
- `camera_quality` (Integer) - JPEG quality setting (1-100)

**Purpose:** Visual verification and parent notification with student photos.

#### Optional Device Information

**Raspberry Pi Details:**
- `device_id` (String) - Unique Raspberry Pi identifier
- `device_name` (String) - Device name (e.g., "BUS-001-RPI")
- `firmware_version` (String) - Software version running on device

**Network Information:**
- `signal_strength` (Integer) - GSM signal strength (-113 to -51 dBm)
- `network_operator` (String) - Mobile network carrier
- `connection_type` (String) - "2G", "3G", or "4G"

**Device Status:**
- `battery_level` (Float) - If using battery backup (0.0 to 1.0)
- `temperature` (Float) - Device temperature in Celsius
- `uptime` (Integer) - Seconds since device boot

**Purpose:** Diagnostics, troubleshooting, and device health monitoring.

---

## 🔄 Server Behavior

### Automatic Processing

When the server receives an attendance upload:

1. **Attendance Entry Creation:**
   - New attendance record created automatically
   - Status set to `"yellow"` (On Board) initially
   - Record includes timestamp, student_id, date, and trip type
   - Photo linked to attendance record if provided

2. **Trip Type Determination:**
   - Server analyzes timestamp to determine AM/PM
   - AM: Scans before 12:00 UTC
   - PM: Scans after 12:00 UTC
   - Can be overridden by explicit `trip` parameter

3. **Photo Storage:**
   - Photos saved to server directory: `/photos/{student_id}/`
   - Naming convention: `{student_id}/{date}_{trip}.jpg`
   - Example: `a1b2c3d4-uuid/2025-01-15_AM.jpg`
   - Photo URL stored in attendance record
   - Thumbnails generated automatically for faster loading

4. **Status Transitions:**
   - Initial scan → Status: `"yellow"` (On Board)
   - Bus reaches destination → Status: `"green"` (Reached)
   - No scan detected → Status: `"red"` (Missed)
   - Holiday → Status: `"blue"` (Holiday)
   - Not yet scanned → Status: `"gray"` (Pending)

### Data Validation

The server performs comprehensive validation:

**Student Verification:**
- ✅ `student_id` exists in database
- ✅ Student is active (not archived)
- ✅ Student assigned to correct bus
- ✅ Class and section match records

**RFID Validation:**
- ✅ `tag_id` format is correct
- ✅ Tag is registered in system
- ✅ Tag belongs to student claiming it
- ✅ Tag not reported as lost/stolen

**Timestamp Checks:**
- ✅ Timestamp is valid ISO 8601 format
- ✅ Timestamp not in future
- ✅ Timestamp not too old (> 24 hours)
- ✅ Timezone is UTC

**Photo Validation:**
- ✅ Image format supported (JPEG, PNG, WebP)
- ✅ File size within limits (max 5MB)
- ✅ Image dimensions reasonable (max 4096x4096)
- ✅ Image not corrupted

**Rejection Scenarios:**
- ❌ Invalid `student_id` → 404 Not Found
- ❌ Malformed JSON → 400 Bad Request
- ❌ Missing required fields → 422 Unprocessable Entity
- ❌ Invalid credentials → 401 Unauthorized

### Idempotent Behavior

**Duplicate Upload Prevention:**
- Server checks for existing record with same:
  - `student_id`
  - `date`
  - `trip` (AM/PM)
  - `timestamp` (within 5-minute window)

**If duplicate detected:**
- ✅ Request succeeds (200 OK)
- ✅ Existing record returned
- ✅ No new record created
- ✅ Photo updated if newer version provided
- ℹ️ Response includes `"duplicate": true` flag

**Benefits:**
- Safe to retry failed uploads
- Network interruptions don't create duplicates
- Prevents data corruption
- Simplifies device-side error handling

### Authentication & Security

**Required Headers:**
```
Authorization: Bearer <device_token>
Content-Type: application/json
X-Device-ID: <raspberry_pi_id>
```

**Authentication Flow:**
1. Device sends credentials on first connection
2. Server validates and issues JWT token
3. Token included in all subsequent requests
4. Token expires after 24 hours
5. Device must re-authenticate on expiry

**Security Measures:**
- ✅ All requests over HTTPS (TLS 1.2+)
- ✅ Device credentials stored securely
- ✅ Failed authentication attempts logged
- ✅ Rate limiting (max 100 requests/minute per device)
- ✅ IP whitelisting available for production
- ✅ Photo data encrypted in transit

### Error Handling

**Network Interruptions:**
- Server accepts delayed uploads (up to 24 hours old)
- Partial data preserved if upload fails mid-transmission
- Connection timeout: 30 seconds
- Automatic retry with exponential backoff on client

**Failed Uploads:**
- Can be retried without creating duplicates
- Server returns specific error codes
- Error messages include resolution steps
- Failed requests logged for debugging

**Validation Failures:**
- Clear error messages specify which field failed
- Example: `"Invalid student_id: abc123 not found in database"`
- HTTP status codes follow REST conventions
- Response includes `detail` field with explanation

**Response Codes:**
- `200 OK` - Success (new or duplicate)
- `400 Bad Request` - Invalid JSON format
- `401 Unauthorized` - Authentication failed
- `404 Not Found` - Student/Bus/Stop not found
- `422 Unprocessable Entity` - Validation failed
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server issue

---

## 🔔 Notification System

### Triggered Notifications

Each attendance upload triggers notifications based on scan status:

**Parent Notifications:**
1. **Boarding Confirmed (AM scan with high confidence):**
   - Message: "Your child Emma has boarded bus BUS-001 at Main Gate North (7:58 AM)"
   - Includes photo thumbnail
   - Shows timestamp and location

2. **Deboarding Confirmed (PM scan with high confidence):**
   - Message: "Your child Emma has reached school safely via BUS-001 (3:15 PM)"
   - Includes photo thumbnail
   - Marks completion of trip

3. **Identity Mismatch (Low confidence score < 0.75):**
   - Message: "Identity mismatch detected for Emma (Confidence: 68%)"
   - Alert priority: HIGH
   - Requires manual verification
   - Includes scan photo for review

4. **Missed Bus (No scan during expected window):**
   - Message: "Emma did not board bus BUS-001 this morning"
   - Generated 30 minutes after bus departure
   - Status marked as RED in attendance

**Teacher Notifications:**
- Summary of class attendance at 8:00 AM and 3:30 PM
- Identity mismatch alerts for their students
- Attendance pattern anomalies

**Admin Notifications:**
- All identity mismatches across system
- Device offline alerts
- Failed upload attempts
- System errors requiring attention

---

## 🔌 Integration Points

### Primary Endpoint

**POST /api/scan_event**

This is the main endpoint for attendance uploads from Raspberry Pi.

**Request Example:**
```json
{
  "student_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "tag_id": "RFID-4567",
  "verified": true,
  "confidence": 0.97,
  "lat": 37.7749,
  "lon": -122.4194,
  "photo_url": "/photos/a1b2c3d4-uuid/2025-01-15_AM.jpg",
  "timestamp": "2025-01-15T07:58:23.456Z"
}
```

**Response Example (Success):**
```json
{
  "status": "success",
  "event_id": "evt_xyz789",
  "attendance_id": "att_abc123",
  "duplicate": false,
  "student_name": "Emma Johnson",
  "trip": "AM",
  "photo_stored": true
}
```

### Related Endpoints

**GET /api/get_attendance**

Retrieve attendance records (used by dashboards):
- Returns monthly grid with AM/PM status
- Includes photo URLs and timestamps
- Filtered by student_id and month

**POST /api/update_location**

Update bus GPS location:
- Separate from attendance uploads
- Higher frequency (every 30 seconds)
- Lighter payload (lat/lon only)

**GET /api/students/{id}**

Fetch student details:
- Used for verification on device
- Returns student data for RFID validation
- Includes bus and stop assignments

---

## 💾 Photo Management

### Storage Strategy

**Directory Structure:**
```
/photos/
  ├── student1-uuid/
  │   ├── 2025-01-15_AM.jpg
  │   ├── 2025-01-15_PM.jpg
  │   ├── 2025-01-16_AM.jpg
  │   └── ...
  ├── student2-uuid/
  │   └── ...
```

**Automatic Categorization:**
- Photos grouped by student_id
- Filename includes date and trip type
- Thumbnails generated (150x150px)
- Original photos retained
- Old photos archived after 90 days

### Upload Methods

**Method 1: Base64 Encoded (Small files < 1MB):**
```json
{
  "photo_url": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "photo_format": "JPEG",
  "photo_size": 524288
}
```

**Method 2: File Reference (Larger files):**
```json
{
  "photo_url": "/tmp/scan_12345.jpg",
  "photo_format": "JPEG",
  "photo_size": 2097152
}
```

**Method 3: Multipart Upload (Recommended for SIM800):**
- Use multipart/form-data encoding
- Reduces memory usage on Raspberry Pi
- Better for slow connections

### Photo Handling Rules

1. **Failed Photo Uploads:**
   - Attendance record created anyway
   - Photo field set to null
   - Can be uploaded separately later

2. **Photo Updates:**
   - Can replace photo within 2 hours of scan
   - Older photos become read-only
   - Admin can manually override

3. **Photo Access:**
   - Parents: Can view own children's photos
   - Teachers: Can view assigned students' photos
   - Admins: Full access to all photos

4. **Privacy & Retention:**
   - Photos stored for 90 days by default
   - Configurable retention period
   - Automatic deletion after retention
   - GDPR compliance features available

---

## 🛠️ Best Practices

### Device-Side Implementation

**1. Local Buffering:**
```python
# Pseudocode example
def upload_attendance(scan_data):
    # Try to upload immediately
    try:
        response = post_to_server(scan_data)
        if response.success:
            remove_from_buffer(scan_data)
        else:
            add_to_buffer(scan_data)
    except NetworkError:
        add_to_buffer(scan_data)
    
    # Retry buffered uploads when connection available
    retry_buffered_uploads()
```

**2. Retry Logic with Exponential Backoff:**
```python
def retry_with_backoff(upload_function, max_retries=5):
    for attempt in range(max_retries):
        try:
            return upload_function()
        except Exception:
            wait_time = 2 ** attempt  # 1s, 2s, 4s, 8s, 16s
            time.sleep(wait_time)
    # Give up after max retries
    buffer_for_later()
```

**3. Photo Compression:**
```python
# Reduce image size before upload
from PIL import Image

def compress_photo(image_path, max_size_kb=500):
    img = Image.open(image_path)
    # Resize if too large
    if img.size[0] > 640:
        img.thumbnail((640, 480))
    # Compress JPEG
    img.save(output_path, "JPEG", quality=75, optimize=True)
```

**4. Bandwidth Optimization:**
- Compress photos before upload (target 300-500KB)
- Use smaller thumbnails for low signal
- Batch uploads when connection improves
- Priority queue: Identity mismatches first

**5. Error Handling:**
```python
def safe_upload(data):
    try:
        validate_data(data)  # Local validation
        response = upload_to_server(data)
        log_success(response)
    except ValidationError as e:
        log_error("Validation failed", e)
        # Don't retry - fix the data
    except NetworkError as e:
        log_error("Network issue", e)
        buffer_for_retry(data)
    except ServerError as e:
        log_error("Server issue", e)
        if e.status_code == 500:
            buffer_for_retry(data)  # Temporary server issue
        else:
            log_error("Permanent error", e)  # Don't retry
```

### Testing Recommendations

**1. Offline/Online Scenarios:**
- Test with no network connection
- Test with intermittent connection
- Test with slow connection (simulate 2G)
- Verify buffering and retry works

**2. Duplicate Prevention:**
- Upload same scan twice
- Verify only one attendance record created
- Check idempotent response

**3. Photo Upload:**
- Test various image sizes
- Test corrupt/invalid images
- Test without photo (should still work)
- Test photo compression

**4. Error Recovery:**
- Simulate 500 errors from server
- Simulate authentication expiry
- Simulate rate limiting
- Verify graceful degradation

**5. Load Testing:**
- Simulate 50 students boarding within 5 minutes
- Verify all uploads succeed
- Check for race conditions
- Monitor memory usage

### Production Checklist

- [ ] Device credentials securely stored
- [ ] HTTPS enabled (not HTTP)
- [ ] Retry logic implemented
- [ ] Local buffering working
- [ ] Photo compression enabled
- [ ] Error logging configured
- [ ] Monitoring alerts set up
- [ ] Backup power tested
- [ ] Network failover configured
- [ ] Device health checks running
- [ ] Clock synchronization verified (NTP)
- [ ] Rate limiting considered
- [ ] Bandwidth usage optimized
- [ ] Privacy compliance reviewed
- [ ] Documentation updated

---

## 📊 Monitoring & Diagnostics

### Device Health Metrics

**Track these metrics from Raspberry Pi:**
- Upload success rate (should be > 95%)
- Average upload latency (target < 5 seconds)
- Buffer queue size (should stay near 0)
- Failed upload count
- Network signal strength
- Device uptime

**Alert Thresholds:**
- 🔴 Upload success < 80%
- 🟡 Buffer queue > 10 items
- 🟡 Latency > 10 seconds
- 🔴 Device offline > 5 minutes

### Server-Side Monitoring

**Key Metrics:**
- Attendance upload rate
- Photo storage usage
- Authentication failures
- Validation errors
- Duplicate uploads percentage

**Logs to Review:**
- `/var/log/supervisor/backend.err.log` - Server errors
- `/var/log/attendance_uploads.log` - Upload history
- `/var/log/auth_failures.log` - Security incidents

---

## 🆘 Troubleshooting

### Common Issues

**Issue: Uploads failing with 401 Unauthorized**
- ✅ Check device token hasn't expired
- ✅ Verify credentials are correct
- ✅ Re-authenticate to get new token
- ✅ Check clock sync on Raspberry Pi

**Issue: Photos not appearing in dashboard**
- ✅ Verify photo_url is correct
- ✅ Check file permissions on server
- ✅ Confirm photo format is supported
- ✅ Check photo file size < 5MB

**Issue: Duplicate records being created**
- ✅ Ensure timestamp is included
- ✅ Don't modify timestamp on retries
- ✅ Check idempotent behavior working
- ✅ Review duplicate detection logs

**Issue: High latency on uploads**
- ✅ Compress photos more aggressively
- ✅ Check GSM signal strength
- ✅ Consider batch uploads
- ✅ Reduce upload frequency

**Issue: Buffer filling up**
- ✅ Check network connectivity
- ✅ Verify server is reachable
- ✅ Review server logs for errors
- ✅ Increase retry intervals

---

## 📚 Additional Resources

- **API Documentation:** [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- **Development Guide:** [DEVELOPMENT.md](./DEVELOPMENT.md)
- **Database Schema:** [DATABASE.md](./DATABASE.md)
- **Troubleshooting:** [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

---

**For questions or issues, contact the development team or create an issue on GitHub.**
