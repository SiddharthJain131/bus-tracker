# Pi Real-Time Scanner - Quick Start Guide

## Overview

This simulator mimics a **real Raspberry Pi device** with an RFID scanner:

1. **Registers as a device** - Gets API key automatically
2. **Runs continuous scanning thread** - Simulates RFID card swipes
3. **Real-time processing** - For each RFID scan:
   - Fetches student info and embedding from backend API (by RFID)
   - Generates embedding from profile photo using DeepFace
   - Compares embeddings for verification
   - Sends result back to backend API
4. **Attendance tracking** - Saves photos to attendance folder

## Quick Start

### 1. Run the Scanner

```bash
cd /app/backend/tests
python3 pi_realtime_scanner.py
```

That's it! The scanner will:
- ✅ Login as admin automatically
- ✅ Register the device automatically
- ✅ Start scanning students one by one
- ✅ Process each scan with face verification
- ✅ Send results to backend

### 2. Expected Output

```
======================================================================
🚌 Pi Real-Time Scanner - Raspberry Pi Simulator
======================================================================

Checking dependencies...
✓ All dependencies ready

📝 Logging in as admin...
✓ Admin login successful

🔑 Registering device...
✓ Device registered successfully
  Device ID: abc123...
  API Key: 34f135326bbc30ff28...

✓ Device ready for scanning
  Backend: http://localhost:8001
  Bus ID: 3ca09d6a-2650-40e7-a874-5b2879025aff
  Device: Pi Scanner Test Device

🔄 Scanning thread started
Simulating RFID scans every 3 seconds...

Press Ctrl+C to stop scanning...

======================================================================
📡 RFID Scan Detected
======================================================================
  RFID: RFID-1001
  Student: Emma Johnson
  ID: 9afb783f-7952-476d-8626-0143fdbbc2a1
  Type: AM

[1/6] Loading profile photo...
  ✓ Photo loaded: profile.jpg
[2/6] Generating embedding from photo...
  ✓ Embedding generated (shape: (128,))
[3/6] Fetching backend embedding via API...
  ⚠ Backend embedding not found, using local only
  → Assuming verified (first time scan)
[4/6] Comparing embeddings...
  (skipped - no backend embedding)
[5/6] Converting photo to base64...
  ✓ Photo converted (542472 chars)
[6/6] Sending scan event to backend...
  ✓ Scan event sent successfully
  ✓ Photo saved to attendance folder

======================================================================
✓ SCAN SUCCESSFUL
======================================================================
  Student: Emma Johnson
  Similarity: 1.0000
  Status: ✓ VERIFIED
  Attendance: YELLOW
======================================================================

... (continues with next student after 3 seconds)
```

## How It Works

### Automatic Device Registration

```python
1. Admin Login
   ↓
2. POST /api/device/register
   ↓
3. Get API Key
   ↓
4. Ready to scan
```

### Scanning Flow (Continuous Thread)

```
RFID Scan → Get Student by RFID → Fetch Embedding via API
                                         ↓
Profile Photo → Generate Embedding → Compare Embeddings
                                         ↓
                                    Verify (Pass/Fail)
                                         ↓
                              Send Scan Event to Backend
                                         ↓
                              Save to Attendance Folder
```

### Each Scan Does:

1. **Load Photo** - From `backend/photos/students/<student_id>/profile.jpg`
2. **Generate Embedding** - Using DeepFace Facenet model (128 dimensions)
3. **Fetch Backend Embedding** - Via `GET /api/students/{id}/embedding` with API key
4. **Compare** - Cosine similarity between local and backend embeddings
5. **Verify** - Pass if similarity >= 0.6 (threshold)
6. **Send Event** - Via `POST /api/scan_event` with verification result
7. **Save Photo** - To `attendance/YYYY-MM-DD_AM.jpg`

## Configuration

### Backend URL

By default uses `REACT_APP_BACKEND_URL` environment variable or `http://localhost:8001`.

