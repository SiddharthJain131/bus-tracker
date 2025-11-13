# Pi Boarding Simulator - Face Recognition Testing

This simulator replicates the Raspberry Pi boarding process for testing face recognition and attendance tracking.

## Overview

The Pi Boarding Simulator:
1. **Loads students** from a JSON file with their IDs, RFID tags, class, and section
2. **Uses actual profile photos** from `backend/photos/students/<student_id>/profile.jpg`
3. **Generates placeholder photos** from thispersondoesnotexist.com if profile photo doesn't exist
4. **Generates face embeddings** using DeepFace (Facenet model)
5. **Compares embeddings** with backend using cosine similarity
6. **Sends scan events** with photos to the backend API
7. **Saves attendance photos** to `backend/photos/students/<student_id>/attendance/`

## Installation

### Dependencies

The simulator will automatically install DeepFace and its dependencies if not present:
- `deepface` - Face recognition library
- `tf-keras` - TensorFlow Keras
- `tensorflow` - TensorFlow for deep learning
- `opencv-python` - Image processing

Alternatively, install manually:
```bash
cd /app/backend
pip install deepface tf-keras tensorflow opencv-python
```

## Configuration

### 1. Device API Key

Before running the simulator, you need a device API key:

```bash
# Login as admin
curl -X POST http://localhost:8001/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@school.com","password":"password"}'

# Register device for bus
curl -X POST http://localhost:8001/api/device/register \
  -H 'Cookie: session=<admin_session>' \
  -H 'Content-Type: application/json' \
  -d '{"bus_id":"<BUS_ID>","device_name":"Pi Simulator"}'

# Copy the returned API key
```

### 2. Update Configuration

Edit `simulator_config.py`:

```python
# Backend API base URL
BASE_URL = "http://localhost:8001"  # or your backend URL

# Device API Key from registration
DEVICE_API_KEY = "your_64_character_api_key_here"

# Bus ID this device is assigned to
BUS_ID = "your-bus-uuid-here"
```

### 3. Prepare Student Data

The simulator uses `students_boarding.json` with this format:

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

A sample file is included with 5 students. Modify as needed.

## Usage

### Basic Usage

Run the simulator with default settings (AM boarding):

```bash
cd /app/backend/tests
python3 pi_simulator_boarding.py
```

### Scan Type Options

```bash
# Morning boarding (AM - Yellow status)
python3 pi_simulator_boarding.py --scan-type AM

# Afternoon boarding (PM - Green status)
python3 pi_simulator_boarding.py --scan-type PM

# Or use status colors directly
python3 pi_simulator_boarding.py --scan-type yellow
python3 pi_simulator_boarding.py --scan-type green
```

## How It Works

### For Each Student:

#### 1. **Load Profile Photo**
- Checks `backend/photos/students/<student_id>/profile.jpg` (or .png, .jpeg)
- If missing, downloads placeholder from thispersondoesnotexist.com
- Saves placeholder as `profile.jpg` for future use

#### 2. **Generate Embedding**
- Uses DeepFace library with Facenet model
- Generates 128-dimensional face embedding vector
- Handles cases where face detection fails gracefully

#### 3. **Fetch Backend Embedding**
- Calls `GET /api/students/<id>/embedding` with device API key
- Retrieves stored embedding from backend (if available)

#### 4. **Compare Embeddings**
- Calculates cosine similarity between local and backend embeddings
- Similarity range: -1.0 to 1.0 (higher = more similar)
- Default threshold: 0.6 for verification
- If backend embedding unavailable, assumes verified (local-only mode)

#### 5. **Build Scan Event**
- Creates comprehensive scan event payload:
  ```json
  {
    "device_id": "BUS_ID",
    "student_id": "uuid",
    "tag_id": "RFID-1001",
    "verified": true,
    "confidence": 0.85,
    "scan_type": "yellow",
    "lat": 37.7749,
    "lon": -122.4194,
    "photo_base64": "base64_encoded_photo_data"
  }
  ```

#### 6. **Send to Backend**
- Posts to `POST /api/scan_event` with X-API-Key authentication
- Backend creates attendance record and notification if needed
- Returns success/failure status

#### 7. **Save Attendance Photo**
- Copies profile photo to attendance folder
- Naming: `YYYY-MM-DD_AM.jpg` or `YYYY-MM-DD_PM.jpg`
- Location: `backend/photos/students/<student_id>/attendance/`