To change:
```python
# Edit pi_realtime_scanner.py
BACKEND_URL = "https://your-backend-url.com"
```

### Admin Credentials

Default:
```python
ADMIN_EMAIL = "admin@school.com"
ADMIN_PASSWORD = "password"
```

### Bus ID

Default bus ID is used. To change:
```python
# Edit pi_realtime_scanner.py
BUS_ID = "your-bus-uuid-here"
```

### Scan Interval

Scans happen every 3 seconds by default:
```python
SCAN_INTERVAL = 3  # Seconds between scans
```

Adjust for faster/slower scanning:
- `SCAN_INTERVAL = 1` - Fast (1 second)
- `SCAN_INTERVAL = 5` - Slow (5 seconds)
- `SCAN_INTERVAL = 10` - Very slow (10 seconds)

### Verification Threshold

Default similarity threshold is 0.6 (60%):
```python
SIMILARITY_THRESHOLD = 0.6
```

Adjust for stricter/lenient verification:
- `0.8` - Very strict (fewer false positives)
- `0.7` - Strict (recommended for security)
- `0.6` - Balanced (default)
- `0.5` - Lenient (fewer false negatives)

## Features

### ✅ Automatic Setup
- No manual device registration needed
- No configuration file editing required
- Just run and it works!

### ✅ Real-Time Scanning
- Continuous scanning thread
- Processes one student at a time (realistic simulation)
- Automatic AM → PM transition

### ✅ Face Verification
- Generates embeddings using DeepFace
- Compares with backend embeddings
- Sends verification status to backend

### ✅ Complete Workflow
- RFID scan detection
- API calls with device authentication
- Attendance photo saving
- Backend integration

### ✅ Automatic AM/PM Cycling
- Starts with AM (yellow status)
- After all students scanned once, switches to PM (green status)
- Continues cycling

## Stopping the Scanner

Press `Ctrl+C` to stop:

```
🛑 Stopping scanner...
✓ Scanner stopped
```

The scanning thread will stop gracefully.

## Student Data

The scanner uses `students_boarding.json` for RFID mapping:

```json
[
  {
    "student_id": "9afb783f-7952-476d-8626-0143fdbbc2a1",
    "rfid": "RFID-1001",
    "class": "5",
    "section": "A",
    "name": "Emma Johnson"
  }
]
```

To add more students, edit this file.

## Verification Results

### When Backend Embedding Exists

```
[3/6] Fetching backend embedding via API...
  ✓ Backend embedding fetched
[4/6] Comparing embeddings...
  ✓ Similarity: 0.8765
  ✓ Verification: PASSED (>= 0.6)
```

**Status:** Verified ✓
**Attendance:** Created with verified=true

### When Backend Embedding Doesn't Exist

```
[3/6] Fetching backend embedding via API...
  ⚠ Backend embedding not found, using local only
  → Assuming verified (first time scan)
```

**Status:** Verified ✓ (assumes first scan)
**Attendance:** Created with verified=true
**Note:** Backend will store this embedding for future comparisons

### When Verification Fails

```
[4/6] Comparing embeddings...
  ✓ Similarity: 0.4532
  ✗ Verification: FAILED (< 0.6)
```

**Status:** Not Verified ✗
**Attendance:** Created with verified=false
**Notification:** Parent receives identity mismatch alert

## Checking Results

### 1. Backend Logs

```bash
tail -f /var/log/supervisor/backend.out.log
```

Look for:
- `Scan event received`
- `Attendance record created`
- `Identity mismatch notification sent`

### 2. Parent Dashboard

Login as `parent@school.com` / `password`:
- Check attendance grid
- Yellow status = AM boarding (on board)
- Green status = PM boarding (reached)
- Notifications for identity mismatches

### 3. Admin Dashboard

Login as `admin@school.com` / `password`:
- View all students' attendance
- See device registrations
- Check scan events

### 4. Attendance Photos

Check saved photos:
```bash
ls -la /app/backend/photos/students/*/attendance/
```