## Output

### Console Output

The simulator provides detailed, color-coded output:

```
======================================================================
🚌 Pi Boarding Simulator - AM Boarding
======================================================================

Checking dependencies...
✓ DeepFace is already installed

Loading students...
✓ Loaded 5 students from JSON

Starting boarding simulation...

[1/5]
Processing: Emma Johnson (9afb783f-7952-476d-8626-0143fdbbc2a1)
1. Loading profile photo...
   ✓ Photo loaded: profile.jpg
2. Generating embedding with DeepFace...
   ✓ Embedding generated (shape: (128,))
3. Fetching backend embedding...
   ✓ Backend embedding fetched
4. Comparing embeddings...
   ✓ Similarity: 0.8765 (Threshold: 0.6)
   ✓ Verification: PASSED
5. Converting photo to base64...
   ✓ Photo converted (542472 chars)
6. Sending scan event to backend...
   ✓ Scan event uploaded: Success
7. Saving photo to attendance folder...
   ✓ Photo saved: 2025-01-15_AM.jpg

======================================================================
📊 Simulation Summary
======================================================================

Student ID                               | Similarity | Verified | Upload
-----------------------------------------+------------+----------+-----------
9afb783f-7952-476d-8626-0143fdbbc2a1     | 0.8765     | ✓        | Success
   Photo: /app/backend/photos/students/9afb783f-.../attendance/2025-01-15_AM.jpg

Statistics:
   Total Students: 5
   Successful Uploads: 5
   Verified: 5
   Failed: 0
   Success Rate: 100.0%
   Verification Rate: 100.0%
```

### Summary Table

After all students are processed, a summary table shows:
- **Student ID**: Unique identifier
- **Similarity**: Cosine similarity score (0.0 to 1.0)
- **Verified**: ✓ (passed) or ✗ (failed threshold)
- **Upload**: Success or Failed
- **Photo Path**: Saved attendance photo location

### Statistics

- Total students processed
- Successful uploads count
- Verified students count (passed similarity threshold)
- Failed count
- Success rate (%)
- Verification rate (%)

## File Structure

```
/app/backend/
├── photos/
│   └── students/
│       └── <student_id>/
│           ├── profile.jpg          # Profile photo (source)
│           └── attendance/          # Attendance photos
│               ├── 2025-01-15_AM.jpg
│               └── 2025-01-15_PM.jpg
├── tests/
│   ├── pi_simulator_boarding.py     # Main simulator
│   ├── students_boarding.json       # Student data
│   ├── simulator_config.py          # Configuration
│   └── PI_BOARDING_SIMULATOR_README.md  # This file
```

## Features

### ✅ Realistic Simulation
- Uses actual student profile photos
- Generates real face embeddings with DeepFace
- Compares with backend embeddings (if available)
- Sends actual photo data with scan events

### ✅ Automatic Photo Management
- Downloads placeholders for missing photos
- Saves attendance photos with proper naming
- Creates folder structure automatically

### ✅ Robust Error Handling
- Continues processing even if one student fails
- Graceful handling of missing photos
- Fallback to local-only verification if backend unavailable
- Detailed error messages

### ✅ Production-Ready Testing
- Uses device API key authentication
- Sends properly formatted scan events
- Mimics actual Raspberry Pi behavior
- Tests entire boarding workflow

## Configuration Options

### Similarity Threshold

Adjust verification threshold in `pi_simulator_boarding.py`:

```python
SIMILARITY_THRESHOLD = 0.6  # Default: 0.6 (60%)
```

Higher values (0.7-0.9) = stricter verification
Lower values (0.4-0.6) = more lenient verification

### GPS Coordinates

Update test GPS location in `pi_simulator_boarding.py`:

```python
TEST_GPS = {
    "lat": 37.7749,   # San Francisco latitude
    "lon": -122.4194  # San Francisco longitude
}
```

### Placeholder Photo Source

By default uses `https://thispersondoesnotexist.com`

Alternative: Use a specific photo URL in the code:
```python
PLACEHOLDER_PHOTO_URL = "https://your-photo-service.com/api/random"
```

## Troubleshooting

### DeepFace Installation Issues

If automatic installation fails:
```bash
# Install TensorFlow first
pip install tensorflow==2.16.0

# Then install DeepFace
pip install deepface==0.0.79
```