Each student should have:
- `YYYY-MM-DD_AM.jpg` - Morning boarding photo
- `YYYY-MM-DD_PM.jpg` - Afternoon boarding photo

## Troubleshooting

### "✗ Admin login failed"

**Cause:** Admin credentials incorrect or backend not running

**Solution:**
```bash
# Check backend status
sudo supervisorctl status backend

# Restart if needed
sudo supervisorctl restart backend

# Verify admin credentials
curl -X POST http://localhost:8001/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@school.com","password":"password"}'
```

### "✗ Device may already be registered"

**Cause:** Device already exists for this bus

**Solution:** This is normal! The scanner will use the existing API key from `simulator_config.py`. If it doesn't work:

1. Delete the existing device via admin dashboard
2. Or run scanner again (it will create new device)

### "✗ Photo not found"

**Cause:** Student photo doesn't exist

**Solution:**
```bash
# Check if photo exists
ls /app/backend/photos/students/<student_id>/profile.jpg

# If missing, run photo populator
cd /app/backend
python3 populate_photos.py
```

### "✗ Embedding generation failed"

**Cause:** DeepFace model issue or invalid photo

**Solution:**
1. Ensure photo is valid JPEG/PNG
2. Wait for DeepFace model download (first run)
3. Check photo has a recognizable face

### "✗ Failed to send scan event"

**Cause:** API key invalid or backend unreachable

**Solution:**
```bash
# Test API key
curl -X GET http://localhost:8001/api/students \
  -H 'X-API-Key: your-api-key-here'

# Check backend connectivity
curl http://localhost:8001/api/health
```

## Performance

### Typical Timing Per Scan

- Photo loading: ~10ms
- Embedding generation: ~300-500ms
- API call (fetch embedding): ~50-100ms
- Comparison: ~5ms
- API call (send event): ~100-200ms
- Photo save: ~10ms

**Total:** ~500ms - 1 second per scan

### Resource Usage

- **CPU:** Moderate (DeepFace uses TensorFlow)
- **Memory:** ~500MB (TensorFlow models)
- **Network:** Light (small API calls)

## Comparison with Batch Simulator

| Feature | Real-Time Scanner | Batch Simulator |
|---------|------------------|----------------|
| Mode | Continuous thread | One-time batch |
| Registration | Automatic | Manual config |
| RFID Simulation | Yes (threaded) | No |
| Timing | Real-time delays | Sequential |
| Use Case | Device testing | Mass testing |
| Setup | Zero config | Requires config |

## Advanced Usage

### Custom Scan Sequence

Edit `students_boarding.json` to control scan order:

```json
[
  {"student_id": "...", "rfid": "RFID-1001", "name": "First Student"},
  {"student_id": "...", "rfid": "RFID-1002", "name": "Second Student"},
  {"student_id": "...", "rfid": "RFID-1003", "name": "Third Student"}
]
```

Students will be scanned in this order.

### Integration with Real RFID Reader

To connect a real RFID reader:

1. Install RFID library (e.g., `mfrc522`)
2. Replace `scanning_thread()` to read from hardware
3. Keep the processing logic unchanged

Example:
```python
def scanning_thread():
    import mfrc522
    reader = mfrc522.SimpleMFRC522()
    
    while scanning_active:
        rfid, text = reader.read()
        # Look up student by RFID
        # Call process_rfid_scan(...)
```

## Next Steps

1. ✅ Run the scanner: `python3 pi_realtime_scanner.py`
2. ✅ Watch the console output for each scan
3. ✅ Check parent dashboard for attendance records
4. ✅ Review attendance photos in photo directories
5. ✅ Test with different students and scenarios

## Related Documentation

- [Batch Boarding Simulator](./PI_BOARDING_SIMULATOR_README.md)
- [Device API Testing](./README.md)
- [Usage Examples](./USAGE_EXAMPLE.md)

---

**Ready to start scanning!**
```bash
cd /app/backend/tests
python3 pi_realtime_scanner.py
```

Press Ctrl+C when done! 🚌✨