### "Device API Key not configured"

Update `simulator_config.py` with your actual device API key from device registration.

### "Photo not available"

Ensure:
1. Student ID exists in database
2. Photo directory structure exists: `backend/photos/students/<student_id>/`
3. Profile photo exists or internet connection available for placeholder

### "Backend embedding fetch failed: 422"

Missing or invalid X-API-Key header. Check:
1. Device is registered for the bus
2. API key is correct in `simulator_config.py`
3. Backend is running

### "Embedding generation failed"

Could be caused by:
1. Invalid or corrupted photo file
2. DeepFace model not downloaded (first run takes time)
3. Photo doesn't contain a recognizable face (uses enforce_detection=False for flexibility)

### Backend Connection Refused

Ensure backend is running:
```bash
sudo supervisorctl status backend
```

If stopped:
```bash
sudo supervisorctl start backend
```

## Technical Details

### DeepFace Models

The simulator uses **Facenet** model:
- Architecture: Inception ResNet V1
- Embedding size: 128 dimensions
- Accuracy: 99.65% on LFW dataset
- Speed: ~100-200ms per image

Alternative models (edit code to change):
- VGG-Face: 2622 dimensions, slower but accurate
- OpenFace: 128 dimensions, faster
- Dlib: 128 dimensions, good for small faces
- ArcFace: 512 dimensions, state-of-the-art

### Cosine Similarity

Formula: `similarity = (A · B) / (||A|| * ||B||)`

Where:
- A = Local embedding vector
- B = Backend embedding vector
- Result range: -1.0 (opposite) to 1.0 (identical)

Typical ranges:
- 0.8-1.0: Same person (high confidence)
- 0.6-0.8: Same person (medium confidence)
- 0.4-0.6: Uncertain (requires manual review)
- 0.0-0.4: Different person

### Scan Event Flow

```
Student → Photo → DeepFace → Embedding → Compare → Scan Event
                                             ↓
                                    Backend Database
                                             ↓
                                    Attendance Record
                                             ↓
                                    Notification (if needed)
```

## Testing Scenarios

### Scenario 1: Normal Boarding (All Students)
```bash
python3 pi_simulator_boarding.py --scan-type AM
```
Expected: All students verified, photos saved, 100% success

### Scenario 2: Missing Photos
Delete some profile photos to test placeholder generation:
```bash
rm /app/backend/photos/students/<student_id>/profile.jpg
python3 pi_simulator_boarding.py
```
Expected: Placeholder downloaded, saved as profile.jpg

### Scenario 3: Low Similarity
Manually replace a student's profile photo with a different person's photo:
Expected: Low similarity score, verification failed

### Scenario 4: Backend Down
Stop backend and run simulator:
```bash
sudo supervisorctl stop backend
python3 pi_simulator_boarding.py
```
Expected: Local-only verification, scan events fail

## Performance

### Typical Timing (per student):
- Photo loading: ~10ms
- Embedding generation: ~200-500ms (first run: 2-5s for model download)
- Backend comparison: ~50-100ms
- Base64 conversion: ~20ms
- API upload: ~100-200ms
- Photo save: ~10ms

**Total per student**: ~500ms - 1s
**5 students**: ~3-5 seconds
**20 students**: ~10-20 seconds

### Optimization Tips:
1. Pre-download DeepFace models before production
2. Use batch processing for multiple students
3. Cache embeddings to reduce computation
4. Use GPU for DeepFace (if available)

## Future Enhancements

Potential improvements:
- [ ] Batch embedding generation
- [ ] Multi-threading for parallel processing
- [ ] Embedding caching
- [ ] Multiple face detection per photo
- [ ] Photo quality validation
- [ ] Real-time GPS simulation
- [ ] Bus route simulation
- [ ] Integration with actual RFID readers

## Related Documentation

- [Device API Testing](./API_TEST_DEVICE.md)
- [Raspberry Pi Integration](../../docs/RASPBERRY_PI_INTEGRATION.md)
- [Photo Organization](../../docs/PHOTO_ORGANIZATION.md)
- [API Documentation](../../docs/API_DOCUMENTATION.md)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review test logs in console output
3. Check backend logs: `tail -f /var/log/supervisor/backend.out.log`
4. Verify device registration and API key
5. Ensure all dependencies are installed

---

**Last Updated**: January 2025
**Version**: 1.0
**Status**: Production Ready ✅
